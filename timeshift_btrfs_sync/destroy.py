"""Destructive leftover cleanup for removing a ts-btrfs setup."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os
import shlex
import subprocess

from . import btrfs
from . import payload_stats
from . import log as runlog
from . import state as state_mod
from .commands import quote_join, run_local, sudo_prefix
from .config import AppConfig
from .source import SourceRunner

PROTECTED_PATHS = {
    "/",
    "/home",
    "/mnt",
    "/media",
    "/var",
    "/run",
    "/tmp",
    "/usr",
    "/etc",
    "/root",
    "/boot",
}


@dataclass(slots=True)
class DestroyResult:
    """Result summary for one destructive cleanup root."""

    label: str
    path: str
    location: str
    exists: bool = False
    root_is_subvolume: bool = False
    subvolumes: list[str] = field(default_factory=list)
    deleted_subvolumes: int = 0
    confirmed_subvolumes: list[str] = field(default_factory=list)
    removed_tree: bool = False
    verification_required: bool = False
    verification_attempted: bool = False
    verified_root_absent: bool = False
    remaining_subvolumes: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Return True only when cleanup has no errors and required absence was verified."""

        return not self.errors and (not self.verification_required or self.verified_root_absent)


def _safe_cleanup_path(path: str | Path, label: str) -> str:
    """Return a normalized absolute path or raise for dangerous cleanup roots."""

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


def _listed_path_to_absolute(root_path: str, listed_path: str) -> str | None:
    """Convert a Btrfs-listed path back to an absolute path below root_path."""

    listed = os.path.normpath(listed_path.strip())
    if listed.startswith("/"):
        return listed if _is_under(listed, root_path) else None

    root_parts = [part for part in Path(root_path).parts if part not in {"/", ""}]
    listed_parts = [part for part in Path(listed).parts if part not in {"/", ""}]
    for index in range(len(root_parts)):
        suffix = root_parts[index:]
        if listed_parts[: len(suffix)] == suffix:
            absolute = "/" + "/".join(root_parts[:index] + listed_parts)
            return absolute if _is_under(absolute, root_path) else None
    return None


def _is_under(path: str, root: str) -> bool:
    """Return True when path is root or below root."""

    path_norm = os.path.normpath(path).rstrip("/")
    root_norm = os.path.normpath(root).rstrip("/")
    return path_norm == root_norm or path_norm.startswith(root_norm + "/")


def _sort_deepest_first(paths: list[str]) -> list[str]:
    """Return unique paths deepest first for safe Btrfs subvolume deletion."""

    return sorted(set(paths), key=lambda item: (item.count("/"), item), reverse=True)


def _collect_recursive_subvolumes(root_path: str, child_loader) -> list[str] | None:
    """List all descendant Btrfs subvolumes by walking one level at a time."""

    seen: set[str] = set()
    pending = [root_path]
    while pending:
        current = pending.pop(0)
        children = child_loader(current)
        if children is None:
            return None
        for child in children:
            if _is_under(child, root_path) and child not in seen:
                seen.add(child)
                pending.append(child)
    return _sort_deepest_first(list(seen))


def _run_quiet(cmd: list[str], *, env: dict[str, str] | None = None):
    """Run a probe/delete command quietly but record it in active run logs."""

    try:
        result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, env=env)
    except FileNotFoundError as exc:
        result = subprocess.CompletedProcess(cmd, 127, "", str(exc))
    logger = runlog.get_logger()
    if logger:
        logger.completed(cmd, result.returncode, result.stdout, result.stderr)
    return result


def _run_source_quiet(source: SourceRunner, source_command: str):
    """Run one source command quietly for structured destroy output."""

    return _run_quiet(source.command(source_command), env=source.environment())


def _path_exists_status(result) -> tuple[bool | None, str]:
    """Return True/False for test -e, or None when the check itself failed."""

    if result.returncode == 0:
        return True, ""
    if result.returncode == 1:
        return False, ""
    return None, result.stderr.strip() or result.stdout.strip() or f"return code {result.returncode}"


