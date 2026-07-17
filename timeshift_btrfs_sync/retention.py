"""Destination retention/pruning logic."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from . import inventory
from .btrfs_ops import BtrfsOps
from .cache_ops import cache_parent_path
from .paths import is_under, is_same_or_under
from .endpoint import CommandEndpoint
from .tree_ops import delete_subvolume_tree
from .planning import ActionKind, plan_prune_snapshot
from .executor import WorkflowExecutor
from .config import AppConfig
from .models import SnapshotMeta, tags_text
from .state import (
    STATE_VERSION,
    normalize_state_paths,
    remove_snapshot_from_state,
    resolve_destination_path,
    resolve_state_send_path,
    save_state,
    state_send_path_is_app_cache,
    state_send_path_is_protected_timeshift_original,
)
from .log import emit_success_summary, get_logger
from .source import SourceRunner


@dataclass(slots=True)
class PrunePlan:
    """Dry-run friendly prune plan."""

    keep: set[str] = field(default_factory=set)
    delete: set[str] = field(default_factory=set)
    reasons: dict[str, list[str]] = field(default_factory=dict)

    def add_keep(self, snapshot: str, reason: str) -> None:
        """Mark a snapshot as kept and remember the human reason."""

        self.keep.add(snapshot)
        self.delete.discard(snapshot)
        self.reasons.setdefault(snapshot, []).append(f"keep: {reason}")

    def add_delete(self, snapshot: str, reason: str) -> None:
        """Mark a snapshot as deletable only when it is not already protected."""

        if snapshot not in self.keep:
            self.delete.add(snapshot)
        self.reasons.setdefault(snapshot, []).append(f"delete: {reason}")


def _is_app_created_ondemand(snapshot_state: dict, marker: str) -> bool:
    """Return true when a state entry is a tag O snapshot with the app marker."""

    if "O" not in snapshot_state.get("tags", []):
        return False
    marker = marker.lower().strip()
    if not marker:
        return False
    return marker in str(snapshot_state.get("comment") or "").lower()



def _delete_reason_for_snapshot(
    config: AppConfig,
    snapshots: dict,
    name: str,
    *,
    app_created_ondemand: set[str],
    normal_ondemand: set[str],
) -> str:
    """Explain why a snapshot is outside the active retention rules."""

    snapshot_state = snapshots.get(name, {})
    tags = snapshot_state.get("tags", []) or []
    tag_text = tags_text(snapshot_state.get('tags', []))

    if name in app_created_ondemand:
        return (
            "app-created on-demand snapshot outside "
            f"manual_snapshot.retention_count={config.manual_snapshot.retention_count}; tags={tag_text}"
        )

    if name in normal_ondemand:
        return f"normal on-demand snapshot outside retention.ondemand={config.retention.ondemand}; tags={tag_text}"

    matched_rules: list[str] = []
    for tag, count in config.retention.counts_by_tag().items():
        if tag == "O" or count <= 0:
            continue
        if tag in tags:
            matched_rules.append(f"tag {tag} keeps newest {count}")

    if matched_rules:
        return f"outside active Timeshift tag retention ({'; '.join(matched_rules)}); tags={tag_text}"

    return f"not protected by any active retention rule; tags={tag_text}"


def _delete_reasons(plan: PrunePlan, name: str) -> list[str]:
    """Return delete reasons without the internal prefix."""

    reasons: list[str] = []
    for reason in plan.reasons.get(name, []):
        if reason.startswith("delete: "):
            reasons.append(reason.removeprefix("delete: "))
    return reasons or ["outside retention"]

def _source_cache_delete_paths(
    config: AppConfig,
    snapshot_name: str,
    snapshot_state: dict,
) -> list[tuple[str, str]]:
    """Return app-owned source send-cache paths for a prune decision.

    Original Timeshift snapshot paths are deliberately excluded even when they
    were used as direct read-only send sources. Timeshift owns
    source.snapshot_root; this app only prunes app-created source-cache paths.
    Older state did not store send_path_kind, so the compatibility fallback
    still treats only paths below source.cache_root as app-owned.
    """

    if not config.source.cleanup_superseded_cache or not config.source.cache_root:
        return []
    paths: dict[str, str] = {}
    for subvol_name, subvol in snapshot_state.get("subvolumes", {}).items():
        if not isinstance(subvol, dict):
            continue
        if not subvol.get("send_path"):
            continue
        if not state_send_path_is_app_cache(
            subvol,
            cache_root=config.source.cache_root,
            snapshot_root=config.source.snapshot_root,
        ):
            continue
        try:
            send_path = resolve_state_send_path(
                subvol,
                snapshot_root=config.source.snapshot_root,
                cache_root=config.source.cache_root,
                snapshot_name=snapshot_name,
                subvolume_name=str(subvol_name),
            )
        except ValueError as exc:
            raise RuntimeError(
                f"Invalid source-cache send_path in state for {snapshot_name}/{subvol_name}: {exc}"
            ) from exc
        if is_same_or_under(send_path, config.source.snapshot_root):
            # Final safety guard: Timeshift owns source.snapshot_root and every
            # snapshot subvolume below it. Never return those paths as delete
            # candidates, even if stale state incorrectly marks them as cache.
            continue
        if is_under(send_path, config.source.cache_root):
            paths[subvol_name] = send_path
    return sorted(paths.items())


def _protected_timeshift_send_paths(
    config: AppConfig,
    snapshot_name: str,
    snapshot_state: dict,
) -> list[tuple[str, str]]:
    """Return direct Timeshift send paths that prune must never delete."""

    paths: dict[str, str] = {}
    for subvol_name, subvol in snapshot_state.get("subvolumes", {}).items():
        if not isinstance(subvol, dict):
            continue
        if not subvol.get("send_path"):
            continue
        if not state_send_path_is_protected_timeshift_original(
            subvol,
            cache_root=config.source.cache_root,
            snapshot_root=config.source.snapshot_root,
        ):
            continue
        try:
            paths[subvol_name] = resolve_state_send_path(
                subvol,
                snapshot_root=config.source.snapshot_root,
                cache_root=config.source.cache_root,
                snapshot_name=snapshot_name,
                subvolume_name=str(subvol_name),
            )
        except ValueError as exc:
            raise RuntimeError(
                f"Invalid protected Timeshift send_path in state for {snapshot_name}/{subvol_name}: {exc}"
            ) from exc
    return sorted(paths.items())


def _destination_delete_paths(config: AppConfig, snapshot_state: dict) -> list[tuple[str, Path]]:
    """Return tracked destination subvolume paths for a prune decision."""

    paths: dict[str, Path] = {}
    for subvol_name, subvol in snapshot_state.get("subvolumes", {}).items():
        destination_path = subvol.get("destination_path")
        if destination_path:
            paths[subvol_name] = resolve_destination_path(config.destination.target_root, destination_path)
    return sorted(paths.items())


def source_snapshot_state(snapshots: Iterable[SnapshotMeta]) -> dict:
    """Return temporary state-like data from source Timeshift snapshots.

    Initial/full sync uses this to apply the same retention rules before
    transferring anything. Only snapshot-level Timeshift metadata is needed for
    that decision; transfer identity fields are intentionally absent because no
    destination state exists yet.
    """

    return {
        "version": STATE_VERSION,
        "snapshots": {
            snap.name: {
                "name": snap.name,
                "tags": list(snap.tags),
                "comment": snap.comment,
                "created": snap.created,
                "path": (Path("snapshots") / snap.name).as_posix(),
                "subvolumes": {},
            }
            for snap in snapshots
        },
    }


def initial_sync_keep_names(config: AppConfig, snapshots: Iterable[SnapshotMeta]) -> set[str]:
    """Return source snapshot names that a fresh destination should seed.

    This uses the same retention planner as prune so a new/full sync does not
    waste time sending snapshots that the post-sync retention step would delete
    immediately.
    """

    return build_prune_plan(config, source_snapshot_state(snapshots)).keep


def _cleanup_source_cache_for_pruned_snapshot(
    config: AppConfig,
    source: SourceRunner,
    snapshot_name: str,
    snapshot_state: dict,
    source_cache_index: inventory.BtrfsIndex | None = None,
) -> bool:
    """Delete one pruned snapshot's app-owned cache through the shared tree engine."""

    protected_paths = _protected_timeshift_send_paths(config, snapshot_name, snapshot_state)
    if protected_paths:
        print("  source Timeshift originals: protected; not deleted by this app")
        for subvolume_name, path in protected_paths:
            print(f"  protected {subvolume_name}: {path}")

    cache_paths = _source_cache_delete_paths(config, snapshot_name, snapshot_state)
    if not cache_paths:
        print("  source send-cache: no tracked app-created cache paths; confirmed gone")
        return True
    if not config.source.cache_root:
        print("  warning: tracked cache paths exist but source.cache_root is unavailable")
        return False

    parent = cache_parent_path(config.source.cache_root, snapshot_name)
    ops = BtrfsOps(
        CommandEndpoint.for_source(source),
        config.source.sudo,
        config.source.btrfs_command,
    )
    result = delete_subvolume_tree(
        ops,
        parent,
        protected_roots=[config.source.snapshot_root],
        refuse_unknown_entries=True,
    )
    if result.success:
        if source_cache_index is not None:
            source_cache_index.remove_tree(parent)
        print(f"  source send-cache: confirmed gone {parent}")
        return True
    print("  warning: source send-cache cleanup incomplete; keeping state entry for retry")
    for error in result.errors:
        print(f"    {error}")
    for path in result.remaining:
        print(f"    remaining: {path}")
    return False

