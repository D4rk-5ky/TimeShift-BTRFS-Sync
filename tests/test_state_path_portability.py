from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from timeshift_btrfs_sync import retention, sync
from timeshift_btrfs_sync.models import SnapshotMeta, SubvolumeMeta
from timeshift_btrfs_sync.state import (
    SEND_PATH_KIND_SOURCE_CACHE,
    SEND_PATH_KIND_TIMESHIFT_ORIGINAL_READONLY,
    STATE_VERSION,
    load_state,
    mark_subvolume_synced,
    resolve_state_send_path,
    save_state,
    source_path_to_relative,
)


class CurrentStatePathTests(unittest.TestCase):
    def _snapshot(self, name: str, source_root: str) -> tuple[SnapshotMeta, SubvolumeMeta]:
        subvolume = SubvolumeMeta(
            name="@",
            path=f"{source_root}/{name}/@",
            uuid=f"original-{name}",
            readonly=False,
        )
        return (
            SnapshotMeta(
                name=name,
                path=f"{source_root}/{name}",
                tags=["H"],
                comment="test",
                created=name,
                subvolumes={"@": subvolume},
            ),
            subvolume,
        )

    def test_cache_paths_are_written_in_current_relative_schema(self):
        snapshot_root = "/source/snapshots"
        cache_root = "/source/cache"
        target_root = Path("/backup")
        parent = "2026-07-15_04-00-02"
        name = "2026-07-15_05-00-02"
        snapshot, source_meta = self._snapshot(name, snapshot_root)
        state = {"version": STATE_VERSION, "snapshots": {}}
        mark_subvolume_synced(
            state,
            snapshot=snapshot,
            subvolume=source_meta,
            destination_path=target_root / "snapshots" / name / "@",
            destination_root=target_root,
            snapshot_root=snapshot_root,
            cache_root=cache_root,
            parent_snapshot=parent,
            parent_source_path=f"{cache_root}/{parent}/@",
            send_path=f"{cache_root}/{name}/@",
            received_meta=SubvolumeMeta("@", str(target_root / "snapshots" / name / "@"), uuid="dest", received_uuid="cache"),
            original_meta=source_meta,
            send_meta=SubvolumeMeta("@", f"{cache_root}/{name}/@", uuid="cache", parent_uuid=source_meta.uuid, readonly=True),
        )
        stored = state["snapshots"][name]["subvolumes"]["@"]
        self.assertEqual(stored["source_path"], f"{name}/@")
        self.assertEqual(stored["send_path"], f"{name}/@")
        self.assertEqual(stored["send_path_kind"], SEND_PATH_KIND_SOURCE_CACHE)
        self.assertEqual(stored["parent_source_path"], f"{parent}/@")
        self.assertEqual(stored["parent_source_path_kind"], SEND_PATH_KIND_SOURCE_CACHE)
        self.assertEqual(stored["destination_path"], f"snapshots/{name}/@")
        self.assertEqual(
            set(stored),
            {
                "status", "name", "source_path", "send_path", "send_path_kind",
                "send_source_uuid", "original_source_uuid", "destination_path",
                "parent_snapshot", "parent_source_path", "parent_source_path_kind",
            },
        )

    def test_direct_timeshift_path_uses_explicit_current_kind(self):
        snapshot_root = "/source/snapshots"
        name = "2026-07-15_05-00-02"
        snapshot, source_meta = self._snapshot(name, snapshot_root)
        source_meta.readonly = True
        state = {"version": STATE_VERSION, "snapshots": {}}
        mark_subvolume_synced(
            state,
            snapshot=snapshot,
            subvolume=source_meta,
            destination_path=Path(f"/backup/snapshots/{name}/@"),
            destination_root=Path("/backup"),
            snapshot_root=snapshot_root,
            cache_root="/source/cache",
            parent_snapshot=None,
            parent_source_path=None,
            send_path=source_meta.path,
            received_meta=SubvolumeMeta("@", f"/backup/snapshots/{name}/@", received_uuid=source_meta.uuid),
            original_meta=source_meta,
            send_meta=source_meta,
        )
        stored = state["snapshots"][name]["subvolumes"]["@"]
        self.assertEqual(stored["send_path_kind"], SEND_PATH_KIND_TIMESHIFT_ORIGINAL_READONLY)
        self.assertEqual(stored["send_path"], f"{name}/@")

    def test_loader_accepts_only_current_state_version(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            path.write_text(json.dumps({"version": STATE_VERSION, "snapshots": {}}), encoding="utf-8")
            self.assertEqual(load_state(path)["version"], STATE_VERSION)
            path.write_text(json.dumps({"version": STATE_VERSION + 1, "snapshots": {}}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "version must be"):
                load_state(path)

    def test_loader_rejects_invalid_state_shapes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            path.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must contain an object"):
                load_state(path)
            path.write_text(json.dumps({"version": STATE_VERSION, "snapshots": []}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "snapshots must be an object"):
                load_state(path)

    def test_relative_state_rebases_under_current_cache_root(self):
        name = "2026-07-15_05-00-02"
        stored = {"send_path": f"{name}/@", "send_path_kind": SEND_PATH_KIND_SOURCE_CACHE}
        self.assertEqual(
            resolve_state_send_path(
                stored,
                snapshot_root="/new/source/snapshots",
                cache_root="/new/cache",
                snapshot_name=name,
                subvolume_name="@",
            ),
            f"/new/cache/{name}/@",
        )

    def test_missing_send_path_kind_is_rejected(self):
        name = "2026-07-15_05-00-02"
        with self.assertRaisesRegex(ValueError, "send_path_kind"):
            resolve_state_send_path(
                {"send_path": f"{name}/@"},
                snapshot_root="/source/snapshots",
                cache_root="/source/cache",
                snapshot_name=name,
                subvolume_name="@",
            )

    def test_writer_rejects_paths_outside_current_roots(self):
        name = "2026-07-15_05-00-02"
        snapshot, source_meta = self._snapshot(name, "/source/snapshots")
        with self.assertRaisesRegex(ValueError, "outside source.snapshot_root"):
            mark_subvolume_synced(
                {"version": STATE_VERSION, "snapshots": {}},
                snapshot=snapshot,
                subvolume=source_meta,
                destination_path=Path(f"/backup/snapshots/{name}/@"),
                destination_root=Path("/backup"),
                snapshot_root="/source/snapshots",
                cache_root="/source/cache",
                parent_snapshot=None,
                parent_source_path=None,
                send_path=f"/other/{name}/@",
                received_meta=None,
            )

    def test_prune_resolves_current_relative_cache_path(self):
        name = "2026-07-15_05-00-02"
        config = SimpleNamespace(source=SimpleNamespace(
            cleanup_superseded_cache=True,
            cache_root="/moved/cache",
            snapshot_root="/moved/snapshots",
        ))
        state = {"subvolumes": {"@": {
            "status": "ok",
            "send_path": f"{name}/@",
            "send_path_kind": SEND_PATH_KIND_SOURCE_CACHE,
        }}}
        self.assertEqual(retention._source_cache_delete_paths(config, name, state), [("@", f"/moved/cache/{name}/@")])

    def test_parent_selection_rebases_current_relative_cache_path(self):
        parent = "2026-07-15_04-00-02"
        current = "2026-07-15_05-00-02"
        config = SimpleNamespace(
            source=SimpleNamespace(snapshot_root="/moved/snapshots", cache_root="/moved/cache", verify_incremental_parent_once_per_run=True),
            destination=SimpleNamespace(target_root=Path("/moved/target")),
        )
        state = {"snapshots": {parent: {"subvolumes": {"@": {
            "status": "ok",
            "send_path": f"{parent}/@",
            "send_path_kind": SEND_PATH_KIND_SOURCE_CACHE,
        }}}}}
        with patch.object(sync, "_filesystem_parent_candidates", return_value=[]):
            name, path = sync._select_parent(config, SimpleNamespace(), state, {}, SnapshotMeta(name=current, path="/unused"), "@", dry_run=True)
        self.assertEqual((name, path), (parent, f"/moved/cache/{parent}/@"))

    def test_save_preserves_current_schema_version(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            state = {"version": STATE_VERSION, "snapshots": {}}
            save_state(path, state)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["version"], STATE_VERSION)

    def test_relative_path_must_match_record_identity(self):
        with self.assertRaises(ValueError):
            source_path_to_relative(
                "another-snapshot/@",
                "/source/snapshots",
                snapshot_name="2026-07-15_05-00-02",
                subvolume_name="@",
            )


if __name__ == "__main__":
    unittest.main()