def _local_exists(path: str, sudo: str) -> tuple[bool | None, str]:
    """Return local path existence status, using sudo if configured."""

    return _path_exists_status(_run_quiet(sudo_prefix(sudo) + ["test", "-e", path]))


def _source_exists(source: SourceRunner, path: str, sudo: str) -> tuple[bool | None, str]:
    """Return source path existence status without sudo.

    Source-side sudoers is intentionally narrow and should only need
    passwordless ``btrfs`` and ``timeshift``. Existence checks use the source
    user's normal shell permissions instead of ``sudo test``.
    """

    result = _run_source_quiet(source, "test -e " + shlex.quote(path))
    return _path_exists_status(result)


def _local_subvolume_meta(path: str, sudo: str, btrfs_command: str):
    """Return local Btrfs subvolume metadata, or None for ordinary/missing paths."""

    result = _run_quiet(btrfs.local_btrfs_cmd(sudo, btrfs_command, ["subvolume", "show", path]))
    return btrfs.parse_subvolume_show(result.stdout, Path(path).name, path) if result.returncode == 0 else None


def _source_subvolume_meta(source: SourceRunner, path: str, sudo: str, btrfs_command: str):
    """Return source Btrfs subvolume metadata, or None for ordinary/missing paths."""

    result = _run_source_quiet(source, btrfs.remote_btrfs_cmd(sudo, btrfs_command, ["subvolume", "show", path]))
    return btrfs.parse_subvolume_show(result.stdout, Path(path).name, path) if result.returncode == 0 else None


def _local_child_subvolumes(path: str, sudo: str, btrfs_command: str) -> list[str] | None:
    """Return absolute local child subvolume paths below path."""

    result = _run_quiet(btrfs.local_btrfs_cmd(sudo, btrfs_command, ["subvolume", "list", "-o", path]))
    if result.returncode != 0:
        return None
    converted = [_listed_path_to_absolute(path, item) for item in btrfs._subvolume_list_paths(result.stdout)]
    return [item for item in converted if item]


def _source_child_subvolumes(source: SourceRunner, path: str, sudo: str, btrfs_command: str) -> list[str] | None:
    """Return absolute source child subvolume paths below path."""

    result = _run_source_quiet(source, btrfs.remote_btrfs_cmd(sudo, btrfs_command, ["subvolume", "list", "-o", path]))
    if result.returncode != 0:
        return None
    converted = [_listed_path_to_absolute(path, item) for item in btrfs._subvolume_list_paths(result.stdout)]
    return [item for item in converted if item]


def _confirm_or_raise(prompt: str, expected: str) -> None:
    """Require an exact typed confirmation."""

    answer = input(prompt).strip()
    if answer != expected:
        raise RuntimeError("Confirmation did not match; destructive cleanup aborted")


def _append_delete_count_error(result: DestroyResult) -> None:
    """Require an exact confirmed deletion result for every planned subvolume."""

    planned_paths = list(dict.fromkeys(result.subvolumes))
    confirmed_paths = list(dict.fromkeys(result.confirmed_subvolumes))
    result.deleted_subvolumes = len(confirmed_paths)

    missing = [path for path in planned_paths if path not in set(confirmed_paths)]
    unexpected = [path for path in confirmed_paths if path not in set(planned_paths)]
    if not missing and not unexpected:
        return

    if not confirmed_paths and planned_paths:
        result.errors.append(
            f"no subvolume deletions were confirmed; planned {len(planned_paths)}, confirmed 0"
        )
    else:
        result.errors.append(
            "not every planned subvolume deletion was confirmed; "
            f"planned {len(planned_paths)}, confirmed {len(confirmed_paths)}"
        )
    if missing:
        result.errors.append("unconfirmed planned subvolume deletion(s): " + ", ".join(missing))
    if unexpected:
        result.errors.append("unexpected confirmed subvolume deletion(s): " + ", ".join(unexpected))


