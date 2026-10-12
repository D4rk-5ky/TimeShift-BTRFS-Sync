"""Read-only, unprivileged snapshot and filesystem reports for both endpoints."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath
import json
import base64
import re
import shlex

from .btrfs_ops import BtrfsOps
from .config import AppConfig
from .commands import Completed, quote_join
from .endpoint import CommandEndpoint
from .restore import BackupDirectoryRecord, BackupRepository, _scan_snapshot_directories
from .source import SourceRunner
from .timeshift import SNAPSHOT_RE, normalize_tags
from .topology import describe_restore_topology, describe_sync_topology


@dataclass(slots=True)
class SnapshotListingRow:
    """One physical date, retaining incomplete or inaccessible payloads visibly."""

    name: str
    tags: str
    description: str
    payloads: list[str] = field(default_factory=list)
    verified: bool = False
    complete: bool = False
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SnapshotListingSection:
    """Independent endpoint outcome so one failed side cannot hide the other."""

    title: str
    location: str
    root: str | None
    rows: list[SnapshotListingRow] = field(default_factory=list)
    space: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    failed: bool = False


def _terminal_text(value: object) -> str:
    """Remove terminal controls and collapse lines in untrusted remote metadata."""

    return " ".join("".join(ch if ch.isprintable() else " " for ch in str(value)).split())


def _snapshot_description(record: BackupDirectoryRecord | None) -> tuple[str, str, str | None]:
    """Decode Timeshift's named retention tags without misreading 'hourly' as O/H."""

    if record is None or record.info_content is None:
        return "?", "", "Timeshift info.json unavailable; tags/description unknown"
    try:
        doc = json.loads(record.info_content)
        if not isinstance(doc, dict):
            raise ValueError("expected an object")
        raw = doc.get("tags")
        if not isinstance(raw, str):
            raise ValueError("tags must be a string")
        comment = doc.get("comments", "")
        if not isinstance(comment, str):
            raise ValueError("comments must be a string")
        names = {"ondemand": "O", "hourly": "H", "daily": "D", "weekly": "W", "monthly": "M", "boot": "B"}
        letters: list[str] = []
        for token in re.split(r"[\s,]+", raw.strip()):
            if not token:
                continue
            tag = names.get(token.lower())
            if tag is None:
                if all(ch.upper() in "OHDWMB" for ch in token):
                    tag = token.upper()
                else:
                    raise ValueError(f"unknown Timeshift tag: {token}")
            letters.extend(normalize_tags(tag))
        tags = " ".join(tag for tag in "OHDWMB" if tag in letters) or "-"
        return tags, _terminal_text(comment), None
    except (ValueError, TypeError) as exc:
        return "?", "", f"Invalid Timeshift info.json: {_terminal_text(exc)}"


def _filesystem_space(endpoint: CommandEndpoint, root: str) -> dict[str, str]:
    """Read GNU df's available filesystem space without mounting or using sudo."""

    result = endpoint.run_shell(
        f"LC_ALL=C df -h -P -T -- {shlex.quote(root)}",
        check=False, log_stderr=False, mirror_stderr=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"df exited {result.returncode}")
    lines = result.stdout.splitlines()
    if len(lines) != 2:
        raise RuntimeError("df did not return one filesystem record")
    fields = lines[1].split(None, 6)
    if len(fields) != 7:
        raise RuntimeError("unrecognized df output")
    return dict(zip(("device", "fstype", "size", "used", "available", "percent", "mount"), fields))


def _scan_unprivileged(endpoint: CommandEndpoint, root: str, label: str) -> dict[str, BackupDirectoryRecord]:
    """Reuse physical repository discovery with an explicitly empty privilege prefix."""

    return _scan_snapshot_directories(endpoint, root, location_label=label, privilege_prefix=[])


