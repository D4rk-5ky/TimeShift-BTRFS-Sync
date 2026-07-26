# Configuration and CLI audit

This file lists the current public interface. The loader rejects any key not listed here.

## Commands

- `init-config`
- `test-source`
- `list-source`
- `sync`
- `prune`
- `restore`
- `create-manual`
- `show-state`
- `clear-state`
- `delete-lock`
- `destroy-leftovers`



## Packaged config profiles

- `timeshift_btrfs_sync/data/config.example.toml`: complete normal sync/local-restore profile.
- `timeshift_btrfs_sync/data/config.restore-pull.example.toml`: complete SSH-backup-to-local-Timeshift restore profile.
- `init-config --profile sync` writes the first profile.
- `init-config --profile restore-pull` writes the second profile.
- Both profiles document every current schema key, including restore transport and all SSH authentication/transport settings.
- SSH password authentication is supported only through `sshpass`, using exactly one of `ssh.password` or `ssh.password_file`; key authentication remains recommended.

## `init-config` flags

- `--path`
- `--profile sync`
- `--profile restore-pull`
- `--force`

The default profile is `sync`. Both generated profiles contain every current configuration key and differ only in profile-oriented defaults and explanations.

## Destination Btrfs layout

- `destination.target_root` must be a Btrfs subvolume.
- `<target_root>/snapshots` must be a Btrfs subvolume and never uses mkdir fallback.
- Every direct `<target_root>/snapshots/<date>` entry must be a Btrfs subvolume.
- Destination bulk inventory is rooted at `<target_root>/snapshots`; a direct date missed by bulk path mapping is checked with exact `btrfs subvolume show` before rejection.
- State, lock, and optional log helper directories may still be ordinary directories.

## Top-level keys

- `default_dry_run`
- `lock_file`
- `log_dir`
- `name`
- `prune_after_sync`
- `state_file`

## `[restore]`

- `mode`

## `[source]`

- `btrfs_command`
- `cache_root`
- `cleanup_superseded_cache`
- `create_readonly_cache`
- `mode`
- `send_compressed_data`
- `send_proto`
- `snapshot_root`
- `source_change_retry_count`
- `subvolumes`
- `sudo`
- `timeshift_command`
- `verify_incremental_parent_once_per_run`
- `verify_subvolumes_at_discovery`

## `[destination]`

- `btrfs_command`
- `cleanup_incomplete_receive`
- `create_target_root`
- `sudo`
- `target_root`

## `[stream]`

- `btrfs_verbose`
- `mbuffer_command`
- `mbuffer_extra_args`
- `mbuffer_rate`
- `mbuffer_size`
- `use_mbuffer`

## `[retention]`

- `boot`
- `cleanup_ondemand`
- `daily`
- `hourly`
- `keep_latest`
- `keep_latest_common_parent`
- `monthly`
- `ondemand`
- `protected_snapshots`
- `weekly`

## `[manual_snapshot]`

- `cleanup_enabled`
- `comment`
- `enabled`
- `marker`
- `retention_count`

## `[ssh]`

- `cipher`
- `compression`
- `control_master`
- `control_path`
- `control_persist`
- `extra_args`
- `host`
- `identity_file`
- `password`
- `password_file`
- `port`
- `user`

## `[mqtt]`

- `client_id`
- `enabled`
- `host`
- `notify_on_failure`
- `notify_on_success`
- `password`
- `password_file`
- `port`
- `qos`
- `retain`
- `timeout`
- `topic`
- `username`

## `[mail]`

- `attach_logs`
- `enabled`
- `from_addr`
- `include_json`
- `max_attachment_bytes`
- `notify_on_failure`
- `notify_on_success`
- `password`
- `password_file`
- `smtp_host`
- `smtp_port`
- `smtp_ssl`
- `starttls`
- `subject_prefix`
- `timeout`
- `to_addrs`
- `username`

## Current behavior checks

