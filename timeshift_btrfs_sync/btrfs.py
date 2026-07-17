"""Compatibility exports for the shared Btrfs architecture.

Runtime workflows use :class:`btrfs_ops.BtrfsOps`,
:class:`cache_ops.CacheManager`, :func:`tree_ops.delete_subvolume_tree`, and
``paths`` directly.  This original module is retained so external imports of
common metadata/path helpers do not fail, but it contains no second command or
cleanup implementation.
"""

from .btrfs_ops import BtrfsOps, clean_uuid, parse_subvolume_list_paths, parse_subvolume_show
from .cache_ops import CacheManager, cache_child_path, cache_parent_path, validate_cache_snapshot
from .paths import is_same_or_under, is_under, listed_path_to_absolute, normalize_source_path, sort_deepest_first
from .tree_ops import TreeDeleteResult, delete_subvolume_tree, discover_subvolume_tree

# Historical read-only aliases; all point to the single shared implementations.
_subvolume_list_paths = parse_subvolume_list_paths
readonly_cache_path = cache_child_path
readonly_cache_parent_path = cache_parent_path
path_is_same_or_under = is_same_or_under
path_is_under_cache = is_under
