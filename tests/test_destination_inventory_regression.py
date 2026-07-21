from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from timeshift_btrfs_sync import inventory, preflight, sync
from timeshift_btrfs_sync.btrfs_ops import BtrfsOps
from timeshift_btrfs_sync.commands import Completed
from timeshift_btrfs_sync.config import load_config
from timeshift_btrfs_sync.endpoint import CommandEndpoint
from timeshift_btrfs_sync.models import SubvolumeMeta
from timeshift_btrfs_sync.sync import SyncError


SNAPSHOT = "2026-07-17_19-57-22"


class DestinationInventoryRegressionTests(unittest.TestCase):
    def make_config(self, root: Path):
        config = load_config("timeshift_btrfs_sync/data/config.example.toml")
        config.destination.target_root = root
        config.log_dir = root.parent / "logs"
        config.lock_file = root / ".ts-btrfs-sync" / "lock"
        config.state_file = root / ".ts-btrfs-sync" / "state.json"
        return config

    def test_mounted_destination_list_path_maps_from_snapshots_root(self) -> None:
        root = "/media/darkyere/btrbk/KubuntuBTRFSRAID0/snapshots"
        output = (
            "ID 100 gen 1 top level 256 parent_uuid - received_uuid - "
            f"uuid date-uuid path snapshots/{SNAPSHOT}\n"
            "ID 101 gen 1 top level 100 parent_uuid - received_uuid send-uuid "
            f"uuid payload-uuid path snapshots/{SNAPSHOT}/@\n"
        )
        metas = inventory.parse_subvolume_list(output, root)
        self.assertEqual(
            [meta.path for meta in metas],
            [f"{root}/{SNAPSHOT}", f"{root}/{SNAPSHOT}/@"],
        )

    def test_sync_builds_destination_index_from_snapshots_subvolume(self) -> None:
        class StopAfterIndex(RuntimeError):
            pass

        class LocalSource:
            uses_ssh = False

        with tempfile.TemporaryDirectory() as tmp:
            config = self.make_config(Path(tmp) / "target")
            expected = config.destination.target_root / "snapshots"
            seen: list[Path] = []

            def stop_index(root, **_kwargs):
                seen.append(Path(root))
                raise StopAfterIndex

            with (
                patch.object(sync.SourceRunner, "from_config", return_value=LocalSource()),
                patch.object(sync.preflight, "check_required_sync_paths"),
                patch.object(sync, "prepare_destination"),
                patch.object(sync.inventory, "build_local_btrfs_index", side_effect=stop_index),
            ):
                with self.assertRaises(StopAfterIndex):
                    sync.sync_once(config, {"snapshots": {}}, dry_run=False)

            self.assertEqual(seen, [expected])

    def test_bulk_index_miss_is_exact_probed_before_layout_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = self.make_config(Path(tmp) / "target")
            date_path = config.destination.target_root / "snapshots" / SNAPSHOT
            date_path.mkdir(parents=True)
            index = inventory.BtrfsIndex(str(date_path.parent), "local")
            meta = SubvolumeMeta(SNAPSHOT, str(date_path), uuid="date-uuid")

            with patch.object(sync.inventory, "refresh_path", return_value=meta) as refresh:
                sync._validate_destination_snapshot_layout(config, index)

            refresh.assert_called_once()

    def test_exact_probe_still_refuses_real_ordinary_date_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = self.make_config(Path(tmp) / "target")
            date_path = config.destination.target_root / "snapshots" / SNAPSHOT
            date_path.mkdir(parents=True)
            index = inventory.BtrfsIndex(str(date_path.parent), "local")

            with patch.object(sync.inventory, "refresh_path", return_value=None):
                with self.assertRaisesRegex(SyncError, "exact btrfs subvolume show probe"):
                    sync._validate_destination_snapshot_layout(config, index)

    def test_destination_snapshots_never_falls_back_to_mkdir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = self.make_config(Path(tmp) / "target")
            config.destination.target_root.mkdir()
            snapshots_root = config.destination.target_root / "snapshots"
            failed = subprocess.CompletedProcess(
                args=["btrfs"],
                returncode=1,
                stdout="",
                stderr="forced create failure",
            )

            with (
                patch.object(preflight, "_local_btrfs_result", return_value=failed),
                patch.object(Path, "mkdir") as mkdir_mock,
            ):
                result = preflight.ensure_local_helper_dir(
                    config,
                    "destination.snapshots",
                    snapshots_root,
                    dry_run=False,
                    require_btrfs=True,
                )

            self.assertFalse(result.ok)
            self.assertIn("mkdir fallback is disabled", result.detail)
            mkdir_mock.assert_not_called()

    def test_btrfs_create_operation_uses_subvolume_create(self) -> None:
        captured: list[list[str]] = []

        def fake_run(argv, **_kwargs):
            captured.append(list(argv))
            return Completed(0, "", "")

        endpoint = CommandEndpoint.local()
        with patch.object(CommandEndpoint, "run_argv", side_effect=fake_run):
            BtrfsOps(endpoint, "sudo -n", "btrfs").create("/backup/snapshots/date")

        self.assertEqual(
            captured,
            [["sudo", "-n", "btrfs", "subvolume", "create", "/backup/snapshots/date"]],
        )


if __name__ == "__main__":
    unittest.main()
