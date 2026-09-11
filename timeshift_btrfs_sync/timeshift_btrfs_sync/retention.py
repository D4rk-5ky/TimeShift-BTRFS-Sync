"""Paired destination and app-created source Timeshift retention/pruning logic."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from . import inventory, timeshift
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
    remove_snapshot_from_state,
    resolve_destination_path,
    resolve_state_send_path,
    save_state,
    snapshot_is_synced,
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


def _is_current_source_app_created_ondemand(snapshot: SnapshotMeta, marker: str) -> bool:
    """Re-prove app ownership from the current Timeshift listing before deletion."""

    marker = marker.lower().strip()
    if not marker or "O" not in snapshot.tags:
        return False
    return marker in str(snapshot.comment or "").lower()



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

    Original Timeshift snapshot paths are deliberately excluded from this raw
    Btrfs cache cleanup even when they were used as direct read-only send
    sources.  App-created source Timeshift snapshots, when eligible for paired
    retention, are deleted separately through Timeshift itself.
    Ownership is taken from the required ``send_path_kind`` state field.
    """

    if not config.source.cleanup_superseded_cache or not config.source.cache_root:
        return []
    paths: dict[str, str] = {}
    for subvol_name, subvol in snapshot_state.get("subvolumes", {}).items():
        if not isinstance(subvol, dict):
            continue
        if not subvol.get("send_path"):
            continue
        if not state_send_path_is_app_cache(subvol):
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
        if not state_send_path_is_protected_timeshift_original(subvol):
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
        print("  source Timeshift originals: protected from raw Btrfs cache deletion")
        for subvolume_name, path in protected_paths:
            print(f"  protected {subvolume_name}: {path}")
        print("  note: eligible app-created O snapshots are retired separately through Timeshift")

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


def _load_source_timeshift_index(config: AppConfig, source: SourceRunner) -> dict[str, SnapshotMeta]:
    """Read one current Timeshift list for destructive source-retention checks."""

    snapshots = timeshift.list_source_snapshots(
        source,
        snapshot_root=config.source.snapshot_root,
        subvolumes=config.source.subvolumes,
        sudo=config.source.sudo,
        timeshift_command=config.source.timeshift_command,
        btrfs_command=config.source.btrfs_command,
        include_btrfs_info=False,
    )
    return {snapshot.name: snapshot for snapshot in snapshots}


def _delete_source_timeshift_snapshot_for_prune(
    config: AppConfig,
    state: dict,
    source: SourceRunner,
    source_timeshift_index: dict[str, SnapshotMeta],
    snapshot_name: str,
    *,
    require_synced_state: bool = True,
) -> bool:
    """Delete one old app-created source O snapshot through Timeshift only.

    Tracked paired deletes require state to prove every configured subvolume
    completed sync. A current Timeshift listing must independently prove tag O
    plus the configured marker. Legacy source-only cleanup may bypass only the
    per-snapshot state check after the newest retained app-snapshot backup window
    has been independently proven complete on the live destination.
    """

    if require_synced_state and not snapshot_is_synced(
        state, snapshot_name, list(config.source.subvolumes)
    ):
        print("  warning: source Timeshift delete refused; state does not prove a complete transfer")
        return False

    current = source_timeshift_index.get(snapshot_name)
    if current is None:
        print("  source Timeshift: snapshot is no longer listed by Timeshift; no source delete needed")
        return True

    if not _is_current_source_app_created_ondemand(current, config.manual_snapshot.marker):
        print("  warning: source Timeshift delete refused; current Timeshift metadata no longer proves tag O + app marker")
        print(f"  current tags: {tags_text(current.tags)}")
        print(f"  required marker: {config.manual_snapshot.marker!r}")
        return False

    try:
        timeshift.delete_source_manual_snapshot(
            source,
            snapshot_root=config.source.snapshot_root,
            sudo=config.source.sudo,
            timeshift_command=config.source.timeshift_command,
            snapshot_name=snapshot_name,
        )
    except RuntimeError as exc:
        print(f"  warning: Timeshift source deletion failed; keeping state for retry: {exc}")
        return False

    source_timeshift_index.pop(snapshot_name, None)
    print(f"  source Timeshift: confirmed gone via timeshift --delete --snapshot {snapshot_name}")
    return True


