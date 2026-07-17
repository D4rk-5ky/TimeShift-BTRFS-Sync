from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

from timeshift_btrfs_sync import destroy, tree_ops
from timeshift_btrfs_sync.btrfs_ops import BtrfsOps
from timeshift_btrfs_sync.config import load_config
from timeshift_btrfs_sync.endpoint import CommandEndpoint
from timeshift_btrfs_sync.models import SubvolumeMeta

ROOT = "/cache"
CHILD = "/cache/2026-07-15_05-00-02/@"
ROOT_META = SubvolumeMeta("cache", ROOT, uuid="root-uuid")


def ops() -> BtrfsOps:
    return BtrfsOps(CommandEndpoint.local("test"), "", "btrfs")


class SharedTreePostVerificationTests(unittest.TestCase):
    def test_zero_confirmed_deletions_and_existing_root_is_incomplete(self) -> None:
        bops = ops()
        with (
            patch.object(BtrfsOps, "meta", side_effect=[ROOT_META, ROOT_META]),
            patch.object(BtrfsOps, "batch_delete", return_value=([], [])),
            patch.object(tree_ops, "_path_exists", side_effect=[(True, ""), (True, "")]),
            patch.object(tree_ops, "discover_subvolume_tree", side_effect=[([CHILD, ROOT], []), ([CHILD, ROOT], [])]),
            patch.object(tree_ops, "list_direct_entries", return_value=([CHILD], "")),
        ):
            result = tree_ops.delete_subvolume_tree(bops, ROOT)
        self.assertFalse(result.success)
        self.assertEqual(result.deleted_subvolumes, 0)
        self.assertEqual(result.remaining, [CHILD, ROOT])
        self.assertTrue(any("no subvolume deletions" in error for error in result.errors))
        self.assertTrue(any("still exists" in error for error in result.errors))

    def test_all_confirmed_and_absent_root_is_complete(self) -> None:
        bops = ops()
        with (
            patch.object(BtrfsOps, "meta", side_effect=[ROOT_META, None]),
            patch.object(BtrfsOps, "batch_delete", return_value=([CHILD, ROOT], [])),
            patch.object(tree_ops, "_path_exists", side_effect=[(True, ""), (False, "")]),
            patch.object(tree_ops, "discover_subvolume_tree", return_value=([CHILD, ROOT], [])),
        ):
            result = tree_ops.delete_subvolume_tree(bops, ROOT)
        self.assertTrue(result.success)
        self.assertTrue(result.verified_root_absent)
        self.assertEqual(result.deleted_subvolumes, 2)

    def test_partial_confirmations_remain_incomplete_even_if_root_is_absent(self) -> None:
        bops = ops()
        with (
            patch.object(BtrfsOps, "meta", side_effect=[ROOT_META, None]),
            patch.object(BtrfsOps, "batch_delete", return_value=([CHILD], [])),
            patch.object(tree_ops, "_path_exists", side_effect=[(True, ""), (False, "")]),
            patch.object(tree_ops, "discover_subvolume_tree", return_value=([CHILD, ROOT], [])),
        ):
            result = tree_ops.delete_subvolume_tree(bops, ROOT)
        self.assertFalse(result.success)
        self.assertTrue(result.verified_root_absent)
        self.assertTrue(any("not every planned" in error for error in result.errors))

    def test_failed_final_existence_check_is_incomplete(self) -> None:
        bops = ops()
        with (
            patch.object(BtrfsOps, "meta", side_effect=[ROOT_META, None]),
            patch.object(BtrfsOps, "batch_delete", return_value=([CHILD, ROOT], [])),
            patch.object(tree_ops, "_path_exists", side_effect=[(True, ""), (None, "verification failed")]),
            patch.object(tree_ops, "discover_subvolume_tree", return_value=([CHILD, ROOT], [])),
        ):
            result = tree_ops.delete_subvolume_tree(bops, ROOT)
        self.assertFalse(result.success)
        self.assertTrue(any("final configured-root existence check failed" in error for error in result.errors))


class DestroySummaryVerificationTests(unittest.TestCase):
    def test_dry_run_blocking_error_is_reported_incomplete(self) -> None:
        config = load_config("timeshift_btrfs_sync/data/config.example.toml")
        config.source.cache_root = "/srv/ts-btrfs-cache"
        tree = tree_ops.TreeDeleteResult(
            root=config.source.cache_root,
            endpoint="source",
            existed=True,
            root_is_subvolume=False,
            errors=["configured root is an ordinary non-empty directory"],
        )
        output = io.StringIO()
        with (
            patch.object(destroy.SourceRunner, "from_config", return_value=MagicMock(location="local")),
            patch.object(destroy, "delete_subvolume_tree", return_value=tree),
            redirect_stdout(output),
        ):
            with self.assertRaisesRegex(RuntimeError, "incomplete target cleanup"):
                destroy.destroy_leftovers(
                    config,
                    delete_source=True,
                    delete_destination=False,
                    dry_run=True,
                    danger_confirmed=False,
                    interactive=False,
                )
        rendered = output.getvalue()
        self.assertIn("result:     incomplete", rendered)
        self.assertIn("ordinary non-empty", rendered)
        self.assertIn("complete:   0", rendered)
        self.assertIn("incomplete: 1", rendered)

    def test_unverified_tree_is_counted_incomplete(self) -> None:
        config = load_config("timeshift_btrfs_sync/data/config.example.toml")
        config.source.cache_root = "/srv/ts-btrfs-cache"
        tree = tree_ops.TreeDeleteResult(
            root=config.source.cache_root,
            endpoint="source",
            existed=True,
            root_is_subvolume=True,
        )
        output = io.StringIO()
        with (
            patch.object(destroy.SourceRunner, "from_config", return_value=MagicMock(location="local")),
            patch.object(destroy, "delete_subvolume_tree", return_value=tree),
            redirect_stdout(output),
        ):
            with self.assertRaisesRegex(RuntimeError, "incomplete target cleanup"):
                destroy.destroy_leftovers(
                    config,
                    delete_source=True,
                    delete_destination=False,
                    dry_run=False,
                    danger_confirmed=True,
                    interactive=False,
                )
        rendered = output.getvalue()
        self.assertIn("verified configured root absent: no", rendered)
        self.assertIn("complete:   0", rendered)
        self.assertIn("incomplete: 1", rendered)


if __name__ == "__main__":
    unittest.main()
