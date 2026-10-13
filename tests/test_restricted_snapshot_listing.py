"""Restricted sudo discovery and truthful metadata fallbacks for service accounts."""

from unittest import TestCase, mock
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
import base64

from timeshift_btrfs_sync import listing
from timeshift_btrfs_sync.btrfs_ops import BtrfsOps
from timeshift_btrfs_sync.commands import Completed
from timeshift_btrfs_sync.endpoint import CommandEndpoint
from timeshift_btrfs_sync.inventory import BtrfsIndex
from timeshift_btrfs_sync.models import SubvolumeMeta
from timeshift_btrfs_sync.restore import BackupDirectoryRecord
from test_manual_snapshot_retention import _config
from test_snapshot_listing import NAME, SPACE


UUID = "7346e8a6-c3a5-49e3-887f-3abaa94f63a4"
TS = f"UUID : {UUID}\nNum Name Tags Description\n0 > {NAME} H D W M scheduled snapshot\n"


def _row(*, metadata: bool = False, receiver: bool = False):
    """Build a two-payload observed date with exact source/received stream identities."""

    row = listing.SnapshotListingRow(NAME, "W M" if metadata else "?", "known snapshot" if metadata else "", verified=True, complete=True, metadata_origin="info.json" if metadata else "?")
    for payload in ("@", "@home"):
        row.subvolumes[payload] = SubvolumeMeta(payload, f"/repo/{NAME}/{payload}", uuid=f"{'dest' if receiver else 'cache'}-{payload}", received_uuid=f"cache-{payload}" if receiver else None, readonly=True)
        row.payloads.append(f"{payload}:ro")
    return row


