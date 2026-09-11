from __future__ import annotations

import ast
import unittest
from pathlib import Path
from unittest.mock import patch

from timeshift_btrfs_sync import destroy, inventory, retention, sync, tree_ops
from timeshift_btrfs_sync.btrfs_ops import BtrfsOps
from timeshift_btrfs_sync.cache_ops import CacheManager
from timeshift_btrfs_sync.commands import Completed
from timeshift_btrfs_sync.endpoint import CommandEndpoint
from timeshift_btrfs_sync.executor import WorkflowExecutor
from timeshift_btrfs_sync.models import SnapshotMeta, SubvolumeMeta
from timeshift_btrfs_sync.planning import ActionKind, WorkflowAction, plan_prune_snapshot, plan_snapshot_recovery, plan_sync_queue


DATE_1 = "2026-07-15_04-00-02"
DATE_2 = "2026-07-15_05-00-02"


def snapshot(name: str, root: str = "/snapshots") -> SnapshotMeta:
    return SnapshotMeta(
        name=name,
        path=f"{root}/{name}",
        tags=["H"],
        subvolumes={
            "@": SubvolumeMeta("@", f"{root}/{name}/@", uuid=f"source-{name}", readonly=False),
            "@home": SubvolumeMeta("@home", f"{root}/{name}/@home", uuid=f"home-{name}", readonly=False),
        },
    )


