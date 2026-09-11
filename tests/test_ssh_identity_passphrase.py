from __future__ import annotations

import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest

from timeshift_btrfs_sync.config import ConfigError, load_config
from timeshift_btrfs_sync.source import SourceRunner
from timeshift_btrfs_sync.ssh import SSHConfig, SSHRunner


class SSHIdentityPassphraseTests(unittest.TestCase):
    def test_password_only_keeps_established_sshpass_path(self) -> None:
        config = SSHConfig(host="backup", password="login-secret")
        self.assertEqual(config.base_command()[:3], ["sshpass", "-e", "ssh"])
        self.assertEqual(config.environment(), {"SSHPASS": "login-secret"})

    def test_identity_passphrase_uses_prompt_aware_askpass_without_sshpass(self) -> None:
        config = SSHConfig(
            host="backup",
            identity_file="/root/.ssh/backup-key",
            identity_passphrase="key-secret",
        )
        command = config.base_command()
        self.assertEqual(command[0], "ssh")
        self.assertNotIn("sshpass", command)

        env = config.environment()
        assert env is not None
        helper = Path(env["SSH_ASKPASS"])
        self.assertTrue(helper.is_file())
        self.assertEqual(stat.S_IMODE(helper.stat().st_mode), 0o700)
        self.assertEqual(env["SSH_ASKPASS_REQUIRE"], "force")
        self.assertEqual(env["TSBTRFS_IDENTITY_PASSPHRASE"], "key-secret")
        self.assertNotIn("TSBTRFS_SSH_PASSWORD", env)

    def test_distinct_key_and_account_secrets_are_dispatched_by_prompt(self) -> None:
        config = SSHConfig(
            host="backup",
            identity_file="/root/.ssh/backup-key",
            identity_passphrase="key-secret",
            password="login-secret",
        )
        env = config.environment()
        assert env is not None
        helper = env["SSH_ASKPASS"]
        child_env = os.environ.copy()
        child_env.update(env)

        key_prompt = subprocess.run(
            [helper, "Enter passphrase for key '/root/.ssh/backup-key':"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=child_env,
        )
        self.assertEqual(key_prompt.returncode, 0)
        self.assertEqual(key_prompt.stdout, "key-secret\n")

        password_prompt = subprocess.run(
            [helper, "root@backup's password:"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=child_env,
        )
        self.assertEqual(password_prompt.returncode, 0)
        self.assertEqual(password_prompt.stdout, "login-secret\n")

        unknown_prompt = subprocess.run(
            [helper, "Are you sure you want to continue connecting?"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=child_env,
        )
        self.assertNotEqual(unknown_prompt.returncode, 0)
        self.assertEqual(unknown_prompt.stdout, "")

    def test_identity_passphrase_file_is_read_without_final_newline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            secret_file = Path(tmp) / "key.passphrase"
            secret_file.write_text("file-secret\n", encoding="utf-8")
            config = SSHConfig(
                host="backup",
                identity_file="/root/.ssh/backup-key",
                identity_passphrase_file=str(secret_file),
            )
            env = config.environment()
        assert env is not None
        self.assertEqual(env["TSBTRFS_IDENTITY_PASSPHRASE"], "file-secret")

    def test_empty_identity_passphrase_file_is_refused_at_use(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            secret_file = Path(tmp) / "key.passphrase"
            secret_file.write_text("\n", encoding="utf-8")
            config = SSHConfig(
                host="backup",
                identity_file="/root/.ssh/backup-key",
                identity_passphrase_file=str(secret_file),
            )
            with self.assertRaisesRegex(ValueError, "identity_passphrase"):
                config.environment()

    def test_ssh_runner_and_streaming_runner_share_prompt_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake_ssh = Path(tmp) / "ssh"
            fake_ssh.write_text(
                "#!/bin/sh\n"
                "key=$($SSH_ASKPASS \"Enter passphrase for key '/root/.ssh/backup-key':\") || exit 20\n"
                "password=$($SSH_ASKPASS \"root@backup's password:\") || exit 21\n"
                "[ \"$key\" = key-secret ] || exit 22\n"
                "[ \"$password\" = login-secret ] || exit 23\n"
                "printf connected\n",
                encoding="utf-8",
            )
            fake_ssh.chmod(0o700)
            config = SSHConfig(
                host="backup",
                user="root",
                identity_file="/root/.ssh/backup-key",
                identity_passphrase="key-secret",
                password="login-secret",
            )
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{tmp}:{old_path}"
            try:
                SSHRunner(config).test()
                source = SourceRunner.from_mode("ssh", config)
                self.assertEqual(source.environment(), config.environment())
            finally:
                os.environ["PATH"] = old_path


class SSHIdentityPassphraseConfigTests(unittest.TestCase):
    def _write_config(self, tmp: str, ssh_lines: list[str], *, batch_mode: bool = False) -> Path:
        extra = '["-o", "BatchMode=yes"]' if batch_mode else '["-o", "ConnectTimeout=15"]'
        text = f'''name = "test"
state_file = "{tmp}/state.json"
lock_file = "{tmp}/lock"

[restore]
mode = "local"

[ssh]
host = "backup"
{chr(10).join(ssh_lines)}
extra_args = {extra}

[source]
mode = "ssh"
snapshot_root = "/snapshots"
cache_root = "/cache"
subvolumes = ["@", "@home"]

[destination]
target_root = "{tmp}/target"
'''
        path = Path(tmp) / "config.toml"
        path.write_text(text, encoding="utf-8")
        return path

    def test_loader_accepts_direct_identity_passphrase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_config(
                tmp,
                [
                    'identity_file = "/root/.ssh/backup-key"',
                    'identity_passphrase = "key-secret"',
                ],
            )
            config = load_config(path)
        assert config.ssh is not None
        self.assertEqual(config.ssh.identity_passphrase, "key-secret")

    def test_loader_accepts_identity_passphrase_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            passphrase_file = Path(tmp) / "identity.passphrase"
            passphrase_file.write_text("key-secret\n", encoding="utf-8")
            path = self._write_config(
                tmp,
                [
                    'identity_file = "/root/.ssh/backup-key"',
                    f'identity_passphrase_file = "{passphrase_file}"',
                ],
            )
            config = load_config(path)
        assert config.ssh is not None
        self.assertEqual(config.ssh.identity_passphrase_file, str(passphrase_file))

    def test_loader_rejects_both_identity_passphrase_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            passphrase_file = Path(tmp) / "identity.passphrase"
            passphrase_file.write_text("key-secret\n", encoding="utf-8")
            path = self._write_config(
                tmp,
                [
                    'identity_file = "/root/.ssh/backup-key"',
                    'identity_passphrase = "key-secret"',
                    f'identity_passphrase_file = "{passphrase_file}"',
                ],
            )
            with self.assertRaisesRegex(ConfigError, "either ssh.identity_passphrase"):
                load_config(path)

    def test_loader_requires_identity_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_config(tmp, ['identity_passphrase = "key-secret"'])
            with self.assertRaisesRegex(ConfigError, "requires ssh.identity_file"):
                load_config(path)

    def test_loader_rejects_batch_mode_with_identity_passphrase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_config(
                tmp,
                [
                    'identity_file = "/root/.ssh/backup-key"',
                    'identity_passphrase = "key-secret"',
                ],
                batch_mode=True,
            )
            with self.assertRaisesRegex(ConfigError, "cannot be used with BatchMode=yes"):
                load_config(path)


if __name__ == "__main__":
    unittest.main()
