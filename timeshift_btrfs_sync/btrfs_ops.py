"""Reusable Btrfs operations independent of workflow order.

This module is the single command layer for probing, creating, snapshotting,
deleting, sending, and receiving Btrfs subvolumes.  Workflows compose these
operations; they do not rebuild local/SSH variants of the same command.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import re
import shlex

from .commands import Completed, sudo_prefix
from .endpoint import CommandEndpoint
from .models import SubvolumeMeta

UUID_KEYS = {"UUID": "uuid", "Parent UUID": "parent_uuid", "Received UUID": "received_uuid"}


@dataclass(slots=True, frozen=True)
class _ListedSubvolume:
    """One numeric containment record from ``btrfs subvolume list -a -p``."""

    subvolume_id: int
    parent_id: int | None
    path: str


def _parse_listed_subvolumes(output: str) -> list[_ListedSubvolume]:
    """Parse numeric ID, containing-parent ID, and raw path fields."""

    records: list[_ListedSubvolume] = []
    for line in output.splitlines():
        before, separator, raw_path = line.strip().partition(" path ")
        if not separator:
            continue
        id_match = re.search(r"(?:^|\s)ID\s+(\d+)(?:\s|$)", before)
        parent_match = re.search(r"(?:^|\s)parent\s+(\d+)(?:\s|$)", before)
        if parent_match is None:
            parent_match = re.search(r"(?:^|\s)top level\s+(\d+)(?:\s|$)", before)
        if id_match is None:
            continue
        records.append(
            _ListedSubvolume(
                subvolume_id=int(id_match.group(1)),
                parent_id=int(parent_match.group(1)) if parent_match else None,
                path=raw_path.strip().rstrip("/"),
            )
        )
    return records


def _descendant_list_paths(output: str, root_id: int) -> list[str]:
    """Return only numeric descendants of ``root_id`` from one full list."""

    records = _parse_listed_subvolumes(output)
    descendant_ids = {root_id}
    changed = True
    while changed:
        changed = False
        for record in records:
            if record.subvolume_id in descendant_ids:
                continue
            if record.parent_id in descendant_ids:
                descendant_ids.add(record.subvolume_id)
                changed = True
    return [record.path for record in records if record.subvolume_id in descendant_ids and record.subvolume_id != root_id]


def clean_uuid(value: str) -> str | None:
    value = value.strip()
    return None if not value or value == "-" else value


def parse_subvolume_show(output: str, name: str, path: str) -> SubvolumeMeta:
    """Parse UUID and read-only fields from ``btrfs subvolume show``."""

    meta = SubvolumeMeta(name=name, path=path)
    for line in output.splitlines():
        if ":" not in line:
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        attr = UUID_KEYS.get(key)
        if attr:
            setattr(meta, attr, clean_uuid(value))
        elif key == "Subvolume ID":
            try:
                meta.subvolume_id = int(value)
            except ValueError:
                pass
        elif key.lower() == "flags":
            lower = value.lower()
            if "readonly" in lower or "read-only" in lower:
                meta.readonly = True
            elif lower in {"", "-", "none"}:
                meta.readonly = False
    return meta


@dataclass(slots=True)
class BtrfsOps:
    """Btrfs command facade for one local or source endpoint."""

    endpoint: CommandEndpoint
    sudo: str = ""
    command_name: str = "btrfs"

    @property
    def prefix(self) -> list[str]:
        return sudo_prefix(self.sudo) + [self.command_name]

    def argv(self, args: Iterable[str]) -> list[str]:
        return self.prefix + [str(arg) for arg in args]

    def run(
        self,
        args: Iterable[str],
        *,
        check: bool = True,
        log_stderr: bool = True,
        mirror_stderr: bool = True,
    ) -> Completed:
        return self.endpoint.run_argv(
            self.argv(args),
            check=check,
            log_stderr=log_stderr,
            mirror_stderr=mirror_stderr,
        )

    def meta(self, path: str | Path, *, name: str | None = None, required: bool = True) -> SubvolumeMeta | None:
        """Return exact-path subvolume metadata or ``None`` for an optional miss."""

        path_text = str(path)
        result = self.run(
            ["subvolume", "show", path_text],
            check=False,
            log_stderr=required,
            mirror_stderr=required,
        )
        if result.returncode == 0:
            return parse_subvolume_show(result.stdout, name or Path(path_text).name, path_text)
        if not required:
            return None
        detail = result.stderr.strip() or result.stdout.strip() or f"return code {result.returncode}"
        raise RuntimeError(
            f"Cannot read {self.endpoint.location} Btrfs subvolume metadata for {path_text}: {detail}"
        )

    def list_children(self, path: str | Path, *, root_id: int) -> list[str] | None:
        """Return all descendants selected from one Btrfs containment graph.

        ``subvolume list -a -p`` supplies the filesystem-wide parent graph.
        Numeric parent IDs select only descendants of the exact configured root,
        preventing similarly named subvolumes elsewhere from entering a delete
        plan.
        """

        result = self.run(
            ["subvolume", "list", "-a", "-p", str(path)],
            check=False,
            log_stderr=False,
            mirror_stderr=False,
        )
        if result.returncode != 0:
            return None
        return _descendant_list_paths(result.stdout, root_id)

    def create(self, path: str | Path, *, check: bool = True) -> Completed:
        return self.run(["subvolume", "create", str(path)], check=check)

    def delete(
        self,
        path: str | Path,
        *,
        check: bool = True,
        log_stderr: bool = True,
        mirror_stderr: bool = True,
    ) -> Completed:
        return self.run(
            ["subvolume", "delete", str(path)],
            check=check,
            log_stderr=log_stderr,
            mirror_stderr=mirror_stderr,
        )

    def send_command(
        self,
        current_path: str,
        *,
        parent_path: str | None = None,
        compressed_data: bool = False,
        proto: int | None = None,
        verbose: bool = False,
    ) -> list[str]:
        args = ["send"]
        if verbose:
            args.append("-v")
        if proto is not None:
            args += ["--proto", str(proto)]
        if compressed_data:
            args.append("--compressed-data")
        if parent_path:
            args += ["-p", parent_path]
        args.append(current_path)
        return self.endpoint.command(self.argv(args))

    def receive_command(self, destination_dir: str | Path, *, verbose: bool = False) -> list[str]:
        args = ["receive"]
        if verbose:
            args.append("-v")
        args.append(str(destination_dir))
        return self.endpoint.command(self.argv(args))

    def batch_delete(self, paths: list[str]) -> tuple[list[str], list[str]]:
        """Delete exact paths in one endpoint command and validate confirmations.

        The returned first list contains unique expected paths confirmed by the
        remote/local shell.  Duplicate, malformed, or unexpected output is
        returned as errors.  Post-deletion root verification belongs to the
        shared tree-deletion layer.
        """

        if not paths:
            return [], []
        expected = set(paths)
        path_lines = "\n".join(paths)
        prefix = " ".join(shlex.quote(part) for part in self.prefix)
        script = f"""
