from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from timeshift_btrfs_sync.models import SnapshotMeta, SubvolumeMeta
from timeshift_btrfs_sync import retention, sync
from timeshift_btrfs_sync.state import (
    SEND_PATH_KIND_SOURCE_CACHE,
    SEND_PATH_KIND_TIMESHIFT_ORIGINAL_READONLY,
    STATE_VERSION,
    load_state,
    mark_subvolume_synced,
    resolve_state_parent_source_path,
    resolve_state_send_path,
    resolve_state_source_path,
    save_state,
    source_path_to_relative,
)


class StatePathPortabilityTests(unittest.TestCase):
    def _snapshot(self, name: str, source_root: str) -> tuple[SnapshotMeta, SubvolumeMeta]:
        sub = SubvolumeMeta(
            name="@",
            path=f"{source_root}/{name}/@",
            uuid=f"original-{name}",
            parent_uuid=None,
            received_uuid=None,
            readonly=False,
        )
        snap = SnapshotMeta(
            name=name,
            path=f"{source_root}/{name}",
            tags=["H"],
            comment="test",
            created=name,
            subvolumes={"@": sub},
        )
        return snap, sub

    def test_cache_send_paths_are_stored_relative_to_cache_root(self):
        snapshot_root = "/source/timeshift-btrfs/snapshots"
        cache_root = "/source/.ts-btrfs-sync/send-cache"
        target_root = Path("/backup/timeshift")
        parent_name = "2026-07-15_04-00-02"
        name = "2026-07-15_05-00-02"
        snapshot, subvolume = self._snapshot(name, snapshot_root)
        state = {"version": 1, "snapshots": {}}

        mark_subvolume_synced(
            state,
            snapshot=snapshot,
            subvolume=subvolume,
            destination_path=target_root / "snapshots" / name / "@",
            destination_root=target_root,
            snapshot_root=snapshot_root,
            cache_root=cache_root,
            parent_snapshot=parent_name,
            parent_source_path=f"{cache_root}/{parent_name}/@",
            send_path=f"{cache_root}/{name}/@",
            received_meta=SubvolumeMeta(
                name="@",
                path=str(target_root / "snapshots" / name / "@"),
                uuid="destination-uuid",
                received_uuid="cache-uuid",
                readonly=True,
            ),
            original_meta=subvolume,
            send_meta=SubvolumeMeta(
                name="@",
                path=f"{cache_root}/{name}/@",
                uuid="cache-uuid",
                parent_uuid="cache-parent",
                readonly=True,
            ),
        )

        stored = state["snapshots"][name]["subvolumes"]["@"]
        self.assertEqual(state["version"], STATE_VERSION)
        self.assertEqual(stored["source_path"], f"{name}/@")
        self.assertEqual(stored["send_path"], f"{name}/@")
        self.assertEqual(stored["send_path_kind"], SEND_PATH_KIND_SOURCE_CACHE)
        self.assertEqual(stored["parent_source_path"], f"{parent_name}/@")
        self.assertEqual(stored["parent_source_path_kind"], SEND_PATH_KIND_SOURCE_CACHE)
        self.assertEqual(stored["destination_path"], f"snapshots/{name}/@")

    def test_direct_timeshift_send_paths_are_stored_relative_to_snapshot_root(self):
        snapshot_root = "/source/timeshift-btrfs/snapshots"
        cache_root = "/source/.ts-btrfs-sync/send-cache"
        target_root = Path("/backup/timeshift")
        name = "2026-07-15_05-00-02"
        snapshot, subvolume = self._snapshot(name, snapshot_root)
        subvolume.readonly = True
        state = {"snapshots": {}}

        mark_subvolume_synced(
            state,
            snapshot=snapshot,
            subvolume=subvolume,
            destination_path=target_root / "snapshots" / name / "@",
            destination_root=target_root,
            snapshot_root=snapshot_root,
            cache_root=cache_root,
            parent_snapshot=None,
            parent_source_path=None,
            send_path=subvolume.path,
            received_meta=SubvolumeMeta(
                name="@",
                path=str(target_root / "snapshots" / name / "@"),
                uuid="destination-uuid",
                received_uuid=subvolume.uuid,
                readonly=True,
            ),
            original_meta=subvolume,
            send_meta=subvolume,
        )

        stored = state["snapshots"][name]["subvolumes"]["@"]
        self.assertEqual(stored["source_path"], f"{name}/@")
        self.assertEqual(stored["send_path"], f"{name}/@")
        self.assertEqual(stored["send_path_kind"], SEND_PATH_KIND_TIMESHIFT_ORIGINAL_READONLY)
        self.assertTrue(stored["send_path_prune_protected"])

    def test_old_absolute_state_migrates_after_all_roots_move(self):
        name = "2026-07-15_05-00-02"
        parent_name = "2026-07-15_04-00-02"
        state_doc = {
            "version": 1,
            "snapshots": {
                parent_name: {
                    "name": parent_name,
                    "subvolumes": {
                        "@": {
                            "status": "ok",
                            "source_path": f"/old/source/snapshots/{parent_name}/@",
                            "send_path": f"/old/cache/{parent_name}/@",
                            "send_path_kind": SEND_PATH_KIND_SOURCE_CACHE,
                            "destination_path": f"/old/target/snapshots/{parent_name}/@",
                        }
                    },
                },
                name: {
                    "name": name,
                    "subvolumes": {
                        "@": {
                            "status": "ok",
                            "source_path": f"/old/source/snapshots/{name}/@",
                            "send_path": f"/old/cache/{name}/@",
                            "send_path_kind": SEND_PATH_KIND_SOURCE_CACHE,
                            "parent_snapshot": parent_name,
                            "parent_source_path": f"/old/cache/{parent_name}/@",
                            "destination_path": f"/old/target/snapshots/{name}/@",
                        }
                    },
                },
            },
        }

        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "state.json"
            state_file.write_text(json.dumps(state_doc), encoding="utf-8")
            loaded = load_state(
                state_file,
                Path("/new/target"),
                snapshot_root="/new/source/snapshots",
                cache_root="/new/cache",
            )
            save_state(state_file, loaded)
            written = json.loads(state_file.read_text(encoding="utf-8"))

        stored = loaded["snapshots"][name]["subvolumes"]["@"]
        self.assertEqual(loaded["version"], STATE_VERSION)
        self.assertEqual(stored["source_path"], f"{name}/@")
        self.assertEqual(stored["send_path"], f"{name}/@")
        self.assertEqual(stored["parent_source_path"], f"{parent_name}/@")
        self.assertEqual(stored["parent_source_path_kind"], SEND_PATH_KIND_SOURCE_CACHE)
        self.assertEqual(stored["destination_path"], f"snapshots/{name}/@")
        self.assertEqual(written["version"], STATE_VERSION)
        self.assertEqual(
            written["snapshots"][name]["subvolumes"]["@"]["send_path"],
            f"{name}/@",
        )
        self.assertNotIn("/old/", json.dumps(written))
        self.assertEqual(
            resolve_state_source_path(
                stored,
                snapshot_root="/new/source/snapshots",
                snapshot_name=name,
                subvolume_name="@",
            ),
            f"/new/source/snapshots/{name}/@",
        )
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
        self.assertEqual(
            resolve_state_parent_source_path(
                stored,
                snapshot_root="/new/source/snapshots",
                cache_root="/new/cache",
                parent_snapshot_name=parent_name,
                subvolume_name="@",
            ),
            f"/new/cache/{parent_name}/@",
        )

    def test_prune_resolves_relative_cache_path_under_current_cache_root(self):
        name = "2026-07-15_05-00-02"
        config = SimpleNamespace(
            source=SimpleNamespace(
                cleanup_superseded_cache=True,
                cache_root="/moved/cache",
                snapshot_root="/moved/timeshift/snapshots",
            )
        )
        snapshot_state = {
            "name": name,
            "subvolumes": {
                "@": {
                    "status": "ok",
                    "send_path": f"{name}/@",
                    "send_path_kind": SEND_PATH_KIND_SOURCE_CACHE,
                }
            },
        }
        self.assertEqual(
            retention._source_cache_delete_paths(config, name, snapshot_state),
            [("@", f"/moved/cache/{name}/@")],
        )


    def test_parent_selection_resolves_relative_send_path_under_moved_cache_root(self):
        parent_name = "2026-07-15_04-00-02"
        current_name = "2026-07-15_05-00-02"
        config = SimpleNamespace(
            source=SimpleNamespace(
                snapshot_root="/moved/timeshift/snapshots",
                cache_root="/moved/cache",
                verify_incremental_parent_once_per_run=True,
            ),
            destination=SimpleNamespace(target_root=Path("/moved/target")),
        )
        state_doc = {
            "snapshots": {
                parent_name: {
                    "subvolumes": {
                        "@": {
                            "status": "ok",
                            "send_path": f"{parent_name}/@",
                            "send_path_kind": SEND_PATH_KIND_SOURCE_CACHE,
                        }
                    }
                }
            }
        }
        current_snapshot = SnapshotMeta(name=current_name, path="/unused")
        with patch.object(sync, "_filesystem_parent_candidates", return_value=[]):
            selected_name, selected_path = sync._select_parent(
                config,
                SimpleNamespace(),
                state_doc,
                {},
                current_snapshot,
                "@",
                dry_run=True,
            )
        self.assertEqual(selected_name, parent_name)
        self.assertEqual(selected_path, f"/moved/cache/{parent_name}/@")



    def test_parent_selection_resolves_direct_send_path_under_moved_snapshot_root(self):
        parent_name = "2026-07-15_04-00-02"
        current_name = "2026-07-15_05-00-02"
        config = SimpleNamespace(
            source=SimpleNamespace(
                snapshot_root="/moved/timeshift/snapshots",
                cache_root="/moved/cache",
                verify_incremental_parent_once_per_run=True,
            ),
            destination=SimpleNamespace(target_root=Path("/moved/target")),
        )
        state_doc = {
            "snapshots": {
                parent_name: {
                    "subvolumes": {
                        "@": {
                            "status": "ok",
                            "send_path": f"{parent_name}/@",
                            "send_path_kind": SEND_PATH_KIND_TIMESHIFT_ORIGINAL_READONLY,
                        }
                    }
                }
            }
        }
        current_snapshot = SnapshotMeta(name=current_name, path="/unused")
        with patch.object(sync, "_filesystem_parent_candidates", return_value=[]):
            selected_name, selected_path = sync._select_parent(
                config,
                SimpleNamespace(),
                state_doc,
                {},
                current_snapshot,
                "@",
                dry_run=True,
            )
        self.assertEqual(selected_name, parent_name)
        self.assertEqual(selected_path, f"/moved/timeshift/snapshots/{parent_name}/@")

    def test_prune_resolves_protected_direct_path_under_current_snapshot_root(self):
        name = "2026-07-15_05-00-02"
        config = SimpleNamespace(
            source=SimpleNamespace(
                cleanup_superseded_cache=True,
                cache_root="/moved/cache",
                snapshot_root="/moved/timeshift/snapshots",
            )
        )
        snapshot_state = {
            "subvolumes": {
                "@": {
                    "status": "ok",
                    "send_path": f"{name}/@",
                    "send_path_kind": SEND_PATH_KIND_TIMESHIFT_ORIGINAL_READONLY,
                }
            }
        }
        self.assertEqual(
            retention._protected_timeshift_send_paths(config, name, snapshot_state),
            [("@", f"/moved/timeshift/snapshots/{name}/@")],
        )
        self.assertEqual(retention._source_cache_delete_paths(config, name, snapshot_state), [])

    def test_real_parent_guard_resolves_relative_state_path_before_uuid_match(self):
        parent_name = "2026-07-15_04-00-02"
        config = SimpleNamespace(
            source=SimpleNamespace(
                snapshot_root="/moved/timeshift/snapshots",
                cache_root="/moved/cache",
            ),
            destination=SimpleNamespace(target_root=Path("/moved/target")),
        )
        parent_state = {
            "status": "ok",
            "send_path": f"{parent_name}/@",
            "send_path_kind": SEND_PATH_KIND_SOURCE_CACHE,
        }
        destination_meta = SubvolumeMeta(
            name="@",
            path=f"/moved/target/snapshots/{parent_name}/@",
            received_uuid="cache-parent-uuid",
        )
        seen_paths: list[str] = []

        def matcher(*args, source_path: str, **kwargs):
            seen_paths.append(source_path)
            return True, "uuid matched"

        with (
            patch.object(sync, "_read_local_destination_parent_metadata", return_value=destination_meta),
            patch.object(sync, "_match_source_path_to_destination_received_uuid", side_effect=matcher),
        ):
            selected, reason = sync._select_verified_parent_send_path(
                config,
                SimpleNamespace(),
                parent_name=parent_name,
                parent_subvol=None,
                subvolume_name="@",
                state_parent=parent_state,
            )
        self.assertEqual(selected, f"/moved/cache/{parent_name}/@")
        self.assertEqual(seen_paths, [f"/moved/cache/{parent_name}/@"])
        self.assertEqual(reason, "uuid matched")

    def test_prune_plan_reporting_resolves_relative_source_and_destination_paths(self):
        name = "2026-07-15_05-00-02"
        config = SimpleNamespace(
            source=SimpleNamespace(
                cleanup_superseded_cache=True,
                cache_root="/moved/cache",
                snapshot_root="/moved/timeshift/snapshots",
            ),
            destination=SimpleNamespace(target_root=Path("/moved/target")),
        )
        state_doc = {
            "snapshots": {
                name: {
                    "name": name,
                    "tags": ["H"],
                    "subvolumes": {
                        "@": {
                            "status": "ok",
                            "send_path": f"{name}/@",
                            "send_path_kind": SEND_PATH_KIND_SOURCE_CACHE,
                            "destination_path": f"snapshots/{name}/@",
                        }
                    },
                }
            }
        }
        plan = retention.PrunePlan(delete={name}, reasons={name: ["delete: test"]})
        with patch.object(retention, "emit_success_summary") as emit:
            retention.print_prune_plan(config, plan, state_doc, dry_run=True)
        rendered = emit.call_args.args[0]
        self.assertIn(f"/moved/cache/{name}/@", rendered)
        self.assertIn(f"/moved/target/snapshots/{name}/@", rendered)

    def test_relative_source_path_must_match_snapshot_and_subvolume_identity(self):
        with self.assertRaises(ValueError):
            source_path_to_relative(
                "another-snapshot/@",
                "/source/snapshots",
                snapshot_name="2026-07-15_05-00-02",
                subvolume_name="@",
            )


if __name__ == "__main__":
    unittest.main()
