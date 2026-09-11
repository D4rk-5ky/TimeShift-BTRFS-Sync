"""SSH command construction.

Supports key-based authentication, encrypted private-key passphrases, optional
remote account password authentication, SSH compression, and a chosen SSH
cipher.
"""

from __future__ import annotations

import atexit
from dataclasses import dataclass, field
import os
from pathlib import Path
import shutil
import tempfile
import threading

from .commands import Completed, CommandError, run_local


_ASKPASS_HELPER_LOCK = threading.Lock()
_ASKPASS_HELPER_DIR: Path | None = None
_ASKPASS_HELPER_PATH: Path | None = None


_ASKPASS_SCRIPT = """#!/bin/sh
prompt=${1-}
case "$prompt" in
    *passphrase*|*Passphrase*)
        [ -n "${TSBTRFS_IDENTITY_PASSPHRASE-}" ] || exit 1
        printf '%s\n' "$TSBTRFS_IDENTITY_PASSPHRASE"
        ;;
    *password*|*Password*)
        [ -n "${TSBTRFS_SSH_PASSWORD-}" ] || exit 1
        printf '%s\n' "$TSBTRFS_SSH_PASSWORD"
        ;;
    *)
        # Never approve host-key questions, confirmation prompts, or unknown
        # keyboard-interactive challenges automatically.
        exit 1
        ;;
esac
"""


def _is_relative_to(path: Path, root: Path) -> bool:
    """Return True when path is root or below root without broad string matching."""

    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _cleanup_askpass_helper() -> None:
    """Remove the process-private askpass helper directory at normal exit."""

    global _ASKPASS_HELPER_DIR, _ASKPASS_HELPER_PATH
    directory = _ASKPASS_HELPER_DIR
    _ASKPASS_HELPER_DIR = None
    _ASKPASS_HELPER_PATH = None
    if directory is not None:
        shutil.rmtree(directory, ignore_errors=True)


def _ensure_askpass_helper() -> Path:
    """Create and return one private prompt-dispatch helper for this process.

    The helper contains no secret. Secrets are inherited only by the SSH child
    process and are selected according to the prompt text: private-key
    passphrase prompts receive the identity passphrase, while remote account
    password prompts receive the SSH account password. Unknown prompts fail
    closed instead of being approved automatically.
    """

    global _ASKPASS_HELPER_DIR, _ASKPASS_HELPER_PATH
    with _ASKPASS_HELPER_LOCK:
        if _ASKPASS_HELPER_PATH is not None and _ASKPASS_HELPER_PATH.is_file():
            return _ASKPASS_HELPER_PATH

        directory = Path(tempfile.mkdtemp(prefix=f"ts-btrfs-askpass-{os.geteuid()}-"))
        directory.chmod(0o700)
        helper = directory / "askpass"
        fd = os.open(helper, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o700)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(_ASKPASS_SCRIPT)
                handle.flush()
                os.fsync(handle.fileno())
        except Exception:
            shutil.rmtree(directory, ignore_errors=True)
            raise
        helper.chmod(0o700)

        _ASKPASS_HELPER_DIR = directory
        _ASKPASS_HELPER_PATH = helper
        atexit.register(_cleanup_askpass_helper)
        return helper


def validate_control_path_safety(control_path: str | None) -> None:
    """Create and validate a private SSH ControlPath socket directory.

    OpenSSH ControlMaster creates a local Unix-domain control socket. Any local
    user that can access that socket may be able to reuse the already
    authenticated SSH connection without unlocking the private key again. The app
    therefore requires an explicit absolute ControlPath whose parent directory is
    owned by the current user and is not accessible by group or other users.

    If the parent directory does not exist, create it with mode 0700 for the user
    running ts-btrfs. Existing directories are never relaxed or ownership-fixed
    automatically; they must already be owned by the current user and private.
    Shared temporary locations are rejected even when a nested directory appears
    private, because they are easy to configure incorrectly.
    """

    if not control_path:
        raise ValueError(
            "ssh.control_path must be set when ssh.control_master is true; "
            "use a private directory such as /run/ts-btrfs-ssh/%C"
        )

    expanded = Path(control_path).expanduser()
    if not expanded.is_absolute():
        raise ValueError("ssh.control_path must be an absolute path when ssh.control_master is true")

    parent = expanded.parent
    unsafe_roots = [Path("/tmp"), Path("/var/tmp"), Path("/dev/shm")]
    for unsafe_root in unsafe_roots:
        if _is_relative_to(parent, unsafe_root):
            raise ValueError(
                f"ssh.control_path parent must not be inside shared temporary storage: {parent}. "
                "Use a private directory such as /run/ts-btrfs-ssh owned by the user running ts-btrfs."
            )

    if not parent.exists():
        missing_dirs: list[Path] = []
        cursor = parent
        while not cursor.exists():
            missing_dirs.append(cursor)
            cursor = cursor.parent
        try:
            parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            for created_dir in missing_dirs:
                created_dir.chmod(0o700)
        except OSError as exc:
            raise ValueError(
                f"failed creating ssh.control_path parent directory {parent}: {exc}. "
                "Create it as the user running ts-btrfs and set chmod 0700."
            ) from exc

    if not parent.is_dir():
        raise ValueError(f"ssh.control_path parent is not a directory: {parent}")

    stat_result = parent.stat()
    current_uid = os.geteuid()
    if stat_result.st_uid != current_uid:
        raise ValueError(
            f"ssh.control_path parent must be owned by the user running ts-btrfs: {parent}. "
            f"owner uid is {stat_result.st_uid}, current uid is {current_uid}."
        )

    if stat_result.st_mode & 0o077:
        raise ValueError(
            f"ssh.control_path parent must be private: {parent}. "
            "Run chmod 0700 on that directory before enabling ssh.control_master."
        )


