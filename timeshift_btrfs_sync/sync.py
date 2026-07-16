"""Main destination-pull sync workflow.

The important performance/safety rule in this version is:

* Discovery is fast and only uses Timeshift names plus configured subvolume
  names. It does not run `btrfs subvolume show` for every snapshot unless
  source.verify_subvolumes_at_discovery is enabled.
* Before the first real incremental send for each subvolume name in a run, the
  selected parent is always verified with Btrfs metadata on both sides. Later
  incrementals in the same run reuse that verified chain and only refresh local
  destination metadata after receive.
"""

from __future__ import annotations

from pathlib import Path
import os
import tempfile
from . import btrfs, timeshift
from . import preflight, remote_index
from .commands import CommandError, stream_pipeline
from .config import AppConfig
from .models import SnapshotMeta, SubvolumeMeta, tags_text
from .source import SourceRunner
from .log import emit_success_summary
from .retention import initial_sync_keep_names
from .state import (
    latest_synced_before,
    mark_subvolume_synced,
    normalize_state_paths,
    refresh_state_metadata_and_report,
    remove_snapshot_from_state,
    resolve_destination_path,
    resolve_state_send_path,
    save_state,
    state_send_path_is_app_cache,
    snapshot_is_synced,
)


class SyncError(RuntimeError):
    """Raised for sync safety errors."""


def _local_meta(config: AppConfig, path: str | Path, name: str, required: bool = True) -> SubvolumeMeta | None:
    return btrfs.get_subvolume_meta("local", path, name, config.destination.sudo, config.destination.btrfs_command, required=required)


def _source_meta(
    config: AppConfig,
    source: SourceRunner,
    path: str | Path,
    name: str,
    required: bool = True,
    *,
    source_snapshot_index: remote_index.BtrfsIndex | None = None,
    source_cache_index: remote_index.BtrfsIndex | None = None,
) -> SubvolumeMeta | None:
    """Return source metadata, preferring bulk indexes over one-off probes."""

    path_text = str(path)
    if source_cache_index is not None and btrfs.path_is_under_cache(path_text, config.source.cache_root):
        indexed = source_cache_index.meta(path_text)
        if indexed is not None:
            return indexed
    if source_snapshot_index is not None:
        indexed = source_snapshot_index.meta(path_text)
        if indexed is not None:
            return indexed
    return btrfs.source_get_subvolume_meta(source, path, name, config.source.sudo, config.source.btrfs_command, required=required)


def _human_blank() -> None:
    """Print one blank line to separate human-readable status blocks."""

    print()


def _human_rule(text: str = "----") -> None:
    """Print a visual separator with blank lines around it."""

    print()
    print(text)
    print()



def _record_sync_event(
    events: list[dict],
    *,
    mode: str,
    snapshot: SnapshotMeta,
    subvolume_name: str,
    source_path: str,
    destination_path: Path,
    parent_name: str | None,
    parent_send_path: str | None,
    status: str,
) -> None:
    """Add one planned or completed transfer to the run summary."""

    events.append(
        {
            "mode": mode,
            "snapshot": snapshot.name,
            "tags": tags_text(snapshot.tags),
            "subvolume": subvolume_name,
            "source": source_path,
            "destination": str(destination_path),
            "parent": parent_name or "-",
            "parent_source": parent_send_path or "-",
            "status": status,
        }
    )


def _print_sync_summary(
    events: list[dict],
    *,
    dry_run: bool,
    skipped_by_floor: int,
    already_synced: int,
) -> None:
    """Write a terminal-friendly transfer summary to terminal and .succes.

    The readable statistics intentionally go to the separate .succes file, not
    the normal .log file. Mail uses .succes as the plain-text success body.
    """

    full_count = sum(1 for event in events if event.get("mode") == "full")
    incremental_count = sum(1 for event in events if event.get("mode") == "incremental")
    mode_text = "dry-run plan" if dry_run else "completed transfers"
    lines = [
        "SYNC SUMMARY",
        "============",
        f"  mode:              {mode_text}",
        f"  full syncs:        {full_count}",
        f"  incremental syncs: {incremental_count}",
        f"  total listed:      {len(events)}",
        f"  already synced:    {already_synced}",
        f"  skipped by floor:  {skipped_by_floor}",
    ]

    if not events:
        lines += ["  transfers:         none", ""]
        emit_success_summary("\n".join(lines))
        return

    lines += ["", "SYNC TRANSFERS", "--------------"]
    for event in events:
        action = "FULL SYNC" if event["mode"] == "full" else "INCREMENTAL SYNC"
        if dry_run:
            action = "WOULD " + action
        lines.append(f"  [{action}] {event['snapshot']}  subvol={event['subvolume']}  tags={event['tags']}")
        lines.append(f"      parent:      {event['parent']}")
        if event["parent_source"] != "-":
            lines.append(f"      parent path: {event['parent_source']}")
        lines.append(f"      source:      {event['source']}")
        lines.append(f"      destination: {event['destination']}")
    lines.append("")
    emit_success_summary("\n".join(lines))

def prepare_destination(config: AppConfig) -> None:
    """Create/validate destination helper folders before writes.

    The destination target root itself is handled by sync path preflight. Helper
    folders such as ``snapshots/``, the state/lock directory, and optional
    ``log_dir`` are accepted as either ordinary directories or Btrfs subvolumes.
    When missing, the app tries ``btrfs subvolume create`` first and falls back
    to mkdir if Btrfs creation is not possible at that location.
    """

    root = config.destination.target_root
    if not root.exists():
        raise SyncError(f"Destination target_root was not created by preflight: {root}")
    if not root.is_dir():
        raise SyncError(f"Destination target_root exists but is not a directory: {root}")
    try:
        preflight.prepare_destination_helper_paths(config, dry_run=False)
    except preflight.PathPreflightError as exc:
        raise SyncError(str(exc)) from exc


def list_source_snapshots(
    config: AppConfig,
    source: SourceRunner,
    *,
    include_btrfs_info: bool = True,
    source_snapshot_index: remote_index.BtrfsIndex | None = None,
    timeshift_output: str | None = None,
) -> list[SnapshotMeta]:
    """Discover source Timeshift snapshots."""

    return timeshift.list_source_snapshots(
        source,
        snapshot_root=config.source.snapshot_root,
        subvolumes=config.source.subvolumes,
        sudo=config.source.sudo,
        timeshift_command=config.source.timeshift_command,
        btrfs_command=config.source.btrfs_command,
        include_btrfs_info=include_btrfs_info,
        btrfs_index=source_snapshot_index,
        timeshift_output=timeshift_output,
    )


def source_snapshot_index(snapshots) -> dict[str, SnapshotMeta]:
    return {snap.name: snap for snap in snapshots if snap.subvolumes}


def _snapshots_from_source_inventory(
    config: AppConfig,
    source: SourceRunner,
    inventory: remote_index.SourceInventory,
) -> dict[str, SnapshotMeta]:
    """Build Timeshift snapshot objects from one coherent source inventory."""

    return source_snapshot_index(
        list_source_snapshots(
            config,
            source,
            include_btrfs_info=config.source.verify_subvolumes_at_discovery,
            source_snapshot_index=inventory.snapshot_index,
            timeshift_output=inventory.timeshift_output,
        )
    )


def _required_pipeline_source_changes(
    before: remote_index.SourceInventory,
    after: remote_index.SourceInventory,
    *,
    current_path: str,
    parent_path: str | None,
    additional_paths: tuple[tuple[str, str | None], ...] = (),
) -> list[str]:
    """Return identity changes to source paths required by current work.

    Unrelated Timeshift churn is not enough to reinterpret a network, mbuffer,
    cache-creation, or destination failure as a source-change retry. Automatic
    continuation is allowed only when a path required by the failed operation
    disappeared or changed Btrfs UUID between coherent inventory generations.
    """

    changes: list[str] = []
    required_paths = (
        ("current send path", current_path),
        ("incremental parent path", parent_path),
        *additional_paths,
    )
    seen: set[str] = set()
    for label, path in required_paths:
        if not path or path in seen:
            continue
        seen.add(path)
        old_meta = before.meta(path)
        new_meta = after.meta(path)
        if old_meta is not None and new_meta is None:
            changes.append(f"{label} disappeared: {path}")
            continue
        if old_meta is not None and new_meta is not None and old_meta.uuid and new_meta.uuid != old_meta.uuid:
            changes.append(
                f"{label} UUID changed: {path}: {old_meta.uuid} -> {new_meta.uuid or '-'}"
            )
    return changes


def confirm_source_identity_before_manual_snapshot(
    config: AppConfig,
    source: SourceRunner,
    state: dict,
    source_by_name: dict[str, SnapshotMeta] | None = None,
    load_source_index=None,
    source_cache_index: remote_index.BtrfsIndex | None = None,
    source_snapshot_index: remote_index.BtrfsIndex | None = None,
    destination_index: remote_index.BtrfsIndex | None = None,
) -> tuple[str | None, str]:
    """Print and enforce the shared manual-snapshot source identity guard."""

    print("MANUAL SNAPSHOT SOURCE IDENTITY CHECK")
    if not _destination_has_existing_snapshots(config):
        print("  destination: no existing snapshots found")
        print("  first full seed is allowed; later snapshots in the same run become incremental")
        return None, "empty destination; first full seed allowed"

    print("  destination: existing snapshots found")
    print("  checking existing source Timeshift list against state.json UUID history")
    if source_by_name is None:
        if load_source_index is None:
            raise SyncError("Internal error: source Timeshift index is required for manual snapshot identity check")
        source_by_name = load_source_index()

    confirmed_name, reason = _find_confirmed_sync_floor(
        config,
        source,
        state,
        source_by_name,
        source_cache_index=source_cache_index,
        source_snapshot_index=source_snapshot_index,
        destination_index=destination_index,
    )
    if not confirmed_name:
        raise SyncError(
            "Refusing to create manual Timeshift snapshot.\n\n"
            "Source and destination do not match in any UUID-confirmed snapshot. "
            "The configured source could not be matched to any already received "
            "snapshot in state.json.\n"
            "This may be the wrong mounted OS, wrong snapshot_root, wrong source host, "
            "or a backup target from another source.\n"
            f"Reason: {reason}\n\n"
            "Use an empty/separate target_root for a new full backup, or repair "
            "state/cache so a matching source/destination parent can be proven."
        )
    print(f"  confirmed source anchor: {confirmed_name}")
    print(f"  reason: {reason}")
    return confirmed_name, reason



def _is_app_manual_snapshot(snapshot: SnapshotMeta, marker: str) -> bool:
    """Return True for source Timeshift O snapshots created by this app.

    The app cannot rely on state.json for interrupted runs, because an on-demand
    snapshot may have been created before any destination receive completed. The
    source Timeshift list still contains the comment/tag, so this source-side
    check lets the next run notice older pending app-created snapshots and keep
    them in the normal oldest-to-newest send order.
    """

    marker_text = (marker or "").strip().lower()
    if not marker_text:
        return False
    return "O" in snapshot.tags and marker_text in str(snapshot.comment or "").lower()


def _pending_app_manual_snapshots(
    config: AppConfig,
    state: dict,
    source_by_name: dict[str, SnapshotMeta],
) -> list[SnapshotMeta]:
    """Return app-created on-demand snapshots that still need syncing.

    This protects interrupted retry behavior. If a previous run created an
    automatic Timeshift on-demand snapshot and then failed before completing the
    send/receive, the next run should still process that existing source
    snapshot in normal oldest-to-newest order. It must not suppress creation of
    a fresh on-demand snapshot, because the previous one may be old.
    """

    pending: list[SnapshotMeta] = []
    for snapshot in source_by_name.values():
        if not _is_app_manual_snapshot(snapshot, config.manual_snapshot.marker):
            continue
        expected = [name for name in config.source.subvolumes if name in snapshot.subvolumes]
        if not expected:
            continue
        if not snapshot_is_synced(state, snapshot.name, expected):
            pending.append(snapshot)
    return _snapshots_in_sync_order(pending)

def _maybe_create_manual_snapshot(
    config: AppConfig,
    source: SourceRunner,
    *,
    state: dict,
    source_by_name: dict[str, SnapshotMeta],
    dry_run: bool,
    only_snapshot: str | None,
    source_cache_index: remote_index.BtrfsIndex | None = None,
    source_snapshot_index: remote_index.BtrfsIndex | None = None,
    destination_index: remote_index.BtrfsIndex | None = None,
) -> bool:
    """Optionally create a source Timeshift tag O snapshot before sync.

    This function only creates the source-side Timeshift snapshot. It never
    sends it directly and never turns it into a special targeted sync. After a
    real creation the caller must re-read ``timeshift --list``; the newly
    created snapshot is then handled by the normal oldest-to-newest sync loop,
    exactly like any other Timeshift snapshot.

    For safety, the source list is read before this function is called. If the
    destination already contains snapshots, the app walks state.json
    newest-to-oldest and requires a UUID-confirmed match between the configured
    source and an already received destination snapshot before it asks Timeshift
    to create a new snapshot. If the destination is empty, the first full seed
    is allowed.

    Returns True only when a real source snapshot was created and the caller
    should read `timeshift --list` again.
    """

    manual = config.manual_snapshot
    if not manual.enabled:
        return False
    if only_snapshot:
        print("Manual snapshot creation: skipped because --snapshot was specified.")
        _human_rule("----")
        return False

    pending_manual = _pending_app_manual_snapshots(config, state, source_by_name)
    if pending_manual:
        _human_blank()
        print("PENDING APP ON-DEMAND SNAPSHOT(S)")
        print(f"  existing pending: {', '.join(snapshot.name for snapshot in pending_manual)}")
        print("  recovery:         they remain in the normal oldest-to-newest sync order")
        print("  create policy:    still create a fresh on-demand snapshot for this run")
        print("  reason:           the previous app-created on-demand snapshot may be old after an interrupted run")
        _human_rule("----")

    _human_blank()
    confirm_source_identity_before_manual_snapshot(
        config,
        source,
        state,
        source_by_name,
        source_cache_index=source_cache_index,
        source_snapshot_index=source_snapshot_index,
        destination_index=destination_index,
    )
    _human_rule("----")

    _human_blank()
    print("MANUAL SNAPSHOT CREATE")
    print(f"  tag:     O (Timeshift default; --tags O is intentionally omitted)")
    print(f"  comment: {manual.comment}")

    if manual.marker and manual.marker.lower() not in manual.comment.lower():
        print()
        print(f"WARNING: manual_snapshot.comment does not contain marker {manual.marker!r};")
        print("         marker-based retention may not recognize this snapshot later.")

    if dry_run:
        print()
        print("Dry-run: would run source Timeshift --create --scripted --comments ...")
        _human_rule("----")
        return False

    timeshift.create_source_manual_snapshot(
        source,
        sudo=config.source.sudo,
        timeshift_command=config.source.timeshift_command,
        comment=manual.comment,
    )
    print()
    print("Requested source Timeshift on-demand snapshot. Reading source list after creation.")
    _human_rule("----")
    return True


