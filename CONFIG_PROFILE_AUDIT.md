# Configuration profile audit — TimeShift-BTRFS-Sync 0.2.8

All eight examples cover 108 supported scalar/list settings across the top level and ten tables. The runtime registries match their dataclass fields; active documents load with the real parser. Each commented option example parses as TOML and is loaded separately with coherent temporary credentials where file/auth prerequisites apply. Optional examples are alternatives, not instructions to uncomment all settings together. This document describes example configuration, not a deployed machine's mounts or credentials.

## Choosing a profile

| Profile for `init-config --profile` | Complete example | Run on | Intended workflow |
|---|---|---|---|
| `sync` | [config.example.toml](timeshift_btrfs_sync/data/config.example.toml) | Backup host | SSH Timeshift → local backup; local restore default |
| `remote-roundtrip` | [config.remote-roundtrip.example.toml](timeshift_btrfs_sync/data/config.remote-roundtrip.example.toml) | Backup host | SSH Timeshift → local backup → same SSH Timeshift |
| `restore-pull` | [config.restore-pull.example.toml](timeshift_btrfs_sync/data/config.restore-pull.example.toml) | Local Timeshift host | SSH backup → local Timeshift |
| `local-backup` | [example-config-local-backup.toml](timeshift_btrfs_sync/data/example-config-local-backup.toml) | Timeshift host with backup mounted | Local Timeshift → local backup |
| `remote-pull` | [example-config-remote-pull.toml](timeshift_btrfs_sync/data/example-config-remote-pull.toml) | Backup host | SSH Timeshift → local backup |
| `local-restore` | [example-config-local-restore.toml](timeshift_btrfs_sync/data/example-config-local-restore.toml) | Timeshift host with backup mounted | Local backup → local Timeshift |
| `remote-push-restore` | [example-config-remote-push-restore.toml](timeshift_btrfs_sync/data/example-config-remote-push-restore.toml) | Backup host | Local backup → SSH Timeshift |
| `remote-pull-restore` | [example-config-remote-pull-restore.toml](timeshift_btrfs_sync/data/example-config-remote-pull-restore.toml) | Local Timeshift host | SSH backup → local Timeshift |

The default profile is `sync`, supplied as `timeshift_btrfs_sync/data/config.example.toml`. Source `init-config` emits that exact file and all named profiles emit their corresponding resources byte-for-byte. Templates come from the app version you invoke; check both source and installed CLI versions if outputs differ. Supplied paths, SSH hosts/accounts and mail recipients are placeholders to adapt.

All profiles leave `default_dry_run=true`, `prune_after_sync=false`, normal/user O cleanup disabled, newest/common-parent safeguards enabled, and mail/MQTT/live monitoring disabled. All preserve configured paired/extra cleanup switches and their runtime consent/proof requirements. Capacity preflight remains disabled with estimate mode. Backup-oriented profiles enable automatic backup-time app snapshots; the four restore-only examples disable them. The flag does not change restore: a restore safety snapshot requires `--create-pre-restore-snapshot`.

## Setting coverage by section

| Section | Supported settings | Keys present in every template (active or valid commented example) |
|---|---:|---|
| Top level | 6 | `default_dry_run`, `lock_file`, `log_dir`, `name`, `prune_after_sync`, `state_file` |
| `[source]` | 15 | `btrfs_command`, `cache_root`, `cleanup_superseded_cache`, `create_readonly_cache`, `delete_redundant_snapshots`, `mode`, `send_compressed_data`, `send_proto`, `snapshot_root`, `source_change_retry_count`, `subvolumes`, `sudo`, `timeshift_command`, `verify_incremental_parent_once_per_run`, `verify_subvolumes_at_discovery` |
| `[destination]` | 6 | `btrfs_command`, `cleanup_incomplete_receive`, `create_target_root`, `delete_redundant_snapshots`, `sudo`, `target_root` |
| `[stream]` | 9 | `btrfs_verbose`, `mbuffer_command`, `mbuffer_extra_args`, `mbuffer_rate`, `mbuffer_size`, `transfer_size_check`, `transfer_size_mode`, `transfer_size_safety_margin`, `use_mbuffer` |
| `[retention]` | 10 | `boot`, `cleanup_ondemand`, `daily`, `hourly`, `keep_latest`, `keep_latest_common_parent`, `monthly`, `ondemand`, `protected_snapshots`, `weekly` |
| `[manual_snapshot]` | 5 | `cleanup_enabled`, `comment`, `enabled`, `marker`, `retention_count` |
| `[mqtt]` | 13 | `client_id`, `enabled`, `host`, `notify_on_failure`, `notify_on_success`, `password`, `password_file`, `port`, `qos`, `retain`, `timeout`, `topic`, `username` |
| `[mqtt_monitor]` | 10 | `discovery`, `discovery_prefix`, `enabled`, `events`, `expire_after`, `heartbeat_interval`, `manufacturer`, `measure_transfers`, `progress_interval`, `topic_prefix` |
| `[mail]` | 19 | `attach_logs`, `enabled`, `from_addr`, `include_json`, `max_attachment_bytes`, `notify_on_failure`, `notify_on_success`, `password`, `password_file`, `smtp_host`, `smtp_port`, `smtp_ssl`, `starttls`, `subject_prefix`, `timeout`, `to_addr`, `to_addrs`, `use_mailx_util`, `username` |
| `[ssh]` | 14 | `cipher`, `compression`, `control_master`, `control_path`, `control_persist`, `extra_args`, `host`, `identity_file`, `identity_passphrase`, `identity_passphrase_file`, `password`, `password_file`, `port`, `user` |
| `[restore]` | 1 | `mode` |

