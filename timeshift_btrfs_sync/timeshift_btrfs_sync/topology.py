"""Command topology descriptions and safety checks.

The configuration intentionally reuses one ``[ssh]`` profile, but normal sync
and restore interpret it differently:

* ``sync`` uses only ``source.mode``. The backup destination is always local.
* ``restore`` uses only ``restore.mode`` to decide which side is remote.

Keeping that distinction in one module prevents a pull-restore profile from
silently being used to create a local backup that restore later expects to find
on the SSH host.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import AppConfig


class TopologyError(RuntimeError):
    """Raised when a command/config combination would use unintended hosts."""


@dataclass(frozen=True, slots=True)
class TopologyDescription:
    """Human-readable endpoint ownership for one command."""

    source_label: str
    destination_label: str
    detail: str


def _ssh_target(config: AppConfig) -> str:
    if config.ssh is None:
        return "SSH host (not configured)"
    user = getattr(config.ssh, "user", None) or "?"
    host = getattr(config.ssh, "host", None) or "?"
    return f"{user}@{host}"


def describe_sync_topology(config: AppConfig) -> TopologyDescription:
    """Return the endpoints actually used by ``sync``."""

    if config.source.mode == "ssh":
        source = f"SSH Timeshift source {_ssh_target(config)}"
    else:
        source = "local Timeshift source"
    destination = "local backup destination"
    detail = (
        f"sync reads {config.source.snapshot_root} from {source} and writes "
        f"{config.destination.target_root} on the machine running the command"
    )
    return TopologyDescription(source, destination, detail)


def describe_restore_topology(config: AppConfig) -> TopologyDescription:
    """Return the endpoints actually used by ``restore``."""

    mode = config.restore.mode
    if mode == "local":
        backup = "local backup repository"
        timeshift = "local Timeshift target"
    elif mode == "ssh":
        backup = f"SSH backup repository {_ssh_target(config)}"
        timeshift = "local Timeshift target"
    elif mode == "ssh-target":
        backup = "local backup repository"
        timeshift = f"SSH Timeshift target {_ssh_target(config)}"
    else:  # validated by config.py, retained as a defensive guard
        raise TopologyError(f"unsupported restore mode: {mode}")
    detail = (
        f"restore reads {config.destination.target_root}/snapshots from {backup} and writes "
        f"{config.source.snapshot_root} on {timeshift}"
    )
    return TopologyDescription(backup, timeshift, detail)


def reject_pull_restore_profile_for_sync(config: AppConfig) -> None:
    """Refuse ``sync`` with a profile whose restore backup lives over SSH.

    ``restore.mode = 'ssh'`` means ``destination.target_root`` is interpreted on
    the SSH host during restore. Normal sync never sends the destination over
    SSH; it always writes the same path locally. Running sync with such a
    pull-restore profile therefore creates a different repository from the one
    that restore will inspect. A separate sync config is required.
    """

    if config.restore.mode != "ssh":
        return
    ssh_target = _ssh_target(config)
    raise TopologyError(
        "Refusing to run sync with a pull-restore profile ([restore] mode = \"ssh\"). "
        "Normal sync always writes destination.target_root on the local machine, while this "
        f"restore profile reads that path from {ssh_target}. The [ssh] host is "
        f"{'used only by restore because source.mode is local' if config.source.mode == 'local' else 'used as the Timeshift source by sync, not as the backup destination'}. "
        "Use a dedicated sync config. For SSH Timeshift source -> local backup -> push restore "
        "back to the same SSH Timeshift host, use source.mode = \"ssh\" and restore.mode = "
        "\"ssh-target\" with the same [ssh] host."
    )
