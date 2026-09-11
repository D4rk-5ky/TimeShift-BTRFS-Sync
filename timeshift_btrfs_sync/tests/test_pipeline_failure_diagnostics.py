from __future__ import annotations

import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from timeshift_btrfs_sync.commands import CommandError, stream_pipeline
from timeshift_btrfs_sync.inventory import BtrfsIndex, SourceInventory
from timeshift_btrfs_sync.models import SubvolumeMeta
from timeshift_btrfs_sync.sync import (
    _revalidate_missing_required_pipeline_paths,
    _required_pipeline_source_changes,
    _terminal_destination_receive_failure_reason,
)


class PipelineFailureDiagnosticsTests(unittest.TestCase):
    def test_enospc_from_receive_is_terminal_destination_failure(self) -> None:
        exc = CommandError(
            "send | receive",
            1,
            stderr="upstream broken pipe\nERROR: writing unencoded data failed: No space left on device",
            stage_returncodes={"send": 1, "buffer": 1, "receive": 1},
            stage_stderr={
                "send": "ERROR: write failed: Broken pipe\n",
                "buffer": "Broken pipe\n",
                "receive": "ERROR: writing unencoded data failed: No space left on device\n",
            },
        )
        self.assertEqual(
            _terminal_destination_receive_failure_reason(exc),
            "destination reported no allocatable space (ENOSPC)",
        )


    def test_stream_pipeline_preserves_receive_stage_failure_details(self) -> None:
        left = [sys.executable, "-c", "import sys; sys.stdout.write('payload')"]
        right = [
            sys.executable,
            "-c",
            "import sys; sys.stdin.read(); print('No space left on device', file=sys.stderr); sys.exit(1)",
        ]
        with self.assertRaises(CommandError) as caught:
            stream_pipeline(left, right, verbose=False)
        exc = caught.exception
        self.assertNotEqual(exc.stage_returncodes.get("receive"), 0)
        self.assertIn("No space left on device", exc.stage_stderr.get("receive", ""))
        self.assertEqual(
            _terminal_destination_receive_failure_reason(exc),
            "destination reported no allocatable space (ENOSPC)",
        )

    def test_broken_pipe_without_receive_storage_signature_is_not_terminal_destination_failure(self) -> None:
        exc = CommandError(
            "send | receive",
            1,
            stage_returncodes={"send": 1, "buffer": 1, "receive": 1},
            stage_stderr={
                "send": "Broken pipe\n",
                "buffer": "Broken pipe\n",
                "receive": "ERROR: failed to read stream\n",
            },
        )
        self.assertIsNone(_terminal_destination_receive_failure_reason(exc))

    def test_exact_probe_repairs_bulk_cache_omission_before_change_detection(self) -> None:
        path = "/cache/2026-08-14_16-33-59/@"
        before_cache = BtrfsIndex(root="/cache", location="remote")
        before_cache.add(SubvolumeMeta(name="@", path=path, uuid="cache-uuid", readonly=True))
        after_cache = BtrfsIndex(root="/cache", location="remote")
        before = SourceInventory("", BtrfsIndex(root="/snapshots", location="remote"), before_cache)
        after = SourceInventory("", BtrfsIndex(root="/snapshots", location="remote"), after_cache)
        config = SimpleNamespace(
            source=SimpleNamespace(cache_root="/cache", sudo="sudo -n", btrfs_command="btrfs")
        )
        source = SimpleNamespace(location="remote")

        def fake_refresh(index, _ops, refresh_path, *, name=None):
            self.assertEqual(refresh_path, path)
            meta = SubvolumeMeta(name=name or "@", path=path, uuid="cache-uuid", readonly=True)
            index.add(meta)
            return meta

        with patch("timeshift_btrfs_sync.sync.inventory.refresh_path", side_effect=fake_refresh):
            notes = _revalidate_missing_required_pipeline_paths(
                config,
                source,
                before,
                after,
                current_path=path,
                parent_path=None,
            )

        self.assertTrue(any("bulk inventory omitted path" in note for note in notes))
        self.assertEqual(after.meta(path).uuid, "cache-uuid")
        self.assertEqual(
            _required_pipeline_source_changes(
                before,
                after,
                current_path=path,
                parent_path=None,
            ),
            [],
        )

    def test_exact_probe_confirmed_absence_remains_a_source_change(self) -> None:
        path = "/cache/2026-08-14_16-33-59/@"
        before_cache = BtrfsIndex(root="/cache", location="remote")
        before_cache.add(SubvolumeMeta(name="@", path=path, uuid="cache-uuid", readonly=True))
        after_cache = BtrfsIndex(root="/cache", location="remote")
        before = SourceInventory("", BtrfsIndex(root="/snapshots", location="remote"), before_cache)
        after = SourceInventory("", BtrfsIndex(root="/snapshots", location="remote"), after_cache)
        config = SimpleNamespace(
            source=SimpleNamespace(cache_root="/cache", sudo="sudo -n", btrfs_command="btrfs")
        )
        source = SimpleNamespace(location="remote")

        with patch("timeshift_btrfs_sync.sync.inventory.refresh_path", return_value=None):
            notes = _revalidate_missing_required_pipeline_paths(
                config,
                source,
                before,
                after,
                current_path=path,
                parent_path=None,
            )

        self.assertTrue(any("exact Btrfs probe confirms absent" in note for note in notes))
        self.assertEqual(
            _required_pipeline_source_changes(
                before,
                after,
                current_path=path,
                parent_path=None,
            ),
            [f"current send path disappeared: {path}"],
        )


if __name__ == "__main__":
    unittest.main()
