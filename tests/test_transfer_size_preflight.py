from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from timeshift_btrfs_sync.btrfs_ops import BtrfsOps
from timeshift_btrfs_sync.endpoint import CommandEndpoint
from timeshift_btrfs_sync.commands import Completed
from timeshift_btrfs_sync.config import ConfigError, load_config
from timeshift_btrfs_sync.sync import SyncError, _transfer_size_preflight
from timeshift_btrfs_sync.transfer_size import TransferSizeMeasurement
from timeshift_btrfs_sync.transfer_size import (
    TransferSizeError,
    destination_free_bytes,
    estimated_send_stream_size,
    exact_send_stream_size,
    parse_estimate_changed_bytes,
    parse_btrfs_usage_free_bytes,
    parse_size_bytes,
)


class TransferSizeParsingTests(unittest.TestCase):
    def test_size_parser_uses_binary_suffixes(self) -> None:
        self.assertEqual(parse_size_bytes("1G"), 1024**3)
        self.assertEqual(parse_size_bytes("512M"), 512 * 1024**2)
        self.assertEqual(parse_size_bytes("1.5G"), 1536 * 1024**2)
        self.assertEqual(parse_size_bytes("4096"), 4096)

    def test_btrfs_usage_prefers_minimum_free_estimate(self) -> None:
        output = """Overall:\n    Free (estimated):             9000000 (min: 7000000)\n"""
        self.assertEqual(parse_btrfs_usage_free_bytes(output), 7000000)

    def test_estimate_summary_parser_reads_ascii_marker(self) -> None:
        self.assertEqual(
            parse_estimate_changed_bytes("TSBTRFS_ESTIMATE_CHANGED_BYTES=12288\n"),
            12288,
        )

    def test_estimate_summary_parser_requires_marker(self) -> None:
        with self.assertRaisesRegex(TransferSizeError, "summary marker"):
            parse_estimate_changed_bytes("update_extent path=file-a size=4096\n")


class ExactTransferMeasurementTests(unittest.TestCase):
    def _ops(self, completed: Completed) -> tuple[BtrfsOps, Mock]:
        endpoint = Mock()
        endpoint.run_shell.return_value = completed
        ops = BtrfsOps(endpoint, "sudo -n", "btrfs")
        return ops, endpoint

    def test_exact_measurement_counts_on_source_endpoint_with_real_send_options(self) -> None:
        completed = Completed(
            0,
            stdout="6825172992\n",
            stderr="At subvol /cache/current\nTSBTRFS_SEND_SIZE_RC=0\n",
        )
        ops, endpoint = self._ops(completed)
        result = exact_send_stream_size(
            ops,
            "/cache/current",
            parent_path="/cache/parent",
            compressed_data=True,
            proto=2,
        )
        self.assertEqual(result.size_bytes, 6825172992)
        script = endpoint.run_shell.call_args.args[0]
        self.assertIn("sudo -n btrfs send", script)
        self.assertIn("--proto 2", script)
        self.assertIn("--compressed-data", script)
        self.assertIn("-p /cache/parent /cache/current", script)
        self.assertIn("| wc -c", script)

    def test_exact_measurement_does_not_hide_failed_btrfs_send_behind_wc(self) -> None:
        completed = Completed(
            0,
            stdout="0\n",
            stderr="ERROR: parent vanished\nTSBTRFS_SEND_SIZE_RC=1\n",
        )
        ops, _endpoint = self._ops(completed)
        with self.assertRaisesRegex(TransferSizeError, "parent vanished"):
            exact_send_stream_size(ops, "/cache/current", parent_path="/cache/parent")


