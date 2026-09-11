from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from timeshift_btrfs_sync.cli import _format_cleanup_summary
from timeshift_btrfs_sync.log import RunLogger, active_logger, emit_final_terminal_summary, stage_final_run_summary
from timeshift_btrfs_sync.retention import PrunePlan, PruneResult
from timeshift_btrfs_sync.sync import (
    SyncRunSummary,
    format_duration,
    format_sync_summary,
    format_transferred_snapshots,
)


class SyncCleanupSummaryTests(unittest.TestCase):
    def test_cleanup_summary_is_present_when_prune_not_requested(self) -> None:
        text = _format_cleanup_summary(None, requested=False, dry_run=False)
        self.assertIn("CLEANUP SUMMARY", text)
        self.assertIn("requested:          no", text)
        self.assertIn("cleaned snapshots:  0", text)
        self.assertIn("cleanup skipped; cleaned 0 snapshots", text)

    def test_cleanup_summary_reports_successful_zero_cleanup(self) -> None:
        result = PruneResult(
            plan=PrunePlan(),
            dry_run=False,
            remaining_state=7,
        )
        text = _format_cleanup_summary(result, requested=True, dry_run=False)
        self.assertIn("requested:          yes", text)
        self.assertIn("cleaned snapshots:       0", text)
        self.assertIn("SUCCESS - cleaned 0 snapshot(s)", text)

    def test_cleanup_summary_reports_dry_run_zero_deletions(self) -> None:
        result = PruneResult(
            plan=PrunePlan(delete={"2026-09-01_00-00-00"}),
            dry_run=True,
            source_delete_candidates=1,
            source_delete_authorized=1,
            remaining_state=10,
        )
        text = _format_cleanup_summary(result, requested=True, dry_run=True)
        self.assertIn("dry-run only; no snapshots deleted", text)
        self.assertIn("SUCCESS - cleaned 0 snapshots (dry-run)", text)

    def _sample_sync(self) -> SyncRunSummary:
        return SyncRunSummary(
            transferred=1,
            events=[
                {
                    "mode": "incremental",
                    "snapshot": "2026-09-11_12-00-00",
                    "tags": "O",
                    "subvolume": "@",
                    "source": "/source/cache/current/@",
                    "destination": "/backup/snapshots/current/@",
                    "parent": "2026-09-10_12-00-00",
                    "parent_source": "/source/cache/parent/@",
                    "status": "synced",
                }
            ],
            dry_run=False,
            skipped_by_floor=2,
            already_synced=3,
        )

    def test_final_terminal_log_order_is_transfers_sync_cleanup(self) -> None:
        sync = self._sample_sync()
        cleanup = PruneResult(plan=PrunePlan(), dry_run=False, remaining_state=3)
        transfers = format_transferred_snapshots(sync)
        sync_text = format_sync_summary(sync, elapsed_seconds=3661)
        cleanup_text = _format_cleanup_summary(cleanup, requested=True, dry_run=False)
        final_text = transfers + "\n\n" + sync_text + "\n\n" + cleanup_text + "\n"

        with tempfile.TemporaryDirectory() as tmp:
            logger = RunLogger(Path(tmp), "summary-contract")
            with active_logger(logger):
                print("ordinary work before final summary")
                stage_final_run_summary(final_text)
                emit_final_terminal_summary(final_text)

            log_text = logger.log_path.read_text(encoding="utf-8")
            success_text = logger.success_path.read_text(encoding="utf-8")
            self.assertTrue(log_text.rstrip().endswith(final_text.rstrip()))
            self.assertTrue(success_text.rstrip().endswith(final_text.rstrip()))
            self.assertLess(log_text.rfind("TRANSFERRED SNAPSHOTS"), log_text.rfind("SYNC SUMMARY"))
            self.assertLess(log_text.rfind("SYNC SUMMARY"), log_text.rfind("CLEANUP SUMMARY"))
            self.assertLess(success_text.rfind("TRANSFERRED SNAPSHOTS"), success_text.rfind("SYNC SUMMARY"))
            self.assertLess(success_text.rfind("SYNC SUMMARY"), success_text.rfind("CLEANUP SUMMARY"))

    def test_mail_success_text_replaces_intermediate_success_output_and_starts_with_name(self) -> None:
        sync = self._sample_sync()
        transfers = format_transferred_snapshots(sync)
        sync_text = format_sync_summary(sync, elapsed_seconds=65)
        cleanup_text = _format_cleanup_summary(None, requested=False, dry_run=False)
        terminal_text = transfers + "\n\n" + sync_text + "\n\n" + cleanup_text + "\n"
        mail_text = (
            "BACKUP RUN\n==========\n  name: Test Backup\n\n"
            + sync_text
            + "\n\n"
            + cleanup_text
            + "\n\n"
            + transfers
            + "\n"
        )

        with tempfile.TemporaryDirectory() as tmp:
            logger = RunLogger(Path(tmp), "mail-order")
            with active_logger(logger):
                logger.success_text("INTERMEDIATE RETENTION SUMMARY\n")
                stage_final_run_summary(terminal_text, success_text=mail_text)

            success_text = logger.success_path.read_text(encoding="utf-8")
            self.assertTrue(success_text.startswith("BACKUP RUN\n==========\n  name: Test Backup\n"))
            self.assertNotIn("INTERMEDIATE RETENTION SUMMARY", success_text)
            self.assertLess(success_text.index("SYNC SUMMARY"), success_text.index("CLEANUP SUMMARY"))
            self.assertLess(success_text.index("CLEANUP SUMMARY"), success_text.index("TRANSFERRED SNAPSHOTS"))
            self.assertIn("total backup time: 00:01:05", success_text)

    def test_sync_summary_includes_total_backup_time(self) -> None:
        text = format_sync_summary(self._sample_sync(), elapsed_seconds=3723.6)
        self.assertIn("total backup time: 01:02:04", text)

    def test_duration_supports_days(self) -> None:
        self.assertEqual(format_duration(90061), "1d 01:01:01")

    def test_transfer_section_explains_what_is_listed(self) -> None:
        text = format_transferred_snapshots(self._sample_sync())
        self.assertTrue(text.startswith("TRANSFERRED SNAPSHOTS"))
        self.assertIn("transferred successfully during this sync run", text)
        self.assertIn("2026-09-11_12-00-00", text)

    def test_failed_sync_summary_format_is_not_used_for_completed_sync(self) -> None:
        summary = SyncRunSummary(
            transferred=2,
            events=[],
            dry_run=False,
            skipped_by_floor=1,
            already_synced=4,
        )
        text = format_sync_summary(summary, elapsed_seconds=2)
        self.assertIn("SYNC SUMMARY", text)
        self.assertIn("transferred:       2", text)
        self.assertIn("total backup time:", text)
        self.assertNotIn("FAILED", text)


if __name__ == "__main__":
    unittest.main()