btrfs_words={shlex.quote(prefix)}
run_btrfs() {{
    # shellcheck disable=SC2086
    $btrfs_words "$@"
}}
while IFS= read -r subvol; do
    [ -n "$subvol" ] || continue
    output=$(run_btrfs subvolume delete "$subvol" 2>&1)
    status=$?
    if [ "$status" -eq 0 ]; then
        printf 'TSBTRFS_DELETED\\t%s\\n' "$subvol"
    else
        safe_output=$(printf '%s' "$output" | tr '\\n' ' ')
        printf 'TSBTRFS_DELETE_ERROR\\t%s\\t%s\\n' "$subvol" "$safe_output"
    fi
done <<'TSBTRFS_PATHS'
{path_lines}
TSBTRFS_PATHS
""".strip()
        result = self.endpoint.run_shell(
            script,
            check=False,
            log_stderr=False,
            mirror_stderr=False,
        )
        confirmed: list[str] = []
        seen: set[str] = set()
        errors: list[str] = []
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or f"return code {result.returncode}"
            return confirmed, [detail]
        for line in result.stdout.splitlines():
            if line.startswith("TSBTRFS_DELETED\t"):
                path = line.split("\t", 1)[1]
                if path not in expected:
                    errors.append(f"unexpected deletion confirmation for subvolume {path}")
                elif path in seen:
                    errors.append(f"duplicate deletion confirmation for subvolume {path}")
                else:
                    confirmed.append(path)
                    seen.add(path)
            elif line.startswith("TSBTRFS_DELETE_ERROR\t"):
                parts = line.split("\t", 2)
                if len(parts) == 3:
                    errors.append(f"failed deleting subvolume {parts[1]}: {parts[2]}")
                else:
                    errors.append(f"malformed deletion error line: {line}")
        return confirmed, errors