def _probe_payloads(ops: BtrfsOps, paths: list[str]) -> dict[str, Completed]:
    """Batch Btrfs subvolume read-only property reads without privileged tree searches."""

    if not paths:
        return {}
    batches: list[list[tuple[int, str]]] = [[]]
    script_bytes = 0
    for index, path in enumerate(paths):
        argv = ops.argv(["property", "get", "-ts", path, "ro"])
        command = (
            f"out=$({quote_join(argv)} 2>&1); code=$?\n"
            f"printf 'TSBTRFS_LIST_PROBE\\t{index}\\t%s\\t%s\\n' \"$code\" \"$(printf '%s' \"$out\" | base64 -w 0)\""
        )
        size = len(command.encode("utf-8")) + 1
        # Leave room for shell quoting at both transport layers and avoid the
        # per-argument exec limit when a repository has hundreds of dates.
        if batches[-1] and script_bytes + size > 16000:
            batches.append([])
            script_bytes = 0
        batches[-1].append((index, command))
        script_bytes += size
    probes = {}
    for batch in batches:
        script = "\n".join(command for _index, command in batch)
        result = ops.endpoint.run_shell(script, check=False, log_stderr=False, mirror_stderr=False)
        expected = {index for index, _command in batch}
        received: set[int] = set()
        for line in result.stdout.splitlines():
            fields = line.split("\t")
            if len(fields) != 4 or fields[0] != "TSBTRFS_LIST_PROBE":
                continue
            try:
                index, code = int(fields[1]), int(fields[2])
                if index not in expected or index in received:
                    raise ValueError("invalid or duplicate probe index")
                output = base64.b64decode(fields[3], validate=True).decode("utf-8", errors="replace")
                received.add(index)
                probes[paths[index]] = Completed(code, output, "")
            except (ValueError, UnicodeError) as exc:
                raise RuntimeError(f"Invalid Btrfs probe response: {exc}") from exc
        if result.returncode != 0 or received != expected:
            raise RuntimeError(result.stderr.strip() or "Incomplete batched Btrfs probe response")
    return probes


def _collect_section(
    config: AppConfig, endpoint: CommandEndpoint, *, title: str, location: str,
    root: str | None, btrfs_command: str,
    metadata: dict[str, BackupDirectoryRecord] | None = None,
    records: dict[str, BackupDirectoryRecord] | None = None,
    scan_error: str | None = None,
) -> SnapshotListingSection:
    """Probe physical payloads with Btrfs and keep errors visible instead of inferring state."""

    section = SnapshotListingSection(title, location, root)
    space_root = root or config.source.snapshot_root
    try:
        section.space = _filesystem_space(endpoint, space_root)
        if root is not None and section.space["fstype"].lower() != "btrfs":
            section.failed = True
            section.notes.append(f"Configured repository filesystem is {section.space['fstype']}, not Btrfs")
    except Exception as exc:
        section.failed = True
        section.notes.append(f"Free space unavailable: {_terminal_text(exc)}")
    if root is None:
        section.notes.append("Source send-cache disabled: source.cache_root is not configured")
        section.notes.append(f"Filesystem report uses source.snapshot_root: {space_root}")
        return section
    if scan_error is not None:
        section.failed = True
        section.notes.append(scan_error)
        return section
    try:
        if records is None:
            records = _scan_unprivileged(endpoint, root, location)
    except Exception as exc:
        section.failed = True
        section.notes.append(_terminal_text(exc))
        return section
    # Construct commands through the shared facade, always overriding configured sudo.
    ops = BtrfsOps(endpoint, sudo="", command_name=btrfs_command)
    paths = [str(PurePosixPath(root) / name / payload)
             for name, record in sorted(records.items())
             if SNAPSHOT_RE.fullmatch(name) and record.kind == "directory"
             for payload, kind in sorted(record.entries.items()) if kind == "directory"]
    try:
        probes = _probe_payloads(ops, paths)
    except Exception as exc:
        section.failed = True
        section.notes.append(f"Btrfs verification unavailable: {_terminal_text(exc)}")
        probes = {}
    for name, record in sorted(records.items()):
        if SNAPSHOT_RE.fullmatch(name) is None:
            continue  # Hidden restore chains and repository helper files are not dates.
        info_record = (metadata or {}).get(name) if metadata is not None else record
        tags, description, info_note = _snapshot_description(info_record)
        row = SnapshotListingRow(name, tags, description)
        section.rows.append(row)
        if info_note:
            row.notes.append(info_note)
        if record.kind != "directory":
            section.failed = True
            row.notes.append(f"Date entry is {record.kind}; not followed or verified")
            continue
        candidates = set(config.source.subvolumes) | {entry for entry, kind in record.entries.items() if kind == "directory"}
        verified_names: set[str] = set()
        for payload in sorted(candidates):
            kind = record.entries.get(payload)
            if kind != "directory":
                section.failed = True
                row.payloads.append(f"{payload}:?")
                row.notes.append(f"{payload}: {kind or 'missing'}; not a verified payload")
                continue
            path = str(PurePosixPath(root) / name / payload)
            try:
                result = probes.get(path)
                if result is None:
                    raise RuntimeError("no Btrfs probe result")
                if result.returncode != 0:
                    raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}")
                value = result.stdout.strip()
                if value not in {"ro=true", "ro=false"}:
                    raise RuntimeError("Btrfs did not return an unambiguous subvolume ro property")
                verified_names.add(payload)
                row.payloads.append(f"{payload}:{'ro' if value == 'ro=true' else 'rw'}")
            except Exception as exc:
                section.failed = True
                row.payloads.append(f"{payload}:?")
                row.notes.append(f"{payload}: {_terminal_text(exc)}")
        row.verified = bool(verified_names)
        row.complete = set(config.source.subvolumes).issubset(verified_names)
    return section


