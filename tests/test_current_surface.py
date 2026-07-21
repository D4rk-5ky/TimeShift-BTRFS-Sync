from __future__ import annotations

import argparse
import tempfile
import unittest
from pathlib import Path

from timeshift_btrfs_sync.cli import build_parser
from timeshift_btrfs_sync.config import ConfigError, load_config
from timeshift_btrfs_sync.state import STATE_SUBVOLUME_KEYS, STATE_VERSION


EXPECTED_COMMANDS = {
    "init-config", "test-source", "list-source", "sync", "prune",
    "restore", "create-manual", "show-state", "clear-state", "delete-lock",
    "destroy-leftovers",
}
EXPECTED_MODULES = {
    "__init__", "__main__", "btrfs_ops", "cache_ops", "cli", "commands",
    "config", "destroy", "endpoint", "executor", "inventory", "lock", "log",
    "mail", "maintenance", "models", "mqtt", "notify", "paths",
    "payload_stats", "planning", "preflight", "restore", "retention",
    "source", "ssh", "state", "sync", "timeshift", "tree_ops",
}
EXPECTED_STATE_FIELDS = {
    "status", "name", "source_path", "send_path", "send_path_kind",
    "send_source_uuid", "original_source_uuid", "destination_path",
    "parent_snapshot", "parent_source_path", "parent_source_path_kind",
}


class CurrentPublicSurfaceTests(unittest.TestCase):
    def test_cli_contains_only_current_commands(self):
        parser = build_parser()
        subparsers = next(
            action for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        )
        self.assertEqual(set(subparsers.choices), EXPECTED_COMMANDS)

    def test_runtime_package_contains_only_current_modules(self):
        package = Path(__file__).parents[1] / "timeshift_btrfs_sync"
        modules = {path.stem for path in package.glob("*.py")}
        self.assertEqual(modules, EXPECTED_MODULES)

    def test_state_schema_contains_only_current_fields(self):
        self.assertEqual(STATE_VERSION, 3)
        self.assertEqual(STATE_SUBVOLUME_KEYS, EXPECTED_STATE_FIELDS)

    def test_local_config_does_not_construct_ssh_settings(self):
        template = Path(__file__).parents[1] / "timeshift_btrfs_sync/data/config.example.toml"
        text = template.read_text(encoding="utf-8").replace('\nmode = "ssh"', '\nmode = "local"', 1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.toml"
            path.write_text(text, encoding="utf-8")
            config = load_config(path)
        self.assertIsNone(config.ssh)

    def test_unknown_config_key_is_rejected(self):
        template = Path(__file__).parents[1] / "timeshift_btrfs_sync/data/config.example.toml"
        text = template.read_text(encoding="utf-8").replace(
            "[source]", "[source]\nnot_a_current_option = true", 1
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.toml"
            path.write_text(text, encoding="utf-8")
            with self.assertRaises(ConfigError):
                load_config(path)


if __name__ == "__main__":
    unittest.main()
