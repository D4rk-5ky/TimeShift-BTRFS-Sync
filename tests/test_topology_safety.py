from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace

from timeshift_btrfs_sync.config import load_config
from timeshift_btrfs_sync.cli import build_parser, cmd_sync
from timeshift_btrfs_sync import restore
from timeshift_btrfs_sync.inventory import SourceInventory, BtrfsIndex
from timeshift_btrfs_sync.models import SubvolumeMeta
from timeshift_btrfs_sync.topology import (
    TopologyError,
    describe_restore_topology,
    describe_sync_topology,
    reject_pull_restore_profile_for_sync,
)


ROOT = Path(__file__).parents[1]
DATA = ROOT / "timeshift_btrfs_sync" / "data"


class TopologySafetyTests(unittest.TestCase):

    def test_sync_command_refuses_pull_restore_profile_before_work(self):
        config_path = DATA / "config.restore-pull.example.toml"
        args = build_parser().parse_args(["sync", "--config", str(config_path), "--dry-run"])
        with self.assertRaisesRegex(TopologyError, "Normal sync always writes"):
            cmd_sync(args)

    def test_pull_restore_profile_is_refused_for_sync(self):
        config = load_config(DATA / "config.restore-pull.example.toml")
        with self.assertRaisesRegex(TopologyError, "pull-restore profile"):
            reject_pull_restore_profile_for_sync(config)

    def test_remote_roundtrip_profile_is_valid_for_sync_and_push_restore(self):
        config = load_config(DATA / "config.remote-roundtrip.example.toml")
        reject_pull_restore_profile_for_sync(config)
        sync = describe_sync_topology(config)
        restore = describe_restore_topology(config)
        self.assertIn("SSH Timeshift source", sync.source_label)
        self.assertIn("local backup", sync.destination_label)
        self.assertIn("local backup", restore.source_label)
        self.assertIn("SSH Timeshift target", restore.destination_label)


    def test_no_overlap_reason_reports_both_newest_physical_dates(self):
        config = load_config(DATA / "config.remote-roundtrip.example.toml")
        backup_name = "2026-07-22_09-00-02"
        source_name = "2026-07-22_10-00-02"
        backups = {
            backup_name: restore.BackupSnapshot(
                backup_name,
                f"/backup/snapshots/{backup_name}",
                '{"sys-uuid":"one","type":"btrfs"}\n',
                {
                    "@": SubvolumeMeta("@", f"/backup/snapshots/{backup_name}/@", uuid="b1", received_uuid="s1", readonly=True),
                    "@home": SubvolumeMeta("@home", f"/backup/snapshots/{backup_name}/@home", uuid="b2", received_uuid="s2", readonly=True),
                },
            )
        }
        source_by_name = {source_name: SimpleNamespace(name=source_name)}
        inventory = SourceInventory(
            timeshift_output="",
            snapshot_index=BtrfsIndex(config.source.snapshot_root, "remote"),
            cache_index=BtrfsIndex(config.source.cache_root, "remote"),
        )
        common, reason = restore._find_latest_common_parent(
            config,
            backups,
            source_by_name,
            {},
            {"version": 3, "snapshots": {}},
            timeshift_ops=SimpleNamespace(),
            timeshift_inventory=inventory,
        )
        self.assertIsNone(common)
        self.assertIn(f"newest={backup_name}", reason)
        self.assertIn(f"newest={source_name}", reason)

    def test_restore_pull_and_push_endpoint_descriptions_are_directional(self):
        pull = load_config(DATA / "config.restore-pull.example.toml")
        push = load_config(DATA / "config.remote-roundtrip.example.toml")
        self.assertIn("SSH backup repository", describe_restore_topology(pull).source_label)
        self.assertEqual(describe_restore_topology(pull).destination_label, "local Timeshift target")
        self.assertEqual(describe_restore_topology(push).source_label, "local backup repository")
        self.assertIn("SSH Timeshift target", describe_restore_topology(push).destination_label)


if __name__ == "__main__":
    unittest.main()