def _inventory_remaining_local_subvolumes(
    path: str,
    sudo: str,
    btrfs_command: str,
) -> tuple[list[str], str]:
    """Rebuild a local Btrfs index below a root that still exists."""

    root_meta = _local_subvolume_meta(path, sudo, btrfs_command)
    children = _collect_recursive_subvolumes(
        path,
        lambda current: _local_child_subvolumes(current, sudo, btrfs_command),
    )
    if children is None:
        return [], "could not rebuild the local Btrfs index for the remaining configured root"
    remaining = list(children)
    if root_meta is not None:
        remaining.append(path)
    return _sort_deepest_first(remaining), ""


def _inventory_remaining_source_subvolumes(
    source: SourceRunner,
    path: str,
    sudo: str,
    btrfs_command: str,
) -> tuple[list[str], str]:
    """Rebuild a source Btrfs index below a cache root that still exists."""

    root_meta = _source_subvolume_meta(source, path, sudo, btrfs_command)
    children = _collect_recursive_subvolumes(
        path,
        lambda current: _source_child_subvolumes(source, current, sudo, btrfs_command),
    )
    if children is None:
        return [], "could not rebuild the source Btrfs index for the remaining configured root"
    remaining = list(children)
    if root_meta is not None:
        remaining.append(path)
    return _sort_deepest_first(remaining), ""


def _verify_local_root_absent(
    result: DestroyResult,
    sudo: str,
    btrfs_command: str,
) -> None:
    """Verify the configured local root is gone and inventory anything remaining."""

    result.verification_attempted = True
    exists, exists_error = _local_exists(result.path, sudo)
    if exists is None:
        result.errors.append(f"final configured-root existence check failed: {exists_error}")
        return
    if not exists:
        result.verified_root_absent = True
        result.removed_tree = True
        return

    result.errors.append(f"configured destination root still exists after deletion: {result.path}")
    remaining, inventory_error = _inventory_remaining_local_subvolumes(result.path, sudo, btrfs_command)
    result.remaining_subvolumes = remaining
    if inventory_error:
        result.errors.append(inventory_error)
    if remaining:
        result.errors.append(f"remaining destination Btrfs subvolumes: {len(remaining)}")


def _verify_source_root_absent(
    result: DestroyResult,
    source: SourceRunner,
    sudo: str,
    btrfs_command: str,
) -> None:
    """Verify the configured source-cache root is gone and inventory leftovers."""

    result.verification_attempted = True
    exists, exists_error = _source_exists(source, result.path, sudo)
    if exists is None:
        result.errors.append(f"final configured-root existence check failed: {exists_error}")
        return

    # A normal shell test can report false when the unprivileged source account
    # cannot traverse a parent. Confirm absence with the configured Btrfs command
    # before accepting that result.
    root_meta = _source_subvolume_meta(source, result.path, sudo, btrfs_command)
    if not exists and root_meta is None:
        result.verified_root_absent = True
        result.removed_tree = True
        return

    result.errors.append(f"configured source cache root still exists after deletion: {result.path}")
    remaining, inventory_error = _inventory_remaining_source_subvolumes(
        source,
        result.path,
        sudo,
        btrfs_command,
    )
    result.remaining_subvolumes = remaining
    if inventory_error:
        result.errors.append(inventory_error)
    if remaining:
        result.errors.append(f"remaining source Btrfs subvolumes: {len(remaining)}")


