# Configuration and CLI audit

This file lists the current public interface. The loader rejects any key not listed here.

## Commands

- `init-config`
- `test-source`
- `list-source`
- `sync`
- `prune`
- `create-manual`
- `show-state`
- `clear-state`
- `delete-lock`
- `destroy-leftovers`

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
