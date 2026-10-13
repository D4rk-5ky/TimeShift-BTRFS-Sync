from __future__ import annotations

import subprocess
import io
import tempfile
from pathlib import Path
from contextlib import redirect_stdout
from unittest.mock import Mock, patch, call
import unittest

from timeshift_btrfs_sync.commands import Completed
from timeshift_btrfs_sync.models import SubvolumeMeta
from timeshift_btrfs_sync import preflight, inventory, sync, timeshift
from timeshift_btrfs_sync.btrfs_ops import BtrfsOps
from timeshift_btrfs_sync.cache_ops import CacheManager
from timeshift_btrfs_sync.endpoint import CommandEndpoint


class FakeSource:
    def __init__(self, result: Completed):
        self._result = result
        self.calls: list[str] = []
        self.uses_ssh = True
        self.location = "remote"

    def run(self, command: str, **_kwargs) -> Completed:
        self.calls.append(command)
        return self._result


def index(root: str, *metas: SubvolumeMeta) -> inventory.BtrfsIndex:
    value = inventory.BtrfsIndex(root=root, location="remote")
    for meta in metas:
        value.add(meta)
    return value


class CombinedInventoryTests(unittest.TestCase):
    def test_build_source_inventory_uses_one_source_command_and_parses_all_sections(self) -> None:
        snapshot_root = "/timeshift/snapshots"
        cache_root = "/timeshift/.ts-btrfs-sync/send-cache"
        snapshot_path = f"{snapshot_root}/2026-07-14_01-00-00/@"
        cache_path = f"{cache_root}/2026-07-14_01-00-00/@"
        output = f"""TSBTRFS_SOURCE_IDENTITY_BEGIN
TSBTRFS_SOURCE_USER_NAME\tbtrbk-source
TSBTRFS_SOURCE_USER_UID\t1001
TSBTRFS_SOURCE_IDENTITY_END
TSBTRFS_TIMESHIFT_BEGIN
TSBTRFS_TIMESHIFT_STATUS\t0
2026-07-14_01-00-00 H hourly
TSBTRFS_TIMESHIFT_END
TSBTRFS_INFO_JSON_BEGIN\t2026-07-14_01-00-00
{{"sys-uuid":"source-root-uuid","tags":"hourly","comments":"","live":"false","type":"btrfs"}}
TSBTRFS_INFO_JSON_END\t2026-07-14_01-00-00\t0
TSBTRFS_INDEX_SECTION_BEGIN\tsnapshot
TSBTRFS_ROOT\t{snapshot_root}
TSBTRFS_ROOT_SHOW_BEGIN
TSBTRFS_ROOT_SHOW_END
TSBTRFS_LIST_BEGIN\t{snapshot_root}
TSBTRFS_LIST_STATUS\t{snapshot_root}\t0
ID 10 gen 1 top level 5 parent_uuid - received_uuid - uuid source-uuid path timeshift/snapshots/2026-07-14_01-00-00/@
TSBTRFS_LIST_END\t{snapshot_root}
TSBTRFS_READONLY_BEGIN\t{snapshot_root}
TSBTRFS_READONLY_STATUS\t{snapshot_root}\t0
ID 10 gen 1 top level 5 path timeshift/snapshots/2026-07-14_01-00-00/@
TSBTRFS_READONLY_END\t{snapshot_root}
TSBTRFS_INDEX_SECTION_END\tsnapshot
TSBTRFS_INDEX_SECTION_BEGIN\tcache
TSBTRFS_ROOT\t{cache_root}
TSBTRFS_ROOT_SHOW_BEGIN
Name: send-cache
UUID: cache-root-uuid
Parent UUID: -
Received UUID: -
Flags: -
TSBTRFS_ROOT_SHOW_END
TSBTRFS_LIST_BEGIN\t{cache_root}
TSBTRFS_LIST_STATUS\t{cache_root}\t0
ID 20 gen 1 top level 5 parent_uuid source-uuid received_uuid - uuid cache-uuid path timeshift/.ts-btrfs-sync/send-cache/2026-07-14_01-00-00/@
TSBTRFS_LIST_END\t{cache_root}
TSBTRFS_READONLY_BEGIN\t{cache_root}
TSBTRFS_READONLY_STATUS\t{cache_root}\t0
ID 20 gen 1 top level 5 path timeshift/.ts-btrfs-sync/send-cache/2026-07-14_01-00-00/@
TSBTRFS_READONLY_END\t{cache_root}
TSBTRFS_INDEX_SECTION_END\tcache
"""
        source = FakeSource(Completed(0, output, ""))

        built_inventory = inventory.build_source_inventory(
            source,
            snapshot_root=snapshot_root,
            cache_root=cache_root,
            sudo="sudo -n",
            btrfs_command="btrfs",
            timeshift_command="timeshift",
        )

        self.assertEqual(len(source.calls), 1)
        self.assertIn("timeshift", source.calls[0])
        self.assertIn(snapshot_root, source.calls[0])
        self.assertIn(cache_root, source.calls[0])
        self.assertIn("cat", source.calls[0])
        self.assertIn("id -un", source.calls[0])
        self.assertIn("id -u", source.calls[0])
        self.assertNotIn("sudo -n cat", source.calls[0])
        self.assertNotIn("sudo -n id", source.calls[0])
        self.assertIn("info.json", source.calls[0])
        self.assertEqual(built_inventory.snapshot_names, ("2026-07-14_01-00-00",))
        self.assertEqual(built_inventory.source_user_name, "btrbk-source")
        self.assertEqual(built_inventory.source_user_uid, 1001)
        self.assertEqual(
            built_inventory.snapshot_info_json["2026-07-14_01-00-00"],
            '{"sys-uuid":"source-root-uuid","tags":"hourly","comments":"","live":"false","type":"btrfs"}',
        )
        self.assertEqual(built_inventory.snapshot_index.meta(snapshot_path).uuid, "source-uuid")
        self.assertTrue(built_inventory.snapshot_index.meta(snapshot_path).readonly)
        self.assertEqual(built_inventory.cache_index.meta(cache_path).uuid, "cache-uuid")
        self.assertTrue(built_inventory.cache_index.meta(cache_path).readonly)


    def test_index_finds_received_copy_by_effective_send_uuid(self) -> None:
        root = "/cache"
        received = SubvolumeMeta(
            "@",
            "/cache/date/@",
            uuid="local-received-uuid",
            received_uuid="original-stream-uuid",
            readonly=True,
        )
        built = index(root, received)

        self.assertIs(built.find_send_uuid("original-stream-uuid"), received)
        self.assertIsNone(built.find_send_uuid("local-received-uuid"))

    def test_unreadable_snapshot_root_is_applied_to_each_missing_info_json(self) -> None:
        output = """TSBTRFS_SOURCE_IDENTITY_BEGIN
TSBTRFS_SOURCE_USER_NAME\tbtrbk-source
TSBTRFS_SOURCE_USER_UID\t1001
TSBTRFS_SOURCE_IDENTITY_END
TSBTRFS_TIMESHIFT_BEGIN
TSBTRFS_TIMESHIFT_STATUS\t0
2026-07-14_01-00-00 H hourly
TSBTRFS_TIMESHIFT_END
TSBTRFS_INFO_ROOT_ERROR\tsnapshot_root does not exist or cannot be traversed by the source user
TSBTRFS_INDEX_SECTION_BEGIN\tsnapshot
TSBTRFS_ROOT\t/timeshift/snapshots
TSBTRFS_ROOT_MISSING\t/timeshift/snapshots
TSBTRFS_INDEX_SECTION_END\tsnapshot
"""
        source = FakeSource(Completed(0, output, ""))
        built_inventory = inventory.build_source_inventory(
            source,
            snapshot_root="/timeshift/snapshots",
            cache_root=None,
            sudo="sudo -n",
            btrfs_command="btrfs",
            timeshift_command="timeshift",
            required=False,
        )
        self.assertEqual(built_inventory.source_user_name, "btrbk-source")
        self.assertEqual(built_inventory.source_user_uid, 1001)
        self.assertIn("cannot be traversed", built_inventory.snapshot_info_errors["2026-07-14_01-00-00"])

    def test_required_path_changes_ignore_unrelated_churn(self) -> None:
        current = "/cache/current/@"
        parent = "/cache/parent/@"
        unrelated = "/snapshots/unrelated/@"
        before = inventory.SourceInventory(
            "2026-07-14_01-00-00 H",
            index("/snapshots", SubvolumeMeta("@", unrelated, uuid="u1")),
            index(
                "/cache",
                SubvolumeMeta("@", current, uuid="c1"),
                SubvolumeMeta("@", parent, uuid="p1"),
            ),
        )
        after = inventory.SourceInventory(
            "2026-07-14_02-00-00 H",
            index("/snapshots"),
            index(
                "/cache",
                SubvolumeMeta("@", current, uuid="c1"),
                SubvolumeMeta("@", parent, uuid="p1"),
            ),
        )
        self.assertEqual(
            sync._required_pipeline_source_changes(
                before,
                after,
                current_path=current,
                parent_path=parent,
            ),
            [],
        )

    def test_required_path_changes_detect_disappearance_and_uuid_replacement(self) -> None:
        current = "/cache/current/@"
        parent = "/cache/parent/@"
        before = inventory.SourceInventory(
            "",
            index("/snapshots"),
            index(
                "/cache",
                SubvolumeMeta("@", current, uuid="c1"),
                SubvolumeMeta("@", parent, uuid="p1"),
            ),
        )
        after = inventory.SourceInventory(
            "",
            index("/snapshots"),
            index("/cache", SubvolumeMeta("@", parent, uuid="p2")),
        )
        changes = sync._required_pipeline_source_changes(
            before,
            after,
            current_path=current,
            parent_path=parent,
        )
        self.assertTrue(any("current send path disappeared" in item for item in changes))
        self.assertTrue(any("incremental parent path UUID changed" in item for item in changes))


