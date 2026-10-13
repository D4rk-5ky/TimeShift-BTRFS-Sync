"""Reconcile proven pairs and retire authorized one-sided cache/destination leftovers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath
import shlex
import re
from datetime import datetime

from . import inventory
from .btrfs_ops import BtrfsOps
from .cache_ops import cache_parent_path, cache_child_path
from .config import AppConfig
from .endpoint import CommandEndpoint
from .listing import _discover_repository
from .models import SnapshotMeta, SubvolumeMeta, send_stream_uuid
from .paths import is_same_or_under
from .source import SourceRunner
from .state import resolve_state_send_path, resolve_destination_path, snapshot_is_synced, refresh_state_metadata_and_report
from .timeshift import SNAPSHOT_RE
from .tree_ops import delete_subvolume_tree, discover_subvolume_tree, NativeCacheDeletionProof


@dataclass(slots=True)
class ReconciliationContext:
    """One validated inventory generation shared by recovery and bounded cleanup."""

    source: SourceRunner
    source_inventory: inventory.SourceInventory
    source_by_name: dict[str, SnapshotMeta]
    destination_index: inventory.BtrfsIndex
    destination_records: dict


@dataclass(slots=True)
class RedundantCacheResult:
    """Keep one-sided repository cleanup outcomes separate from paired/state deletion."""

    candidates: int = 0
    attempted: int = 0
    completed: int = 0
    blocked: list[str] = field(default_factory=list)
    skipped_reason: str = ""


def refresh_repository_indexes(config: AppConfig, source: SourceRunner, built: inventory.SourceInventory) -> tuple[inventory.BtrfsIndex, dict]:
    """Reuse scoped discovery so date-container children cannot be missing from reconciliation indexes."""

    source_ops = BtrfsOps(CommandEndpoint.for_source(source), config.source.sudo, config.source.btrfs_command)
    source_uuid = None
    if not built.snapshot_index.root_missing:
        original, _records, _notes, source_uuid, _device = _discover_repository(source_ops, config.source.snapshot_root)
        if original.errors:
            raise RuntimeError("Incomplete source snapshot inventory; reconciliation/deletion refused: " + "; ".join(original.errors))
        built.snapshot_index = original
    if config.source.cache_root:
        built.cache_index, _records, _notes, cache_uuid, _device = _discover_repository(source_ops, config.source.cache_root)
        if built.cache_index.errors:
            raise RuntimeError("Incomplete source cache inventory; reconciliation/deletion refused: " + "; ".join(built.cache_index.errors))
        source_uuid = source_uuid or cache_uuid
    timeshift_uuid = re.search(r"^\s*UUID\s*:\s*([0-9a-fA-F-]{36})", built.timeshift_output, re.MULTILINE)
    if timeshift_uuid and source_uuid and timeshift_uuid.group(1).lower() != source_uuid.lower():
        raise RuntimeError("Timeshift filesystem UUID differs from configured source repository; reconciliation/deletion refused")
    target_ops = BtrfsOps(CommandEndpoint.local(), config.destination.sudo, config.destination.btrfs_command)
    target, records, _notes, _uuid, _device = _discover_repository(target_ops, str(config.destination.target_root / "snapshots"))
    if target.errors:
        raise RuntimeError("Incomplete destination inventory; reconciliation/deletion refused: " + "; ".join(target.errors))
    return target, records


def prepare_reconciliation(config: AppConfig, state: dict, *, dry_run: bool) -> ReconciliationContext:
    """Load complete scoped Btrfs views and recover missing pairs before retention decisions."""

    from .sync import _recover_state_from_existing_destination, _snapshots_from_source_inventory, _validate_destination_snapshot_layout

    source = SourceRunner.from_config(config)
    built = inventory.build_source_inventory(
        source, snapshot_root=config.source.snapshot_root, cache_root=config.source.cache_root,
        sudo=config.source.sudo, btrfs_command=config.source.btrfs_command,
        timeshift_command=config.source.timeshift_command, required=True,
    )
    target, records = refresh_repository_indexes(config, source, built)
    _validate_destination_snapshot_layout(config, target)
    source_by_name = _snapshots_from_source_inventory(config, source, built)
    refresh_state_metadata_and_report(state, source_by_name.values(), config.state_file, dry_run=dry_run)
    _recover_state_from_existing_destination(
        config, source, state, source_by_name, dry_run=dry_run,
        source_cache_index=built.cache_index, source_snapshot_index=built.snapshot_index,
        destination_index=target, destination_records=records,
    )
    return ReconciliationContext(source, built, source_by_name, target, records)


def _destination_date_absent(config: AppConfig, name: str) -> bool:
    """Prove date absence with ordinary traversal; denied access is never interpreted as absence."""

    root = shlex.quote(str(config.destination.target_root / "snapshots"))
    path = shlex.quote(str(config.destination.target_root / "snapshots" / name))
    result = CommandEndpoint.local().run_shell(
        f"[ -d {root} ] && [ -r {root} ] && [ -x {root} ] && [ ! -L {root} ] && [ ! -e {path} ] && [ ! -L {path} ]",
        check=False, log_stderr=False, mirror_stderr=False,
    )
    return result.returncode == 0


def _protected_cache_dates(config: AppConfig, state: dict) -> set[str]:
    """Protect tracked dates, explicit exclusions and parents of incomplete transfers."""

    protected = set(state.get("snapshots", {})) | set(config.retention.protected_snapshots)
    for name, snapshot in state.get("snapshots", {}).items():
        if snapshot_is_synced(state, name, config.source.subvolumes):
            continue
        for payload, subvolume in snapshot.get("subvolumes", {}).items():
            if subvolume.get("parent_snapshot"):
                protected.add(subvolume["parent_snapshot"])
            if subvolume.get("send_path"):
                path = resolve_state_send_path(subvolume, snapshot_root=config.source.snapshot_root,
                                               cache_root=config.source.cache_root, snapshot_name=name,
                                               subvolume_name=payload)
                if config.source.cache_root and is_same_or_under(path, config.source.cache_root):
                    relative = PurePosixPath(path).relative_to(config.source.cache_root)
                    if relative.parts:
                        protected.add(relative.parts[0])
    return protected


def _confirmed_window(config: AppConfig, state: dict, context: ReconciliationContext) -> tuple[str, str] | None:
    """Bound cleanup by state dates that still have complete immutable UUID-confirmed pairs."""

    from .sync import _find_confirmed_sync_floor

    confirmed = []
    for name, snapshot in sorted(state.get("snapshots", {}).items()):
        if not SNAPSHOT_RE.fullmatch(name):
            continue
        found, _reason = _find_confirmed_sync_floor(
            config, context.source, {"snapshots": {name: snapshot}}, context.source_by_name,
            source_cache_index=context.source_inventory.cache_index,
            source_snapshot_index=context.source_inventory.snapshot_index,
            destination_index=context.destination_index,
        )
        if found:
            confirmed.append(name)
    return (confirmed[0], confirmed[-1]) if confirmed else None


def _verified_managed_cache_root(config: AppConfig, state: dict, context: ReconciliationContext, ops: BtrfsOps) -> tuple[SubvolumeMeta | None, str]:
    """Anchor a dedicated native cache to canonical state paths and complete received UUID pairs."""

    root = config.source.cache_root
    assert root is not None
    if root == "/" or is_same_or_under(root, config.source.snapshot_root) or is_same_or_under(config.source.snapshot_root, root):
        return None, "cache root overlaps protected Timeshift storage"
    cache = context.source_inventory.cache_index
    assert cache is not None
    meta = ops.meta(root, required=False)
    if not meta or not meta.uuid or not meta.subvolume_id or meta.subvolume_id < 256 or meta.parent_uuid or meta.received_uuid:
        return None, "cache_root is not a verified native Btrfs container"
    original_root = ops.meta(config.source.snapshot_root, required=False)
    if ((original_root and original_root.uuid == meta.uuid)
            or set(cache.by_uuid) & set(context.source_inventory.snapshot_index.by_uuid)):
        return None, "cache native identities overlap protected Timeshift snapshots"
    tree, errors = discover_subvolume_tree(ops, root)
    if errors or set(tree) != {root, *cache.by_path}:
        return None, "cache containment differs from the complete inventory"
    confirmed = _confirmed_window(config, state, context)
    if not confirmed:
        return None, "no UUID-confirmed state/receiver pairs"
    anchored = 0
    for name, snapshot in state.get("snapshots", {}).items():
        if not snapshot_is_synced(state, name, config.source.subvolumes):
            return None, "incomplete transfer state remains"
        fields = snapshot.get("subvolumes", {})
        if not all(fields.get(payload, {}).get("send_path_kind") == "source-cache" for payload in config.source.subvolumes):
            continue
        for payload in config.source.subvolumes:
            saved = fields[payload]
            path = cache_child_path(root, name, payload)
            if resolve_state_send_path(saved, snapshot_root=config.source.snapshot_root, cache_root=root,
                                       snapshot_name=name, subvolume_name=payload) != path:
                return None, "state cache path is not canonical for this root"
            if resolve_destination_path(config.destination.target_root, saved.get("destination_path", "")) != config.destination.target_root / "snapshots" / name / payload:
                return None, "state receiver path is not canonical for this destination"
            sender = cache.meta(path)
            receiver = context.destination_index.meta(str(config.destination.target_root / "snapshots" / name / payload))
            if (not sender or not receiver or not sender.uuid or sender.readonly is not True or receiver.readonly is not True
                    or saved.get("send_source_uuid") != sender.uuid or receiver.received_uuid != sender.uuid):
                return None, "state/cache/destination UUIDs do not all match"
            live = ops.meta(path, required=False)
            if not live or live.uuid != sender.uuid or live.subvolume_id != sender.subvolume_id or live.readonly is not True:
                return None, "paired cache identity changed since discovery"
        anchored += 1
    if not anchored:
        return None, "no complete state pair anchors this cache_root"
    return meta, ""


def _native_identity_matches(saved: SubvolumeMeta, live: SubvolumeMeta | None) -> bool:
    """Require stable UUID, native ID, readonly state and lineage for either repository side."""

    return bool(live and saved.uuid and saved.subvolume_id and live.uuid == saved.uuid
                and live.subvolume_id == saved.subvolume_id and live.readonly == saved.readonly
                and live.parent_uuid == saved.parent_uuid and live.received_uuid == saved.received_uuid)


def _safe_native_cache_date(config: AppConfig, context: ReconciliationContext, name: str, ops: BtrfsOps) -> str | None:
    """Accept a dated RO snapshot or native container of RO snapshots, including partial legacy caches."""

    cache = context.source_inventory.cache_index
    assert cache is not None and config.source.cache_root is not None
    parent = cache_parent_path(config.source.cache_root, name)
    tree = {path: meta for path, meta in cache.by_path.items() if is_same_or_under(path, parent)}
    if parent not in tree:
        return "date is not a native Btrfs subvolume"
    readonly_snapshots = 0
    for path, saved in tree.items():
        live = ops.meta(path, required=False)
        if not _native_identity_matches(saved, live) or live.received_uuid:
            return "native cache subtree identity changed or became unavailable"
        if path == parent and live.readonly is False and not live.parent_uuid:
            continue  # App-created date container; its payload snapshots are RO.
        if live.readonly is not True or not live.parent_uuid:
            return "cache subtree contains a writable or unproven snapshot"
        readonly_snapshots += 1
        original = context.source_inventory.snapshot_index.meta(str(PurePosixPath(config.source.snapshot_root) / name / PurePosixPath(path).relative_to(parent)))
        if original and original.uuid and original.uuid != live.parent_uuid:
            return "cache snapshot differs from its known Timeshift original"
    return None if readonly_snapshots else "no readonly native snapshot in dated cache subtree"


def _safe_cache_date(config: AppConfig, context: ReconciliationContext, name: str, ops: BtrfsOps, *, native_owned: bool = False) -> str | None:
    """Recheck exact cache UUIDs, native snapshot layout and ordinary entries before deletion."""

    root = config.source.cache_root
    assert root is not None
    parent = cache_parent_path(root, name)
    if is_same_or_under(parent, config.source.snapshot_root) or is_same_or_under(config.source.snapshot_root, parent):
        return "cache overlaps protected Timeshift root"
    if native_owned:
        return _safe_native_cache_date(config, context, name, ops)
    # Inspect every cache path component: Btrfs follows path symlinks, while
    # ordinary read-only checks can reject them without granting sudo shell.
    paths = list(reversed(PurePosixPath(parent).parents)) + [PurePosixPath(parent)]
    checks = " && ".join(f"[ ! -L {shlex.quote(str(path))} ]" for path in paths)
    allowed = "|".join(shlex.quote(payload) for payload in [*config.source.subvolumes, "info.json"])
    qparent = shlex.quote(parent)
    script = f"""{checks} && [ -r {qparent} ] && [ -x {qparent} ] || exit 1
