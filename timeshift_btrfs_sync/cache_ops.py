"""Single source send-cache operation used by sync and recovery."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
import shlex

from .btrfs_ops import BtrfsOps, parse_subvolume_show
from .models import SubvolumeMeta

if TYPE_CHECKING:
    from .inventory import BtrfsIndex


def _safe_name(value: str, label: str) -> str:
    if not value or "/" in value or value in {".", ".."}:
        raise RuntimeError(f"Unsafe {label} for cache path: {value!r}")
    return value


def cache_parent_path(cache_root: str, snapshot_name: str) -> str:
    return str(Path(cache_root) / _safe_name(snapshot_name, "snapshot name"))


def cache_child_path(cache_root: str, snapshot_name: str, subvolume_name: str) -> str:
    return str(Path(cache_parent_path(cache_root, snapshot_name)) / _safe_name(subvolume_name, "subvolume name"))


def validate_cache_snapshot(meta: SubvolumeMeta | None, *, cache_path: str, original: SubvolumeMeta) -> SubvolumeMeta | None:
    """Prove an exact cache child is a safe read-only snapshot of ``original``."""

    if meta is None:
        return None
    if meta.readonly is not True:
        raise RuntimeError(
            "Existing source cache path is a Btrfs subvolume but is not read-only:\n"
            f"  {cache_path}\nRefusing to use or overwrite it. Inspect the send-cache path manually."
        )
    if original.uuid and meta.parent_uuid and meta.parent_uuid != original.uuid:
        raise RuntimeError(
            "Existing source cache snapshot does not belong to the requested Timeshift snapshot:\n"
            f"  original: {original.path}\n  original UUID: {original.uuid}\n"
            f"  cache:    {cache_path}\n  cache Parent UUID: {meta.parent_uuid}\n"
            "Refusing to use it as a send source."
        )
    return meta


class CacheManager:
    """Ensure exact reusable send snapshots without nested cache creation."""

    def __init__(self, ops: BtrfsOps, *, cache_root: str | None, create_enabled: bool):
        self.ops = ops
        self.cache_root = cache_root
        self.create_enabled = create_enabled

    def _ensure_subvolume(self, path: str, index: BtrfsIndex | None) -> SubvolumeMeta:
        indexed = index.meta(path) if index else None
        if indexed:
            return indexed
        existing = self.ops.meta(path, required=False)
        if existing:
            if index:
                index.add(existing)
            return existing
        result = self.ops.create(path, check=False)
        if result.returncode != 0:
            if "target path already exists" not in result.stderr.lower():
                detail = result.stderr.strip() or result.stdout.strip() or f"return code {result.returncode}"
                raise RuntimeError(f"Failed to create source cache Btrfs subvolume:\n  {path}\n{detail}")
            existing = self.ops.meta(path, required=False)
            if not existing:
                raise RuntimeError(
                    "Source cache path already exists but is not a Btrfs subvolume:\n"
                    f"  {path}\nInspect or remove the ordinary path manually."
                )
        else:
            existing = self.ops.meta(path, required=True)
        assert existing is not None
        if index:
            index.add(existing)
        return existing

    def _probe_create_verify(
        self,
        *,
        original: SubvolumeMeta,
        cache_path: str,
        subvolume_name: str,
    ) -> SubvolumeMeta:
        """Probe, create if absent, and verify exact cache path in one command."""

        show = self.ops.endpoint.shell_command(self.ops.argv(["subvolume", "show", cache_path]))
        create = self.ops.endpoint.shell_command(
            self.ops.argv(["subvolume", "snapshot", "-r", original.path, cache_path])
        )
        cache_q = shlex.quote(cache_path)
        script = f"""
existing_output=$({show} 2>&1)
existing_status=$?
printf 'TSBTRFS_CACHE_EXISTING_STATUS\\t%s\\n' "$existing_status"
printf 'TSBTRFS_CACHE_EXISTING_OUTPUT_BEGIN\\n%s\\nTSBTRFS_CACHE_EXISTING_OUTPUT_END\\n' "$existing_output"
if [ "$existing_status" -eq 0 ]; then exit 0; fi
if [ -e {cache_q} ]; then printf 'TSBTRFS_CACHE_PATH_EXISTS\\t1\\n'; exit 0; fi
printf 'TSBTRFS_CACHE_PATH_EXISTS\\t0\\n'
create_output=$({create} 2>&1)
create_status=$?
printf 'TSBTRFS_CACHE_CREATE_STATUS\\t%s\\n' "$create_status"
printf 'TSBTRFS_CACHE_CREATE_OUTPUT_BEGIN\\n%s\\nTSBTRFS_CACHE_CREATE_OUTPUT_END\\n' "$create_output"
if [ "$create_status" -eq 0 ]; then
  show_output=$({show} 2>&1); show_status=$?
  printf 'TSBTRFS_CACHE_SHOW_STATUS\\t%s\\n' "$show_status"
  printf 'TSBTRFS_CACHE_SHOW_OUTPUT_BEGIN\\n%s\\nTSBTRFS_CACHE_SHOW_OUTPUT_END\\n' "$show_output"
