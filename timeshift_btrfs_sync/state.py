"""Persistent local state for completed transfers."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Any, Iterable
import json
import os
import posixpath
import tempfile

from .models import SnapshotMeta, SubvolumeMeta

SEND_PATH_KIND_SOURCE_CACHE = "source-cache"
SEND_PATH_KIND_TIMESHIFT_ORIGINAL_READONLY = "timeshift-original-readonly"

# State v2 stores all managed paths relative to their configured roots:
#   destination_path       -> destination.target_root
#   source_path            -> source.snapshot_root
#   send_path              -> source.cache_root or source.snapshot_root,
#                             selected by send_path_kind
#   parent_source_path     -> the corresponding source root selected by
#                             parent_source_path_kind
STATE_VERSION = 2


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


def _absolute_source_path_ends_with(path: str, expected: PurePosixPath) -> bool:
    """Return True when an old absolute source path has the expected suffix."""

    absolute = PurePosixPath(posixpath.normpath(str(path)))
    if not absolute.is_absolute() or len(absolute.parts) < len(expected.parts):
        return False
    return tuple(absolute.parts[-len(expected.parts) :]) == tuple(expected.parts)


def source_path_to_relative(
    source_path: str | PurePosixPath,
    source_root: str,
    *,
    snapshot_name: str,
    subvolume_name: str,
    label: str = "source_path",
) -> str:
    """Convert a source-side state path to a configured-root-relative string.

    New state already contains paths such as ``2026-07-15_05-00-02/@``. Older
    state used absolute source paths. If an old absolute path is below the
    current root, it is relativized directly. If the configured root has already
    moved, the standard snapshot/subvolume suffix is used only when the absolute
    path ends in the exact state snapshot name and subvolume name.
    """

    text = posixpath.normpath(str(source_path))
    candidate = PurePosixPath(text)
    expected = _expected_snapshot_relative_path(snapshot_name, subvolume_name)
    if not candidate.is_absolute():
        relative = _safe_source_relative_path(candidate, label=label)
        if relative != expected:
            raise ValueError(
                f"{label} does not match the state snapshot/subvolume identity "
                f"{expected.as_posix()}: {source_path}"
            )
        return relative.as_posix()

    relative = _source_path_relative_to_root(text, source_root)
    if relative is not None:
        if relative != expected:
            raise ValueError(
                f"absolute {label} is under the configured root but does not match "
                f"{expected.as_posix()}: {source_path}"
            )
        return relative.as_posix()

    if _absolute_source_path_ends_with(text, expected):
        return expected.as_posix()
    raise ValueError(
        f"absolute {label} is not under the current configured root and does not end with "
        f"{expected.as_posix()}: {source_path}"
    )


def resolve_source_path(
    source_root: str,
    stored_path: str | PurePosixPath,
    *,
    snapshot_name: str,
    subvolume_name: str,
    label: str = "source_path",
) -> str:
    """Resolve one source-root-relative state path under the current source root."""

    relative = source_path_to_relative(
        stored_path,
        source_root,
        snapshot_name=snapshot_name,
        subvolume_name=subvolume_name,
        label=label,
    )
    return posixpath.join(_normalize_source_root(source_root), relative)


def destination_path_to_relative(destination_path: Path, target_root: Path) -> str:
    """Convert a destination subvolume path to a target_root-relative string.

    New state stores paths like ``snapshots/2026-06-23_07-10-24/@``. Older state
    versions stored absolute paths. If an old absolute path is no longer below
    the current target_root because the backup was moved, infer the relative path
    from the standard layout suffix starting at the last ``snapshots`` component.
    """

    path = Path(destination_path)
    if not path.is_absolute():
        return _safe_relative_path(path).as_posix()

    root = Path(target_root)
    try:
        rel = path.relative_to(root)
    except ValueError:
        parts = path.parts
        snapshot_indexes = [idx for idx, part in enumerate(parts) if part == "snapshots"]
        if not snapshot_indexes:
            raise ValueError(
                f"absolute destination path is not under target_root and has no snapshots/ suffix: {path}"
            )
        rel = Path(*parts[snapshot_indexes[-1] :])
    return _safe_relative_path(rel).as_posix()


def resolve_destination_path(target_root: Path, stored_path: str | Path) -> Path:
    """Resolve a state destination_path against the current target_root."""

    rel = destination_path_to_relative(Path(stored_path), target_root)
    return Path(target_root) / rel


def send_path_kind_for_state_subvolume(
    subvol_state: dict[str, Any],
    *,
    cache_root: str | None = None,
    snapshot_root: str | None = None,
) -> str:
    """Return the safe ownership/root kind for a stored ``send_path``.

    State v2 stores ``send_path_kind`` explicitly. Compatibility fallbacks use
    the older ownership booleans first, then absolute-path containment. Unknown
    or ambiguous old state remains protected as a Timeshift original rather than
    being treated as app-owned cache data.
    """

    kind = subvol_state.get("send_path_kind")
    if kind in {SEND_PATH_KIND_SOURCE_CACHE, SEND_PATH_KIND_TIMESHIFT_ORIGINAL_READONLY}:
        return str(kind)
    if subvol_state.get("send_path_owned_by_app") is True:
        return SEND_PATH_KIND_SOURCE_CACHE
    if subvol_state.get("send_path_prune_protected") is True:
        return SEND_PATH_KIND_TIMESHIFT_ORIGINAL_READONLY

    send_path = subvol_state.get("send_path")
    if isinstance(send_path, str) and PurePosixPath(posixpath.normpath(send_path)).is_absolute():
        from . import btrfs

        if cache_root and btrfs.path_is_under_cache(send_path, cache_root):
            return SEND_PATH_KIND_SOURCE_CACHE
        if snapshot_root and btrfs.path_is_same_or_under(send_path, snapshot_root):
            return SEND_PATH_KIND_TIMESHIFT_ORIGINAL_READONLY

    send_uuid = subvol_state.get("send_source_uuid") or subvol_state.get("source_uuid")
    original_uuid = subvol_state.get("original_source_uuid")
    if isinstance(send_uuid, str) and isinstance(original_uuid, str) and send_uuid and original_uuid:
        if send_uuid != original_uuid:
            return SEND_PATH_KIND_SOURCE_CACHE
    return SEND_PATH_KIND_TIMESHIFT_ORIGINAL_READONLY


def _source_root_for_kind(kind: str, *, snapshot_root: str, cache_root: str | None) -> str:
    """Return the configured source root used by one stored send-path kind."""

    if kind == SEND_PATH_KIND_SOURCE_CACHE:
        if not cache_root:
            raise ValueError("state send_path_kind is source-cache but source.cache_root is not configured")
        return cache_root
    if kind == SEND_PATH_KIND_TIMESHIFT_ORIGINAL_READONLY:
        return snapshot_root
    raise ValueError(f"unsupported state send_path_kind: {kind}")


def resolve_state_source_path(
    subvol_state: dict[str, Any],
    *,
    snapshot_root: str,
    snapshot_name: str,
    subvolume_name: str,
) -> str:
    """Resolve stored ``source_path`` under the current snapshot_root."""

    stored = subvol_state.get("source_path")
    if not isinstance(stored, str) or not stored:
        stored = _expected_snapshot_relative_path(snapshot_name, subvolume_name).as_posix()
    return resolve_source_path(
        snapshot_root,
        stored,
        snapshot_name=snapshot_name,
        subvolume_name=subvolume_name,
        label="source_path",
    )


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
    kind = send_path_kind_for_state_subvolume(
        subvol_state,
        cache_root=cache_root,
        snapshot_root=snapshot_root,
    )
    root = _source_root_for_kind(kind, snapshot_root=snapshot_root, cache_root=cache_root)
    return resolve_source_path(
        root,
        stored,
        snapshot_name=snapshot_name,
        subvolume_name=subvolume_name,
        label="send_path",
    )


def resolve_state_parent_source_path(
    subvol_state: dict[str, Any],
    *,
    snapshot_root: str,
    cache_root: str | None,
    parent_snapshot_name: str,
    subvolume_name: str,
) -> str:
    """Resolve stored ``parent_source_path`` under its recorded current root."""

    stored = subvol_state.get("parent_source_path")
    if not isinstance(stored, str) or not stored:
        raise ValueError(f"state has no parent_source_path for {parent_snapshot_name}/{subvolume_name}")
    kind = subvol_state.get("parent_source_path_kind")
    if kind not in {SEND_PATH_KIND_SOURCE_CACHE, SEND_PATH_KIND_TIMESHIFT_ORIGINAL_READONLY}:
        # Legacy state normally points at the same path that the parent snapshot
        # stored as send_path. Without an explicit kind, infer conservatively.
        kind = send_path_kind_for_state_subvolume(
            {"send_path": stored},
            cache_root=cache_root,
            snapshot_root=snapshot_root,
        )
    root = _source_root_for_kind(str(kind), snapshot_root=snapshot_root, cache_root=cache_root)
    return resolve_source_path(
        root,
        stored,
        snapshot_name=parent_snapshot_name,
        subvolume_name=subvolume_name,
        label="parent_source_path",
    )


def normalize_destination_paths(state: dict[str, Any], target_root: Path) -> dict[str, Any]:
    """Normalize in-memory destination paths to target_root-relative values."""

    snapshots = state.setdefault("snapshots", {})
    for snapshot_name, item in snapshots.items():
        if isinstance(item, dict):
            item["path"] = (Path("snapshots") / str(snapshot_name)).as_posix()
            for sub in item.get("subvolumes", {}).values():
                if not isinstance(sub, dict):
                    continue
                destination_path = sub.get("destination_path")
                if not isinstance(destination_path, str) or not destination_path:
                    continue
                try:
                    sub["destination_path"] = destination_path_to_relative(Path(destination_path), target_root)
                except ValueError:
                    # Keep invalid legacy values so the later operational check
                    # reports the exact problem rather than silently rewriting it.
                    pass
    return state


def normalize_source_paths(
    state: dict[str, Any],
    *,
    snapshot_root: str,
    cache_root: str | None,
) -> dict[str, Any]:
    """Normalize all source-side state paths to configured-root-relative values.

    Existing v0.1.43-and-older absolute paths are migrated in memory. The exact
    state snapshot name and subvolume key are used as the only relocation suffix,
    so an unrelated absolute path is never silently adopted. Invalid values are
    preserved for a later precise operational error.
    """

    snapshots = state.setdefault("snapshots", {})
    for snapshot_name, item in snapshots.items():
        if not isinstance(item, dict):
            continue
        subvolumes = item.get("subvolumes", {})
        if not isinstance(subvolumes, dict):
            continue
        for subvolume_name, sub in subvolumes.items():
            if not isinstance(sub, dict):
                continue
            snapshot_text = str(snapshot_name)
            subvolume_text = str(subvolume_name)
            kind = send_path_kind_for_state_subvolume(
                sub,
                cache_root=cache_root,
                snapshot_root=snapshot_root,
            )
            sub["send_path_kind"] = kind
            sub["send_path_owned_by_app"] = kind == SEND_PATH_KIND_SOURCE_CACHE
            sub["send_path_prune_protected"] = kind == SEND_PATH_KIND_TIMESHIFT_ORIGINAL_READONLY

            source_path = sub.get("source_path")
            if isinstance(source_path, str) and source_path:
                try:
                    sub["source_path"] = source_path_to_relative(
                        source_path,
                        snapshot_root,
                        snapshot_name=snapshot_text,
                        subvolume_name=subvolume_text,
                        label="source_path",
                    )
                except ValueError:
                    pass

            send_path = sub.get("send_path")
            if isinstance(send_path, str) and send_path:
                try:
                    send_root = _source_root_for_kind(
                        kind,
                        snapshot_root=snapshot_root,
                        cache_root=cache_root,
                    )
                    sub["send_path"] = source_path_to_relative(
                        send_path,
                        send_root,
                        snapshot_name=snapshot_text,
                        subvolume_name=subvolume_text,
                        label="send_path",
                    )
                except ValueError:
                    pass

            parent_path = sub.get("parent_source_path")
            parent_name = sub.get("parent_snapshot")
            if not isinstance(parent_path, str) or not parent_path or not isinstance(parent_name, str) or not parent_name:
                continue

            parent_kind = sub.get("parent_source_path_kind")
            if parent_kind not in {SEND_PATH_KIND_SOURCE_CACHE, SEND_PATH_KIND_TIMESHIFT_ORIGINAL_READONLY}:
                parent_item = snapshots.get(parent_name)
                parent_sub = (
                    parent_item.get("subvolumes", {}).get(subvolume_text)
                    if isinstance(parent_item, dict) and isinstance(parent_item.get("subvolumes"), dict)
                    else None
                )
                if isinstance(parent_sub, dict):
                    parent_kind = send_path_kind_for_state_subvolume(
                        parent_sub,
                        cache_root=cache_root,
                        snapshot_root=snapshot_root,
                    )
                else:
                    parent_kind = send_path_kind_for_state_subvolume(
                        {"send_path": parent_path},
                        cache_root=cache_root,
                        snapshot_root=snapshot_root,
                    )
            sub["parent_source_path_kind"] = parent_kind
            try:
                parent_root = _source_root_for_kind(
                    str(parent_kind),
                    snapshot_root=snapshot_root,
                    cache_root=cache_root,
                )
                sub["parent_source_path"] = source_path_to_relative(
                    parent_path,
                    parent_root,
                    snapshot_name=parent_name,
                    subvolume_name=subvolume_text,
                    label="parent_source_path",
                )
            except ValueError:
                pass
    return state


def normalize_state_paths(
    state: dict[str, Any],
    *,
    target_root: Path | None = None,
    snapshot_root: str | None = None,
    cache_root: str | None = None,
) -> dict[str, Any]:
    """Normalize destination and source paths in one loaded state document."""

    if target_root is not None:
        normalize_destination_paths(state, target_root)
    if snapshot_root is not None:
        normalize_source_paths(state, snapshot_root=snapshot_root, cache_root=cache_root)
    state["version"] = STATE_VERSION
    return state


def load_state(
    path: Path,
    target_root: Path | None = None,
    *,
    snapshot_root: str | None = None,
    cache_root: str | None = None,
) -> dict[str, Any]:
    """Load state.json, migrate known paths in memory, or return empty state."""

    if not path.exists():
        data = empty_state()
    else:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            data = empty_state()
    data.setdefault("version", STATE_VERSION)
    data.setdefault("snapshots", {})
    return normalize_state_paths(
        data,
        target_root=target_root,
        snapshot_root=snapshot_root,
        cache_root=cache_root,
    )


def save_state(path: Path, state: dict[str, Any]) -> None:
    """Atomically write state.json."""

    state["version"] = STATE_VERSION
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
    from . import btrfs

    if cache_root and btrfs.path_is_under_cache(path, cache_root):
        return SEND_PATH_KIND_SOURCE_CACHE
    if btrfs.path_is_same_or_under(path, snapshot_root):
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
        send_path_kind = (
            SEND_PATH_KIND_TIMESHIFT_ORIGINAL_READONLY
            if PurePosixPath(posixpath.normpath(send_path)) == PurePosixPath(posixpath.normpath(subvolume.path))
            else SEND_PATH_KIND_SOURCE_CACHE
        )

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
            parent_item = snapshots.get(parent_snapshot)
            parent_sub = (
                parent_item.get("subvolumes", {}).get(subvolume.name)
                if isinstance(parent_item, dict) and isinstance(parent_item.get("subvolumes"), dict)
                else None
            )
            if isinstance(parent_sub, dict):
                parent_path_kind = send_path_kind_for_state_subvolume(
                    parent_sub,
                    cache_root=cache_root,
                    snapshot_root=snapshot_root,
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
        "send_path_owned_by_app": send_path_kind == SEND_PATH_KIND_SOURCE_CACHE,
        "send_path_prune_protected": send_path_kind == SEND_PATH_KIND_TIMESHIFT_ORIGINAL_READONLY,
        "source_uuid": send_source_uuid,
        "send_source_uuid": send_source_uuid,
        "original_source_uuid": original_source_uuid,
        "source_parent_uuid": (send_meta.parent_uuid if send_meta else None) or subvolume.parent_uuid,
        "source_received_uuid": (send_meta.received_uuid if send_meta else None) or subvolume.received_uuid,
        "original_source_parent_uuid": original_meta.parent_uuid if original_meta else subvolume.parent_uuid,
        "original_source_received_uuid": original_meta.received_uuid if original_meta else subvolume.received_uuid,
        "destination_path": destination_path_to_relative(destination_path, destination_root),
        "destination_uuid": received_meta.uuid if received_meta else None,
        "destination_parent_uuid": received_meta.parent_uuid if received_meta else None,
        "destination_received_uuid": received_meta.received_uuid if received_meta else None,
        "parent_snapshot": parent_snapshot,
        "parent_source_path": parent_path_relative,
        "parent_source_path_kind": parent_path_kind,
        "source_uuid_inferred_from_destination_received_uuid": bool(
            send_meta is None and subvolume.uuid is None and received_meta and received_meta.received_uuid
        ),
    }
    state["version"] = STATE_VERSION


def state_send_path_is_app_cache(
    subvol_state: dict[str, Any],
    *,
    cache_root: str | None = None,
    snapshot_root: str | None = None,
) -> bool:
    """Return True only when prune may delete the stored send_path."""

    return (
        send_path_kind_for_state_subvolume(
            subvol_state,
            cache_root=cache_root,
            snapshot_root=snapshot_root,
        )
        == SEND_PATH_KIND_SOURCE_CACHE
    )


def state_send_path_is_protected_timeshift_original(
    subvol_state: dict[str, Any],
    *,
    cache_root: str | None = None,
    snapshot_root: str | None = None,
) -> bool:
    """Return True when the stored send_path belongs to Timeshift, not the app."""

    return (
        send_path_kind_for_state_subvolume(
            subvol_state,
            cache_root=cache_root,
            snapshot_root=snapshot_root,
        )
        == SEND_PATH_KIND_TIMESHIFT_ORIGINAL_READONLY
    )


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
