"""Exercise dynamic cleanup accounting through real planning and guarded mock deletes."""
from contextlib import contextmanager, redirect_stdout
from copy import deepcopy
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch

from timeshift_btrfs_sync import cli, inventory, monitor, reconciliation, retention
from timeshift_btrfs_sync.models import SnapshotMeta, SubvolumeMeta
from test_manual_snapshot_retention import _config, _name, _source_snapshot, _state


@contextmanager
def tracked(config=None, *, operation="sync", cleanup=True):
    """Run the actual monitor lifecycle with networking disabled at its worker boundary."""
    config = config or _config(cleanup_enabled=False)
    live = monitor.LiveMonitor(config, "/jobs/progress.toml")
    with patch.object(live, "_start_worker"), live:
        monitor.configure_run(cleanup=cleanup, operation=operation)
        yield live


def plan_groups(progress, paired=(), source=(), cache=(), destination=(), *, estimated=False):
    """Supply one complete inventory generation to all four cleanup groups."""
    for group, names in zip(progress.GROUPS, (paired, source, cache, destination)):
        progress.plan(group, names, estimated=estimated)


class CleanupModelTests(unittest.TestCase):
    """Prevent shrinking, growing and incomplete plans from falsifying success."""

    def test_requested_starts_unknown_and_disabled_is_zero(self):
        """Distinguish absent cleanup from inventory that has not been read yet."""
        p = monitor.CleanupProgress(); self.assertEqual(p.view()["cleanup_total"], 0)
        p.configure(True); self.assertIsNone(p.view()["cleanup_total"])
        self.assertEqual(p.view()["cleanup_status"], "planning")

    def test_completed_history_survives_shrink_and_growth(self):
        """Retain completed jobs when new inventory replaces only pending work."""
        p = monitor.CleanupProgress(); p.configure(True)
        plan_groups(p, paired=["a", "b", "c"], estimated=True)
        self.assertEqual(p.view()["cleanup_initial_total"], 3)
        p.complete("paired", "a", True)
        p.plan("paired", ["b"])
        self.assertEqual((p.view()["cleanup_completed"], p.view()["cleanup_total"]), (1, 2))
        p.plan("paired", ["b", "d", "e"])
        self.assertEqual(p.view()["cleanup_total"], 4)
        self.assertEqual(p.view()["cleanup_initial_total"], 3)

    def test_repeated_plans_and_completion_do_not_double_count(self):
        """Two payloads/sides and repeated observer updates still complete one date job."""
        p = monitor.CleanupProgress(); p.configure(True); plan_groups(p, paired=["a", "a"])
        p.complete("paired", "a", True); p.complete("paired", "a", True)
        p.plan("paired", ["a"]); p.finish()
        self.assertEqual((p.view()["cleanup_completed"], p.view()["cleanup_total"]), (1, 1))
        self.assertEqual(p.view()["cleanup_status"], "complete")

    def test_same_date_in_distinct_cleanup_groups_is_distinct_work(self):
        """Per-side leftovers retain their identities independently of a paired job."""
        p = monitor.CleanupProgress(); p.configure(True)
        plan_groups(p, paired=["a"], cache=["a"])
        p.complete("paired", "a", True)
        self.assertEqual((p.view()["cleanup_completed"], p.view()["cleanup_total"]), (1, 2))

    def test_blocked_work_remains_pending_and_later_success_clears_it(self):
        """Evaluated/refused is not confirmed deleted and cannot finish the bar."""
        p = monitor.CleanupProgress(); p.configure(True); plan_groups(p, paired=["a", "b"])
        p.current("paired", "a"); p.complete("paired", "a", False); p.finish()
        self.assertEqual(p.view()["cleanup_status"], "incomplete")
        self.assertEqual((p.view()["cleanup_processed"], p.view()["cleanup_blocked"], p.view()["cleanup_remaining"]), (1, 1, 2))
        p.complete("paired", "a", True)
        self.assertEqual(p.view()["cleanup_blocked"], 0)

    def test_current_number_advances_after_completed_and_blocked_dates(self):
        """Show which evaluated item has been reached without counting it as deleted."""
        p = monitor.CleanupProgress(); p.configure(True); plan_groups(p, paired=["a", "b", "c"])
        p.complete("paired", "a", True); p.complete("paired", "b", False); p.current("paired", "c")
        self.assertEqual(p.view()["cleanup_current_number"], 3)
        self.assertEqual(p.view()["cleanup_completed"], 1)

    def test_unverified_inventory_and_leftover_estimates_stay_unverified(self):
        """Never convert an unread stage or a forecast into a confirmed empty plan."""
        for names, estimated in [(None, False), ([], True)]:
            with self.subTest(names=names, estimated=estimated):
                p = monitor.CleanupProgress(); p.configure(True); plan_groups(p)
                p.plan("cache", names, estimated=estimated); p.finish()
                self.assertEqual(p.view()["cleanup_status"], "unverified")

    def test_authoritative_plan_clears_estimate_and_obsolete_blocked_work(self):
        """A fresh plan may remove ineligible pending dates while retaining successes."""
        p = monitor.CleanupProgress(); p.configure(True); plan_groups(p, paired=["a", "b"], estimated=True)
        p.complete("paired", "a", False); plan_groups(p, paired=["b"])
        self.assertEqual(p.view()["cleanup_blocked"], 0)
        self.assertFalse(p.view()["cleanup_plan_estimated"])
        self.assertTrue(p.view()["cleanup_initial_plan_estimated"])

    def test_broken_observer_does_not_block_cleanup_accounting(self):
        """Monitoring errors remain isolated from guarded deletion work."""
        p = monitor.CleanupProgress(observer=Mock(side_effect=RuntimeError("offline")))
        p.configure(True); plan_groups(p, paired=["a"]); p.complete("paired", "a", True)
        self.assertEqual(p.view()["cleanup_completed"], 1)


