from __future__ import annotations

import sys
import unittest

from timeshift_btrfs_sync.commands import parse_mbuffer_transferred_bytes, stream_pipeline
from timeshift_btrfs_sync.sync import SyncRunSummary, format_sync_summary, format_transferred_bytes_total


class TransferAccountingTests(unittest.TestCase):
    def test_parse_mbuffer_final_summary(self) -> None:
        text = "summary: 6509 MiByte in  2min 57.6sec - average of 36.7 MiB/s\n"
        self.assertEqual(parse_mbuffer_transferred_bytes(text), 6509 * 1024 * 1024)

    def test_parse_mbuffer_progress_total_fallback(self) -> None:
        text = "in @ 48.5 MiB/s, out @ 47.9 MiB/s, 6509 MiB total, buffer 10% full\r"
        self.assertEqual(parse_mbuffer_transferred_bytes(text), 6509 * 1024 * 1024)


    def test_parse_mbuffer_multi_sender_summary(self) -> None:
        text = "summary: 2x 6.5 GiByte in 1min 2.0sec - average of 107 MiB/s\n"
        self.assertEqual(parse_mbuffer_transferred_bytes(text), int(round(6.5 * 1024**3)))

    def test_middle_process_runs_without_controlling_terminal_for_capture(self) -> None:
        left = [sys.executable, "-c", "import sys; sys.stdout.buffer.write(b'x' * 1024)"]
        middle = [
            sys.executable,
            "-c",
            (
                "import os,sys; data=sys.stdin.buffer.read(); "
                "sys.stdout.buffer.write(data); sys.stdout.buffer.flush(); "
                "is_new_session=(os.getsid(0)==os.getpid()); "
                "print('summary: 3 MiByte in 1sec - average of 3 MiB/s', file=sys.stderr) "
                "if is_new_session else None"
            ),
        ]
        right = [sys.executable, "-c", "import sys; sys.stdin.buffer.read()"]
        result = stream_pipeline(left, right, middle_cmd=middle, verbose=False)
        self.assertEqual(result.transferred_bytes, 3 * 1024 * 1024)

    def test_successful_pipeline_returns_mbuffer_byte_total(self) -> None:
        left = [sys.executable, "-c", "import sys; sys.stdout.buffer.write(b'x' * 1024)"]
        middle = [
            sys.executable,
            "-c",
            (
                "import sys; data=sys.stdin.buffer.read(); "
                "sys.stdout.buffer.write(data); sys.stdout.buffer.flush(); "
                "print('summary: 2 MiByte in 1sec - average of 2 MiB/s', file=sys.stderr)"
            ),
        ]
        right = [sys.executable, "-c", "import sys; sys.stdin.buffer.read()"]
        result = stream_pipeline(left, right, middle_cmd=middle, verbose=False)
        self.assertEqual(result.transferred_bytes, 2 * 1024 * 1024)

    def _summary(self, sizes: list[int | None]) -> SyncRunSummary:
        events = []
        for index, size in enumerate(sizes):
            events.append(
                {
                    "mode": "incremental",
                    "snapshot": f"snapshot-{index}",
                    "tags": "O",
                    "subvolume": "@",
                    "source": "/source/@",
                    "destination": "/backup/@",
                    "parent": "parent",
                    "parent_source": "/source/parent/@",
                    "status": "synced",
                    "transferred_bytes": size,
                    "transferred_bytes_source": "mbuffer" if size is not None else None,
                }
            )
        return SyncRunSummary(
            transferred=len(sizes),
            events=events,
            dry_run=False,
            skipped_by_floor=0,
            already_synced=0,
        )

    def test_sync_summary_sums_all_successful_transfer_bytes(self) -> None:
        summary = self._summary([600_000_000, 650_000_000])
        text = format_sync_summary(summary, elapsed_seconds=10)
        self.assertIn("total transferred: 1.25 GB", text)

    def test_sync_summary_uses_tb_when_large(self) -> None:
        self.assertEqual(format_transferred_bytes_total(2_500_000_000_000), "2.50 TB")

    def test_sync_summary_reports_unavailable_when_any_actual_size_is_unknown(self) -> None:
        text = format_sync_summary(self._summary([1_000_000_000, None]))
        self.assertIn("total transferred: unavailable", text)
        self.assertIn("missing for 1 of 2 transfer(s)", text)


if __name__ == "__main__":
    unittest.main()
