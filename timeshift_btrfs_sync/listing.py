"""Read-only inventory using the configured restricted Btrfs/Timeshift privileges."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath
import json
import base64
import re
import shlex

from .btrfs_ops import BtrfsOps
from .config import AppConfig
from .commands import Completed, quote_join, sudo_prefix
from .inventory import BtrfsIndex, parse_subvolume_list, parse_subvolume_paths
from .models import SubvolumeMeta, send_stream_uuid
from .endpoint import CommandEndpoint
from .restore import BackupDirectoryRecord, BackupRepository, _scan_snapshot_directories
from .source import SourceRunner
from .timeshift import SNAPSHOT_RE, normalize_tags, parse_timeshift_list
from .transfer_size import format_bytes, parse_btrfs_usage_free_bytes
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
    metadata_origin: str = "?"
    subvolumes: dict[str, SubvolumeMeta] = field(default_factory=dict)


@dataclass(slots=True)
class SnapshotPairComparison:
    """Report observed cache/receiver differences without authorizing deletion."""

    cache_dates: int
    destination_dates: int
    shared_dates: list[str]
    matching_dates: list[str]
    unproven_dates: list[str]
    cache_only_dates: list[str]
    destination_only_dates: list[str]
    in_window_dates: list[str]
    outside_window_dates: list[str]
    window: tuple[str, str] | None
    inventory_complete: bool
    cache_enabled: bool

    def parity_confirmed(self) -> bool:
        """Require enabled, complete inventories and matching UUIDs for every observed date."""

        return (self.cache_enabled and self.inventory_complete
                and not (self.cache_only_dates or self.destination_only_dates or self.unproven_dates))


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
    filesystem_uuid: str | None = None
    inventory_complete: bool = True
    comparison: SnapshotPairComparison | None = None


def _terminal_text(value: object) -> str:
    """Remove terminal controls and collapse lines in untrusted remote metadata."""

    return " ".join("".join(ch if ch.isprintable() else " " for ch in str(value)).split())


def _snapshot_description(record: BackupDirectoryRecord | None) -> tuple[str, str, str | None]:
    """Decode Timeshift's named retention tags without misreading 'hourly' as O/H."""

    if record is None or record.info_content is None:
        reason = f" ({_terminal_text(record.info_error)})" if record is not None and record.info_error else ""
        return "?", "", "Timeshift info.json unavailable; tags/description unknown" + reason
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


def _scan_unprivileged(endpoint: CommandEndpoint, root: str, label: str, *, read_info: bool = True) -> dict[str, BackupDirectoryRecord]:
    """Reuse ordinary physical discovery, optionally skipping JSON already supplied by Timeshift."""

    return _scan_snapshot_directories(endpoint, root, location_label=label, privilege_prefix=[], read_info=read_info)