def build_prune_plan(config: AppConfig, state: dict) -> PrunePlan:
    """Build retention plan from state without deleting anything.

    On-demand cleanup is intentionally split into two independent decisions:

    * manual_snapshot.cleanup_enabled controls app-created tag O snapshots whose
      saved Timeshift comment contains manual_snapshot.marker.
    * retention.cleanup_ondemand controls normal/user-created tag O snapshots.

    This prevents normal manual Timeshift snapshots from being deleted merely
    because the app also has its own on-demand snapshot retention rule.
    """

    snapshots = state.get("snapshots", {})
    names = sorted(snapshots.keys())
    plan = PrunePlan()
    if not names:
        return plan

    marker = config.manual_snapshot.marker.lower().strip()
    app_created_ondemand = {
        name for name in names if _is_app_created_ondemand(snapshots[name], marker)
    }
    normal_ondemand = {
        name
        for name in names
        if "O" in snapshots[name].get("tags", []) and name not in app_created_ondemand
    }

    for name in config.retention.protected_snapshots:
        if name in snapshots:
            plan.add_keep(name, "protected")
    if config.retention.keep_latest:
        plan.add_keep(names[-1], "newest synced snapshot")

    # App-created on-demand retention. This only affects snapshots with the
    # configured marker in the saved Timeshift comment.
    if config.manual_snapshot.cleanup_enabled:
        manual_count = config.manual_snapshot.retention_count
        selected = sorted(app_created_ondemand, reverse=True)
        for name in selected[:manual_count]:
            plan.add_keep(name, f"app-created on-demand retention count {manual_count}")
    else:
        for name in sorted(app_created_ondemand):
            plan.add_keep(name, "app-created on-demand cleanup disabled")

    # Normal/user-created on-demand retention. This is independent from the
    # app-created rule above and is disabled by default for safety.
    if config.retention.cleanup_ondemand:
        selected = sorted(normal_ondemand, reverse=True)
        for name in selected[: config.retention.ondemand]:
            plan.add_keep(name, f"normal on-demand retention count {config.retention.ondemand}")
    else:
        for name in sorted(normal_ondemand):
            plan.add_keep(name, "normal on-demand cleanup disabled")

    # Non-O Timeshift tag retention. Tag O is handled separately above so the
    # two on-demand cleanup switches stay independent.
    for tag, count in config.retention.counts_by_tag().items():
        if tag == "O" or count <= 0:
            continue
        tagged = [name for name in names if tag in snapshots[name].get("tags", [])]
        tagged.sort(reverse=True)
        for name in tagged[:count]:
            plan.add_keep(name, f"tag {tag} retention count {count}")

    if config.retention.keep_latest_common_parent:
        plan.add_keep(names[-1], "latest common parent safety")

    for name in names:
        if name not in plan.keep:
            plan.add_delete(
                name,
                _delete_reason_for_snapshot(
                    config,
                    snapshots,
                    name,
                    app_created_ondemand=app_created_ondemand,
                    normal_ondemand=normal_ondemand,
                ),
            )
    plan.delete -= plan.keep
    return plan


