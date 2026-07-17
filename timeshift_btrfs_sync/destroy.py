"""Destructive setup retirement using the shared Btrfs tree engine."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from . import payload_stats
from . import state as state_mod
from .btrfs_ops import BtrfsOps
from .config import AppConfig
from .endpoint import CommandEndpoint
from .executor import WorkflowExecutor
from .paths import is_same_or_under
from .planning import ActionKind, WorkflowAction, plan_destroy_targets
from .source import SourceRunner
from .tree_ops import TreeDeleteResult, delete_subvolume_tree

PROTECTED_PATHS = {
    "/", "/home", "/mnt", "/media", "/var", "/run", "/tmp", "/usr", "/etc", "/root", "/boot",
}


@dataclass(slots=True)
class DestroyResult:
    """Named wrapper around the shared tree-deletion result."""

    label: str
    tree: TreeDeleteResult


def _safe_cleanup_path(path: str | Path, label: str) -> str:
    text = os.path.normpath(str(path).strip())
    if not text or text == "." or not text.startswith("/"):
        raise RuntimeError(f"Refusing unsafe {label} path; it must be absolute: {path!r}")
    if ".." in Path(text).parts:
        raise RuntimeError(f"Refusing unsafe {label} path containing '..': {text}")
    if text.rstrip("/") in PROTECTED_PATHS:
        raise RuntimeError(f"Refusing to destroy protected broad path for {label}: {text}")
    if len([part for part in Path(text).parts if part not in {"/", ""}]) < 2:
        raise RuntimeError(f"Refusing suspiciously broad {label} path: {text}")
    return text.rstrip("/")


def _confirm_or_raise(prompt: str, expected: str) -> None:
    if input(prompt).strip() != expected:
        raise RuntimeError("Confirmation did not match; destructive cleanup aborted")


def _mode_text(delete_source: bool, delete_destination: bool) -> str:
    if delete_source and delete_destination:
        return "DELETE BOTH"
    return "DELETE SOURCE" if delete_source else "DELETE DESTINATION"


def _load_payload_state(config: AppConfig) -> dict | None:
    try:
        return state_mod.load_state(config.state_file)
    except Exception:
        return None


def _result_by_label(results: list[DestroyResult], label: str) -> DestroyResult | None:
    return next((result for result in results if result.label == label and result.tree.existed), None)


def _print_payload_match(config: AppConfig, results: list[DestroyResult], state_doc: dict | None) -> None:
    source = _result_by_label(results, "Source send-cache root")
    destination = _result_by_label(results, "Destination target_root")
    if source is None or destination is None:
        return
    cache_stats = payload_stats.source_send_cache_stats(source.tree.root, source.tree.planned, config.source.subvolumes)
    direct_stats = (
        payload_stats.direct_send_payload_stats(state_doc, config.source.subvolumes)
        if state_doc is not None else None
    )
    source_stats = payload_stats.merge_source_payload_stats(cache_stats, direct_stats)
    destination_stats = payload_stats.destination_payload_stats(
        destination.tree.root, destination.tree.planned, config.source.subvolumes
    )
    for line in payload_stats.render_payload_match(payload_stats.compare_payloads(source_stats, destination_stats)):
        print(line)
    print()


def _print_result(result: DestroyResult, *, dry_run: bool) -> None:
    tree = result.tree
    print(f"{result.label}:")
    print(f"  path:       {tree.root}")
    if not tree.existed:
        if not dry_run:
            print(f"  verified configured root absent: {'yes' if tree.verified_root_absent else 'no'}")
        print("  result:     already missing" if tree.success else "  result:     incomplete")
    else:
        print(f"  subvolumes: {len(tree.planned)}")
        if dry_run:
            for path in tree.planned:
                print(f"    would delete subvolume: {path}")
            if tree.errors:
                print("  result:     incomplete")
                for error in tree.errors:
                    print(f"    error: {error}")
            else:
                print("  result:     dry-run plan complete")
            return
        print(f"  deleted subvolumes: {len(tree.confirmed)}")
        print(f"  verified configured root absent: {'yes' if tree.verified_root_absent else 'no'}")
        if tree.remaining:
            print("  remaining Btrfs subvolumes:")
            for path in tree.remaining:
                print(f"    {path}")
        print("  result:     complete" if tree.success else "  result:     incomplete")
    for error in tree.errors:
        print(f"    error: {error}")


def destroy_leftovers(
    config: AppConfig,
    *,
    delete_source: bool,
    delete_destination: bool,
    dry_run: bool,
    danger_confirmed: bool,
    interactive: bool = True,
) -> list[DestroyResult]:
    """Plan and execute selected source/destination tree retirement."""

    if not delete_source and not delete_destination:
        raise RuntimeError("Choose exactly one of --delete-source, --delete-destination, or --delete-both")

    targets: list[tuple[str, str]] = []
    source_runner: SourceRunner | None = None
    source_ops: BtrfsOps | None = None
    destination_ops = BtrfsOps(
        CommandEndpoint.local("destination"), config.destination.sudo, config.destination.btrfs_command
    )
    if delete_source:
        if not config.source.cache_root:
            raise RuntimeError("--delete-source requires source.cache_root")
        if is_same_or_under(config.source.cache_root, config.source.snapshot_root):
            raise RuntimeError("Refusing source cleanup because source.cache_root overlaps protected source.snapshot_root")
        source_runner = SourceRunner.from_config(config)
        source_ops = BtrfsOps(
            CommandEndpoint.for_source(source_runner), config.source.sudo, config.source.btrfs_command
        )
        targets.append(("Source send-cache root", _safe_cleanup_path(config.source.cache_root, "source.cache_root")))
    if delete_destination:
        targets.append(("Destination target_root", _safe_cleanup_path(config.destination.target_root, "destination.target_root")))

    mode = _mode_text(delete_source, delete_destination)
    print("DESTRUCTIVE LEFTOVER CLEANUP")
    print("============================")
    print("This command ignores state retention and deletes only selected app-owned Btrfs trees.")
    print(f"Run mode: {'dry-run' if dry_run else 'REAL DELETION'}")
    print(f"Selected mode: {mode}")
    print(f"Configured job: {config.name}")
    for label, path in targets:
        print(f"{label}:\n  {path}")
    print()

    if not dry_run:
        if not danger_confirmed:
            raise RuntimeError("Real destroy-leftovers requires --i-understand-this-destroys-data")
        if interactive:
            _confirm_or_raise(f"Type {mode} to continue: ", mode)
            _confirm_or_raise(f"Type the configured job name ({config.name}) to continue: ", config.name)

    payload_state = _load_payload_state(config) if delete_source and delete_destination else None
    plan = plan_destroy_targets(targets)

    def handle(action: WorkflowAction) -> DestroyResult:
        label = str(action.payload["label"])
        path = str(action.payload["path"])
        is_source = label == "Source send-cache root"
        ops = source_ops if is_source else destination_ops
        assert ops is not None
        protected = [config.source.snapshot_root] if is_source else []
        tree = delete_subvolume_tree(
            ops,
            path,
            protected_roots=protected,
            dry_run=dry_run,
            allow_empty_ordinary_root=True,
        )
        return DestroyResult(label, tree)

    executor = WorkflowExecutor({ActionKind.DESTROY_TREE: handle})
    results = [result for _action, result in executor.execute(plan)]
    for result in results:
        _print_result(result, dry_run=dry_run)
        print()

    _print_payload_match(config, results, payload_state)
    failures = [
        result for result in results
        if result.tree.errors or (not dry_run and not result.tree.success)
    ]
    print("DESTROY SUMMARY")
    print("===============")
    print(f"  targets:    {len(results)}")
    print(f"  complete:   {len(results) - len(failures)}")
    print(f"  incomplete: {len(failures)}")
    if failures:
        raise RuntimeError("destroy-leftovers finished with incomplete target cleanup; inspect errors above")
    return results