def _snapshots_in_sync_order(snapshots) -> list[SnapshotMeta]:
    """Return source snapshots oldest-to-newest for Btrfs send."""

    return sorted(snapshots, key=lambda s: s.sort_key())


def _select_initial_sync_snapshots(config: AppConfig, source_by_name: dict[str, SnapshotMeta]) -> list[SnapshotMeta]:
    """Return retention-kept source snapshots for a fresh destination seed."""

    keep_names = initial_sync_keep_names(config, source_by_name.values())
    selected = [source_by_name[name] for name in sorted(keep_names) if name in source_by_name]
    skipped = len(source_by_name) - len(selected)
    _human_blank()
    print("FULL SYNC RETENTION SELECTION")
    print(f"  source snapshots:  {len(source_by_name)}")
    print(f"  selected to send:  {len(selected)}")
    print(f"  skipped by rules:  {skipped}")
    if selected:
        print(f"  first selected:    {selected[0].name}")
        print(f"  newest selected:   {selected[-1].name}")
    print("  sending order:     oldest selected to newest selected")
    print("  reason:            fresh destination only receives snapshots kept by retention")
    _human_rule("----")
    return selected

def print_snapshot_table(snapshots: list[SnapshotMeta]) -> None:
    """Print source snapshots in table form."""

    if not snapshots:
        print("No source snapshots found.")
        return
    print(f"{'SNAPSHOT':<22} {'TAGS':<8} {'SUBVOLUMES':<20} COMMENT")
    for snap in snapshots:
        print(f"{snap.name:<22} {''.join(snap.tags) or '-':<8} {','.join(snap.subvolumes.keys()) or '-':<20} {snap.comment or ''}")


def _dest_subvolume_path(config: AppConfig, snapshot_name: str, subvolume_name: str) -> Path:
    """Return the final local path for one received subvolume.

    Example:
      <target_root>/snapshots/2026-06-22_18-00-01/@
    """

    return config.destination.target_root / "snapshots" / snapshot_name / subvolume_name


def _target_snapshot_dir(config: AppConfig, snapshot_name: str) -> Path:
    """Return the managed destination date subvolume passed to `btrfs receive`.

    ``btrfs receive <date-subvolume>`` creates the incoming ``@`` or
    ``@home`` child subvolume inside this app-owned Btrfs container.
    """

    return config.destination.target_root / "snapshots" / snapshot_name


def _destination_info_json_path(config: AppConfig, snapshot_name: str) -> Path:
    """Return the destination Timeshift control-file path for one snapshot."""

    return _target_snapshot_dir(config, snapshot_name) / "info.json"


def _ensure_destination_snapshot_subvolume(
    config: AppConfig,
    snapshot_name: str,
    destination_index: remote_index.BtrfsIndex | None,
) -> Path:
    """Create or validate one managed destination date subvolume.

    Every ``snapshots/<date>`` path created by this release is a Btrfs
    subvolume. Existing ordinary date folders are an unsupported legacy layout
    and are refused instead of migrated or deleted automatically.
    """

    snapshot_dir = _target_snapshot_dir(config, snapshot_name)
    if snapshot_dir.is_symlink():
        raise SyncError(f"Refusing symlinked destination snapshot date path: {snapshot_dir}")
    if snapshot_dir.exists():
        indexed = destination_index.meta(snapshot_dir) if destination_index is not None else None
        if indexed:
            return snapshot_dir
        meta = remote_index.refresh_local_path(
            destination_index,
            snapshot_dir,
            name=snapshot_dir.name,
            sudo=config.destination.sudo,
            btrfs_command=config.destination.btrfs_command,
        )
        if not meta:
            raise SyncError(
                "Unsupported legacy destination layout: snapshot date path is an ordinary directory, "
                "not a Btrfs subvolume. Move/remove it manually before retrying; automatic legacy "
                "migration and ordinary recursive deletion are intentionally disabled:\n"
                f"  {snapshot_dir}"
            )
        return snapshot_dir

    parent = snapshot_dir.parent
    if not parent.exists() or not parent.is_dir():
        raise SyncError(f"Destination snapshots parent is unavailable: {parent}")
    try:
        btrfs.create_local_subvolume(snapshot_dir, config.destination.sudo, config.destination.btrfs_command)
    except Exception as exc:
        raise SyncError(f"Could not create destination snapshot date Btrfs subvolume {snapshot_dir}: {exc}") from exc
    meta = remote_index.refresh_local_path(
        destination_index,
        snapshot_dir,
        name=snapshot_dir.name,
        sudo=config.destination.sudo,
        btrfs_command=config.destination.btrfs_command,
    )
    if not meta:
        raise SyncError(f"Destination date path was created but is not a Btrfs subvolume: {snapshot_dir}")
    print(f"  destination date subvolume: created {snapshot_dir}")
    return snapshot_dir


def _validate_destination_snapshot_layout(
    config: AppConfig,
    destination_index: remote_index.BtrfsIndex,
) -> None:
    """Refuse every existing ordinary/symlinked destination date entry."""

    snapshots_root = config.destination.target_root / "snapshots"
    if not snapshots_root.exists():
        return
    try:
        entries = list(snapshots_root.iterdir())
    except OSError as exc:
        raise SyncError(f"Could not inspect destination snapshots root {snapshots_root}: {exc}") from exc
    invalid: list[str] = []
    for entry in entries:
        if entry.is_symlink() or not entry.is_dir() or not destination_index.contains(entry):
            invalid.append(str(entry))
    if invalid:
        raise SyncError(
            "Unsupported destination layout detected. Every entry directly below destination "
            "snapshots/ must be a Btrfs date subvolume. Ordinary date folders/files and symlinks "
            "are not migrated or deleted automatically. Inspect and move/remove them manually:\n  "
            + "\n  ".join(sorted(invalid))
        )


def _atomic_write_snapshot_info_json(path: Path, content: str) -> None:
    """Atomically write one captured Timeshift ``info.json`` file.

    The temporary file is created in the destination snapshot directory so the
    final ``os.replace`` stays on the same filesystem. A failed write therefore
    leaves either the previous complete file or no file, never a partial JSON
    document under the final name.
    """

    if not path.parent.exists():
        raise OSError(f"destination snapshot date subvolume is missing: {path.parent}")
    fd, tmp_name = tempfile.mkstemp(prefix=".info.json.", suffix=".tmp", dir=str(path.parent))
    raw_fd_open = True
    try:
        os.fchmod(fd, 0o644)
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            raw_fd_open = False
            fh.write(content)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    finally:
        if raw_fd_open:
            try:
                os.close(fd)
            except OSError:
                pass
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass


def _require_snapshot_info_json(
    inventory: remote_index.SourceInventory,
    snapshot_name: str,
) -> str:
    """Return captured control-file content or raise a precise sync error."""

    if snapshot_name in inventory.snapshot_info_json:
        return inventory.snapshot_info_json[snapshot_name]
    reason = inventory.snapshot_info_errors.get(snapshot_name, "info.json was not captured")
    source_user_name = inventory.source_user_name or "unknown"
    source_user_uid = str(inventory.source_user_uid) if inventory.source_user_uid is not None else "unknown"
    account_role = (
        "remote SSH source account used by this destination"
        if inventory.snapshot_index.location == "remote"
        else "local source process account"
    )
    raise SyncError(
        "Timeshift snapshot metadata could not be copied. The app refuses to complete "
        "this snapshot without its shared control file:\n"
        f"  snapshot: {snapshot_name}\n"
        f"  source:   {inventory.snapshot_index.root}/{snapshot_name}/info.json\n"
        f"  reason:   {reason}\n"
        f"  {account_role}: {source_user_name} (uid {source_user_uid})\n\n"
        "The source inventory reads info.json with ordinary non-sudo cat permissions "
        "inside the same combined source request used for Timeshift and Btrfs discovery.\n"
        "The source Timeshift-Btrfs filesystem must be mounted at a path this account "
        "can traverse and read. The account needs execute/search permission on every "
        "parent directory and read permission on info.json. A privileged administrator "
        "can create a stable mount in /etc/fstab and grant this user access by ownership, "
        "normal mode bits, or a narrow POSIX ACL. For Btrfs, use filesystem permissions "
        "or ACLs rather than assuming uid=/gid= mount options will change ownership."
    )


def _sync_snapshot_info_json(
    config: AppConfig,
    inventory: remote_index.SourceInventory,
    snapshot_name: str,
    *,
    dry_run: bool,
) -> bool:
    """Create or refresh destination ``info.json`` for one complete snapshot.

    One Timeshift snapshot date has one shared control file beside its ``@`` and
    optional ``@home`` subvolumes. The helper is therefore called once only
    after all subvolumes configured for that date are present and marked synced.
    It also backfills or refreshes the file for already-complete snapshots.
    """

    content = _require_snapshot_info_json(inventory, snapshot_name)
    destination = _destination_info_json_path(config, snapshot_name)
    if destination.is_symlink():
        raise SyncError(f"Refusing to read or replace symlinked destination info.json: {destination}")
    existing: str | None = None
    if destination.exists():
        try:
            existing = destination.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise SyncError(f"Could not read existing destination info.json {destination}: {exc}") from exc
    if existing == content:
        return False
    if dry_run:
        action = "update" if destination.exists() else "create"
        print(f"  info.json: would {action} {destination}")
        return True
    try:
        _atomic_write_snapshot_info_json(destination, content)
    except OSError as exc:
        raise SyncError(f"Could not write destination info.json {destination}: {exc}") from exc
    action = "updated" if existing is not None else "created"
    print(f"  info.json: {action} {destination}")
    return True


def _destination_has_existing_snapshots(config: AppConfig) -> bool:
    """Return True when the destination has real received snapshot content.

    Important bug fix: an earlier version created the empty destination snapshot
    directory before selecting a parent. That empty directory made the guard
    think the destination already contained backups and it refused the first full
    send. Here we only count folders that contain at least one configured
    subvolume name, for example @ or @home.
    """

    snapshots_root = config.destination.target_root / "snapshots"
    if not snapshots_root.exists():
        return False
    for child in snapshots_root.iterdir():
        if not child.is_dir():
            continue
        for subvol_name in config.source.subvolumes:
            if (child / subvol_name).exists():
                return True
    return False



def _snapshot_destination_paths_exist(config: AppConfig, snapshot_name: str, subvolume_names: list[str]) -> bool:
    """Return True only when every expected destination subvolume path exists."""

    return all(_dest_subvolume_path(config, snapshot_name, name).exists() for name in subvolume_names)

def _preview_send_path(config: AppConfig, snapshot_name: str, subvolume: SubvolumeMeta) -> str:
    """Return the send path that would be used, without creating cache snapshots.

    Dry-run uses this so it can show paths without changing source or
    destination.
    """

    if subvolume.readonly is True:
        return subvolume.path
    if config.source.cache_root:
        return btrfs.readonly_cache_path(config.source.cache_root, snapshot_name, subvolume.name)
    return "<no-cache-root-configured>"


def _send_path_kind_text(config: AppConfig, send_path: str, original_path: str) -> str:
    """Return human text explaining who owns the selected send path."""

    if Path(send_path) == Path(original_path):
        return "Timeshift original read-only snapshot; protected from app prune"
    if btrfs.path_is_under_cache(send_path, config.source.cache_root):
        return "app-created source send-cache snapshot; prune may delete with destination retention"
    return "external read-only send path; protected from app prune"


def _ensure_source_send_path(
    config: AppConfig,
    source: SourceRunner,
    snapshot_name: str,
    subvolume: SubvolumeMeta,
    source_cache_index: remote_index.BtrfsIndex | None = None,
    source_snapshot_index: remote_index.BtrfsIndex | None = None,
) -> str:
    """Return a real read-only source path, creating cache snapshots if needed.

    This calls only source-side `sudo btrfs ...` commands. It never uses source-side
    mkdir/cat/find/helper scripts.
    """

    return btrfs.source_ensure_readonly_send_path(
        source,
        sudo=config.source.sudo,
        btrfs_command=config.source.btrfs_command,
        original_path=subvolume.path,
        cache_root=config.source.cache_root,
        snapshot_name=snapshot_name,
        subvolume_name=subvolume.name,
        create_readonly_cache=config.source.create_readonly_cache,
        cache_index=source_cache_index,
        original_index=source_snapshot_index,
    )