class ForecastTests(unittest.TestCase):
    """Reuse retention and repository selectors without extra probes or state writes."""

    def setUp(self):
        """Model two daily backups and a future daily send under one-day retention."""
        self.config = _config(cleanup_enabled=False)
        self.config.retention.daily = 1
        self.state = _state([_name(1), _name(2)])
        for item in self.state["snapshots"].values(): item.update(tags=["D"], comment="daily")
        self.source = {name: SnapshotMeta(name, "/source/"+name, tags=["D"], comment="daily") for name in [_name(1), _name(2), _name(3)]}
        self.cache = inventory.BtrfsIndex(self.config.source.cache_root, "local")
        self.target = inventory.BtrfsIndex(str(self.config.destination.target_root / "snapshots"), "local")

    def test_project_pending_transfers_without_mutating_state_or_reading_disk(self):
        """An upcoming newest date changes expected retention before it is sent."""
        before = deepcopy(self.state)
        with tracked(self.config) as live, patch.object(retention, "save_state") as save, patch.object(retention, "_confirmed_prune_parent") as probe:
            retention.forecast_cleanup(self.config, self.state, self.source, self.cache, self.target, [_name(3)])
            self.assertEqual(live.payload()["cleanup_total"], 2)
            self.assertTrue(live.payload()["cleanup_plan_estimated"])
            probe.assert_not_called(); save.assert_not_called()
        self.assertEqual(self.state, before)

    def test_tag_change_replans_existing_dates_from_current_metadata(self):
        """Refresh retention tags of already stored dates in the disposable projection."""
        with tracked(self.config) as live:
            retention.forecast_cleanup(self.config, self.state, self.source, self.cache, self.target, [])
            self.assertEqual(live.payload()["cleanup_total"], 1)
            self.source[_name(1)].tags = ["O"]
            retention.forecast_cleanup(self.config, self.state, self.source, self.cache, self.target, [])
            self.assertEqual(live.payload()["cleanup_total"], 0)
            self.assertEqual(live.payload()["cleanup_initial_total"], 1)

    def test_source_disappearance_changes_forecast_for_pending_sends(self):
        """An unsent future date disappearing can shrink the initial cleanup estimate."""
        with tracked(self.config) as live:
            retention.forecast_cleanup(self.config, self.state, self.source, self.cache, self.target, [_name(3)])
            self.source.pop(_name(3))
            retention.forecast_cleanup(self.config, self.state, self.source, self.cache, self.target, [])
            self.assertEqual((live.payload()["cleanup_initial_total"], live.payload()["cleanup_total"]), (2, 1))

    def test_disabled_cleanup_never_invokes_planner(self):
        """No new inventory or planning is added to runs without requested monitoring/cleanup."""
        with tracked(self.config, cleanup=False), patch.object(retention, "build_prune_plan") as planner:
            retention.forecast_cleanup(self.config, self.state, self.source, self.cache, self.target, [])
            planner.assert_not_called()

    def test_failed_forecast_is_unknown_and_does_not_fail_backup(self):
        """Optional planning errors cannot authorize or interrupt the actual workflow."""
        with tracked(self.config) as live, patch.object(retention, "build_prune_plan", side_effect=RuntimeError("inventory changed")):
            retention.forecast_cleanup(self.config, self.state, self.source, self.cache, self.target, [])
            self.assertIsNone(live.payload()["cleanup_total"])

    def test_extra_estimate_reuses_selectors_and_avoids_paired_double_count(self):
        """Existing cache-only and receiver-only dates contribute separate date jobs."""
        self.config.source.delete_redundant_snapshots = True
        self.config.destination.delete_redundant_snapshots = True
        # day 1 will be handled by paired retention; day 0 is only in the cache.
        cache_only = "2026-08-31_01-00-00"
        target_only = "2026-08-30_01-00-00"
        for name in [_name(1), cache_only]:
            path = self.cache.root + "/" + name + "/@"
            self.cache.add(SubvolumeMeta("@", path))
        self.target.add(SubvolumeMeta("@", self.target.root + "/" + target_only + "/@"))
        with tracked(self.config) as live:
            retention.forecast_cleanup(self.config, self.state, self.source, self.cache, self.target, [])
            groups = live.payload()["cleanup_groups"]
            self.assertEqual([groups[k]["total"] for k in ["paired", "cache", "destination"]], [1, 1, 1])
            self.assertEqual(live.payload()["cleanup_total"], 3)


