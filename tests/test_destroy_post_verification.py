from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from timeshift_btrfs_sync import destroy
from timeshift_btrfs_sync.config import load_config
from timeshift_btrfs_sync.models import SubvolumeMeta


class FakeSource:
    def command(self, source_command: str):
        return ["sh", "-c", source_command]

    def environment(self):
        return None


ROOT = "/cache"
CHILD = "/cache/2026-07-15_05-00-02/@"
ROOT_META = SubvolumeMeta("cache", ROOT, uuid="root-uuid")


class DestroySourcePostVerificationTests(unittest.TestCase):
    def test_zero_confirmed_deletions_and_existing_cache_root_is_incomplete(self) -> None:
        source = FakeSource()
        with (
            patch.object(destroy, "_source_subvolume_meta", return_value=ROOT_META),
            patch.object(destroy, "_collect_recursive_subvolumes", side_effect=[[CHILD], [CHILD]]),
            patch.object(destroy, "_source_delete_subvolumes_batched", return_value=([], [])),
            patch.object(destroy, "_source_exists", return_value=(True, "")),
        ):
            result = destroy._delete_source_tree(
                source,
                ROOT,
                "sudo -n",
                "btrfs",
                dry_run=False,
                label="Source send-cache root",
                protected_snapshot_root="/timeshift/snapshots",
            )

        self.assertFalse(result.success)
        self.assertFalse(result.verified_root_absent)
        self.assertEqual(result.deleted_subvolumes, 0)
        self.assertEqual(result.remaining_subvolumes, [CHILD, ROOT])
        self.assertTrue(any("no subvolume deletions were confirmed" in item for item in result.errors))
        self.assertTrue(any("root still exists" in item for item in result.errors))

        output = io.StringIO()
        with redirect_stdout(output):
            destroy._print_result(result, dry_run=False)
        rendered = output.getvalue()
        self.assertIn("verified configured root absent: no", rendered)
        self.assertIn("remaining Btrfs subvolumes:", rendered)
        self.assertIn(CHILD, rendered)
        self.assertIn("result:     incomplete", rendered)
        self.assertNotIn("result:     complete", rendered)

    def test_all_source_deletions_and_absent_cache_root_is_complete(self) -> None:
        source = FakeSource()
        with (
            patch.object(destroy, "_source_subvolume_meta", side_effect=[ROOT_META, None]),
            patch.object(destroy, "_collect_recursive_subvolumes", return_value=[CHILD]),
            patch.object(destroy, "_source_delete_subvolumes_batched", return_value=([CHILD, ROOT], [])),
            patch.object(destroy, "_source_exists", return_value=(False, "")),
        ):
            result = destroy._delete_source_tree(
                source,
                ROOT,
                "sudo -n",
                "btrfs",
                dry_run=False,
                label="Source send-cache root",
                protected_snapshot_root="/timeshift/snapshots",
            )

        self.assertTrue(result.success)
        self.assertTrue(result.verification_attempted)
        self.assertTrue(result.verified_root_absent)
        self.assertEqual(result.deleted_subvolumes, 2)
        self.assertEqual(result.errors, [])

        output = io.StringIO()
        with redirect_stdout(output):
            destroy._print_result(result, dry_run=False)
        rendered = output.getvalue()
        self.assertIn("verified configured root absent: yes", rendered)
        self.assertIn("result:     complete", rendered)

    def test_fewer_confirmed_deletions_is_incomplete_even_when_root_is_absent(self) -> None:
        source = FakeSource()
        with (
            patch.object(destroy, "_source_subvolume_meta", side_effect=[ROOT_META, None]),
            patch.object(destroy, "_collect_recursive_subvolumes", return_value=[CHILD]),
            patch.object(destroy, "_source_delete_subvolumes_batched", return_value=([CHILD], [])),
            patch.object(destroy, "_source_exists", return_value=(False, "")),
        ):
            result = destroy._delete_source_tree(
                source,
                ROOT,
                "sudo -n",
                "btrfs",
                dry_run=False,
                label="Source send-cache root",
                protected_snapshot_root="/timeshift/snapshots",
            )

        self.assertFalse(result.success)
        self.assertTrue(result.verified_root_absent)
        self.assertTrue(any("not every planned" in item for item in result.errors))

    def test_failed_final_source_existence_check_is_incomplete(self) -> None:
        source = FakeSource()
        with (
            patch.object(destroy, "_source_subvolume_meta", return_value=ROOT_META),
            patch.object(destroy, "_collect_recursive_subvolumes", return_value=[CHILD]),
            patch.object(destroy, "_source_delete_subvolumes_batched", return_value=([CHILD, ROOT], [])),
            patch.object(destroy, "_source_exists", return_value=(None, "ssh verification failed")),
        ):
            result = destroy._delete_source_tree(
                source,
                ROOT,
                "sudo -n",
                "btrfs",
                dry_run=False,
                label="Source send-cache root",
                protected_snapshot_root="/timeshift/snapshots",
            )

        self.assertFalse(result.success)
        self.assertFalse(result.verified_root_absent)
        self.assertTrue(any("final configured-root existence check failed" in item for item in result.errors))


class DestroyLocalPostVerificationTests(unittest.TestCase):
    def test_local_root_remaining_rebuilds_index_and_is_incomplete(self) -> None:
        with (
            patch.object(destroy, "_local_exists", side_effect=[(True, ""), (True, "")]),
            patch.object(destroy, "_local_subvolume_meta", return_value=ROOT_META),
            patch.object(destroy, "_collect_recursive_subvolumes", side_effect=[[CHILD], [CHILD]]),
            patch.object(destroy.btrfs, "delete_local_subvolume"),
        ):
            result = destroy._delete_local_tree(
                ROOT,
                "sudo -n",
                "btrfs",
                dry_run=False,
                label="Destination target_root",
            )

        self.assertFalse(result.success)
        self.assertFalse(result.verified_root_absent)
        self.assertEqual(result.deleted_subvolumes, 2)
        self.assertEqual(result.remaining_subvolumes, [CHILD, ROOT])
        self.assertTrue(any("root still exists" in item for item in result.errors))

    def test_local_root_absence_is_required_for_complete(self) -> None:
        with (
            patch.object(destroy, "_local_exists", side_effect=[(True, ""), (False, "")]),
            patch.object(destroy, "_local_subvolume_meta", return_value=ROOT_META),
            patch.object(destroy, "_collect_recursive_subvolumes", return_value=[CHILD]),
            patch.object(destroy.btrfs, "delete_local_subvolume"),
        ):
            result = destroy._delete_local_tree(
                ROOT,
                "sudo -n",
                "btrfs",
                dry_run=False,
                label="Destination target_root",
            )

        self.assertTrue(result.success)
        self.assertTrue(result.verified_root_absent)
        self.assertEqual(result.deleted_subvolumes, 2)


class DestroySummaryVerificationTests(unittest.TestCase):
    def test_unverified_target_is_counted_incomplete_even_without_error_strings(self) -> None:
        config = load_config("timeshift_btrfs_sync/data/config.example.toml")
        summary_root = "/srv/ts-btrfs-cache"
        config.source.cache_root = summary_root
        unverified = destroy.DestroyResult(
            label="Source send-cache root",
            path=summary_root,
            location="source",
            exists=True,
            root_is_subvolume=True,
            verification_required=True,
        )
        output = io.StringIO()
        with (
            patch.object(destroy.SourceRunner, "from_config", return_value=FakeSource()),
            patch.object(destroy, "_delete_source_tree", return_value=unverified),
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