def _run_batched_commands(endpoint: CommandEndpoint, commands: list[list[str]]) -> dict[int, Completed]:
    """Batch captured reads with bounded shell arguments and per-command failure framing."""

    if not commands:
        return {}
    batches: list[list[tuple[int, str]]] = [[]]
    script_bytes = 0
    for index, argv in enumerate(commands):
        command = (
            f"out=$(LC_ALL=C {quote_join(argv)} 2>&1); code=$?\n"
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
        result = endpoint.run_shell(script, check=False, log_stderr=False, mirror_stderr=False)
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
                probes[index] = Completed(code, output, "")
            except (ValueError, UnicodeError) as exc:
                raise RuntimeError(f"Invalid Btrfs probe response: {exc}") from exc
        if result.returncode != 0 or received != expected:
            raise RuntimeError(result.stderr.strip() or "Incomplete batched Btrfs probe response")
    return probes


def _probe_payloads(ops: BtrfsOps, paths: list[str]) -> dict[str, Completed]:
    """Read exact subvolume flags through the same configured Btrfs privilege prefix."""

    results = _run_batched_commands(ops.endpoint, [ops.argv(["property", "get", "-ts", path, "ro"]) for path in paths])
    return {path: results[index] for index, path in enumerate(paths)}


def _filesystem_identity(output: str) -> tuple[str | None, str]:
    """Parse filesystem UUID and all device paths from Btrfs filesystem show output."""

    match = re.search(r"\buuid:\s*([0-9a-fA-F-]{36})\b", output)
    devices = re.findall(r"^\s*devid\s+\d+.*?\spath\s+(.+)$", output, re.MULTILINE)
    return (match.group(1).lower() if match else None), ", ".join(devices) or "unavailable"


def _add_listing_index(index: BtrfsIndex, root: str, full: Completed, readonly: Completed) -> list[str]:
    """Reuse scoped Btrfs parsers and preserve unknown flags when readonly listing fails."""

    if full.returncode != 0:
        raise RuntimeError(full.stderr.strip() or full.stdout.strip() or "Btrfs subvolume list failed")
    metas = parse_subvolume_list(full.stdout, root)
    readonly_paths = parse_subvolume_paths(readonly.stdout, root) if readonly.returncode == 0 else None
    for meta in metas:
        meta.readonly = meta.path in readonly_paths if readonly_paths is not None else None
        index.add(meta)
    return [] if readonly_paths is not None else [f"Readonly list unavailable for {root}; exact property reads will be tried"]


def _discover_repository(ops: BtrfsOps, root: str) -> tuple[BtrfsIndex, dict[str, BackupDirectoryRecord], list[str], str | None, str]:
    """Discover protected dates and nested payloads using only sudo-authorized Btrfs reads."""

    index = BtrfsIndex(root=root, location=ops.endpoint.location)
    results = _run_batched_commands(ops.endpoint, [
        ops.argv(["subvolume", "list", "-u", "-q", "-R", "-o", root]),
        ops.argv(["subvolume", "list", "-r", "-o", root]),
        ops.argv(["filesystem", "show", root]),
    ])
    notes = _add_listing_index(index, root, results[0], results[1])
    uuid, device = _filesystem_identity(results[2].stdout) if results[2].returncode == 0 else (None, "unavailable")
    # -o can stop at nested date containers. Query those containers explicitly
    # rather than requiring ordinary ls permission or assuming the root list is recursive.
    dates = []
    for path in index.by_path:
        relative = PurePosixPath(path).relative_to(root).parts
        if len(relative) == 1 and SNAPSHOT_RE.fullmatch(relative[0]):
            dates.append(path)
    commands = [ops.argv(args) for date in sorted(dates) for args in (
        ["subvolume", "list", "-u", "-q", "-R", "-o", date],
        ["subvolume", "list", "-r", "-o", date],
    )]
    nested = _run_batched_commands(ops.endpoint, commands)
    for i, date in enumerate(sorted(dates)):
        try:
            notes.extend(_add_listing_index(index, date, nested[2 * i], nested[2 * i + 1]))
        except RuntimeError as exc:
            index.errors.append(f"Btrfs payload listing failed for {date}: {_terminal_text(exc)}")
    notes.extend(index.errors)
    records: dict[str, BackupDirectoryRecord] = {}
    for path in index.by_path:
        parts = PurePosixPath(path).relative_to(root).parts
        if not parts or SNAPSHOT_RE.fullmatch(parts[0]) is None or len(parts) > 2:
            continue
        record = records.setdefault(parts[0], BackupDirectoryRecord(parts[0], "directory", {}, None))
        if len(parts) == 2:
            record.entries[parts[1]] = "directory"
    return index, records, notes, uuid, device


def _read_listing_metadata(endpoint: CommandEndpoint, root: str, records: dict[str, BackupDirectoryRecord], *, skip_names: frozenset[str] = frozenset()) -> None:
    """Read regular info.json as the login user, excluding dates already supplied by Timeshift; never sudo a file reader."""

    names = sorted(name for name, record in records.items() if name not in skip_names and SNAPSHOT_RE.fullmatch(name) and record.kind == "directory" and record.info_content is None)
    commands = []
    for name in names:
        path = shlex.quote(str(PurePosixPath(root) / name / "info.json"))
        commands.append(["sh", "-c", f"[ ! -L {path} ] && [ -f {path} ] && base64 -w 0 -- {path}"])
    results = _run_batched_commands(endpoint, commands)
    for i, name in enumerate(names):
        result = results[i]
        if result.returncode != 0:
            records[name].info_error = _terminal_text(result.stderr or result.stdout) or "missing or unreadable info.json"
            continue
        try:
            records[name].info_content = base64.b64decode(result.stdout.strip(), validate=True).decode("utf-8")
        except (ValueError, UnicodeError) as exc:
            records[name].info_error = f"invalid metadata encoding: {_terminal_text(exc)}"


def _space_with_btrfs_fallback(
    ops: BtrfsOps, root: str, *, device: str = "unavailable", filesystem_uuid: str | None = None,
) -> dict[str, str]:
    """Keep ordinary df space; use native Btrfs evidence for denied reads or unknown types."""

    try:
        space = _filesystem_space(ops.endpoint, root)
        if space["fstype"].lower() not in {"-", "", "unknown"}:
            return space
        if filesystem_uuid:
            return {**space, "fstype": "btrfs", "provider": "df space; type confirmed by Btrfs filesystem show"}
        raise RuntimeError("df filesystem type unavailable")
    except Exception as df_error:
        result = ops.run(["filesystem", "usage", "-b", root], check=False, log_stderr=False, mirror_stderr=False)
        if result.returncode != 0:
            raise RuntimeError(f"df: {_terminal_text(df_error)}; Btrfs usage: {_terminal_text(result.stderr or result.stdout)}")
        values = dict(re.findall(r"^\s*(Device size|Used|Free \(statfs, df\)):\s*(\d+)\s*$", result.stdout, re.MULTILINE))
        if "Device size" not in values or "Used" not in values:
            raise RuntimeError("Btrfs usage did not return device size/used bytes")
        free = int(values["Free (statfs, df)"]) if "Free (statfs, df)" in values else parse_btrfs_usage_free_bytes(result.stdout)
        total, used = int(values["Device size"]), int(values["Used"])
        return {"device": device, "fstype": "btrfs", "size": format_bytes(total), "used": format_bytes(used),
                "available": format_bytes(free), "percent": "unavailable", "mount": "unavailable (Btrfs path: " + root + ")",
                "provider": "Btrfs filesystem usage; statfs availability" if "Free (statfs, df)" in values else "Btrfs filesystem usage; conservative estimated free space"}


def _collect_section(
    config: AppConfig, endpoint: CommandEndpoint, *, title: str, location: str,
    root: str | None, btrfs_command: str, sudo: str = "",
    metadata: dict[str, BackupDirectoryRecord] | None = None,
    records: dict[str, BackupDirectoryRecord] | None = None,
    scan_error: str | None = None,
    timeshift_names: frozenset[str] = frozenset(),
    timeshift_filesystem_uuid: str | None = None,
) -> SnapshotListingSection:
    """Combine Btrfs-authorized discovery with ordinary JSON reads without requiring sudo ls/cat."""

    section = SnapshotListingSection(title, location, root)
    ops = BtrfsOps(endpoint, sudo=sudo, command_name=btrfs_command)
    index = BtrfsIndex(root=root or "", location=endpoint.location)
    device = "unavailable"
    if root is not None and records is None:
        try:
            index, records, notes, section.filesystem_uuid, device = _discover_repository(ops, root)
            section.notes.extend(notes)
            section.failed = bool(index.errors)
            section.inventory_complete = not bool(index.errors)
        except Exception as exc:
            section.failed = True
            section.inventory_complete = False
            section.notes.append(f"Btrfs inventory unavailable: {_terminal_text(exc)}")
            records = {}
        skip_names = timeshift_names if not (timeshift_filesystem_uuid and section.filesystem_uuid and timeshift_filesystem_uuid != section.filesystem_uuid) else frozenset()
        try:
            # Timeshift has already decoded these source control files. Keep
            # physical discovery, then read only omitted dates directly. A
            # known repository mismatch must still read its own JSON instead.
            ordinary = (_scan_unprivileged(endpoint, root, location, read_info=False)
                        if timeshift_names else _scan_unprivileged(endpoint, root, location))
            for name, record in ordinary.items():
                if name in records and record.kind == "directory":
                    for entry, kind in records[name].entries.items():
                        record.entries.setdefault(entry, kind)
                records[name] = record
        except Exception as exc:
            section.notes.append(f"Ordinary directory scan unavailable; using Btrfs inventory: {_terminal_text(exc)}")
        try:
            _read_listing_metadata(endpoint, root, records, skip_names=skip_names)
        except Exception as exc:
            section.notes.append(f"info.json reads unavailable: {_terminal_text(exc)}")
    try:
        section.space = _space_with_btrfs_fallback(
            ops, root or config.source.snapshot_root, device=device, filesystem_uuid=section.filesystem_uuid,
        )
        if root is not None and section.space["fstype"].lower() != "btrfs":
            section.failed = True
            section.notes.append(f"Configured repository filesystem is {section.space['fstype']}, not Btrfs")
    except Exception as exc:
        section.failed = True
        section.notes.append(f"Free space unavailable: {_terminal_text(exc)}")
    if root is None:
        section.notes.append("Source send-cache disabled: source.cache_root is not configured")
        section.notes.append(f"Filesystem report uses source.snapshot_root: {config.source.snapshot_root}")
        return section
    if scan_error is not None:
        section.failed = True
        section.inventory_complete = False
        section.notes.append(scan_error)
        return section
    assert records is not None
    paths = [str(PurePosixPath(root) / name / payload)
             for name, record in sorted(records.items())
             if SNAPSHOT_RE.fullmatch(name) and record.kind == "directory"
             for payload, kind in sorted(record.entries.items())
             if kind == "directory" and index.meta(str(PurePosixPath(root) / name / payload)) is None]
    flag_paths = [path for path, meta in index.by_path.items() if meta.readonly is None]
    try:
        probes = _probe_payloads(ops, sorted(set(paths + flag_paths)))
    except Exception as exc:
        section.failed = True
        section.notes.append(f"Btrfs verification unavailable: {_terminal_text(exc)}")
        probes = {}
    for name, record in sorted(records.items()):
        if SNAPSHOT_RE.fullmatch(name) is None:
            continue
        tags, description, info_note = _snapshot_description(record)
        origin = "info.json" if not info_note else "?"
        if info_note and metadata is not None:
            fallback_tags, fallback_description, fallback_note = _snapshot_description(metadata.get(name))
            if not fallback_note:
                tags, description, info_note, origin = fallback_tags, fallback_description, None, "source info.json"
        row = SnapshotListingRow(name, tags, description, metadata_origin=origin)
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
            meta = index.meta(path)
            if meta is not None:
                row.subvolumes[payload] = meta
                verified_names.add(payload)
                if meta.readonly is None:
                    result = probes.get(path)
                    if result and result.returncode == 0 and result.stdout.strip() in {"ro=true", "ro=false"}:
                        meta.readonly = result.stdout.strip() == "ro=true"
                row.payloads.append(f"{payload}:{'ro' if meta.readonly is True else 'rw' if meta.readonly is False else '?'}")
                if meta.readonly is None:
                    section.failed = True
                    row.notes.append(f"{payload}: readonly flag unavailable")
                continue
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


def _set_listing_metadata(row: SnapshotListingRow, tags: str, description: str, origin: str) -> None:
    """Apply a labeled live metadata observation, retaining other diagnostics."""

    row.tags, row.description, row.metadata_origin = tags, _terminal_text(description), origin
    row.notes = [note for note in row.notes if not note.startswith(("Timeshift info.json unavailable", "Invalid Timeshift info.json"))]


def _matching_listing_payloads(config: AppConfig, sender: SnapshotListingRow, receiver: SnapshotListingRow) -> bool:
    """Require all configured live RO payloads to share send/received UUIDs before borrowing metadata."""

    for payload in config.source.subvolumes:
        source, destination = sender.subvolumes.get(payload), receiver.subvolumes.get(payload)
        if source is None or destination is None or source.readonly is not True or destination.readonly is not True:
            return False
        identity = send_stream_uuid(source)
        if not identity or destination.received_uuid != identity:
            return False
    return bool(config.source.subvolumes)


def compare_snapshot_listings(
    config: AppConfig, cache: SnapshotListingSection, backup: SnapshotListingSection,
) -> SnapshotPairComparison:
    """Compare every observed date and reuse full readonly send/Received UUID proof."""

    cache_by_name = {row.name: row for row in cache.rows}
    backup_by_name = {row.name: row for row in backup.rows}
    shared = sorted(cache_by_name.keys() & backup_by_name.keys())
    matching = [name for name in shared if _matching_listing_payloads(config, cache_by_name[name], backup_by_name[name])]
    cache_only = sorted(cache_by_name.keys() - backup_by_name.keys())
    target_only = sorted(backup_by_name.keys() - cache_by_name.keys())
    window = (matching[0], matching[-1]) if matching else None
    in_window = [name for name in cache_only if window and window[0] <= name <= window[1]]
    return SnapshotPairComparison(
        len(cache_by_name), len(backup_by_name), shared, matching,
        sorted(set(shared) - set(matching)), cache_only, target_only, in_window,
        [name for name in cache_only if window and not window[0] <= name <= window[1]],
        window, cache.inventory_complete and backup.inventory_complete, cache.root is not None,
    )


def _format_pair_comparison(comparison: SnapshotPairComparison) -> list[str]:
    """Make unequal repositories and unproven pairs visible, without claiming cleanup eligibility."""

    status = ("DISABLED (cache_root not configured)" if not comparison.cache_enabled
              else "INCOMPLETE (differences are observations, not proof of absence)" if not comparison.inventory_complete
              else "OK" if comparison.parity_confirmed() else "WARNING - cache/destination pairs differ")
    lines = ["", "CACHE / DESTINATION COMPARISON", "=" * 30,
             f"Status                   : {status}",
             f"Cache dates              : {comparison.cache_dates}",
             f"Destination dates        : {comparison.destination_dates}",
             f"Shared date names        : {len(comparison.shared_dates)}",
             f"Proven readonly UUID pairs: {len(comparison.matching_dates)}",
             f"Cache-only dates         : {len(comparison.cache_only_dates)}",
             f"Destination-only dates   : {len(comparison.destination_only_dates)}",
             f"Shared dates not proven  : {len(comparison.unproven_dates)}"]
    if comparison.window:
        lines += [f"Proven shared date range : {comparison.window[0]} .. {comparison.window[1]}",
                  f"Cache-only inside range  : {len(comparison.in_window_dates)}",
                  f"Cache-only outside range : {len(comparison.outside_window_dates)}",
                  f"Destination-only inside range : {sum(comparison.window[0] <= name <= comparison.window[1] for name in comparison.destination_only_dates)}",
                  f"Destination-only outside range: {sum(not comparison.window[0] <= name <= comparison.window[1] for name in comparison.destination_only_dates)}",
                  f"Destination-only at/before latest: {sum(name <= comparison.window[1] for name in comparison.destination_only_dates)}",
                  f"Destination-only newer than latest: {sum(name > comparison.window[1] for name in comparison.destination_only_dates)}"]
    else:
        lines.append("Proven shared date range : unavailable; cache-only dates cannot be classified by bounds")
    for title, names in (("CACHE-ONLY DATES (not observed at destination)", comparison.cache_only_dates),
                         ("DESTINATION-ONLY DATES (not observed in cache)", comparison.destination_only_dates),
                         ("SHARED DATES WITHOUT A PROVEN FULL UUID PAIR", comparison.unproven_dates)):
        if names:
            lines += ["", title]
            for name in names:
                suffix = (" [inside proven range]" if name in comparison.in_window_dates
                          else " [outside proven range]" if name in comparison.outside_window_dates else "")
                if name in comparison.destination_only_dates and comparison.window:
                    suffix = (" [newer than latest shared pair; compare with state cutoff]" if name > comparison.window[1]
                              else " [older than first shared pair; needs prune safety check]" if name < comparison.window[0]
                              else " [inside proven range]")
                lines.append(f"  {name}{suffix}")
    lines += ["", "Comparison uses live Btrfs identities for every configured payload; matching names/counts or O/H/D/W/M/B tags alone do not prove a pair.",
              "One-sided dates no newer than the latest shared pair, including older-than-first dates, need a prune safety check; this listing neither reads/rebuilds state nor deletes snapshots. Cleanup derives its upper limit from confirmed state pairs.",
              "Preview: python3 -m timeshift_btrfs_sync prune --config <same-config.toml> --dry-run",
              "Sync without --prune/prune_after_sync does not perform retention cleanup. Tracked, active-parent, unverified or newer caches may remain; verified older cache leftovers and destination-only dates no newer than the latest confirmed state pair can be cleaned after successful sync."]
    return lines


def collect_snapshot_listings(
    config: AppConfig, *, workflow: str = "auto", include_timeshift: bool = True,
) -> tuple[str, list[SnapshotListingSection]]:
    """Report Timeshift, cache and backup in order using their actual configured local/SSH hosts."""

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
    timeshift_rows = {}
    timeshift_uuid = None
    timeshift_error = None
    try:
        result = _run_batched_commands(source, [sudo_prefix(config.source.sudo) + [config.source.timeshift_command, "--list"]])[0]
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Timeshift --list failed")
        timeshift_rows = {snap.name: snap for snap in parse_timeshift_list(result.stdout, config.source.snapshot_root)}
        match = re.search(r"^\s*UUID\s*:\s*([0-9a-fA-F-]{36})", result.stdout, re.MULTILINE)
        timeshift_uuid = match.group(1).lower() if match else None
    except Exception as exc:
        timeshift_error = _terminal_text(exc)
    originals = _collect_section(
        config, source, title="TIMESHIFT SNAPSHOTS", location=source_label,
        root=config.source.snapshot_root, btrfs_command=config.source.btrfs_command, sudo=config.source.sudo,
        timeshift_names=frozenset(timeshift_rows), timeshift_filesystem_uuid=timeshift_uuid,
    )
    if timeshift_error:
        originals.failed = True
        originals.notes.append(f"Timeshift --list unavailable; physical snapshot-root inventory retained: {timeshift_error}")
    identity_mismatch = bool(timeshift_uuid and originals.filesystem_uuid and timeshift_uuid != originals.filesystem_uuid)
    if identity_mismatch:
        originals.failed = True
        originals.notes.append("Timeshift --list filesystem UUID differs from configured snapshot_root; its tags/rows were not applied")
    else:
        by_name = {row.name: row for row in originals.rows}
        for name, snapshot in sorted(timeshift_rows.items()):
            row = by_name.get(name)
            if row is None:
                row = SnapshotListingRow(name, "?", "")
                row.notes.append("Listed by Timeshift; payloads were not confirmed below configured snapshot_root")
                originals.rows.append(row)
                originals.failed = True
            _set_listing_metadata(row, " ".join(tag for tag in "OHDWMB" if tag in snapshot.tags) or "-", snapshot.comment or "", "Timeshift --list")
        originals.rows.sort(key=lambda row: row.name)
    cache = _collect_section(
        config, source, title="CACHE_ROOT SNAPSHOTS", location=source_label,
        root=config.source.cache_root, btrfs_command=config.source.btrfs_command, sudo=config.source.sudo,
    )
    backup = _collect_section(
        config, destination, title="TARGET_ROOT SNAPSHOTS", location=destination_label,
        root=str(PurePosixPath(str(config.destination.target_root)) / "snapshots"),
        btrfs_command=config.destination.btrfs_command, sudo=config.destination.sudo,
    )
    original_by_name = {row.name: row for row in originals.rows}
    cache_by_name = {row.name: row for row in cache.rows}
    backup_by_name = {row.name: row for row in backup.rows}
    for row in cache.rows:
        original = original_by_name.get(row.name)
        if row.tags == "?" and original is not None and original.tags != "?":
            _set_listing_metadata(row, original.tags, original.description, "source " + original.metadata_origin)
    for row in backup.rows:
        if row.tags != "?":
            continue
        for sender in (cache_by_name.get(row.name), original_by_name.get(row.name)):
            if sender is not None and sender.tags != "?" and _matching_listing_payloads(config, sender, row):
                _set_listing_metadata(row, sender.tags, sender.description, "matching source UUIDs (" + sender.metadata_origin + ")")
                break
    for row in cache.rows:
        destination_row = backup_by_name.get(row.name)
        if row.tags == "?" and destination_row is not None and destination_row.tags != "?" and _matching_listing_payloads(config, row, destination_row):
            _set_listing_metadata(row, destination_row.tags, destination_row.description, "matching target info/metadata via UUIDs")
    cache.comparison = compare_snapshot_listings(config, cache, backup)
    # Keep the former opt-in argument accepted for API/CLI compatibility; the
    # user requested all three sections unconditionally and in this order.
    return workflow, [originals, cache, backup]


def format_snapshot_listings(workflow: str, sections: list[SnapshotListingSection]) -> str:
    """Render Timeshift-style name/tag/description tables and independent df summaries."""

    lines = [f"SNAPSHOT INVENTORY (workflow: {workflow}; configured sudo for Btrfs/Timeshift reads)",
             "Source means the configured Timeshift/cache side; destination means the backup repository.",
             "Live observations can change during listing; this is not a transfer or restore safety check."]
    for section in sections:
        lines.extend(["", section.title, "=" * len(section.title),
                      f"Endpoint : {_terminal_text(section.location)}", f"Path     : {_terminal_text(section.root or '(cache disabled)')}"])
        space = section.space
        if space:
            lines.extend([f"Device   : {_terminal_text(space['device'])}", f"Mount    : {_terminal_text(space['mount'])}",
                          f"Mode     : {_terminal_text(space['fstype']).upper()}",
                          f"Space via: {_terminal_text(space.get('provider', 'df'))}",
                          f"Space    : {_terminal_text(space['available'])} free / {_terminal_text(space['size'])} total; {_terminal_text(space['used'])} used ({_terminal_text(space['percent'])})"])
        else:
            lines.append("Space    : unavailable")
        if section.filesystem_uuid:
            lines.append(f"UUID     : {section.filesystem_uuid}")
        status = "INCOMPLETE / UNAVAILABLE" if section.failed else "DISABLED" if section.root is None else "OK"
        verified = sum(row.verified for row in section.rows)
        lines.extend([f"Status   : {status}",
                      f"{verified} verified snapshot date(s), {len(section.rows) - verified} unverified date entry/entries; {len(section.rows)} listed",
                      "", f"{'Num':<5} {'Name':<20} {'Tags':<11} {'Payloads':<22} {'Check':<12} Description", "-" * 94])
        for i, row in enumerate(section.rows):
            check = "complete" if row.complete else "incomplete" if row.verified else "unverified"
            payloads = _terminal_text(', '.join(row.payloads)) or '-'
            lines.append(f"{i:<5} {row.name:<20} {row.tags:<11} {payloads:<22} {check:<12} {row.description}")
            lines.append(f"      Metadata: {_terminal_text(row.metadata_origin)}")
            for note in row.notes:
                lines.append(f"      Note: {_terminal_text(note)}")
        for note in section.notes:
            lines.append(f"Note: {_terminal_text(note)}")
    for section in sections:
        if section.comparison is not None:
            lines.extend(_format_pair_comparison(section.comparison))
            break
    lines.extend(["", "Free space is filesystem-wide (df, or labeled Btrfs usage fallback), not per-snapshot usage or guaranteed receive capacity.",
                  "Complete means configured Btrfs payloads were observed; it does not prove restore eligibility.",
                  "Source metadata uses Timeshift --list with ordinary JSON fallback; cache/target prefer their own readable info.json. Fallback origins are labeled. Unknown/orphan metadata stays ? unless a live matching backup proves it."])
    return "\n".join(lines)