def _delete_local_tree(path: str, sudo: str, btrfs_command: str, *, dry_run: bool, label: str) -> DestroyResult:
    """Delete one local managed tree using Btrfs subvolume deletion only.

    A configured ordinary directory is never recursively removed. An empty
    ordinary root may be removed with ``rmdir``; a non-empty ordinary root is a
    layout/safety error that requires manual inspection.
    """

    result = DestroyResult(
        label=label,
        path=path,
        location="destination",
        verification_required=not dry_run,
    )
    print(f"  checking destination path existence: {path}", flush=True)
    exists, exists_error = _local_exists(path, sudo)
    if exists is None:
        result.errors.append(f"could not check local path existence: {exists_error}")
        return result
    result.exists = exists
    if not result.exists:
        if not dry_run:
            result.verification_attempted = True
            result.verified_root_absent = True
        return result

    meta = _local_subvolume_meta(path, sudo, btrfs_command)
    result.root_is_subvolume = meta is not None
    if not result.root_is_subvolume:
        try:
            nonempty = any(Path(path).iterdir())
        except OSError as exc:
            result.errors.append(f"could not inspect ordinary destination root {path}: {exc}")
            return result
        if nonempty:
            result.errors.append(
                "configured destination root is an ordinary non-empty directory. "
                "Recursive ordinary deletion is disabled; inspect and remove or migrate it manually: "
                + path
            )
            return result
        if dry_run:
            return result
        try:
            Path(path).rmdir()
        except OSError as exc:
            result.errors.append(f"failed removing empty ordinary destination root {path}: {exc}")
        _verify_local_root_absent(result, sudo, btrfs_command)
        return result

    print(f"  discovering destination Btrfs subvolumes below: {path}", flush=True)
    children = _collect_recursive_subvolumes(path, lambda current: _local_child_subvolumes(current, sudo, btrfs_command))
    if children is None:
        result.errors.append("could not recursively list local child subvolumes")
        return result

    result.subvolumes = _sort_deepest_first(children + [path])
    print(f"  discovered destination subvolumes: {len(result.subvolumes)}", flush=True)
    if dry_run:
        return result

    print(f"  deleting destination subvolumes deepest-first: {len(result.subvolumes)}", flush=True)
    for subvol in result.subvolumes:
        try:
            btrfs.delete_local_subvolume(Path(subvol), sudo, btrfs_command)
            result.confirmed_subvolumes.append(subvol)
        except Exception as exc:
            result.errors.append(f"failed deleting local subvolume {subvol}: {exc}")
    _append_delete_count_error(result)
    _verify_local_root_absent(result, sudo, btrfs_command)
    return result



def _source_delete_subvolumes_batched(
    source: SourceRunner,
    paths: list[str],
    sudo: str,
    btrfs_command: str,
    *,
    protected_snapshot_root: str | None = None,
) -> tuple[list[str], list[str]]:
    """Delete many source Btrfs subvolumes in one source command.

    Refuse the complete batch if any path is ``source.snapshot_root`` or below
    it. The remote shell contains only guarded ``btrfs subvolume delete``
    operations; it never deletes ordinary cache files or directories.
    """

    if not paths:
        return [], []
    protected = [path for path in paths if btrfs.path_is_same_or_under(path, protected_snapshot_root)]
    if protected:
        return [], [
            "refusing to delete Timeshift-owned source.snapshot_root path(s): "
            + ", ".join(protected)
            + f"; protected root: {protected_snapshot_root}"
        ]
    sudo_words = " ".join(shlex.quote(part) for part in sudo_prefix(sudo))
    path_lines = "\n".join(paths)
    script = f"""
sudo_words={shlex.quote(sudo_words)}
btrfs_cmd={shlex.quote(btrfs_command)}
run_btrfs() {{
    if [ -n "$sudo_words" ]; then
        # shellcheck disable=SC2086
        $sudo_words "$btrfs_cmd" "$@"
    else
        "$btrfs_cmd" "$@"
    fi
}}
while IFS= read -r subvol; do
    [ -n "$subvol" ] || continue
    output=$(run_btrfs subvolume delete "$subvol" 2>&1)
    status=$?
    if [ "$status" -eq 0 ]; then
        echo "TSBTRFS_DELETED\t$subvol"
    else
        safe_output=$(printf '%s' "$output" | tr '\n' ' ')
        echo "TSBTRFS_DELETE_ERROR\t$subvol\t$safe_output"
    fi
done <<'TSBTRFS_PATHS'
{path_lines}
TSBTRFS_PATHS
""".strip()
    result = _run_source_quiet(source, "sh -c " + shlex.quote(script))
    confirmed: list[str] = []
    confirmed_set: set[str] = set()
    expected = set(paths)
    errors: list[str] = []
    if result.returncode != 0:
        errors.append(result.stderr.strip() or result.stdout.strip() or f"return code {result.returncode}")
        return confirmed, errors
    for line in result.stdout.splitlines():
        if line.startswith("TSBTRFS_DELETED\t"):
            subvol = line.split("\t", 1)[1]
            if subvol not in expected:
                errors.append(f"unexpected deletion confirmation for source subvolume {subvol}")
            elif subvol in confirmed_set:
                errors.append(f"duplicate deletion confirmation for source subvolume {subvol}")
            else:
                confirmed.append(subvol)
                confirmed_set.add(subvol)
        elif line.startswith("TSBTRFS_DELETE_ERROR\t"):
            parts = line.split("\t", 2)
            if len(parts) == 3:
                _tag, subvol, detail = parts
                errors.append(f"failed deleting source subvolume {subvol}: {detail}")
            else:
                errors.append(f"malformed source deletion error line: {line}")
    return confirmed, errors

