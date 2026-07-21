from __future__ import annotations

import contextlib
import io
import re
import tempfile
import unittest
from importlib.resources import files
from pathlib import Path

from timeshift_btrfs_sync.cli import build_parser, cmd_init_config
from timeshift_btrfs_sync.config import (
    DESTINATION_KEYS,
    MAIL_KEYS,
    MANUAL_SNAPSHOT_KEYS,
    MQTT_KEYS,
    RETENTION_KEYS,
    RESTORE_KEYS,
    SOURCE_KEYS,
    SSH_KEYS,
    STREAM_KEYS,
    TOP_LEVEL_KEYS,
    load_config,
)


ROOT = Path(__file__).parents[1]
DATA = ROOT / "timeshift_btrfs_sync" / "data"
TEMPLATES = {
    "sync": DATA / "config.example.toml",
    "restore-pull": DATA / "config.restore-pull.example.toml",
}


class ConfigProfileTests(unittest.TestCase):
    def _write_profile(self, profile: str) -> str:
        parser = build_parser()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "config.toml"
            args = parser.parse_args(
                ["init-config", "--profile", profile, "--path", str(output)]
            )
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(cmd_init_config(args), 0)
            return output.read_text(encoding="utf-8")


    def test_both_profiles_are_packaged_resources(self):
        data = files("timeshift_btrfs_sync").joinpath("data")
        for name in ("config.example.toml", "config.restore-pull.example.toml"):
            text = data.joinpath(name).read_text(encoding="utf-8")
            self.assertIn("[ssh]", text)
            self.assertIn("password_file", text)

    def test_init_config_sync_profile_matches_packaged_template(self):
        self.assertEqual(
            self._write_profile("sync"),
            TEMPLATES["sync"].read_text(encoding="utf-8"),
        )

    def test_init_config_restore_pull_profile_matches_packaged_template(self):
        self.assertEqual(
            self._write_profile("restore-pull"),
            TEMPLATES["restore-pull"].read_text(encoding="utf-8"),
        )

    def test_restore_pull_profile_loads_remote_backup_ssh_settings(self):
        config = load_config(TEMPLATES["restore-pull"])
        self.assertEqual(config.source.mode, "local")
        self.assertIsNotNone(config.ssh)
        self.assertEqual(config.ssh.host, "backup-machine.example.lan")
        self.assertEqual(config.ssh.user, "ts-btrfs-restore-user")
        self.assertFalse(config.manual_snapshot.enabled)
        self.assertEqual(config.restore.mode, "ssh")
        self.assertEqual(
            config.state_file,
            Path("/Backups/Kubuntu/timeshift-btrfs/.ts-btrfs-sync/state.json"),
        )
        self.assertEqual(
            config.lock_file,
            Path("/media/darkyere/OS-Root/timeshift-btrfs/.ts-btrfs-sync/restore.lock"),
        )

    def test_sync_profile_keeps_local_backup_transport_default(self):
        config = load_config(TEMPLATES["sync"])
        self.assertEqual(config.restore.mode, "local")

    def test_every_current_option_is_documented_in_both_profiles(self):
        expected = {
            None: TOP_LEVEL_KEYS - {
                "source", "destination", "stream", "retention", "manual_snapshot",
                "mqtt", "mail", "ssh", "restore",
            },
            "source": SOURCE_KEYS,
            "destination": DESTINATION_KEYS,
            "stream": STREAM_KEYS,
            "retention": RETENTION_KEYS,
            "manual_snapshot": MANUAL_SNAPSHOT_KEYS,
            "mqtt": MQTT_KEYS,
            "mail": MAIL_KEYS,
            "ssh": SSH_KEYS,
            "restore": RESTORE_KEYS,
        }
        assignment = re.compile(r"^\s*#?\s*([A-Za-z_][A-Za-z0-9_]*)\s*=")
        section = re.compile(r"^\s*\[([A-Za-z_][A-Za-z0-9_]*)\]\s*$")

        for profile, path in TEMPLATES.items():
            found = {name: set() for name in expected}
            current = None
            for line in path.read_text(encoding="utf-8").splitlines():
                section_match = section.match(line)
                if section_match:
                    current = section_match.group(1)
                    continue
                assignment_match = assignment.match(line)
                if assignment_match and current in found:
                    found[current].add(assignment_match.group(1))
            for table, keys in expected.items():
                missing = sorted(keys - found[table])
                self.assertFalse(
                    missing,
                    f"{profile} profile is missing documented {table or 'top-level'} keys: {missing}",
                )

    def test_ssh_password_and_connection_examples_are_commented(self):
        for path in TEMPLATES.values():
            text = path.read_text(encoding="utf-8")
            for required in (
                '# password = "your-ssh-password"',
                '# password_file = "/root/.config/ts-btrfs/ssh.password"',
                'sudo apt install sshpass',
                'NumberOfPasswordPrompts=1',
                'ConnectTimeout=15',
                'ServerAliveInterval=30',
                'StrictHostKeyChecking=yes',
                'UserKnownHostsFile=/root/.ssh/known_hosts',
                'jump-user@jump-host',
            ):
                self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
