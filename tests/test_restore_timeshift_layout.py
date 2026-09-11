from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace

from timeshift_btrfs_sync.inventory import BtrfsIndex
from timeshift_btrfs_sync import restore
from timeshift_btrfs_sync.config import load_config


DATE = "2026-06-23_07-10-24"


class TimeshiftNativeLayoutTests(unittest.TestCase):
    def test_misrouted_native_timeshift_date_gets_transport_guidance(self):
        config = SimpleNamespace(
            source=SimpleNamespace(
                snapshot_root="/media/OS-Root/timeshift-btrfs/snapshots",
                subvolumes=["@", "@home"],
            ),
            destination=SimpleNamespace(
                target_root=Path("/media/OS-Root/timeshift-btrfs"),
            ),
        )
        repository = restore.BackupRepository(
            config=config,
            runner=SimpleNamespace(uses_ssh=False),
            endpoint=SimpleNamespace(),
            ops=SimpleNamespace(meta=lambda *args, **kwargs: None),
        )
        record = restore.BackupDirectoryRecord(
            name=DATE,
            kind="directory",
            entries={"@": "directory", "@home": "directory", "info.json": "file"},
            info_content='{"sys-uuid":"root","type":"btrfs"}\n',
        )

        with self.assertRaisesRegex(
            restore.RestoreError,
            r'Timeshift date folders.*ordinary directories.*mode = \"ssh\"',
        ):
            restore._validate_backup_snapshot(
                config,
                repository,
                record,
                BtrfsIndex(repository.snapshots_root, "local"),
            )

    def test_pull_profile_transport_is_enabled_without_cli_flag(self):
        config = load_config(Path("timeshift_btrfs_sync/data/config.restore-pull.example.toml"))
        self.assertEqual(config.restore.mode, "ssh")
        self.assertEqual(config.source.mode, "local")


if __name__ == "__main__":
    unittest.main()