def _delete_source_tree(
    source: SourceRunner,
    path: str,
    sudo: str,
    btrfs_command: str,
    *,
    dry_run: bool,
    label: str,
    protected_snapshot_root: str | None = None,
) -> DestroyResult:
    """Delete one app-owned source-cache tree using Btrfs only.

    ``source.snapshot_root`` is always protected. A configured ordinary
    non-empty cache root is refused and must be inspected manually. An empty
    ordinary root may be removed with the source user's normal ``rmdir``.
    """

    result = DestroyResult(
        label=label,
        path=path,
        location="source",
        verification_required=not dry_run,
    )
    if btrfs.path_is_same_or_under(path, protected_snapshot_root):
        result.errors.append(
            f"refusing to destroy Timeshift-owned source.snapshot_root path {path}; "
            f"protected root: {protected_snapshot_root}"
        )
        return result

    print(f"  checking source Btrfs subvolume status: {path}", flush=True)
    root_meta = _source_subvolume_meta(source, path, sudo, btrfs_command)
    result.root_is_subvolume = root_meta is not None
    if not result.root_is_subvolume:
        print(f"  checking source shell path existence: {path}", flush=True)
        exists, exists_error = _source_exists(source, path, sudo)
        if exists is None:
            result.errors.append(f"could not check source path existence: {exists_error}")
            return result
        result.exists = exists
        if not result.exists:
            if not dry_run:
                result.verification_attempted = True
                result.verified_root_absent = True
            return result
        inspect_script = f"""
path={shlex.quote(path)}
nonempty=0
for child in "$path"/* "$path"/.[!.]* "$path"/..?*; do
    [ -e "$child" ] || continue
    nonempty=1
    break
done
if [ "$nonempty" -eq 1 ]; then
    echo TSBTRFS_ORDINARY_NONEMPTY
    exit 3
fi
exit 0
""".strip()
        inspected = _run_source_quiet(source, "sh -c " + shlex.quote(inspect_script))
        if inspected.returncode == 3:
            result.errors.append(
                "configured source cache root is an ordinary non-empty directory. "
                "Recursive ordinary deletion is disabled; inspect and remove or migrate it manually: "
                + path
            )
            return result
        if inspected.returncode != 0:
            result.errors.append(
                f"could not inspect ordinary source cache root {path}: "
                f"{inspected.stderr.strip() or inspected.stdout.strip() or inspected.returncode}"
            )
            return result
        if dry_run:
            return result
        removed = _run_source_quiet(source, quote_join(["rmdir", "--", path]))
        if removed.returncode != 0:
            result.errors.append(
                f"failed removing empty ordinary source cache root {path}: "
                f"{removed.stderr.strip() or removed.stdout.strip() or removed.returncode}"
            )
        _verify_source_root_absent(result, source, sudo, btrfs_command)
        return result

    result.exists = True
    print(f"  discovering source Btrfs subvolumes below: {path}", flush=True)
    children = _collect_recursive_subvolumes(
        path,
        lambda current: _source_child_subvolumes(source, current, sudo, btrfs_command),
    )
    if children is None:
        result.errors.append("could not recursively list source child subvolumes")
        return result

    result.subvolumes = _sort_deepest_first(children + [path])
    print(f"  discovered source subvolumes: {len(result.subvolumes)}", flush=True)
    if dry_run:
        return result

    print(f"  deleting source subvolumes deepest-first in one source command: {len(result.subvolumes)}", flush=True)
    confirmed, errors = _source_delete_subvolumes_batched(
        source,
        result.subvolumes,
        sudo,
        btrfs_command,
        protected_snapshot_root=protected_snapshot_root,
    )
    result.confirmed_subvolumes = confirmed
    result.errors.extend(errors)
    _append_delete_count_error(result)
    _verify_source_root_absent(result, source, sudo, btrfs_command)
    return result

