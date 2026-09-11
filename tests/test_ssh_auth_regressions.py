from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from timeshift_btrfs_sync.config import ConfigError, load_config
from timeshift_btrfs_sync.ssh import SSHConfig, SSHRunner, _cleanup_askpass_helper


class SSHAuthenticationRegressionTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup_askpass_helper()

    def _write_config(self, directory: Path, ssh_lines: str) -> Path:
        path = directory / "config.toml"
        path.write_text(
            """
name = "test"
[source]
mode = "ssh"
snapshot_root = "/timeshift/snapshots"
cache_root = "/timeshift/cache"
subvolumes = ["@"]
[destination]
target_root = "/backup"
[restore]
mode = "local"
[ssh]
host = "example.invalid"
""".lstrip()
            + ssh_lines,
            encoding="utf-8",
        )
        return path

    def test_password_only_behavior_still_uses_sshpass_environment(self) -> None:
        config = SSHConfig(host="example.invalid", user="backup", password="account-secret")
        self.assertEqual(config.environment(), {"SSHPASS": "account-secret"})
        self.assertEqual(config.base_command()[:3], ["sshpass", "-e", "ssh"])

    def test_direct_identity_passphrase_uses_prompt_aware_askpass(self) -> None:
        config = SSHConfig(
            host="example.invalid",
            identity_file="/keys/id_ed25519",
            identity_passphrase="key-secret",
        )
        env = config.environment()
        assert env is not None
        self.assertEqual(env["TSBTRFS_IDENTITY_PASSPHRASE"], "key-secret")
        self.assertEqual(env["SSH_ASKPASS_REQUIRE"], "force")
        self.assertNotIn("SSHPASS", env)
        self.assertEqual(config.base_command()[0], "ssh")
        self.assertNotIn("sshpass", config.base_command())

    def test_file_backed_identity_passphrase_allows_one_final_newline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            secret_file = Path(tmp) / "identity.passphrase"
            secret_file.write_text("file-secret\n", encoding="utf-8")
            config = SSHConfig(
                host="example.invalid",
                identity_file="/keys/id_ed25519",
                identity_passphrase_file=str(secret_file),
            )
            env = config.environment()
            assert env is not None
            self.assertEqual(env["TSBTRFS_IDENTITY_PASSPHRASE"], "file-secret")

    def test_key_and_account_secrets_can_be_distinct(self) -> None:
        config = SSHConfig(
            host="example.invalid",
            identity_file="/keys/id_ed25519",
            identity_passphrase="key-secret",
            password="account-secret",
        )
        env = config.environment()
        assert env is not None
        self.assertEqual(env["TSBTRFS_IDENTITY_PASSPHRASE"], "key-secret")
        self.assertEqual(env["TSBTRFS_SSH_PASSWORD"], "account-secret")
        self.assertNotIn("SSHPASS", env)
        self.assertNotIn("sshpass", config.base_command())

    def test_askpass_dispatches_key_and_account_prompts_and_refuses_unknown_prompt(self) -> None:
        config = SSHConfig(
            host="example.invalid",
            identity_file="/keys/id_ed25519",
            identity_passphrase="key-secret",
            password="account-secret",
        )
        env = config.environment()
        assert env is not None
        process_env = os.environ.copy()
        process_env.update(env)
        helper = env["SSH_ASKPASS"]

        key = subprocess.run(
            [helper, "Enter passphrase for key '/keys/id_ed25519':"],
            env=process_env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        account = subprocess.run(
            [helper, "backup@example.invalid's password:"],
            env=process_env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        unknown = subprocess.run(
            [helper, "Are you sure you want to continue connecting?"],
            env=process_env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual((key.returncode, key.stdout.rstrip()), (0, "key-secret"))
        self.assertEqual((account.returncode, account.stdout.rstrip()), (0, "account-secret"))
        self.assertNotEqual(unknown.returncode, 0)
        self.assertEqual(unknown.stdout, "")

    def test_batch_mode_yes_is_rejected_with_password_or_passphrase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_config(
                Path(tmp),
                'identity_file = "/keys/id_ed25519"\n'
                'identity_passphrase = "secret"\n'
                'extra_args = ["-o", "BatchMode=yes"]\n',
            )
            with self.assertRaisesRegex(ConfigError, "BatchMode=yes"):
                load_config(path)

    def test_identity_passphrase_requires_identity_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_config(Path(tmp), 'identity_passphrase = "secret"\n')
            with self.assertRaisesRegex(ConfigError, "requires ssh.identity_file"):
                load_config(path)

    def test_identity_passphrase_file_must_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_config(
                Path(tmp),
                'identity_file = "/keys/id_ed25519"\n'
                f'identity_passphrase_file = "{Path(tmp) / "missing.secret"}"\n',
            )
            with self.assertRaisesRegex(ConfigError, "does not exist"):
                load_config(path)

    def test_direct_and_file_secret_are_mutually_exclusive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            secret_file = Path(tmp) / "secret"
            secret_file.write_text("file-secret", encoding="utf-8")
            path = self._write_config(
                Path(tmp),
                'identity_file = "/keys/id_ed25519"\n'
                'identity_passphrase = "direct-secret"\n'
                f'identity_passphrase_file = "{secret_file}"\n',
            )
            with self.assertRaisesRegex(ConfigError, "either ssh.identity_passphrase"):
                load_config(path)

    def test_empty_secrets_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "ssh.password/password_file is empty"):
            SSHConfig(host="example.invalid", password="").environment()
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty.secret"
            empty.write_text("\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "identity_passphrase"):
                SSHConfig(
                    host="example.invalid",
                    identity_file="/keys/id_ed25519",
                    identity_passphrase_file=str(empty),
                ).environment()

    def test_runner_stream_environment_uses_same_authentication_builder(self) -> None:
        config = SSHConfig(
            host="example.invalid",
            identity_file="/keys/id_ed25519",
            identity_passphrase="key-secret",
        )
        runner = SSHRunner(config)
        self.assertEqual(runner.environment(), config.environment())
        self.assertEqual(runner.command("printf connected")[:-1], config.base_command())


if __name__ == "__main__":
    unittest.main()
