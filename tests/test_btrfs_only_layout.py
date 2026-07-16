from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from timeshift_btrfs_sync import destroy, remote_index, sync
from timeshift_btrfs_sync.commands import Completed
from timeshift_btrfs_sync.config import load_config
from timeshift_btrfs_sync.models import SubvolumeMeta
from timeshift_btrfs_sync.sync import SyncError


SNAPSHOT = "2026-07-14_01-00-00"


class DestinationDateSubvolumeTests(unittest.TestCase):
    def make_config(self, root: Path):
        config = load_config("timeshift_btrfs_sync/data/config.example.toml")
        config.source.subvolumes = ["@", "@home"]
        config.destination.target_root = root
        return config

    def test_new_date_path_is_created_as_btrfs_subvolume_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = self.make_config(Path(tmp) / "target")
            snapshots_root = config.destination.target_root / "snapshots"
            snapshots_root.mkdir(parents=True)
            date_path = snapshots_root / SNAPSHOT
            index = remote_index.BtrfsIndex(str(config.destination.target_root), "local")
            created: list[Path] = []
            refreshed: list[Path] = []

            def fake_create(path: Path, *_args) -> None:
                created.append(path)
                path.mkdir()

            def fake_refresh(current_index, path, **_kwargs):
                refreshed.append(Path(path))
                meta = SubvolumeMeta(Path(path).name, str(path), uuid="date-uuid")
                current_index.add(meta)
                return meta

            with (
                patch.object(sync.btrfs, "create_local_subvolume", side_effect=fake_create),
                patch.object(sync.remote_index, "refresh_local_path", side_effect=fake_refresh),
            ):
                self.assertEqual(sync._ensure_destination_snapshot_subvolume(config, SNAPSHOT, index), date_path)
                self.assertEqual(sync._ensure_destination_snapshot_subvolume(config, SNAPSHOT, index), date_path)

            self.assertEqual(created, [date_path])
            self.assertEqual(refreshed, [date_path])

    def test_existing_ordinary_date_folder_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = self.make_config(Path(tmp) / "target")
            date_path = config.destination.target_root / "snapshots" / SNAPSHOT
            date_path.mkdir(parents=True)
            index = remote_index.BtrfsIndex(str(config.destination.target_root), "local")
            with self.assertRaisesRegex(SyncError, "Unsupported destination layout"):
                sync._validate_destination_snapshot_layout(config, index)


class DestroyBtrfsOnlyTests(unittest.TestCase):
    def test_nonempty_ordinary_destination_root_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "ordinary-root"
            root.mkdir()
            (root / "unknown-file").write_text("keep", encoding="utf-8")
            with (
                patch.object(destroy, "_local_exists", return_value=(True, "")),
                patch.object(destroy, "_local_subvolume_meta", return_value=None),
                patch.object(destroy.btrfs, "delete_local_subvolume") as delete_mock,
            ):
                result = destroy._delete_local_tree(str(root), "", "btrfs", dry_run=False, label="destination.target_root")
            self.assertTrue(result.errors)
            self.assertIn("ordinary non-empty directory", result.errors[0])
            delete_mock.assert_not_called()
            self.assertTrue(root.exists())


    def test_nonempty_ordinary_source_cache_root_is_refused(self) -> None:
        class FakeSource:
            def command(self, source_command: str):
                return ["sh", "-c", source_command]

            def environment(self):
                return None

        source = FakeSource()
        with (
            patch.object(destroy, "_source_subvolume_meta", return_value=None),
            patch.object(destroy, "_source_exists", return_value=(True, "")),
            patch.object(
                destroy,
                "_run_source_quiet",
                return_value=Completed("inspect", 3, "TSBTRFS_ORDINARY_NONEMPTY\n", ""),
            ),
            patch.object(destroy, "_source_delete_subvolumes_batched") as delete_mock,
        ):
            result = destroy._delete_source_tree(
                source,
                "/cache",
                "sudo -n",
                "btrfs",
                dry_run=False,
                label="source.cache_root",
                protected_snapshot_root="/timeshift/snapshots",
            )
        self.assertTrue(result.errors)
        self.assertIn("ordinary non-empty directory", result.errors[0])
        delete_mock.assert_not_called()

    def test_source_batch_contains_only_btrfs_subvolume_deletes(self) -> None:
        class FakeSource:
            def __init__(self) -> None:
                self.commands: list[str] = []

            def command(self, source_command: str):
                return ["sh", "-c", source_command]

            def environment(self):
                return None

        source = FakeSource()
        captured: list[str] = []

        def fake_run(source_obj, command: str):
            captured.append(command)
            return Completed(command, 0, "TSBTRFS_DELETED\t/cache/date/@\n", "")

        with patch.object(destroy, "_run_source_quiet", side_effect=fake_run):
            deleted, errors = destroy._source_delete_subvolumes_batched(
                source,
                ["/cache/date/@"],
                "sudo -n",
                "btrfs",
                protected_snapshot_root="/timeshift/snapshots",
            )

        self.assertEqual(deleted, 1)
        self.assertEqual(errors, [])
        self.assertEqual(len(captured), 1)
        self.assertIn("subvolume delete", captured[0])
        self.assertNotIn("rm -rf", captured[0])
        self.assertNotIn("rmdir", captured[0])

    def test_runtime_package_contains_no_recursive_rm_fallback(self) -> None:
        package_root = Path("timeshift_btrfs_sync")
        offenders = []
        for path in package_root.glob("*.py"):
            text = path.read_text(encoding="utf-8")
            if "rm -rf" in text:
                offenders.append(path.name)
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
