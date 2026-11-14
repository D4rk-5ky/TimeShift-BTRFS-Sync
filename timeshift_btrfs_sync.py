#!/usr/bin/env python3
"""Run the existing CLI directly; keep this file beside timeshift_btrfs_sync/."""

import sys
from pathlib import Path


if __name__ == "__main__":
    if sys.version_info < (3, 11):
        raise SystemExit("TimeShift-BTRFS-Sync requires Python 3.11 or newer.")
    package = Path(__file__).resolve().parent / "timeshift_btrfs_sync"
    if not (package / "__init__.py").is_file() or not (package / "cli.py").is_file():
        raise SystemExit("Keep timeshift_btrfs_sync.py beside the complete timeshift_btrfs_sync/ package. Extract the full project ZIP before running it.")
    from timeshift_btrfs_sync.cli import main

    raise SystemExit(main())