def _delete_destination_snapshot_for_prune(config: AppConfig, state: dict, snapshot_name: str) -> bool:
    """Delete one destination date through the shared tree engine."""

    snapshot_path = config.destination.target_root / "snapshots" / snapshot_name
    ops = BtrfsOps(
        CommandEndpoint.local("destination"),
        config.destination.sudo,
        config.destination.btrfs_command,
    )
    result = delete_subvolume_tree(
        ops,
        snapshot_path,
        allowed_regular_names={"info.json"},
        expected_subvolume_paths={snapshot_path / subvolume for subvolume in config.source.subvolumes},
        refuse_unknown_entries=True,
    )
    if result.success:
        print("  destination: confirmed gone; info.json was removed with the date subvolume")
        return True
    print("  warning: destination cleanup incomplete; keeping state entry for retry")
    for error in result.errors:
        print(f"    {error}")
    for path in result.remaining:
        print(f"    remaining: {path}")
    return False

def _delete_prune_item(
    config: AppConfig,
    state: dict,
    plan: PrunePlan,
    source_cache_runner: SourceRunner | None,
    name: str,
    *,
    source_cache_index: inventory.BtrfsIndex | None = None,
) -> bool:
    """Execute one pure prune plan and remove state after both trees are gone."""

    snapshot_state = state.get("snapshots", {}).get(name, {})
    print()
    print("RETENTION DELETE")
    print(f"  snapshot: {name}")
    print(f"  tags:     {tags_text(snapshot_state.get('tags', []))}")
    for reason in _delete_reasons(plan, name):
        print(f"  why:      {reason}")

    workflow = plan_prune_snapshot(
        name,
        delete_cache=source_cache_runner is not None,
        delete_destination=True,
    )
    status = {"destination": True, "cache": True}

    def delete_destination(_action):
        print("\nRetention Delete Destination")
        status["destination"] = _delete_destination_snapshot_for_prune(config, state, name)
        return status["destination"]

    def delete_cache(_action):
        print("\nRetention Delete Source send-cache")
        assert source_cache_runner is not None
        status["cache"] = _cleanup_source_cache_for_pruned_snapshot(
            config,
            source_cache_runner,
            name,
            snapshot_state,
            source_cache_index=source_cache_index,
        )
        return status["cache"]

    def remove_state(_action):
        print("\nState")
        if status["destination"] and status["cache"]:
            remove_snapshot_from_state(state, name)
            print("  removed; destination and source send-cache are confirmed gone")
            return True
        print("  kept; cleanup can be retried safely on the next prune")
        return False

    executor = WorkflowExecutor({
        ActionKind.DELETE_DESTINATION_TREE: delete_destination,
        ActionKind.DELETE_CACHE_TREE: delete_cache,
        ActionKind.REMOVE_STATE: remove_state,
    })
    results = executor.execute(workflow)
    return bool(results and results[-1][1])