`[mail]` includes both `use_mailx_util` and `to_addr` in every file. Mail is disabled by default; selecting utility delivery still needs `enabled=true`, a recipient and a working local mail client/MTA setup. Optional secrets, SSH port/key/cipher/control-path overrides, send protocol, buffer rate and metadata-path overrides remain commented where optional. A commented path example still needs a real suitable path before use.

## Active and optional coverage

| Profile | Active leaf settings | Additional settings supplied as commented examples | Total covered |
|---|---:|---:|---:|
| `sync` | 89 | 19 | 108 |
| `restore-pull` | 91 | 17 | 108 |
| `remote-roundtrip` | 89 | 19 | 108 |
| `local-backup` | 89 | 19 | 108 |
| `remote-pull` | 89 | 19 | 108 |
| `local-restore` | 90 | 18 | 108 |
| `remote-push-restore` | 90 | 18 | 108 |
| `remote-pull-restore` | 90 | 18 | 108 |

## Endpoint and path roles

`source.mode` controls normal backup/source commands; `restore.mode` independently selects restore hosts. Sync always writes the backup locally. A restore pull profile (`restore.mode="ssh"`) must not be used for sync and the existing runtime guard refuses it. `remote-roundtrip` uses one SSH Timeshift host for both backup and push restore. Local profiles ignore their documented SSH examples.

The backup root and state file share an endpoint. Timeshift snapshot_root and cache_root share the Timeshift endpoint. The local lock/log paths belong to the machine running the command in every mode. Restore requires the local lock parent to exist; it is not a remote-lock setting. Every supplied root/path is absolute, the source cache stays outside snapshots, and local backup examples avoid overlapping the protected Timeshift/cache roots.

| Profile | Source mode / restore mode | Timeshift root (on selected Timeshift endpoint) | Backup root / state endpoint | Effective local lock | Effective local log directory |
|---|---|---|---|---|---|
| `sync` | `ssh` / `local` | `/timeshift-btrfs/snapshots` | `/Backups/Kubuntu/timeshift-btrfs` (local) | `/Backups/Kubuntu/timeshift-btrfs/.ts-btrfs-sync/lock` | `/Backups/Kubuntu/timeshift-btrfs/.ts-btrfs-sync/logs` |
| `restore-pull` | `local` / `ssh` | `/media/darkyere/OS-Root/timeshift-btrfs/snapshots` | `/Backups/Kubuntu/timeshift-btrfs` (SSH during restore) | `/media/darkyere/OS-Root/timeshift-btrfs/.ts-btrfs-sync/restore.lock` | `/var/log/timeshift-btrfs-sync` |
| `remote-roundtrip` | `ssh` / `ssh-target` | `/timeshift-btrfs/snapshots` | `/Backups/Kubuntu/timeshift-btrfs` (local) | `/Backups/Kubuntu/timeshift-btrfs/.ts-btrfs-sync/lock` | `/Backups/Kubuntu/timeshift-btrfs/.ts-btrfs-sync/logs` |
| `local-backup` | `local` / `local` | `/mnt/system/timeshift-btrfs/snapshots` | `/mnt/backup/timeshift-btrfs` (local) | `/mnt/backup/timeshift-btrfs/.ts-btrfs-sync/lock` | `/mnt/backup/timeshift-btrfs/.ts-btrfs-sync/logs` |
| `remote-pull` | `ssh` / `local` | `/mnt/system/timeshift-btrfs/snapshots` | `/mnt/backup/timeshift-btrfs` (local) | `/mnt/backup/timeshift-btrfs/.ts-btrfs-sync/lock` | `/mnt/backup/timeshift-btrfs/.ts-btrfs-sync/logs` |
| `local-restore` | `local` / `local` | `/mnt/system/timeshift-btrfs/snapshots` | `/mnt/backup/timeshift-btrfs` (local) | `/mnt/system/.ts-btrfs-sync/restore.lock` | `/mnt/backup/timeshift-btrfs/.ts-btrfs-sync/logs` |
| `remote-push-restore` | `ssh` / `ssh-target` | `/mnt/system/timeshift-btrfs/snapshots` | `/mnt/backup/timeshift-btrfs` (local) | `/mnt/backup/timeshift-btrfs/.ts-btrfs-sync/restore.lock` | `/mnt/backup/timeshift-btrfs/.ts-btrfs-sync/logs` |
| `remote-pull-restore` | `local` / `ssh` | `/mnt/system/timeshift-btrfs/snapshots` | `/mnt/backup/timeshift-btrfs` (SSH during restore) | `/mnt/system/.ts-btrfs-sync/restore.lock` | `/mnt/system/.ts-btrfs-sync/logs` |

For restore, state always resolves to `<backup-root>/.ts-btrfs-sync/state.json`. Only pull restore reads it remotely. SSH backup roles use the restore account example, while SSH Timeshift roles retain the sync account example; actual names/permissions must match your machines. Legacy example paths remain supported rather than being silently moved.

## Verification boundaries

The profile tests use the real loader, CLI generation and endpoint factories without running endpoint commands. Optional examples are tested one at a time; they do not validate every possible combination of user-edited values. Final ZIP resources are checked against the source, their manifest, fresh extraction and generated configs. No supplied placeholder host, remote account, mount, sudo policy, Postfix/SMTP delivery or actual Btrfs/Timeshift backup/restore was exercised. Those require the user's real environment. See RELEASE_VERIFICATION.md for release checks and limitations.