class CleanupLifecycleTests(unittest.TestCase):
    """Connect real prune decisions and final monitor outcomes through isolated boundaries."""

    def test_overall_combines_both_dynamic_plans_and_keeps_completed_history(self):
        """Changing either denominator updates the same combined total immediately."""
        with tracked() as live:
            p = monitor.SnapshotProgress(); p.replan(["a", "b", "c"])
            plan_groups(live.cleanup, paired=["old1", "old2"], estimated=True)
            p.complete("a"); live.cleanup.complete("paired", "old1", True)
            self.assertEqual((live.payload()["overall_completed_steps"], live.payload()["overall_total_steps"]), (2, 5))
            p.replan(["b"]); plan_groups(live.cleanup, paired=["old3"])
            self.assertEqual((live.payload()["overall_completed_steps"], live.payload()["overall_total_steps"]), (2, 4))
            p.complete("b"); live.cleanup.complete("paired", "old3", True)
        self.assertEqual(live._result["status"], "success")
        self.assertEqual(live._result["overall_completed_steps"], live._result["overall_total_steps"])

    def test_unverified_cleanup_is_incomplete_even_after_all_transfers(self):
        """A normal CLI return cannot silently declare an unknown cleanup stage successful."""
        with tracked() as live:
            p = monitor.SnapshotProgress(); p.replan(["a"]); p.complete("a")
        self.assertEqual(live._result["status"], "incomplete")
        self.assertIsNone(live._result["overall_total_steps"])

    def test_prune_requires_yes_delete_and_never_uses_estimate_as_consent(self):
        """Live planning must leave the existing destructive authorization guard intact."""
        config = _config(cleanup_enabled=False)
        with tracked(config, operation="prune") as live, redirect_stdout(StringIO()), patch.object(retention, "build_prune_plan", return_value=retention.PrunePlan(delete={_name(1)})), patch.object(retention, "_delete_prune_item") as delete:
            with self.assertRaisesRegex(RuntimeError, "--yes-delete"):
                retention.prune(config, _state([_name(1)]), dry_run=False, yes_delete=False)
            delete.assert_not_called()
            self.assertEqual(live.payload()["cleanup_completed"], 0)

    def test_real_prune_reports_partial_paired_failure_and_retains_state(self):
        """A successful destination delete followed by failed cache cleanup completes no job."""
        config = _config(cleanup_enabled=False); state = _state([_name(1)])
        with tracked(config, operation="prune") as live, redirect_stdout(StringIO()), patch.object(retention, "build_prune_plan", return_value=retention.PrunePlan(delete={_name(1)})), patch.object(retention.SourceRunner, "from_config", return_value=SimpleNamespace()), patch.object(retention.inventory, "build_source_btrfs_index", return_value=None), patch.object(retention, "_delete_destination_snapshot_for_prune", return_value=True), patch.object(retention, "_cleanup_source_cache_for_pruned_snapshot", return_value=False), patch.object(retention, "save_state"):
            result = retention.prune(config, state, dry_run=False, yes_delete=True)
            self.assertEqual(result.destination_cleanup_completed, 1)
            self.assertEqual((live.payload()["cleanup_completed"], live.payload()["cleanup_blocked"]), (0, 1))
            self.assertIn(_name(1), state["snapshots"])
        self.assertEqual(live._result["status"], "incomplete")

    def test_real_prune_advances_after_required_sides_and_exposes_current_date(self):
        """The active item stays visible during deletion and completes only with state removal."""
        config = _config(cleanup_enabled=False); config.source.cleanup_superseded_cache = False
        state = _state([_name(1)])
        with tracked(config, operation="prune") as live:
            def destination(_config, name):
                """Inspect the active date while the original delete handler is running."""
                self.assertEqual(live.payload()["cleanup_current_snapshot"], name)
                self.assertEqual(live.payload()["cleanup_completed"], 0)
                return True
            with redirect_stdout(StringIO()), patch.object(retention, "build_prune_plan", return_value=retention.PrunePlan(delete={_name(1)})), patch.object(retention, "_delete_destination_snapshot_for_prune", side_effect=destination), patch.object(retention, "save_state"):
                retention.prune(config, state, dry_run=False, yes_delete=True)
            self.assertEqual(state["snapshots"], {})
            self.assertEqual((live.payload()["overall_completed_steps"], live.payload()["overall_total_steps"]), (1, 1))
        self.assertEqual(live._result["status"], "success")

    def test_interrupt_marks_current_cleanup_unconfirmed_without_transfer_failure(self):
        """Ctrl+C preserves partial cleanup progress and the existing exit 130 behavior."""
        with self.assertRaises(KeyboardInterrupt):
            with tracked(operation="prune") as live:
                plan_groups(live.cleanup, paired=["a"]); live.cleanup.current("paired", "a")
                raise KeyboardInterrupt
        self.assertEqual((live._result["status"], live._result["exit_code"]), ("interrupted", 130))
        self.assertEqual((live._result["cleanup_blocked"], live._result["failed_snapshots"]), (1, 0))

    def test_prune_cli_dry_run_does_not_activate_monitor(self):
        """Standalone prune keeps the original no-lock/no-live dry-run boundary."""
        config = _config(cleanup_enabled=False); config.mqtt_monitor.enabled = True
        args = SimpleNamespace(config="job.toml", run=False, dry_run=True, yes_delete=False)
        with patch.object(cli, "load_config", return_value=config), patch.object(cli, "_load_config_state", return_value=_state([])), patch.object(cli, "prune"), patch.object(cli, "_with_logging", side_effect=lambda c, command, fn: fn()), patch.object(cli, "LiveMonitor") as live, patch.object(cli, "FileLock") as lock, redirect_stdout(StringIO()):
            cli.cmd_prune(args)
        live.assert_not_called(); lock.assert_not_called()

    def test_legacy_source_progress_respects_current_backup_authorization(self):
        """Count only confirmed app-created source-only deletions; preserve blocked proof cases."""
        for authorized in [True, False]:
            with self.subTest(authorized=authorized):
                config = _config(cleanup_enabled=True, retention_count=1)
                index = {_name(day): _source_snapshot(day) for day in [1, 2]}
                with tracked(config, operation="prune") as live, redirect_stdout(StringIO()), patch.object(retention.SourceRunner, "from_config", return_value=SimpleNamespace()), patch.object(retention, "_load_source_timeshift_index", return_value=index), patch.object(retention.inventory, "build_local_btrfs_index", return_value=None), patch.object(retention, "_authorized_source_timeshift_delete_names", return_value=({_name(1)} if authorized else set(), authorized)), patch.object(retention, "_delete_source_timeshift_snapshot_for_prune", return_value=True) as delete, patch.object(retention, "save_state"):
                    result = retention.prune(config, _state([]), dry_run=False, yes_delete=True)
                    self.assertEqual(result.legacy_source_deleted, int(authorized))
                    self.assertEqual(live.payload()["cleanup_groups"]["source"]["total"], 1)
                    self.assertEqual(live.payload()["cleanup_completed"], int(authorized))
                    self.assertEqual(live.payload()["cleanup_blocked"], int(not authorized))
                    self.assertEqual(delete.call_count, int(authorized))

    def test_cleanup_start_replaces_old_estimate_before_first_delete(self):
        """Display a changed initial/current count at the first actual cleanup operation."""
        config = _config(cleanup_enabled=False); config.source.cleanup_superseded_cache = False
        state = _state([_name(1)])
        with tracked(config, operation="prune") as live:
            plan_groups(live.cleanup, paired=[_name(1), _name(2), _name(3)], estimated=True)
            def destination(_config, name):
                """Check the fresh plan while the first guarded delete is active."""
                metrics = live.payload()
                self.assertEqual((metrics["cleanup_initial_total"], metrics["cleanup_total"]), (3, 1))
                self.assertFalse(metrics["cleanup_plan_estimated"])
                return True
            with redirect_stdout(StringIO()), patch.object(retention, "build_prune_plan", return_value=retention.PrunePlan(delete={_name(1)})), patch.object(retention, "_delete_destination_snapshot_for_prune", side_effect=destination), patch.object(retention, "save_state"):
                retention.prune(config, state, dry_run=False, yes_delete=True)

    def test_prune_cli_live_metrics_only_start_while_lock_owned(self):
        """Standalone cleanup uses the same exclusive-lock ownership as real sync monitoring."""
        config = _config(cleanup_enabled=False); config.mqtt_monitor.enabled = True
        with tempfile.TemporaryDirectory() as tmp:
            config.lock_file = Path(tmp) / "lock"
            args = SimpleNamespace(config="job.toml", run=True, dry_run=False, yes_delete=True)
            observed = []
            def prune(*args, **kwargs):
                """Verify real flock exclusion at the actual prune command boundary."""
                contender = cli.FileLock(config.lock_file)
                try:
                    with self.assertRaises(BlockingIOError): contender.__enter__()
                finally:
                    if contender._fh: contender._fh.close()
                observed.append(monitor._ACTIVE.get().payload())
            with patch.object(cli, "load_config", return_value=config), patch.object(cli, "prepare_lock_path"), patch.object(cli, "prepare_destination_helper_paths"), patch.object(cli, "_load_config_state", return_value=_state([])), patch.object(cli, "prune", side_effect=prune), patch.object(cli, "_with_logging", side_effect=lambda c, command, fn: fn()), patch.object(monitor.LiveMonitor, "_start_worker"), redirect_stdout(StringIO()):
                cli.cmd_prune(args)
            self.assertEqual(observed[0]["operation"], "prune")
            self.assertEqual(observed[0]["total_snapshots"], 0)
            with cli.FileLock(config.lock_file): pass


