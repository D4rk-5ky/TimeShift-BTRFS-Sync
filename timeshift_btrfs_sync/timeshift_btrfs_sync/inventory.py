"""Per-run Btrfs subvolume indexes for fewer SSH calls.

The index is intentionally short lived. It is built at the start of a command
or refreshed after a create/receive/delete operation. It never replaces the
UUID safety rules; it only replaces repeated ``btrfs subvolume list/show``
process startups with dictionary lookups whenever the same metadata has already
been read in the current run.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os
import pwd
import re
import shlex

from .commands import quote_join, sudo_prefix
from .models import SubvolumeMeta, send_stream_uuid
from .btrfs_ops import BtrfsOps, parse_subvolume_show
from .endpoint import CommandEndpoint
from .paths import normalize_source_path as normalize_path, is_same_or_under as is_under, listed_path_to_absolute
from .ssh import SSHRunner
from .source import SourceRunner


@dataclass(slots=True)
class BtrfsIndex:
    """In-memory index of Btrfs subvolumes below one root path."""

    root: str
    location: str
    by_path: dict[str, SubvolumeMeta] = field(default_factory=dict)
    by_uuid: dict[str, SubvolumeMeta] = field(default_factory=dict)
    by_received_uuid: dict[str, SubvolumeMeta] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    root_missing: bool = False

    def add(self, meta: SubvolumeMeta | None) -> None:
        """Add or replace one indexed subvolume."""

        if not meta or not meta.path:
            return
        path = normalize_path(meta.path)
        meta.path = path
        self.by_path[path] = meta
        if meta.uuid:
            self.by_uuid[meta.uuid] = meta
        if meta.received_uuid:
            self.by_received_uuid[meta.received_uuid] = meta

    def discard(self, path: str) -> None:
        """Remove one path and any known UUID lookup entries for it."""

        path = normalize_path(path)
        meta = self.by_path.pop(path, None)
        if not meta:
            return
        if meta.uuid and self.by_uuid.get(meta.uuid) is meta:
            self.by_uuid.pop(meta.uuid, None)
        if meta.received_uuid and self.by_received_uuid.get(meta.received_uuid) is meta:
            self.by_received_uuid.pop(meta.received_uuid, None)

    def contains(self, path: str | Path | None) -> bool:
        """Return True when ``path`` is an indexed subvolume."""

        return bool(path) and normalize_path(path) in self.by_path

    def meta(self, path: str | Path | None) -> SubvolumeMeta | None:
        """Return metadata for ``path`` if it was indexed."""

        return self.by_path.get(normalize_path(path)) if path else None

    def find_send_uuid(self, uuid: str | None) -> SubvolumeMeta | None:
        """Return a subvolume whose Btrfs send-stream identity equals ``uuid``.

        Native snapshots send their local UUID. Received snapshots send the
        original identity stored in ``Received UUID``. Looking through both
        indexes prevents a received copy from being mistaken for a different
        stream merely because its local UUID changed on receive.
        """

        if not uuid:
            return None
        for candidate in (self.by_received_uuid.get(uuid), self.by_uuid.get(uuid)):
            if candidate is not None and send_stream_uuid(candidate) == uuid:
                return candidate
        return None

    def remove_tree(self, path: str | Path) -> None:
        """Remove a deleted path and all indexed descendants."""

        root = normalize_path(path)
        for candidate in list(self.by_path):
            if is_under(candidate, root):
                self.discard(candidate)


@dataclass(slots=True)
class SourceInventory:
    """One coherent source-side Timeshift/Btrfs inventory.

    In SSH mode the Timeshift list, all readable per-date ``info.json``
    contents, the snapshot-root Btrfs index, and the cache-root Btrfs index are
    captured inside one SSH session. Keeping these views together is important
    when short-lived snapshots are created or deleted: parent selection and
    metadata preservation use one inventory generation instead of mixing
    results from several separately timed SSH commands.
    """

    timeshift_output: str
    snapshot_index: BtrfsIndex
    cache_index: BtrfsIndex | None
    snapshot_info_json: dict[str, str] = field(default_factory=dict)
    snapshot_info_errors: dict[str, str] = field(default_factory=dict)
    source_user_name: str | None = None
    source_user_uid: int | None = None

    @property
    def snapshot_names(self) -> tuple[str, ...]:
        """Return Timeshift timestamp names in sorted order."""

        pattern = re.compile(r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}")
        return tuple(sorted(set(pattern.findall(self.timeshift_output))))

    def meta(self, path: str | Path | None) -> SubvolumeMeta | None:
        """Return source metadata from cache first, then snapshot-root index."""

        if not path:
            return None
        if self.cache_index is not None:
            meta = self.cache_index.meta(path)
            if meta is not None:
                return meta
        return self.snapshot_index.meta(path)

def _clean_uuid(value: str | None) -> str | None:
    """Normalize Btrfs UUID fields from list/show output."""

    if value is None:
        return None
    value = value.strip()
    return None if not value or value == "-" else value


def parse_subvolume_list(output: str, root_path: str | Path) -> list[SubvolumeMeta]:
    """Parse ``btrfs subvolume list -u -q -R`` output for one root."""

    metas: list[SubvolumeMeta] = []
    for line in output.splitlines():
        before, sep, raw_path = line.strip().partition(" path ")
        if not sep:
            continue
        abs_path = listed_path_to_absolute(root_path, raw_path, scoped_to_root=True)
        if not abs_path:
            continue
        tokens = before.split()
        meta = SubvolumeMeta(name=Path(abs_path).name, path=abs_path)
        for idx, token in enumerate(tokens[:-1]):
            key = token.lower()
            value = _clean_uuid(tokens[idx + 1])
            if key == "uuid":
                meta.uuid = value
            elif key == "parent_uuid":
                meta.parent_uuid = value
            elif key == "received_uuid":
                meta.received_uuid = value
        metas.append(meta)
    return metas


def parse_subvolume_paths(output: str, root_path: str | Path) -> set[str]:
    """Return root-scoped absolute paths from ``btrfs subvolume list`` output."""

    paths: set[str] = set()
    for line in output.splitlines():
        _before, sep, raw_path = line.strip().partition(" path ")
        if not sep:
            continue
        abs_path = listed_path_to_absolute(root_path, raw_path, scoped_to_root=True)
        if abs_path:
            paths.add(abs_path)
    return paths


def _mark_readonly_from_list(index: BtrfsIndex, output: str, root_path: str | Path) -> None:
    """Mark indexed paths read-only using one ``btrfs subvolume list -r`` result."""

    readonly_paths = parse_subvolume_paths(output, root_path)
    if not readonly_paths:
        # A successful empty readonly list means indexed descendants are writable.
        for meta in index.by_path.values():
            if is_under(meta.path, root_path):
                meta.readonly = False
        return
    for path, meta in list(index.by_path.items()):
        if not is_under(path, root_path):
            continue
        meta.readonly = path in readonly_paths


def build_local_btrfs_index(
    root_path: str | Path,
    *,
    sudo: str,
    btrfs_command: str,
    include_root: bool = True,
    required: bool = False,
) -> BtrfsIndex:
    """Build a local Btrfs index with bulk list commands.

    One UUID/parent/received-UUID list command is used for descendants below the
    root, and one read-only list command marks which indexed subvolumes can be
    used directly as ``btrfs send`` sources. This avoids running
    ``btrfs subvolume show`` for every Timeshift/cache child.
    """

    root = normalize_path(root_path)
    index = BtrfsIndex(root=root, location="local")
    if not Path(root).exists():
        index.root_missing = True
        if required:
            index.errors.append(f"local index root is missing: {root}")
        return index

    ops = BtrfsOps(CommandEndpoint.local(), sudo, btrfs_command)
    result = ops.endpoint.run_argv(
        ops.argv(["subvolume", "list", "-u", "-q", "-R", "-o", root]),
        check=False, log_stderr=False, mirror_stderr=False,
    )
    if result.returncode != 0:
        if required:
            index.errors.append(result.stderr.strip() or result.stdout.strip() or f"return code {result.returncode}")
    else:
        for meta in parse_subvolume_list(result.stdout, root):
            index.add(meta)

    readonly_result = ops.endpoint.run_argv(
        ops.argv(["subvolume", "list", "-r", "-o", root]),
        check=False, log_stderr=False, mirror_stderr=False,
    )
    if readonly_result.returncode == 0:
        _mark_readonly_from_list(index, readonly_result.stdout, root)

    if include_root:
        root_meta = ops.meta(root, name=Path(root).name, required=False)
        index.add(root_meta)
    return index

def _remote_bulk_index_script(root: str, sudo: str, btrfs_command: str) -> str:
    """Return a POSIX shell script that bulk-lists source Btrfs metadata.

    The script is intentionally executed in one SSH session. It runs one
    UUID/parent/received-UUID list for descendants, one read-only list for the
    same root, and an optional root ``subvolume show``. That gives the app the
    metadata it normally needs without opening one SSH connection per snapshot.
    """

    root_q = shlex.quote(normalize_path(root))
    sudo_words = " ".join(shlex.quote(part) for part in sudo_prefix(sudo))
    btrfs_q = shlex.quote(btrfs_command)
    return f"""