def _mode_text(delete_source: bool, delete_destination: bool) -> str:
    """Return uppercase confirmation text for the selected destroy mode."""

    if delete_source and delete_destination:
        return "DELETE BOTH"
    if delete_source:
        return "DELETE SOURCE"
    return "DELETE DESTINATION"


def _print_target(label: str, path: str) -> None:
    """Print one destroy target path."""

    print(f"{label}:")
    print(f"  {path}")


def _print_result(result: DestroyResult, *, dry_run: bool) -> None:
    """Print one target cleanup result."""

    action = "would delete" if dry_run else "deleted"
    print(f"{result.label}:")
    print(f"  path:       {result.path}")
    if not result.exists:
        if not dry_run:
            print(f"  verified configured root absent: {'yes' if result.verified_root_absent else 'no'}")
        if result.success:
            print("  result:     already missing")
        else:
            print("  result:     incomplete")
            for error in result.errors:
                print(f"    error: {error}")
        return
    print(f"  subvolumes: {len(result.subvolumes)}")
    if dry_run:
        for path in result.subvolumes:
            print(f"    would delete subvolume: {path}")
        if result.root_is_subvolume:
            print(f"  result:     {action} the configured Btrfs root after its child subvolumes")
        else:
            print(f"  result:     {action} the configured root only if it is an empty ordinary directory")
        return
    print(f"  deleted subvolumes: {result.deleted_subvolumes}")
    print(f"  verified configured root absent: {'yes' if result.verified_root_absent else 'no'}")
    if result.remaining_subvolumes:
        print("  remaining Btrfs subvolumes:")
        for remaining in result.remaining_subvolumes:
            print(f"    {remaining}")
    if result.success:
        print("  result:     complete")
    else:
        print("  result:     incomplete")
        for error in result.errors:
            print(f"    error: {error}")


def _result_by_label(results: list[DestroyResult], label: str) -> DestroyResult | None:
    """Return a result by printed target label."""

    for result in results:
        if result.label == label and result.exists:
            return result
    return None


def _load_payload_state(config: AppConfig) -> dict | None:
    """Load state for payload explanation only, or None when unavailable.

    destroy-leftovers deliberately does not use state.json to decide what to
    delete. This read is only for explaining normalized source/destination
    payload statistics, especially when v0.1.2 direct read-only Timeshift sends
    mean valid source payload may live outside source.cache_root.
    """

    try:
        return state_mod.load_state(
            config.state_file,
            config.destination.target_root,
            snapshot_root=config.source.snapshot_root,
            cache_root=config.source.cache_root,
        )
    except Exception:
        return None


def _print_payload_match_if_available(config: AppConfig, results: list[DestroyResult], state_doc: dict | None) -> None:
    """Print normalized source/destination payload counts when both sides were selected."""

    source = _result_by_label(results, "Source send-cache root")
    destination = _result_by_label(results, "Destination target_root")
    if source is None or destination is None:
        return
    cache_stats = payload_stats.source_send_cache_stats(source.path, source.subvolumes, config.source.subvolumes)
    direct_stats = None
    if state_doc is not None:
        direct_stats = payload_stats.direct_send_payload_stats(
            state_doc,
            config.source.subvolumes,
            cache_root=config.source.cache_root,
        )
    source_stats = payload_stats.merge_source_payload_stats(cache_stats, direct_stats)
    destination_stats = payload_stats.destination_payload_stats(destination.path, destination.subvolumes, config.source.subvolumes)
    for line in payload_stats.render_payload_match(payload_stats.compare_payloads(source_stats, destination_stats)):
        print(line)
    print()