def _cleanup_incomplete_destination_receive(
    config: AppConfig,
    dest_path: Path,
    subvolume_name: str,
    destination_index: remote_index.BtrfsIndex | None = None,
) -> None:
    """Delete one incomplete received Btrfs child subvolume before retrying.

    Ordinary-directory fallback deletion is intentionally unsupported. The
    containing date subvolume remains in place for the retry.
    """

    if not dest_path.exists():
        return
    if not config.destination.cleanup_incomplete_receive:
        raise SyncError(f"Destination path already exists but is not recorded as synced: {dest_path}")

    _human_blank()
    print(f"  {subvolume_name}: found incomplete destination receive not recorded in state.json")
    print("  retry policy: delete only this incomplete Btrfs child subvolume now")
    print("  date layout: keep the managed snapshot-date Btrfs subvolume for retry")
    print()
    print(f"LOCAL INCOMPLETE BTRFS DELETE: {dest_path}")
    print()

    meta = remote_index.refresh_local_path(
        destination_index,
        dest_path,
        name=subvolume_name,
        sudo=config.destination.sudo,
        btrfs_command=config.destination.btrfs_command,
    )
    if not meta:
        raise SyncError(
            "Destination path exists but is not a Btrfs subvolume. Ordinary-directory cleanup "
            "is disabled; inspect and remove it manually before retrying:\n"
            f"  {dest_path}"
        )
    try:
        btrfs.delete_local_subvolume(dest_path, config.destination.sudo, config.destination.btrfs_command)
    except Exception as exc:
        raise SyncError(f"Could not delete incomplete destination Btrfs subvolume {dest_path}: {exc}") from exc
    if destination_index is not None:
        destination_index.remove_tree(dest_path)
    print("  incomplete destination Btrfs subvolume removed")
    print("  retrying this snapshot/subvolume at its current oldest-to-newest queue position")
    _human_rule("---")

def _source_cache_live_child_paths(
    config: AppConfig,
    source: SourceRunner,
    parent_dir: str,
) -> list[str] | None:
    """Return live source-cache child subvolumes below one date parent.

    The run-start Btrfs indexes are intentionally not trusted for recovery,
    because this function is used exactly when an hourly snapshot or failed
    cache entry may have disappeared during the same run. A fresh
    ``btrfs subvolume list -o`` result is converted back to absolute paths and
    restricted to source.cache_root before any destructive action is allowed.
    """

    if not config.source.cache_root or not btrfs.path_is_under_cache(parent_dir, config.source.cache_root):
        return []
    listed_paths = btrfs.source_list_child_subvolumes(
        source,
        sudo=config.source.sudo,
        btrfs_command=config.source.btrfs_command,
        path=parent_dir,
    )
    if listed_paths is None:
        return None

    children: set[str] = set()
    for listed_path in listed_paths:
        for root in (parent_dir, config.source.cache_root):
            absolute = remote_index.listed_path_to_absolute(root, listed_path)
            if (
                absolute
                and absolute != parent_dir
                and btrfs.path_is_under_cache(absolute, config.source.cache_root)
                and btrfs.path_is_under_cache(absolute, parent_dir)
            ):
                children.add(absolute)
                break
        else:
            if "/" not in listed_path and listed_path not in {".", "..", ""}:
                absolute = str(Path(parent_dir) / listed_path)
                if btrfs.path_is_under_cache(absolute, parent_dir):
                    children.add(absolute)
    return sorted(children, key=lambda item: (item.count("/"), item), reverse=True)


def _cleanup_source_cache_snapshot_version(
    config: AppConfig,
    source: SourceRunner,
    snapshot_name: str,
    source_cache_index: remote_index.BtrfsIndex | None = None,
) -> None:
    """Delete only the app-owned source send-cache tree for one snapshot date.

    This is used by sync recovery, not retention. If a snapshot transfer is
    partial or the source Timeshift snapshot vanished mid-run, the current date
    cache must not remain as a future parent candidate. The helper deletes live
    child subvolumes deepest-first, then the cache date parent when it is empty.
    It never targets ``source.snapshot_root`` and never uses recursive ordinary deletion.
    """

    if not config.source.cache_root:
        return
    parent_dir = btrfs.readonly_cache_parent_path(config.source.cache_root, snapshot_name)
    if btrfs.path_is_same_or_under(parent_dir, config.source.snapshot_root):
        raise SyncError(f"Refusing recovery cleanup below Timeshift source.snapshot_root: {parent_dir}")

    parent_meta = remote_index.refresh_source_path(
        source_cache_index,
        source,
        parent_dir,
        name=Path(parent_dir).name,
        sudo=config.source.sudo,
        btrfs_command=config.source.btrfs_command,
    )
    if not parent_meta:
        if source_cache_index is not None:
            source_cache_index.remove_tree(parent_dir)
        print(f"  recovery source cache: already gone {parent_dir}")
        return

    live_children = _source_cache_live_child_paths(config, source, parent_dir)
    if live_children is None:
        raise SyncError(f"Could not list source send-cache children for recovery cleanup: {parent_dir}")

    # Also include the configured direct child names in case Btrfs list output
    # was unusual but targeted metadata can still see a child path.
    for subvol_name in config.source.subvolumes:
        child = btrfs.readonly_cache_path(config.source.cache_root, snapshot_name, subvol_name)
        if child not in live_children:
            child_meta = remote_index.refresh_source_path(
                source_cache_index,
                source,
                child,
                name=subvol_name,
                sudo=config.source.sudo,
                btrfs_command=config.source.btrfs_command,
            )
            if child_meta:
                live_children.append(child)
    live_children = sorted(set(live_children), key=lambda item: (item.count("/"), item), reverse=True)

    for child in live_children:
        if btrfs.path_is_same_or_under(child, config.source.snapshot_root):
            raise SyncError(f"Refusing recovery cleanup of Timeshift-owned source path: {child}")
        print(f"  recovery source cache child: deleting {child}")
        result = btrfs.source_delete_subvolume(
            source,
            config.source.sudo,
            config.source.btrfs_command,
            child,
            protected_snapshot_root=config.source.snapshot_root,
            check=False,
        )
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or f"return code {result.returncode}"
            raise SyncError(f"Source send-cache recovery cleanup failed for {child}: {detail}")
        if source_cache_index is not None:
            source_cache_index.remove_tree(child)

    empty = btrfs.source_cache_is_empty(
        source,
        sudo=config.source.sudo,
        btrfs_command=config.source.btrfs_command,
        cache_root=config.source.cache_root,
        path=parent_dir,
    )
    if empty is True:
        print(f"  recovery source cache parent: deleting {parent_dir}")
        result = btrfs.source_delete_subvolume(
            source,
            config.source.sudo,
            config.source.btrfs_command,
            parent_dir,
            protected_snapshot_root=config.source.snapshot_root,
            check=False,
        )
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or f"return code {result.returncode}"
            raise SyncError(f"Source send-cache parent recovery cleanup failed for {parent_dir}: {detail}")
        if source_cache_index is not None:
            source_cache_index.remove_tree(parent_dir)
        return
    if empty is None:
        raise SyncError(f"Could not verify source send-cache parent is empty: {parent_dir}")
    raise SyncError(f"Source send-cache parent still has child subvolumes after recovery cleanup: {parent_dir}")




def _cleanup_destination_snapshot_version(
    config: AppConfig,
    snapshot_name: str,
    destination_index: remote_index.BtrfsIndex | None = None,
) -> None:
    """Delete one whole destination date version using Btrfs only.

    Configured child subvolumes are deleted first. The date subvolume is then
    deleted, which removes its regular ``info.json`` automatically. Ordinary
    date folders and unexpected content are refused for manual inspection.
    """

    snapshot_dir = _target_snapshot_dir(config, snapshot_name)
    if not snapshot_dir.exists():
        if destination_index is not None:
            destination_index.remove_tree(snapshot_dir)
        print(f"  recovery destination: already gone {snapshot_dir}")
        return
    if snapshot_dir.is_symlink():
        raise SyncError(f"Refusing symlinked destination snapshot date path during recovery: {snapshot_dir}")

    live_index = remote_index.build_local_btrfs_index(
        snapshot_dir,
        sudo=config.destination.sudo,
        btrfs_command=config.destination.btrfs_command,
        include_root=True,
        required=False,
    )
    if not live_index.contains(snapshot_dir):
        raise SyncError(
            "Unsupported legacy destination layout during recovery: snapshot date path is not a "
            "Btrfs subvolume. Automatic ordinary-directory cleanup is disabled:\n"
            f"  {snapshot_dir}"
        )

    expected_children = {_dest_subvolume_path(config, snapshot_name, name) for name in config.source.subvolumes}
    live_children = {Path(path) for path in live_index.child_paths(snapshot_dir)}
    unexpected_subvolumes = sorted(str(path) for path in live_children if path not in expected_children)
    try:
        unexpected_entries = sorted(
            str(entry) for entry in snapshot_dir.iterdir()
            if entry.name not in set(config.source.subvolumes) | {"info.json"}
        )
    except OSError as exc:
        raise SyncError(f"Could not inspect destination date subvolume during recovery: {snapshot_dir}: {exc}") from exc
    if unexpected_subvolumes or unexpected_entries:
        details = unexpected_subvolumes + unexpected_entries
        raise SyncError(
            "Destination date subvolume contains unexpected content. Refusing automatic recovery "
            "deletion; inspect it manually:\n  " + "\n  ".join(details)
        )

    for child in sorted(live_children, key=lambda item: (len(item.parts), str(item)), reverse=True):
        print(f"  recovery destination child subvolume: deleting {child}")
        btrfs.delete_local_subvolume(child, config.destination.sudo, config.destination.btrfs_command)
        if destination_index is not None:
            destination_index.remove_tree(child)

    print(f"  recovery destination date subvolume: deleting {snapshot_dir}")
    btrfs.delete_local_subvolume(snapshot_dir, config.destination.sudo, config.destination.btrfs_command)
    if destination_index is not None:
        destination_index.remove_tree(snapshot_dir)

def _refresh_snapshot_source_subvolumes_live(
    config: AppConfig,
    source: SourceRunner,
    snapshot: SnapshotMeta,
    source_snapshot_index: remote_index.BtrfsIndex | None,
) -> tuple[dict[str, SubvolumeMeta], list[tuple[str, str]]]:
    """Return configured source subvolumes, preferring the bulk index.

    Normal sync passes use the coherent bulk source inventory and therefore do
    not open one SSH session per snapshot child. A targeted metadata probe is
    used only when no inventory was supplied by a legacy/internal caller.
    """

    found: dict[str, SubvolumeMeta] = {}
    missing: list[tuple[str, str]] = []
    for subvol_name in config.source.subvolumes:
        path = snapshot.subvolumes.get(subvol_name).path if subvol_name in snapshot.subvolumes else _expected_original_source_path(config, snapshot.name, subvol_name)
        meta = source_snapshot_index.meta(path) if source_snapshot_index is not None else None
        if source_snapshot_index is None:
            meta = remote_index.refresh_source_path(
                source_snapshot_index,
                source,
                path,
                name=subvol_name,
                sudo=config.source.sudo,
                btrfs_command=config.source.btrfs_command,
            )
        if meta:
            found[subvol_name] = meta
        else:
            missing.append((subvol_name, path))
    return found, missing


def _snapshot_destination_has_any_path(config: AppConfig, snapshot_name: str) -> bool:
    """Return True when the destination date folder or configured children exist."""

    snapshot_dir = _target_snapshot_dir(config, snapshot_name)
    if snapshot_dir.exists():
        return True
    return any(_dest_subvolume_path(config, snapshot_name, name).exists() for name in config.source.subvolumes)


def _snapshot_state_is_complete_with_destination(config: AppConfig, state: dict, snapshot_name: str) -> bool:
    """Return True only when state and destination contain every configured subvolume."""

    expected = list(config.source.subvolumes)
    return snapshot_is_synced(state, snapshot_name, expected) and _snapshot_destination_paths_exist(config, snapshot_name, expected)


def _recover_snapshot_version(
    config: AppConfig,
    source: SourceRunner,
    state: dict,
    snapshot_name: str,
    *,
    reason: str,
    source_still_exists: bool,
    dry_run: bool,
    source_cache_index: remote_index.BtrfsIndex | None,
    destination_index: remote_index.BtrfsIndex | None,
) -> None:
    """Remove stale current-version traces from cache, destination, and state."""

    _human_blank()
    print("SNAPSHOT RECOVERY")
    print(f"  snapshot: {snapshot_name}")
    print(f"  reason:   {reason}")
    if source_still_exists:
        print("  source:   configured subvolumes still exist in source.snapshot_root")
        print("  action:   clear failed current cache/destination/state, then recreate cache and transfer again")
    else:
        print("  source:   missing from source.snapshot_root")
        print("  action:   remove stale cache/destination/state for this snapshot and continue")

    if dry_run:
        print("  dry-run:  would clean source cache, destination version, and state.json")
        _human_rule("---")
        return

    _cleanup_source_cache_snapshot_version(config, source, snapshot_name, source_cache_index)
    _cleanup_destination_snapshot_version(config, snapshot_name, destination_index)
    if snapshot_name in state.get("snapshots", {}):
        remove_snapshot_from_state(state, snapshot_name)
        save_state(config.state_file, state)
        print("  state:    removed snapshot entry from state.json")
    else:
        print("  state:    no snapshot entry to remove")
    print("  indexes:  source-cache and destination metadata cache updated")
    _human_rule("---")


