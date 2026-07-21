"""Restore backed-up snapshots into Timeshift's native Btrfs layout.

The backup destination stores each timestamp as a Btrfs date-container
subvolume. Timeshift expects an ordinary timestamp directory containing
writable ``@``/``@home`` Btrfs snapshots and the original ``info.json``.

Single restore and chain restore use the same workflow. Chain restore reuses
the exact recorded read-only Timeshift-side send parent when it is still present with
the expected UUID, allowing the first newer backup to arrive incrementally.
Otherwise it creates one justified full hidden seed before applying later
incrementals. Visible Timeshift payloads are writable Btrfs snapshots of the
hidden received subvolumes, preserving Btrfs copy-on-write sharing while the
receive chain remains intact until every stream has completed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any
import base64
import json
import shlex

from .btrfs_ops import BtrfsOps
from .commands import CommandError, stream_pipeline, sudo_prefix
from .config import AppConfig
from .endpoint import CommandEndpoint
from .inventory import BtrfsIndex, SourceInventory, build_source_btrfs_index, build_source_inventory
from .models import SnapshotMeta, SubvolumeMeta
from .source import SourceRunner
from .state import empty_state, resolve_state_send_path, validate_state_document
from .timeshift import (
    SNAPSHOT_RE,
    create_source_manual_snapshot,
    list_source_snapshots,
    parse_timeshift_list,
    timeshift_cmd,
)


RESTORE_RETENTION_CONFIRMATION = "I UNDERSTAND TIMESHIFT MAY DELETE RESTORED SNAPSHOTS OR OLDER THAN RESTORED SNAPSHOTS"
RESTORE_OS_IDENTITY_CONFIRMATION = "I UNDERSTAND THIS BACKUP MAY BELONG TO ANOTHER OS"
PRE_RESTORE_SNAPSHOT_COMMENT = "TimeShift-BTRFS-Sync pre-restore safety snapshot"


class RestoreError(RuntimeError):
    """Raised when backups cannot be imported safely into Timeshift."""


@dataclass(frozen=True, slots=True)
class TimeshiftOsIdentity:
    """Timeshift ``info.json`` provenance metadata for one snapshot."""

    sys_uuid: str
    snapshot_type: str
    sys_distro: str | None = None


@dataclass(slots=True)
class BackupSnapshot:
    """One validated local or SSH backup snapshot available for restore."""

    name: str
    path: str
    info_content: str
    payloads: dict[str, SubvolumeMeta]
    os_identity: TimeshiftOsIdentity | None = None


@dataclass(slots=True)
class BackupDirectoryRecord:
    """Ordinary filesystem facts for one backup timestamp directory."""

    name: str
    kind: str
    entries: dict[str, str]
    info_content: str | None
    info_error: str | None = None


@dataclass(slots=True)
class BackupRepository:
    """Access one local or SSH backup repository through one transport layer."""

    config: AppConfig
    runner: SourceRunner
    endpoint: CommandEndpoint
    ops: BtrfsOps

    @classmethod
    def from_config(cls, config: AppConfig) -> "BackupRepository":
        """Create the backup endpoint selected by restore.mode."""

        mode = "ssh" if config.restore.backup_uses_ssh else "local"
        runner = SourceRunner.from_mode(mode, config.ssh)
        endpoint = CommandEndpoint.for_source(runner) if runner.uses_ssh else CommandEndpoint.local("backup destination")
        return cls(
            config=config,
            runner=runner,
            endpoint=endpoint,
            ops=BtrfsOps(endpoint, config.destination.sudo, config.destination.btrfs_command),
        )

    @property
    def root(self) -> str:
        return str(PurePosixPath(str(self.config.destination.target_root)))

    @property
    def snapshots_root(self) -> str:
        return str(PurePosixPath(self.root) / "snapshots")

    @property
    def environment(self) -> dict[str, str] | None:
        return self.runner.environment()

    @property
    def location_label(self) -> str:
        return "remote SSH backup" if self.runner.uses_ssh else "local backup"

    def load_state(self) -> dict[str, Any]:
        """Read and validate state.json from the same endpoint as the backup."""

        path = str(PurePosixPath(str(self.config.state_file)))
        script = f"""
state_file={shlex.quote(path)}
if [ -L "$state_file" ]; then
    printf 'TSBTRFS_STATE_SYMLINK\n'
    exit 0
fi
if [ ! -e "$state_file" ]; then
    printf 'TSBTRFS_STATE_MISSING\n'
    exit 0
fi
if [ ! -f "$state_file" ]; then
    printf 'TSBTRFS_STATE_NOT_REGULAR\n'
    exit 0
fi
if [ ! -r "$state_file" ]; then
    printf 'TSBTRFS_STATE_UNREADABLE\n'
    exit 0
fi
printf 'TSBTRFS_STATE_BEGIN\n'
cat -- "$state_file"
printf '\nTSBTRFS_STATE_END\n'
""".strip()
        result = self.endpoint.run_shell(script, log_stderr=False, mirror_stderr=False)
        lines = result.stdout.splitlines()
        if lines == ["TSBTRFS_STATE_MISSING"]:
            return empty_state()
        markers = {
            "TSBTRFS_STATE_SYMLINK": "is a symlink",
            "TSBTRFS_STATE_NOT_REGULAR": "is not a regular file",
            "TSBTRFS_STATE_UNREADABLE": "is not readable by the backup SSH/local account",
        }
        if lines and lines[0] in markers:
            raise RestoreError(f"Backup state.json {path} {markers[lines[0]]}")
        try:
            start = lines.index("TSBTRFS_STATE_BEGIN")
            end = lines.index("TSBTRFS_STATE_END", start + 1)
        except ValueError as exc:
            raise RestoreError(f"Could not frame backup state.json from {self.location_label}: {path}") from exc
        content = "\n".join(lines[start + 1 : end])
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RestoreError(f"Backup state.json is invalid JSON: {path}: {exc}") from exc
        if not isinstance(data, dict):
            raise RestoreError(f"Backup state.json must contain a JSON object: {path}")
        validate_state_document(data)
        return data

    def scan_directories(self) -> dict[str, BackupDirectoryRecord]:
        """Read direct date entries and all info.json files in one endpoint call."""

        root = self.snapshots_root
        script = f"""
root={shlex.quote(root)}
if [ ! -d "$root" ]; then
    printf 'TSBTRFS_BACKUP_ROOT_MISSING\n'
    exit 0
fi
for date_path in "$root"/*; do
    [ -e "$date_path" ] || [ -L "$date_path" ] || continue
    name=${{date_path##*/}}
    if [ -L "$date_path" ]; then date_kind=symlink
    elif [ -d "$date_path" ]; then date_kind=directory
    else date_kind=other
    fi
    printf 'TSBTRFS_BACKUP_DATE\t%s\t%s\n' "$name" "$date_kind"
    [ "$date_kind" = directory ] || continue
    for entry_path in "$date_path"/* "$date_path"/.[!.]* "$date_path"/..?*; do
        [ -e "$entry_path" ] || [ -L "$entry_path" ] || continue
        entry=${{entry_path##*/}}
        if [ -L "$entry_path" ]; then entry_kind=symlink
        elif [ -f "$entry_path" ]; then entry_kind=file
        elif [ -d "$entry_path" ]; then entry_kind=directory
        else entry_kind=other
        fi
        printf 'TSBTRFS_BACKUP_ENTRY\t%s\t%s\t%s\n' "$name" "$entry" "$entry_kind"
    done
    info_path="$date_path/info.json"
    if [ -L "$info_path" ]; then
        printf 'TSBTRFS_BACKUP_INFO_ERROR\t%s\tsymlink\n' "$name"
    elif [ ! -f "$info_path" ]; then
        printf 'TSBTRFS_BACKUP_INFO_ERROR\t%s\tnot-regular\n' "$name"
    elif [ ! -r "$info_path" ]; then
        printf 'TSBTRFS_BACKUP_INFO_ERROR\t%s\tunreadable\n' "$name"
    else
        encoded=$(base64 < "$info_path" | tr -d '\n') || exit 41
        printf 'TSBTRFS_BACKUP_INFO\t%s\t%s\n' "$name" "$encoded"
    fi