def destroy_leftovers(
    config: AppConfig,
    *,
    delete_source: bool,
    delete_destination: bool,
    dry_run: bool,
    danger_confirmed: bool,
    interactive: bool = True,
) -> list[DestroyResult]:
    """Destroy configured source/destination leftovers for retiring this app setup."""

    if not delete_source and not delete_destination:
        raise RuntimeError("Choose exactly one of --delete-source, --delete-destination, or --delete-both")

    targets: list[tuple[str, str, str]] = []
    if delete_source:
        if not config.source.cache_root:
            raise RuntimeError("--delete-source requires source.cache_root; source.snapshot_root is Timeshift-owned and is never destroyed")
        if btrfs.path_is_same_or_under(config.source.cache_root, config.source.snapshot_root):
            raise RuntimeError(
                "Refusing --delete-source because source.cache_root is source.snapshot_root or below it. "
                "source.snapshot_root is Timeshift-owned and must never be deleted, pruned, destroyed, or cleaned by this app."
            )
        targets.append(("Source send-cache root", _safe_cleanup_path(config.source.cache_root, "source.cache_root"), "source"))
    if delete_destination:
        targets.append(("Destination target_root", _safe_cleanup_path(config.destination.target_root, "destination.target_root"), "destination"))

    mode_text = _mode_text(delete_source, delete_destination)
    print("DESTRUCTIVE LEFTOVER CLEANUP")
    print("============================")
    print("This command is for permanently removing a ts-btrfs setup.")
    print("It ignores state.json and retention rules.")
    print("It recursively deletes managed Btrfs subvolumes deepest-first.")
    print("It only deletes app-created source send-cache paths when --delete-source is used.")
    print("It must never delete, prune, destroy, or clean source.snapshot_root or anything below it.")
    print()
    print(f"Run mode: {'dry-run' if dry_run else 'REAL DELETION'}")
    print(f"Selected mode: {mode_text}")
    print(f"Configured job: {config.name}")
    print()
    for label, path, _ in targets:
        _print_target(label, path)
    print()

    if not dry_run:
        if not danger_confirmed:
            raise RuntimeError("Real destroy-leftovers requires --i-understand-this-destroys-data")
        if interactive:
            _confirm_or_raise(f"Type {mode_text} to continue: ", mode_text)
            _confirm_or_raise(f"Type the configured job name ({config.name}) to continue: ", config.name)

    source = SourceRunner.from_config(config) if delete_source else None
    payload_state = _load_payload_state(config) if delete_source and delete_destination else None

    results: list[DestroyResult] = []
    print("DESTROY PLAN" if dry_run else "DESTROY EXECUTION")
    print("============" if dry_run else "=================")
    for label, path, location in targets:
        print(f"Starting cleanup target: {label}", flush=True)
        print(f"  location: {location}", flush=True)
        print(f"  path:     {path}", flush=True)
        if location == "source":
            assert source is not None
            result = _delete_source_tree(
                source,
                path,
                config.source.sudo,
                config.source.btrfs_command,
                dry_run=dry_run,
                label=label,
                protected_snapshot_root=config.source.snapshot_root,
            )
        else:
            result = _delete_local_tree(
                path,
                config.destination.sudo,
                config.destination.btrfs_command,
                dry_run=dry_run,
                label=label,
            )
        results.append(result)
        _print_result(result, dry_run=dry_run)
        print()

    _print_payload_match_if_available(config, results, payload_state)

    failures = [result for result in results if not result.success]
    print("DESTROY SUMMARY")
    print("===============")
    print(f"  targets:    {len(results)}")
    print(f"  complete:   {len(results) - len(failures)}")
    print(f"  incomplete: {len(failures)}")
    if failures:
        raise RuntimeError("destroy-leftovers finished with incomplete target cleanup; inspect errors above and rerun after fixing them")
    return results
