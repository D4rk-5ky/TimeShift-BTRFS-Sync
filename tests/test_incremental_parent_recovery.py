"""Regression scenarios for snapshot churn, live UUID proof and retention."""

from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from timeshift_btrfs_sync import inventory, retention, sync
from timeshift_btrfs_sync.config import load_config
from timeshift_btrfs_sync.models import SnapshotMeta, SubvolumeMeta


DAILY = "2026-09-10_00-00-00"
HOURLY = "2026-09-10_01-00-00"
NEWEST = "2026-09-10_02-00-00"


class IncrementalParentRecoveryTests(unittest.TestCase):
    def setUp(self):
        """Build isolated inventories so tests never run Btrfs, sudo or SSH."""
        self.config = load_config(Path(__file__).resolve().parents[1] / "timeshift_btrfs_sync/data/config.example.toml")
        self.config.source.snapshot_root = "/source/snapshots"
        self.config.source.cache_root = "/source/cache"
        self.config.source.subvolumes = ["@"]
        self.config.destination.target_root = Path("/backup")
        self.source = SimpleNamespace()
        self.cache = inventory.BtrfsIndex("/source/cache", "test")
        self.originals = inventory.BtrfsIndex("/source/snapshots", "test")
        self.dest = inventory.BtrfsIndex("/backup/snapshots", "test")
        self.state = {"snapshots": {}}
        self.source_by_name = {}

    def add_pair(self, name, *, original=True, cache_path=None):
        """Represent an immutable send-cache and its completed received copy."""
        cache_path = cache_path or f"/source/cache/{name}/@"
        source_uuid = f"stream-{name}"
        self.cache.add(SubvolumeMeta("@", cache_path, uuid=source_uuid, readonly=True))
        dest_path = f"/backup/snapshots/{name}/@"
        self.dest.add(SubvolumeMeta("@", dest_path, uuid=f"received-{name}", received_uuid=source_uuid, readonly=True))
        self.state["snapshots"][name] = {
            "tags": ["D" if name == DAILY else "H"],
            "subvolumes": {"@": {
                "status": "ok", "send_path": cache_path.removeprefix("/source/cache/"), "send_path_kind": "source-cache",
                "send_source_uuid": source_uuid, "destination_path": dest_path.removeprefix("/backup/"),
                "original_source_uuid": f"original-{name}",
            }},
        }
        if original:
            original_path = f"/source/snapshots/{name}/@"
            meta = SubvolumeMeta("@", original_path, uuid=f"original-{name}", readonly=False)
            self.originals.add(meta)
            self.source_by_name[name] = SnapshotMeta(name, f"/source/snapshots/{name}", tags=list(self.state["snapshots"][name]["tags"]), subvolumes={"@": meta})

    def select_parent(self, filesystem_names=None):
        """Choose a parent using only the fake filesystem metadata."""
        with (
            patch.object(sync, "_filesystem_parent_candidates", return_value=filesystem_names or []),
            patch.object(sync, "_source_meta", side_effect=lambda _config, _source, path, *_args, **_kwargs: self.cache.meta(path) or self.originals.meta(path)),
        ):
            return sync._select_parent(
                self.config, self.source, self.state, self.source_by_name,
                SnapshotMeta(NEWEST, "/unused"), "@", dry_run=False,
                source_cache_index=self.cache, source_snapshot_index=self.originals,
                destination_index=self.dest,
            )

    def test_newest_cache_match_wins_when_original_hourly_is_gone(self):
        self.add_pair(DAILY)
        self.add_pair(HOURLY, original=False)
        self.assertEqual(self.select_parent(), (HOURLY, f"/source/cache/{HOURLY}/@"))

    def test_newer_filesystem_match_wins_over_older_state_parent(self):
        self.add_pair(DAILY)
        self.add_pair(HOURLY)
        self.state["snapshots"].pop(HOURLY)
        self.assertEqual(self.select_parent([HOURLY, DAILY])[0], HOURLY)

    def test_missing_newer_destination_falls_back_to_daily(self):
        self.add_pair(DAILY)
        self.add_pair(HOURLY)
        self.dest.discard(f"/backup/snapshots/{HOURLY}/@")
        with patch.object(Path, "exists", return_value=False):
            self.assertEqual(self.select_parent(), (DAILY, f"/source/cache/{DAILY}/@"))

    def test_stale_state_uuid_cannot_override_actual_destination(self):
        self.add_pair(DAILY)
        self.dest.meta(f"/backup/snapshots/{DAILY}/@").received_uuid = "different-stream"
        ok, _ = sync._match_source_path_to_destination_received_uuid(
            self.config, self.source, source_path=f"/source/cache/{DAILY}/@",
            subvolume_name="@", destination_meta=self.dest.meta(f"/backup/snapshots/{DAILY}/@"),
            expected_uuids={f"stream-{DAILY}"}, require_readonly=True,
            source_cache_index=self.cache,
        )
        self.assertFalse(ok)

    def test_unknown_source_readonly_is_not_a_verified_parent(self):
        self.add_pair(DAILY)
        self.cache.meta(f"/source/cache/{DAILY}/@").readonly = None
        with self.assertRaises(sync.SyncError):
            self.select_parent()

    def test_writable_destination_is_not_a_verified_parent(self):
        self.add_pair(DAILY)
        self.dest.meta(f"/backup/snapshots/{DAILY}/@").readonly = False
        with self.assertRaises(sync.SyncError):
            self.select_parent()

    def test_state_adoption_rejects_unproven_cache_or_receiver(self):
        for cache_readonly, destination_readonly in ((None, True), (False, True), (True, None), (True, False)):
            with self.subTest(cache=cache_readonly, destination=destination_readonly):
                self.add_pair(DAILY)
                self.cache.meta(f"/source/cache/{DAILY}/@").readonly = cache_readonly
                self.dest.meta(f"/backup/snapshots/{DAILY}/@").readonly = destination_readonly
                result = sync._match_existing_destination_to_source(
                    self.config, self.source, self.source_by_name,
                    snapshot_name=DAILY, subvolume_name="@",
                    destination_meta=self.dest.meta(f"/backup/snapshots/{DAILY}/@"),
                    source_cache_index=self.cache, source_snapshot_index=self.originals,
                )
                self.assertIsNone(result[2])

    def test_floor_requires_all_configured_payloads(self):
        self.add_pair(DAILY)
        self.config.source.subvolumes = ["@", "@home"]
        name, _ = sync._find_confirmed_sync_floor(
            self.config, self.source, self.state, self.source_by_name,
            source_cache_index=self.cache, source_snapshot_index=self.originals,
            destination_index=self.dest,
        )
        self.assertIsNone(name)

    def test_floor_finds_relocated_cache_by_uuid_after_original_disappears(self):
        self.add_pair(HOURLY, original=False, cache_path="/source/cache/relocated/@")
        self.state["snapshots"][HOURLY]["subvolumes"]["@"]["send_path"] = f"{HOURLY}/@"
        with patch.object(sync, "_source_meta", side_effect=lambda _config, _source, path, *_args, **_kwargs: self.cache.meta(path)):
            # Indexed UUID lookup must find the live path before probing the stale saved path.
            name, _ = sync._find_confirmed_sync_floor(
                self.config, self.source, self.state, self.source_by_name,
                source_cache_index=self.cache, source_snapshot_index=self.originals,
                destination_index=self.dest,
            )
        self.assertEqual(name, HOURLY)

    def test_tag_changes_do_not_change_verified_parent(self):
        self.add_pair(DAILY)
        self.source_by_name[DAILY].tags = ["W", "M"]
        self.assertEqual(self.select_parent()[0], DAILY)

    def test_hourly_without_original_or_cache_falls_back_to_daily(self):
        self.add_pair(DAILY)
        self.add_pair(HOURLY, original=False)
        self.cache.discard(f"/source/cache/{HOURLY}/@")
        self.assertEqual(self.select_parent()[0], DAILY)

    def test_existing_destination_cannot_silently_full_send_without_parent(self):
        self.add_pair(HOURLY, original=False)
        self.cache.discard(f"/source/cache/{HOURLY}/@")
        with self.assertRaisesRegex(sync.SyncError, "full send is refused"):
            self.select_parent()

    def test_full_seed_is_allowed_only_with_explicit_empty_start_permission(self):
        with patch.object(sync, "_filesystem_parent_candidates", return_value=[]):
            self.assertEqual(sync._select_parent(
                self.config, self.source, self.state, {}, SnapshotMeta(NEWEST, "/unused"), "@",
                dry_run=False, allow_full_seed=True,
            ), (None, None))

    def test_verified_daily_survives_retention_when_newest_hourly_is_not_shared(self):
        self.add_pair(DAILY)
        self.add_pair(HOURLY, original=False)
        self.config.retention.keep_latest = False
        for key in ("hourly", "daily", "weekly", "monthly", "boot"):
            setattr(self.config.retention, key, 0)
        plan = retention.build_prune_plan(self.config, self.state, common_parent_name=DAILY)
        self.assertIn(DAILY, plan.keep)
        self.assertIn(HOURLY, plan.delete)

    def test_prune_anchor_uses_the_same_live_floor_proof(self):
        self.add_pair(DAILY)
        self.add_pair(HOURLY, original=False)
        self.cache.discard(f"/source/cache/{HOURLY}/@")
        built = inventory.SourceInventory("", self.originals, self.cache)
        with (
            patch.object(retention.inventory, "build_source_inventory", return_value=built),
            patch.object(retention.inventory, "build_local_btrfs_index", return_value=self.dest),
            patch.object(sync, "_snapshots_from_source_inventory", return_value=self.source_by_name),
            patch.object(sync, "_source_meta", side_effect=lambda _config, _source, path, *_args, **_kwargs: self.cache.meta(path) or self.originals.meta(path)),
        ):
            self.assertEqual(retention._confirmed_prune_parent(self.config, self.state), DAILY)

    def test_prune_without_proven_anchor_stops_before_any_delete(self):
        self.config.manual_snapshot.cleanup_enabled = False
        with (
            patch.object(retention, "build_prune_plan", return_value=retention.PrunePlan(delete={HOURLY})),
            patch.object(retention, "_confirmed_prune_parent", side_effect=RuntimeError("no proven parent")),
            patch.object(retention, "_delete_prune_item") as delete,
            patch.object(retention, "save_state") as save,
        ):
            with self.assertRaisesRegex(RuntimeError, "no proven parent"):
                retention.prune(self.config, self.state, dry_run=False, yes_delete=True)
            delete.assert_not_called()
            save.assert_not_called()

    def test_retention_selection_avoids_sending_unneeded_hourlies(self):
        self.add_pair(DAILY)
        self.config.retention.hourly = 1
        self.config.retention.daily = 1
        self.source_by_name[HOURLY] = SnapshotMeta(HOURLY, "/unused", tags=["H"])
        self.source_by_name[NEWEST] = SnapshotMeta(NEWEST, "/unused", tags=["H"])
        selected = sync._select_initial_sync_snapshots(self.config, self.source_by_name)
        self.assertEqual([item.name for item in selected], [DAILY, NEWEST])

    def test_completed_outside_retention_is_kept_in_queue_for_metadata_refresh(self):
        self.add_pair(DAILY)
        self.add_pair(HOURLY)
        self.config.retention.hourly = 1
        self.config.retention.daily = 1
        self.source_by_name[NEWEST] = SnapshotMeta(NEWEST, "/unused", tags=["H"])
        with patch.object(sync, "_snapshot_destination_paths_exist", return_value=True):
            selected = sync._select_initial_sync_snapshots(self.config, self.source_by_name, state=self.state)
        self.assertEqual([item.name for item in selected], [DAILY, HOURLY, NEWEST])


if __name__ == "__main__":
    unittest.main()
