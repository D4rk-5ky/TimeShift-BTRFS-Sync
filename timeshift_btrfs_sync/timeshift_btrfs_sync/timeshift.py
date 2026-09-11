"""Timeshift command wrappers and parser for `timeshift --list`."""

from __future__ import annotations

from pathlib import Path
import re
from .commands import quote_join, remote_double_quote, sudo_prefix
from .btrfs_ops import BtrfsOps
from .endpoint import CommandEndpoint
from .models import SnapshotMeta, SubvolumeMeta
from .source import SourceRunner

SNAPSHOT_RE = re.compile(r"(?P<name>\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})")
TAG_CHARS = set("HDWMBO")
DELETE_VERIFY_MARKER = "TSBTRFS_TIMESHIFT_DELETE_VERIFY"


def timeshift_cmd(sudo: str, timeshift_command: str, args: list[str]) -> str:
    """Build a source-side shell command that invokes sudo+timeshift."""

    return quote_join(sudo_prefix(sudo) + [timeshift_command] + args)


def normalize_tags(text: str | None) -> list[str]:
    """Return unique Timeshift tag letters found in text."""

    tags: list[str] = []
    for ch in (text or "").upper():
        if ch in TAG_CHARS and ch not in tags:
            tags.append(ch)
    return tags


def parse_timeshift_list(output: str, snapshot_root: str) -> list[SnapshotMeta]:
    """Parse Timeshift snapshot names and tag/comment text."""

    snapshots: list[SnapshotMeta] = []
    seen: set[str] = set()
    for line in output.splitlines():
        match = SNAPSHOT_RE.search(line)
        if not match:
            continue
        name = match.group("name")
        if name in seen:
            continue
        seen.add(name)
        after = line[match.end():].strip()
        tags: list[str] = []
        comment: str | None = None
        if after:
            # Timeshift versions/themes may render tags either compact (DWM) or
            # separated by spaces (D W M). Collect all leading tag-only tokens
            # before treating the rest of the line as the comment.
            tokens = after.split()
            tag_tokens: list[str] = []
            while tokens and all(ch.upper() in TAG_CHARS for ch in tokens[0]):
                tag_tokens.append(tokens.pop(0))
            if tag_tokens:
                tags = normalize_tags("".join(tag_tokens))
                comment = " ".join(tokens) if tokens else None
            else:
                comment = after
        snapshots.append(SnapshotMeta(name=name, path=str(Path(snapshot_root) / name), tags=tags, comment=comment, created=name))
    return sorted(snapshots, key=lambda s: s.name)


def list_source_snapshots(
    source: SourceRunner,
    *,
    snapshot_root: str,
    subvolumes: list[str],
    sudo: str,
    timeshift_command: str,
    btrfs_command: str,
    include_btrfs_info: bool = True,
    btrfs_index=None,
    timeshift_output: str | None = None,
) -> list[SnapshotMeta]:
    """Discover source snapshots through SSH or local source commands.

    When a bulk Btrfs index for ``snapshot_root`` is supplied, discovery fills
    each configured subvolume from that in-memory metadata. That avoids running
    one ``btrfs subvolume show`` per Timeshift snapshot over SSH. If discovery
    verification is disabled, missing entries are represented by path-only
    metadata and checked later at send time.
    """

    if timeshift_output is None:
        result = source.run(timeshift_cmd(sudo, timeshift_command, ["--list"]))
        timeshift_output = result.stdout
    snapshots = parse_timeshift_list(timeshift_output, snapshot_root)
    for snap in snapshots:
        for subvol in subvolumes:
            path = str(Path(snap.path) / subvol)
            indexed = btrfs_index.meta(path) if btrfs_index is not None else None
            if indexed:
                snap.subvolumes[subvol] = indexed
                continue
            if not include_btrfs_info:
                snap.subvolumes[subvol] = SubvolumeMeta(name=subvol, path=path)
                continue
            meta = BtrfsOps(CommandEndpoint.for_source(source), sudo, btrfs_command).meta(path, name=subvol, required=False)
            if meta:
                snap.subvolumes[subvol] = meta
    return snapshots


def create_remote_manual_snapshot_cmd(sudo: str, timeshift_command: str, comment: str) -> str:
    """Build the Timeshift manual/on-demand snapshot create command.

    Do not pass ``--tags O`` here. Timeshift documents O as the default
    on-demand tag, but several Timeshift versions reject an explicit O tag due
    to a CLI validation bug. Omitting ``--tags`` is both cleaner and safer: a
    plain ``timeshift --create`` snapshot becomes an on-demand snapshot by
    default.

    The comment is intentionally quoted with remote-safe double quotes instead
    of the default single-quote style. That avoids very noisy logged SSH
    commands such as ``'"'"'comment'"'"'`` while still making comments with
    spaces safe for the remote shell.
    """

    base = sudo_prefix(sudo) + [timeshift_command, "--create", "--scripted", "--comments"]
    return quote_join(base) + " " + remote_double_quote(comment)


def create_source_manual_snapshot(source: SourceRunner, *, sudo: str, timeshift_command: str, comment: str) -> None:
    """Create a source Timeshift on-demand snapshot through SSH or locally."""

    source.run(create_remote_manual_snapshot_cmd(sudo, timeshift_command, comment), mirror_stdout_on_failure=True)


def delete_remote_manual_snapshot_cmd(
    sudo: str,
    timeshift_command: str,
    snapshot_name: str,
) -> str:
    """Build one Timeshift delete command with an in-command verification list.

    Source snapshot retention must never raw-delete paths below
    ``source.snapshot_root``.  The app asks Timeshift to delete the exact
    timestamp instead, then lists Timeshift again in the same source-shell/SSH
    invocation.  This keeps the destructive operation inside Timeshift while
    avoiding a second SSH round trip solely for verification.
    """

    delete_cmd = timeshift_cmd(
        sudo,
        timeshift_command,
        ["--delete", "--snapshot", snapshot_name, "--scripted", "--yes"],
    )
    marker_cmd = quote_join(["printf", "%s\\n", DELETE_VERIFY_MARKER])
    list_cmd = timeshift_cmd(sudo, timeshift_command, ["--list"])
    return f"{delete_cmd} && {marker_cmd} && {list_cmd}"


def delete_source_manual_snapshot(
    source: SourceRunner,
    *,
    snapshot_root: str,
    sudo: str,
    timeshift_command: str,
    snapshot_name: str,
) -> None:
    """Delete one app-created source snapshot through Timeshift and verify it is gone."""

    result = source.run(
        delete_remote_manual_snapshot_cmd(sudo, timeshift_command, snapshot_name),
        mirror_stdout_on_failure=True,
    )
    _before, marker, post_delete_list = result.stdout.partition(DELETE_VERIFY_MARKER)
    if not marker:
        raise RuntimeError(
            f"Timeshift delete verification marker was missing for source snapshot {snapshot_name}"
        )
    remaining = {
        snapshot.name
        for snapshot in parse_timeshift_list(post_delete_list, snapshot_root)
    }
    if snapshot_name in remaining:
        raise RuntimeError(
            f"Timeshift reported success but source snapshot is still listed: {snapshot_name}"
        )