root={root_q}
sudo_words={shlex.quote(sudo_words)}
btrfs_cmd={btrfs_q}

run_btrfs() {{
    if [ -n "$sudo_words" ]; then
        # shellcheck disable=SC2086
        $sudo_words "$btrfs_cmd" "$@"
    else
        "$btrfs_cmd" "$@"
    fi
}}

printf 'TSBTRFS_ROOT\t%s\n' "$root"
printf 'TSBTRFS_ROOT_SHOW_BEGIN\n'
run_btrfs subvolume show "$root" 2>&1
printf 'TSBTRFS_ROOT_SHOW_END\n'

printf 'TSBTRFS_LIST_BEGIN\t%s\n' "$root"
list_output=$(run_btrfs subvolume list -u -q -R -o "$root" 2>&1)
list_status=$?
printf 'TSBTRFS_LIST_STATUS\t%s\t%s\n' "$root" "$list_status"
printf '%s\n' "$list_output"
printf 'TSBTRFS_LIST_END\t%s\n' "$root"

printf 'TSBTRFS_READONLY_BEGIN\t%s\n' "$root"
readonly_output=$(run_btrfs subvolume list -r -o "$root" 2>&1)
readonly_status=$?
printf 'TSBTRFS_READONLY_STATUS\t%s\t%s\n' "$root" "$readonly_status"
printf '%s\n' "$readonly_output"
printf 'TSBTRFS_READONLY_END\t%s\n' "$root"
""".strip()

def build_source_btrfs_index(
    source: SourceRunner,
    root_path: str | Path | None,
    *,
    sudo: str,
    btrfs_command: str,
    include_root: bool = True,
    required: bool = False,
) -> BtrfsIndex:
    """Build a source Btrfs index in SSH or local mode."""

    if source.uses_ssh:
        assert source.ssh is not None
        return build_remote_btrfs_index(
            source.ssh,
            root_path,
            sudo=sudo,
            btrfs_command=btrfs_command,
            include_root=include_root,
            required=required,
        )
    if not root_path:
        return BtrfsIndex(root="", location="local")
    return build_local_btrfs_index(
        root_path,
        sudo=sudo,
        btrfs_command=btrfs_command,
        include_root=include_root,
        required=required,
    )


def build_remote_btrfs_index(
    ssh: SSHRunner,
    root_path: str | Path | None,
    *,
    sudo: str,
    btrfs_command: str,
    include_root: bool = True,
    required: bool = False,
) -> BtrfsIndex:
    """Build a remote source index using one SSH command.

    The remote command may run several ``btrfs`` probes on the source host, but
    all of them happen inside one SSH session. This avoids repeated encrypted-key
    authentication while still using only the configured restricted sudo+btrfs
    permissions.
    """

    if not root_path:
        return BtrfsIndex(root="", location="remote")
    root = normalize_path(root_path)
    script = _remote_bulk_index_script(root, sudo, btrfs_command)
    result = ssh.run("sh -c " + shlex.quote(script), check=False, log_stderr=False, mirror_stderr=False)
    return _parse_remote_btrfs_index_result(
        result.returncode,
        result.stdout,
        result.stderr,
        root=root,
        include_root=include_root,
        required=required,
    )


def _parse_remote_btrfs_index_result(
    returncode: int,
    stdout: str,
    stderr: str,
    *,
    root: str,
    include_root: bool,
    required: bool,
) -> BtrfsIndex:
    """Parse one remote bulk-index section into a :class:`BtrfsIndex`.

    The standalone one-root index and the combined source inventory use this
    same parser so UUID, parent UUID, received UUID, and read-only handling stay
    identical.
    """

    index = BtrfsIndex(root=root, location="remote")
    if returncode != 0:
        text = stderr.strip() or stdout.strip() or f"return code {returncode}"
        if "No such file or directory" in text or "can't access" in text or "cannot access" in text:
            index.root_missing = True
        if required:
            index.errors.append(text)
        return index

    root_show: list[str] = []
    in_root_show = False
    current_list_root: str | None = None
    current_list_lines: list[str] = []
    current_readonly_root: str | None = None
    current_readonly_lines: list[str] = []

    def flush_list() -> None:
        nonlocal current_list_root, current_list_lines
        if current_list_root is not None:
            for meta in parse_subvolume_list("\n".join(current_list_lines), current_list_root):
                index.add(meta)
        current_list_root = None
        current_list_lines = []

    def flush_readonly() -> None:
        nonlocal current_readonly_root, current_readonly_lines
        if current_readonly_root is not None:
            _mark_readonly_from_list(index, "\n".join(current_readonly_lines), current_readonly_root)
        current_readonly_root = None
        current_readonly_lines = []

    for line in stdout.splitlines():
        if line == "TSBTRFS_ROOT_SHOW_BEGIN":
            flush_list()
            flush_readonly()
            in_root_show = True
            continue
        if line == "TSBTRFS_ROOT_SHOW_END":
            in_root_show = False
            continue
        if in_root_show:
            root_show.append(line)
            continue
        if line.startswith("TSBTRFS_LIST_BEGIN\t"):
            flush_list()
            flush_readonly()
            current_list_root = normalize_path(line.split("\t", 1)[1])
            continue
        if line.startswith("TSBTRFS_LIST_STATUS\t"):
            parts = line.split("\t")
            if len(parts) >= 3 and normalize_path(parts[1]) == root and parts[2] != "0":
                index.root_missing = True
                if required:
                    index.errors.append(f"remote index root is missing or not listable: {root}")
            continue
        if line.startswith("TSBTRFS_LIST_END\t"):
            flush_list()
            continue
        if line.startswith("TSBTRFS_READONLY_BEGIN\t"):
            flush_list()
            flush_readonly()
            current_readonly_root = normalize_path(line.split("\t", 1)[1])
            continue
        if line.startswith("TSBTRFS_READONLY_STATUS\t"):
            # The read-only list is an optimization. Failure is not fatal; the
            # app can still fall back to a targeted subvolume show when needed.
            continue
        if line.startswith("TSBTRFS_READONLY_END\t"):
            flush_readonly()
            continue
        if current_list_root is not None:
            current_list_lines.append(line)
        elif current_readonly_root is not None:
            current_readonly_lines.append(line)
    flush_list()
    flush_readonly()

    if include_root and root_show:
        root_meta = parse_subvolume_show("\n".join(root_show), Path(root).name, root)
        if root_meta.uuid or root_meta.parent_uuid or root_meta.received_uuid or root_meta.readonly is not None:
            index.add(root_meta)
    return index


def _remote_source_inventory_script(
    snapshot_root: str,
    cache_root: str | None,
    *,
    sudo: str,
    btrfs_command: str,
    timeshift_command: str,
) -> str:
    """Return one remote script for Timeshift, info.json, and both Btrfs roots.

    Several source commands run inside the script, but SSH mode opens only one
    SSH session for the complete inventory generation. Snapshot control files
    are ordinary readable files, so the script reads them with ``cat`` and does
    not require any extra sudo permission beyond Timeshift and Btrfs.
    """

    timeshift_command_text = quote_join(sudo_prefix(sudo) + [timeshift_command, "--list"])
    snapshot_root_normalized = normalize_path(snapshot_root)
    snapshot_script = _remote_bulk_index_script(snapshot_root_normalized, sudo, btrfs_command)
    cache_block = ""
    if cache_root:
        cache_script = _remote_bulk_index_script(normalize_path(cache_root), sudo, btrfs_command)
        cache_block = (
            "\nprintf 'TSBTRFS_INDEX_SECTION_BEGIN\\tcache\\n'\n"
            + cache_script
            + "\nprintf 'TSBTRFS_INDEX_SECTION_END\\tcache\\n'\n"
        )

    prefix = """printf 'TSBTRFS_SOURCE_IDENTITY_BEGIN\n'
