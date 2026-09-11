from __future__ import annotations

import io
import subprocess
import unittest
from unittest.mock import patch

from timeshift_btrfs_sync.lock import RemoteFileLock


class FakeRunner:
    uses_ssh = True

    def __init__(self):
        self.commands: list[str] = []

    def command(self, shell_command: str) -> list[str]:
        self.commands.append(shell_command)
        return ["ssh", "backup", shell_command]

    def environment(self):
        return {"SSHPASS": "secret"}


class FakeStdin(io.StringIO):
    pass


class FakeProcess:
    def __init__(self, marker: str, *, stderr: str = "", returncode: int = 0):
        self.stdin = FakeStdin()
        self.stdout = io.StringIO(marker + "\n")
        self.stderr = io.StringIO(stderr)
        self.returncode = returncode
        self.terminated = False
        self.killed = False
        self.wait_calls = 0

    def wait(self, timeout=None):
        self.wait_calls += 1
        return self.returncode

    def terminate(self):
        self.terminated = True

    def kill(self):
        self.killed = True


class RemoteFileLockTests(unittest.TestCase):
    def test_holds_remote_flock_until_context_exit(self):
        runner = FakeRunner()
        process = FakeProcess(RemoteFileLock._LOCKED_MARKER)
        with (
            patch("timeshift_btrfs_sync.lock.subprocess.Popen", return_value=process) as popen,
            patch("timeshift_btrfs_sync.lock.select.select", return_value=([process.stdout], [], [])),
        ):
            with RemoteFileLock("/remote/backup/.ts-btrfs-sync/lock", runner):
                self.assertFalse(process.stdin.closed)

        self.assertTrue(process.stdin.closed)
        self.assertGreaterEqual(process.wait_calls, 1)
        command = runner.commands[0]
        self.assertIn("flock -n 9", command)
        self.assertIn("/remote/backup/.ts-btrfs-sync/lock", command)
        self.assertIn("cat >/dev/null", command)
        popen.assert_called_once()
        self.assertEqual(popen.call_args.kwargs["env"], {"SSHPASS": "secret"})

    def test_busy_remote_lock_raises_blocking_error(self):
        runner = FakeRunner()
        process = FakeProcess(RemoteFileLock._BUSY_MARKER, stderr="busy", returncode=71)
        with (
            patch("timeshift_btrfs_sync.lock.subprocess.Popen", return_value=process),
            patch("timeshift_btrfs_sync.lock.select.select", return_value=([process.stdout], [], [])),
        ):
            with self.assertRaisesRegex(BlockingIOError, "already held"):
                with RemoteFileLock("/remote/backup/.ts-btrfs-sync/lock", runner):
                    pass

    def test_timeout_terminates_remote_lock_process(self):
        runner = FakeRunner()
        process = FakeProcess("")
        with (
            patch("timeshift_btrfs_sync.lock.subprocess.Popen", return_value=process),
            patch("timeshift_btrfs_sync.lock.select.select", return_value=([], [], [])),
        ):
            with self.assertRaisesRegex(TimeoutError, "Timed out acquiring"):
                with RemoteFileLock("/remote/backup/.ts-btrfs-sync/lock", runner, timeout=1):
                    pass
        self.assertTrue(process.stdin.closed)

    def test_requires_ssh_runner(self):
        runner = FakeRunner()
        runner.uses_ssh = False
        with self.assertRaisesRegex(ValueError, "requires an SSH"):
            RemoteFileLock("/tmp/lock", runner)


if __name__ == "__main__":
    unittest.main()