def print_prune_plan(config: AppConfig, plan: PrunePlan, state: dict, *, dry_run: bool) -> None:
    """Write an easy-to-read retention summary to terminal and .succes."""

    snapshots = state.get("snapshots", {})
    mode_text = "dry-run plan" if dry_run else "real deletion plan"
    lines = [
        "",
        "RETENTION SUMMARY",
        "=================",
        f"  mode:              {mode_text}",
        f"  snapshots in state:{len(snapshots):>5}",
        f"  kept by rules:     {len(plan.keep):>5}",
        f"  delete candidates: {len(plan.delete):>5}",
    ]

    if not plan.delete:
        lines += ["  deletion:          none", ""]
        emit_success_summary("\n".join(lines))
        return

    lines += ["", "RETENTION DELETE PLAN", "---------------------"]
    for name in sorted(plan.delete):
        snapshot_state = snapshots.get(name, {})
        action = "WOULD DELETE" if dry_run else "DELETE"
        lines.append(f"  [{action}] {name}  tags={tags_text(snapshot_state.get('tags', []))}")
        destination_paths = _destination_delete_paths(config, snapshot_state)
        if destination_paths:
            lines.append("      destination subvolumes:")
            for subvol_name, destination_path in destination_paths:
                lines.append(f"        {subvol_name}: {destination_path}")
        cache_paths = _source_cache_delete_paths(config, name, snapshot_state)
        if cache_paths:
            lines.append("      app-owned source send-cache subvolumes:")
            for subvol_name, send_path in cache_paths:
                lines.append(f"        {subvol_name}: {send_path}")
        protected_paths = _protected_timeshift_send_paths(config, name, snapshot_state)
        if protected_paths:
            lines.append("      protected Timeshift original send paths, not deleted by prune:")
            for subvol_name, send_path in protected_paths:
                lines.append(f"        {subvol_name}: {send_path}")
        for reason in _delete_reasons(plan, name):
            lines.append(f"      why: {reason}")
    lines.append("")
    emit_success_summary("\n".join(lines))