- Local source mode does not construct an SSH configuration or SSH command.
- SSH source mode requires `[ssh].host` and uses one source endpoint abstraction.
- The source snapshot root is Timeshift-owned and is never a delete target.
- The source cache root and destination root are app-owned Btrfs trees.
- Root-scoped cache inventory accepts Btrfs descendants reported with an on-disk prefix, as `<date>/@`, or as bare `@` below an exact date parent; unmatched paths remain rejected outside scoped `-o` listings.
- A cache child missed by the bulk index is checked through an authoritative parent-scoped UUID/read-only list before any snapshot creation; an existing valid child is reused and an unavailable safety check aborts.
- Incremental sends require source UUID to match destination Received UUID.
- Full send begins a chain only when the destination is empty at run start.
- Retention selects snapshots by Timeshift tags and processes transfers oldest-to-newest.
- Prune deletes destination, source cache, then state for each selected snapshot.
- Recursive Btrfs cleanup discovers the complete subvolume graph and deletes deepest-first.
- Ordinary non-empty managed roots are refused; recursive ordinary deletion is not used.
- State must use schema version 3, relative managed paths, and explicit send-path kinds.
- Real prune and destroy operations require their destructive confirmations.
- Timeshift native date paths below `source.snapshot_root` are ordinary directories containing `info.json` plus Btrfs payload subvolumes; only backup date containers below `destination.target_root/snapshots` must themselves be Btrfs subvolumes.
- Restore can import one timestamp or every backup newer than the newest safely confirmed timestamp physically present in both configured repositories. It prefers exact state/cache Btrfs lineage, falls back to matching same-date `info.json` `sys-uuid`/`type` when all payloads are real Btrfs subvolumes, always full-receives the exact common backup as a receiver-side hidden seed, writes the exact saved `info.json`, exposes writable CoW payload snapshots, and requires Timeshift to list every committed date.
- Restore prints that original H/D/W/M tags remain subject to Timeshift retention, including the risk that restored snapshots or existing tagged snapshots older than the restored snapshots may be pruned, and every real local or SSH restore requires the exact sentence `I UNDERSTAND TIMESHIFT MAY DELETE RESTORED SNAPSHOTS OR OLDER THAN RESTORED SNAPSHOTS` before transfer.
- Local backup restore, local-backup-to-SSH restore, and SSH-backup-to-local restore use the same planner and execution loop; only the backup and Timeshift endpoint transports change.
- Restore transport is selected only by `[restore] mode`: `local` reads a local backup and restores locally, `ssh` pulls an SSH backup into local Timeshift, and `ssh-target` restores a local backup into an SSH Timeshift target. `source.mode` remains sync-only. `source.snapshot_root` and `source.cache_root` always share the Timeshift endpoint selected by restore mode: local for `local`/`ssh`, SSH remote for `ssh-target`. Backup inventory/state/send never use `source.cache_root`. Restore locking always uses the configured local `lock_file` on the machine running the command and never opens a lock over SSH.
- Restore requires source-side read-only `test`, `ls`, and `base64` plus ordinary filesystem privilege for `mkdir`, `tee`, `chmod`, `mv`, exact `rm`, and `rmdir` in addition to Btrfs and Timeshift privilege. Backup-side physical scans use `destination.sudo` for the same read-only commands. No privileged shell is invoked.

## `restore` flags

- `--config`, `-c`
- exactly one of `--snapshot` or `--all`
- `--create-pre-restore-snapshot`
- `--allow-no-common-parent`
- `--allow-os-identity-mismatch`
- `--dry-run`
- `--run`
- `--i-understand-this-modifies-timeshift`

Restore uses `[restore] mode` independently from `source.mode`. `local` uses local backup and local Timeshift endpoints; `ssh` uses the configured SSH endpoint as the backup host and restores locally; `ssh-target` reads the backup locally and uses SSH for the Timeshift target. All directions use the same restore planner, identity checks, chain rules, and staging logic.

`--create-pre-restore-snapshot` is a restore-only action. After all plan checks and typed confirmations, but before any receive or staging directory, it calls Timeshift on the configured restore-target `source` endpoint, re-reads `timeshift --list`, identifies one new on-demand snapshot, and exact-checks every configured Btrfs payload. The remote/local backup repository is never used for this command. The safety snapshot remains if later restore work fails. `[manual_snapshot]` remains sync-only.

`--snapshot` performs one full restore. `--all` independently scans physical timestamp directories below the configured Timeshift and backup roots, intersects them, and evaluates candidates newest-to-oldest. The read-only scanner runs only `test`, `ls`, and `base64` through the endpoint's configured privilege prefix; it never invokes a privileged shell. `timeshift --list` contributes tags/comments but is not authoritative for physical timestamp existence.

Every configured payload must exist as a real Btrfs subvolume on both sides. Exact proof is preferred: a completed state record links current Timeshift UUID to `original_source_uuid` and backup Received UUID to `send_source_uuid`; retained-cache proof links current Timeshift UUID to cache Parent UUID and cache send identity to backup Received UUID; a direct read-only payload may match the backup Received UUID. When all exact state/cache paths are unavailable, the newest same physical timestamp is still accepted if its source and backup `info.json` files match stable `sys-uuid` and `type`. H/D/W/M/O/B tags, comments, creation time, file counts, app version, live status, and Btrfs statistics are ignored. Names alone, repository-wide identity from another timestamp, and state records without live payloads are not accepted. Missing, unreadable, symlinked, malformed, or unsupported state is ignored with a diagnostic so independent cache or same-date metadata proof can still be evaluated.

The selected backup set must have one consistent `info.json` identity. `sys-distro` is diagnostic only. If no candidate passes exact Btrfs proof or matching same-date identity proof, `--all` has no common parent. If the backup identity cannot be matched to the current repository and no exact proof overrides that warning, real restore requires `--allow-os-identity-mismatch` and the exact sentence `I UNDERSTAND THIS BACKUP MAY BELONG TO ANOTHER OS`.

With a common parent, restore always full-receives the exact common backup into the hidden chain on the receiving Timeshift filesystem. Later backups are incremental from the immediately preceding backup, and the hidden receiver-side parent is verified read-only with the expected Received UUID before each stream. Source cache paths are used only to prove lineage and are never treated as implicit receive parents. An explicit Btrfs missing-parent/clone-source error deletes only the exact partial child and retries that payload once as a full stream; all unrelated failures remain hard errors. Without a common parent, the oldest backup is the full seed. Visible Timeshift payloads are writable Btrfs snapshots of the hidden received chain, retaining CoW sharing. Without a common parent, real execution is refused unless `--allow-no-common-parent` is supplied and the stronger typed confirmations succeed.

The original `info.json` is restored unchanged, so its H/D/W/M tags remain active and normal Timeshift retention can delete restored snapshots or existing tagged snapshots older than the restored snapshots. Dry-run and real mode print the warning. Every real restore requires the exact additional sentence `I UNDERSTAND TIMESHIFT MAY DELETE RESTORED SNAPSHOTS OR OLDER THAN RESTORED SNAPSHOTS` before any Btrfs receive.
