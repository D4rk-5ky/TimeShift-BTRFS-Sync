from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from timeshift_btrfs_sync import remote_index, retention, sync
from timeshift_btrfs_sync.config import load_config
from timeshift_btrfs_sync.sync import SyncError


SNAPSHOT = "2026-07-14_01-00-00"
INFO_CONTENT = '{"date":"2026-07-14_01-00-00","tags":["H"]}\n'


def inventory_with_info(content: str = INFO_CONTENT) -> remote_index.SourceInventory:
    return remote_index.SourceInventory(
        timeshift_output=f"{SNAPSHOT} H hourly",
        snapshot_index=remote_index.BtrfsIndex("/snapshots", "remote"),
        cache_index=remote_index.BtrfsIndex("/cache", "remote"),
        snapshot_info_json={SNAPSHOT: content},
    )


class InfoJsonFrameTests(unittest.TestCase):
    def test_parser_preserves_content_with_final_newline(self) -> None:
        output = (
            f"before\nTSBTRFS_INFO_JSON_BEGIN\t{SNAPSHOT}\n"
            f"{INFO_CONTENT}"
            f"\nTSBTRFS_INFO_JSON_END\t{SNAPSHOT}\t0\nafter\n"
        )
        cleaned, captured, errors = remote_index._extract_snapshot_info_json_frames(output)
        self.assertEqual(captured[SNAPSHOT], INFO_CONTENT)
        self.assertEqual(errors, {})
        self.assertEqual(cleaned, "before\nafter\n")

    def test_local_reader_loads_only_timeshift_date_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            date_dir = root / SNAPSHOT
            date_dir.mkdir()
            (date_dir / "info.json").write_text(INFO_CONTENT, encoding="utf-8", newline="")
            other = root / "not-a-timeshift-date"
            other.mkdir()
            (other / "info.json").write_text("other", encoding="utf-8")
            captured, errors = remote_index._read_local_snapshot_info_json(str(root))
            self.assertEqual(captured, {SNAPSHOT: INFO_CONTENT})
            self.assertEqual(errors, {})

    def test_parser_preserves_content_without_final_newline(self) -> None:
        content = '{"date":"2026-07-14_01-00-00"}'
        output = (
            f"TSBTRFS_INFO_JSON_BEGIN\t{SNAPSHOT}\n"
            f"{content}\n"
            f"TSBTRFS_INFO_JSON_END\t{SNAPSHOT}\t0\n"
        )
        _cleaned, captured, errors = remote_index._extract_snapshot_info_json_frames(output)
        self.assertEqual(captured[SNAPSHOT], content)
        self.assertEqual(errors, {})


