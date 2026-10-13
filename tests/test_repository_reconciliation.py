"""State repair and bounded cache cleanup with actual ordinary files and simulated Btrfs."""

from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, mock
from contextlib import redirect_stdout
import io
import json

from timeshift_btrfs_sync import inventory, reconciliation, retention, sync
from timeshift_btrfs_sync.btrfs_ops import BtrfsOps
from timeshift_btrfs_sync.config import load_config, ConfigError
from timeshift_btrfs_sync.models import SnapshotMeta, SubvolumeMeta
from timeshift_btrfs_sync.restore import BackupDirectoryRecord
from timeshift_btrfs_sync.source import SourceRunner
from timeshift_btrfs_sync.state import empty_state, mark_subvolume_synced, validate_state_document
from timeshift_btrfs_sync.tree_ops import TreeDeleteResult
from test_manual_snapshot_retention import _config

FIRST = "2026-10-01_12-00-00"
MIDDLE = "2026-10-02_12-00-00"
LAST = "2026-10-03_12-00-00"


class RepositoryReconciliationTests(TestCase):
    """Prevent state gaps or cache leaks without ever deleting real Btrfs snapshots."""

    def setUp(self):
        """Create readable ordinary fixtures and isolated immutable identity indexes."""

        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.config = _config(cleanup_enabled=False)
        self.config.source.snapshot_root = str(root / "original")
        self.config.source.cache_root = str(root / "cache")
        self.config.destination.target_root = root / "backup"
        self.config.state_file = root / "state.json"
        for folder in (root / "original", root / "cache", root / "backup/snapshots"):
            folder.mkdir(parents=True)
        self.source = SourceRunner.from_config(self.config)
        self.cache = inventory.BtrfsIndex(str(root / "cache"), "local")
        self.originals = inventory.BtrfsIndex(str(root / "original"), "local")
        self.target = inventory.BtrfsIndex(str(root / "backup/snapshots"), "local")
        self.source_by_name = {}
        self.records = {}
        self.root_meta = SubvolumeMeta("cache", self.config.source.cache_root, uuid="owned-cache-root", subvolume_id=256, readonly=False)
        self.next_id = 257
        self.state = empty_state()
        self.context = reconciliation.ReconciliationContext(self.source, inventory.SourceInventory("", self.originals, self.cache), self.source_by_name, self.target, self.records)

    def add_cache(self, name):
        """Model a native app-cache container and two readonly snapshots of known originals."""

        parent = Path(self.config.source.cache_root) / name
        parent.mkdir(exist_ok=True)
        self.cache.add(SubvolumeMeta(name, str(parent), uuid="container-" + name, readonly=False, subvolume_id=self.next_id))
        self.next_id += 1
        for payload in self.config.source.subvolumes:
            (parent / payload).mkdir(exist_ok=True)
            self.cache.add(SubvolumeMeta(payload, str(parent / payload), uuid=f"send-{name}-{payload}", parent_uuid=f"original-{name}-{payload}", readonly=True, subvolume_id=self.next_id))
            self.next_id += 1

    def add_pair(self, name, *, tracked=True, original=True):
        """Build a complete matching received pair with valid current state when requested."""

        self.add_cache(name)
        parent = self.config.destination.target_root / "snapshots" / name
        parent.mkdir(exist_ok=True)
        self.target.add(SubvolumeMeta(name, str(parent), uuid="target-container-" + name))
        (parent / "info.json").write_text(json.dumps({"tags":"daily weekly", "comments":"saved target control file"}))
        self.records[name] = BackupDirectoryRecord(name, "directory", {"@":"directory", "@home":"directory"}, None)
        snapshot = SnapshotMeta(name, str(Path(self.config.source.snapshot_root) / name), tags=["O"], comment="ordinary protected on-demand", created=name)
        for payload in self.config.source.subvolumes:
            (parent / payload).mkdir(exist_ok=True)
            origin = SubvolumeMeta(payload, str(Path(self.config.source.snapshot_root) / name / payload), uuid=f"original-{name}-{payload}", readonly=False)
            snapshot.subvolumes[payload] = origin
            if original:
                self.originals.add(origin)
            received = SubvolumeMeta(payload, str(parent / payload), uuid=f"received-{name}-{payload}", received_uuid=f"send-{name}-{payload}", readonly=True)
            self.target.add(received)
            if tracked:
                mark_subvolume_synced(self.state, snapshot=snapshot, subvolume=origin, destination_path=parent / payload,
                                      destination_root=self.config.destination.target_root, snapshot_root=self.config.source.snapshot_root,
                                      cache_root=self.config.source.cache_root, parent_snapshot=None, parent_source_path=None,
                                      send_path=str(Path(self.config.source.cache_root) / name / payload), received_meta=received,
                                      original_meta=origin, send_meta=self.cache.meta(str(Path(self.config.source.cache_root) / name / payload)))
        if original:
            self.source_by_name[name] = snapshot

    def recover(self, *, dry_run=False):
        """Run real whole-date recovery against fixtures while observing state writes."""

        with mock.patch.object(sync, "save_state") as save, redirect_stdout(io.StringIO()):
            result = sync._recover_state_from_existing_destination(self.config, self.source, self.state, self.source_by_name,
                dry_run=dry_run, source_cache_index=self.cache, source_snapshot_index=self.originals,
                destination_index=self.target, destination_records=self.records)
        return result, save

    def cleanup(self, *, dry_run=False, yes_delete=True, absence=None, live=None, delete_success=True, successful_sync=True):
        """Mock only storage metadata/deletion while exercising actual ordinary filesystem safety checks."""

        def meta(_ops, path, **_kwargs):
            """Return current metadata without invoking sudo or Btrfs."""
            if str(path) == self.config.source.cache_root: return self.root_meta
            if Path(path).is_symlink(): return None
            return live(path) if live else self.cache.meta(str(path))
        with mock.patch.object(BtrfsOps, "meta", meta), mock.patch.object(reconciliation, "discover_subvolume_tree", return_value=([self.config.source.cache_root, *self.cache.by_path], [])), mock.patch.object(reconciliation, "_discover_repository", side_effect=[(self.cache, {}, [], None, "device"), (self.target, self.records, [], None, "device")]), mock.patch.object(reconciliation, "delete_subvolume_tree", return_value=TreeDeleteResult("fixture", "local", verified_root_absent=delete_success)) as delete, redirect_stdout(io.StringIO()):
            if absence is None:
                result = reconciliation.cleanup_redundant_cache(self.config, self.state, self.context, dry_run=dry_run, yes_delete=yes_delete, successful_sync=successful_sync)
            else:
                with mock.patch.object(reconciliation, "_destination_date_absent", side_effect=absence):
                    result = reconciliation.cleanup_redundant_cache(self.config, self.state, self.context, dry_run=dry_run, yes_delete=yes_delete, successful_sync=successful_sync)
        return result, delete

    def add_window(self):
        """Retain two proven bounds around a missing cache-only middle date."""
        self.add_pair(FIRST)
        self.add_pair(LAST)
        self.add_cache(MIDDLE)

    def test_populated_state_recovers_missing_complete_pair_without_overwrite(self):
        self.add_pair(FIRST)
        before = deepcopy(self.state["snapshots"][FIRST])
        self.add_pair(MIDDLE, tracked=False)
        result, save = self.recover()
        self.assertEqual(result[0], MIDDLE)
        self.assertEqual(self.state["snapshots"][FIRST], before)
        validate_state_document(self.state)
        self.assertIsNone(self.state["snapshots"][MIDDLE]["subvolumes"]["@"]["parent_snapshot"])
        save.assert_called_once()

    def test_empty_state_recovers_expired_original_from_cache_and_target_json(self):
        self.add_pair(MIDDLE, tracked=False, original=False)
        self.recover()
        validate_state_document(self.state)
        recovered = self.state["snapshots"][MIDDLE]
        self.assertEqual(recovered["tags"], ["D", "W"])
        self.assertEqual(recovered["comment"], "saved target control file")
        self.assertEqual(recovered["subvolumes"]["@"]["original_source_uuid"], f"original-{MIDDLE}-@")

    def test_partial_or_mismatched_pairs_never_create_partial_state(self):
        for problem in ("missing", "uuid", "writable", "unknown"):
            self.state = empty_state()
            self.add_pair(MIDDLE, tracked=False)
            path = str(self.config.destination.target_root / "snapshots" / MIDDLE / "@home")
            if problem == "missing":
                self.target.discard(path)
            elif problem == "uuid":
                self.target.meta(path).received_uuid = "foreign"
            else:
                self.target.meta(path).readonly = False if problem == "writable" else None
            self.recover()
            self.assertEqual(self.state["snapshots"], {}, problem)

    def test_unknown_retention_metadata_preserves_untracked_expired_pair(self):
        self.add_pair(MIDDLE, tracked=False, original=False)
        (self.config.destination.target_root / "snapshots" / MIDDLE / "info.json").unlink()
        self.recover()
        self.assertEqual(self.state["snapshots"], {})

    def test_changed_original_cannot_be_mislabelled_as_already_backed_up(self):
        self.add_pair(MIDDLE, tracked=False)
        self.originals.meta(str(Path(self.config.source.snapshot_root) / MIDDLE / "@")).uuid = "changed-original"
        self.recover()
        self.assertEqual(self.state["snapshots"], {})

    def test_ordinary_or_symlinked_destination_container_is_not_adopted(self):
        self.add_pair(MIDDLE, tracked=False)
        path = self.config.destination.target_root / "snapshots" / MIDDLE
        self.target.discard(str(path))
        with mock.patch.object(sync, "_local_meta", return_value=None):
            self.recover()
        self.assertEqual(self.state["snapshots"], {})
        elsewhere = path.with_name("foreign")
        path.rename(elsewhere)
        path.symlink_to(elsewhere)
        self.recover()
        self.assertEqual(self.state["snapshots"], {})

    def test_relocated_cache_identity_is_not_relabelled_as_another_date(self):
        self.add_pair(MIDDLE, tracked=False)
        meta = self.cache.meta(str(Path(self.config.source.cache_root) / MIDDLE / "@"))
        self.cache.discard(meta.path)
        self.cache.add(replace(meta, path=str(Path(self.config.source.cache_root) / FIRST / "@")))
        self.recover()
        self.assertEqual(self.state["snapshots"], {})

    def test_dry_recovery_uses_memory_without_writing_state(self):
        self.add_pair(MIDDLE, tracked=False)
        _result, save = self.recover(dry_run=True)
        self.assertIn(MIDDLE, self.state["snapshots"])
        save.assert_not_called()

    def test_existing_partial_state_is_preserved_for_normal_recovery(self):
        self.add_pair(MIDDLE)
        self.state["snapshots"][MIDDLE]["subvolumes"].pop("@home")
        before = deepcopy(self.state)
        self.recover()
        self.assertEqual(self.state, before)

    def test_incomplete_index_blocks_state_recovery(self):
        self.add_pair(MIDDLE, tracked=False)
        self.target.errors.append("read failure")
        with self.assertRaisesRegex(sync.SyncError, "Incomplete"):
            self.recover()
        self.assertEqual(self.state["snapshots"], {})

    def test_redundant_middle_cache_is_deleted_without_destination_or_state_deletion(self):
        self.add_window()
        before = deepcopy(self.state)
        result, delete = self.cleanup()
        self.assertEqual((result.candidates, result.attempted, result.completed), (1, 1, 1))
        self.assertEqual(self.state, before)
        self.assertEqual(set(self.records), {FIRST, LAST})
        self.assertEqual(delete.call_args.kwargs["protected_roots"], [self.config.source.snapshot_root])
        self.assertEqual(len(delete.call_args.kwargs["expected_subvolume_paths"]), 2)

    def test_user_29_cache_17_destination_case_retires_only_12_middle_leftovers(self):
        for day in range(1, 18):
            self.add_pair(f"2026-10-{day:02d}_12-00-00")
        for hour in range(12, 24):
            self.add_cache(f"2026-10-08_{hour:02d}-30-00")
        result, delete = self.cleanup()
        self.assertEqual((result.candidates, result.completed, delete.call_count), (12, 12, 12))
        self.assertEqual(len(self.state["snapshots"]), 17)
        self.assertEqual(len(self.records), 17)
        self.assertEqual(len({Path(path).parent.name for path in self.cache.by_path if Path(path).name == "@"}), 17)

    def test_newer_cache_remains_and_explicitly_protected_older_cache_is_preserved(self):
        self.add_window()
        self.add_cache("2026-09-30_12-00-00")
        self.add_cache("2026-10-04_12-00-00")
        self.config.retention.protected_snapshots = [MIDDLE, "2026-09-30_12-00-00"]
        result, delete = self.cleanup()
        self.assertEqual(result.candidates, 0)
        delete.assert_not_called()

    def test_existing_destination_or_unknown_absence_blocks_cleanup(self):
        self.add_window()
        result, delete = self.cleanup(absence=[False])
        self.assertEqual(len(result.blocked), 1)
        delete.assert_not_called()
        self.records[MIDDLE] = BackupDirectoryRecord(MIDDLE, "directory", {}, None)
        result, delete = self.cleanup()
        self.assertEqual(len(result.blocked), 1)
        delete.assert_not_called()

    def test_receiver_appearing_during_checks_is_preserved(self):
        self.add_window()
        result, delete = self.cleanup(absence=[True, False])
        self.assertEqual(result.completed, 0)
        delete.assert_not_called()

    def test_owned_native_date_contents_do_not_require_ordinary_listing(self):
        for problem in ("file", "directory", "symlink"):
            self.add_window()
            path = Path(self.config.source.cache_root) / MIDDLE / "foreign"
            if problem == "file":
                path.write_text("preserve")
            elif problem == "directory":
                path.mkdir()
            else:
                path.symlink_to("missing")
            result, delete = self.cleanup()
            self.assertFalse(result.blocked)
            self.assertEqual(result.completed, 1)
            delete.assert_called_once()
            path.rmdir() if problem == "directory" else path.unlink()

    def test_changed_writable_or_foreign_cache_uuid_blocks_cleanup(self):
        self.add_window()
        for problem in ("changed", "writable", "received", "parent"):
            def live(path):
                """Alter one live payload to exercise identity and ownership refusal."""
                meta = self.cache.meta(str(path))
                if meta and meta.name == "@" and MIDDLE in str(path):
                    return replace(meta, **{"uuid":"changed"} if problem == "changed" else {"readonly":False} if problem == "writable" else {"received_uuid":"foreign"} if problem == "received" else {"parent_uuid":None})
                return meta
            result, delete = self.cleanup(live=live)
            self.assertTrue(result.blocked, problem)
            delete.assert_not_called()

    def test_incomplete_transfer_parent_is_protected(self):
        self.add_window()
        self.state["snapshots"][LAST]["subvolumes"].pop("@home")
        self.state["snapshots"][LAST]["subvolumes"]["@"]["parent_snapshot"] = MIDDLE
        self.assertIn(MIDDLE, reconciliation._protected_cache_dates(self.config, self.state))
        result, delete = self.cleanup()
        self.assertEqual(result.candidates, 0)
        delete.assert_not_called()

    def test_disabled_option_master_switch_and_dry_run_never_delete(self):
        self.add_window()
        for flag in ("delete_redundant_snapshots", "cleanup_superseded_cache"):
            setattr(self.config.source, flag, False)
            result, delete = self.cleanup()
            self.assertEqual(result.candidates, 0)
            delete.assert_not_called()
            setattr(self.config.source, flag, True)
        result, delete = self.cleanup(dry_run=True, yes_delete=False)
        self.assertEqual((result.candidates, result.attempted, result.completed), (1, 0, 0))
        delete.assert_not_called()

    def test_real_cleanup_requires_existing_yes_delete_consent(self):
        self.add_window()
        with self.assertRaisesRegex(RuntimeError, "--yes-delete"):
            self.cleanup(yes_delete=False)

    def test_failed_deletion_stays_pending_for_next_run(self):
        self.add_window()
        result, _delete = self.cleanup(delete_success=False)
        self.assertEqual((result.attempted, result.completed, len(result.blocked)), (1, 0, 1))
        self.assertIsNotNone(self.cache.meta(str(Path(self.config.source.cache_root) / MIDDLE)))

    def test_prune_reconciles_then_cleans_even_with_zero_paired_candidates(self):
        self.add_window()
        self.config.destination.delete_redundant_snapshots = False
        extra = reconciliation.RedundantCacheResult(candidates=1, attempted=1, completed=1)
        with mock.patch.object(reconciliation, "prepare_reconciliation", return_value=self.context) as prepare, mock.patch.object(reconciliation, "cleanup_redundant_cache", return_value=extra) as clean, mock.patch.object(retention, "save_state"), redirect_stdout(io.StringIO()):
            result = retention.prune(self.config, self.state, dry_run=False, yes_delete=True, reconcile_inventory=True, successful_sync=True)
        prepare.assert_called_once()
        clean.assert_called_once()
        self.assertEqual(len(result.plan.delete), 0)
        self.assertEqual((result.cache_delete_candidates, result.cache_cleanup_completed), (1, 1))
        self.assertEqual(result.destination_state_deleted, 0)
        self.assertIn("redundant confirmed gone: 1", retention.format_prune_cleanup_summaries(result))

    def test_config_option_defaults_true_can_disable_and_rejects_non_boolean(self):
        template = (Path(__file__).parents[1] / "timeshift_btrfs_sync/data/example-config-local-backup.toml").read_text()
        path = Path(self.temp.name) / "config.toml"
        path.write_text(template.replace("delete_redundant_snapshots = true", "# omitted default"))
        self.assertTrue(load_config(path).source.delete_redundant_snapshots)
        path.write_text(template.replace("delete_redundant_snapshots = true", "delete_redundant_snapshots = false"))
        self.assertFalse(load_config(path).source.delete_redundant_snapshots)
        path.write_text(template.replace("delete_redundant_snapshots = true", 'delete_redundant_snapshots = "true"'))
        with self.assertRaises(ConfigError):
            load_config(path)

    def test_no_confirmed_state_window_preserves_all_cache(self):
        self.add_window()
        for meta in self.target.by_path.values():
            meta.readonly = False
        result, delete = self.cleanup()
        self.assertEqual(result.candidates, 0)
        delete.assert_not_called()

    def test_cache_payload_symlink_and_changed_container_are_preserved(self):
        self.add_window()
        payload = Path(self.config.source.cache_root) / MIDDLE / "@"
        payload.rmdir()
        payload.symlink_to("missing")
        result, delete = self.cleanup()
        self.assertTrue(result.blocked)
        delete.assert_not_called()
        payload.unlink()
        payload.mkdir()
        def live(path):
            """Simulate replacement of a date container after the inventory was collected."""
            meta = self.cache.meta(str(path))
            return replace(meta, uuid="replacement") if meta and meta.name == MIDDLE else meta
        result, delete = self.cleanup(live=live)
        self.assertTrue(result.blocked)
        delete.assert_not_called()

    def test_partial_nested_inventory_stops_reconciliation_before_adoption(self):
        self.add_pair(MIDDLE, tracked=False)
        self.cache.errors.append("failed date-child query")
        with mock.patch.object(inventory, "build_source_inventory", return_value=self.context.source_inventory), mock.patch.object(reconciliation, "_discover_repository", side_effect=[(self.originals, {}, [], None, "device"), (self.cache, {}, [], None, "device")]), mock.patch.object(sync, "_recover_state_from_existing_destination") as adopt:
            with self.assertRaisesRegex(RuntimeError, "Incomplete source cache"):
                reconciliation.prepare_reconciliation(self.config, self.state, dry_run=False)
        adopt.assert_not_called()

    def test_wrong_timeshift_filesystem_stops_reconciliation_before_state_or_deletes(self):
        self.context.source_inventory.timeshift_output = "UUID : 7346e8a6-c3a5-49e3-887f-3abaa94f63a4"
        different = "11111111-1111-1111-1111-111111111111"
        with mock.patch.object(inventory, "build_source_inventory", return_value=self.context.source_inventory), mock.patch.object(reconciliation, "_discover_repository", side_effect=[(self.originals, {}, [], different, "device"), (self.cache, {}, [], different, "device")]), mock.patch.object(sync, "_recover_state_from_existing_destination") as adopt:
            with self.assertRaisesRegex(RuntimeError, "filesystem UUID differs"):
                reconciliation.prepare_reconciliation(self.config, self.state, dry_run=False)
        adopt.assert_not_called()

    def test_summary_does_not_claim_full_success_when_extra_cache_is_blocked(self):
        from timeshift_btrfs_sync.cli import _format_cleanup_summary
        result = retention.PruneResult(plan=retention.PrunePlan(), dry_run=False, remaining_state=17,
                                       cache_cleanup_enabled=True, cache_delete_candidates=12,
                                       cache_cleanup_completed=11, redundant_cache_candidates=12,
                                       redundant_cache_completed=11, redundant_cache_blocked=1,
                                       redundant_cache_cleanup_enabled=True)
        text = _format_cleanup_summary(result, requested=True, dry_run=False)
        self.assertIn("completed with protected/retry items", text)
        self.assertIn("redundant cache confirmed gone: 11", text)

    def test_real_redundant_cleanup_requires_current_successful_sync(self):
        self.add_window()
        result, delete = self.cleanup(successful_sync=False)
        self.assertEqual(result.candidates, 0)
        self.assertIn('successful sync', result.skipped_reason)
        delete.assert_not_called()

    def test_proven_root_cleanup_does_not_run_ordinary_cache_checks(self):
        self.add_window()
        with mock.patch.object(reconciliation, '_safe_cache_date', wraps=reconciliation._safe_cache_date) as guard:
            result, delete = self.cleanup()
        self.assertEqual(result.completed, 1)
        self.assertTrue(guard.call_args.kwargs['native_owned'])
        self.assertIsNotNone(delete.call_args.kwargs['native_cache_proof'])

    def test_date_style_readonly_snapshot_and_partial_cache_are_stale_candidates(self):
        for bare in (False, True):
            with self.subTest(bare=bare):
                self.add_window()
                parent = str(Path(self.config.source.cache_root) / MIDDLE)
                self.cache.discard(parent + '/@home')
                if bare:
                    self.cache.discard(parent + '/@')
                    self.cache.add(replace(self.cache.meta(parent), readonly=True, parent_uuid='original-bare-snapshot'))
                result, delete = self.cleanup()
                self.assertEqual(result.completed, 1)
                proof = delete.call_args.kwargs['native_cache_proof']
                self.assertEqual(len(proof.subvolumes), 1 if bare else 2)

    def test_older_than_first_pair_is_removed_but_newer_is_preserved(self):
        self.add_window()
        older, newer = '2026-09-30_12-00-00', '2026-10-04_12-00-00'
        self.add_cache(older); self.add_cache(newer)
        result, delete = self.cleanup()
        self.assertEqual(result.completed, 2)
        self.assertIn(str(Path(self.config.source.cache_root) / newer), self.cache.by_path)
        self.assertNotIn(str(Path(self.config.source.cache_root) / older), self.cache.by_path)

    def test_root_state_uuid_mismatch_foreign_root_and_incomplete_state_preserve_cache(self):
        for problem in ('state', 'root', 'incomplete'):
            self.add_window()
            original_root = self.root_meta
            if problem == 'state': self.state['snapshots'][FIRST]['subvolumes']['@']['send_source_uuid'] = 'wrong'
            if problem == 'root': self.root_meta = replace(self.root_meta, received_uuid='foreign')
            if problem == 'incomplete': self.state['snapshots'][LAST]['subvolumes'].pop('@home')
            result, delete = self.cleanup()
            if problem != "incomplete": self.assertTrue(result.blocked, problem)
            self.assertEqual(result.completed, 0)
            delete.assert_not_called()
            self.root_meta = original_root
            self.state = empty_state()

    def test_writable_nested_cache_subvolume_blocks_only_its_date(self):
        self.add_window()
        path = str(Path(self.config.source.cache_root) / MIDDLE / 'extra')
        self.cache.add(SubvolumeMeta('extra', path, uuid='extra', subvolume_id=999, readonly=False))
        result, delete = self.cleanup()
        self.assertTrue(result.blocked)
        delete.assert_not_called()

    def test_36_cache_17_pairs_remove_19_stale_dates_without_ordinary_cache_access(self):
        self.add_pair(FIRST); self.add_pair(LAST)
        for minute in range(15): self.add_pair(f'2026-10-02_12-{minute:02d}-00')
        for minute in range(19): self.add_cache(f'2026-09-30_11-{minute:02d}-00')
        from timeshift_btrfs_sync.endpoint import CommandEndpoint
        with mock.patch.object(CommandEndpoint, 'run_shell', side_effect=AssertionError('ordinary cache reader invoked')):
            result, delete = self.cleanup(absence=[True]*38)
        self.assertEqual((result.candidates, result.completed, delete.call_count), (19,19,19))
        self.assertEqual(len(self.state['snapshots']),17)
        self.assertEqual(len(self.records),17)
        self.assertEqual(len({Path(p).parent.name for p in self.cache.by_path if Path(p).name=='@'}),17)


