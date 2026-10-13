"""Single Btrfs tree discovery, deletion, and post-verification engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
import shlex

from .btrfs_ops import BtrfsOps, _parse_listed_subvolumes
from .models import SubvolumeMeta
from .paths import is_same_or_under, listed_path_to_absolute, sort_deepest_first


@dataclass(slots=True)
class TreeDeleteResult:
    root: str
    endpoint: str
    existed: bool = False
    planned: list[str] = field(default_factory=list)
    confirmed: list[str] = field(default_factory=list)
    remaining: list[str] = field(default_factory=list)
    verified_root_absent: bool = False
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return not self.errors and self.verified_root_absent


@dataclass(slots=True)
class NativeCacheDeletionProof:
    """Exact native identities below a repository root anchored to state/cache/receiver pairs.

    The historical cache field/API also carries a proven destination root.
    """

    cache_root: SubvolumeMeta
    subvolumes: dict[str, SubvolumeMeta]


def _native_cache_view(ops: BtrfsOps, proof: NativeCacheDeletionProof) -> tuple[set[int], str]:
    """Check the surviving repository identity and read live IDs without ordinary directory access."""

    anchor = proof.cache_root
    current = ops.meta(anchor.path, required=False)
    if (not current or not anchor.uuid or current.uuid != anchor.uuid or current.subvolume_id != anchor.subvolume_id
            or current.readonly != anchor.readonly or current.parent_uuid != anchor.parent_uuid
            or current.received_uuid != anchor.received_uuid):
        return set(), "native repository root identity changed or became unreadable"
    result = ops.run(["subvolume", "list", "-a", "-p", anchor.path], check=False, log_stderr=False, mirror_stderr=False)
    records = _parse_listed_subvolumes(result.stdout)
    ids = {record.subvolume_id for record in records}
    if (result.returncode or anchor.subvolume_id not in ids
            or len(records) != len([line for line in result.stdout.splitlines() if line.strip()])
            or len(ids) != len(records)):
        return set(), "complete native repository filesystem ID view unavailable"
    descendants = {anchor.subvolume_id}
    while True:
        expanded = descendants | {record.subvolume_id for record in records if record.parent_id in descendants}
        if expanded == descendants:
            break
        descendants = expanded
    if any(meta.subvolume_id in ids and meta.subvolume_id not in descendants for meta in proof.subvolumes.values()):
        return set(), "native repository subtree moved outside the anchored root"
    date_meta = min(proof.subvolumes.values(), key=lambda meta: len(Path(meta.path).parts))
    date_ids = {date_meta.subvolume_id}
    while True:
        expanded = date_ids | {record.subvolume_id for record in records if record.parent_id in date_ids}
        if expanded == date_ids:
            break
        date_ids = expanded
    expected_ids = {meta.subvolume_id for meta in proof.subvolumes.values()}
    if (date_ids & ids) - expected_ids or any(meta.subvolume_id in ids and meta.subvolume_id not in date_ids for meta in proof.subvolumes.values()):
        return set(), "native dated repository subtree changed after proof"
    return ids, ""



def _path_exists(ops: BtrfsOps, path: str) -> tuple[bool | None, str]:
    script = f"test -e {shlex.quote(path)}"
    result = ops.endpoint.run_shell(script, check=False, log_stderr=False, mirror_stderr=False)
    if result.returncode == 0:
        return True, ""
    if result.returncode == 1:
        return False, ""
    detail = result.stderr.strip() or result.stdout.strip() or f"return code {result.returncode}"
    return None, detail


def discover_subvolume_tree(ops: BtrfsOps, root: str, *, include_root: bool = True) -> tuple[list[str], list[str]]:
    """Discover a complete nested Btrfs tree in one endpoint list command.

    The Btrfs facade requests the filesystem-wide ``-a -p`` view and follows
    numeric containing-parent IDs from the exact root subvolume ID. Every
    selected raw path is then resolved through the central mount-aware mapper.
    This includes payload grandchildren such
    as ``<date>/@`` and ``<date>/@home`` before parent deletion is planned.
    """

    root_meta = ops.meta(root, required=False)
    if root_meta is None:
        return [], []
    discovered: set[str] = {root} if include_root else set()
    listed = ops.list_children(root, root_id=root_meta.subvolume_id)
    if listed is None:
        return sort_deepest_first(list(discovered)), [f"could not list Btrfs children below {root}"]
    for raw in listed:
        absolute = listed_path_to_absolute(root, raw)
        if absolute != root and is_same_or_under(absolute, root):
            discovered.add(absolute)
    return sort_deepest_first(list(discovered)), []




def list_direct_entries(ops: BtrfsOps, root: str) -> tuple[list[str], str]:
    """List exact direct children with shell built-ins on either endpoint."""

    root_q = shlex.quote(root)
    script = f"""