class ExtraCleanupProgressTests(unittest.TestCase):
    """Reuse repository safety fixtures to observe actual one-sided cleanup paths."""

    def cache_fixture(self):
        """Prepare proven bounds and one untracked cache-only date in temporary storage."""
        from test_repository_reconciliation import RepositoryReconciliationTests
        fixture = RepositoryReconciliationTests(); fixture.setUp()
        self.addCleanup(fixture.doCleanups); fixture.add_window()
        fixture.config.source.delete_redundant_snapshots = True
        return fixture

    def destination_fixture(self):
        """Prepare a receiver-only date with the existing native-root proof fixtures."""
        from test_repository_reconciliation import DestinationReconciliationTests
        fixture = DestinationReconciliationTests(); fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.f.config.destination.delete_redundant_snapshots = True
        return fixture

    def test_cache_success_replaces_forecast_with_fresh_candidates(self):
        """Refresh a stale two-item estimate and count one confirmed real cache deletion."""
        fixture = self.cache_fixture()
        with tracked(fixture.config) as live:
            plan_groups(live.cleanup, cache=["old-estimate", "gone"], estimated=True)
            result, delete = fixture.cleanup()
            group = live.payload()["cleanup_groups"]["cache"]
            self.assertEqual((result.completed, group["completed"], group["total"]), (1, 1, 1))
            self.assertFalse(group["estimated"]); delete.assert_called_once()

    def test_cache_absence_race_is_blocked_and_never_completes(self):
        """A newly appearing receiver keeps the original race guard and remains unconfirmed."""
        fixture = self.cache_fixture()
        with tracked(fixture.config) as live:
            plan_groups(live.cleanup)
            result, delete = fixture.cleanup(absence=[True, False])
            self.assertEqual((result.completed, live.payload()["cleanup_completed"], live.payload()["cleanup_blocked"]), (0, 0, 1))
            delete.assert_not_called()

    def test_cache_delete_failure_retains_pending_job(self):
        """A failed shared tree deletion advances evaluated count but not completion."""
        fixture = self.cache_fixture()
        with tracked(fixture.config) as live:
            plan_groups(live.cleanup)
            fixture.cleanup(delete_success=False)
            self.assertEqual((live.payload()["cleanup_remaining"], live.payload()["cleanup_processed"]), (1, 1))

    def test_cache_incomplete_inventory_remains_unknown(self):
        """Fresh inventory errors replace stale estimates with unknown totals."""
        fixture = self.cache_fixture(); fixture.cache.errors.append("denied")
        with tracked(fixture.config) as live:
            plan_groups(live.cleanup, cache=["stale"], estimated=True)
            fixture.cleanup()
            self.assertIsNone(live.payload()["cleanup_groups"]["cache"]["total"])
            self.assertIsNone(live.payload()["overall_total_steps"])

    def test_standalone_extra_stage_keeps_successful_sync_guard(self):
        """Standalone prune reports no authorized extra work and performs no deletion."""
        fixture = self.cache_fixture()
        with tracked(fixture.config, operation="prune") as live:
            plan_groups(live.cleanup, cache=["stale"], estimated=True)
            result, delete = fixture.cleanup(successful_sync=False)
            self.assertIn("successful sync", result.skipped_reason)
            self.assertEqual(live.payload()["cleanup_groups"]["cache"]["total"], 0)
            delete.assert_not_called()

    def test_destination_success_and_failure_have_separate_confirmed_counts(self):
        """Receiver-only deletion uses its own group and counts only verified absence."""
        for success in [True, False]:
            with self.subTest(success=success):
                fixture = self.destination_fixture()
                with tracked(fixture.f.config) as live:
                    plan_groups(live.cleanup)
                    result, _ = fixture.cleanup(deleted=success)
                    self.assertEqual(result.completed, int(success))
                    self.assertEqual(live.payload()["cleanup_groups"]["destination"]["completed"], int(success))
                    self.assertEqual(live.payload()["cleanup_blocked"], int(not success))