class NativeCacheTreeTests(TestCase):
    """Exercise numeric deletion and privileged final proof with simulated Btrfs commands only."""

    def _run(self, *, leave_id=False, changed=False, unexpected=False, fail_delete=False, unsupported=False, moved=False, malformed=False, moved_within=False, added_id=False):
        """Model a native root/date/payload ID graph; ordinary readers must never be called."""
        from timeshift_btrfs_sync import tree_ops
        from timeshift_btrfs_sync.commands import Completed
        anchor = SubvolumeMeta('cache', '/cache', uuid='cache-root', subvolume_id=256, readonly=False)
        date = '/cache/' + MIDDLE
        metas = {date: SubvolumeMeta(MIDDLE, date, uuid='date', subvolume_id=257, readonly=False),
                 date+'/@': SubvolumeMeta('@', date+'/@', uuid='snapshot', subvolume_id=258, parent_uuid='original', readonly=True)}
        proof = tree_ops.NativeCacheDeletionProof(anchor, metas)
        ids = {256, 257, 258} | ({259} if added_id else set())
        ops = mock.Mock()
        def meta(path, **kwargs):
            """Return stable live native metadata, with optional replacement refusal."""
            result = anchor if path == '/cache' else metas.get(path)
            return replace(result, uuid='replacement') if changed and result and path.endswith('/@') else result
        def run(args, **kwargs):
            """Only simulated native Btrfs list/delete commands are supported."""
            if args[:2] == ['subvolume', 'list']:
                return Completed(0, ''.join(f'ID {i} gen 1 parent {5 if moved and i == 257 else 256 if moved_within and i == 258 else 257 if added_id and i == 259 else 256 if i != 258 else 257} top level 5 path cache/id-{i}\n' for i in sorted(ids))+('truncated record\n' if malformed else ''), '')
            self.assertEqual(args[:4], ['subvolume', 'delete', '--commit-after', '--subvolid'])
            self.assertEqual(args[-1], '/cache')
            if fail_delete or unsupported: return Completed(1, '', 'unsupported --subvolid' if unsupported else 'delete failed')
            if not leave_id: ids.discard(int(args[-2]))
            return Completed(0, '', '')
        ops.meta.side_effect = meta
        ops.run.side_effect = run
        planned = [date+'/@', date]
        if unexpected: planned.insert(0, date+'/foreign')
        with mock.patch.object(tree_ops, 'discover_subvolume_tree', return_value=(planned, [])):
            result = tree_ops.delete_subvolume_tree(ops, date, protected_roots=['/timeshift/snapshots'], native_cache_proof=proof)
        ops.endpoint.run_shell.assert_not_called()
        return result, ops

    def test_numeric_delete_proves_absence_without_any_ordinary_reader(self):
        result, ops = self._run()
        self.assertTrue(result.success)
        deletes = [c.args[0] for c in ops.run.call_args_list if c.args[0][:2] == ['subvolume', 'delete']]
        self.assertEqual([c[-2] for c in deletes], ['258', '257'])

    def test_uuid_replacement_or_unexpected_subvolume_blocks_before_delete(self):
        for kwargs in ({'changed':True}, {'unexpected':True}, {'moved':True}, {'malformed':True}, {'moved_within':True}, {'added_id':True}):
            result, ops = self._run(**kwargs)
            self.assertFalse(result.success)
            self.assertFalse(any(c.args[0][:2] == ['subvolume', 'delete'] for c in ops.run.call_args_list))

    def test_failed_delete_remaining_ids_and_unsupported_tool_never_claim_success(self):
        for kwargs in ({'fail_delete':True}, {'leave_id':True}, {'unsupported':True}):
            result, _ops = self._run(**kwargs)
            self.assertFalse(result.success)
            self.assertTrue(result.errors)