for entry in {root_q}/* {root_q}/.[!.]* {root_q}/..?*; do
    [ -e "$entry" ] || continue
    printf '%s\n' "$entry"
done
""".strip()
    result = ops.endpoint.run_shell(script, check=False, log_stderr=False, mirror_stderr=False)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"return code {result.returncode}"
        return [], detail
    return [line for line in result.stdout.splitlines() if line], ""

def _validate_confirmations(result: TreeDeleteResult) -> None:
    planned = list(dict.fromkeys(result.planned))
    confirmed = list(dict.fromkeys(result.confirmed))
    missing = [path for path in planned if path not in set(confirmed)]
    unexpected = [path for path in confirmed if path not in set(planned)]
    if not confirmed and planned:
        result.errors.append(f"no subvolume deletions were confirmed; planned {len(planned)}, confirmed 0")
    elif missing or unexpected:
        result.errors.append(
            f"not every planned subvolume deletion was confirmed; planned {len(planned)}, confirmed {len(confirmed)}"
        )
    if missing:
        result.errors.append("unconfirmed planned subvolume deletion(s): " + ", ".join(missing))
    if unexpected:
        result.errors.append("unexpected confirmed subvolume deletion(s): " + ", ".join(unexpected))


def _verify_absent(result: TreeDeleteResult, ops: BtrfsOps) -> None:
    exists, error = _path_exists(ops, result.root)
    root_meta = ops.meta(result.root, required=False)
    if exists is None:
        result.errors.append(f"final configured-root existence check failed: {error}")
        return
    if not exists and root_meta is None:
        result.verified_root_absent = True
        return
    result.errors.append(f"configured root still exists after deletion: {result.root}")
    remaining, errors = discover_subvolume_tree(ops, result.root, include_root=True)
    result.remaining = remaining
    result.errors.extend(errors)
    if remaining:
        result.errors.append(f"remaining Btrfs subvolumes: {len(remaining)}")


def delete_subvolume_tree(
    ops: BtrfsOps,
    root: str | Path,
    *,
    protected_roots: Iterable[str | Path] = (),
    dry_run: bool = False,
    allow_empty_ordinary_root: bool = False,
    allowed_regular_names: Iterable[str] = (),
    expected_subvolume_paths: Iterable[str | Path] | None = None,
    refuse_unknown_entries: bool = False,
    native_cache_proof: NativeCacheDeletionProof | None = None,
) -> TreeDeleteResult:
    """Delete one managed tree deepest-first and prove the root is absent.

    This is the only recursive managed-tree deletion operation.  It refuses
    protected roots and ordinary non-empty directories; it never uses recursive
    ordinary deletion.
    """

    root_text = str(root)
    result = TreeDeleteResult(root=root_text, endpoint=ops.endpoint.label)
    for protected in protected_roots:
        if is_same_or_under(root_text, str(protected)):
            result.errors.append(
                f"refusing to delete protected Btrfs path {root_text}; protected root: {protected}"
            )
            return result

    if native_cache_proof is not None:
        anchor = native_cache_proof.cache_root
        if root_text == anchor.path or not is_same_or_under(root_text, anchor.path):
            result.errors.append("native deletion must be strictly below the verified repository root")
            return result
        if root_text not in native_cache_proof.subvolumes:
            result.errors.append("native deletion proof does not identify the date container")
            return result
        exists, existence_error = True, ""
    else:
        exists, existence_error = _path_exists(ops, root_text)
    meta = ops.meta(root_text, required=False)
    if exists is None:
        result.errors.append(f"could not check path existence: {existence_error}")
        return result
    result.existed = bool(exists or meta)
    if not result.existed:
        if not dry_run:
                    result.verified_root_absent = True
        return result

    if meta is None:
        if native_cache_proof is not None:
            result.errors.append("native date container identity became unavailable")
            return result
        if not allow_empty_ordinary_root:
            result.errors.append(
                "configured root is an ordinary path, not a Btrfs subvolume; manual inspection is required: "
                + root_text
            )
            return result
        entries, entry_error = list_direct_entries(ops, root_text)
        if entry_error:
            result.errors.append(f"could not inspect ordinary configured root: {entry_error}")
            return result
        if entries:
            result.errors.append(
                "configured root is an ordinary non-empty directory. Recursive ordinary deletion is disabled; "
                "inspect and remove it manually: " + root_text
            )
            return result
        script = f"rmdir -- {shlex.quote(root_text)}"
        if dry_run:
            return result
        removed = ops.endpoint.run_shell(script, check=False, log_stderr=False, mirror_stderr=False)
        if removed.returncode != 0:
            detail = removed.stderr.strip() or removed.stdout.strip() or f"return code {removed.returncode}"
            result.errors.append(f"failed removing empty ordinary root {root_text}: {detail}")
        _verify_absent(result, ops)
        return result

    planned, errors = discover_subvolume_tree(ops, root_text, include_root=True)
    result.planned = planned
    result.errors.extend(errors)
    if native_cache_proof is not None:
        proof = native_cache_proof
        if set(planned) != set(proof.subvolumes):
            result.errors.append("native repository subtree differs from the verified deletion identities")
        ids, view_error = _native_cache_view(ops, proof)
        if view_error:
            result.errors.append(view_error)
        for path in planned:
            expected = proof.subvolumes.get(path)
            live = ops.meta(path, required=False)
            if (not expected or not live or not expected.uuid or live.uuid != expected.uuid
                    or not expected.subvolume_id or live.subvolume_id != expected.subvolume_id
                    or expected.subvolume_id not in ids or live.readonly != expected.readonly
                    or live.parent_uuid != expected.parent_uuid or live.received_uuid != expected.received_uuid):
                result.errors.append(f"native repository identity not confirmed: {path}")
        if dry_run or result.errors:
            return result
        for path in planned:
            expected = proof.subvolumes[path]
            live = ops.meta(path, required=False)
            _ids, error = _native_cache_view(ops, proof)
            if (error or expected.subvolume_id not in _ids or not live or live.uuid != expected.uuid
                    or live.subvolume_id != expected.subvolume_id or live.readonly != expected.readonly
                    or live.parent_uuid != expected.parent_uuid or live.received_uuid != expected.received_uuid):
                result.errors.append(error or f"native repository identity changed before deletion: {path}")
                break
            # Delete by the proven numeric ID on the anchored filesystem. This
            # avoids ordinary path traversal and path/symlink redirection.
            removed = ops.run(["subvolume", "delete", "--commit-after", "--subvolid", str(expected.subvolume_id), proof.cache_root.path],
                              check=False, log_stderr=False, mirror_stderr=False)
            if removed.returncode:
                result.errors.append(f"native ID deletion failed for {path}: {removed.stderr.strip() or removed.stdout.strip()}")
                break
            result.confirmed.append(path)
        _validate_confirmations(result)
        ids, error = _native_cache_view(ops, proof)
        if error:
            result.errors.append(error)
        else:
            result.remaining = [path for path, expected in proof.subvolumes.items() if expected.subvolume_id in ids]
            if result.remaining:
                result.errors.append("native repository IDs remain after deletion: " + ", ".join(result.remaining))
            elif not result.errors:
                result.verified_root_absent = True
        return result
    if refuse_unknown_entries and not errors:
        if expected_subvolume_paths is not None:
            expected = {str(Path(path)) for path in expected_subvolume_paths}
            unexpected_subvolumes = [path for path in planned if path != root_text and path not in expected]
            if unexpected_subvolumes:
                result.errors.append(
                    "managed Btrfs root contains unexpected subvolume(s); manual inspection is required: "
                    + ", ".join(sorted(unexpected_subvolumes))
                )
        entries, entry_error = list_direct_entries(ops, root_text)
        if entry_error:
            result.errors.append(f"could not inspect direct root entries: {entry_error}")
        else:
            planned_set = set(planned)
            allowed_names = set(allowed_regular_names)
            unknown = [
                entry for entry in entries
                if entry not in planned_set and Path(entry).name not in allowed_names
            ]
            if unknown:
                result.errors.append(
                    "managed Btrfs root contains unexpected ordinary content; manual inspection is required: "
                    + ", ".join(sorted(unknown))
                )
    if dry_run or result.errors:
        return result

    confirmed, delete_errors = ops.batch_delete(planned)
    result.confirmed = confirmed
    result.errors.extend(delete_errors)
    _validate_confirmations(result)
    _verify_absent(result, ops)
    return result
