"""Unified command endpoints for local and source-side operations.

Business logic should depend on :class:`CommandEndpoint`, not on separate local
and SSH helper functions.  The endpoint owns only command transport; Btrfs,
Timeshift, inventory, cache, and workflow policy remain in their own layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import shlex

from .commands import Completed, quote_join, run_local
from .source import SourceRunner


@dataclass(slots=True)
class CommandEndpoint:
    """Execute commands on one local or source-side endpoint.

    ``source`` is set for both SSH and local-source mode.  A destination/local
    endpoint has ``source=None`` and executes argv directly on this machine.
    """

    source: SourceRunner | None = None
    label: str = "destination"

    @classmethod
    def for_source(cls, source: SourceRunner) -> "CommandEndpoint":
        return cls(source=source, label=source.location)

    @classmethod
    def local(cls, label: str = "destination") -> "CommandEndpoint":
        return cls(source=None, label=label)

    @property
    def location(self) -> str:
        return self.source.location if self.source else "local"

    def shell_command(self, argv: Iterable[str]) -> str:
        """Return a safely quoted shell command for this endpoint."""

        return quote_join(str(part) for part in argv)

    def command(self, argv: Iterable[str]) -> list[str]:
        """Return process argv for a command executed on this endpoint."""

        parts = [str(part) for part in argv]
        if self.source is not None:
            return self.source.command(self.shell_command(parts))
        return parts

    def run_argv(
        self,
        argv: Iterable[str],
        *,
        check: bool = True,
        log_stderr: bool = True,
        mirror_stderr: bool = True,
        mirror_stdout_on_failure: bool = False,
    ) -> Completed:
        """Execute one argv command through the endpoint transport."""

        parts = [str(part) for part in argv]
        if self.source is not None:
            return self.source.run(
                self.shell_command(parts),
                check=check,
                log_stderr=log_stderr,
                mirror_stderr=mirror_stderr,
                mirror_stdout_on_failure=mirror_stdout_on_failure,
            )
        return run_local(
            parts,
            check=check,
            log_stderr=log_stderr,
            mirror_stderr=mirror_stderr,
            mirror_stdout_on_failure=mirror_stdout_on_failure,
        )

    def run_shell(
        self,
        script: str,
        *,
        check: bool = True,
        log_stderr: bool = True,
        mirror_stderr: bool = True,
        mirror_stdout_on_failure: bool = False,
    ) -> Completed:
        """Execute one shell script through the endpoint transport."""

        if self.source is not None:
            return self.source.run(
                "sh -c " + shlex.quote(script),
                check=check,
                log_stderr=log_stderr,
                mirror_stderr=mirror_stderr,
                mirror_stdout_on_failure=mirror_stdout_on_failure,
            )
        return run_local(
            ["sh", "-c", script],
            check=check,
            log_stderr=log_stderr,
            mirror_stderr=mirror_stderr,
            mirror_stdout_on_failure=mirror_stdout_on_failure,
        )