class DestinationInfoJsonTests(unittest.TestCase):
    def make_config(self, root: Path, subvolumes: list[str]):
        config = load_config("timeshift_btrfs_sync/data/config.example.toml")
        config.source.subvolumes = subvolumes
        config.destination.target_root = root
        return config

    def test_single_subvolume_snapshot_writes_shared_info_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = self.make_config(Path(tmp) / "target", ["@"])
            changed = sync._sync_snapshot_info_json(
                config,
                inventory_with_info(),
                SNAPSHOT,
                dry_run=False,
            )
            destination = config.destination.target_root / "snapshots" / SNAPSHOT / "info.json"
            self.assertTrue(changed)
            self.assertEqual(destination.read_text(encoding="utf-8"), INFO_CONTENT)

    def test_home_only_snapshot_writes_shared_info_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = self.make_config(Path(tmp) / "target", ["@home"])
            sync._sync_snapshot_info_json(config, inventory_with_info(), SNAPSHOT, dry_run=False)
            destination = config.destination.target_root / "snapshots" / SNAPSHOT / "info.json"
            self.assertEqual(destination.read_text(encoding="utf-8"), INFO_CONTENT)

    def test_paired_snapshot_is_complete_only_after_both_subvolumes_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = self.make_config(Path(tmp) / "target", ["@", "@home"])
            snapshot_dir = config.destination.target_root / "snapshots" / SNAPSHOT
            (snapshot_dir / "@").mkdir(parents=True)
            state = {
                "snapshots": {
                    SNAPSHOT: {
                        "subvolumes": {
                            "@": {"status": "ok", "destination_path": str(snapshot_dir / "@")},
                        }
                    }
                }
            }
            self.assertFalse(sync._snapshot_state_is_complete_with_destination(config, state, SNAPSHOT))

            (snapshot_dir / "@home").mkdir()
            state["snapshots"][SNAPSHOT]["subvolumes"]["@home"] = {
                "status": "ok",
                "destination_path": str(snapshot_dir / "@home"),
            }
            self.assertTrue(sync._snapshot_state_is_complete_with_destination(config, state, SNAPSHOT))
            sync._sync_snapshot_info_json(config, inventory_with_info(), SNAPSHOT, dry_run=False)
            self.assertEqual((snapshot_dir / "info.json").read_text(encoding="utf-8"), INFO_CONTENT)

    def test_existing_file_is_updated_and_then_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = self.make_config(Path(tmp) / "target", ["@"])
            destination = config.destination.target_root / "snapshots" / SNAPSHOT / "info.json"
            destination.parent.mkdir(parents=True)
            destination.write_text("old", encoding="utf-8")
            self.assertTrue(sync._sync_snapshot_info_json(config, inventory_with_info(), SNAPSHOT, dry_run=False))
            self.assertFalse(sync._sync_snapshot_info_json(config, inventory_with_info(), SNAPSHOT, dry_run=False))
            self.assertEqual(destination.read_text(encoding="utf-8"), INFO_CONTENT)

    def test_missing_source_metadata_is_a_hard_error(self) -> None:
        inventory = inventory_with_info()
        inventory.snapshot_info_json.clear()
        inventory.snapshot_info_errors[SNAPSHOT] = "info.json was not readable"
        with tempfile.TemporaryDirectory() as tmp:
            config = self.make_config(Path(tmp) / "target", ["@"])
            with self.assertRaisesRegex(SyncError, "refuses to complete"):
                sync._sync_snapshot_info_json(config, inventory, SNAPSHOT, dry_run=False)


    def test_missing_metadata_error_names_remote_user_uid_and_fstab_fix(self) -> None:
        inventory = inventory_with_info()
        inventory.snapshot_info_json.clear()
        inventory.snapshot_info_errors[SNAPSHOT] = "info.json exists but is not readable by the source user"
        inventory.source_user_name = "btrbk-source"
        inventory.source_user_uid = 1001
        with tempfile.TemporaryDirectory() as tmp:
            config = self.make_config(Path(tmp) / "target", ["@"] )
            with self.assertRaises(SyncError) as caught:
                sync._sync_snapshot_info_json(config, inventory, SNAPSHOT, dry_run=False)
        message = str(caught.exception)
        self.assertIn("btrbk-source (uid 1001)", message)
        self.assertIn("remote SSH source account used by this destination", message)
        self.assertIn("/etc/fstab", message)
        self.assertIn("execute/search permission on every parent directory", message)
        self.assertIn("POSIX ACL", message)

    def test_symlink_destination_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root / "target", ["@"])
            destination = config.destination.target_root / "snapshots" / SNAPSHOT / "info.json"
            destination.parent.mkdir(parents=True)
            outside = root / "outside.json"
            outside.write_text("outside", encoding="utf-8")
            destination.symlink_to(outside)
            with self.assertRaisesRegex(SyncError, "symlinked destination"):
                sync._sync_snapshot_info_json(config, inventory_with_info(), SNAPSHOT, dry_run=False)
            self.assertEqual(outside.read_text(encoding="utf-8"), "outside")

    def test_prune_preserves_info_json_when_unknown_content_remains(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = self.make_config(Path(tmp) / "target", ["@"])
            snapshot_dir = config.destination.target_root / "snapshots" / SNAPSHOT
            snapshot_dir.mkdir(parents=True)
            info_path = snapshot_dir / "info.json"
            info_path.write_text(INFO_CONTENT, encoding="utf-8")
            (snapshot_dir / "unknown-file").write_text("keep", encoding="utf-8")
            state = {"snapshots": {SNAPSHOT: {"subvolumes": {}}}}
            self.assertFalse(retention._delete_destination_snapshot_for_prune(config, state, SNAPSHOT))
            self.assertEqual(info_path.read_text(encoding="utf-8"), INFO_CONTENT)

    def test_prune_removes_info_json_after_subvolumes_are_gone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = self.make_config(Path(tmp) / "target", ["@"])
            snapshot_dir = config.destination.target_root / "snapshots" / SNAPSHOT
            snapshot_dir.mkdir(parents=True)
            (snapshot_dir / "info.json").write_text(INFO_CONTENT, encoding="utf-8")
            state = {"snapshots": {SNAPSHOT: {"subvolumes": {}}}}
            self.assertTrue(retention._delete_destination_snapshot_for_prune(config, state, SNAPSHOT))
            self.assertFalse(snapshot_dir.exists())


if __name__ == "__main__":
    unittest.main()