class RestrictedSnapshotListingTests(TestCase):
    """Check the user's Btrfs/Timeshift-only sudo model without requiring a root login."""

    def test_timeshift_is_primary_only_for_originals(self):
        """Current Timeshift tags replace source observations while own cache/target tags stay independent."""

        originals = listing.SnapshotListingSection("TIMESHIFT", "local", "/source", [_row(metadata=True)], filesystem_uuid=UUID)
        cache = listing.SnapshotListingSection("CACHE", "local", "/cache", [_row(metadata=True)])
        target = listing.SnapshotListingSection("TARGET", "local", "/target", [_row(metadata=True, receiver=True)])
        cache.rows[0].tags = "O H"
        self._collect(originals, cache, target)
        self.assertEqual([section.rows[0].tags for section in (originals, cache, target)], ["H D W M", "O H", "W M"])
        self.assertEqual(originals.rows[0].metadata_origin, "Timeshift --list")
        self.assertEqual(cache.rows[0].metadata_origin, "info.json")
        self.assertEqual(target.rows[0].metadata_origin, "info.json")

    def test_source_metadata_reads_skip_only_compatible_timeshift_names(self):
        """Avoid rereading known source JSON, but retain ordinary reads for omitted dates or a mismatched root."""

        omitted = "2026-10-11_12-25-36"
        for observed_uuid, expected in ((UUID, frozenset({NAME})), ("other-filesystem", frozenset())):
            records = {name: BackupDirectoryRecord(name, "directory", {}, None) for name in (NAME, omitted)}
            with mock.patch.object(listing, "_discover_repository", return_value=(BtrfsIndex("/source", "local"), records, [], observed_uuid, "device")), mock.patch.object(listing, "_scan_unprivileged", return_value={}) as scan, mock.patch.object(listing, "_read_listing_metadata") as read, mock.patch.object(listing, "_filesystem_space", return_value=SPACE):
                listing._collect_section(_config(), CommandEndpoint.local(), title="TIMESHIFT", location="local", root="/source", btrfs_command="btrfs", timeshift_names=frozenset({NAME}), timeshift_filesystem_uuid=UUID)
            self.assertFalse(scan.call_args.kwargs["read_info"])
            self.assertEqual(read.call_args.kwargs["skip_names"], expected)

    def test_failed_ordinary_scan_still_skips_known_source_json(self):
        """A Btrfs-only physical inventory does not trigger redundant reads of Timeshift-supplied JSON."""

        records = {NAME: BackupDirectoryRecord(NAME, "directory", {}, None)}
        with mock.patch.object(listing, "_discover_repository", return_value=(BtrfsIndex("/source", "local"), records, [], UUID, "device")), mock.patch.object(listing, "_scan_unprivileged", side_effect=RuntimeError("directory unavailable")), mock.patch.object(listing, "_read_listing_metadata") as read, mock.patch.object(listing, "_filesystem_space", return_value=SPACE):
            listing._collect_section(_config(), CommandEndpoint.local(), title="TIMESHIFT", location="local", root="/source", btrfs_command="btrfs", timeshift_names=frozenset({NAME}), timeshift_filesystem_uuid=UUID)
        self.assertEqual(read.call_args.kwargs["skip_names"], frozenset({NAME}))

    def test_ordinary_json_fallback_reads_only_unlisted_dates(self):
        """Read omitted-date metadata as the login user without opening the known date's file."""

        omitted = "2026-10-11_12-25-36"
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name in (NAME, omitted):
                (root / name).mkdir()
                (root / name / "info.json").write_text('{"tags":"weekly monthly","comments":"ordinary JSON"}')
            records = {name: BackupDirectoryRecord(name, "directory", {}, None) for name in (NAME, omitted)}
            endpoint = CommandEndpoint.local()
            with mock.patch.object(CommandEndpoint, "run_shell", wraps=endpoint.run_shell) as run:
                listing._read_listing_metadata(endpoint, str(root), records, skip_names=frozenset({NAME}))
            self.assertIsNone(records[NAME].info_content)
            self.assertEqual(listing._snapshot_description(records[omitted])[:2], ("W M", "ordinary JSON"))
            script = run.call_args.args[0]
            self.assertNotIn("sudo", script)
            self.assertNotIn(str(root / NAME / "info.json"), script)

    def test_skipping_source_json_preserves_restore_scanner_default(self):
        """Listing can skip file contents while restore's default still reads the original JSON and entries."""

        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / NAME / "@").mkdir(parents=True)
            (root / NAME / "info.json").write_text('{"tags":"daily","comments":"restore default"}')
            endpoint = CommandEndpoint.local()
            normal = listing._scan_snapshot_directories(endpoint, str(root), location_label="fixture", privilege_prefix=[])
            listing_only = listing._scan_unprivileged(endpoint, str(root), "fixture", read_info=False)
            self.assertEqual(normal[NAME].entries, listing_only[NAME].entries)
            self.assertEqual(listing._snapshot_description(normal[NAME])[:2], ("D", "restore default"))
            self.assertIsNone(listing_only[NAME].info_content)

    def _collect(self, originals, cache, target, *, output: Completed | None = None):
        """Isolate transport reads while retaining the real merge, proof and table ordering."""

        sections = [originals, cache, target]
        with mock.patch.object(listing, "_collect_section", side_effect=sections), mock.patch.object(listing, "_run_batched_commands", return_value={0: output or Completed(0, TS, "")}) as run:
            workflow, result = listing.collect_snapshot_listings(_config())
        command = run.call_args.args[1][0]
        self.assertEqual(command, ["sudo", "-n", "timeshift", "--list"])
        return workflow, result

    def test_default_order_and_timeshift_metadata_survive_denied_json(self):
        originals = listing.SnapshotListingSection("TIMESHIFT SNAPSHOTS", "local", "/source", [_row()], filesystem_uuid=UUID)
        cache = listing.SnapshotListingSection("CACHE_ROOT SNAPSHOTS", "local", "/cache", [_row()])
        target = listing.SnapshotListingSection("TARGET_ROOT SNAPSHOTS", "local", "/target", [_row(receiver=True)])
        workflow, sections = self._collect(originals, cache, target)
        self.assertEqual(sections, [originals, cache, target])
        self.assertEqual(originals.rows[0].tags, "H D W M")
        self.assertEqual(cache.rows[0].tags, "H D W M")
        self.assertEqual(target.rows[0].tags, "H D W M")
        self.assertEqual(originals.rows[0].metadata_origin, "Timeshift --list")
        self.assertIn("UUIDs", target.rows[0].metadata_origin)
        text = listing.format_snapshot_listings(workflow, sections)
        self.assertLess(text.index("TIMESHIFT SNAPSHOTS"), text.index("CACHE_ROOT SNAPSHOTS"))
        self.assertLess(text.index("CACHE_ROOT SNAPSHOTS"), text.index("TARGET_ROOT SNAPSHOTS"))

    def test_timeshift_failure_keeps_physical_rows_and_other_sides(self):
        originals = listing.SnapshotListingSection("TIMESHIFT", "local", "/source", [_row(metadata=True)])
        cache = listing.SnapshotListingSection("CACHE", "local", "/cache")
        target = listing.SnapshotListingSection("TARGET", "local", "/target")
        _workflow, result = self._collect(originals, cache, target, output=Completed(1, "", "sudo denied"))
        self.assertEqual(len(result), 3)
        self.assertTrue(result[0].failed)
        self.assertEqual(result[0].rows[0].tags, "W M")
        self.assertIn("sudo denied", " ".join(result[0].notes))

    def test_wrong_timeshift_filesystem_cannot_supply_tags(self):
        originals = listing.SnapshotListingSection("TIMESHIFT", "local", "/source", [_row()], filesystem_uuid="11111111-1111-1111-1111-111111111111")
        cache = listing.SnapshotListingSection("CACHE", "local", "/cache", [_row()])
        target = listing.SnapshotListingSection("TARGET", "local", "/target", [_row(receiver=True)])
        _workflow, result = self._collect(originals, cache, target)
        self.assertTrue(result[0].failed)
        self.assertEqual([section.rows[0].tags for section in result], ["?", "?", "?"])

    def test_expired_original_cache_uses_verified_target_metadata(self):
        originals = listing.SnapshotListingSection("TIMESHIFT", "local", "/source")
        cache = listing.SnapshotListingSection("CACHE", "local", "/cache", [_row()])
        target = listing.SnapshotListingSection("TARGET", "local", "/target", [_row(metadata=True, receiver=True)])
        self._collect(originals, cache, target, output=Completed(0, "0 snapshots", ""))
        self.assertEqual(cache.rows[0].tags, "W M")
        self.assertIn("UUIDs", cache.rows[0].metadata_origin)
        self.assertEqual(originals.rows, [])

    def test_mismatch_missing_or_writable_sibling_blocks_metadata_borrowing(self):
        for problem in ("uuid", "missing", "writable"):
            originals = listing.SnapshotListingSection("TIMESHIFT", "local", "/source")
            cache = listing.SnapshotListingSection("CACHE", "local", "/cache", [_row()])
            target_row = _row(metadata=True, receiver=True)
            if problem == "uuid":
                target_row.subvolumes["@home"].received_uuid = "other-stream"
            elif problem == "missing":
                target_row.subvolumes.pop("@home")
            else:
                target_row.subvolumes["@home"].readonly = False
            target = listing.SnapshotListingSection("TARGET", "local", "/target", [target_row])
            self._collect(originals, cache, target, output=Completed(0, "0 snapshots", ""))
            self.assertEqual(cache.rows[0].tags, "?", problem)

    def test_btrfs_discovery_queries_nested_date_containers_with_only_approved_commands(self):
        endpoint = CommandEndpoint.local()
        ops = BtrfsOps(endpoint, sudo="sudo -n", command_name="/usr/bin/btrfs")
        def batches(_endpoint, commands):
            """Simulate root-only enumeration and second-level readonly payloads."""
            for command in commands:
                self.assertEqual(command[:3], ["sudo", "-n", "/usr/bin/btrfs"])
                self.assertNotIn("sh", command)
                self.assertNotIn("cat", command)
                self.assertNotIn("ls", command)
            if len(commands) == 3:
                return {0: Completed(0, f"ID 500 gen 1 top level 5 uuid date-uuid path cache/{NAME}\n", ""), 1: Completed(0, "", ""), 2: Completed(0, f"Label: none uuid: {UUID}\n  devid 1 size 100 used 90 path /dev/sda2\n", "")}
            root = commands[0][-1]
            self.assertEqual(root, f"/cache/{NAME}")
            text = "".join(f"ID {501+i} gen 1 top level 500 uuid cache-{payload} path cache/{NAME}/{payload}\n" for i, payload in enumerate(("@", "@home")))
            return {0: Completed(0, text, ""), 1: Completed(0, text, "")}
        with mock.patch.object(listing, "_run_batched_commands", side_effect=batches):
            index, records, _notes, uuid, device = listing._discover_repository(ops, "/cache")
        self.assertEqual(uuid, UUID)
        self.assertEqual(device, "/dev/sda2")
        self.assertEqual(set(records[NAME].entries), {"@", "@home"})
        self.assertTrue(index.meta(f"/cache/{NAME}/@home").readonly)

    def test_denied_ls_does_not_prevent_complete_btrfs_inventory(self):
        index = BtrfsIndex("/cache", "local")
        row = _row()
        for payload, meta in row.subvolumes.items():
            meta.path = f"/cache/{NAME}/{payload}"
            index.add(meta)
        records = {NAME: BackupDirectoryRecord(NAME, "directory", {"@": "directory", "@home": "directory"}, None)}
        with mock.patch.object(listing, "_discover_repository", return_value=(index, records, [], UUID, "/dev/sda2")), mock.patch.object(listing, "_scan_unprivileged", side_effect=RuntimeError("ls denied")), mock.patch.object(listing, "_read_listing_metadata"), mock.patch.object(listing, "_filesystem_space", return_value=SPACE):
            section = listing._collect_section(_config(), CommandEndpoint.local(), title="CACHE", location="local", root="/cache", btrfs_command="btrfs", sudo="sudo -n")
        self.assertFalse(section.failed)
        self.assertTrue(section.rows[0].complete)
        self.assertEqual(section.rows[0].tags, "?")
        self.assertIn("ls denied", " ".join(section.notes))

    def test_failed_date_query_retains_other_dates_and_reports_partial_inventory(self):
        old_name = "2026-10-11_12-25-36"
        def batches(_endpoint, commands):
            """Simulate one vanished date without losing a different successful date."""
            if len(commands) == 3:
                text = "".join(f"ID {500+i} gen 1 top level 5 uuid date-{i} path cache/{name}\n" for i, name in enumerate((old_name, NAME)))
                return {0: Completed(0, text, ""), 1: Completed(0, "", ""), 2: Completed(0, "", "")}
            output = {}
            for i, command in enumerate(commands):
                name = PurePosixPath(command[-1]).name
                text = f"ID 505 gen 1 top level 500 uuid cache-root path cache/{name}/@\n"
                output[i] = Completed(1, "date disappeared", "") if name == old_name else Completed(0, text, "")
            return output
        with mock.patch.object(listing, "_run_batched_commands", side_effect=batches):
            index, records, _notes, _uuid, _device = listing._discover_repository(BtrfsOps(CommandEndpoint.local()), "/cache")
        self.assertIn(old_name, records)
        self.assertIn("@", records[NAME].entries)
        self.assertTrue(index.errors)

    def test_df_denial_falls_back_to_sudo_btrfs_usage(self):
        ops = mock.Mock()
        ops.run.return_value = Completed(0, "Device size: 107374182400\nUsed: 80530636800\nFree (statfs, df): 26843545600\n", "")
        with mock.patch.object(listing, "_filesystem_space", side_effect=RuntimeError("df path permission denied")):
            space = listing._space_with_btrfs_fallback(ops, "/protected/cache", device="/dev/sda2")
        self.assertIn("25.00 GiB", space["available"])
        self.assertIn("statfs", space["provider"])
        self.assertEqual(ops.run.call_args.args[0], ["filesystem", "usage", "-b", "/protected/cache"])
        ops.run.return_value = Completed(0, "Device size: 107374182400\nUsed: 80530636800\nFree (estimated): 26843545600 (min: 21474836480)\n", "")
        with mock.patch.object(listing, "_filesystem_space", side_effect=RuntimeError("denied")):
            space = listing._space_with_btrfs_fallback(ops, "/protected/cache")
        self.assertIn("20.00 GiB", space["available"])
        self.assertIn("estimated", space["provider"])

    def test_json_reads_are_unprivileged_and_refuse_symlinks(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / NAME).mkdir()
            info = root / NAME / "info.json"
            info.write_text('{"tags":"weekly monthly","comments":"read-only fixture"}')
            records = {NAME: BackupDirectoryRecord(NAME, "directory", {}, None)}
            listing._read_listing_metadata(CommandEndpoint.local(), str(root), records)
            self.assertEqual(listing._snapshot_description(records[NAME])[:2], ("W M", "read-only fixture"))
            info.unlink()
            secret = root / "other.json"
            secret.write_text('{"tags":"daily"}')
            info.symlink_to(secret)
            records[NAME].info_content = None
            listing._read_listing_metadata(CommandEndpoint.local(), str(root), records)
            self.assertIsNone(records[NAME].info_content)

    def test_unconfirmed_timeshift_dates_are_visible_and_not_counted_as_verified(self):
        originals = listing.SnapshotListingSection("TIMESHIFT", "local", "/source")
        _workflow, result = self._collect(originals, listing.SnapshotListingSection("CACHE", "local", None), listing.SnapshotListingSection("TARGET", "local", "/target"))
        self.assertEqual(result[0].rows[0].name, NAME)
        self.assertFalse(result[0].rows[0].verified)
        self.assertTrue(result[0].failed)
