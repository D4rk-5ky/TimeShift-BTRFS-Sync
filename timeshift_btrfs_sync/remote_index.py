"""Compatibility facade for the single authoritative :mod:`inventory` module.

New runtime code imports :mod:`timeshift_btrfs_sync.inventory`.  The original
module name is retained for external callers without keeping a second scanner.
"""

from . import inventory as _inventory

_exports = {
    name: getattr(_inventory, name)
    for name in dir(_inventory)
    if not name.startswith("__")
}
globals().update(_exports)
__all__ = sorted(name for name in _exports if not name.startswith("_"))

del _exports, _inventory