for entry in {qparent}/* {qparent}/.[!.]* {qparent}/..?*; do
    [ -e "$entry" ] || [ -L "$entry" ] || continue
    [ ! -L "$entry" ] || exit 2
    case "${{entry##*/}}" in {allowed}) ;; *) exit 3 ;; esac
    if [ "${{entry##*/}}" = info.json ]; then [ -f "$entry" ] || exit 4; fi
done"""
    if not native_owned:
        result = ops.endpoint.run_shell(script, check=False, log_stderr=False, mirror_stderr=False)
        if result.returncode:
            return "cache traversal, symlink or unknown ordinary-entry check failed"
    cache = context.source_inventory.cache_index
    assert cache is not None
    saved_parent = cache.meta(parent)
    live_parent = ops.meta(parent, required=False)
    if (not saved_parent or not live_parent or not saved_parent.uuid or live_parent.uuid != saved_parent.uuid
            or live_parent.received_uuid or live_parent.parent_uuid
            or (native_owned and (not saved_parent.subvolume_id or live_parent.subvolume_id != saved_parent.subvolume_id))):
        return "date container is not an unchanged native app-cache subvolume"
    for payload in config.source.subvolumes:
        path = cache_child_path(root, name, payload)
        saved, live = cache.meta(path), ops.meta(path, name=payload, required=False)
        if (not saved or not live or not live.uuid or live.uuid != saved.uuid or live.readonly is not True
                or not live.parent_uuid or live.parent_uuid != saved.parent_uuid or live.received_uuid
                or (native_owned and (not saved.subvolume_id or live.subvolume_id != saved.subvolume_id))):
            return f"{payload}: immutable native cache snapshot identity could not be re-proven"
        original = context.source_inventory.snapshot_index.meta(str(PurePosixPath(config.source.snapshot_root) / name / payload))
        if original and original.uuid and live.parent_uuid != original.uuid:
            return f"{payload}: cache does not match the known Timeshift original"
    return None


def cleanup_redundant_cache(config: AppConfig, state: dict, context: ReconciliationContext, *, dry_run: bool, yes_delete: bool, successful_sync: bool = False) -> RedundantCacheResult:
    """After successful sync, delete proven stale native cache dates no newer than the latest pair."""

    result = RedundantCacheResult()
    if not (config.source.delete_redundant_snapshots and config.source.cleanup_superseded_cache and config.source.cache_root):
        return result
    if not dry_run and not successful_sync:
        result.skipped_reason = "requires a successful sync in this run"
        print("Redundant cache cleanup: skipped; " + result.skipped_reason)
        return result
    # Paired retention ran first and may have removed dates from both sides.
    # Refresh the two physical views before trusting ownership or absence.
    ops = BtrfsOps(CommandEndpoint.for_source(context.source), config.source.sudo, config.source.btrfs_command)
    cache, _cache_records, _notes, _uuid, _device = _discover_repository(ops, config.source.cache_root)
    target_ops = BtrfsOps(CommandEndpoint.local(), config.destination.sudo, config.destination.btrfs_command)
    target, records, _notes, _uuid, _device = _discover_repository(target_ops, str(config.destination.target_root / "snapshots"))
    if cache.errors or target.errors:
        result.skipped_reason = "fresh source/destination inventory incomplete"
        print("Redundant cache cleanup: skipped; " + result.skipped_reason)
        return result
    context.source_inventory.cache_index = cache
    context.destination_index, context.destination_records = target, records
    window = _confirmed_window(config, state, context)
    cache = context.source_inventory.cache_index
    if not window or cache is None or cache.root_missing or cache.errors or context.destination_index.errors:
        print("Redundant cache cleanup: no complete verified window/inventory; cache preserved")
        return result
    protected = _protected_cache_dates(config, state)
    names = {PurePosixPath(path).relative_to(config.source.cache_root).parts[0]
             for path in cache.by_path if is_same_or_under(path, config.source.cache_root)
             and PurePosixPath(path) != PurePosixPath(config.source.cache_root)}
    candidates = sorted(name for name in names if SNAPSHOT_RE.fullmatch(name) and name <= window[1] and name not in protected)
    result.candidates = len(candidates)
    if candidates and not dry_run and not yes_delete:
        raise RuntimeError("Refusing redundant cache deletion without --yes-delete")
    print(f"Redundant cache cleanup: confirmed pairs {window[0]} .. {window[1]}; {len(candidates)} untracked date(s) no newer than latest pair")
    if dry_run:
        print("  preview only: real redundant deletion requires successful sync before cleanup")
    owned_root, ownership_error = _verified_managed_cache_root(config, state, context, ops)
    if not owned_root:
        result.blocked = [f"{name}: {ownership_error}" for name in candidates]
        for reason in result.blocked:
            print(f"  [KEEP] {reason}")
        return result
    print("  ownership: native cache root, state and received UUID pairs confirmed; ordinary cache listing not required")
    for name in candidates:
        parent = cache_parent_path(config.source.cache_root, name)
        reason = "destination date exists or cannot be proven absent" if name in context.destination_records or not _destination_date_absent(config, name) else _safe_cache_date(config, context, name, ops, native_owned=True)
        if reason:
            result.blocked.append(f"{name}: {reason}")
            print(f"  [KEEP] {result.blocked[-1]}")
            continue
        print(f"  [{'WOULD DELETE' if dry_run else 'DELETE'}] redundant cache {parent}")
        if dry_run:
            continue
        # Repeat receiver absence immediately before deleting; never remove a
        # newly received counterpart just because the earlier index lacked it.
        if not _destination_date_absent(config, name):
            result.blocked.append(f"{name}: destination appeared or absence became unknown")
            continue
        result.attempted += 1
        deleted = delete_subvolume_tree(
            ops, parent, protected_roots=[config.source.snapshot_root], refuse_unknown_entries=True,
            allowed_regular_names={"info.json"},
            expected_subvolume_paths=[cache_child_path(config.source.cache_root, name, payload) for payload in config.source.subvolumes],
            native_cache_proof=NativeCacheDeletionProof(owned_root, {
                path: meta for path, meta in cache.by_path.items() if is_same_or_under(path, parent)
            }),
        )
        if deleted.success:
            result.completed += 1
            cache.remove_tree(parent)
        else:
            result.blocked.append(f"{name}: " + "; ".join(deleted.errors or ["deletion not confirmed"]))
            print(f"  [RETRY] {result.blocked[-1]}")
    return result


def _verified_destination_root(config: AppConfig, state: dict, context: ReconciliationContext, ops: BtrfsOps, cache_ops: BtrfsOps) -> tuple[SubvolumeMeta | None, str]:
    """Anchor destination containment and fresh receiver identities to the verified cache/state job."""

    cache_root, error = _verified_managed_cache_root(config, state, context, cache_ops)
    if not cache_root:
        return None, error
    root = str(config.destination.target_root / "snapshots")
    if config.source.mode == "local" and (is_same_or_under(root, config.source.snapshot_root)
            or is_same_or_under(config.source.snapshot_root, root)
            or is_same_or_under(root, config.source.cache_root)
            or is_same_or_under(config.source.cache_root, root)):
        return None, "destination overlaps protected source storage"
    meta = ops.meta(root, required=False)
    if not meta or not meta.uuid or not meta.subvolume_id or meta.subvolume_id < 256 or meta.parent_uuid or meta.received_uuid:
        return None, "destination snapshots root is not a verified native Btrfs container"
    cache = context.source_inventory.cache_index
    assert cache is not None
    original_ids = set(context.source_inventory.snapshot_index.by_uuid) | set(cache.by_uuid) | {cache_root.uuid}
    if meta.uuid in original_ids or set(context.destination_index.by_uuid) & original_ids:
        return None, "destination native identities overlap protected source storage"
    tree, errors = discover_subvolume_tree(ops, root)
    if errors or set(tree) != {root, *context.destination_index.by_path}:
        return None, "destination containment differs from complete inventory"
    for name, snapshot in state.get("snapshots", {}).items():
        for payload in config.source.subvolumes:
            saved = snapshot.get("subvolumes", {}).get(payload, {})
            path = str(config.destination.target_root / "snapshots" / name / payload)
            if resolve_destination_path(config.destination.target_root, saved.get("destination_path", "")) != config.destination.target_root / "snapshots" / name / payload:
                return None, "state receiver path is not canonical for this destination"
            indexed = context.destination_index.meta(path)
            live = ops.meta(path, required=False)
            if (not indexed or not live or not indexed.uuid or not indexed.subvolume_id
                    or live.uuid != indexed.uuid or live.subvolume_id != indexed.subvolume_id
                    or live.readonly is not True or indexed.readonly is not True
                    or live.received_uuid != indexed.received_uuid
                    or live.received_uuid != saved.get("send_source_uuid")):
                return None, "paired receiver identity changed or state UUID differs"
    return meta, ""


def _safe_native_destination_date(config: AppConfig, context: ReconciliationContext, name: str, ops: BtrfsOps) -> str | None:
    """Require unchanged native date trees containing only readonly snapshot payloads."""

    parent = str(config.destination.target_root / "snapshots" / name)
    tree = {path: meta for path, meta in context.destination_index.by_path.items() if is_same_or_under(path, parent)}
    if parent not in tree:
        return "date is not a native Btrfs subvolume"
    readonly_snapshots = 0
    known_streams = {send_stream_uuid(meta) for index in (context.source_inventory.cache_index, context.source_inventory.snapshot_index)
                     if index is not None for meta in index.by_path.values() if send_stream_uuid(meta)}
    for path, saved in tree.items():
        live = ops.meta(path, required=False)
        if not _native_identity_matches(saved, live):
            return "native destination subtree identity changed or became unavailable"
        if path == parent and live.readonly is False and not live.parent_uuid and not live.received_uuid:
            continue
        if live.readonly is not True or not (live.received_uuid or live.parent_uuid):
            return "destination subtree contains a writable or unproven snapshot"
        if live.received_uuid in known_streams or live.parent_uuid in known_streams:
            return "destination still corresponds to a known source/cache snapshot"
        readonly_snapshots += 1
    return None if readonly_snapshots else "no readonly native snapshot in dated destination subtree"


def _refresh_absent_cache_date(config: AppConfig, context: ReconciliationContext, name: str, ops: BtrfsOps, anchor: SubvolumeMeta) -> str | None:
    """Re-prove complete cache inventory and stable root before accepting native date absence."""

    root = config.source.cache_root
    assert root is not None
    live = ops.meta(root, required=False)
    if not live or live.uuid != anchor.uuid or live.subvolume_id != anchor.subvolume_id or live.readonly != anchor.readonly or live.parent_uuid or live.received_uuid:
        return "source cache root changed or became unavailable"
    cache, _records, _notes, _uuid, _device = _discover_repository(ops, root)
    if cache.errors or cache.root_missing:
        return "source cache inventory incomplete; absence not proven"
    context.source_inventory.cache_index = cache
    parent = cache_parent_path(root, name)
    if any(is_same_or_under(path, parent) for path in cache.by_path):
        return "source cache counterpart exists or appeared"
    return None


def cleanup_redundant_destination(config: AppConfig, state: dict, context: ReconciliationContext, *, dry_run: bool, yes_delete: bool, successful_sync: bool = False) -> RedundantCacheResult:
    """After successful sync, remove untracked destination-only RO dates no newer than the newest proven pair."""

    result = RedundantCacheResult()
    if not config.destination.delete_redundant_snapshots:
        return result
    if not dry_run and not successful_sync:
        result.skipped_reason = "requires a successful sync in this run"
    elif not config.source.cache_root:
        result.skipped_reason = "source cache_root is required to prove destination-only snapshots"
    if result.skipped_reason:
        print("Redundant destination cleanup: skipped; " + result.skipped_reason)
        return result
    cache_ops = BtrfsOps(CommandEndpoint.for_source(context.source), config.source.sudo, config.source.btrfs_command)
    ops = BtrfsOps(CommandEndpoint.local(), config.destination.sudo, config.destination.btrfs_command)
    cache, _records, _notes, _uuid, _device = _discover_repository(cache_ops, config.source.cache_root)
    target, records, _notes, _uuid, _device = _discover_repository(ops, str(config.destination.target_root / "snapshots"))
    if cache.errors or cache.root_missing or target.errors or target.root_missing:
        result.skipped_reason = "fresh source/destination inventory incomplete"
        print("Redundant destination cleanup: skipped; " + result.skipped_reason)
        return result
    context.source_inventory.cache_index = cache
    context.destination_index, context.destination_records = target, records
    window = _confirmed_window(config, state, context)
    if not window:
        result.skipped_reason = "no complete UUID-confirmed state/cache/destination range"
        print("Redundant destination cleanup: skipped; " + result.skipped_reason)
        return result
    protected = _protected_cache_dates(config, state)
    root = str(config.destination.target_root / "snapshots")
    names = {PurePosixPath(path).relative_to(root).parts[0] for path in target.by_path
             if is_same_or_under(path, root) and PurePosixPath(path) != PurePosixPath(root)}
    candidates = []
    for name in sorted(names - protected):
        if not SNAPSHOT_RE.fullmatch(name) or name > window[1]:
            continue
        try:
            datetime.strptime(name, "%Y-%m-%d_%H-%M-%S")
        except ValueError:
            continue
        parent = cache_parent_path(config.source.cache_root, name)
        if not any(is_same_or_under(path, parent) for path in cache.by_path):
            candidates.append(name)
    result.candidates = len(candidates)
    if not candidates:
        print(f"Redundant destination cleanup: confirmed pairs {window[0]} .. {window[1]}; no untracked destination-only dates no newer than latest pair")
        return result
    if not dry_run and not yes_delete:
        raise RuntimeError("Refusing redundant destination deletion without --yes-delete")
    print(f"Redundant destination cleanup: confirmed pairs {window[0]} .. {window[1]}; {len(candidates)} untracked destination-only date(s) no newer than latest pair")
    cache_anchor = cache_ops.meta(config.source.cache_root, required=False)
    anchor, error = _verified_destination_root(config, state, context, ops, cache_ops)
    if not anchor:
        result.blocked = [f"{name}: {error}" for name in candidates]
        for reason in result.blocked:
            print(f"  [KEEP] {reason}")
        return result
    if cache_anchor is None:
        result.blocked = [f"{name}: source cache anchor unavailable" for name in candidates]
        return result
    print("  ownership: native destination root, state, cache and received UUID pairs confirmed")
    if dry_run:
        print("  preview only: real redundant deletion requires successful sync before cleanup")
    for name in candidates:
        parent = str(config.destination.target_root / "snapshots" / name)
        reason = _refresh_absent_cache_date(config, context, name, cache_ops, cache_anchor)
        reason = reason or _safe_native_destination_date(config, context, name, ops)
        if reason:
            result.blocked.append(f"{name}: {reason}")
            print(f"  [KEEP] {result.blocked[-1]}")
            continue
        print(f"  [{'WOULD DELETE' if dry_run else 'DELETE'}] redundant destination {parent}")
        if dry_run:
            continue
        reason = _refresh_absent_cache_date(config, context, name, cache_ops, cache_anchor)
        reason = reason or _safe_native_destination_date(config, context, name, ops)
        if reason:
            result.blocked.append(f"{name}: {reason}")
            print(f"  [KEEP] {result.blocked[-1]}")
            continue
        result.attempted += 1
        deleted = delete_subvolume_tree(ops, parent,
            protected_roots=[config.source.snapshot_root, config.source.cache_root] if config.source.mode == "local" else [],
            native_cache_proof=NativeCacheDeletionProof(anchor, {
                path: meta for path, meta in target.by_path.items() if is_same_or_under(path, parent)
            }))
        if deleted.success:
            result.completed += 1
            target.remove_tree(parent)
            context.destination_records.pop(name, None)
        else:
            result.blocked.append(f"{name}: " + "; ".join(deleted.errors or ["deletion not confirmed"]))
            print(f"  [RETRY] {result.blocked[-1]}")
    return result