def collect_snapshot_listings(
    config: AppConfig, *, workflow: str = "auto", include_timeshift: bool = False,
) -> tuple[str, list[SnapshotListingSection]]:
    """Resolve backup/restore hosts once and independently inventory both configured repositories."""

    if workflow == "auto":
        workflow = "restore" if config.restore.mode != "local" else "backup"
    if workflow not in {"backup", "restore"}:
        raise ValueError("workflow must be auto, backup or restore")
    if workflow == "restore":
        runner = SourceRunner.from_mode("ssh" if config.restore.timeshift_uses_ssh else "local", config.ssh)
        destination = BackupRepository.from_config(config).endpoint
        topology = describe_restore_topology(config)
        source_label, destination_label = topology.destination_label, topology.source_label
    else:
        runner = SourceRunner.from_config(config)
        destination = CommandEndpoint.local("backup destination")
        topology = describe_sync_topology(config)
        source_label, destination_label = topology.source_label, topology.destination_label
    source = CommandEndpoint.for_source(runner)
    metadata: dict[str, BackupDirectoryRecord] = {}
    metadata_error = None
    if config.source.cache_root or include_timeshift:
        try:
            metadata = _scan_unprivileged(source, config.source.snapshot_root, source_label)
        except Exception as exc:
            metadata_error = _terminal_text(exc)
    sections = [_collect_section(
        config, source, title="SOURCE SEND-CACHE SNAPSHOTS", location=source_label,
        root=config.source.cache_root, btrfs_command=config.source.btrfs_command, metadata=metadata,
    )]
    if metadata_error:
        sections[0].notes.append(f"Tags/description lookup unavailable: {metadata_error}")
    sections.append(_collect_section(
        config, destination, title="DESTINATION BACKUP SNAPSHOTS", location=destination_label,
        root=str(PurePosixPath(str(config.destination.target_root)) / "snapshots"),
        btrfs_command=config.destination.btrfs_command,
    ))
    if include_timeshift:
        sections.append(_collect_section(
            config, source, title="SOURCE TIMESHIFT SNAPSHOTS", location=source_label,
            root=config.source.snapshot_root, btrfs_command=config.source.btrfs_command,
            records=metadata, scan_error=metadata_error,
        ))
    return workflow, sections


def format_snapshot_listings(workflow: str, sections: list[SnapshotListingSection]) -> str:
    """Render Timeshift-style name/tag/description tables and independent df summaries."""

    lines = [f"SNAPSHOT INVENTORY (workflow: {workflow}; read-only commands, no sudo)",
             "Source means the configured Timeshift/cache side; destination means the backup repository.",
             "Live observations can change during listing; this is not a transfer or restore safety check."]
    for section in sections:
        lines.extend(["", section.title, "=" * len(section.title),
                      f"Endpoint : {_terminal_text(section.location)}", f"Path     : {_terminal_text(section.root or '(cache disabled)')}"])
        space = section.space
        if space:
            lines.extend([f"Device   : {_terminal_text(space['device'])}", f"Mount    : {_terminal_text(space['mount'])}",
                          f"Mode     : {_terminal_text(space['fstype']).upper()}",
                          f"Space    : {_terminal_text(space['available'])} free / {_terminal_text(space['size'])} total; {_terminal_text(space['used'])} used ({_terminal_text(space['percent'])})"])
        else:
            lines.append("Space    : unavailable")
        status = "INCOMPLETE / UNAVAILABLE" if section.failed else "DISABLED" if section.root is None else "OK"
        verified = sum(row.verified for row in section.rows)
        lines.extend([f"Status   : {status}",
                      f"{verified} verified snapshot date(s), {len(section.rows) - verified} unverified date entry/entries; {len(section.rows)} listed",
                      "", f"{'Num':<5} {'Name':<20} {'Tags':<11} {'Payloads':<22} {'Check':<12} Description", "-" * 94])
        for i, row in enumerate(section.rows):
            check = "complete" if row.complete else "incomplete" if row.verified else "unverified"
            payloads = _terminal_text(', '.join(row.payloads)) or '-'
            lines.append(f"{i:<5} {row.name:<20} {row.tags:<11} {payloads:<22} {check:<12} {row.description}")
            for note in row.notes:
                lines.append(f"      Note: {_terminal_text(note)}")
        for note in section.notes:
            lines.append(f"Note: {_terminal_text(note)}")
    lines.extend(["", "Free space is df filesystem availability, not per-snapshot usage or guaranteed Btrfs receive capacity.",
                  "Complete means configured Btrfs payloads were observed; it does not prove restore eligibility.",
                  "Cache tags/descriptions come from the current same-date source info.json; missing originals show ?. Destination metadata is its own stored info.json."])
    return "\n".join(lines)