done
""".strip()
        result = self.endpoint.run_shell(script, log_stderr=False, mirror_stderr=False)
        if result.stdout.strip() == "TSBTRFS_BACKUP_ROOT_MISSING":
            raise RestoreError(f"Backup snapshots root is unavailable on {self.location_label}: {root}")
        records: dict[str, BackupDirectoryRecord] = {}
        for line in result.stdout.splitlines():
            parts = line.split("\t")
            if not parts:
                continue
            if parts[0] == "TSBTRFS_BACKUP_DATE" and len(parts) == 3:
                records[parts[1]] = BackupDirectoryRecord(parts[1], parts[2], {}, None)
            elif parts[0] == "TSBTRFS_BACKUP_ENTRY" and len(parts) == 4:
                record = records.get(parts[1])
                if record is not None:
                    record.entries[parts[2]] = parts[3]
            elif parts[0] == "TSBTRFS_BACKUP_INFO" and len(parts) == 3:
                record = records.get(parts[1])
                if record is not None:
                    try:
                        record.info_content = base64.b64decode(parts[2], validate=True).decode("utf-8")
                    except (ValueError, UnicodeError) as exc:
                        record.info_error = f"invalid base64/UTF-8 metadata: {exc}"
            elif parts[0] == "TSBTRFS_BACKUP_INFO_ERROR" and len(parts) == 3:
                record = records.get(parts[1])
                if record is not None:
                    record.info_error = parts[2]
        return records

    def btrfs_index(self) -> BtrfsIndex:
        """Build one local or SSH Btrfs index for the complete backup tree."""

        index = build_source_btrfs_index(
            self.runner,
            self.snapshots_root,
            sudo=self.config.destination.sudo,
            btrfs_command=self.config.destination.btrfs_command,
            include_root=True,
            required=True,
        )
        if index.errors:
            raise RestoreError(
                f"Could not inventory backup Btrfs tree on {self.location_label}: " + "; ".join(index.errors)
            )
        return index


def _effective_send_uuid(meta: SubvolumeMeta) -> str:
    """Return the UUID identity carried by a Btrfs send stream.

    A normal source snapshot is identified by its UUID. A subvolume that was
    itself created by ``btrfs receive`` carries the original stream identity in
    ``Received UUID``; Btrfs reuses that identity when it is sent again.
    """

    value = meta.received_uuid or meta.uuid
    if not value:
        raise RestoreError(f"Btrfs payload has no usable send-stream UUID: {meta.path}")
    return value


def _info_os_identity(info_doc: dict[str, Any]) -> TimeshiftOsIdentity | None:
    """Return Timeshift provenance identity while ignoring mutable fields.

    Timeshift changes tags, comments, creation time, file counts, app version,
    live status, and Btrfs statistics between snapshots. ``sys-uuid`` records
    the root filesystem from which that snapshot originated; it is preserved
    when this app restores the original control file and is therefore provenance
    rather than authoritative live-repository identity. ``type`` identifies the
    snapshot backend. ``sys-distro`` is diagnostic only because an in-place
    distribution upgrade may change it.
    """

    sys_uuid = str(info_doc.get("sys-uuid") or "").strip()
    snapshot_type = str(info_doc.get("type") or "").strip().lower()
    sys_distro = str(info_doc.get("sys-distro") or "").strip() or None
    if snapshot_type and snapshot_type != "btrfs":
        raise RestoreError(f"Timeshift info.json describes unsupported snapshot type: {snapshot_type}")
    if not sys_uuid or not snapshot_type:
        return None
    return TimeshiftOsIdentity(sys_uuid, snapshot_type, sys_distro)


def _parse_info_json(content: str, *, label: str) -> tuple[dict[str, Any], TimeshiftOsIdentity | None]:
    """Parse one Timeshift control file and extract its provenance identity."""

    try:
        info_doc = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RestoreError(f"{label} is invalid JSON: {exc}") from exc
    if not isinstance(info_doc, dict):
        raise RestoreError(f"{label} must contain a JSON object")
    return info_doc, _info_os_identity(info_doc)


def _same_os_identity(left: TimeshiftOsIdentity | None, right: TimeshiftOsIdentity | None) -> bool:
    """Return whether two Timeshift control files have matching provenance."""

    return bool(
        left
        and right
        and left.sys_uuid == right.sys_uuid
        and left.snapshot_type == right.snapshot_type
    )


def _consistent_backup_identity(
    backups: dict[str, BackupSnapshot],
    names: list[str],
) -> tuple[TimeshiftOsIdentity | None, str]:
    """Require one non-conflicting provenance identity across the backup set."""

    identified = [(name, backups[name].os_identity) for name in names if backups[name].os_identity is not None]
    if not identified:
        return None, "selected backup info.json files do not contain sys-uuid and type"
    first_name, first = identified[0]
    assert first is not None
    conflicts = [
        name
        for name, identity in identified[1:]
        if not _same_os_identity(first, identity)
    ]
    if conflicts:
        raise RestoreError(
            "Selected backup snapshots contain conflicting Timeshift OS identities; refusing to combine them: "
            + ", ".join([first_name, *conflicts])
        )
    missing = [name for name in names if backups[name].os_identity is None]
    if missing:
        return None, "selected backup info.json identity is missing for: " + ", ".join(missing)
    return first, f"all selected backups identify sys-uuid {first.sys_uuid} with type {first.snapshot_type}"


def _timeshift_info_identities(timeshift_inventory: SourceInventory) -> dict[str, TimeshiftOsIdentity | None]:
    """Parse provenance identities from the coherent source info.json inventory."""

    identities: dict[str, TimeshiftOsIdentity | None] = {}
    for name, content in timeshift_inventory.snapshot_info_json.items():
        try:
            _doc, identity = _parse_info_json(content, label=f"Source Timeshift info.json for {name}")
        except RestoreError:
            identity = None
        identities[name] = identity
    return identities


def _compare_repository_os_identity(
    backup_identity: TimeshiftOsIdentity | None,
    source_identities: dict[str, TimeshiftOsIdentity | None],
) -> tuple[bool, str]:
    """Compare backup provenance with currently readable Timeshift control files.

    This is a useful cross-OS warning when no exact UUID common parent exists.
    It must not overrule a common parent already proven through state and live
    Btrfs identities.
    """

    if backup_identity is None:
        return False, "backup info.json does not provide sys-uuid and type"
    matching = [name for name, identity in source_identities.items() if _same_os_identity(backup_identity, identity)]
    if matching:
        distro_values = sorted(
            {identity.sys_distro for identity in source_identities.values() if _same_os_identity(backup_identity, identity) and identity and identity.sys_distro}
        )
        distro_note = f"; source distro metadata: {', '.join(distro_values)}" if distro_values else ""
        return True, (
            f"backup sys-uuid {backup_identity.sys_uuid} and type {backup_identity.snapshot_type} "
            f"match current Timeshift snapshot(s): {', '.join(sorted(matching))}{distro_note}"
        )
    source_uuids = sorted({identity.sys_uuid for identity in source_identities.values() if identity is not None})
    if not source_uuids:
        return False, "current Timeshift snapshots do not provide a comparable sys-uuid/type identity"
    return False, (
        f"backup sys-uuid {backup_identity.sys_uuid} does not match current Timeshift sys-uuid(s): "
        + ", ".join(source_uuids)
    )


@dataclass(slots=True)
class RestorePlan:
    """A side-effect-free single or chain restore plan."""

    backups: dict[str, BackupSnapshot]
    chain_names: list[str]
    restore_names: list[str]
    common_parent: str | None
    common_reason: str
    no_common_parent: bool
    initial_send_parent: str | None = None
    receive_parent_paths: dict[str, str] | None = None
    receive_parent_reason: str = "no reusable receive parent was selected"
    backup_identity: TimeshiftOsIdentity | None = None
    os_identity_match: bool = True
    os_identity_reason: str = "OS identity was prevalidated by the plan builder"

    @property
    def seed_name(self) -> str | None:
        return self.chain_names[0] if self.chain_names else None


def _source_path_exists(endpoint: CommandEndpoint, path: str) -> tuple[bool | None, str]:
    result = endpoint.run_shell(
        f"test -e {shlex.quote(path)}",
        check=False,
        log_stderr=False,
        mirror_stderr=False,
    )
    if result.returncode == 0:
        return True, ""
    if result.returncode == 1:
        return False, ""
    return None, result.stderr.strip() or result.stdout.strip() or f"return code {result.returncode}"


def _privileged_argv(config: AppConfig, *parts: str) -> list[str]:
    return sudo_prefix(config.source.sudo) + [str(part) for part in parts]


def _write_source_info_json(
    endpoint: CommandEndpoint,
    config: AppConfig,
    path: str,
    content: str,
) -> None:
    """Write exact captured metadata through the configured source privilege prefix."""

    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    tmp_path = path + ".ts-btrfs-sync.tmp"
    sudo_words = " ".join(shlex.quote(part) for part in sudo_prefix(config.source.sudo))
    script = f"""