source_user_name=$(id -un 2>/dev/null || printf 'unknown')
source_user_uid=$(id -u 2>/dev/null || printf 'unknown')
printf 'TSBTRFS_SOURCE_USER_NAME\t%s\n' "$source_user_name"
printf 'TSBTRFS_SOURCE_USER_UID\t%s\n' "$source_user_uid"
printf 'TSBTRFS_SOURCE_IDENTITY_END\n'

printf 'TSBTRFS_TIMESHIFT_BEGIN\n'
timeshift_output=$(__TIMESHIFT_COMMAND__ 2>&1)
timeshift_status=$?
printf 'TSBTRFS_TIMESHIFT_STATUS\t%s\n' "$timeshift_status"
printf '%s\n' "$timeshift_output"
printf 'TSBTRFS_TIMESHIFT_END\n'

""".replace("__TIMESHIFT_COMMAND__", timeshift_command_text)

    info_block = """snapshot_info_root=__SNAPSHOT_ROOT__
if [ ! -e "$snapshot_info_root" ]; then
    printf 'TSBTRFS_INFO_ROOT_ERROR\t%s\n' 'snapshot_root does not exist or cannot be traversed by the source user'
elif [ ! -d "$snapshot_info_root" ]; then
    printf 'TSBTRFS_INFO_ROOT_ERROR\t%s\n' 'snapshot_root is not a directory'
