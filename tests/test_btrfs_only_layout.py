from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from timeshift_btrfs_sync import destroy, inventory, sync
from timeshift_btrfs_sync.btrfs_ops import BtrfsOps
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
            index = inventory.BtrfsIndex(str(config.destination.target_root), "local")
            created: list[Path] = []
            refreshed: list[Path] = []

            def fake_create(path: Path, *_args) -> None:
                created.append(path)
                path.mkdir()

            def fake_refresh(current_index, _ops, path, **_kwargs):
                refreshed.append(Path(path))
                meta = SubvolumeMeta(Path(path).name, str(path), uuid="date-uuid")
                current_index.add(meta)
                return meta

            with (
                patch.object(BtrfsOps, "create", side_effect=fake_create),
                patch.object(sync.inventory, "refresh_path", side_effect=fake_refresh),
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
            index = inventory.BtrfsIndex(str(config.destination.target_root), "local")
            with self.assertRaisesRegex(SyncError, "Unsupported destination layout"):
                sync._validate_destination_snapshot_layout(config, index)


class DestroyBtrfsOnlyTests(unittest.TestCase):
    def test_nonempty_ordinary_root_is_refused_by_shared_tree_engine(self) -> None:
        from timeshift_btrfs_sync.btrfs_ops import BtrfsOps
        from timeshift_btrfs_sync.endpoint import CommandEndpoint
        from timeshift_btrfs_sync import tree_ops
        ops = BtrfsOps(CommandEndpoint.local("test"), "", "btrfs")
        with (
            patch.object(tree_ops, "_path_exists", return_value=(True, "")),
            patch.object(BtrfsOps, "meta", return_value=None),
        ):
            result = tree_ops.delete_subvolume_tree(ops, "/cache")
        self.assertFalse(result.success)
        self.assertTrue(any("ordinary path" in error for error in result.errors))

    def test_batch_delete_uses_only_btrfs_and_rejects_bad_confirmations(self) -> None:
        from timeshift_btrfs_sync.btrfs_ops import BtrfsOps
        from timeshift_btrfs_sync.endpoint import CommandEndpoint
        endpoint = CommandEndpoint.local("test")
        output = (
            "TSBTRFS_DELETED\t/cache/a\n"
            "TSBTRFS_DELETED\t/cache/a\n"
            "TSBTRFS_DELETED\t/cache/unexpected\n"
        )
        captured = []
        def fake_run(script, **kwargs):
            captured.append(script)
            return Completed(script, 0, output, "")
        with patch.object(CommandEndpoint, "run_shell", side_effect=fake_run):
            confirmed, errors = BtrfsOps(endpoint, "sudo -n", "btrfs").batch_delete(["/cache/a", "/cache/b"])
        self.assertEqual(confirmed, ["/cache/a"])
        self.assertTrue(any("duplicate" in error for error in errors))
        self.assertTrue(any("unexpected" in error for error in errors))
        self.assertIn("subvolume delete", captured[0])
        self.assertNotIn("rm -rf", captured[0])

    def test_runtime_package_contains_no_recursive_rm_fallback(self) -> None:
        package_root = Path("timeshift_btrfs_sync")
        offenders = [path.name for path in package_root.glob("*.py") if "rm -rf" in path.read_text(encoding="utf-8")]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
