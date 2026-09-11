from __future__ import annotations

from pathlib import Path
import unittest

from timeshift_btrfs_sync.commands import Completed
from timeshift_btrfs_sync.config import load_config
from timeshift_btrfs_sync.inventory import BtrfsIndex, SourceInventory
from timeshift_btrfs_sync.models import SnapshotMeta, SubvolumeMeta
from timeshift_btrfs_sync.restore import (
    BackupSnapshot,
    TimeshiftOsIdentity,
    _find_latest_common_parent,
    _same_os_identity,
    _scan_snapshot_directories,
)
from timeshift_btrfs_sync.topology import (
    TopologyError,
    describe_restore_topology,
    describe_sync_topology,
    reject_pull_restore_profile_for_sync,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "timeshift_btrfs_sync" / "data"


class _UnusedTimeshiftOps:
    def meta(self, *args, **kwargs):  # pragma: no cover - a failing call is the test failure
        raise AssertionError("exact fallback probe should not be needed in this fixture")


class _CapturingEndpoint:
    def __init__(self, stdout: str = ""):
        self.stdout = stdout
        self.script = ""

    def run_shell(self, script: str, **kwargs) -> Completed:
        self.script = script
        return Completed(0, self.stdout, "")


class RestoreTopologyRegressionTests(unittest.TestCase):
    def test_pull_restore_profile_is_refused_for_sync(self) -> None:
        config = load_config(DATA_DIR / "config.restore-pull.example.toml")
        with self.assertRaisesRegex(TopologyError, "pull-restore profile"):
            reject_pull_restore_profile_for_sync(config)

    def test_remote_roundtrip_uses_one_ssh_timeshift_host_in_both_directions(self) -> None:
        config = load_config(DATA_DIR / "config.remote-roundtrip.example.toml")
        sync_topology = describe_sync_topology(config)
        restore_topology = describe_restore_topology(config)
        self.assertIn("SSH Timeshift source", sync_topology.source_label)
        self.assertEqual(sync_topology.destination_label, "local backup destination")
        self.assertEqual(restore_topology.source_label, "local backup repository")
        self.assertIn("SSH Timeshift target", restore_topology.destination_label)
        assert config.ssh is not None
        self.assertIn(config.ssh.host, sync_topology.source_label)
        self.assertIn(config.ssh.host, restore_topology.destination_label)

    def test_pull_and_push_restore_directions_are_described_separately(self) -> None:
        pull = load_config(DATA_DIR / "config.restore-pull.example.toml")
        push = load_config(DATA_DIR / "config.remote-roundtrip.example.toml")
        pull_topology = describe_restore_topology(pull)
        push_topology = describe_restore_topology(push)
        self.assertIn("SSH backup repository", pull_topology.source_label)
        self.assertEqual(pull_topology.destination_label, "local Timeshift target")
        self.assertEqual(push_topology.source_label, "local backup repository")
        self.assertIn("SSH Timeshift target", push_topology.destination_label)

    def test_no_overlap_diagnostic_reports_counts_and_newest_dates(self) -> None:
        config = load_config(DATA_DIR / "config.example.toml")
        backup = BackupSnapshot(
            "2026-07-20_10-00-00",
            "/backup/2026-07-20_10-00-00",
            "{}",
            {},
        )
        source = SnapshotMeta("2026-07-21_10-00-00", "/timeshift/2026-07-21_10-00-00")
        common, reason = _find_latest_common_parent(
            config,
            {backup.name: backup},
            {source.name: source},
            {},
            {},
            timeshift_ops=None,  # branch returns before either object is used
            timeshift_inventory=None,
        )
        self.assertIsNone(common)
        self.assertIn("backup dates=1 newest=2026-07-20_10-00-00", reason)
        self.assertIn("Timeshift dates=1 newest=2026-07-21_10-00-00", reason)

    def test_same_date_info_identity_recovers_when_state_and_cache_proof_are_missing(self) -> None:
        config = load_config(DATA_DIR / "config.example.toml")
        config.source.subvolumes = ["@"]
        config.source.cache_root = None
        name = "2026-07-20_10-00-00"
        source_meta = SubvolumeMeta("@", f"/timeshift/{name}/@", uuid="source-uuid", readonly=False)
        backup_meta = SubvolumeMeta(
            "@",
            f"/backup/{name}/@",
            uuid="backup-local-uuid",
            received_uuid="different-send-uuid",
            readonly=True,
        )
        source_snapshot = SnapshotMeta(name, f"/timeshift/{name}", subvolumes={"@": source_meta})
        backup_snapshot = BackupSnapshot(
            name,
            f"/backup/{name}",
            "{}",
            {"@": backup_meta},
            TimeshiftOsIdentity("root-os-uuid", "btrfs", "backup distro text"),
        )
        inventory = SourceInventory(
            timeshift_output=f"> {name} O",
            snapshot_index=BtrfsIndex("/timeshift", "test"),
            cache_index=None,
        )
        common, reason = _find_latest_common_parent(
            config,
            {name: backup_snapshot},
            {name: source_snapshot},
            {name: TimeshiftOsIdentity("root-os-uuid", "btrfs", "different mutable distro text")},
            {"snapshots": {}},
            timeshift_ops=_UnusedTimeshiftOps(),
            timeshift_inventory=inventory,
        )
        self.assertEqual(common, name)
        self.assertIn("same physical timestamp", reason)
        self.assertIn("info.json match sys-uuid root-os-uuid", reason)

    def test_exact_state_uuid_proof_remains_authoritative(self) -> None:
        config = load_config(DATA_DIR / "config.example.toml")
        config.source.subvolumes = ["@"]
        config.source.cache_root = None
        name = "2026-07-20_10-00-00"
        source_meta = SubvolumeMeta("@", f"/timeshift/{name}/@", uuid="source-uuid", readonly=False)
        backup_meta = SubvolumeMeta(
            "@",
            f"/backup/{name}/@",
            uuid="backup-local-uuid",
            received_uuid="sent-uuid",
            readonly=True,
        )
        source_snapshot = SnapshotMeta(name, f"/timeshift/{name}", subvolumes={"@": source_meta})
        backup_snapshot = BackupSnapshot(name, f"/backup/{name}", "{}", {"@": backup_meta}, None)
        state = {
            "snapshots": {
                name: {
                    "subvolumes": {
                        "@": {
                            "status": "ok",
                            "original_source_uuid": "source-uuid",
                            "send_source_uuid": "sent-uuid",
                        }
                    }
                }
            }
        }
        inventory = SourceInventory(
            timeshift_output="",
            snapshot_index=BtrfsIndex("/timeshift", "test"),
            cache_index=None,
        )
        common, reason = _find_latest_common_parent(
            config,
            {name: backup_snapshot},
            {name: source_snapshot},
            {name: None},
            state,
            timeshift_ops=_UnusedTimeshiftOps(),
            timeshift_inventory=inventory,
        )
        self.assertEqual(common, name)
        self.assertIn("exact state/Btrfs UUID proof", reason)
        self.assertIn("authoritative", reason)

    def test_os_identity_matching_ignores_distro_text(self) -> None:
        self.assertTrue(
            _same_os_identity(
                TimeshiftOsIdentity("same-root", "btrfs", "Ubuntu 24.04"),
                TimeshiftOsIdentity("same-root", "btrfs", "Ubuntu 26.04"),
            )
        )
        self.assertFalse(
            _same_os_identity(
                TimeshiftOsIdentity("root-a", "btrfs", None),
                TimeshiftOsIdentity("root-b", "btrfs", None),
            )
        )

    def test_privileged_physical_scanner_prefixes_individual_read_only_commands(self) -> None:
        endpoint = _CapturingEndpoint()
        records = _scan_snapshot_directories(
            endpoint,
            "/timeshift/snapshots",
            location_label="test endpoint",
            privilege_prefix=["sudo", "-n"],
        )
        self.assertEqual(records, {})
        script = endpoint.script
        self.assertIn('run_privileged test -d "$root"', script)
        self.assertIn('run_privileged ls -1A -- "$root"', script)
        self.assertIn('run_privileged base64 -w 0 -- "$info_path"', script)
        self.assertNotIn("sudo -n sh", script)
        self.assertNotIn("sudo -n bash", script)


if __name__ == "__main__":
    unittest.main()
