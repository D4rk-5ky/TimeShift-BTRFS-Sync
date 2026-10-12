"""Non-root inventory tests with physical local fixtures and simulated Btrfs/SSH."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, mock
import base64
import contextlib
import io
import json
import re

from timeshift_btrfs_sync import listing
from timeshift_btrfs_sync.btrfs_ops import BtrfsOps
from timeshift_btrfs_sync.cli import main
from timeshift_btrfs_sync.commands import Completed
from timeshift_btrfs_sync.config import CONFIG_PROFILES, load_config
from timeshift_btrfs_sync.endpoint import CommandEndpoint
from timeshift_btrfs_sync.restore import BackupDirectoryRecord
from timeshift_btrfs_sync.inventory import BtrfsIndex
from timeshift_btrfs_sync.models import SubvolumeMeta
from test_manual_snapshot_retention import _config


NAME = "2026-10-12_12-25-36"
SHOW = "ro=true\n"
SPACE = {"device": "/dev/sda2", "fstype": "btrfs", "size": "100G", "used": "74G", "available": "26G", "percent": "74%", "mount": "/mnt/source"}


def _record(*, tags: str = "hourly daily weekly monthly", payloads: tuple[str, ...] = ("@", "@home")) -> BackupDirectoryRecord:
    """Create a discovered physical date with native Timeshift metadata."""

    return BackupDirectoryRecord(NAME, "directory", {p: "directory" for p in payloads}, json.dumps({"tags": tags, "comments": "Initial install"}))


class SnapshotListingTests(TestCase):
    """Verify truthful reports and transport/privilege boundaries across every profile."""

    def _section(self, record: BackupDirectoryRecord, *, probes: dict | None = None, metadata: dict | None = None):
        """Reuse the shared config fixture and isolate only external discovery/probes."""

        root = "/cache"
        if probes is None:
            probes = {f"{root}/{NAME}/{p}": Completed(0, SHOW, "") for p, kind in record.entries.items() if kind == "directory"}
        with mock.patch.object(listing, "_filesystem_space", return_value=SPACE), mock.patch.object(listing, "_probe_payloads", return_value=probes):
            return listing._collect_section(_config(), CommandEndpoint.local(), title="CACHE", location="local", root=root, btrfs_command="btrfs", records={NAME: record}, metadata=metadata)

    def test_named_tags_do_not_invent_ondemand_or_boot(self):
        self.assertEqual(listing._snapshot_description(_record())[0], "H D W M")
        self.assertEqual(listing._snapshot_description(_record(tags="ondemand hourly daily weekly monthly boot"))[0], "O H D W M B")

    def test_compact_tags_and_unknown_metadata(self):
        self.assertEqual(listing._snapshot_description(_record(tags="DWM H"))[0], "H D W M")
        self.assertEqual(listing._snapshot_description(None)[0], "?")
        record = _record()
        for content in ("broken", "[]", "{}", '{"tags": ["daily"]}', '{"tags":"unexpected"}', '{"tags":"daily","comments":null}'):
            record.info_content = content
            self.assertEqual(listing._snapshot_description(record)[0], "?")

    def test_remote_comments_cannot_inject_terminal_controls(self):
        record = _record()
        record.info_content = json.dumps({"tags": "daily", "comments": "first\nsecond\u001b[31m"})
        text = listing._snapshot_description(record)[1]
        self.assertNotIn("\n", text)
        self.assertNotIn("\x1b", text)

    def test_pair_counts_once_and_readonly_is_visible(self):
        section = self._section(_record())
        self.assertFalse(section.failed)
        self.assertTrue(section.rows[0].complete)
        text = listing.format_snapshot_listings("backup", [section])
        self.assertIn("1 verified snapshot date(s)", text)
        self.assertIn("@:ro, @home:ro", text)
        self.assertIn("26G free / 100G total", text)
        probes = {f"/cache/{NAME}/{p}": Completed(0, "ro=false\n", "") for p in ("@", "@home")}
        writable = self._section(_record(), probes=probes)
        self.assertIn("@:rw", writable.rows[0].payloads)
        probes[f"/cache/{NAME}/@"] = Completed(0, "not a ro property", "")
        self.assertTrue(self._section(_record(), probes=probes).failed)

    def test_incomplete_and_unverified_dates_stay_visible(self):
        section = self._section(_record(payloads=("@",)))
        self.assertTrue(section.failed)
        self.assertTrue(section.rows[0].verified)
        self.assertFalse(section.rows[0].complete)
        section = self._section(_record(), probes={})
        self.assertTrue(section.failed)
        self.assertFalse(section.rows[0].verified)
        self.assertIn(NAME, listing.format_snapshot_listings("backup", [section]))

    def test_permission_denied_is_visible_without_fallback(self):
        probes = {f"/cache/{NAME}/{p}": Completed(1, "", "Permission denied") for p in ("@", "@home")}
        section = self._section(_record(), probes=probes)
        self.assertTrue(section.failed)
        self.assertIn("Permission denied", listing.format_snapshot_listings("backup", [section]))

    def test_symlink_date_and_payload_not_probed(self):
        record = _record()
        record.kind = "symlink"
        section = self._section(record, probes={})
        self.assertTrue(section.failed)
        self.assertFalse(section.rows[0].verified)
        record = _record()
        record.entries["@"] = "symlink"
        section = self._section(record)
        self.assertTrue(section.failed)
        self.assertIn("@: symlink", " ".join(section.rows[0].notes))

    def test_cache_own_metadata_precedes_live_source_fallback(self):
        cache = _record(tags="hourly")
        section = self._section(cache, metadata={NAME: _record(tags="weekly monthly")})
        self.assertEqual(section.rows[0].tags, "H")
        cache.info_content = None
        section = self._section(cache, metadata={NAME: _record(tags="weekly monthly")})
        self.assertEqual(section.rows[0].tags, "W M")
        section = self._section(cache, metadata={})
        self.assertEqual(section.rows[0].tags, "?")
        self.assertFalse(section.failed)

    def test_disabled_cache_reports_source_filesystem(self):
        with mock.patch.object(listing, "_filesystem_space", return_value=SPACE) as space, mock.patch.object(listing, "_scan_unprivileged") as scan:
            section = listing._collect_section(_config(), CommandEndpoint.local(), title="CACHE", location="local", root=None, btrfs_command="btrfs")
        self.assertFalse(section.failed)
        scan.assert_not_called()
        self.assertEqual(space.call_args.args[1], _config().source.snapshot_root)
        self.assertIn("DISABLED", listing.format_snapshot_listings("backup", [section]))

    def test_empty_repository_is_distinct_from_unavailable(self):
        with mock.patch.object(listing, "_filesystem_space", return_value=SPACE), mock.patch.object(listing, "_probe_payloads", return_value={}):
            empty = listing._collect_section(_config(), CommandEndpoint.local(), title="CACHE", location="local", root="/cache", btrfs_command="btrfs", records={})
            failed = listing._collect_section(_config(), CommandEndpoint.local(), title="CACHE", location="local", root="/cache", btrfs_command="btrfs", scan_error="Permission denied")
        self.assertFalse(empty.failed)
        self.assertTrue(failed.failed)
        self.assertIn("UNAVAILABLE", listing.format_snapshot_listings("backup", [failed]))

    def test_wrong_filesystem_is_reported_even_for_empty_repository(self):
        with mock.patch.object(listing, "_filesystem_space", return_value={**SPACE, "fstype": "ext4"}):
            section = listing._collect_section(_config(), CommandEndpoint.local(), title="CACHE", location="local", root="/cache", btrfs_command="btrfs", records={})
        self.assertTrue(section.failed)
        self.assertIn("not Btrfs", " ".join(section.notes))

    def test_real_batch_execution_quotes_paths_and_preserves_failures(self):
        with TemporaryDirectory(prefix="probe's ") as directory:
            command = Path(directory) / "fake btrfs"
            command.write_text("#!/bin/sh\ncase \"$4\" in\n  *fail*) echo 'Permission denied' >&2; exit 1;;\n  *) printf 'ro=true\\n';;\nesac\n")
            command.chmod(0o755)
            paths = [directory + "/@; $(false)", directory + "/fail/@home"]
            probes = listing._probe_payloads(BtrfsOps(CommandEndpoint.local(), command_name=str(command)), paths)
        self.assertEqual(probes[paths[0]].returncode, 0)
        self.assertEqual("ro=true", probes[paths[0]].stdout.strip())
        self.assertEqual(probes[paths[1]].returncode, 1)
        self.assertIn("Permission denied", probes[paths[1]].stdout)

    def test_all_eight_profiles_choose_actual_hosts_in_auto(self):
        data = Path(__file__).parents[1] / "timeshift_btrfs_sync/data"
        with mock.patch.object(listing, "_scan_unprivileged", return_value={}), mock.patch.object(listing, "_filesystem_space", return_value=SPACE), mock.patch.object(listing, "_probe_payloads", return_value={}), mock.patch.object(listing, "_discover_repository", return_value=(BtrfsIndex("/test", "local"), {}, [], None, "device")), mock.patch.object(listing, "_run_batched_commands", return_value={0: Completed(0,"","")}):
            for filename, _description in CONFIG_PROFILES.values():
                config = load_config(data / filename)
                with mock.patch.object(listing, "_collect_section", wraps=listing._collect_section) as collect:
                    workflow, sections = listing.collect_snapshot_listings(config, include_timeshift=True)
                originals, source, destination = (call.args[1] for call in collect.call_args_list)
                restore = config.restore.mode != "local"
                expected_source = config.restore.timeshift_uses_ssh if restore else config.source.mode == "ssh"
                expected_dest = config.restore.backup_uses_ssh if restore else False
                self.assertEqual(source.location, "remote" if expected_source else "local", filename)
                self.assertEqual(destination.location, "remote" if expected_dest else "local", filename)
                self.assertEqual(originals.location, source.location)
                self.assertEqual(collect.call_args_list[0].kwargs["sudo"], config.source.sudo)
                self.assertEqual(collect.call_args_list[1].kwargs["sudo"], config.source.sudo)
                self.assertEqual(collect.call_args_list[2].kwargs["sudo"], config.destination.sudo)
                self.assertEqual(workflow, "restore" if restore else "backup")
                self.assertEqual(len(sections), 3)

    def test_explicit_restore_local_ignores_sync_ssh_source(self):
        data = Path(__file__).parents[1] / "timeshift_btrfs_sync/data/config.example.toml"
        config = load_config(data)
        with mock.patch.object(listing, "_scan_unprivileged", return_value={}), mock.patch.object(listing, "_filesystem_space", return_value=SPACE), mock.patch.object(listing, "_probe_payloads", return_value={}), mock.patch.object(listing, "_discover_repository", return_value=(BtrfsIndex("/test", "local"), {}, [], None, "device")), mock.patch.object(listing, "_run_batched_commands", return_value={0: Completed(0,"","")}):
            workflow, sections = listing.collect_snapshot_listings(config, workflow="restore")
        self.assertEqual(workflow, "restore")
        self.assertTrue(all(section.location.startswith("local") for section in sections))

    def test_source_failure_does_not_hide_destination(self):
        def scan(_endpoint, root, _label):
            """Simulate inaccessible source and a readable backup date."""
            if root.startswith("/timeshift"):
                raise RuntimeError("source denied")
            return {NAME: _record()}
        probes = {f"/backup/snapshots/{NAME}/{p}": Completed(0, SHOW, "") for p in ("@", "@home")}
        with mock.patch.object(listing, "_scan_unprivileged", side_effect=scan), mock.patch.object(listing, "_filesystem_space", return_value=SPACE), mock.patch.object(listing, "_probe_payloads", return_value=probes), mock.patch.object(listing, "_discover_repository", return_value=(BtrfsIndex("/test", "local"), {}, [], None, "device")), mock.patch.object(listing, "_run_batched_commands", return_value={0: Completed(0,"","")}):
            workflow, sections = listing.collect_snapshot_listings(_config())
        self.assertFalse(sections[0].failed)
        self.assertFalse(sections[1].failed)
        self.assertFalse(sections[2].failed)
        text = listing.format_snapshot_listings(workflow, sections)
        self.assertIn("source denied", text)
        self.assertIn("TARGET_ROOT SNAPSHOTS", text)
        self.assertIn(NAME, text)

    def test_cli_returns_failure_after_printing_all_sections_without_run_logging(self):
        sections = [listing.SnapshotListingSection("SOURCE", "local", "/source", failed=True), listing.SnapshotListingSection("DESTINATION", "local", "/backup")]
        with mock.patch("timeshift_btrfs_sync.cli.load_config", return_value=_config()), mock.patch("timeshift_btrfs_sync.cli.collect_snapshot_listings", return_value=("backup", sections)), mock.patch("timeshift_btrfs_sync.cli._with_logging") as logging, contextlib.redirect_stdout(io.StringIO()) as output:
            code = main(["list-snapshots", "--config", "config.toml"])
        self.assertEqual(code, 1)
        logging.assert_not_called()
        self.assertIn("SOURCE", output.getvalue())
        self.assertIn("DESTINATION", output.getvalue())

    def test_df_parses_localized_environment_and_spaced_mount(self):
        endpoint = mock.Mock()
        endpoint.run_shell.return_value = Completed(0, "Filesystem Type Size Used Avail Use% Mounted on\n/dev/sda2 btrfs 100G 74G 26G 74% /mnt/with spaces\n", "")
        space = listing._filesystem_space(endpoint, "/path with 'quotes'")
        self.assertEqual(space["mount"], "/mnt/with spaces")
        self.assertEqual(space["available"], "26G")
        command = endpoint.run_shell.call_args.args[0]
        self.assertTrue(command.startswith("LC_ALL=C df -h -P -T -- "))
        self.assertNotIn("sudo", command)
        endpoint.run_shell.return_value = Completed(1, "", "Permission denied")
        with self.assertRaisesRegex(RuntimeError, "Permission denied"):
            listing._filesystem_space(endpoint, "/denied")

    def test_actual_local_scan_and_df_need_no_privilege(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            date = root / NAME
            date.mkdir()
            (date / "@").mkdir()
            (date / "info.json").write_text('{"tags":"daily","comments":"local fixture"}')
            endpoint = CommandEndpoint.local()
            records = listing._scan_unprivileged(endpoint, str(root), "local fixture")
            self.assertEqual(listing._snapshot_description(records[NAME])[:2], ("D", "local fixture"))
            self.assertIn("available", listing._filesystem_space(endpoint, str(root)))

    def test_batch_probes_reuse_btrfs_argv_and_do_not_inject_sudo(self):
        endpoint = mock.Mock()
        encoded = base64.b64encode(SHOW.encode()).decode()
        endpoint.run_shell.return_value = Completed(0, f"TSBTRFS_LIST_PROBE\t0\t0\t{encoded}\nTSBTRFS_LIST_PROBE\t1\t1\t\n", "")
        paths = ["/cache/a' quote/@", "/cache/second/@home"]
        probes = listing._probe_payloads(BtrfsOps(endpoint, sudo="", command_name="/usr/bin/btrfs"), paths)
        self.assertEqual(probes[paths[0]].returncode, 0)
        self.assertEqual(probes[paths[1]].returncode, 1)
        endpoint.run_shell.assert_called_once()
        script = endpoint.run_shell.call_args.args[0]
        self.assertNotIn("sudo", script)
        self.assertEqual(script.count("/usr/bin/btrfs property get -ts"), 2)
        self.assertNotIn("mktemp", script)
        self.assertNotIn("subvolume list", script)

    def test_truncated_or_duplicate_batch_response_fails(self):
        endpoint = mock.Mock()
        for stdout in ("", "TSBTRFS_LIST_PROBE\t0\t0\t\nTSBTRFS_LIST_PROBE\t0\t0\t\n", "TSBTRFS_LIST_PROBE\t0\t0\t!bad64\n"):
            endpoint.run_shell.return_value = Completed(0, stdout, "")
            with self.assertRaises(RuntimeError):
                listing._probe_payloads(BtrfsOps(endpoint), ["/cache/@"])

    def test_large_repository_uses_bounded_batches_without_losing_rows(self):
        endpoint = mock.Mock()
        encoded = base64.b64encode(SHOW.encode()).decode()
        def respond(script, **_kwargs):
            """Return one flag frame per request in each bounded transport batch."""
            self.assertLessEqual(len(script.encode("utf-8")), 16000)
            indices = re.findall(r"TSBTRFS_LIST_PROBE\\t(\d+)", script)
            return Completed(0, "".join(f"TSBTRFS_LIST_PROBE\t{index}\t0\t{encoded}\n" for index in indices), "")
        endpoint.run_shell.side_effect = respond
        paths = [f"/cache/2026-date-{index:04}/@home" for index in range(1000)]
        probes = listing._probe_payloads(BtrfsOps(endpoint), paths)
        self.assertEqual(set(probes), set(paths))
        self.assertGreater(endpoint.run_shell.call_count, 1)
        self.assertLess(endpoint.run_shell.call_count, 30)


class SnapshotPairComparisonTests(TestCase):
    """Expose cache leftovers and UUID mismatches without changing storage or default exit policy."""

    def _rows(self, names, *, receiver=False, readonly=True):
        """Build both configured payload identities; differing local UUIDs share a valid send identity."""
        rows = []
        for name in names:
            row = listing.SnapshotListingRow(name, 'H', '', verified=True, complete=True)
            row.subvolumes = {payload: SubvolumeMeta(payload, f'/{name}/{payload}', uuid=f'{name}-{payload}-receiver' if receiver else f'{name}-{payload}', received_uuid=f'{name}-{payload}' if receiver else None, readonly=readonly) for payload in ('@', '@home')}
            rows.append(row)
        return rows

    def _compare(self, cache_names, target_names):
        """Keep endpoint discovery separate from the comparison's captured physical observations."""
        cache = listing.SnapshotListingSection('CACHE_ROOT SNAPSHOTS', 'SSH', '/cache', self._rows(cache_names))
        target = listing.SnapshotListingSection('TARGET_ROOT SNAPSHOTS', 'local', '/target', self._rows(target_names, receiver=True))
        return listing.compare_snapshot_listings(_config(), cache, target), cache, target

    def test_user_36_cache_17_target_sample_reports_all_19_july_leftovers(self):
        shared = ['2026-06-23_07-10-24', '2026-09-11_07-57-50', '2026-09-12_07-17-28', '2026-09-15_12-00-03', '2026-09-16_12-00-04', '2026-09-17_11-47-20', '2026-10-01_17-19-36', '2026-10-01_20-00-03', '2026-10-02_15-41-17', '2026-10-02_18-00-03', '2026-10-03_11-00-03', '2026-10-03_12-00-03', '2026-10-12_12-10-30', '2026-10-12_12-27-48', '2026-10-12_14-00-03', '2026-10-12_15-00-04', '2026-10-12_18-47-26']
        extra = ['2026-07-15_14-00-04', '2026-07-16_14-03-26', '2026-07-16_18-40-51', '2026-07-17_14-02-09', '2026-07-17_14-46-41', '2026-07-17_16-28-47', '2026-07-17_19-57-22', '2026-07-21_15-34-52', '2026-07-22_15-03-41', '2026-07-24_16-00-04', '2026-07-24_17-00-05', '2026-07-24_18-00-05', '2026-07-24_19-00-04', '2026-07-24_20-00-09', '2026-07-24_21-02-46', '2026-07-25_11-00-02', '2026-07-25_12-00-02', '2026-07-25_17-39-39', '2026-07-25_18-29-13']
        comparison, cache, target = self._compare(shared + extra, shared)
        self.assertEqual((comparison.cache_dates, comparison.destination_dates), (36, 17))
        self.assertEqual(comparison.matching_dates, shared)
        self.assertEqual(comparison.in_window_dates, extra)
        self.assertEqual(comparison.outside_window_dates, [])
        self.assertFalse(comparison.parity_confirmed())
        cache.comparison = comparison
        text = listing.format_snapshot_listings('backup', [cache, target])
        self.assertIn('WARNING - cache/destination pairs differ', text)
        self.assertIn('Cache-only dates         : 19', text)
        self.assertIn('Cache-only inside range  : 19', text)
        for name in extra:
            self.assertIn(name + ' [inside proven range]', text)

    def test_equal_counts_with_different_dates_are_not_parity(self):
        comparison, _, _ = self._compare(['2026-10-10_00-00-00'], ['2026-10-11_00-00-00'])
        self.assertFalse(comparison.parity_confirmed())
        self.assertEqual(len(comparison.cache_only_dates), 1)
        self.assertEqual(len(comparison.destination_only_dates), 1)

    def test_changed_flags_do_not_invalidate_an_immutable_pair(self):
        _, cache, target = self._compare([NAME], [NAME])
        cache.rows[0].tags = 'H'
        target.rows[0].tags = 'D W M'
        comparison = listing.compare_snapshot_listings(_config(), cache, target)
        self.assertTrue(comparison.parity_confirmed())

    def test_same_names_with_uuid_mismatch_missing_sibling_or_writable_payload_are_unproven(self):
        for change in ('identity', 'missing', 'writable', 'unknown'):
            with self.subTest(change=change):
                _, cache, target = self._compare([NAME], [NAME])
                if change == 'identity': target.rows[0].subvolumes['@home'].received_uuid = 'different-stream'
                if change == 'missing': del cache.rows[0].subvolumes['@home']
                if change == 'writable': cache.rows[0].subvolumes['@home'].readonly = False
                if change == 'unknown': target.rows[0].subvolumes['@home'].readonly = None
                comparison = listing.compare_snapshot_listings(_config(), cache, target)
                self.assertEqual(comparison.matching_dates, [])
                self.assertEqual(comparison.unproven_dates, [NAME])
                self.assertIsNone(comparison.window)
                self.assertFalse(comparison.parity_confirmed())

    def test_received_sender_uses_original_stream_identity(self):
        _, cache, target = self._compare([NAME], [NAME])
        for payload in ('@', '@home'):
            cache.rows[0].subvolumes[payload].received_uuid = cache.rows[0].subvolumes[payload].uuid
            cache.rows[0].subvolumes[payload].uuid = 'different-local-uuid'
        self.assertTrue(listing.compare_snapshot_listings(_config(), cache, target).parity_confirmed())

    def test_outside_window_is_distinguished_without_a_deletion_claim(self):
        names = ['2026-10-09_00-00-00', '2026-10-10_00-00-00', '2026-10-11_00-00-00', '2026-10-12_00-00-00']
        comparison, _, _ = self._compare(names, names[1:3])
        self.assertEqual(comparison.outside_window_dates, [names[0], names[3]])
        self.assertEqual(comparison.in_window_dates, [])
        text = '\n'.join(listing._format_pair_comparison(comparison))
        self.assertIn('newer caches may remain', text)
        self.assertIn('neither reads/rebuilds state nor deletes', text)

    def test_incomplete_discovery_never_confirms_parity_or_absence(self):
        _, cache, target = self._compare([NAME], [NAME])
        target.inventory_complete = False
        comparison = listing.compare_snapshot_listings(_config(), cache, target)
        self.assertFalse(comparison.parity_confirmed())
        self.assertIn('not proof of absence', '\n'.join(listing._format_pair_comparison(comparison)))

    def test_disabled_cache_is_explicit_and_empty_enabled_roots_match(self):
        _, cache, target = self._compare([], [])
        self.assertTrue(listing.compare_snapshot_listings(_config(), cache, target).parity_confirmed())
        cache.root = None
        comparison = listing.compare_snapshot_listings(_config(), cache, target)
        self.assertFalse(comparison.parity_confirmed())
        self.assertIn('DISABLED', '\n'.join(listing._format_pair_comparison(comparison)))

    def test_opt_in_cli_exit_check_and_default_warning_have_no_run_logging(self):
        for different in (False, True):
            comparison, cache, target = self._compare([NAME], [] if different else [NAME])
            cache.comparison = comparison
            for strict in (False, True):
                with self.subTest(different=different, strict=strict), mock.patch('timeshift_btrfs_sync.cli.load_config', return_value=_config()), mock.patch('timeshift_btrfs_sync.cli.collect_snapshot_listings', return_value=('restore', [cache, target])), mock.patch('timeshift_btrfs_sync.cli._with_logging') as logging, contextlib.redirect_stdout(io.StringIO()) as output:
                    code = main(['list-snapshots', '--config', 'config.toml'] + (['--check-pairs'] if strict else []))
                self.assertEqual(code, int(different and strict))
                logging.assert_not_called()
                self.assertIn('CACHE / DESTINATION COMPARISON', output.getvalue())

    def test_df_unknown_type_preserves_space_when_native_identity_confirms_btrfs(self):
        unknown = {**SPACE, 'fstype': '-', 'device': '-'}
        ops = mock.Mock()
        with mock.patch.object(listing, '_filesystem_space', return_value=unknown):
            result = listing._space_with_btrfs_fallback(ops, '/cache', filesystem_uuid='7346e8a6-c3a5-49e3-887f-3abaa94f63a4')
        ops.run.assert_not_called()
        self.assertEqual(result['fstype'], 'btrfs')
        self.assertEqual(result['available'], SPACE['available'])
        self.assertEqual(unknown['fstype'], '-')
        self.assertIn('type confirmed', result['provider'])

    def test_df_unknown_type_without_identity_uses_existing_btrfs_reader(self):
        ops = mock.Mock()
        ops.run.return_value = Completed(0, 'Device size: 107374182400\nUsed: 80530636800\nFree (statfs, df): 26843545600\n', '')
        with mock.patch.object(listing, '_filesystem_space', return_value={**SPACE, 'fstype': '-'}):
            result = listing._space_with_btrfs_fallback(ops, '/cache')
        self.assertEqual(result['fstype'], 'btrfs')
        self.assertIn('Btrfs filesystem usage', result['provider'])
        ops.run.return_value = Completed(1, '', 'denied')
        with mock.patch.object(listing, '_filesystem_space', return_value={**SPACE, 'fstype': '-'}), self.assertRaisesRegex(RuntimeError, 'type unavailable.*denied'):
            listing._space_with_btrfs_fallback(ops, '/cache')

    def test_partial_native_index_marks_comparison_incomplete(self):
        index = BtrfsIndex('/cache', 'local')
        index.errors.append('date disappeared')
        with mock.patch.object(listing, '_discover_repository', return_value=(index, {}, [], None, 'unavailable')), mock.patch.object(listing, '_scan_unprivileged', return_value={}), mock.patch.object(listing, '_read_listing_metadata'), mock.patch.object(listing, '_filesystem_space', return_value=SPACE):
            section = listing._collect_section(_config(), CommandEndpoint.local(), title='CACHE', location='local', root='/cache', btrfs_command='btrfs')
        self.assertFalse(section.inventory_complete)
        self.assertTrue(section.failed)
