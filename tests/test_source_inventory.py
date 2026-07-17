from __future__ import annotations

import subprocess
import unittest

from timeshift_btrfs_sync.commands import Completed
from timeshift_btrfs_sync.models import SubvolumeMeta
from timeshift_btrfs_sync import preflight, inventory, sync
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
{{"date":"2026-07-14_01-00-00","tags":["H"]}}
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
        source = FakeSource(Completed("inventory", 0, output, ""))

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
            '{"date":"2026-07-14_01-00-00","tags":["H"]}',
        )
        self.assertEqual(built_inventory.snapshot_index.meta(snapshot_path).uuid, "source-uuid")
        self.assertTrue(built_inventory.snapshot_index.meta(snapshot_path).readonly)
        self.assertEqual(built_inventory.cache_index.meta(cache_path).uuid, "cache-uuid")
        self.assertTrue(built_inventory.cache_index.meta(cache_path).readonly)


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
        source = FakeSource(Completed("inventory", 0, output, ""))
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
        source = FakeSource(Completed("create", 0, output, ""))
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
        self.assertEqual(cache_result.status, "created")
        self.assertEqual(len(source.calls), 1)
        self.assertEqual(cache_result.meta.uuid, "cache-uuid")
        self.assertEqual(cache_result.meta.parent_uuid, "original-uuid")
        self.assertTrue(cache_result.meta.readonly)


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
                {"2026-07-14_01-00-00": '{"date":"2026-07-14_01-00-00"}\n'},
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

            self.assertEqual(transferred, 0)
            self.assertEqual(len(recovered), 1)
            self.assertIn("current send path disappeared", recovered[0])


if __name__ == "__main__":
    unittest.main()
