from __future__ import annotations

import argparse
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from timeshift_btrfs_sync import cli, retention
from timeshift_btrfs_sync.config import load_config
from timeshift_btrfs_sync.retention import PrunePlan
from timeshift_btrfs_sync.source import SourceRunner
from timeshift_btrfs_sync.state import STATE_VERSION


class CleanupSupersededCacheModeTests(unittest.TestCase):
    def _config_path(self, directory: str, *, mode: str, enabled: bool = True) -> Path:
        template = (
            Path(__file__).parents[1]
            / "timeshift_btrfs_sync"
            / "data"
            / "config.example.toml"
        )
        text = template.read_text(encoding="utf-8")
        text = text.replace('\nmode = "ssh"', f'\nmode = "{mode}"', 1)
        text = text.replace(
            "cleanup_superseded_cache = true",
            f"cleanup_superseded_cache = {'true' if enabled else 'false'}",
            1,
        )
        path = Path(directory) / f"config-{mode}.toml"
        path.write_text(text, encoding="utf-8")
        return path

    def test_current_option_loads_for_local_and_ssh_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            for mode, expected_ssh in (("local", False), ("ssh", True)):
                with self.subTest(mode=mode):
                    config = load_config(self._config_path(directory, mode=mode))
                    self.assertTrue(config.source.cleanup_superseded_cache)
                    self.assertEqual(SourceRunner.from_config(config).uses_ssh, expected_ssh)

    def test_sync_accepts_option_for_local_and_remote_transfer_modes(self):
        with tempfile.TemporaryDirectory() as directory:
            for mode, expected_ssh in (("local", False), ("ssh", True)):
                with self.subTest(mode=mode):
                    path = self._config_path(directory, mode=mode)
                    args = argparse.Namespace(
                        config=str(path),
                        dry_run=True,
                        run=False,
                        limit=None,
                        snapshot=None,
                        resend=False,
                        prune=False,
                        yes_delete=False,
                    )
                    state = {"version": STATE_VERSION, "snapshots": {}}
                    seen: list[tuple[bool, bool]] = []

                    def fake_sync(config, _state, **_kwargs):
                        seen.append(
                            (
                                config.source.cleanup_superseded_cache,
                                SourceRunner.from_config(config).uses_ssh,
                            )
                        )

                    with (
                        patch.object(cli, "_with_logging", side_effect=lambda _cfg, _name, callback, **_kwargs: callback()),
                        patch.object(cli, "_load_config_state", return_value=state),
                        patch.object(cli, "sync_once", side_effect=fake_sync),
                    ):
                        self.assertEqual(cli.cmd_sync(args), 0)

                    self.assertEqual(seen, [(True, expected_ssh)])

    def test_prune_after_transfer_builds_correct_local_or_ssh_cache_runner(self):
        snapshot_name = "2026-07-17_14-00-02"
        state = {"version": STATE_VERSION, "snapshots": {snapshot_name: {}}}
        plan = PrunePlan(delete={snapshot_name})

        with tempfile.TemporaryDirectory() as directory:
            for mode, expected_ssh in (("local", False), ("ssh", True)):
                with self.subTest(mode=mode):
                    config = load_config(self._config_path(directory, mode=mode))
                    seen_runners: list[bool] = []

                    def fake_delete(_config, _state, _plan, runner, _name, **_kwargs):
                        self.assertIsNotNone(runner)
                        seen_runners.append(runner.uses_ssh)
                        return True

                    with (
                        patch.object(retention, "build_prune_plan", return_value=plan),
                        patch.object(retention, "print_prune_plan"),
                        patch.object(retention.inventory, "build_source_btrfs_index", return_value=None),
                        patch.object(retention, "_delete_prune_item", side_effect=fake_delete),
                        patch.object(retention, "save_state"),
                    ):
                        retention.prune(config, state, dry_run=False, yes_delete=True)

                    self.assertEqual(seen_runners, [expected_ssh])


    def test_destroy_leftovers_accepts_option_for_all_targets_in_both_modes(self):
        with tempfile.TemporaryDirectory() as directory:
            target_modes = (
                (True, False, False),
                (False, True, False),
                (False, False, True),
            )
            for mode, expected_ssh in (("local", False), ("ssh", True)):
                for delete_source, delete_destination, delete_both in target_modes:
                    with self.subTest(
                        mode=mode,
                        delete_source=delete_source,
                        delete_destination=delete_destination,
                        delete_both=delete_both,
                    ):
                        path = self._config_path(directory, mode=mode)
                        args = argparse.Namespace(
                            config=str(path),
                            run=False,
                            delete_source=delete_source,
                            delete_destination=delete_destination,
                            delete_both=delete_both,
                            i_understand_this_destroys_data=False,
                        )
                        seen: list[tuple[bool, bool, bool, bool]] = []

                        def fake_destroy(config, **kwargs):
                            seen.append((
                                config.source.cleanup_superseded_cache,
                                SourceRunner.from_config(config).uses_ssh,
                                kwargs["delete_source"],
                                kwargs["delete_destination"],
                            ))

                        with (
                            patch.object(cli, "_safe_destroy_log_dir", return_value=None),
                            patch.object(cli, "_with_logging", side_effect=lambda _cfg, _name, callback, **_kwargs: callback()),
                            patch.object(cli, "destroy_leftovers", side_effect=fake_destroy),
                        ):
                            self.assertEqual(cli.cmd_destroy_leftovers(args), 0)

                        self.assertEqual(
                            seen,
                            [(
                                True,
                                expected_ssh,
                                delete_source or delete_both,
                                delete_destination or delete_both,
                            )],
                        )

    def test_accidental_rename_is_not_part_of_current_config_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._config_path(directory, mode="local")
            text = path.read_text(encoding="utf-8").replace(
                "cleanup_superseded_cache = true",
                "cleanup_cache_during_prune = true",
                1,
            )
            path.write_text(text, encoding="utf-8")
            with self.assertRaisesRegex(Exception, "cleanup_cache_during_prune"):
                load_config(path)

    def test_disabled_option_skips_cache_runner_in_both_modes(self):
        snapshot_name = "2026-07-17_14-00-02"
        state = {"version": STATE_VERSION, "snapshots": {snapshot_name: {}}}
        plan = PrunePlan(delete={snapshot_name})

        with tempfile.TemporaryDirectory() as directory:
            for mode in ("local", "ssh"):
                with self.subTest(mode=mode):
                    config = load_config(self._config_path(directory, mode=mode, enabled=False))
                    seen_runners = []

                    def fake_delete(_config, _state, _plan, runner, _name, **_kwargs):
                        seen_runners.append(runner)
                        return True

                    with (
                        patch.object(retention, "build_prune_plan", return_value=plan),
                        patch.object(retention, "print_prune_plan"),
                        patch.object(retention.inventory, "build_source_btrfs_index", return_value=None),
                        patch.object(retention, "_delete_prune_item", side_effect=fake_delete),
                        patch.object(retention, "save_state"),
                    ):
                        retention.prune(config, state, dry_run=False, yes_delete=True)

                    self.assertEqual(seen_runners, [None])


if __name__ == "__main__":
    unittest.main()
