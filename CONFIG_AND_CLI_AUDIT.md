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
- Incremental sends require source UUID to match destination Received UUID.
- Full send begins a chain only when the destination is empty at run start.
- Retention selects snapshots by Timeshift tags and processes transfers oldest-to-newest.
- Prune deletes destination, source cache, then state for each selected snapshot.
- Recursive Btrfs cleanup discovers the complete subvolume graph and deletes deepest-first.
- Ordinary non-empty managed roots are refused; recursive ordinary deletion is not used.
- State must use schema version 3, relative managed paths, and explicit send-path kinds.
- Real prune and destroy operations require their destructive confirmations.
- Restore can import one timestamp or every backup newer than the latest UUID- and stable-`info.json`-confirmed common parent. It refuses overwrite, reuses an exact recorded read-only source send parent for an incremental first restore when available, otherwise explains and uses one hidden full seed, writes the exact saved `info.json`, exposes writable CoW payload snapshots, and requires Timeshift to list every committed date.
- Restore prints that original H/D/W/M tags remain subject to Timeshift retention, including the risk that restored snapshots or existing tagged snapshots older than the restored snapshots may be pruned, and every real local or SSH restore requires the exact sentence `I UNDERSTAND TIMESHIFT MAY DELETE RESTORED SNAPSHOTS OR OLDER THAN RESTORED SNAPSHOTS` before transfer.
- Local and SSH restore use the same implementation; only the source endpoint transport changes.
- Restore requires source-side ordinary filesystem privilege for `mkdir`, `tee`, `chmod`, `mv`, exact `rm`, and `rmdir` in addition to Btrfs and Timeshift privilege.

## `restore` flags

- `--config`, `-c`
- exactly one of `--snapshot` or `--all`
- `--allow-no-common-parent`
- `--allow-os-identity-mismatch`
- `--dry-run`
- `--run`
- `--i-understand-this-modifies-timeshift`

The backup is always read from local `destination.target_root`. The restored payload is received into the configured local or SSH source endpoint.

`--snapshot` performs one full restore. `--all` discovers all valid destination backups and the current coherent source Timeshift/Btrfs/`info.json` inventory, then uses `state.json` to prove the newest common date for every configured payload. A common date requires the live Timeshift UUID to match `original_source_uuid`, the backup Received UUID to match `send_source_uuid`, and source/backup `info.json` to match by `sys-uuid` and Btrfs `type`. Names alone are not accepted.

The selected backup set must have one consistent stable `info.json` identity. H/D/W/M/O/B tags, comments, creation time, file counts, app version, live status, and Btrfs statistics are ignored because they vary per snapshot. `sys-distro` is diagnostic only. If the backup identity does not match any current Timeshift control file, real restore requires `--allow-os-identity-mismatch` and the exact sentence `I UNDERSTAND THIS BACKUP MAY BELONG TO ANOTHER OS`.

With a common parent, restore resolves every payload's recorded `send_path` and verifies the current source subvolume still has `send_source_uuid` and remains read-only. If all payloads pass, the first newer backup is received incrementally using that existing source/cache parent. If any exact parent is missing, writable, or has the wrong UUID, the terminal prints the reason and the common backup is full-received as a hidden seed. Without a common parent, the oldest backup is the full seed. All later backups are incremental. Visible Timeshift payloads are writable Btrfs snapshots of the hidden received chain, retaining CoW sharing. Without a common parent, real execution is refused unless `--allow-no-common-parent` is supplied and the stronger typed confirmations succeed.

The original `info.json` is restored unchanged, so its H/D/W/M tags remain active and normal Timeshift retention can delete restored snapshots or existing tagged snapshots older than the restored snapshots. Dry-run and real mode print the warning. Every real restore requires the exact additional sentence `I UNDERSTAND TIMESHIFT MAY DELETE RESTORED SNAPSHOTS OR OLDER THAN RESTORED SNAPSHOTS` before any Btrfs receive.