def _prepare_snapshot_for_transfer_or_recover(
    config: AppConfig,
    source: SourceRunner,
    state: dict,
    snapshot: SnapshotMeta,
    *,
    dry_run: bool,
    source_cache_index: remote_index.BtrfsIndex | None,
    source_snapshot_index: remote_index.BtrfsIndex | None,
    destination_index: remote_index.BtrfsIndex | None,
) -> bool:
    """Return True when a snapshot can be transferred, False when skipped.

    Partial snapshot versions are recovered at the snapshot level. This keeps
    ``@`` and ``@home`` paired by the same Timeshift date: if either configured
    source subvolume vanished, the whole failed version is removed from cache,
    destination, and state. If all source subvolumes still exist, any failed
    destination/current-cache version is cleared so the transfer can start over.
    """

    expected = list(config.source.subvolumes)
    state_complete = snapshot_is_synced(state, snapshot.name, expected)
    dest_complete = _snapshot_destination_paths_exist(config, snapshot.name, expected)
    has_state = snapshot.name in state.get("snapshots", {})
    has_destination = _snapshot_destination_has_any_path(config, snapshot.name)

    # Already-complete snapshots do not need source probing. Timeshift may have
    # pruned old hourly sources, but a complete destination backup remains valid
    # until normal destination retention deletes it.
    if state_complete and dest_complete:
        return True

    found, missing = _refresh_snapshot_source_subvolumes_live(config, source, snapshot, source_snapshot_index)
    if missing:
        missing_text = ", ".join(f"{name}={path}" for name, path in missing)
        _recover_snapshot_version(
            config,
            source,
            state,
            snapshot.name,
            reason="source Timeshift subvolume missing during retry/preflight: " + missing_text,
            source_still_exists=False,
            dry_run=dry_run,
            source_cache_index=source_cache_index,
            destination_index=destination_index,
        )
        return False

    # Replace path-only discovery records with live metadata before parent
    # selection and send-cache creation. This also removes stale index entries
    # for hourly snapshots that disappeared and then reappeared in Timeshift.
    snapshot.subvolumes = found

    if has_state or has_destination:
        reason_parts: list[str] = []
        if has_state and not state_complete:
            reason_parts.append("state.json has only a partial current snapshot")
        if has_destination and not dest_complete:
            reason_parts.append("destination version is missing at least one configured subvolume")
        if reason_parts:
            _recover_snapshot_version(
                config,
                source,
                state,
                snapshot.name,
                reason="; ".join(reason_parts),
                source_still_exists=True,
                dry_run=dry_run,
                source_cache_index=source_cache_index,
                destination_index=destination_index,
            )
    return True


def _recover_stale_state_snapshots_missing_from_source(
    config: AppConfig,
    source: SourceRunner,
    state: dict,
    source_by_name: dict[str, SnapshotMeta],
    *,
    dry_run: bool,
    source_cache_index: remote_index.BtrfsIndex | None,
    destination_index: remote_index.BtrfsIndex | None,
) -> int:
    """Clean incomplete state entries whose Timeshift source name is gone."""

    recovered = 0
    for snapshot_name in sorted(list(state.get("snapshots", {}))):
        if snapshot_name in source_by_name:
            continue
        if _snapshot_state_is_complete_with_destination(config, state, snapshot_name):
            continue
        _recover_snapshot_version(
            config,
            source,
            state,
            snapshot_name,
            reason="incomplete state entry has no matching source Timeshift snapshot",
            source_still_exists=False,
            dry_run=dry_run,
            source_cache_index=source_cache_index,
            destination_index=destination_index,
        )
        recovered += 1
    return recovered

def _read_local_destination_parent_metadata(
    config: AppConfig,
    *,
    parent_name: str,
    subvolume_name: str,
    destination_index: remote_index.BtrfsIndex | None = None,
) -> SubvolumeMeta:
    """Read metadata for the destination snapshot that would be the receiver parent."""

    local_parent_path = _dest_subvolume_path(config, parent_name, subvolume_name)
    indexed_meta = destination_index.meta(local_parent_path) if destination_index is not None else None
    if indexed_meta:
        return indexed_meta
    if not local_parent_path.exists():
        raise SyncError(f"Incremental parent is recorded but missing on destination: {local_parent_path}")

    try:
        return _local_meta(config, local_parent_path, subvolume_name)
    except Exception as exc:
        raise SyncError(f"Cannot read destination parent metadata: {local_parent_path}: {exc}") from exc


def _match_source_path_to_destination_received_uuid(
    config: AppConfig,
    source: SourceRunner,
    *,
    source_path: str,
    subvolume_name: str,
    destination_meta: SubvolumeMeta | None = None,
    destination_path: Path | None = None,
    label: str = "source path",
    expected_uuids: set[str] | None = None,
    require_readonly: bool = False,
    source_cache_index: remote_index.BtrfsIndex | None = None,
    source_snapshot_index: remote_index.BtrfsIndex | None = None,
    destination_index: remote_index.BtrfsIndex | None = None,
) -> tuple[bool, str]:
    """Check whether a source subvolume UUID matches the destination identity."""

    if destination_meta is None:
        if destination_path is None:
            raise ValueError("destination_meta or destination_path is required")
        destination_meta = destination_index.meta(destination_path) if destination_index is not None else None
        if destination_meta is None:
            try:
                destination_meta = _local_meta(config, destination_path, subvolume_name)
            except Exception as exc:
                return False, f"cannot read destination metadata for {destination_path}: {exc}"

    remote_meta = _source_meta(
        config,
        source,
        source_path,
        subvolume_name,
        required=False,
        source_snapshot_index=source_snapshot_index,
        source_cache_index=source_cache_index,
    )
    if not remote_meta or not remote_meta.uuid:
        return False, f"{label} not found or has no UUID: {source_path}"

    allowed = set(expected_uuids or set())
    if destination_meta.received_uuid:
        allowed.add(destination_meta.received_uuid)
    if not allowed:
        return False, "destination parent has no received_uuid; cannot prove matching source parent"
    if remote_meta.uuid not in allowed:
        expected = ", ".join(sorted(allowed))
        return False, f"{label} UUID {remote_meta.uuid} does not match destination/state UUID(s) {expected}: {source_path}"
    if require_readonly and remote_meta.readonly is False:
        return False, f"{label} UUID matches, but it is not read-only: {source_path}"

    readonly_note = "read-only confirmed" if remote_meta.readonly is True else "read-only flag not reported"
    return True, f"destination received_uuid/state matches {label} UUID ({readonly_note})"


def _select_verified_parent_send_path(
    config: AppConfig,
    source: SourceRunner,
    *,
    parent_name: str,
    parent_subvol: SubvolumeMeta | None,
    subvolume_name: str,
    state_parent: dict | None,
    source_cache_index: remote_index.BtrfsIndex | None = None,
    source_snapshot_index: remote_index.BtrfsIndex | None = None,
    destination_index: remote_index.BtrfsIndex | None = None,
) -> tuple[str | None, str]:
    """Select a safe source parent path for incremental send without recreating it.

    The safest recovery path is an existing source-cache snapshot whose UUID
    equals the destination parent's Received UUID. This can happen when an
    earlier SSH pull created read-only cache snapshots on the source and a later
    local sync wants to reuse those already-created snapshots. The match is
    accepted only when the indexed source-cache subvolume is read-only and its
    UUID exactly matches the destination parent identity.
    """

    local_parent = _read_local_destination_parent_metadata(
        config,
        parent_name=parent_name,
        subvolume_name=subvolume_name,
        destination_index=destination_index,
    )
    candidates: list[tuple[str, str]] = []

    def add_candidate(label: str, path: str | None) -> None:
        if isinstance(path, str) and path and all(existing != path for _, existing in candidates):
            candidates.append((label, path))

    # If the source-cache index already contains the exact UUID the destination
    # received from an earlier send, prefer that path. This lets a local run
    # adopt read-only cache snapshots left behind by an earlier SSH pull without
    # relying on stale absolute paths in state.json.
    if source_cache_index is not None and local_parent.received_uuid:
        indexed_parent = source_cache_index.by_uuid.get(local_parent.received_uuid)
        if indexed_parent and indexed_parent.path:
            add_candidate("indexed source-cache UUID match", indexed_parent.path)

    saved_send_path = None
    saved_send_path_error: str | None = None
    if state_parent and state_parent.get("send_path"):
        try:
            saved_send_path = resolve_state_send_path(
                state_parent,
                snapshot_root=config.source.snapshot_root,
                cache_root=config.source.cache_root,
                snapshot_name=parent_name,
                subvolume_name=subvolume_name,
            )
        except ValueError as exc:
            saved_send_path_error = f"saved state send_path is invalid: {exc}"
    add_candidate("saved state send_path", saved_send_path)

    # Newer state also stores the exact UUID that was streamed. If the saved
    # path is stale but the cache index still contains that UUID at another
    # path, try it before falling back to the writable Timeshift original.
    if source_cache_index is not None and state_parent:
        for key in ("send_source_uuid", "source_uuid", "destination_received_uuid"):
            value = state_parent.get(key)
            if isinstance(value, str) and value:
                indexed_parent = source_cache_index.by_uuid.get(value)
                if indexed_parent and indexed_parent.path:
                    add_candidate(f"indexed source-cache state {key}", indexed_parent.path)

    original_source_path = parent_subvol.path if parent_subvol else ""
    add_candidate("original Timeshift source path", original_source_path)

    failures: list[str] = []
    if saved_send_path_error:
        failures.append(saved_send_path_error)
    for label, path in candidates:
        ok, reason = _match_source_path_to_destination_received_uuid(
            config,
            source,
            source_path=path,
            subvolume_name=subvolume_name,
            destination_meta=local_parent,
            label=label,
            require_readonly=True,
            source_cache_index=source_cache_index,
            source_snapshot_index=source_snapshot_index,
            destination_index=destination_index,
        )
        if ok:
            return path, reason
        failures.append(reason)

    cache_hint = ""
    if state_parent and state_send_path_is_app_cache(
        state_parent,
        cache_root=config.source.cache_root,
        snapshot_root=config.source.snapshot_root,
    ):
        cache_hint = (
            "\n\nThe saved source parent was a read-only cache snapshot. If that exact "
            "cache UUID still exists anywhere below source.cache_root, the app can "
            "use it as an incremental parent. If the cache snapshot was deleted "
            "and recreated, the recreated cache snapshot gets a new Btrfs UUID and "
            "cannot be used as the parent for this destination snapshot."
        )

    destination_path = _dest_subvolume_path(config, parent_name, subvolume_name)
    reason = "; ".join(failures) if failures else "no source parent candidates were available"
    return (
        None,
        f"destination parent {destination_path} has received_uuid={local_parent.received_uuid}; "
        f"no source parent path matched. {reason}{cache_hint}",
    )

def _state_uuid_values_for_path(
    state_subvol: dict,
    *,
    path: str,
    source_path: str,
    send_path: str | None,
) -> set[str]:
    """Return UUID values that may safely identify the source path.

    State from newer versions has both original_source_uuid and
    send_source_uuid. Older state may only have source_uuid and
    destination_received_uuid. For the exact send_path, destination_received_uuid
    is a strong identifier because Btrfs receive stores the UUID of the streamed
    source subvolume there. For the original Timeshift path, original_source_uuid
    is the strong identifier when available.
    """

    values: set[str] = set()

    def add_key(key: str) -> None:
        value = state_subvol.get(key)
        if isinstance(value, str) and value and value != "-":
            values.add(value)

    if path == send_path:
        add_key("send_source_uuid")
        add_key("source_uuid")
        add_key("destination_received_uuid")

    if path == source_path:
        add_key("original_source_uuid")
        # For direct sends, source_path and send_path are the same path. Older
        # states also used source_uuid for direct sends, so allow those values
        # only when the saved send path is missing or is the original path.
        if not send_path or send_path == source_path:
            add_key("send_source_uuid")
            add_key("source_uuid")
            add_key("destination_received_uuid")

    return values


