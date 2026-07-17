"""Persistent local state for completed transfers."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Any, Iterable
import json
import os
import posixpath
import tempfile

from .models import SnapshotMeta, SubvolumeMeta
from .paths import is_under, is_same_or_under

SEND_PATH_KIND_SOURCE_CACHE = "source-cache"
SEND_PATH_KIND_TIMESHIFT_ORIGINAL_READONLY = "timeshift-original-readonly"

# The current state schema stores all managed paths relative to their configured roots:
#   destination_path       -> destination.target_root
#   source_path            -> source.snapshot_root
#   send_path              -> source.cache_root or source.snapshot_root,
#                             selected by send_path_kind
#   parent_source_path     -> the corresponding source root selected by
#                             parent_source_path_kind
STATE_VERSION = 3


def empty_state() -> dict[str, Any]:
    """Return a new empty state document."""

    return {"version": STATE_VERSION, "snapshots": {}}


def _safe_relative_path(path: Path) -> Path:
    """Return a normalized destination-relative path or raise ValueError."""

    if path.is_absolute():
        raise ValueError(f"path is absolute, not target-root relative: {path}")
    if not path.parts or path == Path("."):
        raise ValueError("empty destination-relative path")
    if any(part == ".." for part in path.parts):
        raise ValueError(f"destination-relative path escapes target_root: {path}")
    return Path(*path.parts)


def _safe_source_relative_path(path: str | PurePosixPath, *, label: str) -> PurePosixPath:
    """Return a normalized safe POSIX path relative to a configured source root.

    Source paths may refer to a remote host, so they are normalized with POSIX
    semantics rather than the destination host's local ``Path`` implementation.
    Empty paths, absolute paths, and parent-directory escapes are rejected.
    """

    text = posixpath.normpath(str(path))
    candidate = PurePosixPath(text)
    if candidate.is_absolute():
        raise ValueError(f"{label} is absolute, not source-root relative: {path}")
    if text in {"", "."} or not candidate.parts:
        raise ValueError(f"empty {label}")
    if any(part == ".." for part in candidate.parts):
        raise ValueError(f"{label} escapes its configured source root: {path}")
    return PurePosixPath(*candidate.parts)


def _normalize_source_root(root: str) -> str:
    """Return one normalized absolute-style POSIX source root."""

    normalized = posixpath.normpath(str(root))
    return normalized.rstrip("/") or "/"


def _source_path_relative_to_root(path: str, root: str) -> PurePosixPath | None:
    """Return ``path`` relative to ``root`` when it is currently below that root."""

    normalized_path = posixpath.normpath(str(path))
    normalized_root = _normalize_source_root(root)
    try:
        common = posixpath.commonpath([normalized_path, normalized_root])
    except ValueError:
        return None
    if common != normalized_root:
        return None
    relative = posixpath.relpath(normalized_path, normalized_root)
    try:
        return _safe_source_relative_path(relative, label="source-relative path")
    except ValueError:
        return None


def _expected_snapshot_relative_path(snapshot_name: str, subvolume_name: str) -> PurePosixPath:
    """Return the canonical ``<snapshot>/<subvolume>`` source-relative path."""

    snapshot_part = _safe_source_relative_path(snapshot_name, label="snapshot name")
    subvolume_part = _safe_source_relative_path(subvolume_name, label="subvolume name")
    return _safe_source_relative_path(snapshot_part / subvolume_part, label="snapshot source path")


def source_path_to_relative(
    source_path: str | PurePosixPath,
    source_root: str,
    *,
    snapshot_name: str,
    subvolume_name: str,
    label: str = "source_path",
) -> str:
    """Convert a current source path to canonical configured-root-relative state form."""

    text = posixpath.normpath(str(source_path))
    candidate = PurePosixPath(text)
    expected = _expected_snapshot_relative_path(snapshot_name, subvolume_name)
    if candidate.is_absolute():
        relative = _source_path_relative_to_root(text, source_root)
        if relative is None:
            raise ValueError(f"absolute {label} is outside its configured root: {source_path}")
    else:
        relative = _safe_source_relative_path(candidate, label=label)
    if relative != expected:
        raise ValueError(
            f"{label} does not match the state snapshot/subvolume identity "
            f"{expected.as_posix()}: {source_path}"
        )
    return relative.as_posix()

def resolve_source_path(
    source_root: str,
    stored_path: str | PurePosixPath,
    *,
    snapshot_name: str,
    subvolume_name: str,
    label: str = "source_path",
) -> str:
    """Resolve a current root-relative state path under its configured source root."""

    relative = _safe_source_relative_path(stored_path, label=label)
    expected = _expected_snapshot_relative_path(snapshot_name, subvolume_name)
    if relative != expected:
        raise ValueError(
            f"{label} does not match the state snapshot/subvolume identity "
            f"{expected.as_posix()}: {stored_path}"
        )
    return posixpath.join(_normalize_source_root(source_root), relative.as_posix())

def destination_path_to_relative(destination_path: Path, target_root: Path) -> str:
    """Convert a current destination path to target-root-relative state form."""

    path = Path(destination_path)
    if not path.is_absolute():
        return _safe_relative_path(path).as_posix()
    try:
        relative = path.relative_to(Path(target_root))
    except ValueError as exc:
        raise ValueError(f"absolute destination path is outside target_root: {path}") from exc
    return _safe_relative_path(relative).as_posix()

def resolve_destination_path(target_root: Path, stored_path: str | Path) -> Path:
    """Resolve a current target-root-relative state destination path."""

    return Path(target_root) / _safe_relative_path(Path(stored_path))

def send_path_kind_for_state_subvolume(subvol_state: dict[str, Any]) -> str:
    """Return the explicitly stored current send-path ownership kind."""

    kind = subvol_state.get("send_path_kind")
    if kind not in {SEND_PATH_KIND_SOURCE_CACHE, SEND_PATH_KIND_TIMESHIFT_ORIGINAL_READONLY}:
        raise ValueError(f"state has invalid or missing send_path_kind: {kind!r}")
    return str(kind)

def _source_root_for_kind(kind: str, *, snapshot_root: str, cache_root: str | None) -> str:
    """Return the configured source root used by one stored send-path kind."""

    if kind == SEND_PATH_KIND_SOURCE_CACHE:
        if not cache_root:
            raise ValueError("state send_path_kind is source-cache but source.cache_root is not configured")
        return cache_root
    if kind == SEND_PATH_KIND_TIMESHIFT_ORIGINAL_READONLY:
        return snapshot_root
    raise ValueError(f"unsupported state send_path_kind: {kind}")


def resolve_state_send_path(
    subvol_state: dict[str, Any],
    *,
    snapshot_root: str,
    cache_root: str | None,
    snapshot_name: str,
    subvolume_name: str,
) -> str:
    """Resolve stored ``send_path`` under its current configured source root."""

    stored = subvol_state.get("send_path")
    if not isinstance(stored, str) or not stored:
        raise ValueError(f"state has no send_path for {snapshot_name}/{subvolume_name}")
    kind = send_path_kind_for_state_subvolume(subvol_state)
    root = _source_root_for_kind(kind, snapshot_root=snapshot_root, cache_root=cache_root)
    return resolve_source_path(
        root,
        stored,
        snapshot_name=snapshot_name,
        subvolume_name=subvolume_name,
        label="send_path",
    )


STATE_ROOT_KEYS = {"version", "snapshots"}
STATE_SNAPSHOT_KEYS = {"name", "tags", "comment", "created", "path", "subvolumes"}
STATE_SUBVOLUME_KEYS = {
    "status", "name", "source_path", "send_path", "send_path_kind",
    "send_source_uuid", "original_source_uuid", "destination_path",
    "parent_snapshot", "parent_source_path", "parent_source_path_kind",
}


def _reject_unknown_state_keys(value: dict[str, Any], allowed: set[str], label: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ValueError(f"state.json has unknown {label} field(s): {', '.join(unknown)}")


def validate_state_document(data: dict[str, Any]) -> None:
    """Validate the complete current state schema before any workflow uses it."""

    _reject_unknown_state_keys(data, STATE_ROOT_KEYS, "root")
    if data.get("version") != STATE_VERSION:
        raise ValueError(f"state.json version must be {STATE_VERSION}")
    snapshots = data.get("snapshots")
    if not isinstance(snapshots, dict):
        raise ValueError("state.json snapshots must be an object")
    for snapshot_name, snapshot in snapshots.items():
        if not isinstance(snapshot_name, str) or not snapshot_name:
            raise ValueError("state.json snapshot names must be non-empty strings")
        if not isinstance(snapshot, dict):
            raise ValueError(f"state.json snapshot {snapshot_name} must be an object")
        _reject_unknown_state_keys(snapshot, STATE_SNAPSHOT_KEYS, f"snapshot {snapshot_name}")
        missing_snapshot_fields = sorted(STATE_SNAPSHOT_KEYS - set(snapshot))
        if missing_snapshot_fields:
            raise ValueError(
                f"state.json snapshot {snapshot_name} is missing field(s): "
                + ", ".join(missing_snapshot_fields)
            )
        if snapshot.get("name") != snapshot_name:
            raise ValueError(f"state.json snapshot {snapshot_name} has a mismatching name field")
        tags = snapshot.get("tags")
        if not isinstance(tags, list) or not all(isinstance(tag, str) and tag for tag in tags):
            raise ValueError(f"state.json snapshot {snapshot_name} tags must be non-empty strings")
        if snapshot.get("comment") is not None and not isinstance(snapshot.get("comment"), str):
            raise ValueError(f"state.json snapshot {snapshot_name} comment must be text or null")
        if snapshot.get("created") is not None and not isinstance(snapshot.get("created"), str):
            raise ValueError(f"state.json snapshot {snapshot_name} created must be text or null")
        expected_snapshot_path = (Path("snapshots") / snapshot_name).as_posix()
        if snapshot.get("path") != expected_snapshot_path:
            raise ValueError(f"state.json snapshot path must be {expected_snapshot_path}")
        subvolumes = snapshot.get("subvolumes")
        if not isinstance(subvolumes, dict):
            raise ValueError(f"state.json snapshot {snapshot_name} subvolumes must be an object")
        for subvolume_name, subvolume in subvolumes.items():
            if not isinstance(subvolume_name, str) or not subvolume_name:
                raise ValueError(f"state.json snapshot {snapshot_name} has an invalid subvolume name")
            if not isinstance(subvolume, dict):
                raise ValueError(f"state.json {snapshot_name}/{subvolume_name} must be an object")
            _reject_unknown_state_keys(subvolume, STATE_SUBVOLUME_KEYS, f"{snapshot_name}/{subvolume_name}")
            missing_fields = sorted(STATE_SUBVOLUME_KEYS - set(subvolume))
            if missing_fields:
                raise ValueError(
                    f"state.json {snapshot_name}/{subvolume_name} is missing field(s): "
                    + ", ".join(missing_fields)
                )
            if subvolume.get("status") != "ok" or subvolume.get("name") != subvolume_name:
                raise ValueError(f"state.json {snapshot_name}/{subvolume_name} has invalid status or name")
            for uuid_field in ("send_source_uuid", "original_source_uuid"):
                if not isinstance(subvolume.get(uuid_field), str) or not subvolume[uuid_field]:
                    raise ValueError(f"state.json {snapshot_name}/{subvolume_name} has invalid {uuid_field}")
            expected_source = _expected_snapshot_relative_path(snapshot_name, subvolume_name).as_posix()
            if subvolume.get("source_path") != expected_source:
                raise ValueError(f"state.json source_path must be {expected_source}")
            if subvolume.get("send_path") != expected_source:
                raise ValueError(f"state.json send_path must be {expected_source}")
            send_path_kind_for_state_subvolume(subvolume)
            expected_destination = (Path("snapshots") / snapshot_name / subvolume_name).as_posix()
            if subvolume.get("destination_path") != expected_destination:
                raise ValueError(f"state.json destination_path must be {expected_destination}")
            parent_name = subvolume.get("parent_snapshot")
            parent_path = subvolume.get("parent_source_path")
            parent_kind = subvolume.get("parent_source_path_kind")
            if parent_name is None:
                if parent_path is not None or parent_kind is not None:
                    raise ValueError(f"state.json {snapshot_name}/{subvolume_name} has parent path data without parent_snapshot")
            else:
                if not isinstance(parent_name, str) or not parent_name:
                    raise ValueError(f"state.json {snapshot_name}/{subvolume_name} has invalid parent_snapshot")
                expected_parent = _expected_snapshot_relative_path(parent_name, subvolume_name).as_posix()
                if parent_path != expected_parent:
                    raise ValueError(f"state.json parent_source_path must be {expected_parent}")
                if parent_kind not in {SEND_PATH_KIND_SOURCE_CACHE, SEND_PATH_KIND_TIMESHIFT_ORIGINAL_READONLY}:
                    raise ValueError(f"state.json {snapshot_name}/{subvolume_name} has invalid parent_source_path_kind")


def load_state(path: Path) -> dict[str, Any]:
    """Load and validate the current state document, or return an empty one when absent."""

    if not path.exists():
        return empty_state()
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("state.json must contain an object")
    validate_state_document(data)
    return data

def save_state(path: Path, state: dict[str, Any]) -> None:
    """Validate and atomically write the current state document."""

    state["version"] = STATE_VERSION
    validate_state_document(state)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2, sort_keys=True)
            fh.write("\n")
        os.replace(tmp_name, path)
    finally:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass


def refresh_snapshot_metadata_from_source(state: dict[str, Any], snapshots: Iterable[SnapshotMeta]) -> list[str]:
    """Refresh mutable Timeshift metadata for already-known snapshots."""

    snapshots_state = state.setdefault("snapshots", {})
    changed: list[str] = []
    for snapshot in snapshots:
        item = snapshots_state.get(snapshot.name)
        if not isinstance(item, dict):
            continue
        new_values = {
            "tags": list(snapshot.tags),
            "comment": snapshot.comment,
            "created": snapshot.created,
            "path": (Path("snapshots") / snapshot.name).as_posix(),
        }
        touched = False
        for key, value in new_values.items():
            if item.get(key) != value:
                item[key] = value
                touched = True
        if touched:
            item.setdefault("name", snapshot.name)
            item.setdefault("subvolumes", {})
            changed.append(snapshot.name)
    return sorted(changed)


def snapshot_is_synced(state: dict[str, Any], snapshot: str, required_subvolumes: list[str] | None = None) -> bool:
    """Return True when a snapshot is recorded as fully synced."""

    item = state.get("snapshots", {}).get(snapshot)
    if not item:
        return False
    subvols = item.get("subvolumes", {})
    if required_subvolumes:
        return all(name in subvols and subvols[name].get("status") == "ok" for name in required_subvolumes)
    return bool(subvols) and all(value.get("status") == "ok" for value in subvols.values())


def _kind_for_absolute_source_path(
    path: str | None,
    *,
    snapshot_root: str,
    cache_root: str | None,
) -> str | None:
    """Classify a current absolute source path by configured ownership root."""

    if not isinstance(path, str) or not path:
        return None
    if cache_root and is_under(path, cache_root):
        return SEND_PATH_KIND_SOURCE_CACHE
    if is_same_or_under(path, snapshot_root):
        return SEND_PATH_KIND_TIMESHIFT_ORIGINAL_READONLY
    return None


def mark_subvolume_synced(
    state: dict[str, Any],
    *,
    snapshot: SnapshotMeta,
    subvolume: SubvolumeMeta,
    destination_path: Path,
    destination_root: Path,
    snapshot_root: str,
    cache_root: str | None,
    parent_snapshot: str | None,
    parent_source_path: str | None,
    send_path: str,
    received_meta: SubvolumeMeta | None,
    original_meta: SubvolumeMeta | None = None,
    send_meta: SubvolumeMeta | None = None,
) -> None:
    """Record one successful send/receive using only root-relative state paths.

    ``source_path`` is stored relative to ``source.snapshot_root``. ``send_path``
    is stored relative to either ``source.cache_root`` or
    ``source.snapshot_root``, selected by ``send_path_kind``. The parent source
    path uses the same rule and records ``parent_source_path_kind`` explicitly.
    UUID fields remain the authority that proves identity after a root is moved.
    """

    snapshots = state.setdefault("snapshots", {})
    snap_state = snapshots.setdefault(
        snapshot.name,
        {
            "name": snapshot.name,
            "tags": snapshot.tags,
            "comment": snapshot.comment,
            "created": snapshot.created,
            "path": str(Path("snapshots") / snapshot.name),
            "subvolumes": {},
        },
    )
    snap_state["tags"] = snapshot.tags
    snap_state["comment"] = snapshot.comment
    snap_state["created"] = snapshot.created
    snap_state["path"] = (Path("snapshots") / snapshot.name).as_posix()

    send_source_uuid = (
        (send_meta.uuid if send_meta else None)
        or (received_meta.received_uuid if received_meta else None)
        or subvolume.uuid
    )
    original_source_uuid = (original_meta.uuid if original_meta else None) or subvolume.uuid
    send_path_kind = _kind_for_absolute_source_path(
        send_path,
        snapshot_root=snapshot_root,
        cache_root=cache_root,
    )
    if send_path_kind is None:
        raise ValueError(f"send_path is outside source.snapshot_root and source.cache_root: {send_path}")

    source_path_relative = source_path_to_relative(
        subvolume.path,
        snapshot_root,
        snapshot_name=snapshot.name,
        subvolume_name=subvolume.name,
        label="source_path",
    )
    send_root = _source_root_for_kind(
        send_path_kind,
        snapshot_root=snapshot_root,
        cache_root=cache_root,
    )
    send_path_relative = source_path_to_relative(
        send_path,
        send_root,
        snapshot_name=snapshot.name,
        subvolume_name=subvolume.name,
        label="send_path",
    )

    parent_path_relative: str | None = None
    parent_path_kind: str | None = None
    if parent_snapshot and parent_source_path:
        parent_path_kind = _kind_for_absolute_source_path(
            parent_source_path,
            snapshot_root=snapshot_root,
            cache_root=cache_root,
        )
        if parent_path_kind is None:
            raise ValueError(f"cannot classify parent source path under snapshot_root or cache_root: {parent_source_path}")
        parent_root = _source_root_for_kind(
            parent_path_kind,
            snapshot_root=snapshot_root,
            cache_root=cache_root,
        )
        parent_path_relative = source_path_to_relative(
            parent_source_path,
            parent_root,
            snapshot_name=parent_snapshot,
            subvolume_name=subvolume.name,
            label="parent_source_path",
        )

    snap_state.setdefault("subvolumes", {})[subvolume.name] = {
        "status": "ok",
        "name": subvolume.name,
        "source_path": source_path_relative,
        "send_path": send_path_relative,
        "send_path_kind": send_path_kind,
        "send_source_uuid": send_source_uuid,
        "original_source_uuid": original_source_uuid,
        "destination_path": destination_path_to_relative(destination_path, destination_root),
        "parent_snapshot": parent_snapshot,
        "parent_source_path": parent_path_relative,
        "parent_source_path_kind": parent_path_kind,
    }
    state["version"] = STATE_VERSION


def state_send_path_is_app_cache(subvol_state: dict[str, Any]) -> bool:
    """Return True when the stored send path belongs to the app cache."""

    return send_path_kind_for_state_subvolume(subvol_state) == SEND_PATH_KIND_SOURCE_CACHE

def state_send_path_is_protected_timeshift_original(subvol_state: dict[str, Any]) -> bool:
    """Return True when the stored send path belongs to Timeshift."""

    return send_path_kind_for_state_subvolume(subvol_state) == SEND_PATH_KIND_TIMESHIFT_ORIGINAL_READONLY

def remove_snapshot_from_state(state: dict[str, Any], snapshot: str) -> None:
    """Remove a pruned snapshot from state."""

    state.setdefault("snapshots", {}).pop(snapshot, None)


def refresh_state_metadata_and_report(
    state: dict[str, Any], snapshots: Iterable[SnapshotMeta], state_file: Path, *, dry_run: bool
) -> list[str]:
    """Refresh only Timeshift tags/comment/created/path, report, and save."""

    changed = refresh_snapshot_metadata_from_source(state, snapshots)
    if not changed:
        return []
    print(
        "STATE METADATA REFRESH\n"
        "  source: latest Timeshift --list metadata\n"
        "  updated fields: tags, comment, created, path\n"
        "  preserved fields: UUIDs, parent chain, send paths, destination paths, status\n"
        f"  snapshot(s): {', '.join(changed)}"
    )
    if dry_run:
        print("  dry-run: state.json would be updated, but was not written")
    else:
        save_state(state_file, state)
        print("  state.json updated")
    print()
    return changed


def latest_synced_before(
    state: dict[str, Any],
    snapshot_name: str,
    subvolume_name: str,
    source_names: set[str] | None = None,
) -> tuple[str, dict[str, Any]] | None:
    """Return newest older synced parent candidate."""

    candidates: list[tuple[str, dict[str, Any]]] = []
    for name, item in state.get("snapshots", {}).items():
        if name >= snapshot_name:
            continue
        sub = item.get("subvolumes", {}).get(subvolume_name)
        if not sub or sub.get("status") != "ok":
            continue
        if source_names and name not in source_names and not sub.get("send_path"):
            continue
        candidates.append((name, sub))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[-1]