class PreflightBatchTests(unittest.TestCase):
    def test_cache_check_runs_only_after_snapshot_ok_inside_one_shell(self) -> None:
        snapshot_ok = "printf 'TSBTRFS_PATH_OK\\tsource.snapshot_root\\t/snapshots\\tok\\n'"
        cache_ok = "printf 'TSBTRFS_PATH_OK\\tsource.cache_root\\t/cache\\tok\\n'"
        script = preflight._combined_source_path_check_script(snapshot_ok, cache_ok, "/cache")
        result = subprocess.run(["sh", "-c", script], text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0)
        self.assertIn("source.snapshot_root", result.stdout)
        self.assertIn("source.cache_root", result.stdout)
        self.assertIn("\tok", result.stdout)

    def test_cache_check_is_skipped_when_snapshot_fails(self) -> None:
        snapshot_fail = "printf 'TSBTRFS_PATH_FAIL\\tsource.snapshot_root\\t/snapshots\\t1\\tbad\\n'"
        cache_should_not_run = "printf 'UNSAFE_CACHE_COMMAND_RAN\\n'"
        script = preflight._combined_source_path_check_script(snapshot_fail, cache_should_not_run, "/cache")
        result = subprocess.run(["sh", "-c", script], text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("UNSAFE_CACHE_COMMAND_RAN", result.stdout)
        self.assertIn("cache storage was not created or modified", result.stdout)


class CacheCreationBatchTests(unittest.TestCase):
    def test_create_and_show_metadata_are_parsed_from_one_source_command(self) -> None:
        output = """TSBTRFS_CACHE_CREATE_STATUS\t0
TSBTRFS_CACHE_CREATE_OUTPUT_BEGIN
Create a readonly snapshot
TSBTRFS_CACHE_CREATE_OUTPUT_END
TSBTRFS_CACHE_SHOW_STATUS\t0
TSBTRFS_CACHE_SHOW_OUTPUT_BEGIN
Name: @
UUID: cache-uuid
Parent UUID: original-uuid
Received UUID: -
Flags: readonly
TSBTRFS_CACHE_SHOW_OUTPUT_END
"""
        source = FakeSource(Completed(0, output, ""))
        manager = CacheManager(
            BtrfsOps(CommandEndpoint.for_source(source), "sudo -n", "btrfs"),
            cache_root="/cache",
            create_enabled=True,
        )
        cache_result = manager._probe_create_verify(
            original=SubvolumeMeta("@", "/snapshots/date/@", uuid="original-uuid"),
            cache_path="/cache/date/@",
            subvolume_name="@",
        )
        self.assertEqual(cache_result.path, "/cache/date/@")
        self.assertTrue(cache_result.readonly)
        self.assertEqual(len(source.calls), 1)
        self.assertEqual(cache_result.uuid, "cache-uuid")
        self.assertEqual(cache_result.parent_uuid, "original-uuid")
        self.assertTrue(cache_result.readonly)


if __name__ == "__main__":
    unittest.main()

class SyncContinuationTests(unittest.TestCase):
    def test_failed_send_rebuilds_inventory_recovers_version_and_continues(self) -> None:
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        from timeshift_btrfs_sync.commands import CommandError
        from timeshift_btrfs_sync.config import load_config

        with tempfile.TemporaryDirectory() as tmp:
            config = load_config("timeshift_btrfs_sync/data/config.example.toml")
            config.source.subvolumes = ["@"]
            config.source.snapshot_root = "/snapshots"
            config.source.cache_root = "/cache"
            config.source.verify_subvolumes_at_discovery = True
            config.source.source_change_retry_count = 2
            config.manual_snapshot.enabled = False
            config.destination.target_root = Path(tmp) / "target"
            (config.destination.target_root / "snapshots").mkdir(parents=True)
            config.state_file = Path(tmp) / "state.json"

            source_path = "/snapshots/2026-07-14_01-00-00/@"
            initial = inventory.SourceInventory(
                "2026-07-14_01-00-00 H",
                index("/snapshots", SubvolumeMeta("@", source_path, uuid="source-uuid", readonly=True)),
                index("/cache"),
                {"2026-07-14_01-00-00": '{"tags":"hourly","type":"btrfs"}\n'},
            )
            after_failure = inventory.SourceInventory("", index("/snapshots"), index("/cache"))
            after_cleanup = inventory.SourceInventory("", index("/snapshots"), index("/cache"))

            class SyncSource:
                uses_ssh = False
                location = "local"

                def command(self, source_shell_command: str):
                    return ["sh", "-c", source_shell_command]

                def environment(self):
                    return None

                def run(self, shell_command, **kwargs):
                    # Exact re-probe confirms the disappeared source without real Btrfs.
                    return Completed(1, "", "No such file or directory")

            recovered: list[str] = []
            pipeline_error = CommandError(["btrfs", "send"], 1, "", "source vanished")
            empty_destination_index = inventory.BtrfsIndex(str(config.destination.target_root), "local")

            with (
                patch.object(sync.SourceRunner, "from_config", return_value=SyncSource()),
                patch.object(sync.preflight, "check_required_sync_paths"),
                patch.object(sync, "prepare_destination"),
                patch.object(sync.inventory, "build_source_inventory", side_effect=[initial, after_failure, after_cleanup]),
                patch.object(sync.inventory, "build_local_btrfs_index", return_value=empty_destination_index),
                patch.object(sync, "_recover_stale_state_snapshots_missing_from_source", return_value=0),
                patch.object(sync, "_verify_sync_viability_before_manual_snapshot"),
                patch.object(sync, "_maybe_create_manual_snapshot", return_value=False),
                patch.object(sync, "refresh_state_metadata_and_report", return_value=0),
                patch.object(sync, "_select_parent", return_value=(None, None)),
                patch.object(sync, "_ensure_source_send_path", return_value=source_path),
                patch.object(sync, "_ensure_destination_snapshot_subvolume", return_value=config.destination.target_root / "snapshots" / "2026-07-14_01-00-00"),
                patch.object(sync, "stream_pipeline", side_effect=pipeline_error),
                patch.object(sync, "_recover_snapshot_version", side_effect=lambda *_a, **kw: recovered.append(kw["reason"])),
            ):
                transferred = sync.sync_once(config, {}, dry_run=False)

            self.assertEqual(transferred.transferred, 0)
            self.assertEqual(len(recovered), 1)
            self.assertIn("current send path disappeared", recovered[0])


if __name__ == "__main__":
    unittest.main()


BUSY = "Another instance of this application is running (PID=2784388)"


def wait_inventory_reply(status: int, listing: str, *, rows=()) -> Completed:
    """Model the real remote inventory protocol with independently dated UUIDs."""
    text = "TSBTRFS_TIMESHIFT_BEGIN\nTSBTRFS_TIMESHIFT_STATUS\t" + str(status) + "\n" + listing + "\nTSBTRFS_TIMESHIFT_END\n"
    for name, tags in rows:
        text += f'TSBTRFS_INFO_JSON_BEGIN\t{name}\n{{"tags":"{tags}","type":"btrfs"}}\nTSBTRFS_INFO_JSON_END\t{name}\t0\n'
    for label, root in (("snapshot", "/snapshots"), ("cache", "/cache")):
        text += f"TSBTRFS_INDEX_SECTION_BEGIN\t{label}\nTSBTRFS_ROOT\t{root}\nTSBTRFS_ROOT_SHOW_BEGIN\n"
        text += f"UUID: {label}-root\nParent UUID: -\nReceived UUID: -\nFlags: -\nTSBTRFS_ROOT_SHOW_END\n"
        text += f"TSBTRFS_LIST_BEGIN\t{root}\nTSBTRFS_LIST_STATUS\t{root}\t0\n"
        for num, (name, _tags) in enumerate(rows, 30):
            text += f"ID {num} gen 1 top level 5 parent_uuid - received_uuid - uuid {label}-{name} path {root.lstrip('/')}/{name}/@\n"
        text += f"TSBTRFS_LIST_END\t{root}\nTSBTRFS_READONLY_BEGIN\t{root}\nTSBTRFS_READONLY_STATUS\t{root}\t0\n"
        for num, (name, _tags) in enumerate(rows, 30):
            text += f"ID {num} gen 1 top level 5 path {root.lstrip('/')}/{name}/@\n"
        text += f"TSBTRFS_READONLY_END\t{root}\nTSBTRFS_INDEX_SECTION_END\t{label}\n"
    return Completed(0, text, "")


class TimeshiftWaitTests(unittest.TestCase):
    def test_startup_denial_recognized_in_either_stream_with_color_and_timestamp(self):
        for stdout, stderr in ((BUSY, ""), ("", BUSY), ("[12:00:00] \x1b[31m" + BUSY + "\x1b[0m", "")):
            with self.subTest(stdout=stdout, stderr=stderr):
                with self.assertRaises(timeshift.TimeshiftBusyError) as caught:
                    timeshift.raise_if_timeshift_busy(1, stdout, stderr)
                self.assertEqual(caught.exception.pid, "2784388")

    def test_success_and_transport_exit_codes_never_classified_as_busy(self):
        for code in (0, 2, 127, 255, -15):
            timeshift.raise_if_timeshift_busy(code, BUSY, BUSY)

    def test_unrelated_busy_messages_and_missing_pid_do_not_retry(self):
        for text in ("device or resource busy", "Another instance of this application is running", "sudo: a password is required", "No space left on device", "Permission denied"):
            timeshift.raise_if_timeshift_busy(1, text, "")

    def test_multiple_polls_are_exactly_one_minute_and_log_resume(self):
        operation = Mock(side_effect=[timeshift.TimeshiftBusyError("12"), timeshift.TimeshiftBusyError("34"), "fresh"])
        with patch.object(timeshift.time, "sleep") as sleep, redirect_stdout(io.StringIO()) as output:
            result = timeshift.wait_for_timeshift(operation, label="Source inventory")
        self.assertEqual(result, "fresh")
        self.assertEqual(sleep.call_args_list, [call(60), call(60)])
        self.assertEqual(operation.call_count, 3)
        self.assertIn("PID=34", output.getvalue())
        self.assertIn("fresh results", output.getvalue())

    def test_ctrl_c_during_wait_propagates_without_retry(self):
        operation = Mock(side_effect=timeshift.TimeshiftBusyError("12"))
        with patch.object(timeshift.time, "sleep", side_effect=KeyboardInterrupt), redirect_stdout(io.StringIO()):
            with self.assertRaises(KeyboardInterrupt):
                timeshift.wait_for_timeshift(operation, label="Source inventory")
        self.assertEqual(operation.call_count, 1)

    def test_different_failure_after_busy_stops_immediately(self):
        operation = Mock(side_effect=[timeshift.TimeshiftBusyError("12"), RuntimeError("network failed")])
        with patch.object(timeshift.time, "sleep") as sleep, redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(RuntimeError, "network failed"):
                timeshift.wait_for_timeshift(operation, label="Source inventory")
        sleep.assert_called_once_with(60)
        self.assertEqual(operation.call_count, 2)

    def build(self, source, required=True):
        return inventory.build_source_inventory(source, snapshot_root="/snapshots", cache_root="/cache", sudo="sudo -n", btrfs_command="btrfs", timeshift_command="timeshift", required=required)

    def test_ssh_discards_busy_inventory_and_refreshes_dates_tags_json_and_uuid(self):
        old = "2026-10-12_11-00-00"
        kept = "2026-10-12_12-00-00"
        new = "2026-10-12_13-00-00"
        stale = wait_inventory_reply(1, BUSY, rows=((old, "hourly"), (kept, "hourly")))
        fresh = wait_inventory_reply(0, f"{kept} D W M B changed\n{new} H new", rows=((kept, "daily weekly monthly boot"), (new, "hourly")))
        source = FakeSource(stale)
        source.run = Mock(side_effect=[stale, stale, fresh])
        with patch.object(timeshift.time, "sleep") as sleep, redirect_stdout(io.StringIO()):
            built = self.build(source)
        self.assertEqual(sleep.call_args_list, [call(60), call(60)])
        self.assertEqual(source.run.call_count, 3)
        self.assertEqual(source.run.call_args_list[0], source.run.call_args_list[-1])
        self.assertEqual(built.snapshot_names, (kept, new))
        self.assertNotIn(old, built.snapshot_info_json)
        self.assertNotIn(f"/cache/{old}/@", built.cache_index.by_path)
        self.assertIn("monthly", built.snapshot_info_json[kept])
        self.assertEqual(built.snapshot_index.meta(f"/snapshots/{new}/@").uuid, "snapshot-" + new)
        from timeshift_btrfs_sync.config import load_config
        config = load_config("timeshift_btrfs_sync/data/config.example.toml")
        config.source.snapshot_root = "/snapshots"
        config.source.subvolumes = ["@"]
        config.source.verify_subvolumes_at_discovery = True
        config.retention.hourly = 1
        config.retention.daily = 1
        source_by_name = sync._snapshots_from_source_inventory(config, source, built)
        self.assertEqual(source_by_name[kept].tags, ["D", "W", "M", "B"])
        with redirect_stdout(io.StringIO()):
            selected = sync._select_initial_sync_snapshots(config, source_by_name)
        self.assertEqual([item.name for item in selected], [kept, new])
        self.assertEqual(source.run.call_count, 3, "planning must use fresh captured output, not an extra stale Timeshift query")

    def test_optional_ssh_inventory_still_waits_for_known_busy(self):
        source = FakeSource(Completed(0, "", ""))
        source.run = Mock(side_effect=[wait_inventory_reply(1, BUSY), wait_inventory_reply(0, "")])
        with patch.object(timeshift.time, "sleep") as sleep, redirect_stdout(io.StringIO()):
            self.assertEqual(self.build(source, required=False).snapshot_names, ())
        sleep.assert_called_once_with(60)

    def test_ssh_transport_error_is_fatal_even_if_old_busy_text_is_present(self):
        source = FakeSource(Completed(255, wait_inventory_reply(1, BUSY).stdout, "Connection reset"))
        with patch.object(timeshift.time, "sleep") as sleep:
            with self.assertRaisesRegex(RuntimeError, "SSH command failed: Connection reset"):
                self.build(source)
        sleep.assert_not_called()
        self.assertEqual(len(source.calls), 1)

    def test_ssh_other_timeshift_error_is_fatal_without_polling(self):
        source = FakeSource(wait_inventory_reply(1, "sudo: a password is required"))
        with patch.object(timeshift.time, "sleep") as sleep:
            with self.assertRaisesRegex(RuntimeError, "password is required"):
                self.build(source)
        sleep.assert_not_called()

    def test_ssh_busy_then_permission_error_does_not_use_the_old_index(self):
        source = FakeSource(Completed(0, "", ""))
        source.run = Mock(side_effect=[wait_inventory_reply(1, BUSY), wait_inventory_reply(1, "permission denied")])
        with patch.object(timeshift.time, "sleep") as sleep, patch.object(inventory, "_parse_remote_btrfs_index_result") as parse, redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(RuntimeError, "permission denied"):
                self.build(source)
        sleep.assert_called_once_with(60)
        parse.assert_not_called()

    def test_local_reads_native_metadata_only_after_timeshift_becomes_available(self):
        source = Mock(uses_ssh=False)
        source.run.side_effect = [Completed(1, "", BUSY), Completed(0, "2026-10-12_13-00-00 H new", "")]
        events = []
        with patch.object(timeshift.time, "sleep", side_effect=lambda seconds: events.append(("wait", seconds))), patch.object(inventory, "build_local_btrfs_index", side_effect=lambda root, **kwargs: events.append(("index", root)) or index(root)), patch.object(inventory, "_read_local_snapshot_info_json", side_effect=lambda root: events.append(("json", root)) or ({}, {})), redirect_stdout(io.StringIO()):
            built = self.build(source)
        self.assertEqual(events, [("wait", 60), ("index", "/snapshots"), ("index", "/cache"), ("json", "/snapshots")])
        self.assertEqual(built.snapshot_names, ("2026-10-12_13-00-00",))
        self.assertFalse(source.run.call_args.kwargs["check"])
        self.assertFalse(source.run.call_args.kwargs["log_stderr"])

    def test_local_nonbusy_error_never_reads_native_metadata_or_sleeps(self):
        source = Mock(uses_ssh=False)
        source.run.return_value = Completed(1, "", "permission denied")
        with patch.object(timeshift.time, "sleep") as sleep, patch.object(inventory, "build_local_btrfs_index") as native:
            with self.assertRaisesRegex(RuntimeError, "permission denied"):
                self.build(source)
        sleep.assert_not_called()
        native.assert_not_called()

    def test_local_interrupt_does_not_read_native_metadata(self):
        source = Mock(uses_ssh=False)
        source.run.return_value = Completed(1, BUSY, "")
        with patch.object(timeshift.time, "sleep", side_effect=KeyboardInterrupt), patch.object(inventory, "build_local_btrfs_index") as native, redirect_stdout(io.StringIO()):
            with self.assertRaises(KeyboardInterrupt):
                self.build(source)
        self.assertEqual(source.run.call_count, 1)
        native.assert_not_called()

    def test_single_list_command_waits_and_parses_only_new_output(self):
        source = Mock()
        source.run.side_effect = [Completed(1, BUSY, ""), Completed(0, "2026-10-12_13-00-00 H", "")]
        with patch.object(timeshift.time, "sleep") as sleep, redirect_stdout(io.StringIO()):
            snapshots = timeshift.list_source_snapshots(source, snapshot_root="/snapshots", subvolumes=["@"], sudo="sudo -n", timeshift_command="timeshift", btrfs_command="btrfs", include_btrfs_info=False)
        sleep.assert_called_once_with(60)
        self.assertEqual([snap.name for snap in snapshots], ["2026-10-12_13-00-00"])
        self.assertTrue(all("--list" in args.args[0] for args in source.run.call_args_list))

    def test_on_demand_create_retries_only_startup_denial(self):
        source = Mock()
        source.run.side_effect = [Completed(1, BUSY, ""), Completed(0, "snapshot created", "")]
        with patch.object(timeshift.time, "sleep") as sleep, redirect_stdout(io.StringIO()):
            timeshift.create_source_manual_snapshot(source, sudo="sudo -n", timeshift_command="timeshift", comment="app marker")
        sleep.assert_called_once_with(60)
        self.assertEqual(source.run.call_count, 2)
        self.assertEqual(source.run.call_args_list[0], source.run.call_args_list[1])
        self.assertIn("--create --scripted --comments", source.run.call_args.args[0])

    def test_on_demand_create_other_failure_is_not_repeated(self):
        source = Mock()
        source.run.return_value = Completed(1, "partial snapshot", "No space left on device")
        with patch.object(timeshift.time, "sleep") as sleep:
            with self.assertRaisesRegex(RuntimeError, "No space left on device"):
                timeshift.create_source_manual_snapshot(source, sudo="sudo -n", timeshift_command="timeshift", comment="app marker")
        sleep.assert_not_called()
        self.assertEqual(source.run.call_count, 1)

    def test_actual_sync_dry_planner_runs_after_wait_with_only_refreshed_dates(self):
        from timeshift_btrfs_sync.config import load_config
        old = "2026-10-12_11-00-00"
        kept = "2026-10-12_12-00-00"
        new = "2026-10-12_13-00-00"
        source = FakeSource(Completed(0, "", ""))
        source.test = Mock()
        source.run = Mock(side_effect=[
            wait_inventory_reply(1, BUSY, rows=((old, "hourly"),)),
            wait_inventory_reply(0, f"{kept} D W M B refreshed\n{new} H new", rows=((kept, "daily weekly monthly boot"), (new, "hourly"))),
        ])
        with tempfile.TemporaryDirectory() as tmp:
            config = load_config("timeshift_btrfs_sync/data/config.example.toml")
            config.source.snapshot_root = "/snapshots"
            config.source.cache_root = "/cache"
            config.source.subvolumes = ["@"]
            config.source.verify_subvolumes_at_discovery = True
            config.source.source_change_retry_count = 0
            config.manual_snapshot.enabled = False
            config.destination.target_root = Path(tmp) / "target"
            config.state_file = Path(tmp) / "state.json"
            empty_destination = inventory.BtrfsIndex(str(config.destination.target_root / "snapshots"), "local")
            with patch.object(sync.SourceRunner, "from_config", return_value=source), patch.object(sync.preflight, "check_required_sync_paths"), patch.object(sync.inventory, "build_local_btrfs_index", return_value=empty_destination), patch.object(sync, "_recover_stale_state_snapshots_missing_from_source", return_value=0), patch.object(sync, "_verify_sync_viability_before_manual_snapshot"), patch.object(sync, "_maybe_create_manual_snapshot", return_value=False), patch.object(sync, "refresh_state_metadata_and_report", return_value=0), patch.object(sync, "_select_parent", return_value=(None, None)), patch.object(timeshift.time, "sleep") as sleep, patch.object(sync, "stream_pipeline") as pipeline, redirect_stdout(io.StringIO()) as output:
                result = sync.sync_once(config, {}, dry_run=True)
            sleep.assert_called_once_with(60)
            pipeline.assert_not_called()
            self.assertFalse(config.state_file.exists())
            self.assertFalse(config.destination.target_root.exists())
        self.assertEqual([item["snapshot"] for item in result.events], [kept, new])
        self.assertEqual(result.events[0]["tags"], "D W M B")
        self.assertEqual(result.events[1]["tags"], "H")
        self.assertNotIn(old, output.getvalue())
        self.assertEqual(source.run.call_count, 2)

    def test_cli_busy_interrupt_returns_130(self):
        from timeshift_btrfs_sync import cli
        source = Mock(uses_ssh=False)
        source.run.return_value = Completed(1, BUSY, "")
        with patch.object(cli.SourceRunner, "from_config", return_value=source), patch.object(cli, "_with_logging", side_effect=lambda _config, _label, action: action()), patch.object(timeshift.time, "sleep", side_effect=KeyboardInterrupt), redirect_stdout(io.StringIO()) as output:
            result = cli.main(["test-source", "--config", "timeshift_btrfs_sync/data/example-config-local-backup.toml"])
        self.assertEqual(result, 130)
        self.assertIn("Waiting 60 seconds", output.getvalue())
        self.assertEqual(source.run.call_count, 1)

    def test_combined_destructive_delete_verification_is_never_replayed(self):
        from timeshift_btrfs_sync.commands import CommandError
        source = Mock()
        source.run.side_effect = CommandError("delete then list", 1, timeshift.DELETE_VERIFY_MARKER + "\n" + BUSY)
        with patch.object(timeshift.time, "sleep") as sleep:
            with self.assertRaises(CommandError):
                timeshift.delete_source_manual_snapshot(source, snapshot_root="/snapshots", sudo="sudo -n", timeshift_command="timeshift", snapshot_name="2026-10-12_12-00-00")
        sleep.assert_not_called()
        self.assertEqual(source.run.call_count, 1)
