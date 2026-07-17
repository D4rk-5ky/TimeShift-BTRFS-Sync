"""Combined per-snapshot view used by every workflow planner."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .inventory import BtrfsIndex, SourceInventory
from .models import SnapshotMeta, SubvolumeMeta


@dataclass(slots=True)
class SnapshotRecord:
    """All known source/cache/destination/state data for one snapshot date."""

    name: str
    source: SnapshotMeta | None = None
    info_json: str | None = None
    info_error: str | None = None
    cache: dict[str, SubvolumeMeta] = field(default_factory=dict)
    destination: dict[str, SubvolumeMeta] = field(default_factory=dict)
    state: dict = field(default_factory=dict)

    def source_meta(self, name: str) -> SubvolumeMeta | None:
        return self.source.subvolumes.get(name) if self.source else None

@dataclass(slots=True)
class BackupInventory:
    """Coherent source/cache/destination/state view keyed by snapshot date."""

    records: dict[str, SnapshotRecord]
    source_inventory: SourceInventory
    destination_index: BtrfsIndex
    state: dict

    def get(self, name: str) -> SnapshotRecord | None:
        return self.records.get(name)


def _indexed_children(index: BtrfsIndex | None, parent: str, names: Iterable[str]) -> dict[str, SubvolumeMeta]:
    if index is None:
        return {}
    result: dict[str, SubvolumeMeta] = {}
    for name in names:
        meta = index.meta(str(Path(parent) / name))
        if meta:
            result[name] = meta
    return result


def build_backup_inventory(
    *,
    source_inventory: SourceInventory,
    source_snapshots: dict[str, SnapshotMeta],
    destination_index: BtrfsIndex,
    state: dict,
    cache_root: str | None,
    target_root: Path,
    subvolume_names: Iterable[str],
) -> BackupInventory:
    """Build one combined record set from already-collected bulk inventories.

    This function performs no commands.  It only joins data collected by the
    unified inventory layer, making it safe for sync, prune, recovery, destroy,
    state reconstruction, and dry-run planners to consume in different orders.
    """

    names = set(source_snapshots) | set((state.get("snapshots") or {}).keys())
    configured = tuple(subvolume_names)

    # Include dates visible only in cache or destination indexes.
    if source_inventory.cache_index and cache_root:
        prefix = str(Path(cache_root)).rstrip("/") + "/"
        for path in source_inventory.cache_index.by_path:
            if path.startswith(prefix):
                rel = path[len(prefix):].split("/", 1)
                if rel and rel[0]:
                    names.add(rel[0])
    dest_prefix = str(target_root / "snapshots").rstrip("/") + "/"
    for path in destination_index.by_path:
        if path.startswith(dest_prefix):
            rel = path[len(dest_prefix):].split("/", 1)
            if rel and rel[0]:
                names.add(rel[0])

    records: dict[str, SnapshotRecord] = {}
    for name in sorted(names):
        source = source_snapshots.get(name)
        cache_parent = str(Path(cache_root) / name) if cache_root else ""
        destination_parent = str(target_root / "snapshots" / name)
        record = SnapshotRecord(
            name=name,
            source=source,
            info_json=source_inventory.snapshot_info_json.get(name),
            info_error=source_inventory.snapshot_info_errors.get(name),
            cache=_indexed_children(source_inventory.cache_index, cache_parent, configured) if cache_root else {},
            destination=_indexed_children(destination_index, destination_parent, configured),
            state=((state.get("snapshots") or {}).get(name) or {}),
        )
        records[name] = record
    return BackupInventory(records, source_inventory, destination_index, state)