sudo_words={shlex.quote(sudo_words)}
target={shlex.quote(path)}
tmp={shlex.quote(tmp_path)}
data={shlex.quote(encoded)}
run_privileged() {{
    if [ -n "$sudo_words" ]; then
        # shellcheck disable=SC2086
        $sudo_words "$@"
    else
        "$@"
    fi
}}
cleanup_tmp() {{ run_privileged rm -f -- "$tmp" >/dev/null 2>&1 || true; }}
trap cleanup_tmp EXIT HUP INT TERM
printf '%s' "$data" | base64 -d | run_privileged tee "$tmp" >/dev/null || exit 21
run_privileged chmod 0644 -- "$tmp" || exit 22
run_privileged mv -- "$tmp" "$target" || exit 23
trap - EXIT HUP INT TERM
""".strip()
    try:
        endpoint.run_shell(script)
    except CommandError as exc:
        raise RestoreError(
            "Could not write restored Timeshift info.json. Restore requires source-side permission "
            "for tee, chmod, mv, and exact temporary-file cleanup through source.sudo. "
            f"Target: {path}. Details: {exc}"
        ) from exc


def _validate_backup_snapshot(
    config: AppConfig,
    repository: BackupRepository,
    record: BackupDirectoryRecord,
    btrfs_index: BtrfsIndex,
) -> BackupSnapshot:
    """Validate one backup date, payload set, metadata file, and Btrfs identity."""

    snapshot_name = record.name
    if SNAPSHOT_RE.fullmatch(snapshot_name) is None or PurePosixPath(snapshot_name).name != snapshot_name:
        raise RestoreError(f"Invalid Timeshift snapshot name: {snapshot_name}")

    backup_date = str(PurePosixPath(repository.snapshots_root) / snapshot_name)
    if record.kind == "symlink":
        raise RestoreError(f"Refusing symlinked backup snapshot date: {backup_date}")
    if record.kind != "directory":
        raise RestoreError(f"Backup snapshot date is not a directory: {backup_date}")
    date_meta = btrfs_index.meta(backup_date)
    if date_meta is None:
        date_meta = repository.ops.meta(backup_date, name=snapshot_name, required=False)
    if date_meta is None:
        mistaken_timeshift_root = False
        if not repository.runner.uses_ssh:
            try:
                PurePosixPath(backup_date).relative_to(PurePosixPath(config.source.snapshot_root))
                mistaken_timeshift_root = True
            except ValueError:
                pass
        if mistaken_timeshift_root:
            raise RestoreError(
                "The local Timeshift repository is being scanned as the backup repository. "
                "Timeshift date folders below source.snapshot_root are correctly ordinary directories; "
                "only TimeShift-BTRFS-Sync backup date containers are Btrfs subvolumes. "
                "For SSH-backup-to-local restore, set [restore] mode = \"ssh\". "
                "Timeshift date folders are ordinary directories; backup date containers are Btrfs subvolumes. "
                "Misrouted path: " + backup_date
            )
        raise RestoreError(f"Backup snapshot date is missing or is not a Btrfs subvolume: {backup_date}")

    info_path = str(PurePosixPath(backup_date) / "info.json")
    if record.info_error:
        raise RestoreError(f"Backup snapshot has unusable info.json ({record.info_error}): {info_path}")
    if record.entries.get("info.json") != "file" or record.info_content is None:
        raise RestoreError(f"Backup snapshot has no readable regular info.json: {info_path}")
    info_content = record.info_content
    _info_doc, os_identity = _parse_info_json(info_content, label=f"Backup info.json {info_path}")

    expected_names = set(config.source.subvolumes) | {"info.json"}
    actual_names = set(record.entries)
    unknown = sorted(actual_names - expected_names)
    missing = sorted(set(config.source.subvolumes) - actual_names)
    if unknown:
        raise RestoreError(f"Backup snapshot {snapshot_name} contains unexpected entries: " + ", ".join(unknown))
    if missing:
        raise RestoreError(
            f"Backup snapshot {snapshot_name} is missing configured payload subvolume(s): " + ", ".join(missing)
        )

    payloads: dict[str, SubvolumeMeta] = {}
    for subvolume_name in config.source.subvolumes:
        path = str(PurePosixPath(backup_date) / subvolume_name)
        if record.entries.get(subvolume_name) == "symlink":
            raise RestoreError(f"Refusing symlinked backup payload: {path}")
        if record.entries.get(subvolume_name) != "directory":
            raise RestoreError(f"Backup payload is not a directory/Btrfs subvolume: {path}")
        meta = btrfs_index.meta(path)
        if meta is None:
            meta = repository.ops.meta(path, name=subvolume_name, required=False)
        if meta is None:
            raise RestoreError(f"Backup payload is not a Btrfs subvolume: {path}")
        if meta.readonly is not True:
            raise RestoreError(f"Backup payload must be read-only before btrfs send: {path}")
        if not meta.uuid:
            raise RestoreError(f"Backup payload has no readable Btrfs UUID: {path}")
        payloads[subvolume_name] = meta
    return BackupSnapshot(snapshot_name, backup_date, info_content, payloads, os_identity)


def _discover_backups(
    config: AppConfig,
    repository: BackupRepository,
    *,
    selected_name: str | None = None,
) -> dict[str, BackupSnapshot]:
    """Return selected or all valid backups ordered by Timeshift timestamp."""

    records = repository.scan_directories()
    if selected_name is not None:
        record = records.get(selected_name)
        if record is None or SNAPSHOT_RE.fullmatch(selected_name) is None:
            raise RestoreError(f"Backup snapshot was not found below {repository.snapshots_root}: {selected_name}")
        names = [selected_name]
    else:
        names = sorted(name for name in records if SNAPSHOT_RE.fullmatch(name) is not None)
    if not names:
        raise RestoreError(f"No restorable backup snapshots were found below {repository.snapshots_root}")
    btrfs_index = repository.btrfs_index()
    return {
        name: _validate_backup_snapshot(config, repository, records[name], btrfs_index)
        for name in names
    }


def _timeshift_snapshots(
    config: AppConfig,
    timeshift: SourceRunner,
) -> tuple[dict[str, SnapshotMeta], SourceInventory]:
    """Read one coherent Timeshift-target snapshot/cache/info.json inventory."""

    generation = build_source_inventory(
        timeshift,
        snapshot_root=config.source.snapshot_root,
        cache_root=config.source.cache_root,
        sudo=config.source.sudo,
        btrfs_command=config.source.btrfs_command,
        timeshift_command=config.source.timeshift_command,
        required=True,
    )
    snapshots = list_source_snapshots(
        timeshift,
        snapshot_root=config.source.snapshot_root,
        subvolumes=config.source.subvolumes,
        sudo=config.source.sudo,
        timeshift_command=config.source.timeshift_command,
        btrfs_command=config.source.btrfs_command,
        include_btrfs_info=True,
        btrfs_index=generation.snapshot_index,
        timeshift_output=generation.timeshift_output,
    )
    return {snapshot.name: snapshot for snapshot in snapshots}, generation


def _find_latest_common_parent(
    config: AppConfig,
    backups: dict[str, BackupSnapshot],
    source_by_name: dict[str, SnapshotMeta],
    source_identities: dict[str, TimeshiftOsIdentity | None],
    state: dict[str, Any],
) -> tuple[str | None, str]:
    """Find the newest date proven common by state and Btrfs UUID identity.

    ``info.json`` is still parsed and reported as useful provenance metadata,
    but it is not authoritative for a common-parent decision. Timeshift keeps
    the original snapshot control file when a snapshot is restored, while the
    currently listed repository may later contain snapshots created on a
    different filesystem incarnation. Scheduled tag/retention activity can
    therefore change which ``sys-uuid`` values are visible without changing
    the Btrfs lineage of an exact snapshot.

    The hard proof is the two independent links stored for every payload:

    * current Timeshift payload UUID == ``state.json original_source_uuid``;
    * backup Received UUID == ``state.json send_source_uuid``.

    A forged or stale state file cannot satisfy those checks unless both live
    Btrfs endpoints carry the recorded UUID identities.
    """

    state_snapshots = state.get("snapshots", {})
    if not state_snapshots:
        return None, "state.json has no snapshot identity history"

    latest_failure = "no backup timestamp is currently present in Timeshift"
    for name in reversed(list(backups)):
        source_snapshot = source_by_name.get(name)
        if source_snapshot is None:
            continue
        state_snapshot = state_snapshots.get(name)
        if not isinstance(state_snapshot, dict):
            latest_failure = f"{name} exists on both sides but has no state.json identity record"
            continue
        state_payloads = state_snapshot.get("subvolumes")
        if not isinstance(state_payloads, dict):
            latest_failure = f"{name} has no usable state.json payload records"
            continue

        reasons: list[str] = []
        backup_identity = backups[name].os_identity
        source_identity = source_identities.get(name)
        for subvolume_name in config.source.subvolumes:
            source_meta = source_snapshot.subvolumes.get(subvolume_name)
            backup_meta = backups[name].payloads.get(subvolume_name)
            state_meta = state_payloads.get(subvolume_name)
            if source_meta is None or backup_meta is None or not isinstance(state_meta, dict):
                reasons.append(f"{subvolume_name}: source, backup, or state metadata is missing")
                continue
            if state_meta.get("status") != "ok":
                reasons.append(f"{subvolume_name}: state record is not a completed transfer")
                continue
            expected_source_uuid = state_meta.get("original_source_uuid")
            expected_send_uuid = state_meta.get("send_source_uuid")
            if not source_meta.uuid or source_meta.uuid != expected_source_uuid:
                reasons.append(
                    f"{subvolume_name}: Timeshift UUID {source_meta.uuid or '-'} does not match "
                    f"recorded original UUID {expected_source_uuid or '-'}"
                )
            if not backup_meta.received_uuid or backup_meta.received_uuid != expected_send_uuid:
                reasons.append(
                    f"{subvolume_name}: backup Received UUID {backup_meta.received_uuid or '-'} does not match "
                    f"recorded send UUID {expected_send_uuid or '-'}"
                )
        if not reasons:
            if _same_os_identity(backup_identity, source_identity):
                info_note = "info.json provenance also matches"
            else:
                info_note = (
                    "info.json provenance differs "
                    f"(backup sys-uuid {backup_identity.sys_uuid if backup_identity else '-'}, "
                    f"source sys-uuid {source_identity.sys_uuid if source_identity else '-'}), "
                    "but this diagnostic-only provenance metadata is not used to override "
                    "exact state/Btrfs UUID proof"
                )
            return name, (
                "all configured Timeshift UUIDs and backup Received UUIDs match the same "
                f"state.json record; {info_note}"
            )
        latest_failure = f"{name} is not common: " + "; ".join(reasons)
    return None, latest_failure


def _find_reusable_receive_parent(
    config: AppConfig,
    timeshift_ops: BtrfsOps,
    timeshift_inventory: SourceInventory,
    state: dict[str, Any],
    common_parent: str,
) -> tuple[dict[str, str] | None, str]:
    """Find exact read-only Timeshift-side subvolumes for the first incremental receive.

    The visible Timeshift snapshot proves OS/source identity but often has a
    different UUID from the read-only cache snapshot that was actually sent.
    Btrfs incremental receive can skip the full common seed only when every
    payload's original send path still exists on the Timeshift side with the recorded send UUID and
    remains read-only.
    """

    state_snapshot = state.get("snapshots", {}).get(common_parent)
    if not isinstance(state_snapshot, dict):
        return None, f"common parent {common_parent} has no state.json record"
    state_payloads = state_snapshot.get("subvolumes")
    if not isinstance(state_payloads, dict):
        return None, f"common parent {common_parent} has no state payload records"

    paths: dict[str, str] = {}
    reasons: list[str] = []
    for subvolume_name in config.source.subvolumes:
        state_meta = state_payloads.get(subvolume_name)
        if not isinstance(state_meta, dict):
            reasons.append(f"{subvolume_name}: state payload record is missing")
            continue
        try:
            path = resolve_state_send_path(
                state_meta,
                snapshot_root=config.source.snapshot_root,
                cache_root=config.source.cache_root,
                snapshot_name=common_parent,
                subvolume_name=subvolume_name,
            )
        except ValueError as exc:
            reasons.append(f"{subvolume_name}: cannot resolve recorded send path: {exc}")
            continue
        expected_uuid = str(state_meta.get("send_source_uuid") or "")
        meta = timeshift_inventory.meta(path)
        if meta is None:
            meta = timeshift_ops.meta(path, name=subvolume_name, required=False)
        if meta is None:
            reasons.append(f"{subvolume_name}: recorded send parent is missing: {path}")
            continue
        if not expected_uuid or meta.uuid != expected_uuid:
            reasons.append(
                f"{subvolume_name}: receive-parent UUID {meta.uuid or '-'} does not match "
                f"recorded send UUID {expected_uuid or '-'} at {path}"
            )
            continue
        if meta.readonly is not True:
            reasons.append(f"{subvolume_name}: receive parent is not read-only: {path}")
            continue
        paths[subvolume_name] = path

    if reasons:
        return None, "; ".join(reasons)
    return paths, (
        "every configured payload still has its exact recorded read-only send parent on the Timeshift filesystem"
    )


def _build_restore_plan(
    config: AppConfig,
    repository: BackupRepository,
    timeshift: SourceRunner,
    *,
    timeshift_ops: BtrfsOps | None = None,
    snapshot_name: str | None,
    restore_all: bool,
) -> tuple[RestorePlan, dict[str, SnapshotMeta], str]:
    """Build a single or complete-chain restore plan without changing either side."""

    if bool(snapshot_name) == bool(restore_all):
        raise RestoreError("Choose exactly one restore selection: --snapshot <date> or --all")
    if timeshift_ops is None:
        timeshift_ops = BtrfsOps(
            CommandEndpoint.for_source(timeshift),
            config.source.sudo,
            config.source.btrfs_command,
        )

    source_by_name, timeshift_inventory = _timeshift_snapshots(config, timeshift)
    source_identities = _timeshift_info_identities(timeshift_inventory)

    if snapshot_name:
        backup = _discover_backups(config, repository, selected_name=snapshot_name)[snapshot_name]
        backup_identity, consistency_reason = _consistent_backup_identity({snapshot_name: backup}, [snapshot_name])
        os_match, os_reason = _compare_repository_os_identity(backup_identity, source_identities)
        return (
            RestorePlan(
                backups={snapshot_name: backup},
                chain_names=[snapshot_name],
                restore_names=[snapshot_name],
                common_parent=None,
                common_reason="single-snapshot restore has no incremental chain parent",
                no_common_parent=False,
                backup_identity=backup_identity,
                os_identity_match=os_match,
                os_identity_reason=f"{consistency_reason}; {os_reason}",
            ),
            source_by_name,
            timeshift_inventory.timeshift_output,
        )

    backups = _discover_backups(config, repository)
    names = list(backups)
    backup_identity, consistency_reason = _consistent_backup_identity(backups, names)
    os_match, os_reason = _compare_repository_os_identity(backup_identity, source_identities)
    try:
        state = repository.load_state()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise RestoreError(f"Could not load current state.json for common-parent validation: {exc}") from exc
    common_parent, reason = _find_latest_common_parent(
        config, backups, source_by_name, source_identities, state
    )

    # An exact common parent proven through current Timeshift UUIDs, backup
    # Received UUIDs, and the same state.json record is stronger evidence than
    # comparing historical Timeshift control-file provenance. The latter may
    # legitimately differ after a restored snapshot is retained, retagged, or
    # later replaced in the visible Timeshift set. Keep info.json as a warning
    # and no-common-parent safeguard, but never let it invalidate stronger
    # Btrfs lineage proof.
    if common_parent and not os_match:
        os_match = True
        os_reason = (
            f"{os_reason}; exact common parent {common_parent} is independently proven by "
            "current Timeshift UUIDs and backup Received UUIDs against the same state.json record, "
            "so differing info.json sys-uuid provenance is diagnostic only"
        )

    initial_send_parent: str | None = None
    receive_parent_paths: dict[str, str] | None = None
    receive_parent_reason = "no common parent exists"
    if common_parent:
        common_index = names.index(common_parent)
        restore_names = names[common_index + 1 :]
        if restore_names:
            receive_parent_paths, receive_parent_reason = _find_reusable_receive_parent(
                config, timeshift_ops, timeshift_inventory, state, common_parent
            )
            if receive_parent_paths is not None:
                initial_send_parent = common_parent
                chain_names = list(restore_names)
            else:
                chain_names = [common_parent, *restore_names]
        else:
            chain_names = []
            receive_parent_reason = "newest backup is already the newest common Timeshift snapshot"
    else:
        restore_names = names
        chain_names = names

    return (
        RestorePlan(
            backups=backups,
            chain_names=chain_names,
            restore_names=restore_names,
            common_parent=common_parent,
            common_reason=reason,
            no_common_parent=common_parent is None,
            initial_send_parent=initial_send_parent,
            receive_parent_paths=receive_parent_paths,
            receive_parent_reason=receive_parent_reason,
            backup_identity=backup_identity,
            os_identity_match=os_match,
            os_identity_reason=f"{consistency_reason}; {os_reason}",
        ),
        source_by_name,
        timeshift_inventory.timeshift_output,
    )


def _remove_restore_directory(
    endpoint: CommandEndpoint,
    source_ops: BtrfsOps,
    config: AppConfig,
    directory: str,
    payload_names: list[str],
) -> list[str]:
    """Remove one exact app-created ordinary restore directory and its payloads."""

    errors: list[str] = []
    exists, exists_error = _source_path_exists(endpoint, directory)
    if exists is None:
        return [f"could not inspect restore directory {directory}: {exists_error}"]
    if not exists:
        return errors

    present: list[str] = []
    for name in payload_names:
        path = f"{directory}/{name}"
        if source_ops.meta(path, name=name, required=False) is not None:
            present.append(path)
    if present:
        confirmed, delete_errors = source_ops.batch_delete(list(reversed(present)))
        errors.extend(delete_errors)
        missing = [path for path in present if path not in set(confirmed)]
        if missing:
            errors.append("could not confirm cleanup of restored subvolume(s): " + ", ".join(missing))

    for metadata_path in (
        f"{directory}/info.json",
        f"{directory}/info.json.ts-btrfs-sync.tmp",
    ):
        result = endpoint.run_argv(
            _privileged_argv(config, "rm", "-f", "--", metadata_path),
            check=False,
            log_stderr=False,
            mirror_stderr=False,
        )
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or f"return code {result.returncode}"
            errors.append(f"could not remove restore metadata {metadata_path}: {detail}")

    result = endpoint.run_argv(
        _privileged_argv(config, "rmdir", "--", directory),
        check=False,
        log_stderr=False,
        mirror_stderr=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"return code {result.returncode}"
        errors.append(f"could not remove restore directory {directory}: {detail}")
    return errors


def _cleanup_restore_attempt(
    endpoint: CommandEndpoint,
    source_ops: BtrfsOps,
    config: AppConfig,
    *,
    chain_root: str,
    chain_names: list[str],
    staging_names: list[str],
    committed_names: list[str],
) -> list[str]:
    """Roll back only directories created by the current restore attempt."""

    errors: list[str] = []
    snapshot_root = config.source.snapshot_root.rstrip("/")
    for name in reversed(committed_names):
        errors.extend(
            _remove_restore_directory(
                endpoint,
                source_ops,
                config,
                f"{snapshot_root}/{name}",
                config.source.subvolumes,
            )
        )
    for name in reversed(staging_names):
        errors.extend(
            _remove_restore_directory(
                endpoint,
                source_ops,
                config,
                f"{snapshot_root}/.ts-btrfs-sync-restore-{name}",
                config.source.subvolumes,
            )
        )
    for name in reversed(chain_names):
        errors.extend(
            _remove_restore_directory(
                endpoint,
                source_ops,
                config,
                f"{chain_root}/{name}",
                config.source.subvolumes,
            )
        )
    result = endpoint.run_argv(
        _privileged_argv(config, "rmdir", "--", chain_root),
        check=False,
        log_stderr=False,
        mirror_stderr=False,
    )
    if result.returncode != 0:
        exists, exists_error = _source_path_exists(endpoint, chain_root)
        if exists is None:
            errors.append(f"could not verify restore chain root cleanup {chain_root}: {exists_error}")
        elif exists:
            detail = result.stderr.strip() or result.stdout.strip() or f"return code {result.returncode}"
            errors.append(f"could not remove restore chain root {chain_root}: {detail}")
    return errors


def _create_pre_restore_snapshot(
    config: AppConfig,
    timeshift: SourceRunner,
    timeshift_ops: BtrfsOps,
    *,
    existing_names: set[str],
    restore_names: list[str],
) -> str:
    """Create and verify one safety snapshot on the Timeshift restore target.

    The configured ``source`` endpoint is always the Timeshift side. In pull
    restore mode that endpoint is local while the backup repository is remote,
    so this helper can never create a snapshot on the backup host.
    """

    location = "SSH Timeshift target" if timeshift.uses_ssh else "local Timeshift target"
    print()
    print("PRE-RESTORE SAFETY SNAPSHOT")
    print("===========================")
    print(f"  location: {location}")
    print("  tag:      O (Timeshift on-demand default)")
    print(f"  comment:  {PRE_RESTORE_SNAPSHOT_COMMENT}")
    print("  timing:   before any restore directory, Btrfs receive, or visible restored snapshot")
    print("  backup:   no snapshot or other backup-tree change is made")

    try:
        create_source_manual_snapshot(
            timeshift,
            sudo=config.source.sudo,
            timeshift_command=config.source.timeshift_command,
            comment=PRE_RESTORE_SNAPSHOT_COMMENT,
        )
    except CommandError as exc:
        raise RestoreError(
            "Could not create the requested pre-restore Timeshift safety snapshot on the restore target. "
            "No backup stream has started. Verify source-side Timeshift privilege and configuration. "
            f"Details: {exc}"
        ) from exc

    try:
        listed = timeshift.run(timeshift_cmd(config.source.sudo, config.source.timeshift_command, ["--list"]))
    except CommandError as exc:
        raise RestoreError(
            "The pre-restore Timeshift command completed, but a fresh timeshift --list could not verify it. "
            "The safety snapshot may exist; no backup stream has started. Inspect Timeshift before retrying. "
            f"Details: {exc}"
        ) from exc
    current = parse_timeshift_list(listed.stdout, config.source.snapshot_root.rstrip("/"))
    newly_listed = [snapshot for snapshot in current if snapshot.name not in existing_names]
    comment_matches = [
        snapshot
        for snapshot in newly_listed
        if (snapshot.comment or "").strip() == PRE_RESTORE_SNAPSHOT_COMMENT
    ]
    if len(comment_matches) == 1:
        created = comment_matches[0]
    elif len(newly_listed) == 1:
        # Some Timeshift versions or list formats do not expose the complete
        # comment. One newly listed timestamp still proves the scripted create
        # produced exactly one snapshot during this guarded operation.
        created = newly_listed[0]
    else:
        names = ", ".join(snapshot.name for snapshot in newly_listed) or "none"
        raise RestoreError(
            "Timeshift create returned successfully, but the pre-restore snapshot could not be identified "
            f"uniquely in a fresh timeshift --list. New timestamp(s): {names}. "
            "No backup stream has started; inspect Timeshift before retrying."
        )

    if created.name in restore_names:
        raise RestoreError(
            "The new pre-restore safety snapshot timestamp collides with a backup selected for restore: "
            f"{created.name}. The safety snapshot was left in place and no backup stream was started."
        )

    snapshot_root = config.source.snapshot_root.rstrip("/")
    for subvolume_name in config.source.subvolumes:
        payload_path = f"{snapshot_root}/{created.name}/{subvolume_name}"
        try:
            meta = timeshift_ops.meta(payload_path, name=subvolume_name, required=True)
        except RuntimeError as exc:
            raise RestoreError(
                "The pre-restore Timeshift snapshot is listed, but a configured Btrfs payload could not be verified: "
                f"{payload_path}. The snapshot was left in place and no backup stream was started. Details: {exc}"
            ) from exc
        if not meta.uuid:
            raise RestoreError(
                "The pre-restore Timeshift snapshot is listed but its Btrfs payload has no UUID: "
                f"{payload_path}. The snapshot was left in place and no backup stream was started."
            )

    print(f"  created:  {created.name}")
    print("  verified: Timeshift lists it and every configured Btrfs payload has a UUID")
    print("  retention: this safety snapshot is intentionally left in place even if restore later fails")
    return created.name


def _print_restored_snapshot_retention_warning() -> None:
    """Explain that restored Timeshift tags remain subject to normal retention."""

    print()
    print("RESTORED SNAPSHOT RETENTION WARNING")
    print("===================================")
    print("The original info.json is restored unchanged, including its original H/D/W/M tags.")
    print("Normal Timeshift retention may later delete a restored Hourly, Daily, Weekly, or Monthly")
    print("snapshot when it falls outside the configured keep counts.")
    print("Adding a tagged restored snapshot may also push an existing tagged snapshot older than")
    print("the restored snapshot outside the same keep count, causing that older snapshot to be deleted.")
    print("A restored rollback point or an older existing rollback point may therefore disappear.")
    print("Review or pause Timeshift scheduling and retention until the rollback is complete.")
    print("Real restore requires typing this exact sentence:")
    print(f"  {RESTORE_RETENTION_CONFIRMATION}")


def _print_restore_plan(
    config: AppConfig,
    timeshift: SourceRunner,
    plan: RestorePlan,
    *,
    dry_run: bool,
    create_pre_restore_snapshot: bool = False,
    repository: BackupRepository | None = None,
) -> None:
    print("TIMESHIFT SNAPSHOT RESTORE")
    print("==========================")
    print(f"  selection:      {'all snapshots' if plan.common_parent or plan.no_common_parent else plan.restore_names[0]}")
    print(f"  restore mode:   {config.restore.mode}")
    timeshift_location = "SSH remote" if timeshift.uses_ssh else "local"
    print(f"  Timeshift side: {timeshift_location}")
    print(f"  snapshot_root:  {config.source.snapshot_root.rstrip('/')} ({timeshift_location})")
    print(f"  cache_root:     {config.source.cache_root or 'disabled'} ({timeshift_location})")
    print("  path ownership: snapshot_root and cache_root always use the same Timeshift endpoint")
    print("  date path type: ordinary directory")
    print(f"  payloads:       {', '.join(config.source.subvolumes)}")
    if repository is not None:
        print(f"  backup side:    {'SSH remote' if repository.runner.uses_ssh else 'local'}")
        print(f"  backup root:    {repository.root}")
    print(f"  run mode:       {'dry-run' if dry_run else 'REAL RESTORE'}")
    if create_pre_restore_snapshot:
        print("  safety snapshot: create one Timeshift on-demand snapshot on the restore target before receive")
        print("  backup changes:  none; the safety snapshot is never created on the backup repository")
    else:
        print("  safety snapshot: disabled (enable with --create-pre-restore-snapshot)")
    if plan.backup_identity:
        print(f"  backup OS UUID: {plan.backup_identity.sys_uuid}")
        print(f"  backup type:    {plan.backup_identity.snapshot_type}")
        print(f"  backup distro:  {plan.backup_identity.sys_distro or '-'}")
    else:
        print("  backup OS UUID: UNKNOWN")
    print(f"  OS identity:    {'MATCH' if plan.os_identity_match else 'NOT PROVEN'}")
    print(f"  OS detail:      {plan.os_identity_reason}")
    if not plan.os_identity_match:
        print("  DANGER: info.json does not prove that this backup belongs to the current OS")

    if plan.common_parent:
        print(f"  common parent:  {plan.common_parent}")
        print(f"  identity proof: {plan.common_reason}")
        if plan.initial_send_parent:
            print(f"  chain start:    incremental from common backup {plan.initial_send_parent}")
            print("  receive parent: exact existing read-only Timeshift-side send parent(s)")
            if plan.receive_parent_paths:
                for payload, path in sorted(plan.receive_parent_paths.items()):
                    print(f"    {payload}: {path}")
        elif plan.restore_names:
            print("  chain seed:     full hidden receive of the common backup")
            print(f"  full reason:    {plan.receive_parent_reason}")
    elif plan.no_common_parent:
        print("  common parent:  NONE")
        print(f"  identity check: {plan.common_reason}")
        print("  DANGER: the backup could belong to a different OS/source repository")
        print("  chain seed:     full receive of the oldest backup")
    else:
        print("  chain seed:     full receive of the selected backup")
    if plan.restore_names:
        print(f"  restore count:  {len(plan.restore_names)}")
        print(f"  first restore:  {plan.restore_names[0]}")
        print(f"  last restore:   {plan.restore_names[-1]}")
        print("  transfer order: oldest to newest")
        if plan.initial_send_parent:
            print("  transfer mode:  incremental from common parent, then incrementals")
        else:
            print("  transfer mode:  one full chain seed, then Btrfs incrementals")
        print("  final payloads: writable CoW snapshots of hidden received subvolumes")
    else:
        print("  restore count:  0")
        print("  status:         source Timeshift already reaches the newest backup/common parent")
    if plan.restore_names:
        _print_restored_snapshot_retention_warning()


def restore_backups(
    config: AppConfig,
    *,
    snapshot_name: str | None,
    restore_all: bool,
    dry_run: bool,
    danger_confirmed: bool,
    allow_no_common_parent: bool,
    allow_os_identity_mismatch: bool = False,
    create_pre_restore_snapshot: bool = False,
) -> None:
    """Restore one snapshot or a complete backup chain into Timeshift."""

    repository = BackupRepository.from_config(config)
    timeshift_mode = "ssh" if config.restore.timeshift_uses_ssh else "local"
    timeshift = SourceRunner.from_mode(timeshift_mode, config.ssh)
    timeshift_endpoint = CommandEndpoint.for_source(timeshift)
    timeshift_ops = BtrfsOps(timeshift_endpoint, config.source.sudo, config.source.btrfs_command)
    plan, source_by_name, _timeshift_output = _build_restore_plan(
        config,
        repository,
        timeshift,
        timeshift_ops=timeshift_ops,
        snapshot_name=snapshot_name,
        restore_all=restore_all,
    )
    _print_restore_plan(
        config,
        timeshift,
        plan,
        dry_run=dry_run,
        create_pre_restore_snapshot=create_pre_restore_snapshot,
        repository=repository,
    )

    if not plan.restore_names:
        return
    if restore_all and plan.no_common_parent and not dry_run and not allow_no_common_parent:
        raise RestoreError(
            "No state/Btrfs UUID-confirmed common snapshot exists between the current Timeshift repository and this backup. "
            "Restoring all snapshots could import another OS. Re-run only after verification with "
            "--allow-no-common-parent."
        )
    if not plan.os_identity_match and not dry_run and not allow_os_identity_mismatch:
        raise RestoreError(
            "Timeshift info.json does not prove that the backup belongs to the current OS. "
            "Re-run only after independent verification with --allow-os-identity-mismatch."
        )
    if allow_no_common_parent and not restore_all:
        raise RestoreError("--allow-no-common-parent is valid only with --all")

    snapshot_root = config.source.snapshot_root.rstrip("/")
    seed = plan.seed_name
    assert seed is not None
    last = plan.chain_names[-1]
    chain_root = f"{snapshot_root}/.ts-btrfs-sync-restore-chain-{seed}-to-{last}"

    root_check = timeshift_endpoint.run_shell(
        f"test -d {shlex.quote(snapshot_root)}",
        check=False,
        log_stderr=False,
        mirror_stderr=False,
    )
    if root_check.returncode != 0:
        detail = root_check.stderr.strip() or root_check.stdout.strip() or "path is missing, inaccessible, or not a directory"
        raise RestoreError(f"Source Timeshift snapshot_root is unavailable: {snapshot_root}: {detail}")

    paths_to_require_absent = [("restore chain root", chain_root)]
    for name in plan.restore_names:
        paths_to_require_absent.extend(
            [
                ("final Timeshift date", f"{snapshot_root}/{name}"),
                ("restore staging directory", f"{snapshot_root}/.ts-btrfs-sync-restore-{name}"),
            ]
        )
    for label, path in paths_to_require_absent:
        exists, error = _source_path_exists(timeshift_endpoint, path)
        if exists is None:
            raise RestoreError(f"Could not check {label} {path}: {error}")
        if exists:
            raise RestoreError(f"Refusing to overwrite existing {label}: {path}")

    # A target date that Timeshift already lists but failed the UUID common-parent
    # proof is a divergent/cross-OS collision and must never be overwritten.
    collisions = sorted(set(plan.restore_names) & set(source_by_name))
    if collisions:
        raise RestoreError(
            "Restore target date(s) already exist in Timeshift but are not the newest state/Btrfs UUID-confirmed common parent: "
            + ", ".join(collisions)
        )

    if dry_run:
        if create_pre_restore_snapshot:
            location = "SSH Timeshift target" if timeshift.uses_ssh else "local Timeshift target"
            print(
                f"  would create one pre-restore Timeshift on-demand safety snapshot on the {location}; "
                "the backup repository would remain unchanged"
            )
        previous_name = plan.initial_send_parent
        for name in plan.chain_names:
            mode = "full" if previous_name is None else f"incremental from {previous_name}"
            visibility = "hidden seed only" if name == plan.common_parent else "then CoW-cloned into Timeshift"
            print(f"  would receive {name}: {mode}; {visibility}")
            previous_name = name
        return

    if not danger_confirmed:
        raise RestoreError("Real restore requires --i-understand-this-modifies-timeshift")
    retention_confirmation = input(
        f"Type {RESTORE_RETENTION_CONFIRMATION} to confirm you understand the retention risk: "
    ).strip()
    if retention_confirmation != RESTORE_RETENTION_CONFIRMATION:
        raise RestoreError("Restored-snapshot retention confirmation did not match")
    if not plan.os_identity_match:
        os_confirmation = input(
            f"Type {RESTORE_OS_IDENTITY_CONFIRMATION} to accept the cross-OS identity risk: "
        ).strip()
        if os_confirmation != RESTORE_OS_IDENTITY_CONFIRMATION:
            raise RestoreError("OS-identity risk confirmation did not match")
    if restore_all and plan.no_common_parent:
        if input("Type RESTORE ALL WITHOUT COMMON PARENT to continue: ").strip() != "RESTORE ALL WITHOUT COMMON PARENT":
            raise RestoreError("No-common-parent restore confirmation did not match")
        if input(f"Type the configured job name ({config.name}) to continue: ").strip() != config.name:
            raise RestoreError("Configured job-name confirmation did not match")
    elif restore_all:
        if input("Type RESTORE SNAPSHOT CHAIN to continue: ").strip() != "RESTORE SNAPSHOT CHAIN":
            raise RestoreError("Restore-chain confirmation did not match")
        if input(f"Type the common parent ({plan.common_parent}) to continue: ").strip() != plan.common_parent:
            raise RestoreError("Common-parent confirmation did not match")
    else:
        selected = plan.restore_names[0]
        if input("Type RESTORE SNAPSHOT to continue: ").strip() != "RESTORE SNAPSHOT":
            raise RestoreError("Restore confirmation did not match")
        if input(f"Type the snapshot name ({selected}) to continue: ").strip() != selected:
            raise RestoreError("Snapshot-name confirmation did not match")

    pre_restore_snapshot_name: str | None = None
    if create_pre_restore_snapshot:
        pre_restore_snapshot_name = _create_pre_restore_snapshot(
            config,
            timeshift,
            timeshift_ops,
            existing_names=set(source_by_name),
            restore_names=plan.restore_names,
        )

    chain_created: list[str] = []
    staging_created: list[str] = []
    committed: list[str] = []
    try:
        try:
            timeshift_endpoint.run_argv(_privileged_argv(config, "mkdir", "-m", "0755", "--", chain_root))
        except CommandError as exc:
            raise RestoreError(
                "Could not create the ordinary hidden restore-chain directory. Run local restore as root or grant "
                "narrow source.sudo permission for mkdir, tee, chmod, mv, rm, and rmdir in addition to "
                "btrfs/timeshift. For SSH restore those permissions must exist on the remote source. "
                f"Path: {chain_root}. Details: {exc}"
            ) from exc

        right_label = "REMOTE TIMESHIFT RECEIVE" if timeshift.uses_ssh else "LOCAL TIMESHIFT RECEIVE"
        previous_name: str | None = plan.initial_send_parent
        for name in plan.chain_names:
            receive_dir = f"{chain_root}/{name}"
            timeshift_endpoint.run_argv(_privileged_argv(config, "mkdir", "-m", "0755", "--", receive_dir))
            chain_created.append(name)
            for subvolume_name in config.source.subvolumes:
                backup = plan.backups[name]
                backup_path = str(PurePosixPath(backup.path) / subvolume_name)
                parent_path = (
                    str(PurePosixPath(plan.backups[previous_name].path) / subvolume_name)
                    if previous_name is not None
                    else None
                )
                received_path = f"{receive_dir}/{subvolume_name}"
                print()
                print(f"Restoring chain {name}/{subvolume_name}: {'full' if parent_path is None else 'incremental'}")
                stream_pipeline(
                    repository.ops.send_command(
                        backup_path,
                        parent_path=parent_path,
                        compressed_data=False,
                        proto=None,
                        verbose=config.stream.btrfs_verbose,
                    ),
                    timeshift_ops.receive_command(receive_dir, verbose=config.stream.btrfs_verbose),
                    middle_cmd=config.stream.command(),
                    left_env=repository.environment,
                    middle_env=None,
                    right_env=timeshift.environment(),
                    left_label="REMOTE BACKUP SEND" if repository.runner.uses_ssh else "LOCAL BACKUP SEND",
                    right_label=right_label,
                )
                received_meta = timeshift_ops.meta(received_path, name=subvolume_name, required=True)
                expected_uuid = _effective_send_uuid(backup.payloads[subvolume_name])
                if received_meta.received_uuid != expected_uuid:
                    raise RestoreError(
                        f"Restored chain payload Received UUID mismatch for {received_path}: "
                        f"expected {expected_uuid}, got {received_meta.received_uuid or '-'}"
                    )
                if received_meta.readonly is not True:
                    raise RestoreError(f"Hidden received chain payload must remain read-only: {received_path}")
            previous_name = name

        # Only after the complete received chain exists do we expose writable
        # Timeshift snapshots. These snapshots share extents with the hidden
        # received chain through Btrfs CoW.
        for name in plan.restore_names:
            staging_dir = f"{snapshot_root}/.ts-btrfs-sync-restore-{name}"
            timeshift_endpoint.run_argv(_privileged_argv(config, "mkdir", "-m", "0755", "--", staging_dir))
            staging_created.append(name)
            for subvolume_name in config.source.subvolumes:
                received_path = f"{chain_root}/{name}/{subvolume_name}"
                visible_path = f"{staging_dir}/{subvolume_name}"
                timeshift_ops.snapshot(received_path, visible_path, readonly=False)
                visible_meta = timeshift_ops.meta(visible_path, name=subvolume_name, required=True)
                if visible_meta.readonly is not False:
                    raise RestoreError(f"Restored Timeshift payload is not writable: {visible_path}")
                received_meta = timeshift_ops.meta(received_path, name=subvolume_name, required=True)
                if received_meta.uuid and visible_meta.parent_uuid and visible_meta.parent_uuid != received_meta.uuid:
                    raise RestoreError(
                        f"Restored Timeshift payload does not identify its hidden received CoW parent: {visible_path}"
                    )
            _write_source_info_json(
                timeshift_endpoint,
                config,
                f"{staging_dir}/info.json",
                plan.backups[name].info_content,
            )
            info_result = timeshift_endpoint.run_argv(["cat", "--", f"{staging_dir}/info.json"])
            if info_result.stdout != plan.backups[name].info_content:
                raise RestoreError(f"Restored info.json content verification failed: {staging_dir}/info.json")

        for name in plan.restore_names:
            staging_dir = f"{snapshot_root}/.ts-btrfs-sync-restore-{name}"
            final_dir = f"{snapshot_root}/{name}"
            timeshift_endpoint.run_argv(_privileged_argv(config, "mv", "--", staging_dir, final_dir))
            committed.append(name)
            for subvolume_name in config.source.subvolumes:
                final_payload = f"{final_dir}/{subvolume_name}"
                meta = timeshift_ops.meta(final_payload, name=subvolume_name, required=True)
                if meta.readonly is not False:
                    raise RestoreError(f"Final Timeshift payload is not writable: {final_payload}")
            final_info = timeshift_endpoint.run_argv(["cat", "--", f"{final_dir}/info.json"])
            if final_info.stdout != plan.backups[name].info_content:
                raise RestoreError(f"Final Timeshift info.json verification failed: {final_dir}/info.json")

        listed = timeshift.run(timeshift_cmd(config.source.sudo, config.source.timeshift_command, ["--list"]))
        listed_names = {item.name for item in parse_timeshift_list(listed.stdout, snapshot_root)}
        missing_listed = [name for name in plan.restore_names if name not in listed_names]
        if missing_listed:
            raise RestoreError(
                "Restore files were committed, but Timeshift --list did not report: " + ", ".join(missing_listed)
            )

        cleanup_errors = _cleanup_restore_attempt(
            timeshift_endpoint,
            timeshift_ops,
            config,
            chain_root=chain_root,
            chain_names=chain_created,
            staging_names=[],
            committed_names=[],
        )
        if cleanup_errors:
            # The visible snapshots have already been committed and verified by
            # Timeshift. Do not destroy usable restored snapshots merely because
            # cleanup of the hidden read-only receive chain needs manual help.
            raise RestoreError(
                "Snapshots were restored and accepted by Timeshift, but hidden restore-chain cleanup failed. "
                "The restored snapshots were intentionally left in place:\n  "
                + "\n  ".join(cleanup_errors)
            )
        print()
        print(f"Restore complete: Timeshift accepts {len(plan.restore_names)} snapshot(s)")
        print(f"First restored: {plan.restore_names[0]}")
        print(f"Last restored:  {plan.restore_names[-1]}")
        if pre_restore_snapshot_name:
            print(f"Pre-restore safety snapshot retained: {pre_restore_snapshot_name}")
    except Exception as exc:
        if committed and set(committed) == set(plan.restore_names):
            # All requested visible snapshots were already committed. A later
            # Timeshift-list or hidden-cleanup error must be reported for manual
            # inspection without deleting those potentially usable snapshots.
            raise
        cleanup_errors = _cleanup_restore_attempt(
            timeshift_endpoint,
            timeshift_ops,
            config,
            chain_root=chain_root,
            chain_names=chain_created,
            staging_names=staging_created,
            committed_names=committed,
        )
        if cleanup_errors:
            raise RestoreError(f"{exc}\nRestore rollback also failed:\n  " + "\n  ".join(cleanup_errors)) from exc
        raise