class PostSyncCleanupOrderTests(TestCase):
    """Keep real extra cleanup behind the successful sync return, including verified no-op runs."""

    def test_successful_noop_sync_passes_gate_and_failed_sync_never_calls_prune(self):
        from timeshift_btrfs_sync import cli
        for failed in (False, True):
            config = _config(cleanup_enabled=False)
            config.source.mode = 'local'
            with mock.patch.object(cli, 'load_config', return_value=config), mock.patch.object(cli, '_load_config_state', return_value=empty_state()), mock.patch.object(cli, 'prepare_lock_path'), mock.patch.object(cli, 'FileLock'), mock.patch.object(cli, '_with_logging', side_effect=lambda _cfg,_cmd,fn,**kwargs:fn()), mock.patch.object(cli, 'sync_once', side_effect=sync.SyncError('transfer failed') if failed else None, return_value=sync.SyncRunSummary(0, [], False, 0, 0)) as transfer, mock.patch.object(cli, 'prune', return_value=retention.PruneResult(retention.PrunePlan(), False)) as prune, redirect_stdout(io.StringIO()):
                events = mock.Mock();events.attach_mock(transfer, 'sync');events.attach_mock(prune, 'prune')
                code = cli.main(['sync', '--config', 'fixture.toml', '--run', '--prune', '--yes-delete'])
            self.assertEqual(code, int(failed))
            if failed: prune.assert_not_called()
            else:
                self.assertTrue(prune.call_args.kwargs['successful_sync'])
                self.assertEqual([c[0] for c in events.mock_calls], ['sync', 'prune'])