def _destination_snapshot_is_proven_complete(
    config: AppConfig,
    state: dict,
    destination_index: inventory.BtrfsIndex,
    snapshot_name: str,
) -> bool:
    """Prove that state and the live destination contain every configured payload."""

    if not snapshot_is_synced(state, snapshot_name, list(config.source.subvolumes)):
        return False
    snapshot_state = state.get("snapshots", {}).get(snapshot_name, {})
    paths = dict(_destination_delete_paths(config, snapshot_state))
    if set(paths) != set(config.source.subvolumes):
        return False
    return all(destination_index.contains(paths[name]) for name in config.source.subvolumes)


def _source_app_retention_delete_names(
    config: AppConfig,
    source_timeshift_index: dict[str, SnapshotMeta],
) -> set[str]:
    """Return current app-created source O snapshots outside the same retention rules."""

    if not config.manual_snapshot.cleanup_enabled:
        return set()
    source_plan = build_prune_plan(config, source_snapshot_state(source_timeshift_index.values()))
    return {
        name
        for name in source_plan.delete
        if name in source_timeshift_index
        and _is_current_source_app_created_ondemand(
            source_timeshift_index[name], config.manual_snapshot.marker
        )
    }


def _authorized_source_timeshift_delete_names(
    config: AppConfig,
    state: dict,
    source_timeshift_index: dict[str, SnapshotMeta],
    destination_index: inventory.BtrfsIndex,
    source_delete_candidates: set[str],
) -> tuple[set[str], bool]:
    """Authorize source deletion from direct backup proof or a backed retained window.

    Normal tracked prune candidates are authorized only when state plus the
    live destination prove a complete transfer.  For legacy 0.1.73 source
    leftovers whose state/destination entry was already pruned, an old source
    snapshot may still be retired when all newest ``retention_count``
    app-created source snapshots are currently proven complete on the backup.
    That migration rule cleans the historical one-sided retention backlog
    without allowing a failed/unsynced newest snapshot to trigger source loss.
    """

    authorized: set[str] = set()
    for name in source_delete_candidates:
        if _destination_snapshot_is_proven_complete(config, state, destination_index, name):
            authorized.add(name)

    manual_count = config.manual_snapshot.retention_count
    app_names = sorted(
        name
        for name, snapshot in source_timeshift_index.items()
        if _is_current_source_app_created_ondemand(snapshot, config.manual_snapshot.marker)
    )
    retained_window = app_names[-manual_count:] if manual_count > 0 else []
    retained_window_proven = bool(retained_window) and len(retained_window) == manual_count and all(
        _destination_snapshot_is_proven_complete(config, state, destination_index, name)
        for name in retained_window
    )

    if retained_window_proven:
        for name in source_delete_candidates:
            if name not in state.get("snapshots", {}):
                authorized.add(name)

    return authorized, retained_window_proven


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


