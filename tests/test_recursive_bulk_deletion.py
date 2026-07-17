from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

from timeshift_btrfs_sync import tree_ops
from timeshift_btrfs_sync.btrfs_ops import BtrfsOps
from timeshift_btrfs_sync.commands import Completed
from timeshift_btrfs_sync.endpoint import CommandEndpoint
from timeshift_btrfs_sync.models import SubvolumeMeta


CACHE_ROOT = "/media/darkyere/OS-Root/timeshift-btrfs/.ts-btrfs/send-cache"
CACHE_DATE = "2026-07-17_14-04-41"
DEST_ROOT = "/media/darkyere/btrbk/Ubuntu-ZFS-RAID-Import-Test"
DEST_DATE = "2026-07-17_14-04-41"


class RecursiveBulkListTests(unittest.TestCase):
    def test_cache_tree_includes_date_payload_children_from_one_all_filesystem_list(self):
        output = "\n".join(
            [
                "ID 2228 gen 10 parent 5 top level 5 path <FS_TREE>/timeshift-btrfs/.ts-btrfs/send-cache",
                f"ID 2346 gen 11 parent 2228 top level 2228 path <FS_TREE>/timeshift-btrfs/.ts-btrfs/send-cache/{CACHE_DATE}",
                f"ID 2347 gen 12 parent 2346 top level 2346 path <FS_TREE>/timeshift-btrfs/.ts-btrfs/send-cache/{CACHE_DATE}/@",
                f"ID 2348 gen 13 parent 2346 top level 2346 path <FS_TREE>/timeshift-btrfs/.ts-btrfs/send-cache/{CACHE_DATE}/@home",
                "ID 9999 gen 20 parent 5 top level 5 path <FS_TREE>/other/timeshift-btrfs/.ts-btrfs/send-cache/not-ours/@",
            ]
        )
        endpoint = CommandEndpoint.local("source")
        ops = BtrfsOps(endpoint, "", "btrfs")
        calls: list[list[str]] = []

        def run_argv(argv, **_kwargs):
            calls.append(list(argv))
            return Completed(list(argv), 0, output, "")

        with (
            patch.object(CommandEndpoint, "run_argv", side_effect=run_argv),
            patch.object(BtrfsOps, "meta", return_value=SubvolumeMeta("send-cache", CACHE_ROOT, uuid="root", subvolume_id=2228)),
        ):
            planned, errors = tree_ops.discover_subvolume_tree(ops, CACHE_ROOT)

        self.assertEqual(errors, [])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][-5:], ["subvolume", "list", "-a", "-p", CACHE_ROOT])
        self.assertEqual(
            planned,
            [
                f"{CACHE_ROOT}/{CACHE_DATE}/@home",
                f"{CACHE_ROOT}/{CACHE_DATE}/@",
                f"{CACHE_ROOT}/{CACHE_DATE}",
                CACHE_ROOT,
            ],
        )

    def test_destination_tree_includes_payload_children_before_all_parent_containers(self):
        output = "\n".join(
            [
                "ID 3377 gen 10 parent 5 top level 5 path <FS_TREE>/btrbk/Ubuntu-ZFS-RAID-Import-Test",
                "ID 3400 gen 11 parent 3377 top level 3377 path <FS_TREE>/btrbk/Ubuntu-ZFS-RAID-Import-Test/.ts-btrfs-sync",
                "ID 3547 gen 12 parent 3377 top level 3377 path <FS_TREE>/btrbk/Ubuntu-ZFS-RAID-Import-Test/snapshots",
                f"ID 3548 gen 13 parent 3547 top level 3547 path <FS_TREE>/btrbk/Ubuntu-ZFS-RAID-Import-Test/snapshots/{DEST_DATE}",
                f"ID 3549 gen 14 parent 3548 top level 3548 path <FS_TREE>/btrbk/Ubuntu-ZFS-RAID-Import-Test/snapshots/{DEST_DATE}/@",
                f"ID 3550 gen 15 parent 3548 top level 3548 path <FS_TREE>/btrbk/Ubuntu-ZFS-RAID-Import-Test/snapshots/{DEST_DATE}/@home",
            ]
        )
        endpoint = CommandEndpoint.local("destination")
        ops = BtrfsOps(endpoint, "", "btrfs")
        with (
            patch.object(CommandEndpoint, "run_argv", return_value=Completed(["btrfs"], 0, output, "")),
            patch.object(BtrfsOps, "meta", return_value=SubvolumeMeta(Path(DEST_ROOT).name, DEST_ROOT, uuid="root", subvolume_id=3377)),
        ):
            planned, errors = tree_ops.discover_subvolume_tree(ops, DEST_ROOT)

        self.assertEqual(errors, [])
        self.assertLess(planned.index(f"{DEST_ROOT}/snapshots/{DEST_DATE}/@"), planned.index(f"{DEST_ROOT}/snapshots/{DEST_DATE}"))
        self.assertLess(planned.index(f"{DEST_ROOT}/snapshots/{DEST_DATE}"), planned.index(f"{DEST_ROOT}/snapshots"))
        self.assertLess(planned.index(f"{DEST_ROOT}/snapshots"), planned.index(DEST_ROOT))
        self.assertIn(f"{DEST_ROOT}/.ts-btrfs-sync", planned)

    def test_ssh_source_uses_same_single_graph_command(self):
        output = "\n".join(
            [
                "ID 2228 gen 10 parent 5 top level 5 path <FS_TREE>/timeshift-btrfs/.ts-btrfs/send-cache",
                f"ID 2346 gen 11 parent 2228 top level 2228 path <FS_TREE>/timeshift-btrfs/.ts-btrfs/send-cache/{CACHE_DATE}",
                f"ID 2347 gen 12 parent 2346 top level 2346 path <FS_TREE>/timeshift-btrfs/.ts-btrfs/send-cache/{CACHE_DATE}/@",
            ]
        )
        commands: list[str] = []

        def run(command: str, **_kwargs):
            commands.append(command)
            return Completed(["ssh"], 0, output, "")

        source = SimpleNamespace(location="remote", run=run)
        ops = BtrfsOps(CommandEndpoint.for_source(source), "sudo -n", "btrfs")
        listed = ops.list_children(CACHE_ROOT, root_id=2228)

        self.assertEqual(len(commands), 1)
        self.assertIn("sudo -n btrfs subvolume list -a -p", commands[0])
        self.assertEqual(
            listed,
            [
                f"<FS_TREE>/timeshift-btrfs/.ts-btrfs/send-cache/{CACHE_DATE}",
                f"<FS_TREE>/timeshift-btrfs/.ts-btrfs/send-cache/{CACHE_DATE}/@",
            ],
        )

    def test_subvolume_show_parses_numeric_containment_ids(self):
        from timeshift_btrfs_sync.btrfs_ops import parse_subvolume_show

        meta = parse_subvolume_show(
            "Name: send-cache\nSubvolume ID: 2228\nTop level ID: 5\nUUID: root-uuid\nFlags: -\n",
            "send-cache",
            CACHE_ROOT,
        )
        self.assertEqual(meta.subvolume_id, 2228)
        self.assertEqual(meta.containing_parent_id, 5)

    def test_shared_delete_engine_passes_complete_deepest_first_plan_to_one_batch(self):
        planned = [
            f"{CACHE_ROOT}/{CACHE_DATE}/@home",
            f"{CACHE_ROOT}/{CACHE_DATE}/@",
            f"{CACHE_ROOT}/{CACHE_DATE}",
            CACHE_ROOT,
        ]
        ops = BtrfsOps(CommandEndpoint.local("source"), "", "btrfs")
        with (
            patch.object(tree_ops, "_path_exists", side_effect=[(True, ""), (False, "")]),
            patch.object(BtrfsOps, "meta", side_effect=[SubvolumeMeta("send-cache", CACHE_ROOT, uuid="root", subvolume_id=2228), None]),
            patch.object(tree_ops, "discover_subvolume_tree", return_value=(planned, [])),
            patch.object(BtrfsOps, "batch_delete", return_value=(planned, [])) as delete,
        ):
            result = tree_ops.delete_subvolume_tree(ops, CACHE_ROOT)

        delete.assert_called_once_with(planned)
        self.assertEqual(result.confirmed, planned)
        self.assertTrue(result.success)



if __name__ == "__main__":
    unittest.main()