class SharedWorkflowTests(unittest.TestCase):
    def source_snapshots(self):
        return {DATE_1: snapshot(DATE_1), DATE_2: snapshot(DATE_2)}

    def test_sync_planner_is_pure_and_orders_oldest_to_newest(self):
        source_snapshots = self.source_snapshots()
        before = repr(source_snapshots)
        plan = plan_sync_queue(source_snapshots, [DATE_2, DATE_1], ["@", "@home"])
        self.assertEqual(repr(source_snapshots), before)
        actions = [(action.kind, action.snapshot, action.subvolume) for action in plan.actions]
        self.assertEqual(
            actions,
            [
                # Already-recorded items remain in the queue so the real sync
                # workflow can run UUID, partial-date, path, and metadata checks.
                (ActionKind.ENSURE_CACHE, DATE_1, "@"),
                (ActionKind.SYNC_SUBVOLUME, DATE_1, "@"),
                (ActionKind.ENSURE_CACHE, DATE_1, "@home"),
                (ActionKind.SYNC_SUBVOLUME, DATE_1, "@home"),
                (ActionKind.COPY_INFO_JSON, DATE_1, None),
                (ActionKind.ENSURE_CACHE, DATE_2, "@"),
                (ActionKind.SYNC_SUBVOLUME, DATE_2, "@"),
                (ActionKind.ENSURE_CACHE, DATE_2, "@home"),
                (ActionKind.SYNC_SUBVOLUME, DATE_2, "@home"),
                (ActionKind.COPY_INFO_JSON, DATE_2, None),
            ],
        )

    def test_planner_and_executor_compose_in_the_same_order(self):
        plan = plan_sync_queue(self.source_snapshots(), [DATE_2, DATE_1], ["@", "@home"])
        seen: list[tuple[ActionKind, str | None, str | None]] = []

        def handle(action: WorkflowAction):
            seen.append((action.kind, action.snapshot, action.subvolume))
            return len(seen)

        executor = WorkflowExecutor({kind: handle for kind in ActionKind})
        results = executor.execute(plan)
        self.assertEqual(seen, [(a.kind, a.snapshot, a.subvolume) for a in plan.actions])
        self.assertEqual([result for _action, result in results], list(range(1, len(plan.actions) + 1)))

    def test_prune_plan_preserves_destination_cache_state_order(self):
        plan = plan_prune_snapshot(DATE_1, delete_cache=True, delete_destination=True)
        self.assertEqual(
            [action.kind for action in plan.actions],
            [ActionKind.DELETE_DESTINATION_TREE, ActionKind.DELETE_CACHE_TREE, ActionKind.REMOVE_STATE],
        )

    def test_recovery_plan_uses_cache_destination_state_order(self):
        plan = plan_snapshot_recovery(DATE_1)
        self.assertEqual(
            [action.kind for action in plan.actions],
            [ActionKind.DELETE_CACHE_TREE, ActionKind.DELETE_DESTINATION_TREE, ActionKind.REMOVE_STATE],
        )

    def test_all_cleanup_workflows_use_one_tree_delete_implementation(self):
        self.assertIs(sync.delete_subvolume_tree, tree_ops.delete_subvolume_tree)
        self.assertIs(retention.delete_subvolume_tree, tree_ops.delete_subvolume_tree)
        self.assertIs(destroy.delete_subvolume_tree, tree_ops.delete_subvolume_tree)

    def test_cache_operation_uses_one_btrfs_facade_and_exact_target(self):
        endpoint = CommandEndpoint.local("test")
        ops = BtrfsOps(endpoint, "", "btrfs")
        manager = CacheManager(ops, cache_root="/cache", create_enabled=True)
        original = SubvolumeMeta("@", f"/snapshots/{DATE_1}/@", uuid="source-uuid", readonly=False)
        source_index = inventory.BtrfsIndex("/snapshots", "source")
        source_index.add(original)
        cache_index = inventory.BtrfsIndex("/cache", "source")
        cache_index.add(SubvolumeMeta("send-cache", "/cache", uuid="cache-root"))
        cache_index.add(SubvolumeMeta(DATE_1, f"/cache/{DATE_1}", uuid="date-root"))
        scripts: list[str] = []
        output = (
            "TSBTRFS_CACHE_PARENT_LIST_STATUS\t0\n"
            "TSBTRFS_CACHE_PARENT_LIST_BEGIN\n"
            "ID 20 gen 1 top level 5 parent_uuid source-uuid "
            "received_uuid - uuid cache-uuid path @\n"
            "TSBTRFS_CACHE_PARENT_LIST_END\n"
            "TSBTRFS_CACHE_PARENT_READONLY_STATUS\t0\n"
            "TSBTRFS_CACHE_PARENT_READONLY_BEGIN\n"
            "ID 20 gen 1 top level 5 path @\n"
            "TSBTRFS_CACHE_PARENT_READONLY_END\n"
        )

        def run_shell(script: str, **_kwargs):
            scripts.append(script)
            return Completed(0, output, "")

        with patch.object(CommandEndpoint, "run_shell", side_effect=run_shell):
            result = manager.ensure_send_snapshot(
                original_path=original.path,
                snapshot_name=DATE_1,
                subvolume_name="@",
                cache_index=cache_index,
                original_index=source_index,
            )
        self.assertEqual(result.path, f"/cache/{DATE_1}/@")
        self.assertEqual(result.path, f"/cache/{DATE_1}/@")
        self.assertTrue(result.readonly)
        self.assertEqual(len(scripts), 1)
        self.assertNotIn(f"/cache/{DATE_1}/@/@", scripts[0])

    def test_tree_discovery_uses_one_bulk_child_listing(self):
        ops = BtrfsOps(CommandEndpoint.local("test"), "", "btrfs")
        root = "/cache"
        listed = ["cache/date", "cache/date/@", "cache/date/@home"]
        with (
            patch.object(BtrfsOps, "meta", return_value=SubvolumeMeta("cache", root, uuid="root")),
            patch.object(BtrfsOps, "list_children", return_value=listed) as children,
        ):
            paths, errors = tree_ops.discover_subvolume_tree(ops, root)
        self.assertEqual(errors, [])
        self.assertEqual(children.call_count, 1)
        self.assertEqual(paths[-1], root)

    def test_operation_modules_have_single_authoritative_definitions(self):
        package = Path("timeshift_btrfs_sync")
        definitions: dict[str, list[str]] = {
            "build_source_inventory": [],
            "delete_subvolume_tree": [],
            "CacheManager": [],
            "BtrfsOps": [],
            "WorkflowExecutor": [],
        }
        for path in package.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in definitions:
                    definitions[node.name].append(path.name)
        self.assertEqual(definitions["build_source_inventory"], ["inventory.py"])
        self.assertEqual(definitions["delete_subvolume_tree"], ["tree_ops.py"])
        self.assertEqual(definitions["CacheManager"], ["cache_ops.py"])
        self.assertEqual(definitions["BtrfsOps"], ["btrfs_ops.py"])
        self.assertEqual(definitions["WorkflowExecutor"], ["executor.py"])

