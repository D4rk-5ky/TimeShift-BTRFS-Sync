"""Canonical path normalization and containment rules.

Every workflow uses these helpers so destructive guards, Btrfs-list path
resolution, state paths, and inventory paths cannot disagree.
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath
import posixpath


def normalize_source_path(path: str) -> str:
    """Normalize POSIX path text while preserving an intentionally empty value."""

    text = str(path).strip()
    if not text:
        return ""
    value = posixpath.normpath(text)
    return "/" if value == "/" else value.rstrip("/")


def is_same_or_under(path: str | Path | None, root: str | Path | None) -> bool:
    """Return true when ``path`` equals ``root`` or is below it."""

    if path is None or root is None:
        return False
    path_text = normalize_source_path(str(path))
    root_text = normalize_source_path(str(root))
    if not path_text or not root_text:
        return False
    return path_text == root_text or path_text.startswith(root_text.rstrip("/") + "/")


def is_local_same_or_under(path: str | Path | None, root: str | Path | None) -> bool:
    """Return true when one local path resolves to ``root`` or below it.

    Source paths can be remote and therefore use lexical POSIX normalization.
    Local destructive/log-survival checks must additionally resolve ``~``, ``..``,
    and symlinks so a path cannot appear outside a target while physically living
    inside it.
    """

    if path is None or root is None:
        return False
    try:
        path_value = Path(path).expanduser().resolve(strict=False)
        root_value = Path(root).expanduser().resolve(strict=False)
        path_value.relative_to(root_value)
        return True
    except (OSError, RuntimeError, ValueError):
        return False


def is_under(path: str | Path | None, root: str | Path | None) -> bool:
    """Return true only when ``path`` is strictly below ``root``."""

    if path is None or root is None:
        return False
    path_text = normalize_source_path(str(path))
    root_text = normalize_source_path(str(root))
    if not path_text or not root_text:
        return False
    return path_text != root_text and path_text.startswith(root_text.rstrip("/") + "/")


def listed_path_to_absolute(
    root: str | Path,
    listed_path: str,
    *,
    scoped_to_root: bool = False,
) -> str | None:
    """Resolve one Btrfs-list path below a mounted root.

    Btrfs can include an on-disk mount-subvolume prefix that is absent from the
    configured mount path. The longest matching suffix of the configured root
    anchors the descendant. Commands using ``btrfs subvolume list -o ROOT``
    may instead return a path relative to ``ROOT`` itself, such as
    ``2026-07-21_07-28-49/@``. Callers that actually used ``-o ROOT`` set
    ``scoped_to_root=True`` so that safe relative form is joined below the exact
    requested root. Unscoped callers continue to reject unmatched paths.
    """

    root_text = normalize_source_path(str(root))
    listed_text = posixpath.normpath(str(listed_path).strip())
    if not listed_text or listed_text == ".":
        return None
    if listed_text.startswith("/"):
        candidate = normalize_source_path(listed_text)
        return candidate if is_same_or_under(candidate, root_text) else None

    root_parts = [part for part in PurePosixPath(root_text).parts if part != "/"]
    listed_parts = [part for part in PurePosixPath(listed_text).parts if part not in {"/", ""}]
    if not listed_parts:
        return None

    if listed_parts[: len(root_parts)] == root_parts:
        candidate = normalize_source_path("/" + "/".join(listed_parts))
        return candidate if is_same_or_under(candidate, root_text) else None

    for suffix_length in range(len(root_parts), 0, -1):
        suffix = root_parts[-suffix_length:]
        for index in range(0, len(listed_parts) - suffix_length + 1):
            if listed_parts[index:index + suffix_length] != suffix:
                continue
            candidate = normalize_source_path(str(PurePosixPath(root_text, *listed_parts[index + suffix_length:])))
            return candidate if is_same_or_under(candidate, root_text) else None

    if scoped_to_root and ".." not in listed_parts:
        candidate = normalize_source_path(str(PurePosixPath(root_text, *listed_parts)))
        return candidate if is_under(candidate, root_text) else None
    return None


def sort_deepest_first(paths: list[str]) -> list[str]:
    """Deduplicate and order paths for child-before-parent deletion."""

    return sorted(set(paths), key=lambda item: (len(PurePosixPath(item).parts), item), reverse=True)