@dataclass(slots=True)
class SSHConfig:
    """Connection and SSH transport settings."""

    host: str
    user: str | None = None
    port: int | None = None
    identity_file: str | None = None
    identity_passphrase: str | None = None
    identity_passphrase_file: str | None = None
    password: str | None = None
    password_file: str | None = None
    compression: bool = False
    cipher: str | None = None
    control_master: bool = False
    control_persist: str | None = None
    control_path: str | None = None
    extra_args: list[str] = field(default_factory=list)

    @property
    def target(self) -> str:
        """Return host or user@host."""

        return f"{self.user}@{self.host}" if self.user else self.host

    @property
    def uses_password_auth(self) -> bool:
        """Return True when a remote SSH account password is configured."""

        return bool(self.password or self.password_file)

    @property
    def uses_identity_passphrase(self) -> bool:
        """Return True when the configured private key needs an app-supplied passphrase."""

        return bool(self.identity_passphrase or self.identity_passphrase_file)

    @property
    def uses_askpass(self) -> bool:
        """Return True when prompt-aware OpenSSH askpass dispatch is required."""

        return self.uses_identity_passphrase

    @staticmethod
    def _read_secret(value: str | None, file_path: str | None, label: str) -> str | None:
        """Read one configured secret and reject an empty direct value or file."""

        if value is not None:
            secret = value
        elif file_path:
            secret = Path(file_path).expanduser().read_text(encoding="utf-8").rstrip("\r\n")
        else:
            return None
        if not secret:
            raise ValueError(f"{label} is empty")
        return secret

    def _read_password(self) -> str | None:
        """Read the remote SSH account password from TOML or password_file."""

        return self._read_secret(self.password, self.password_file, "ssh.password/password_file")

    def _read_identity_passphrase(self) -> str | None:
        """Read the private-key passphrase from TOML or identity_passphrase_file."""

        return self._read_secret(
            self.identity_passphrase,
            self.identity_passphrase_file,
            "ssh.identity_passphrase/identity_passphrase_file",
        )

    def environment(self) -> dict[str, str] | None:
        """Return authentication environment for sshpass or OpenSSH askpass.

        Password-only authentication keeps the established ``sshpass -e`` path.
        When an identity passphrase is configured, a prompt-aware askpass helper
        is used instead so a key passphrase and a different remote account
        password can both be supplied correctly.
        """

        password = self._read_password()
        identity_passphrase = self._read_identity_passphrase()
        if identity_passphrase is not None:
            env = {
                "SSH_ASKPASS": str(_ensure_askpass_helper()),
                "SSH_ASKPASS_REQUIRE": "force",
                "DISPLAY": os.environ.get("DISPLAY") or "ts-btrfs-sync:0",
                "TSBTRFS_IDENTITY_PASSPHRASE": identity_passphrase,
            }
            if password is not None:
                env["TSBTRFS_SSH_PASSWORD"] = password
            return env
        if password is not None:
            return {"SSHPASS": password}
        return None

    def base_command(self) -> list[str]:
        """Build base SSH argv; remote command is appended later."""

        cmd: list[str] = []
        # sshpass is retained for the established account-password-only path.
        # When an encrypted identity is configured, OpenSSH askpass handles both
        # the key passphrase and an optional separate account password.
        if self.uses_password_auth and not self.uses_askpass:
            cmd += ["sshpass", "-e"]
        cmd.append("ssh")
        if self.port:
            cmd += ["-p", str(self.port)]
        if self.identity_file:
            cmd += ["-i", self.identity_file]
        if self.compression:
            cmd += ["-C"]
        if self.cipher:
            cmd += ["-c", self.cipher]
        if self.control_master:
            cmd += ["-o", "ControlMaster=auto"]
            cmd += ["-o", f"ControlPersist={self.control_persist or '10m'}"]
            if self.control_path:
                cmd += ["-o", f"ControlPath={self.control_path}"]
        cmd += self.extra_args
        cmd.append(self.target)
        return cmd


class SSHRunner:
    """Run remote commands through SSH."""

    def __init__(self, config: SSHConfig):
        self.config = config

    def command(self, remote_command: str) -> list[str]:
        """Return argv for one SSH remote command."""

        return self.config.base_command() + [remote_command]

    def run(
        self,
        remote_command: str,
        *,
        check: bool = True,
        log_stderr: bool = True,
        mirror_stderr: bool = True,
        mirror_stdout_on_failure: bool = False,
    ) -> Completed:
        """Run a remote command and capture stdout/stderr.

        By default stderr is mirrored to the terminal and to .err when file
        logging is enabled. Expected negative probes can pass
        ``log_stderr=False`` and ``mirror_stderr=False`` to keep harmless
        "not found" checks out of the error stream.
        """

        return run_local(
            self.command(remote_command),
            check=check,
            env=self.config.environment(),
            log_stderr=log_stderr,
            mirror_stderr=mirror_stderr,
            mirror_stdout_on_failure=mirror_stdout_on_failure,
        )

    def environment(self) -> dict[str, str] | None:
        """Return SSH environment for streaming pipeline calls."""

        return self.config.environment()

    def test(self) -> None:
        """Verify SSH works and stdout is not polluted by banners."""

        result = self.run("printf connected", check=True)
        if result.stdout != "connected":
            raise CommandError(self.command("printf connected"), 1, result.stdout, result.stderr)
