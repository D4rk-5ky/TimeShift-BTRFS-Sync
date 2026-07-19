"""Local and SSH-held file locks for backup operations."""

from __future__ import annotations

from pathlib import Path
import fcntl
import select
import shlex
import subprocess

from .source import SourceRunner


class FileLock:
    """flock() based non-blocking exclusive lock on the local machine."""

    def __init__(self, path: Path):
        self.path = path
        self._fh = None

    def __enter__(self):
        if not self.path.parent.is_dir():
            raise FileNotFoundError(
                f"Lock directory does not exist or is not a directory: {self.path.parent}. "
                "Real sync/prune should create it during lock path preflight before FileLock opens the lock file."
            )
        self._fh = self.path.open("w")
        fcntl.flock(self._fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        self._fh.write("locked\n")
        self._fh.flush()
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._fh:
            fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
            self._fh.close()


class RemoteFileLock:
    """Hold the configured backup lock through one persistent SSH command.

    The remote shell opens the same lock file used by local sync/prune and holds
    an advisory ``flock`` until this process closes SSH stdin. This prevents a
    remote backup from being pruned or changed while it is being pulled for a
    local restore.
    """

    _LOCKED_MARKER = "TSBTRFS_REMOTE_LOCKED"
    _BUSY_MARKER = "TSBTRFS_REMOTE_LOCK_BUSY"

    def __init__(self, path: str | Path, runner: SourceRunner, *, timeout: int = 30):
        if not runner.uses_ssh:
            raise ValueError("RemoteFileLock requires an SSH command runner")
        self.path = str(path)
        self.runner = runner
        self.timeout = timeout
        self._proc: subprocess.Popen[str] | None = None

    def __enter__(self):
        script = f"""
lock_file={shlex.quote(self.path)}
exec 9>>"$lock_file" || exit 70
if ! flock -n 9; then
    printf '{self._BUSY_MARKER}\\n'
    exit 71
fi
printf '{self._LOCKED_MARKER}\\n'
cat >/dev/null
""".strip()
        command = self.runner.command("sh -c " + shlex.quote(script))
        self._proc = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=self.runner.environment(),
        )
        assert self._proc.stdout is not None
        ready, _, _ = select.select([self._proc.stdout], [], [], self.timeout)
        if not ready:
            self._terminate()
            raise TimeoutError(f"Timed out acquiring remote backup lock: {self.path}")
        marker = self._proc.stdout.readline().strip()
        if marker == self._LOCKED_MARKER:
            return self
        if marker == self._BUSY_MARKER:
            proc = self._proc
            self._proc = None
            returncode = proc.wait(timeout=5)
            stderr = proc.stderr.read().strip() if proc.stderr is not None else ""
            detail = stderr or f"return code {returncode}"
            raise BlockingIOError(f"Remote backup lock is already held: {self.path} ({detail})")
        self._terminate()
        detail = marker or "no lock acknowledgement was returned"
        raise RuntimeError(f"Could not acquire remote backup lock {self.path}: unexpected response: {detail}")

    def _terminate(self) -> None:
        proc = self._proc
        self._proc = None
        if proc is None:
            return
        if proc.stdin is not None:
            try:
                proc.stdin.close()
            except OSError:
                pass
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()

    def __exit__(self, exc_type, exc, tb):
        self._terminate()
