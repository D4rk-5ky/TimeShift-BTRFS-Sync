# Removed older nested project — 0.1.87

Removed on 2026-10-12 at the user's explicit request. The nested application identified itself as **0.1.75**. The current application is **0.1.87**.

The main older source directory was:

`timeshift_btrfs_sync/timeshift_btrfs_sync/`

Related duplicate project material was under:

- `timeshift_btrfs_sync/tests/`
- `timeshift_btrfs_sync/scripts/`
- `timeshift_btrfs_sync/tools/`
- `timeshift_btrfs_sync/sudoers/`
- `timeshift_btrfs_sync/systemd/`
- Package-local README, INSTALL, VERSIONING, code map, audit, LICENSE and .gitignore files.

All paths below are relative to the extracted project's root. The active first-level package `.py` files, its complete `data/` examples, and root-level docs/tests/helpers/license/integration files are retained. The original upload and previous version ZIPs have not been modified; those archived versions still contain the older copy.

The removed working-copy paths were formerly below:

`/home/darkyere/Documents/Codex/2026-10-12/please-work-with-this-project-using/work/release/TimeShift-BTRFS-Sync-0.1.86/`

The working 0.1.86 reference remains unchanged. The removal applies to the new 0.1.87 project and ZIP.

## Complete removal list — 52 files

- `timeshift_btrfs_sync/.gitignore`
- `timeshift_btrfs_sync/COMMENTED_CODE_MAP.md`
- `timeshift_btrfs_sync/CONFIG_AND_CLI_AUDIT.md`
- `timeshift_btrfs_sync/INSTALL.md`
- `timeshift_btrfs_sync/LICENSE`
- `timeshift_btrfs_sync/README.md`
- `timeshift_btrfs_sync/VERSIONING.md`
- `timeshift_btrfs_sync/scripts/build_pyinstaller.py`
- `timeshift_btrfs_sync/sudoers/source-minimal.example`
- `timeshift_btrfs_sync/systemd/ts-btrfs-sync.service`
- `timeshift_btrfs_sync/systemd/ts-btrfs-sync.timer`
- `timeshift_btrfs_sync/tests/test_manual_snapshot_retention.py`
- `timeshift_btrfs_sync/tests/test_pipeline_failure_diagnostics.py`
- `timeshift_btrfs_sync/tests/test_profiles_and_packaging.py`
- `timeshift_btrfs_sync/tests/test_release_hygiene.py`
- `timeshift_btrfs_sync/tests/test_restore_topology_regressions.py`
- `timeshift_btrfs_sync/tests/test_ssh_auth_regressions.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/__init__.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/__main__.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/btrfs_ops.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/cache_ops.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/cli.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/commands.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/config.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/data/config.example.toml`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/data/config.remote-roundtrip.example.toml`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/data/config.restore-pull.example.toml`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/destroy.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/endpoint.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/executor.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/inventory.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/lock.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/log.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/mail.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/maintenance.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/models.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/mqtt.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/notify.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/paths.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/payload_stats.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/planning.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/preflight.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/restore.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/retention.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/source.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/ssh.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/state.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/sync.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/timeshift.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/topology.py`
- `timeshift_btrfs_sync/timeshift_btrfs_sync/tree_ops.py`
- `timeshift_btrfs_sync/tools/pyinstaller_entry.py`