else
  race_output=$({show} 2>&1); race_status=$?
  printf 'TSBTRFS_CACHE_RACE_SHOW_STATUS\\t%s\\n' "$race_status"
  printf 'TSBTRFS_CACHE_RACE_SHOW_OUTPUT_BEGIN\\n%s\\nTSBTRFS_CACHE_RACE_SHOW_OUTPUT_END\\n' "$race_output"
fi
exit 0
""".strip()
        result = self.ops.endpoint.run_shell(script, check=False, log_stderr=False, mirror_stderr=False)
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or f"return code {result.returncode}"
            raise RuntimeError("Failed to probe/create source cache snapshot.\n" + detail)

        statuses: dict[str, int | None] = {"existing": None, "create": None, "show": None, "race": None}
        outputs: dict[str, list[str]] = {key: [] for key in statuses}
        section: str | None = None
        path_exists = False
        status_map = {
            "TSBTRFS_CACHE_EXISTING_STATUS\t": "existing",
            "TSBTRFS_CACHE_CREATE_STATUS\t": "create",
            "TSBTRFS_CACHE_SHOW_STATUS\t": "show",
            "TSBTRFS_CACHE_RACE_SHOW_STATUS\t": "race",
        }
        begin_map = {
            "TSBTRFS_CACHE_EXISTING_OUTPUT_BEGIN": "existing",
            "TSBTRFS_CACHE_CREATE_OUTPUT_BEGIN": "create",
            "TSBTRFS_CACHE_SHOW_OUTPUT_BEGIN": "show",
            "TSBTRFS_CACHE_RACE_SHOW_OUTPUT_BEGIN": "race",
        }
        end_markers = {marker.replace("BEGIN", "END") for marker in begin_map}
        for line in result.stdout.splitlines():
            matched = False
            for marker, key in status_map.items():
                if line.startswith(marker):
                    try:
                        statuses[key] = int(line.split("\t", 1)[1])
                    except ValueError:
                        statuses[key] = None
                    matched = True
                    break
            if matched:
                continue
            if line.startswith("TSBTRFS_CACHE_PATH_EXISTS\t"):
                path_exists = line.endswith("\t1")
            elif line in begin_map:
                section = begin_map[line]
            elif line in end_markers:
                section = None
            elif section:
                outputs[section].append(line)

        def meta(section_name: str) -> SubvolumeMeta:
            parsed = parse_subvolume_show("\n".join(outputs[section_name]), subvolume_name, cache_path)
            validated = validate_cache_snapshot(parsed, cache_path=cache_path, original=original)
            assert validated is not None
            return validated

        if statuses["existing"] == 0:
            return meta("existing")
        if path_exists:
            detail = "\n".join(outputs["existing"]).strip()
            raise RuntimeError(
                "Exact source cache target already exists but is not a reusable read-only Btrfs snapshot. "
                "Refusing snapshot creation because Btrfs could create a nested subvolume:\n"
                f"  {cache_path}" + (f"\n{detail}" if detail else "")
            )
        if statuses["create"] == 0:
            if statuses["show"] != 0:
                raise RuntimeError(
                    "Created read-only source cache snapshot, but metadata verification failed:\n"
                    f"  {cache_path}\n" + ("\n".join(outputs["show"]).strip() or f"return code {statuses['show']}")
                )
            return meta("show")
        if statuses["race"] == 0:
            return meta("race")
        detail = "\n".join(outputs["create"]).strip() or f"return code {statuses['create']}"
        raise RuntimeError("Failed to create read-only source cache snapshot.\n" + detail)

    def ensure_send_snapshot(
        self,
        *,
        original_path: str,
        snapshot_name: str,
        subvolume_name: str,
        cache_index: BtrfsIndex | None = None,
        original_index: BtrfsIndex | None = None,
    ) -> SubvolumeMeta:
        """Return original read-only source or create/reuse one exact cache child."""

        original = original_index.meta(original_path) if original_index else None
        if original is None:
            original = self.ops.meta(original_path, name=subvolume_name, required=False)
        if original is None:
            raise RuntimeError(f"Source path is not a Btrfs subvolume or cannot be read: {original_path}")
        if original.readonly is True:
            return original
        if not self.create_enabled:
            raise RuntimeError(
                f"Source subvolume is not confirmed read-only and cache creation is disabled: {original_path}"
            )
        if not self.cache_root:
            raise RuntimeError("Source subvolume is not confirmed read-only and source.cache_root is not configured")

        parent = cache_parent_path(self.cache_root, snapshot_name)
        child = cache_child_path(self.cache_root, snapshot_name, subvolume_name)
        indexed = validate_cache_snapshot(
            cache_index.meta(child) if cache_index else None,
            cache_path=child,
            original=original,
        )
        if indexed:
            return indexed

        self._ensure_subvolume(self.cache_root, cache_index)
        self._ensure_subvolume(parent, cache_index)
        result = self._probe_create_verify(original=original, cache_path=child, subvolume_name=subvolume_name)
        if cache_index:
            cache_index.add(result)
        return result
