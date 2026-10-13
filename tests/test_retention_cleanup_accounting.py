"""Verify each retention side is counted without changing deletion safety."""
from contextlib import redirect_stdout
from io import StringIO
from types import SimpleNamespace
from unittest import TestCase, mock

from timeshift_btrfs_sync import retention
from timeshift_btrfs_sync.cli import _format_cleanup_summary
from timeshift_btrfs_sync.state import SEND_PATH_KIND_TIMESHIFT_ORIGINAL_READONLY
from test_manual_snapshot_retention import _config, _name, _source_snapshot, _state


class RetentionCleanupAccountingTests(TestCase):
    def _execute(self, *, destination_ok=True, cache_ok=True, cache_enabled=True, direct=False):
        """Reuse existing fixtures and mocked deletion endpoints for one date."""
        config = _config(cleanup_enabled=False)
        config.source.cleanup_superseded_cache = cache_enabled
        name = _name(1)
        state = _state([name])
        if direct:
            for subvol, item in state["snapshots"][name]["subvolumes"].items():
                item["send_path_kind"] = SEND_PATH_KIND_TIMESHIFT_ORIGINAL_READONLY
                item["send_path"] = f"{name}/{subvol}"
        result = retention.PruneResult(
            plan=retention.PrunePlan(delete={name}), dry_run=False,
            cache_cleanup_enabled=cache_enabled,
            cache_delete_candidates=int(cache_enabled and not direct),
        )
        with (
            redirect_stdout(StringIO()),
            mock.patch.object(retention, "_delete_destination_snapshot_for_prune", return_value=destination_ok) as dest,
            mock.patch.object(retention, "_cleanup_source_cache_for_pruned_snapshot", return_value=cache_ok) as cache,
        ):
            ok = retention._delete_prune_item(
                config, state, result.plan, SimpleNamespace(), None, set(), name,
                cleanup_result=result,
            )
        return result, state, ok, dest, cache

    def test_two_payload_subvolumes_count_as_one_snapshot_date_per_side(self):
        result, state, ok, _dest, _cache = self._execute()
        self.assertTrue(ok)
        self.assertEqual(state["snapshots"], {})
        self.assertEqual((result.destination_cleanup_attempted, result.destination_cleanup_completed), (1, 1))
        self.assertEqual((result.cache_cleanup_attempted, result.cache_cleanup_completed), (1, 1))
        self.assertEqual(result.source_timeshift_cleanup_completed, 0)

    def test_cache_failure_preserves_destination_success_and_state_for_retry(self):
        result, state, ok, _dest, _cache = self._execute(cache_ok=False)
        self.assertFalse(ok)
        self.assertIn(_name(1), state["snapshots"])
        self.assertEqual(result.destination_cleanup_completed, 1)
        self.assertEqual((result.cache_cleanup_attempted, result.cache_cleanup_completed), (1, 0))
        text = retention.format_prune_cleanup_summaries(result)
        dest, cache = text.split("SOURCE SEND-CACHE CLEANUP SUMMARY")
        self.assertIn("confirmed gone:     1", dest)
        self.assertIn("confirmed gone:     0", cache)
        self.assertIn("pending/skipped:    1", cache)

    def test_destination_failure_does_not_attempt_cache_cleanup(self):
        result, _state_doc, ok, _dest, cache = self._execute(destination_ok=False)
        self.assertFalse(ok)
        self.assertEqual((result.destination_cleanup_attempted, result.destination_cleanup_completed), (1, 0))
        self.assertEqual((result.cache_cleanup_attempted, result.cache_cleanup_completed), (0, 0))
        cache.assert_not_called()

    def test_disabled_cache_is_not_counted_or_deleted(self):
        result, _state_doc, ok, _dest, cache = self._execute(cache_enabled=False)
        self.assertTrue(ok)
        cache.assert_not_called()
        self.assertEqual(result.cache_cleanup_completed, 0)
        text = retention.format_prune_cleanup_summaries(result).split("SOURCE SEND-CACHE CLEANUP SUMMARY")[1]
        self.assertIn("disabled; source send-cache left unchanged", text)
        self.assertIn("candidates:         0", text)

    def test_direct_timeshift_send_is_not_counted_as_a_cache_snapshot(self):
        result, _state_doc, ok, _dest, _cache = self._execute(direct=True)
        self.assertTrue(ok)
        self.assertEqual(result.destination_cleanup_completed, 1)
        self.assertEqual((result.cache_cleanup_attempted, result.cache_cleanup_completed), (0, 0))

    def test_blocked_source_authorization_keeps_both_sides_untouched(self):
        config = _config(cleanup_enabled=True)
        name = _name(1)
        state = _state([name])
        result = retention.PruneResult(plan=retention.PrunePlan(delete={name}), dry_run=False)
        with (
            redirect_stdout(StringIO()),
            mock.patch.object(retention, "_delete_destination_snapshot_for_prune") as dest,
            mock.patch.object(retention, "_cleanup_source_cache_for_pruned_snapshot") as cache,
        ):
            ok = retention._delete_prune_item(
                config, state, result.plan, SimpleNamespace(), {name: _source_snapshot(1)}, set(), name,
                cleanup_result=result,
            )
        self.assertFalse(ok)
        dest.assert_not_called()
        cache.assert_not_called()
        self.assertEqual(result.destination_cleanup_attempted, 0)
        self.assertEqual(result.cache_cleanup_attempted, 0)

    def test_prune_returns_side_counts_when_cache_failure_prevents_state_removal(self):
        config = _config(cleanup_enabled=False)
        state = _state([_name(1)])
        plan = retention.PrunePlan(delete={_name(1)})
        with (
            redirect_stdout(StringIO()),
            mock.patch.object(retention, "build_prune_plan", return_value=plan),
            mock.patch.object(retention, "save_state"),
            mock.patch.object(retention.SourceRunner, "from_config", return_value=SimpleNamespace()),
            mock.patch.object(retention.inventory, "build_source_btrfs_index", return_value=None),
            mock.patch.object(retention, "_delete_destination_snapshot_for_prune", return_value=True),
            mock.patch.object(retention, "_cleanup_source_cache_for_pruned_snapshot", return_value=False),
        ):
            result = retention.prune(config, state, dry_run=False, yes_delete=True)
        self.assertEqual(result.destination_cleanup_completed, 1)
        self.assertEqual(result.cache_delete_candidates, 1)
        self.assertEqual(result.cache_cleanup_completed, 0)
        self.assertEqual(result.destination_state_deleted, 0)
        self.assertEqual(result.remaining_state, 1)

    def test_dry_run_uses_candidates_and_never_claims_real_deletion(self):
        config = _config(cleanup_enabled=False)
        state = _state([_name(1)])
        plan = retention.PrunePlan(delete={_name(1)})
        with (
            redirect_stdout(StringIO()),
            mock.patch.object(retention, "build_prune_plan", return_value=plan),
            mock.patch.object(retention, "_delete_destination_snapshot_for_prune") as dest,
            mock.patch.object(retention, "_cleanup_source_cache_for_pruned_snapshot") as cache,
        ):
            result = retention.prune(config, state, dry_run=True, yes_delete=False)
        dest.assert_not_called()
        cache.assert_not_called()
        self.assertEqual(result.cache_delete_candidates, 1)
        text = retention.format_prune_cleanup_summaries(result)
        self.assertEqual(text.count("confirmed gone:     0"), 2)
        self.assertEqual(text.count("dry-run only; no deletion performed"), 2)

    def test_missing_result_labels_both_sides_unknown_instead_of_zero(self):
        text = _format_cleanup_summary(None, requested=True, dry_run=False, error=RuntimeError("prune failed"))
        self.assertEqual(text.count("confirmed gone:     unknown"), 2)
        self.assertIn("prune failed", text)

    def test_not_requested_still_has_both_side_summaries(self):
        text = _format_cleanup_summary(None, requested=False, dry_run=False)
        self.assertIn("DESTINATION CLEANUP SUMMARY", text)
        self.assertIn("SOURCE SEND-CACHE CLEANUP SUMMARY", text)
        self.assertEqual(text.count("confirmed gone:     0"), 2)

    def test_original_timeshift_cleanup_is_labeled_separately_from_cache(self):
        result = retention.PruneResult(plan=retention.PrunePlan(), dry_run=False, source_timeshift_cleanup_completed=2)
        text = _format_cleanup_summary(result, requested=True, dry_run=False)
        self.assertIn("Timeshift app confirmed gone:     2", text)
        self.assertIn("ordinary source snapshots: retention managed by Timeshift", text)

    def test_source_app_success_is_counted_before_later_destination_failure(self):
        config = _config(cleanup_enabled=True)
        config.source.cleanup_superseded_cache = False
        name = _name(1)
        state = _state([name])
        result = retention.PruneResult(plan=retention.PrunePlan(delete={name}), dry_run=False)
        with (
            redirect_stdout(StringIO()),
            mock.patch.object(retention, "_delete_source_timeshift_snapshot_for_prune", return_value=True),
            mock.patch.object(retention, "_delete_destination_snapshot_for_prune", return_value=False),
        ):
            ok = retention._delete_prune_item(
                config, state, result.plan, SimpleNamespace(), {name: _source_snapshot(1)}, {name}, name,
                cleanup_result=result,
            )
        self.assertFalse(ok)
        self.assertEqual(result.source_timeshift_cleanup_completed, 1)
        self.assertEqual(result.destination_cleanup_completed, 0)
        self.assertIn(name, state["snapshots"])