def prune(config: AppConfig, state: dict, *, dry_run: bool, yes_delete: bool) -> PrunePlan:
    """Apply destination retention rules."""

    normalize_state_paths(
        state,
        target_root=config.destination.target_root,
        snapshot_root=config.source.snapshot_root,
        cache_root=config.source.cache_root,
    )
    plan = build_prune_plan(config, state)
    print_prune_plan(config, plan, state, dry_run=dry_run)
    if dry_run:
        print("Dry-run: no retention deletes were performed.")
        return plan
    if plan.delete and not yes_delete:
        raise RuntimeError("Refusing to delete without --yes-delete")
    deleted = 0
    source_cache_runner = (
        SourceRunner.from_config(config)
        if plan.delete and config.source.cleanup_superseded_cache and config.source.cache_root
        else None
    )
    source_cache_index = (
        inventory.build_source_btrfs_index(
            source_cache_runner,
            config.source.cache_root,
            sudo=config.source.sudo,
            btrfs_command=config.source.btrfs_command,
            include_root=True,
        )
        if source_cache_runner and config.source.cache_root
        else None
    )
    if source_cache_index is not None:
        print()
        print(f"Source send-cache index: {len(source_cache_index.by_path)} indexed subvolume(s) below {source_cache_index.root}")
    for name in sorted(plan.delete):
        if _delete_prune_item(config, state, plan, source_cache_runner, name, source_cache_index=source_cache_index):
            deleted += 1
    save_state(config.state_file, state)
    summary = "\n".join(
        [
            "",
            "RETENTION DELETE SUMMARY",
            "========================",
            f"  attempted snapshots: {len(plan.delete)}",
            f"  completed snapshots: {deleted}",
            f"  retry snapshots:     {len(plan.delete) - deleted}",
            f"  remaining in state:{len(state.get('snapshots', {})):>5}",
            "",
        ]
    )
    print(summary)
    logger = get_logger()
    if logger:
        logger.success_text(summary + "\n")
    return plan
