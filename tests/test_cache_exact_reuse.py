from __future__ import annotations

import unittest

from timeshift_btrfs_sync import inventory
from timeshift_btrfs_sync.btrfs_ops import BtrfsOps
from timeshift_btrfs_sync.cache_ops import CacheManager
from timeshift_btrfs_sync.endpoint import CommandEndpoint
from timeshift_btrfs_sync.commands import Completed
from timeshift_btrfs_sync.models import SubvolumeMeta


class FakeSource:
    uses_ssh = True
    location = "remote"

    def __init__(self, *results: Completed):
        self.results = list(results)
        self.calls: list[str] = []

    def run(self, command: str, **_kwargs) -> Completed:
        self.calls.append(command)
        if not self.results:
            raise AssertionError(f"Unexpected source command: {command}")
        return self.results.pop(0)


def make_index(root: str, *metas: SubvolumeMeta) -> inventory.BtrfsIndex:
    result = inventory.BtrfsIndex(root=root, location="remote")
    for meta in metas:
        result.add(meta)
    return result


class CacheExactReuseTests(unittest.TestCase):
    def test_stale_bulk_index_reuses_exact_existing_cache_snapshot_without_nested_name(self) -> None:
        cache_root = "/media/btrbk-source/OS-Root/timeshift-btrfs/.ts-btrfs-sync/send-cache"
        snapshot_name = "2026-06-23_07-10-24"
        original_path = f"/media/btrbk-source/OS-Root/timeshift-btrfs/snapshots/{snapshot_name}/@"
        cache_parent = f"{cache_root}/{snapshot_name}"
        cache_path = f"{cache_parent}/@"

        output = f"""TSBTRFS_CACHE_EXISTING_STATUS\t0
TSBTRFS_CACHE_EXISTING_OUTPUT_BEGIN
Name: @
UUID: cache-uuid
Parent UUID: original-uuid
Received UUID: -
Flags: readonly
TSBTRFS_CACHE_EXISTING_OUTPUT_END
"""
        source = FakeSource(Completed("probe-reuse", 0, output, ""))
        original_index = make_index(
            "/media/btrbk-source/OS-Root/timeshift-btrfs/snapshots",
            SubvolumeMeta("@", original_path, uuid="original-uuid", readonly=False),
        )
        # Simulate a bulk cache index that found the root/date parent but missed
        # the existing exact @ child because of a mount-path representation.
        cache_index = make_index(
            cache_root,
            SubvolumeMeta("send-cache", cache_root, uuid="root-uuid", readonly=False),
            SubvolumeMeta(snapshot_name, cache_parent, uuid="parent-uuid", readonly=False),
        )

        manager = CacheManager(
            BtrfsOps(CommandEndpoint.for_source(source), "sudo -n", "btrfs"),
            cache_root=cache_root,
            create_enabled=True,
        )
        cache_result = manager.ensure_send_snapshot(
            original_path=original_path,
            snapshot_name=snapshot_name,
            subvolume_name="@",
            cache_index=cache_index,
            original_index=original_index,
        )

        self.assertEqual(cache_result.path, cache_path)
        self.assertEqual(len(source.calls), 1)
        self.assertIn(f"subvolume show {cache_path}", source.calls[0])
        self.assertIn(f"subvolume snapshot -r {original_path} {cache_path}", source.calls[0])
        self.assertNotIn(f"{cache_path}/@", source.calls[0])
        self.assertEqual(cache_index.meta(cache_path).uuid, "cache-uuid")
        self.assertTrue(cache_index.meta(cache_path).readonly)

    def test_existing_non_subvolume_target_is_refused_before_snapshot_creation(self) -> None:
        cache_path = "/cache/date/@"
        output = """TSBTRFS_CACHE_EXISTING_STATUS\t1
TSBTRFS_CACHE_EXISTING_OUTPUT_BEGIN
ERROR: not a subvolume
TSBTRFS_CACHE_EXISTING_OUTPUT_END
TSBTRFS_CACHE_PATH_EXISTS\t1
"""
        source = FakeSource(Completed("probe", 0, output, ""))
        manager = CacheManager(
            BtrfsOps(CommandEndpoint.for_source(source), "sudo -n", "btrfs"),
            cache_root="/cache",
            create_enabled=True,
        )
        with self.assertRaisesRegex(RuntimeError, "nested"):
            manager._probe_create_verify(
                original=SubvolumeMeta("@", "/snapshots/date/@", uuid="original-uuid"),
                cache_path=cache_path,
                subvolume_name="@",
            )
        self.assertEqual(len(source.calls), 1)

    def test_concurrent_exact_cache_creator_is_reused_after_create_failure(self) -> None:
        output = """TSBTRFS_CACHE_EXISTING_STATUS\t1
TSBTRFS_CACHE_EXISTING_OUTPUT_BEGIN
not found
TSBTRFS_CACHE_EXISTING_OUTPUT_END
TSBTRFS_CACHE_PATH_EXISTS\t0
TSBTRFS_CACHE_CREATE_STATUS\t1
TSBTRFS_CACHE_CREATE_OUTPUT_BEGIN
target path already exists
TSBTRFS_CACHE_CREATE_OUTPUT_END
TSBTRFS_CACHE_RACE_SHOW_STATUS\t0
TSBTRFS_CACHE_RACE_SHOW_OUTPUT_BEGIN
Name: @
UUID: concurrent-cache-uuid
Parent UUID: original-uuid
Received UUID: -
Flags: readonly
TSBTRFS_CACHE_RACE_SHOW_OUTPUT_END
"""
        source = FakeSource(Completed("race", 0, output, ""))
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
        self.assertEqual(cache_result.status, "concurrent-reuse")
        self.assertEqual(cache_result.meta.uuid, "concurrent-cache-uuid")


class MountedSubvolumePathResolutionTests(unittest.TestCase):
    def test_bulk_index_resolves_on_disk_prefix_absent_from_mount_path(self) -> None:
        root = "/media/btrbk-source/OS-Root/timeshift-btrfs/.ts-btrfs-sync/send-cache"
        listed = "@root/timeshift-btrfs/.ts-btrfs-sync/send-cache/2026-06-23_07-10-24/@"
        expected = f"{root}/2026-06-23_07-10-24/@"
        self.assertEqual(inventory.listed_path_to_absolute(root, listed), expected)

    def test_parse_bulk_list_keeps_existing_cache_child_after_remount(self) -> None:
        root = "/media/darkyere/OS-Root/timeshift-btrfs/.ts-btrfs/send-cache"
        expected = f"{root}/2026-06-29_15-13-59/@"
        output = (
            "ID 20 gen 1 top level 256 parent_uuid original-uuid "
            "received_uuid - uuid cache-uuid path "
            "@root/timeshift-btrfs/.ts-btrfs/send-cache/2026-06-29_15-13-59/@\n"
        )
        metas = inventory.parse_subvolume_list(output, root)
        self.assertEqual([meta.path for meta in metas], [expected])
        self.assertEqual(metas[0].uuid, "cache-uuid")


if __name__ == "__main__":
    unittest.main()