elif [ ! -x "$snapshot_info_root" ]; then
    printf 'TSBTRFS_INFO_ROOT_ERROR\t%s\n' 'snapshot_root cannot be traversed by the source user'
elif [ ! -r "$snapshot_info_root" ]; then
    printf 'TSBTRFS_INFO_ROOT_ERROR\t%s\n' 'snapshot_root cannot be listed by the source user'
else
    for info_path in "$snapshot_info_root"/*/info.json; do
        [ -e "$info_path" ] || continue
        snapshot_dir=${info_path%/info.json}
        snapshot_name=${snapshot_dir##*/}
        printf 'TSBTRFS_INFO_JSON_BEGIN\t%s\n' "$snapshot_name"
        if [ -r "$info_path" ]; then
            cat "$info_path"
            info_status=$?
        else
            info_status=126
        fi
        printf '\nTSBTRFS_INFO_JSON_END\t%s\t%s\n' "$snapshot_name" "$info_status"
    done
fi

""".replace("__SNAPSHOT_ROOT__", shlex.quote(snapshot_root_normalized))

    return (
        prefix
        + info_block
        + "printf 'TSBTRFS_INDEX_SECTION_BEGIN\\tsnapshot\\n'\n"
        + snapshot_script
        + "\nprintf 'TSBTRFS_INDEX_SECTION_END\\tsnapshot\\n'\n"
        + cache_block
        + "exit 0"
    )


def _extract_snapshot_info_json_frames(output: str) -> tuple[str, dict[str, str], dict[str, str]]:
    """Remove and parse the ``cat`` payloads from combined SSH output.

    The remote script inserts one separator newline immediately before each end
    marker. The non-greedy parser removes that separator while preserving the
    control file's own final newline, when present.
    """

    pattern = re.compile(
        r"TSBTRFS_INFO_JSON_BEGIN\t(?P<name>[^\r\n]+)\n"
        r"(?P<content>.*?)\n"
        r"TSBTRFS_INFO_JSON_END\t(?P=name)\t(?P<status>\d+)(?:\r?\n|$)",
        re.DOTALL,
    )
    captured: dict[str, str] = {}
    errors: dict[str, str] = {}

    def replace(match: re.Match[str]) -> str:
        name = match.group("name")
        status = int(match.group("status"))
        if status == 0:
            captured[name] = match.group("content")
        elif status == 126:
            errors[name] = "info.json exists but is not readable by the source user"
        else:
            errors[name] = f"cat returned status {status}"
        return ""

    cleaned = pattern.sub(replace, output)
    if "TSBTRFS_INFO_JSON_BEGIN\t" in cleaned or "TSBTRFS_INFO_JSON_END\t" in cleaned:
        errors["<inventory>"] = "malformed info.json framing in combined source inventory output"
    return cleaned, captured, errors


def _split_remote_source_inventory_output(
    output: str,
) -> tuple[
    str,
    int | None,
    dict[str, str],
    dict[str, str],
    dict[str, str],
    str | None,
    int | None,
]:
    """Split combined output into identity, Timeshift, info.json, and Btrfs sections."""

    output, snapshot_info_json, snapshot_info_errors = _extract_snapshot_info_json_frames(output)
    timeshift_lines: list[str] = []
    timeshift_status: int | None = None
    source_user_name: str | None = None
    source_user_uid: int | None = None
    in_timeshift = False
    current_section: str | None = None
    section_lines: dict[str, list[str]] = {}

    for line in output.splitlines():
        if line.startswith("TSBTRFS_SOURCE_USER_NAME\t"):
            source_user_name = line.split("\t", 1)[1] or None
            continue
        if line.startswith("TSBTRFS_SOURCE_USER_UID\t"):
            raw_uid = line.split("\t", 1)[1]
            try:
                source_user_uid = int(raw_uid)
            except ValueError:
                source_user_uid = None
            continue
        if line.startswith("TSBTRFS_INFO_ROOT_ERROR\t"):
            snapshot_info_errors["<info-root>"] = line.split("\t", 1)[1]
            continue
        if line in {"TSBTRFS_SOURCE_IDENTITY_BEGIN", "TSBTRFS_SOURCE_IDENTITY_END"}:
            continue
        if line == "TSBTRFS_TIMESHIFT_BEGIN":
            in_timeshift = True
            continue
        if line.startswith("TSBTRFS_TIMESHIFT_STATUS\t"):
            try:
                timeshift_status = int(line.split("\t", 1)[1])
            except ValueError:
                timeshift_status = None
            continue
        if line == "TSBTRFS_TIMESHIFT_END":
            in_timeshift = False
            continue
        if line.startswith("TSBTRFS_INDEX_SECTION_BEGIN\t"):
            current_section = line.split("\t", 1)[1]
            section_lines.setdefault(current_section, [])
            continue
        if line.startswith("TSBTRFS_INDEX_SECTION_END\t"):
            current_section = None
            continue
        if in_timeshift:
            timeshift_lines.append(line)
        elif current_section is not None:
            section_lines[current_section].append(line)

    return (
        "\n".join(timeshift_lines),
        timeshift_status,
        {name: "\n".join(lines) for name, lines in section_lines.items()},
        snapshot_info_json,
        snapshot_info_errors,
        source_user_name,
        source_user_uid,
    )


def _current_process_identity() -> tuple[str, int]:
    """Return the effective local account name and UID used to read metadata."""

    uid = os.geteuid()
    try:
        name = pwd.getpwuid(uid).pw_name
    except KeyError:
        name = str(uid)
    return name, uid


def _read_local_snapshot_info_json(snapshot_root: str) -> tuple[dict[str, str], dict[str, str]]:
    """Read all local Timeshift control files without spawning commands."""

    captured: dict[str, str] = {}
    errors: dict[str, str] = {}
    root = Path(snapshot_root)
    if not root.is_dir():
        return captured, errors
    try:
        children = sorted(root.iterdir(), key=lambda child: child.name)
    except OSError as exc:
        errors["<inventory>"] = str(exc)
        return captured, errors
    timestamp_pattern = re.compile(r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}")
    for child in children:
        if not child.is_dir() or timestamp_pattern.fullmatch(child.name) is None:
            continue
        info_path = child / "info.json"
        if not info_path.exists():
            continue
        try:
            captured[child.name] = info_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors[child.name] = str(exc)
    return captured, errors


def _record_missing_info_json_errors(
    timeshift_output: str,
    captured: dict[str, str],
    errors: dict[str, str],
) -> None:
    """Record listed Timeshift dates that had no readable control file."""

    pattern = re.compile(r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}")
    root_reason = errors.get("<info-root>")
    for name in sorted(set(pattern.findall(timeshift_output))):
        if name not in captured and name not in errors:
            errors[name] = root_reason or "info.json was not found or was not readable"


def build_source_inventory(
    source: SourceRunner,
    *,
    snapshot_root: str,
    cache_root: str | None,
    sudo: str,
    btrfs_command: str,
    timeshift_command: str,
    required: bool = True,
) -> SourceInventory:
    """Build one coherent Timeshift/snapshot/cache source inventory.

    SSH mode uses one SSH command for all three views. Local mode uses the same
    parsers without caring about local process count because there is no SSH
    authentication or network round trip.
    """

    snapshot_root_normalized = normalize_path(snapshot_root)
    cache_root_normalized = normalize_path(cache_root) if cache_root else None

    if not source.uses_ssh:
        timeshift_result = source.run(
            quote_join(sudo_prefix(sudo) + [timeshift_command, "--list"]),
            check=required,
            log_stderr=required,
            mirror_stderr=required,
            mirror_stdout_on_failure=True,
        )
        snapshot_index = build_local_btrfs_index(
            snapshot_root_normalized,
            sudo=sudo,
            btrfs_command=btrfs_command,
            include_root=False,
            required=required,
        )
        cache_index = (
            build_local_btrfs_index(
                cache_root_normalized,
                sudo=sudo,
                btrfs_command=btrfs_command,
                include_root=True,
                required=required,
            )
            if cache_root_normalized
            else None
        )
        snapshot_info_json, snapshot_info_errors = _read_local_snapshot_info_json(snapshot_root_normalized)
        _record_missing_info_json_errors(timeshift_result.stdout, snapshot_info_json, snapshot_info_errors)
        source_user_name, source_user_uid = _current_process_identity()
        return SourceInventory(
            timeshift_result.stdout,
            snapshot_index,
            cache_index,
            snapshot_info_json,
            snapshot_info_errors,
            source_user_name,
            source_user_uid,
        )

    script = _remote_source_inventory_script(
        snapshot_root_normalized,
        cache_root_normalized,
        sudo=sudo,
        btrfs_command=btrfs_command,
        timeshift_command=timeshift_command,
    )
    result = source.run(
        "sh -c " + shlex.quote(script),
        check=False,
        log_stderr=False,
        mirror_stderr=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"return code {result.returncode}"
        raise RuntimeError(f"Source inventory SSH command failed: {detail}")

    (
        timeshift_output,
        timeshift_status,
        sections,
        snapshot_info_json,
        snapshot_info_errors,
        source_user_name,
        source_user_uid,
    ) = _split_remote_source_inventory_output(result.stdout)
    if timeshift_status != 0 and required:
        detail = timeshift_output.strip() or f"return code {timeshift_status}"
        raise RuntimeError(f"Source Timeshift --list failed while building inventory: {detail}")

    snapshot_output = sections.get("snapshot", "")
    snapshot_index = _parse_remote_btrfs_index_result(
        0 if snapshot_output else 1,
        snapshot_output,
        "missing snapshot inventory section" if not snapshot_output else "",
        root=snapshot_root_normalized,
        include_root=False,
        required=required,
    )
    cache_index = None
    if cache_root_normalized:
        cache_output = sections.get("cache", "")
        cache_index = _parse_remote_btrfs_index_result(
            0 if cache_output else 1,
            cache_output,
            "missing cache inventory section" if not cache_output else "",
            root=cache_root_normalized,
            include_root=True,
            required=required,
        )
    _record_missing_info_json_errors(timeshift_output, snapshot_info_json, snapshot_info_errors)
    if "<inventory>" in snapshot_info_errors and required:
        raise RuntimeError(snapshot_info_errors["<inventory>"])
    return SourceInventory(
        timeshift_output,
        snapshot_index,
        cache_index,
        snapshot_info_json,
        snapshot_info_errors,
        source_user_name,
        source_user_uid,
    )


def describe_source_inventory_changes(before: SourceInventory, after: SourceInventory) -> list[str]:
    """Return concise human-readable differences between two inventories."""

    changes: list[str] = []
    before_names = set(before.snapshot_names)
    after_names = set(after.snapshot_names)
    added_names = sorted(after_names - before_names)
    removed_names = sorted(before_names - after_names)
    if added_names:
        changes.append("Timeshift snapshot(s) added: " + ", ".join(added_names))
    if removed_names:
        changes.append("Timeshift snapshot(s) removed: " + ", ".join(removed_names))

    def compare_index(label: str, old: BtrfsIndex | None, new: BtrfsIndex | None) -> None:
        old_paths = set(old.by_path) if old is not None else set()
        new_paths = set(new.by_path) if new is not None else set()
        added = sorted(new_paths - old_paths)
        removed = sorted(old_paths - new_paths)
        if added:
            changes.append(f"{label} subvolume path(s) added: " + ", ".join(added))
        if removed:
            changes.append(f"{label} subvolume path(s) removed: " + ", ".join(removed))
        for path in sorted(old_paths & new_paths):
            old_meta = old.by_path[path]
            new_meta = new.by_path[path]
            old_identity = (old_meta.uuid, old_meta.parent_uuid, old_meta.received_uuid, old_meta.readonly)
            new_identity = (new_meta.uuid, new_meta.parent_uuid, new_meta.received_uuid, new_meta.readonly)
            if old_identity != new_identity:
                changes.append(
                    f"{label} metadata changed: {path} "
                    f"{old_identity!r} -> {new_identity!r}"
                )
        if old is not None and new is not None and old.root_missing != new.root_missing:
            changes.append(f"{label} root_missing changed: {old.root_missing} -> {new.root_missing}")

    compare_index("snapshot_root", before.snapshot_index, after.snapshot_index)
    compare_index("cache_root", before.cache_index, after.cache_index)

    old_info_names = set(before.snapshot_info_json)
    new_info_names = set(after.snapshot_info_json)
    added_info = sorted(new_info_names - old_info_names)
    removed_info = sorted(old_info_names - new_info_names)
    if added_info:
        changes.append("Timeshift info.json added: " + ", ".join(added_info))
    if removed_info:
        changes.append("Timeshift info.json removed: " + ", ".join(removed_info))
    for name in sorted(old_info_names & new_info_names):
        if before.snapshot_info_json[name] != after.snapshot_info_json[name]:
            changes.append(f"Timeshift info.json changed: {name}")
    return changes


def refresh_path(
    index: BtrfsIndex | None,
    ops: BtrfsOps,
    path: str | Path,
    *,
    name: str | None = None,
) -> SubvolumeMeta | None:
    """Refresh one exact path through the shared Btrfs operation layer."""

    meta = ops.meta(path, name=name or Path(path).name, required=False)
    if index is not None:
        if meta:
            index.add(meta)
        else:
            index.discard(str(path))
    return meta