class DestinationReconciliationTests(TestCase):
    """Exercise bounded receiver-only cleanup without mutating actual storage."""

    def setUp(self):
        """Reuse repository fixtures and give receiver roots/payloads exact native identities."""
        self.f = RepositoryReconciliationTests()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.f.add_pair(FIRST)
        self.f.add_pair(LAST)
        self.receiver_root = SubvolumeMeta('snapshots', str(self.f.config.destination.target_root / 'snapshots'), uuid='owned-target-root', readonly=False, subvolume_id=3000)
        for i, meta in enumerate(self.f.target.by_path.values(), start=3001):
            meta.subvolume_id = i
            if meta.name not in self.f.config.source.subvolumes:
                meta.readonly = False
        self.extra_id = 4000
        self.add_receiver(MIDDLE)

    def add_receiver(self, name, *, bare=False, partial=False):
        """Add a dated native receiver tree whose sending cache has disappeared."""
        parent = str(self.f.config.destination.target_root / 'snapshots' / name)
        meta = SubvolumeMeta(name, parent, uuid='stale-date-'+name, readonly=bare, subvolume_id=self.extra_id,
                             received_uuid='expired-bare-'+name if bare else None)
        self.extra_id += 1
        self.f.target.add(meta)
        if not bare:
            for payload in (['@'] if partial else self.f.config.source.subvolumes):
                self.f.target.add(SubvolumeMeta(payload, parent+'/'+payload, uuid='stale-'+name+payload,
                    received_uuid='expired-send-'+name+payload, readonly=True, subvolume_id=self.extra_id))
                self.extra_id += 1
        self.f.records[name] = BackupDirectoryRecord(name, 'directory', {}, None)

    def cleanup(self, *, dry_run=False, yes_delete=True, successful_sync=True, live=None, discover=None, deleted=True):
        """Mock native storage while using real cleanup/ownership/range logic."""
        f = self.f
        def meta(_ops, path, **kwargs):
            """Return indexed identities or an explicitly simulated changed native path."""
            path = str(path)
            saved = f.root_meta if path == f.config.source.cache_root else self.receiver_root if path == self.receiver_root.path else f.cache.meta(path) or f.target.meta(path) or f.originals.meta(path)
            return live(path, saved) if live else saved
        def tree(_ops, root):
            """Return scoped containment below the selected native repository root."""
            return ([root, *(f.cache.by_path if root == f.config.source.cache_root else f.target.by_path)], [])
        def index(_ops, root):
            """Return complete source/receiver views or a scheduled race/failure fixture."""
            if discover:
                discover(root)
            return (f.cache, {}, [], None, 'device') if root == f.config.source.cache_root else (f.target, f.records, [], None, 'device')
        with mock.patch.object(BtrfsOps, 'meta', meta), mock.patch.object(reconciliation, 'discover_subvolume_tree', tree), mock.patch.object(reconciliation, '_discover_repository', index), mock.patch.object(reconciliation, 'delete_subvolume_tree', return_value=TreeDeleteResult('fixture', 'local', verified_root_absent=deleted)) as delete, redirect_stdout(io.StringIO()):
            result = reconciliation.cleanup_redundant_destination(f.config, f.state, f.context,
                dry_run=dry_run, yes_delete=yes_delete, successful_sync=successful_sync)
        return result, delete

    def test_destination_only_middle_deleted_without_changing_state_or_cache(self):
        before = deepcopy(self.f.state)
        cache = deepcopy(self.f.cache.by_path)
        result, delete = self.cleanup()
        self.assertEqual((result.candidates, result.attempted, result.completed), (1,1,1))
        self.assertEqual(self.f.state, before)
        self.assertEqual(self.f.cache.by_path, cache)
        self.assertEqual(set(self.f.records), {FIRST, LAST})
        self.assertEqual(delete.call_args.kwargs['native_cache_proof'].cache_root, self.receiver_root)
        self.assertEqual(len(delete.call_args.kwargs['native_cache_proof'].subvolumes),3)

    def test_destination_upper_limit_includes_older_but_preserves_newer_bad_dates_and_names(self):
        for name in ('2026-09-30_12-00-00','2026-10-04_12-00-00','2026-10-02_14-99-00','old-backup'):
            self.add_receiver(name)
        result, delete = self.cleanup()
        self.assertEqual((result.candidates,result.completed,delete.call_count),(2,2,2))
        self.assertEqual(len(self.f.records),5)
        self.assertNotIn('2026-09-30_12-00-00', self.f.records)
        self.assertIn('2026-10-04_12-00-00', self.f.records)

    def test_source_counterpart_protected_even_if_missing_from_state(self):
        self.f.add_cache(MIDDLE)
        result, delete = self.cleanup()
        self.assertEqual(result.candidates,0)
        delete.assert_not_called()

    def test_tracked_and_explicitly_protected_receiver_dates_preserved(self):
        self.f.config.retention.protected_snapshots = [MIDDLE]
        result, delete = self.cleanup()
        self.assertEqual(result.candidates,0)
        delete.assert_not_called()
        self.f.config.retention.protected_snapshots = []
        self.f.state['snapshots'][MIDDLE] = deepcopy(self.f.state['snapshots'][FIRST])
        result, delete = self.cleanup()
        self.assertEqual(result.candidates,0)
        delete.assert_not_called()

    def test_no_successful_sync_skip_and_dry_preview_no_delete(self):
        result, delete = self.cleanup(successful_sync=False)
        self.assertIn('successful sync',result.skipped_reason)
        delete.assert_not_called()
        result, delete = self.cleanup(dry_run=True,successful_sync=False,yes_delete=False)
        self.assertEqual((result.candidates,result.attempted,result.completed),(1,0,0))
        self.assertEqual(result.blocked,[])
        delete.assert_not_called()

    def test_destination_option_independent_of_source_cleanup_switches(self):
        self.f.config.source.delete_redundant_snapshots = False
        self.f.config.source.cleanup_superseded_cache = False
        result, delete = self.cleanup()
        self.assertEqual(result.completed,1)
        delete.assert_called_once()

    def test_disabled_destination_option_does_not_call_storage(self):
        self.f.config.destination.delete_redundant_snapshots = False
        with mock.patch.object(reconciliation,'_discover_repository') as read:
            result = reconciliation.cleanup_redundant_destination(self.f.config,self.f.state,self.f.context,dry_run=False,yes_delete=True,successful_sync=True)
        self.assertEqual(result.completed,0)
        read.assert_not_called()

    def test_real_delete_requires_explicit_yes_delete(self):
        with self.assertRaisesRegex(RuntimeError,'--yes-delete'):
            self.cleanup(yes_delete=False)

    def test_incomplete_or_missing_cache_inventory_preserves_receivers(self):
        self.f.cache.errors.append('native list truncated')
        result, delete = self.cleanup()
        self.assertIn('incomplete',result.skipped_reason)
        delete.assert_not_called()
        self.f.cache.errors.clear()
        self.f.cache.root_missing = True
        result, delete = self.cleanup()
        self.assertIn('incomplete',result.skipped_reason)
        delete.assert_not_called()

    def test_missing_cache_configuration_preserves_receivers(self):
        self.f.config.source.cache_root = None
        result, delete = self.cleanup()
        self.assertIn('cache_root',result.skipped_reason)
        delete.assert_not_called()

    def test_writable_unknown_or_changed_payload_cannot_be_deleted(self):
        path = str(self.f.config.destination.target_root / 'snapshots' / MIDDLE / '@')
        original = self.f.target.meta(path)
        for change in ({'readonly':False},{'received_uuid':None,'parent_uuid':None},{'uuid':'replacement'},{'subvolume_id':9999}):
            with self.subTest(change=change):
                result, delete = self.cleanup(live=lambda p,m: replace(m,**change) if p==path else m)
                self.assertTrue(result.blocked)
                delete.assert_not_called()
        self.assertTrue(original.readonly)

    def test_replaced_or_snapshot_destination_root_blocks_cleanup(self):
        self.receiver_root.parent_uuid = 'foreign-root-snapshot'
        result, delete = self.cleanup()
        self.assertTrue(result.blocked)
        delete.assert_not_called()

    def test_mismatched_state_pair_blocks_receiver_ownership(self):
        path = str(self.f.config.destination.target_root / 'snapshots' / FIRST / '@')
        result, delete = self.cleanup(live=lambda p,m: replace(m,received_uuid='foreign') if p==path else m)
        self.assertTrue(result.blocked)
        delete.assert_not_called()

    def test_cache_appearing_immediately_before_delete_blocks_receiver_removal(self):
        calls = 0
        def race(root):
            """Create a source counterpart after the first complete absence check."""
            nonlocal calls
            if root == self.f.config.source.cache_root:
                calls += 1
                if calls == 3:
                    self.f.add_cache(MIDDLE)
        result, delete = self.cleanup(discover=race)
        self.assertEqual(result.completed,0)
        self.assertIn('counterpart',result.blocked[0])
        delete.assert_not_called()

    def test_cache_becoming_unreadable_before_delete_blocks_receiver_removal(self):
        calls = 0
        def race(root):
            """Simulate an unavailable cache between checks without claiming absence."""
            nonlocal calls
            if root == self.f.config.source.cache_root:
                calls += 1
                if calls == 3:
                    self.f.cache.errors.append('connection lost')
        result, delete = self.cleanup(discover=race)
        self.assertIn('absence not proven',result.blocked[0])
        delete.assert_not_called()

    def test_bare_and_partial_readonly_receiver_dates_use_shared_tree_engine(self):
        self.f.target.remove_tree(str(self.f.config.destination.target_root / 'snapshots' / MIDDLE))
        self.add_receiver(MIDDLE,bare=True)
        partial = '2026-10-02_13-00-00'
        self.add_receiver(partial,partial=True)
        result, delete = self.cleanup()
        self.assertEqual((result.completed,delete.call_count),(2,2))
        self.assertEqual([len(c.kwargs['native_cache_proof'].subvolumes) for c in delete.call_args_list],[1,2])

    def test_known_source_uuid_under_another_date_preserves_receiver(self):
        path = str(self.f.config.destination.target_root / 'snapshots' / MIDDLE / '@')
        self.f.target.meta(path).received_uuid = self.f.cache.meta(str(Path(self.f.config.source.cache_root) / FIRST / '@')).uuid
        result, delete = self.cleanup()
        self.assertIn('known source/cache',result.blocked[0])
        delete.assert_not_called()

    def test_deletion_not_confirmed_is_retry_without_state_loss(self):
        before = deepcopy(self.f.state)
        result, delete = self.cleanup(deleted=False)
        self.assertEqual((result.candidates,result.attempted,result.completed),(1,1,0))
        self.assertTrue(result.blocked)
        self.assertEqual(self.f.state,before)
        self.assertIn(MIDDLE,self.f.records)

    def test_destination_boolean_default_disable_and_strict_validation(self):
        template = (Path(__file__).parents[1] / 'timeshift_btrfs_sync/data/example-config-local-backup.toml').read_text()
        before, destination = template.split('[destination]',1)
        path = Path(self.f.temp.name) / 'config.toml'
        for value, expected in (('# omitted',True),('delete_redundant_snapshots = false',False)):
            path.write_text(before+'[destination]'+destination.replace('delete_redundant_snapshots = true',value))
            cfg = load_config(path)
            self.assertEqual(cfg.destination.delete_redundant_snapshots,expected)
            self.assertTrue(cfg.source.delete_redundant_snapshots)
        path.write_text(before+'[destination]'+destination.replace('delete_redundant_snapshots = true','delete_redundant_snapshots = "true"'))
        with self.assertRaises(ConfigError):
            load_config(path)

    def test_receiver_only_counters_do_not_inflate_paired_state_cleanup(self):
        from timeshift_btrfs_sync.cli import _format_cleanup_summary
        result = retention.PruneResult(retention.PrunePlan(),False,redundant_destination_cleanup_enabled=True)
        extra = reconciliation.RedundantCacheResult(candidates=3,attempted=2,completed=1,blocked=['retry','protected'])
        with mock.patch.object(reconciliation,'cleanup_redundant_destination',return_value=extra):
            retention._apply_redundant_destination_cleanup(self.f.config,self.f.state,self.f.context,result,yes_delete=True,successful_sync=True)
        self.assertEqual(result.cleaned_snapshots,0)
        self.assertEqual(result.destination_state_deleted,0)
        text = _format_cleanup_summary(requested=True,dry_run=False,result=result)
        self.assertIn('redundant destination confirmed gone: 1',text)
        self.assertIn('completed with protected/retry items',text)
        self.assertIn('redundant blocked:        2',retention.format_prune_cleanup_summaries(result))


    def test_all_older_valid_dates_are_candidates_without_a_lower_limit(self):
        old = ['2001-01-01_00-00-00','2025-12-31_23-59-59','2026-09-30_23-59-59']
        for name in old:
            self.add_receiver(name)
        before = deepcopy(self.f.state)
        result, delete = self.cleanup()
        self.assertEqual((result.candidates,result.completed,delete.call_count),(4,4,4))
        self.assertEqual(self.f.state,before)
        self.assertEqual(set(self.f.records),{FIRST,LAST})

    def test_older_receiver_preserved_when_ownership_uuid_pair_is_invalid(self):
        old = '2025-01-01_00-00-00'
        self.add_receiver(old)
        path = str(self.f.config.destination.target_root / 'snapshots' / FIRST / '@')
        result, delete = self.cleanup(live=lambda p,m: replace(m,received_uuid='foreign-stream') if p==path else m)
        self.assertEqual(result.completed,0)
        self.assertTrue(result.blocked)
        self.assertIn(old,self.f.records)
        delete.assert_not_called()

    def test_older_excluded_or_writable_snapshots_remain_protected(self):
        old = '2025-01-01_00-00-00'
        self.add_receiver(old)
        self.f.config.retention.protected_snapshots = [old]
        result, delete = self.cleanup()
        self.assertEqual(result.completed,1)
        self.assertIn(old,self.f.records)
        self.f.config.retention.protected_snapshots = []
        path = str(self.f.config.destination.target_root / 'snapshots' / old / '@')
        self.f.target.meta(path).readonly = False
        result, delete = self.cleanup()
        self.assertEqual(result.completed,0)
        self.assertTrue(result.blocked)
        delete.assert_not_called()

    def test_dry_preview_includes_older_snapshots_but_never_newer_snapshots(self):
        old = '2025-01-01_00-00-00'
        future = '2026-10-03_12-00-01'
        self.add_receiver(old)
        self.add_receiver(future)
        before = deepcopy(self.f.state)
        result, delete = self.cleanup(dry_run=True,successful_sync=False,yes_delete=False)
        self.assertEqual((result.candidates,result.attempted,result.completed),(2,0,0))
        self.assertEqual(result.blocked,[])
        self.assertEqual(self.f.state,before)
        self.assertIn(future,self.f.records)
        delete.assert_not_called()