def _find_confirmed_sync_floor(
    config: AppConfig,
    source: SourceRunner,
    state: dict,
    source_by_name: dict[str, SnapshotMeta],
    *,
    source_cache_index: remote_index.BtrfsIndex | None = None,
    source_snapshot_index: remote_index.BtrfsIndex | None = None,
    destination_index: remote_index.BtrfsIndex | None = None,
) -> tuple[str | None, str]:
    """Return newest state snapshot that still exists on source and matches UUIDs.

    After destination pruning, old source snapshots may still exist on the source
    side. Without a floor, sync would see those pruned snapshots as missing and
    send them again. Instead of adding a long list of tombstones, we walk
    state.json newest-to-oldest and find the newest snapshot that:

    * is still listed by `timeshift --list` on the source,
    * is fully synced locally for the configured subvolumes,
    * has matching Btrfs UUID identity between source and destination.

    Source snapshots older than or equal to this confirmed floor are skipped by
    normal sync. If the original Timeshift snapshot no longer exists, the search
    can still confirm a floor through the saved app-created send_path in state.
    """

    state_snapshots = state.get("snapshots", {})
    if not state_snapshots:
        return None, "state is empty"

    source_names = source_by_name.keys()
    checked_missing = 0
    checked_mismatch: list[str] = []

    for name in sorted(state_snapshots.keys(), reverse=True):
        source_snapshot = source_by_name.get(name)
        if name not in source_names:
            checked_missing += 1
        if not snapshot_is_synced(state, name, config.source.subvolumes):
            continue

        state_snapshot = state_snapshots.get(name, {})
        state_subvolumes = state_snapshot.get("subvolumes", {})

        reasons: list[str] = []
        ok = True
        for subvolume_name in config.source.subvolumes:
            source_subvol = source_snapshot.subvolumes.get(subvolume_name) if source_snapshot else None
            state_subvol = state_subvolumes.get(subvolume_name)
            if not state_subvol:
                ok = False
                reasons.append(f"{subvolume_name}: missing state subvolume")
                break
            destination_path_text = state_subvol.get("destination_path")
            if not isinstance(destination_path_text, str) or not destination_path_text:
                ok = False
                reasons.append(f"{subvolume_name}: state has no destination_path")
                break
            try:
                destination_path = resolve_destination_path(config.destination.target_root, destination_path_text)
            except ValueError as exc:
                ok = False
                reasons.append(f"{subvolume_name}: invalid destination_path in state: {exc}")
                break

            sub_reasons: list[str] = []
            source_path = source_subvol.path if source_subvol else ""
            saved_send_path: str | None = None
            if state_subvol.get("send_path"):
                try:
                    saved_send_path = resolve_state_send_path(
                        state_subvol,
                        snapshot_root=config.source.snapshot_root,
                        cache_root=config.source.cache_root,
                        snapshot_name=name,
                        subvolume_name=subvolume_name,
                    )
                except ValueError as exc:
                    sub_reasons.append(f"invalid saved send_path: {exc}")
            candidate_paths = [path for path in (saved_send_path, source_path) if isinstance(path, str) and path]
            if not candidate_paths:
                ok = False
                reasons.append(f"{subvolume_name}: no saved send_path and original source snapshot is not listed")
                break
            for path in dict.fromkeys(candidate_paths):
                sub_ok, reason = _match_source_path_to_destination_received_uuid(
                    config,
                    source,
                    source_path=path,
                    subvolume_name=subvolume_name,
                    destination_path=destination_path,
                    label=path,
                    expected_uuids=_state_uuid_values_for_path(
                        state_subvol,
                        path=path,
                        source_path=source_path,
                        send_path=saved_send_path,
                    ),
                    source_cache_index=source_cache_index,
                    source_snapshot_index=source_snapshot_index,
                    destination_index=destination_index,
                )
                sub_reasons.append(reason)
                if sub_ok:
                    reasons.append(f"{subvolume_name}: {reason}")
                    break
            else:
                ok = False
                reasons.append(f"{subvolume_name}: {'; '.join(sub_reasons)}")
                break

        if ok:
            if name not in source_names:
                return name, "newest state snapshot is no longer in Timeshift, but saved source send-cache UUIDs are confirmed"
            if checked_missing:
                return name, f"newest state snapshot was not on source; walked back {checked_missing} entr{'y' if checked_missing == 1 else 'ies'} and confirmed UUIDs"
            return name, "newest state/source snapshot confirmed by UUIDs"

        checked_mismatch.append(f"{name}: {'; '.join(reasons)}")

    if checked_mismatch:
        return None, "no state/source snapshot passed UUID confirmation; latest mismatch: " + checked_mismatch[0]
    if checked_missing:
        return None, f"no state snapshot still exists on source; checked {checked_missing} missing entr{'y' if checked_missing == 1 else 'ies'}"
    return None, "no usable fully synced state snapshot found"


def _destination_snapshot_names(config: AppConfig) -> list[str]:
    """Return destination snapshot folder names sorted oldest-to-newest."""

    snapshots_root = config.destination.target_root / "snapshots"
    if not snapshots_root.exists():
        return []
    return sorted(child.name for child in snapshots_root.iterdir() if child.is_dir())


def _expected_original_source_path(config: AppConfig, snapshot_name: str, subvolume_name: str) -> str:
    """Return the Timeshift-owned original source path for one snapshot/subvolume."""

    return str(Path(config.source.snapshot_root) / snapshot_name / subvolume_name)


def _source_cache_meta_by_uuid(
    config: AppConfig,
    source: SourceRunner,
    source_cache_index: remote_index.BtrfsIndex | None,
    uuid: str | None,
    subvolume_name: str,
) -> SubvolumeMeta | None:
    """Return coherent indexed source-cache metadata for an exact UUID match.

    The combined source inventory already captures UUID and read-only metadata
    for the complete cache root in one SSH session. Re-reading every candidate
    with a targeted ``subvolume show`` would add one SSH round trip per parent
    comparison without strengthening the exact UUID rule. Mutating operations
    refresh or update the index, and failed sends trigger a full inventory
    rebuild before source-change recovery is considered.
    """

    del config, source, subvolume_name  # Kept in the signature for existing callers.
    if not uuid or source_cache_index is None:
        return None
    indexed = source_cache_index.by_uuid.get(uuid)
    if indexed and indexed.path and indexed.uuid == uuid and indexed.readonly is not False:
        return indexed
    return None


def _match_existing_destination_to_source(
    config: AppConfig,
    source: SourceRunner,
    source_by_name: dict[str, SnapshotMeta],
    *,
    snapshot_name: str,
    subvolume_name: str,
    destination_meta: SubvolumeMeta,
    source_cache_index: remote_index.BtrfsIndex | None,
    source_snapshot_index: remote_index.BtrfsIndex | None = None,
) -> tuple[SnapshotMeta | None, SubvolumeMeta | None, str | None, SubvolumeMeta | None, SubvolumeMeta | None, str]:
    """Match one existing destination subvolume to an exact source/cache UUID.

    Returns ``(snapshot, original_subvol, send_path, original_meta, send_meta,
    reason)``. ``send_path`` is non-empty only when the destination can be
    adopted into state safely. Adoption requires the destination Received UUID
    to equal the UUID of either the original Timeshift source subvolume or an
    existing read-only source-cache subvolume.
    """

    if not destination_meta.received_uuid:
        return None, None, None, None, None, "destination has no Received UUID"

    source_snapshot = source_by_name.get(snapshot_name)
    source_subvol = source_snapshot.subvolumes.get(subvolume_name) if source_snapshot else None
    original_path = source_subvol.path if source_subvol else _expected_original_source_path(config, snapshot_name, subvolume_name)
    original_subvol = source_subvol or SubvolumeMeta(name=subvolume_name, path=original_path)

    original_meta = None
    if source_subvol:
        try:
            original_meta = _source_meta(
                config,
                source,
                original_path,
                subvolume_name,
                required=False,
                source_snapshot_index=source_snapshot_index,
                source_cache_index=source_cache_index,
            )
        except Exception:
            original_meta = None
        if original_meta and original_meta.uuid == destination_meta.received_uuid:
            return source_snapshot, original_subvol, original_path, original_meta, original_meta, "matched original Timeshift source UUID"

    cache_meta = _source_cache_meta_by_uuid(
        config,
        source,
        source_cache_index,
        destination_meta.received_uuid,
        subvolume_name,
    )
    if cache_meta and cache_meta.path:
        if source_snapshot is None:
            source_snapshot = SnapshotMeta(
                name=snapshot_name,
                path=str(Path(config.source.snapshot_root) / snapshot_name),
                tags=[],
                comment=None,
                created=None,
                subvolumes={subvolume_name: original_subvol},
            )
        return source_snapshot, original_subvol, cache_meta.path, original_meta, cache_meta, "matched existing source-cache UUID"

    return (
        source_snapshot,
        original_subvol,
        None,
        original_meta,
        None,
        f"no source/cache UUID matched destination Received UUID {destination_meta.received_uuid}",
    )


def _recover_state_from_existing_destination(
    config: AppConfig,
    source: SourceRunner,
    state: dict,
    source_by_name: dict[str, SnapshotMeta],
    *,
    dry_run: bool,
    source_cache_index: remote_index.BtrfsIndex | None,
    source_snapshot_index: remote_index.BtrfsIndex | None = None,
    destination_index: remote_index.BtrfsIndex | None = None,
) -> tuple[str | None, str]:
    """Rebuild missing/empty state.json from proven source/destination matches.

    This recovery is intentionally conservative. It never trusts names alone and
    never invents a parent chain. A destination subvolume is adopted only when
    Btrfs proves that its Received UUID equals a currently available source
    UUID, either the original Timeshift snapshot subvolume or an existing
    read-only source-cache subvolume. Once adopted, the normal sync-floor logic
    can continue from the newest fully adopted snapshot.
    """

    if state.get("snapshots"):
        return None, "state already has snapshot records"
    if not _destination_has_existing_snapshots(config):
        return None, "destination has no snapshots to adopt"

    adopted_subvolumes = 0
    adopted_full_snapshots: list[str] = []
    skipped: list[str] = []
    parent_by_subvolume: dict[str, tuple[str, str]] = {}

    for snapshot_name in _destination_snapshot_names(config):
        snapshot_any_adopted = False
        snapshot_all_required = True
        synthetic_snapshot: SnapshotMeta | None = None

        for subvolume_name in config.source.subvolumes:
            dest_path = _dest_subvolume_path(config, snapshot_name, subvolume_name)
            dest_meta = destination_index.meta(dest_path) if destination_index is not None else None
            if dest_meta is None and dest_path.exists():
                try:
                    dest_meta = _local_meta(config, dest_path, subvolume_name, required=False)
                except Exception:
                    dest_meta = None
            if dest_meta is None:
                snapshot_all_required = False
                skipped.append(f"{snapshot_name}/{subvolume_name}: destination subvolume missing or unreadable")
                continue

            (
                source_snapshot,
                original_subvol,
                send_path,
                original_meta,
                send_meta,
                reason,
            ) = _match_existing_destination_to_source(
                config,
                source,
                source_by_name,
                snapshot_name=snapshot_name,
                subvolume_name=subvolume_name,
                destination_meta=dest_meta,
                source_cache_index=source_cache_index,
                source_snapshot_index=source_snapshot_index,
            )
            if not send_path or source_snapshot is None or original_subvol is None:
                snapshot_all_required = False
                skipped.append(f"{snapshot_name}/{subvolume_name}: {reason}")
                continue

            synthetic_snapshot = source_snapshot
            parent_snapshot, parent_source_path = parent_by_subvolume.get(subvolume_name, (None, None))
            # Always adopt into the in-memory state. In dry-run this lets the
            # remaining plan use the recovered high-watermark without writing
            # state.json to disk.
            mark_subvolume_synced(
                state,
                snapshot=source_snapshot,
                subvolume=original_subvol,
                destination_path=dest_path,
                destination_root=config.destination.target_root,
                snapshot_root=config.source.snapshot_root,
                cache_root=config.source.cache_root,
                parent_snapshot=parent_snapshot,
                parent_source_path=parent_source_path,
                send_path=send_path,
                received_meta=dest_meta,
                original_meta=original_meta,
                send_meta=send_meta,
            )
            parent_by_subvolume[subvolume_name] = (snapshot_name, send_path)
            adopted_subvolumes += 1
            snapshot_any_adopted = True

        if snapshot_any_adopted and snapshot_all_required:
            adopted_full_snapshots.append(snapshot_name)

    _human_blank()
    print("STATE RECOVERY")
    print("  trigger: state.json is missing or empty, but destination snapshots exist")
    print("  rule:    adopt only exact Btrfs UUID matches; names alone are never trusted")
    print(f"  adopted subvolume(s): {adopted_subvolumes}")
    if adopted_full_snapshots:
        print(f"  fully adopted snapshot(s): {', '.join(adopted_full_snapshots)}")
    if skipped:
        print(f"  skipped candidate(s): {len(skipped)}")
        for line in skipped[:10]:
            print(f"    - {line}")
        if len(skipped) > 10:
            print(f"    ... {len(skipped) - 10} more")
    if dry_run:
        print("  dry-run: recovered state.json would be written, but was not changed")
    elif adopted_subvolumes:
        save_state(config.state_file, state)
        print("  state.json rebuilt from existing destination/source UUID matches")
    else:
        print("  state.json was not rebuilt because no safe UUID matches were found")
    _human_rule("----")

    if not adopted_full_snapshots:
        return None, "no complete configured snapshot could be adopted"
    newest = adopted_full_snapshots[-1]
    return newest, f"rebuilt state from existing destination/source UUID matches through {newest}"

def _filesystem_parent_candidates(config: AppConfig, snapshot_name: str, subvolume_name: str, source_names: set[str]) -> list[str]:
    """Find local destination parent candidates by matching snapshot names.

    This lets the app recover/adopt a valid parent even if state.json is missing
    or incomplete, as long as local Btrfs `Received UUID` matches the source
    parent's UUID.
    """

    snapshots_root = config.destination.target_root / "snapshots"
    if not snapshots_root.exists():
        return []
    candidates: list[str] = []
    for child in snapshots_root.iterdir():
        if not child.is_dir():
            continue
        name = child.name
        if name >= snapshot_name or name not in source_names:
            continue
        if (child / subvolume_name).exists():
            candidates.append(name)
    candidates.sort(reverse=True)
    return candidates