def _delete_destination_snapshot_for_prune(config: AppConfig, snapshot_name: str) -> bool:
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
    source_runner: SourceRunner | None,
    source_timeshift_index: dict[str, SnapshotMeta] | None,
    source_timeshift_delete_allowed: set[str],
    name: str,
    *,
    source_cache_index: inventory.BtrfsIndex | None = None,
) -> bool:
    """Execute one prune item and remove state only after every required side is gone."""

    snapshot_state = state.get("snapshots", {}).get(name, {})
    delete_source_timeshift = (
        config.manual_snapshot.cleanup_enabled
        and _is_app_created_ondemand(snapshot_state, config.manual_snapshot.marker)
    )
    delete_cache = bool(
        source_runner
        and config.source.cleanup_superseded_cache
        and config.source.cache_root
    )

    if delete_source_timeshift and source_timeshift_index is not None:
        current = source_timeshift_index.get(name)
        if current is not None and name not in source_timeshift_delete_allowed:
            print()
            print("RETENTION DELETE")
            print(f"  snapshot: {name}")
            print("  skipped: paired source deletion is not safely authorized by current Timeshift + destination proof")
            print("  result: destination/cache/state are left untouched so this can be retried safely")
            return False

    print()
    print("RETENTION DELETE")
    print(f"  snapshot: {name}")
    print(f"  tags:     {tags_text(snapshot_state.get('tags', []))}")
    for reason in _delete_reasons(plan, name):
        print(f"  why:      {reason}")

    workflow = plan_prune_snapshot(
        name,
        delete_cache=delete_cache,
        delete_destination=True,
        delete_source_timeshift=delete_source_timeshift,
    )
    status = {"destination": True, "cache": True, "source_timeshift": True}

    def delete_source_timeshift_action(_action):
        print("\nRetention Delete Source Timeshift snapshot")
        if source_runner is None or source_timeshift_index is None:
            print("  warning: source Timeshift inventory is unavailable; keeping backup/state for retry")
            status["source_timeshift"] = False
            return False
        status["source_timeshift"] = _delete_source_timeshift_snapshot_for_prune(
            config,
            state,
            source_runner,
            source_timeshift_index,
            name,
        )
        return status["source_timeshift"]

    def delete_destination(_action):
        print("\nRetention Delete Destination")
        if not status["source_timeshift"]:
            print("  skipped: source Timeshift retention step was not confirmed")
            status["destination"] = False
            return False
        status["destination"] = _delete_destination_snapshot_for_prune(config, name)
        return status["destination"]

    def delete_cache_action(_action):
        print("\nRetention Delete Source send-cache")
        if not status["source_timeshift"] or not status["destination"]:
            print("  skipped: earlier source/destination retention step was not confirmed")
            status["cache"] = False
            return False
        assert source_runner is not None
        status["cache"] = _cleanup_source_cache_for_pruned_snapshot(
            config,
            source_runner,
            name,
            snapshot_state,
            source_cache_index=source_cache_index,
        )
        return status["cache"]

    def remove_state(_action):
        print("\nState")
        if status["destination"] and status["cache"] and status["source_timeshift"]:
            remove_snapshot_from_state(state, name)
            print("  removed; all required destination/cache/source retention actions are confirmed")
            return True
        print("  kept; cleanup can be retried safely on the next prune")
        return False

    executor = WorkflowExecutor({
        ActionKind.DELETE_DESTINATION_TREE: delete_destination,
        ActionKind.DELETE_CACHE_TREE: delete_cache_action,
        ActionKind.DELETE_SOURCE_TIMESHIFT: delete_source_timeshift_action,
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
            lines.append("      Timeshift original send paths protected from raw Btrfs deletion:")
            for subvol_name, send_path in protected_paths:
                lines.append(f"        {subvol_name}: {send_path}")
        if config.manual_snapshot.cleanup_enabled and _is_app_created_ondemand(
            snapshot_state, config.manual_snapshot.marker
        ):
            lines.append("      source Timeshift snapshot:")
            lines.append(
                f"        {config.source.snapshot_root}/{name} "
                "(real prune re-verifies current tag O + marker, then uses timeshift --delete)"
            )
        for reason in _delete_reasons(plan, name):
            lines.append(f"      why: {reason}")
    lines.append("")
    emit_success_summary("\n".join(lines))


def prune(
    config: AppConfig,
    state: dict,
    *,
    dry_run: bool,
    yes_delete: bool,
    source_timeshift_index: dict[str, SnapshotMeta] | None = None,
) -> PrunePlan:
    """Apply backup retention plus paired app-created source O retention."""

    plan = build_prune_plan(config, state)
    state_names_before_prune = set(state.get("snapshots", {}))

    source_runner: SourceRunner | None = None
    source_delete_candidates: set[str] = set()
    source_delete_allowed: set[str] = set()
    retained_window_proven = False
    destination_index: inventory.BtrfsIndex | None = None
    legacy_source_only_candidates: set[str] = set()

    # Source app-snapshot retention must also find legacy 0.1.73 leftovers that
    # are no longer represented in state.  Therefore one current Timeshift list
    # is loaded whenever manual cleanup is enabled, even if destination state
    # currently has no delete candidate. Standalone prune can pass the list it
    # already read while refreshing metadata, avoiding a duplicate SSH call.
    if config.manual_snapshot.cleanup_enabled:
        source_runner = SourceRunner.from_config(config)
        if source_timeshift_index is None:
            print()
            print("Refreshing current source Timeshift metadata for app-snapshot retention...")
            source_timeshift_index = _load_source_timeshift_index(config, source_runner)
        source_delete_candidates = _source_app_retention_delete_names(config, source_timeshift_index)

        if source_delete_candidates:
            destination_index = inventory.build_local_btrfs_index(
                config.destination.target_root / "snapshots",
                sudo=config.destination.sudo,
                btrfs_command=config.destination.btrfs_command,
                include_root=True,
            )
            source_delete_allowed, retained_window_proven = _authorized_source_timeshift_delete_names(
                config,
                state,
                source_timeshift_index,
                destination_index,
                source_delete_candidates,
            )

    print_prune_plan(config, plan, state, dry_run=dry_run)

    if source_delete_candidates:
        legacy_source_only_candidates = {
            name for name in source_delete_candidates if name not in state_names_before_prune
        }
        legacy_candidates = sorted(legacy_source_only_candidates)
        print("SOURCE TIMESHIFT APP-SNAPSHOT RETENTION")
        print("=======================================")
        print(f"  current app-created O snapshots: {sum(1 for s in (source_timeshift_index or {}).values() if _is_current_source_app_created_ondemand(s, config.manual_snapshot.marker))}")
        print(f"  configured retention_count:      {config.manual_snapshot.retention_count}")
        print(f"  source delete candidates:        {len(source_delete_candidates)}")
        print(f"  safely authorized now:           {len(source_delete_allowed)}")
        if legacy_candidates:
            print(f"  legacy source-only candidates:   {len(legacy_candidates)}")
            print(f"  newest retained backup window:   {'proven' if retained_window_proven else 'NOT PROVEN'}")
        for name in sorted(source_delete_candidates):
            action = "WOULD DELETE" if dry_run else "DELETE"
            authorization = "authorized" if name in source_delete_allowed else "blocked: backup proof incomplete"
            print(f"  [{action}] {name}: {authorization}")
        print()

    if dry_run:
        print("Dry-run: no retention deletes were performed.")
        return plan
    if (plan.delete or source_delete_candidates) and not yes_delete:
        raise RuntimeError("Refusing to delete without --yes-delete")

    needs_cache_cleanup = bool(
        plan.delete and config.source.cleanup_superseded_cache and config.source.cache_root
    )
    if source_runner is None and needs_cache_cleanup:
        source_runner = SourceRunner.from_config(config)

    source_cache_index = (
        inventory.build_source_btrfs_index(
            source_runner,
            config.source.cache_root,
            sudo=config.source.sudo,
            btrfs_command=config.source.btrfs_command,
            include_root=True,
        )
        if source_runner and needs_cache_cleanup and config.source.cache_root
        else None
    )
    if source_cache_index is not None:
        print()
        print(f"Source send-cache index: {len(source_cache_index.by_path)} indexed subvolume(s) below {source_cache_index.root}")

    deleted = 0
    for name in sorted(plan.delete):
        if _delete_prune_item(
            config,
            state,
            plan,
            source_runner,
            source_timeshift_index,
            source_delete_allowed,
            name,
            source_cache_index=source_cache_index,
        ):
            deleted += 1

    # Clean source-only leftovers created by the old one-sided retention
    # behavior.  Only candidates absent from state are eligible here; tracked
    # candidates are handled transactionally with destination/cache/state above.
    legacy_deleted = 0
    if source_runner is not None and source_timeshift_index is not None:
        for name in sorted(legacy_source_only_candidates):
            if name not in source_delete_allowed:
                print()
                print(f"SOURCE TIMESHIFT LEGACY RETENTION SKIP: {name}")
                print("  reason: newest retained app-snapshot backup window is not fully proven")
                continue
            print()
            print(f"SOURCE TIMESHIFT LEGACY RETENTION DELETE: {name}")
            if _delete_source_timeshift_snapshot_for_prune(
                config,
                state,
                source_runner,
                source_timeshift_index,
                name,
                require_synced_state=False,
            ):
                legacy_deleted += 1

    save_state(config.state_file, state)
    summary = "\n".join(
        [
            "",
            "RETENTION DELETE SUMMARY",
            "========================",
            f"  destination/state candidates: {len(plan.delete)}",
            f"  completed paired/state items: {deleted}",
            f"  retry paired/state items:     {len(plan.delete) - deleted}",
            f"  legacy source-only deleted:   {legacy_deleted}",
            f"  remaining in state:{len(state.get('snapshots', {})):>5}",
            "",
        ]
    )
    print(summary)
    logger = get_logger()
    if logger:
        logger.success_text(summary + "\n")
    return plan