class EstimatedTransferMeasurementTests(unittest.TestCase):
    def _ops(self, completed: Completed) -> tuple[BtrfsOps, Mock]:
        endpoint = Mock()
        endpoint.run_shell.return_value = completed
        ops = BtrfsOps(endpoint, "sudo -n", "btrfs")
        return ops, endpoint

    def test_incremental_estimate_uses_parent_specific_no_data_send(self) -> None:
        completed = Completed(
            0,
            stdout="TSBTRFS_ESTIMATE_CHANGED_BYTES=5368709120\n",
            stderr=(
                "At subvol /cache/current\n"
                "TSBTRFS_ESTIMATE_SEND_RC=0\n"
                "TSBTRFS_ESTIMATE_DUMP_RC=0\n"
            ),
        )
        ops, endpoint = self._ops(completed)
        result = estimated_send_stream_size(
            ops,
            "/cache/current",
            parent_path="/cache/parent",
            compressed_data=True,
            proto=2,
        )
        self.assertEqual(result.size_bytes, 5 * 1024**3)
        self.assertIn("parent-specific changed extent bytes", result.basis)
        script = endpoint.run_shell.call_args.args[0]
        self.assertIn("btrfs send --no-data", script)
        self.assertIn("--proto 2", script)
        self.assertIn("--compressed-data", script)
        self.assertIn("-p /cache/parent /cache/current", script)
        self.assertIn("btrfs receive --dump", script)
        self.assertIn("LC_ALL=C awk", script)
        self.assertIn("TSBTRFS_ESTIMATE_CHANGED_BYTES", script)

    def test_estimate_does_not_use_subvolume_exclusive_bytes(self) -> None:
        completed = Completed(
            0,
            stdout="TSBTRFS_ESTIMATE_CHANGED_BYTES=6442450944\n",
            stderr="TSBTRFS_ESTIMATE_SEND_RC=0\nTSBTRFS_ESTIMATE_DUMP_RC=0\n",
        )
        ops, _endpoint = self._ops(completed)
        result = estimated_send_stream_size(ops, "/cache/current", parent_path="/cache/parent")
        self.assertEqual(result.size_bytes, 6 * 1024**3)
        ops.endpoint.run_shell.assert_called_once()

    def test_estimate_does_not_hide_failed_send_behind_dump(self) -> None:
        completed = Completed(
            0,
            stdout="TSBTRFS_ESTIMATE_CHANGED_BYTES=0\n",
            stderr=(
                "ERROR: parent vanished\n"
                "TSBTRFS_ESTIMATE_SEND_RC=1\n"
                "TSBTRFS_ESTIMATE_DUMP_RC=0\n"
            ),
        )
        ops, _endpoint = self._ops(completed)
        with self.assertRaisesRegex(TransferSizeError, "parent vanished"):
            estimated_send_stream_size(ops, "/cache/current", parent_path="/cache/parent")


    def test_estimate_reduces_non_utf8_stream_before_python_capture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "fake-btrfs"
            fake.write_text(
                "#!/usr/bin/env python3\n"
                "import os, sys\n"
                "if len(sys.argv) > 1 and sys.argv[1] == 'send':\n"
                "    os.write(1, b'\\x00\\xad\\xffBTRFS_BINARY\\x80')\n"
                "    raise SystemExit(0)\n"
                "if len(sys.argv) > 2 and sys.argv[1:3] == ['receive', '--dump']:\n"
                "    sys.stdin.buffer.read()\n"
                "    print('update_extent path=file file_offset=0 size=4096')\n"
                "    print('update_extent path=file file_offset=4096 size=8192')\n"
                "    raise SystemExit(0)\n"
                "raise SystemExit(2)\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            ops = BtrfsOps(CommandEndpoint.local("test-source"), "", str(fake))
            result = estimated_send_stream_size(
                ops,
                "/cache/current",
                parent_path="/cache/parent",
            )
        self.assertEqual(result.size_bytes, 12288)

    def test_estimate_detects_failed_dump_stage(self) -> None:
        completed = Completed(
            0,
            stdout="",
            stderr=(
                "dump failed\n"
                "TSBTRFS_ESTIMATE_SEND_RC=0\n"
                "TSBTRFS_ESTIMATE_DUMP_RC=1\n"
            ),
        )
        ops, _endpoint = self._ops(completed)
        with self.assertRaisesRegex(TransferSizeError, "dump failed"):
            estimated_send_stream_size(ops, "/cache/current", parent_path="/cache/parent")

    def test_destination_free_space_uses_btrfs_estimated_lower_bound(self) -> None:
        ops = Mock()
        ops.run.return_value = Completed(
            0,
            "Overall:\n    Free (estimated): 9000000 (min: 7000000)\n",
            "",
        )
        self.assertEqual(destination_free_bytes(ops, Path("/backup")), 7000000)


class TransferSizeConfigTests(unittest.TestCase):
    def _base_config(self) -> str:
        return """
name = "test"
[restore]
mode = "local"
[source]
mode = "local"
snapshot_root = "/snapshots"
[destination]
target_root = "/backup"
[stream]
transfer_size_check = true
transfer_size_mode = "exact"
transfer_size_safety_margin = "1G"
"""

    def test_requested_transfer_size_options_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.toml"
            path.write_text(self._base_config())
            config = load_config(path)
        self.assertTrue(config.stream.transfer_size_check)
        self.assertEqual(config.stream.transfer_size_mode, "exact")
        self.assertEqual(config.stream.transfer_size_safety_margin, "1G")

    def test_transfer_size_defaults_are_disabled_and_estimate(self) -> None:
        minimal = """
name = "test"
[restore]
mode = "local"
[source]
mode = "local"
snapshot_root = "/snapshots"
[destination]
target_root = "/backup"
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.toml"
            path.write_text(minimal)
            config = load_config(path)
        self.assertFalse(config.stream.transfer_size_check)
        self.assertEqual(config.stream.transfer_size_mode, "estimate")
        self.assertEqual(config.stream.transfer_size_safety_margin, "1G")

    def test_invalid_mode_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.toml"
            path.write_text(self._base_config().replace('"exact"', '"guess"'))
            with self.assertRaisesRegex(ConfigError, "transfer_size_mode"):
                load_config(path)

    def test_invalid_margin_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.toml"
            path.write_text(self._base_config().replace('"1G"', '"lots"'))
            with self.assertRaisesRegex(ConfigError, "transfer_size_safety_margin"):
                load_config(path)


class SyncCapacityGateTests(unittest.TestCase):
    def _config(self, margin: str = "1G"):
        return SimpleNamespace(
            stream=SimpleNamespace(
                transfer_size_check=True,
                transfer_size_mode="exact",
                transfer_size_safety_margin=margin,
            ),
            source=SimpleNamespace(send_compressed_data=True, send_proto=2),
            destination=SimpleNamespace(target_root=Path("/backup")),
        )

    def test_capacity_gate_allows_stream_plus_margin_that_fits(self) -> None:
        with (
            patch(
                "timeshift_btrfs_sync.sync.exact_send_stream_size",
                return_value=TransferSizeMeasurement(2 * 1024**3, "exact", "test exact stream"),
            ),
            patch(
                "timeshift_btrfs_sync.sync.destination_free_bytes",
                return_value=4 * 1024**3,
            ),
        ):
            _transfer_size_preflight(
                self._config(),
                Mock(),
                Mock(),
                snapshot_name="2026-09-11_09-00-00",
                subvolume_name="@",
                current_path="/cache/current/@",
                parent_path="/cache/parent/@",
            )

    def test_capacity_gate_refuses_before_receive_when_stream_plus_margin_does_not_fit(self) -> None:
        with (
            patch(
                "timeshift_btrfs_sync.sync.exact_send_stream_size",
                return_value=TransferSizeMeasurement(4 * 1024**3, "exact", "test exact stream"),
            ),
            patch(
                "timeshift_btrfs_sync.sync.destination_free_bytes",
                return_value=4 * 1024**3,
            ),
        ):
            with self.assertRaisesRegex(SyncError, "Shortfall"):
                _transfer_size_preflight(
                    self._config(),
                    Mock(),
                    Mock(),
                    snapshot_name="2026-09-11_09-00-00",
                    subvolume_name="@",
                    current_path="/cache/current/@",
                    parent_path="/cache/parent/@",
                )

    def test_estimate_capacity_gate_refuses_when_changed_extents_plus_margin_do_not_fit(self) -> None:
        config = self._config()
        config.stream.transfer_size_mode = "estimate"
        with (
            patch(
                "timeshift_btrfs_sync.sync.estimated_send_stream_size",
                return_value=TransferSizeMeasurement(6 * 1024**3, "estimate", "metadata-only changed extents"),
            ),
            patch(
                "timeshift_btrfs_sync.sync.destination_free_bytes",
                return_value=6 * 1024**3,
            ),
        ):
            with self.assertRaisesRegex(SyncError, "Shortfall"):
                _transfer_size_preflight(
                    config,
                    Mock(),
                    Mock(),
                    snapshot_name="2026-09-11_09-00-00",
                    subvolume_name="@",
                    current_path="/cache/current/@",
                    parent_path="/cache/parent/@",
                )


if __name__ == "__main__":
    unittest.main()