def _select_parent(
    config: AppConfig,
    source: SourceRunner,
    state: dict,
    source_by_name: dict[str, SnapshotMeta],
    snapshot: SnapshotMeta,
    subvolume_name: str,
    *,
    dry_run: bool,
    trusted_parent_send_paths: set[str] | None = None,
    allow_full_seed: bool = False,
    source_cache_index: remote_index.BtrfsIndex | None = None,
    source_snapshot_index: remote_index.BtrfsIndex | None = None,
    destination_index: remote_index.BtrfsIndex | None = None,
) -> tuple[str | None, str | None]:
    """Choose the newest valid incremental parent.

    The source parent path is chosen by UUID identity, not by recreating cache
    snapshots. For each candidate destination parent, the app tries the saved
    state send_path first, then the original Timeshift source path. One of those
    paths must currently have a UUID matching the destination parent's
    received_uuid. Otherwise the candidate is rejected and the next older parent
    candidate is tried.

    If the destination was empty when this sync run started, missing parents are
    allowed to fall back to full send. This is needed while seeding the first
    backup snapshot: after @ is received, the destination is no longer globally
    empty, but @home may still need its first full send.
    """

    source_names = source_by_name.keys()
    state_parent = latest_synced_before(state, snapshot.name, subvolume_name, source_names)

    candidate_names: list[str] = []
    state_parent_data: dict[str, dict] = {}
    if state_parent:
        parent_name, parent_state = state_parent
        candidate_names.append(parent_name)
        state_parent_data[parent_name] = parent_state

    # If the newest state parent no longer matches because its source cache was
    # deleted, an older state parent can still be a valid incremental parent. Add
    # every older synced state candidate, newest first. A candidate may be used
    # through its saved send_path even if Timeshift already pruned the original.
    for name in sorted(state.get("snapshots", {}).keys(), reverse=True):
        if name >= snapshot.name or name in candidate_names:
            continue
        item = state.get("snapshots", {}).get(name, {})
        sub = item.get("subvolumes", {}).get(subvolume_name) if isinstance(item, dict) else None
        if isinstance(sub, dict) and sub.get("status") == "ok" and (name in source_names or sub.get("send_path")):
            candidate_names.append(name)
            state_parent_data[name] = sub

    # Also look at the filesystem for matching date-named snapshots. This helps
    # if state.json is missing but destination snapshots are present.
    for name in _filesystem_parent_candidates(config, snapshot.name, subvolume_name, source_names):
        if name not in candidate_names:
            candidate_names.append(name)

    candidate_failures: list[str] = []
    for parent_name in candidate_names:
        parent_snapshot = source_by_name.get(parent_name)
        parent_subvol = parent_snapshot.subvolumes.get(subvolume_name) if parent_snapshot else None
        parent_state = state_parent_data.get(parent_name)
        saved_send_path: str | None = None
        if parent_state and parent_state.get("send_path"):
            try:
                saved_send_path = resolve_state_send_path(
                    parent_state,
                    snapshot_root=config.source.snapshot_root,
                    cache_root=config.source.cache_root,
                    snapshot_name=parent_name,
                    subvolume_name=subvolume_name,
                )
            except ValueError as exc:
                candidate_failures.append(f"{parent_name}/{subvolume_name}: invalid saved send_path: {exc}")
        if not parent_subvol and not saved_send_path:
            continue

        if dry_run:
            # Dry-run remains fast. It explains that real mode will verify the
            # parent before using it.
            if isinstance(saved_send_path, str) and saved_send_path:
                return parent_name, saved_send_path
            return parent_name, _preview_send_path(config, parent_name, parent_subvol)

        if (
            isinstance(saved_send_path, str)
            and saved_send_path
            and trusted_parent_send_paths is not None
            and config.source.verify_incremental_parent_once_per_run
            and saved_send_path in trusted_parent_send_paths
        ):
            _human_blank()
            print(
                f"  {subvolume_name}: parent guard already proven in this run for {parent_name}; "
                "using the just-sent source parent path"
            )
            _human_blank()
            return parent_name, saved_send_path

        parent_send_path, reason = _select_verified_parent_send_path(
            config,
            source,
            parent_name=parent_name,
            parent_subvol=parent_subvol,
            subvolume_name=subvolume_name,
            state_parent=parent_state,
            source_cache_index=source_cache_index,
            source_snapshot_index=source_snapshot_index,
            destination_index=destination_index,
        )
        if parent_send_path:
            _human_blank()
            print(f"  {subvolume_name}: parent guard ok for {parent_name} ({reason})")
            _human_blank()
            return parent_name, parent_send_path

        candidate_failures.append(f"{parent_name}/{subvolume_name}: {reason}")

    # No usable parent was found. Full send is allowed when the destination was
    # empty at run start, because all snapshots/subvolumes created during that
    # run belong to this newly seeded chain. This fixes first-run multi-subvolume
    # seeding where @ makes the destination non-empty before @home is sent.
    if allow_full_seed:
        return None, None

    # Full-send permission is based only on whether the destination was empty at
    # run start (allow_full_seed). Do not re-check current destination emptiness:
    # recovery may have removed a partial version during this run, and temporary
    # emptiness must never turn an existing backup into a new seed.
    details = ""
    if candidate_failures:
        details = "\n\nChecked parent candidate(s):\n  " + "\n  ".join(candidate_failures)
    raise SyncError(
        "Source and destination do not match in any usable snapshot for incremental send. "
        "This run did not start with an empty destination, so a full send is refused even "
        "if recovery cleanup has made the destination temporarily empty. Use an empty/separate "
        "target_root for a new full backup, or restore/repair state.json and the exact source "
        "cache so at least one source snapshot UUID matches a destination Received UUID."
        + details
    )


def _verify_sync_viability_before_manual_snapshot(
    config: AppConfig,
    source: SourceRunner,
    state: dict,
    source_by_name: dict[str, SnapshotMeta],
    *,
    destination_empty_at_start: bool,
    only_snapshot: str | None,
    only_missing: bool,
    source_cache_index: remote_index.BtrfsIndex | None = None,
    source_snapshot_index: remote_index.BtrfsIndex | None = None,
    destination_index: remote_index.BtrfsIndex | None = None,
) -> None:
    """Prove sync can start before asking Timeshift to create a snapshot.

    Creating a Timeshift on-demand snapshot is a source-side change. The app
    must therefore verify the current source/destination chain first. For an
    existing destination, this check requires an exact UUID-proven parent for
    the next pending transfer, or for a future manual snapshot when there are
    no current pending transfers. It performs metadata checks only; it never
    creates source cache snapshots and never starts send/receive.
    """

    if not config.manual_snapshot.enabled or only_snapshot:
        return

    _human_blank()
    print("PRE-MANUAL SNAPSHOT SYNC CHECK")
    print("  purpose: prove the current source/destination chain can continue before creating a new Timeshift snapshot")

    if destination_empty_at_start:
        print("  result:  destination has no existing snapshots; the first selected snapshot can start as a full seed")
        _human_rule("----")
        return

    sync_floor_name, sync_floor_reason = _find_confirmed_sync_floor(
        config,
        source,
        state,
        source_by_name,
        source_cache_index=source_cache_index,
        source_snapshot_index=source_snapshot_index,
        destination_index=destination_index,
    )
    if not sync_floor_name:
        print(f"  result:  failed; no UUID-confirmed sync floor ({sync_floor_reason})")
        _human_rule("----")
        raise SyncError(
            "Refusing to create a new Timeshift on-demand snapshot because source "
            "and destination do not match in any complete UUID-confirmed snapshot. Fix "
            "the parent/state/source-cache problem first, or use an empty/separate "
            "target_root for a new full backup.\n\n"
            f"Sync-floor check: {sync_floor_reason}"
        )

    print(f"  sync floor: {sync_floor_name} ({sync_floor_reason})")

    def verify_parent_for(snapshot: SnapshotMeta, subvolume_name: str, *, future_manual: bool = False) -> tuple[str | None, str | None]:
        try:
            return _select_parent(
                config,
                source,
                state,
                source_by_name,
                snapshot,
                subvolume_name,
                dry_run=False,
                trusted_parent_send_paths=set(),
                allow_full_seed=False,
                source_cache_index=source_cache_index,
                source_snapshot_index=source_snapshot_index,
                destination_index=destination_index,
            )
        except SyncError as exc:
            context = "future manual snapshot" if future_manual else f"pending snapshot {snapshot.name}"
            print(f"  result:  failed while checking {context}/{subvolume_name}")
            _human_rule("----")
            raise SyncError(
                "Refusing to create a new Timeshift on-demand snapshot because "
                "the app cannot prove that sync can continue from the current "
                "destination/source chain. No new source snapshot was created.\n\n"
                f"Failed check: {context}/{subvolume_name}\n"
                f"Reason: {exc}"
            ) from exc

    # If there is already a pending source snapshot newer than the confirmed
    # floor, verify that the first transfer in the normal oldest-to-newest order
    # can select a UUID-proven parent. This catches broken state/cache/destination
    # chains before Timeshift creates another snapshot.
    for snapshot in _snapshots_in_sync_order(source_by_name.values()):
        if snapshot.name <= sync_floor_name:
            continue
        expected = [name for name in config.source.subvolumes if name in snapshot.subvolumes]
        if not expected:
            continue
        if only_missing and snapshot_is_synced(state, snapshot.name, expected) and _snapshot_destination_paths_exist(config, snapshot.name, expected):
            continue
        for subvolume_name in config.source.subvolumes:
            if subvolume_name not in snapshot.subvolumes:
                continue
            parent_name, _parent_path = verify_parent_for(snapshot, subvolume_name)
            print(f"  result:  existing pending transfer can start: {snapshot.name}/{subvolume_name} parent={parent_name or 'full'}")
            _human_rule("----")
            return

    # No existing snapshot needs transfer. A fresh manual snapshot would be newer
    # than every current source snapshot, so verify that each configured subvolume
    # has a usable parent for that future snapshot before asking Timeshift to
    # create it. The sentinel name sorts after normal Timeshift timestamps.
    future_snapshot = SnapshotMeta(
        name="9999-12-31_23-59-59",
        path="<future manual Timeshift snapshot>",
        tags=[],
        comment=None,
        created=None,
        subvolumes={},
    )
    verified: list[str] = []
    for subvolume_name in config.source.subvolumes:
        parent_name, _parent_path = verify_parent_for(future_snapshot, subvolume_name, future_manual=True)
        verified.append(f"{subvolume_name}: parent={parent_name or 'full'}")

    print("  result:  no current pending transfers; future manual snapshot parent chain is verified")
    for line in verified:
        print(f"    - {line}")
    _human_rule("----")


