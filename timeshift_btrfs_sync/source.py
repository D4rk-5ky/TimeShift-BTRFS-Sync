"""Command runner for local or SSH Timeshift and backup endpoints."""

from __future__ import annotations

from dataclasses import dataclass

from .commands import Completed, CommandError, run_local
from .ssh import SSHConfig, SSHRunner


@dataclass(slots=True)
class SourceRunner:
    """Run commands through one local or SSH endpoint.

    Normal workflows use this as the Timeshift source endpoint. Pull restore
    also uses it for the SSH backup endpoint, allowing both directions to share
    one transport implementation.
    """

    mode: str
    ssh: SSHRunner | None = None

    @classmethod
    def from_mode(cls, mode: str, ssh_config: SSHConfig | None) -> "SourceRunner":
        """Create a local or SSH command runner from one validated mode."""

        if mode == "local":
            return cls(mode="local")
        if mode != "ssh":
            raise ValueError(f"unsupported command endpoint mode: {mode}")
        if ssh_config is None:
            raise ValueError("SSH mode was requested but no SSH configuration was loaded")
        return cls(mode="ssh", ssh=SSHRunner(ssh_config))

    @classmethod
    def from_config(cls, config) -> "SourceRunner":
        """Create the configured Timeshift source runner."""

        return cls.from_mode(config.source.mode, config.ssh)

    @property
    def uses_ssh(self) -> bool:
        """Return True when source commands are executed through SSH."""

        return self.ssh is not None

    @property
    def location(self) -> str:
        """Return the metadata location label used by Btrfs helpers."""

        return "remote" if self.uses_ssh else "local"

    def command(self, source_shell_command: str) -> list[str]:
        """Return argv that runs one source-side shell command."""

        if self.ssh is not None:
            return self.ssh.command(source_shell_command)
        return ["sh", "-c", source_shell_command]

    def run(
        self,
        source_shell_command: str,
        *,
        check: bool = True,
        log_stderr: bool = True,
        mirror_stderr: bool = True,
        mirror_stdout_on_failure: bool = False,
    ) -> Completed:
        """Run one source-side command and capture stdout/stderr."""

        if self.ssh is not None:
            return self.ssh.run(
                source_shell_command,
                check=check,
                log_stderr=log_stderr,
                mirror_stderr=mirror_stderr,
                mirror_stdout_on_failure=mirror_stdout_on_failure,
            )
        return run_local(
            self.command(source_shell_command),
            check=check,
            log_stderr=log_stderr,
            mirror_stderr=mirror_stderr,
            mirror_stdout_on_failure=mirror_stdout_on_failure,
        )

    def environment(self) -> dict[str, str] | None:
        """Return environment needed for streaming source commands."""

        if self.ssh is None:
            return None
        return self.ssh.environment()

    def test(self) -> None:
        """Verify that the source command endpoint is usable."""

        if self.ssh is not None:
            self.ssh.test()
            return
        result = self.run("printf connected", check=True)
        if result.stdout != "connected":
            raise CommandError(self.command("printf connected"), 1, result.stdout, result.stderr)