def sync_once(config: AppConfig, state: dict, *, dry_run: bool, limit: int | None = None, only_snapshot: str | None = None, only_missing: bool = True) -> int:
    """Run one sync pass.

    A sync pass processes source snapshots oldest-to-newest. After every
    successful subvolume receive, state.json is updated immediately. That is how
    later snapshots in the same run can become incremental.
    """

    normalize_state_paths(
        state,
        target_root=config.destination.target_root,
        snapshot_root=config.source.snapshot_root,
        cache_root=config.source.cache_root,
    )

    if dry_run:
        print("Strict dry-run: destination preparation is skipped; no target directories or internal metadata directories are created/changed.")
        _human_rule("----")

    # Create one source runner. In ssh mode it wraps SSH; in local mode it runs
    # the same source-side sudo+btrfs/timeshift commands locally and skips SSH.
    source = SourceRunner.from_config(config)
    if source.uses_ssh:
        source.test()
    else:
        print("Source mode: local; SSH setup/test skipped. Source commands run on this machine.")
        _human_rule("----")

    # Before Timeshift creates a fresh on-demand snapshot, before source cache
    # snapshots are created, and before any send/receive pipeline starts,
    # preflight verifies required roots. In real-run mode, missing configured
    # roots are created here first; if creation or Btrfs verification fails, the
    # exact configured path is reported as a hard error.
    preflight.check_required_sync_paths(config, source, dry_run=dry_run)

    if not dry_run:
        prepare_destination(config)

    destination_index = remote_index.build_local_btrfs_index(
        config.destination.target_root,
        sudo=config.destination.sudo,
        btrfs_command=config.destination.btrfs_command,
        include_root=True,
    )
    _validate_destination_snapshot_layout(config, destination_index)
    destination_empty_at_start = not _destination_has_existing_snapshots(config)

    def load_source_inventory(reason: str) -> tuple[remote_index.SourceInventory, dict[str, SnapshotMeta]]:
        """Build and report one coherent source inventory generation."""

        print(f"Reading one combined source inventory ({reason})...")
        inventory = remote_index.build_source_inventory(
            source,
            snapshot_root=config.source.snapshot_root,
            cache_root=config.source.cache_root,
            sudo=config.source.sudo,
            btrfs_command=config.source.btrfs_command,
            timeshift_command=config.source.timeshift_command,
            required=True,
        )
        snapshots = _snapshots_from_source_inventory(config, source, inventory)
        return inventory, snapshots

    source_inventory, source_by_name = load_source_inventory("initial Timeshift/snapshot/cache scan")
    snapshot_root_btrfs_index = source_inventory.snapshot_index
    source_cache_index = source_inventory.cache_index
    _human_blank()
    print("SOURCE INDEX CACHE")
    if snapshot_root_btrfs_index.root_missing:
        print(f"  source snapshots: missing or not listable; indexed 0 subvolumes below {snapshot_root_btrfs_index.root}")
    else:
        print(f"  source snapshots: indexed {len(snapshot_root_btrfs_index.by_path)} subvolume(s) below {snapshot_root_btrfs_index.root}")
    print(
        f"  Timeshift metadata: captured {len(source_inventory.snapshot_info_json)} info.json file(s) "
        "inside the same source inventory request"
    )
    if source_inventory.snapshot_info_errors:
        print(f"  Timeshift metadata warnings: {len(source_inventory.snapshot_info_errors)} unreadable/missing file(s)")
    if source_cache_index is None:
        print("  source cache: disabled; no source.cache_root configured")
    elif source_cache_index.root_missing:
        print(f"  source cache: missing or not listable; indexed 0 subvolumes below {source_cache_index.root}")
    else:
        print(f"  source cache: indexed {len(source_cache_index.by_path)} subvolume(s) below {source_cache_index.root}")
    if destination_index.root_missing:
        print(f"  destination:  missing or not listable; indexed 0 subvolumes below {destination_index.root}")
    else:
        print(f"  destination:  indexed {len(destination_index.by_path)} subvolume(s) below {destination_index.root}")
    print("  purpose:      reuse per-run path/UUID lookups instead of repeated source btrfs probes")
    _human_rule("----")

    _human_blank()
    print(
        "Discovery verification: bulk metadata is already loaded for every configured source path."
        if config.source.verify_subvolumes_at_discovery
        else "Discovery verification: bulk metadata is loaded once; missing paths are handled from the inventory and refreshed only after source change/failure."
    )
    print("SSH policy: Timeshift list, all readable per-snapshot info.json files, snapshot_root metadata, and cache_root metadata came from one source inventory command.")
    _human_rule("----")

    before_manual_snapshot_names = set(source_by_name)

    state_empty_at_start = not state.get("snapshots")
    if state_empty_at_start and not destination_empty_at_start:
        _recover_state_from_existing_destination(
            config,
            source,
            state,
            source_by_name,
            dry_run=dry_run,
            source_cache_index=source_cache_index,
            source_snapshot_index=snapshot_root_btrfs_index,
            destination_index=destination_index,
        )

    # A destination that was already populated when this run started must have a
    # complete UUID-confirmed source/destination anchor before snapshot recovery
    # may delete partial destination versions. This also prevents cleanup from
    # making an existing destination look empty and enabling a full send later.
    confirmed_existing_floor_name: str | None = None
    confirmed_existing_floor_reason = "destination was empty at run start"
    if not destination_empty_at_start:
        confirmed_existing_floor_name, confirmed_existing_floor_reason = _find_confirmed_sync_floor(
            config,
            source,
            state,
            source_by_name,
            source_cache_index=source_cache_index,
            source_snapshot_index=snapshot_root_btrfs_index,
            destination_index=destination_index,
        )
        if not confirmed_existing_floor_name:
            raise SyncError(
                "Source and destination do not match in any complete UUID-confirmed snapshot. "
                "The destination was not empty when this run started, so the app refuses to "
                "delete/recover destination snapshot versions or start a full send. Use an "
                "empty/separate target_root for a new full backup, or restore/repair state.json "
                "and the exact source cache so a source snapshot UUID matches a destination "
                "Received UUID.\n\n"
                f"Match check: {confirmed_existing_floor_reason}"
            )

    stale_recovered = _recover_stale_state_snapshots_missing_from_source(
        config,
        source,
        state,
        source_by_name,
        dry_run=dry_run,
        source_cache_index=source_cache_index,
        destination_index=destination_index,
    )
    if stale_recovered:
        print(f"Recovered {stale_recovered} stale incomplete state snapshot(s) before manual-snapshot checks.")
        _human_rule("----")

    _verify_sync_viability_before_manual_snapshot(
        config,
        source,
        state,
        source_by_name,
        destination_empty_at_start=destination_empty_at_start,
        only_snapshot=only_snapshot,
        only_missing=only_missing,
        source_cache_index=source_cache_index,
        source_snapshot_index=snapshot_root_btrfs_index,
        destination_index=destination_index,
    )

    created_manual_snapshot = _maybe_create_manual_snapshot(
        config,
        source,
        state=state,
        source_by_name=source_by_name,
        dry_run=dry_run,
        only_snapshot=only_snapshot,
        source_cache_index=source_cache_index,
        source_snapshot_index=snapshot_root_btrfs_index,
        destination_index=destination_index,
    )
    if created_manual_snapshot:
        source_inventory, source_by_name = load_source_inventory("after manual snapshot creation")
        snapshot_root_btrfs_index = source_inventory.snapshot_index
        source_cache_index = source_inventory.cache_index
        created_names = sorted(set(source_by_name) - before_manual_snapshot_names)
        _human_blank()
        print("MANUAL SNAPSHOT SYNC ORDER")
        if created_names:
            print(f"  detected new snapshot(s): {', '.join(created_names)}")
        else:
            print("  warning: no new snapshot name was detected after Timeshift create")
        print("  sending rule: no special early send; snapshots are processed in normal oldest-to-newest order")
        _human_rule("----")

    refreshed_metadata = refresh_state_metadata_and_report(state, source_by_name.values(), config.state_file, dry_run=dry_run)
    if refreshed_metadata:
        _human_rule("----")


    sync_floor_name: str | None = None
    if not destination_empty_at_start and not only_snapshot:
        sync_floor_name = confirmed_existing_floor_name
        sync_floor_reason = confirmed_existing_floor_reason
        print(f"Sync floor: confirmed {sync_floor_name} ({sync_floor_reason})")
        print("Source snapshots older than or equal to this floor are skipped, so pruned destination snapshots are not re-sent.")
        _human_rule("----")

    def build_snapshot_queue(*, require_requested_snapshot: bool) -> list[SnapshotMeta]:
        """Build the current oldest-to-newest queue from the latest inventory."""

        if only_snapshot:
            selected = source_by_name.get(only_snapshot)
            if selected is None:
                if require_requested_snapshot:
                    raise SyncError(f"Source snapshot not found: {only_snapshot}")
                return []
            return [selected]
        if destination_empty_at_start:
            return _snapshots_in_sync_order(_select_initial_sync_snapshots(config, source_by_name))
        return _snapshots_in_sync_order(source_by_name.values())

    snapshot_queue = build_snapshot_queue(require_requested_snapshot=True)
    transferred = 0
    already_synced = 0
    sync_events: list[dict] = []

    # Tracks source parent paths that were successfully sent and received during
    # this run. When verify_incremental_parent_once_per_run is true, those freshly
    # created paths can be reused as the next parent without re-reading metadata.
    # Parent paths from previous runs are still validated against destination
    # received_uuid before use.
    trusted_parent_send_paths: set[str] = set()

    skipped_by_floor_names: set[str] = set()
    counted_already: set[tuple[str, str]] = set()
    source_change_retries: dict[tuple[str, str], int] = {}

    def recover_from_source_inventory_change(
        *,
        failed_snapshot: SnapshotMeta,
        subvolume_name: str,
        refreshed_inventory: remote_index.SourceInventory,
        refreshed_source_by_name: dict[str, SnapshotMeta],
        required_changes: list[str],
        inventory_changes: list[str],
        operation: str,
        original_error: Exception,
    ) -> None:
        """Recover one failed snapshot version and rebuild all source lists.

        Recovery is deliberately snapshot-wide because configured subvolumes
        such as ``@`` and ``@home`` must remain one Timeshift date version. The
        helper also removes in-run success accounting for that version because
        recovery deletes its cache, destination paths, and state entries before
        the rebuilt oldest-to-newest queue is evaluated again.
        """

        nonlocal source_inventory
        nonlocal source_by_name
        nonlocal snapshot_root_btrfs_index
        nonlocal source_cache_index
        nonlocal snapshot_queue
        nonlocal transferred
        nonlocal already_synced

        retry_key = (failed_snapshot.name, subvolume_name)
        retry_number = source_change_retries.get(retry_key, 0) + 1
        source_change_retries[retry_key] = retry_number

        _human_blank()
        print("SOURCE INVENTORY CHANGED DURING TRANSFER PREPARATION" if operation != "send/receive" else "SOURCE INVENTORY CHANGED DURING TRANSFER")
        print(f"  failed item: {failed_snapshot.name}/{subvolume_name}")
        print(f"  operation:   {operation}")
        print(f"  retry:       {retry_number}/{config.source.source_change_retry_count}")
        print("  required path change(s):")
        for change in required_changes:
            print(f"    - {change}")
        if inventory_changes:
            print("  complete inventory difference:")
            for change in inventory_changes:
                print(f"    - {change}")
        print("  action:      clean the incomplete snapshot version, rebuild all source lists, and continue oldest-to-newest")
        _human_rule("---")

        if retry_number > config.source.source_change_retry_count:
            raise SyncError(
                "Source Timeshift/cache metadata kept changing while work was in progress and the automatic "
                f"retry limit was exhausted for {failed_snapshot.name}/{subvolume_name}. "
                f"Configured source.source_change_retry_count={config.source.source_change_retry_count}.\n\n"
                + "\n".join(required_changes)
            ) from original_error

        source_inventory = refreshed_inventory
        source_by_name = refreshed_source_by_name
        snapshot_root_btrfs_index = source_inventory.snapshot_index
        source_cache_index = source_inventory.cache_index
        refreshed_snapshot = source_by_name.get(failed_snapshot.name)
        source_still_exists = bool(
            refreshed_snapshot
            and all(
                snapshot_root_btrfs_index.meta(
                    _expected_original_source_path(config, failed_snapshot.name, required_name)
                )
                for required_name in config.source.subvolumes
            )
        )

        removed_events = [event for event in sync_events if event.get("snapshot") == failed_snapshot.name]
        removed_transfers = sum(1 for event in removed_events if event.get("status") == "synced")
        if removed_events:
            sync_events[:] = [event for event in sync_events if event.get("snapshot") != failed_snapshot.name]
        if removed_transfers:
            transferred = max(0, transferred - removed_transfers)
            print(f"  accounting:  removed {removed_transfers} prior in-run success event(s) because recovery deletes the whole snapshot version")
        counted_already.difference_update(
            key for key in tuple(counted_already) if key[0] == failed_snapshot.name
        )
        already_synced = len(counted_already)

        _recover_snapshot_version(
            config,
            source,
            state,
            failed_snapshot.name,
            reason=f"required source path changed during {operation}: " + "; ".join(required_changes),
            source_still_exists=source_still_exists,
            dry_run=False,
            source_cache_index=source_cache_index,
            destination_index=destination_index,
        )

        # Recovery changed source.cache_root and destination.target_root. Rebuild
        # the complete combined source inventory once more so parent comparison
        # and the restarted queue never use pre-cleanup metadata.
        source_inventory, source_by_name = load_source_inventory(
            f"after recovery cleanup for {failed_snapshot.name}/{subvolume_name}"
        )
        snapshot_root_btrfs_index = source_inventory.snapshot_index
        source_cache_index = source_inventory.cache_index
        trusted_parent_send_paths.intersection_update(
            path for path in tuple(trusted_parent_send_paths) if source_inventory.meta(path) is not None
        )
        snapshot_queue = build_snapshot_queue(require_requested_snapshot=False)
        print(f"  rebuilt queue: {len(snapshot_queue)} snapshot(s) currently available")
        print("  continuation:  restarting queue evaluation; surviving completed destination/state entries will be skipped")
        _human_rule("---")

    while snapshot_queue:
        snapshot = snapshot_queue.pop(0)
        expected = list(config.source.subvolumes)

        # Backfill or refresh metadata for every complete destination snapshot
        # still present in the current source inventory, including snapshots at
        # or below the prune-safe sync floor.
        if _snapshot_state_is_complete_with_destination(config, state, snapshot.name):
            _sync_snapshot_info_json(
                config,
                source_inventory,
                snapshot.name,
                dry_run=dry_run,
            )

        if sync_floor_name and snapshot.name <= sync_floor_name:
            skipped_by_floor_names.add(snapshot.name)
            continue

        if only_missing and snapshot_is_synced(state, snapshot.name, expected):
            if _snapshot_destination_paths_exist(config, snapshot.name, expected):
                for subvolume_name in expected:
                    counted_already.add((snapshot.name, subvolume_name))
                already_synced = len(counted_already)
                continue
            print(f"Snapshot {snapshot.name}: state says synced, but at least one destination path is missing; recovering the whole date version before retry.")
            _human_blank()
        if limit is not None and transferred >= limit:
            break

        _require_snapshot_info_json(source_inventory, snapshot.name)
        target_dir = _target_snapshot_dir(config, snapshot.name)
        print(f"Snapshot {snapshot.name} tags={''.join(snapshot.tags) or '-'}")
        _human_blank()
        if dry_run:
            print(f"  would ensure destination date Btrfs subvolume: {target_dir}")
            print(f"  info.json: would create or refresh {target_dir / 'info.json'} after all configured subvolumes succeed")
            _human_blank()

        if not _prepare_snapshot_for_transfer_or_recover(
            config,
            source,
            state,
            snapshot,
            dry_run=dry_run,
            source_cache_index=source_cache_index,
            source_snapshot_index=snapshot_root_btrfs_index,
            destination_index=destination_index,
        ):
            continue

        for subvol_name in config.source.subvolumes:
            # Incomplete destination cleanup is intentionally performed here,
            # inside the already sorted snapshot loop. This matters for failed
            # on-demand snapshots too: the app does not jump them ahead or
            # handle them specially. It deletes only the partial destination
            # path for the current snapshot/subvolume, then sends it when the
            # normal oldest-to-newest order reaches that exact item.
            subvolume = snapshot.subvolumes.get(subvol_name)
            if not subvolume:
                continue
            dest_path = _dest_subvolume_path(config, snapshot.name, subvol_name)
            already = state.get("snapshots", {}).get(snapshot.name, {}).get("subvolumes", {}).get(subvol_name)
            if already and already.get("status") == "ok" and dest_path.exists():
                counted_already.add((snapshot.name, subvol_name))
                already_synced = len(counted_already)
                print(f"  {subvol_name}: already synced")
                _human_blank()
                continue
            if dest_path.exists() and not dry_run:
                if state_empty_at_start:
                    raise SyncError(
                        "Destination subvolume exists but state.json was missing/empty and this "
                        "subvolume could not be adopted by exact UUID match. Refusing to delete it "
                        "as an incomplete receive because it may be a valid backup. Inspect or move "
                        "the existing path, or restore the matching state/source cache before retrying:\n"
                        f"  {dest_path}"
                    )
                _cleanup_incomplete_destination_receive(config, dest_path, subvol_name, destination_index)

            parent_name, parent_send_path = _select_parent(
                config,
                source,
                state,
                source_by_name,
                snapshot,
                subvol_name,
                dry_run=dry_run,
                trusted_parent_send_paths=trusted_parent_send_paths,
                allow_full_seed=destination_empty_at_start,
                source_cache_index=source_cache_index,
                source_snapshot_index=snapshot_root_btrfs_index,
                destination_index=destination_index,
            )
            if dry_run:
                current_send_path = _preview_send_path(config, snapshot.name, subvolume)
            else:
                inventory_before_prepare = source_inventory
                try:
                    current_send_path = _ensure_source_send_path(
                        config,
                        source,
                        snapshot.name,
                        subvolume,
                        source_cache_index,
                        snapshot_root_btrfs_index,
                    )
                except Exception as prepare_exc:
                    try:
                        refreshed_inventory, refreshed_source_by_name = load_source_inventory(
                            f"after failed send-path preparation {snapshot.name}/{subvol_name}"
                        )
                    except Exception as refresh_exc:
                        raise SyncError(
                            "Send-path preparation failed and the source inventory could not be rebuilt. "
                            "The app cannot safely decide whether a Timeshift/cache path disappeared.\n\n"
                            f"Preparation error: {prepare_exc}\n"
                            f"Inventory refresh error: {refresh_exc}"
                        ) from prepare_exc

                    inventory_changes = remote_index.describe_source_inventory_changes(
                        inventory_before_prepare,
                        refreshed_inventory,
                    )
                    sibling_paths = tuple(
                        (
                            f"snapshot sibling {required_name}",
                            _expected_original_source_path(config, snapshot.name, required_name),
                        )
                        for required_name in config.source.subvolumes
                        if required_name != subvol_name
                    )
                    required_changes = _required_pipeline_source_changes(
                        inventory_before_prepare,
                        refreshed_inventory,
                        current_path=subvolume.path,
                        parent_path=parent_send_path,
                        additional_paths=sibling_paths,
                    )
                    cache_candidate = _preview_send_path(config, snapshot.name, subvolume)
                    if (
                        cache_candidate != subvolume.path
                        and inventory_before_prepare.meta(cache_candidate) is None
                        and refreshed_inventory.meta(cache_candidate) is not None
                    ):
                        required_changes.append(
                            f"send-cache target appeared concurrently: {cache_candidate}"
                        )

                    if required_changes:
                        recover_from_source_inventory_change(
                            failed_snapshot=snapshot,
                            subvolume_name=subvol_name,
                            refreshed_inventory=refreshed_inventory,
                            refreshed_source_by_name=refreshed_source_by_name,
                            required_changes=required_changes,
                            inventory_changes=inventory_changes,
                            operation="send-path/cache preparation",
                            original_error=prepare_exc,
                        )
                        break

                    if inventory_changes:
                        _human_blank()
                        print("SOURCE INVENTORY CHANGED, BUT NOT THE FAILED PREPARATION PATHS")
                        for change in inventory_changes:
                            print(f"  - {change}")
                        print("  action: unrelated churn is not a source-change retry reason; preserving the existing one-time cache cleanup/retry policy")
                        _human_rule("---")

                    # Preserve the existing one-time cleanup/retry behavior for a
                    # cache/probe failure when all required source identities are
                    # unchanged. Use the newly rebuilt inventory rather than stale
                    # per-path metadata, then let a second failure propagate.
                    source_inventory = refreshed_inventory
                    source_by_name = refreshed_source_by_name
                    snapshot_root_btrfs_index = source_inventory.snapshot_index
                    source_cache_index = source_inventory.cache_index
                    refreshed_snapshot = source_by_name.get(snapshot.name)
                    if refreshed_snapshot is None:
                        raise prepare_exc
                    snapshot = refreshed_snapshot
                    found, missing = _refresh_snapshot_source_subvolumes_live(
                        config,
                        source,
                        snapshot,
                        snapshot_root_btrfs_index,
                    )
                    if missing:
                        raise prepare_exc
                    snapshot.subvolumes = found
                    _recover_snapshot_version(
                        config,
                        source,
                        state,
                        snapshot.name,
                        reason=f"send-cache creation/probe failed while source identities remained unchanged: {prepare_exc}",
                        source_still_exists=True,
                        dry_run=False,
                        source_cache_index=source_cache_index,
                        destination_index=destination_index,
                    )
                    source_inventory, source_by_name = load_source_inventory(
                        f"after unchanged-source preparation recovery for {snapshot.name}/{subvol_name}"
                    )
                    snapshot_root_btrfs_index = source_inventory.snapshot_index
                    source_cache_index = source_inventory.cache_index
                    snapshot = source_by_name.get(snapshot.name) or snapshot
                    subvolume = snapshot.subvolumes[subvol_name]
                    current_send_path = _ensure_source_send_path(
                        config,
                        source,
                        snapshot.name,
                        subvolume,
                        source_cache_index,
                        snapshot_root_btrfs_index,
                    )
            mode = "incremental" if parent_send_path else "full"

            if dry_run:
                _record_sync_event(
                    sync_events,
                    mode=mode,
                    snapshot=snapshot,
                    subvolume_name=subvol_name,
                    source_path=current_send_path,
                    destination_path=dest_path,
                    parent_name=parent_name,
                    parent_send_path=parent_send_path,
                    status="planned",
                )
                parent_text = f" parent={parent_name}" if parent_name else ""
                print(f"  {subvol_name}: would {mode} send{parent_text}")
                print()
                print(f"    source: {current_send_path}")
                print(f"    source-kind: {_send_path_kind_text(config, current_send_path, subvolume.path)}")
                print()
                print(f"    dest:   {dest_path}")
                if parent_name:
                    print()
                    print("    safety: real run verifies the selected parent send_path or original source UUID against destination received_uuid")
                if config.stream.use_mbuffer:
                    print()
                    print(f"    stream: would use {' '.join(config.stream.command() or [])}")
                if config.stream.btrfs_verbose:
                    print()
                    print("    btrfs: would add -v to send/receive and show operation output live")
                _human_rule("---")
                continue

            # Save the exact path that will be streamed. After receive, state is
            # updated with both original-source and send-path UUID metadata so a
            # later run can establish a prune-safe high-watermark without keeping
            # tombstones for every deleted destination snapshot.
            subvolume.send_path = current_send_path

            # Create the local receive directory only after parent selection.
            # This prevents an empty in-progress directory from being mistaken as
            # an existing backup by the safety guard.
            target_dir = _ensure_destination_snapshot_subvolume(config, snapshot.name, destination_index)
            _human_blank()
            print(f"  {subvol_name}: {mode} send/receive")
            print(f"    source-kind: {_send_path_kind_text(config, current_send_path, subvolume.path)}")
            # Build source send command. If parent_send_path is set, btrfs send
            # receives `-p <parent>` and sends an incremental stream.
            send_cmd = btrfs.source_send_cmd(
                source,
                sudo=config.source.sudo,
                btrfs_command=config.source.btrfs_command,
                current_path=current_send_path,
                parent_path=parent_send_path,
                compressed_data=config.source.send_compressed_data,
                proto=config.source.send_proto,
                verbose=config.stream.btrfs_verbose,
            )

            # Build local receive command. Destination compression is left to
            # the filesystem mount/property policy outside this app.
            receive_cmd = btrfs.local_receive_cmd(
                target_dir,
                config.destination.sudo,
                config.destination.btrfs_command,
                verbose=config.stream.btrfs_verbose,
            )

            # Optional mbuffer is inserted as the middle command. Password auth
            # environment is passed to the source side so streamed sends work
            # with sshpass in SSH mode. Local mode uses no extra environment.
            inventory_before_send = source_inventory
            try:
                stream_pipeline(
                    send_cmd,
                    receive_cmd,
                    middle_cmd=config.stream.command(),
                    verbose=True,
                    left_env=source.environment(),
                    # If stream.btrfs_verbose is enabled, let Btrfs operation
                    # output appear live in the terminal. mbuffer remains the real
                    # byte/throughput progress display.
                    passthrough_right_stdout=config.stream.btrfs_verbose,
                )
            except CommandError as pipeline_exc:
                try:
                    refreshed_inventory, refreshed_source_by_name = load_source_inventory(
                        f"after failed transfer {snapshot.name}/{subvol_name}"
                    )
                except Exception as refresh_exc:
                    raise SyncError(
                        "The send/receive pipeline failed and the source inventory could not be rebuilt. "
                        "The app cannot safely decide whether a Timeshift/cache parent disappeared.\n\n"
                        f"Pipeline error: {pipeline_exc}\n"
                        f"Inventory refresh error: {refresh_exc}"
                    ) from pipeline_exc

                inventory_changes = remote_index.describe_source_inventory_changes(
                    inventory_before_send,
                    refreshed_inventory,
                )
                required_changes = _required_pipeline_source_changes(
                    inventory_before_send,
                    refreshed_inventory,
                    current_path=current_send_path,
                    parent_path=parent_send_path,
                )
                if not required_changes:
                    if inventory_changes:
                        _human_blank()
                        print("SOURCE INVENTORY CHANGED, BUT NOT THE FAILED PIPELINE PATHS")
                        for change in inventory_changes:
                            print(f"  - {change}")
                        print("  action: preserving the original pipeline failure; unrelated snapshot churn is not treated as a retry reason")
                        _human_rule("---")
                    raise

                recover_from_source_inventory_change(
                    failed_snapshot=snapshot,
                    subvolume_name=subvol_name,
                    refreshed_inventory=refreshed_inventory,
                    refreshed_source_by_name=refreshed_source_by_name,
                    required_changes=required_changes,
                    inventory_changes=inventory_changes,
                    operation="send/receive",
                    original_error=pipeline_exc,
                )
                break
            _human_rule("---")

            received_meta = None
            original_meta = None
            send_meta = None
            if dest_path.exists():
                try:
                    received_meta = remote_index.refresh_local_path(
                        destination_index,
                        dest_path,
                        name=subvol_name,
                        sudo=config.destination.sudo,
                        btrfs_command=config.destination.btrfs_command,
                    )
                except Exception:
                    received_meta = None

            # Save both the original Timeshift source UUID and the exact send-path
            # UUID. When source cache is used, those are different subvolumes. This
            # metadata lets later runs establish a prune-safe high-watermark without
            # maintaining tombstones for every deleted destination snapshot.
            try:
                original_meta = _source_meta(
                    config,
                    source,
                    subvolume.path,
                    subvol_name,
                    required=False,
                    source_snapshot_index=snapshot_root_btrfs_index,
                    source_cache_index=source_cache_index,
                )
            except Exception:
                original_meta = None
            try:
                if source_cache_index is not None and btrfs.path_is_under_cache(current_send_path, config.source.cache_root):
                    send_meta = source_cache_index.meta(current_send_path) or remote_index.refresh_source_path(
                        source_cache_index,
                        source,
                        current_send_path,
                        name=subvol_name,
                        sudo=config.source.sudo,
                        btrfs_command=config.source.btrfs_command,
                    )
                else:
                    send_meta = _source_meta(
                        config,
                        source,
                        current_send_path,
                        subvol_name,
                        required=False,
                        source_snapshot_index=snapshot_root_btrfs_index,
                        source_cache_index=source_cache_index,
                    )
            except Exception:
                send_meta = None

            mark_subvolume_synced(
                state,
                snapshot=snapshot,
                subvolume=subvolume,
                destination_path=dest_path,
                destination_root=config.destination.target_root,
                snapshot_root=config.source.snapshot_root,
                cache_root=config.source.cache_root,
                parent_snapshot=parent_name,
                parent_source_path=parent_send_path,
                send_path=current_send_path,
                received_meta=received_meta,
                original_meta=original_meta,
                send_meta=send_meta,
            )
            save_state(config.state_file, state)
            trusted_parent_send_paths.add(current_send_path)
            _record_sync_event(
                sync_events,
                mode=mode,
                snapshot=snapshot,
                subvolume_name=subvol_name,
                source_path=current_send_path,
                destination_path=dest_path,
                parent_name=parent_name,
                parent_send_path=parent_send_path,
                status="synced",
            )

            # Keep every source-side read-only cache snapshot created by this
            # run. Cache snapshots are pruned only by the retention step, using
            # the same keep/delete decision as destination snapshots. This avoids
            # losing the newest common source/destination UUID merely because a
            # short-lived hourly parent was superseded during sync.

            transferred += 1

        if _snapshot_state_is_complete_with_destination(config, state, snapshot.name):
            _sync_snapshot_info_json(
                config,
                source_inventory,
                snapshot.name,
                dry_run=dry_run,
            )

    _human_rule("----")
    skipped_by_floor = len(skipped_by_floor_names)
    if skipped_by_floor:
        print(f"Skipped {skipped_by_floor} source snapshot(s) at or below confirmed sync floor.")
    print("No missing subvolumes to sync." if transferred == 0 else f"Synced {transferred} subvolume(s).")
    print()
    _print_sync_summary(
        sync_events,
        dry_run=dry_run,
        skipped_by_floor=skipped_by_floor,
        already_synced=already_synced,
    )
    return transferred
