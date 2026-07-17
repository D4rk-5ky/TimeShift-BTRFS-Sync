# Commented code map

This map describes the **current 0.1.49 implementation only**. It names every
runtime class, function, method, property, and nested command helper, and
explains its role. The architecture intentionally keeps each low-level Btrfs,
inventory, cache, path, planning, execution, and deletion operation in one
authoritative module. Sync, prune, recovery, and destroy workflows compose
those shared operations in different orders instead of maintaining separate
local/SSH implementations.

## Architecture layers

1. **Transport — `endpoint.py`**: one local/source/SSH execution abstraction.
2. **Btrfs operations — `btrfs_ops.py`**: one probe/list/create/snapshot/delete/send/receive command facade.
3. **Inventory — `inventory.py`**: one coherent Timeshift, `info.json`, snapshot-root, and cache-root inventory. `remote_index.py` only re-exports it for compatibility.
4. **Combined records — `snapshot_records.py`**: joins source, cache, destination, and state into one `SnapshotRecord` per date.
5. **Planning — `planning.py`**: pure ordered action plans with no filesystem changes.
6. **Execution — `executor.py`**: runs or previews plans through registered handlers.
7. **Shared safety operations — `cache_ops.py`, `tree_ops.py`, and `paths.py`**: exact cache creation/reuse, verified deepest-first tree deletion, and one path-safety implementation.
8. **Workflows — `sync.py`, `retention.py`, and `destroy.py`**: arrange inventory, plans, and shared operations according to the requested job.

## CLI commands

- `init-config`: writes the complete current example TOML and refuses overwrite unless `--force` is given.
- `test-source` / `test-ssh`: checks the configured source transport plus Timeshift and Btrfs command access.
- `list-source`: lists Timeshift snapshots, optionally forcing Btrfs verification.
- `sync`: discovers once, plans oldest-to-newest full/incremental work, executes transfers, copies `info.json`, recovers source-change races, and optionally prunes.
- `prune`: applies the same retention policy and shared Btrfs deletion engine without running sync.
- `create-manual`: creates one guarded Timeshift on-demand snapshot after source identity and chain viability checks.
- `show-state`: prints the relocatable state summary or raw JSON.
- `clear-state`: removes only the guarded state file after explicit confirmation.
- `delete-lock`: removes only a confirmed stale app lock after explicit confirmation.
- `destroy-leftovers`: plans selected source-cache/destination tree retirement and succeeds only after exact deletion confirmations and root-absence verification.

## Runtime modules and symbols

### `__init__.py`
Timeshift Btrfs sync package.
- Contains no independent runtime class/function implementation; it provides metadata, entry-point wiring, or compatibility exports.

### `__main__.py`
Run the CLI with: python -m timeshift_btrfs_sync.
- Contains no independent runtime class/function implementation; it provides metadata, entry-point wiring, or compatibility exports.

### `btrfs.py`
Compatibility exports for the shared Btrfs architecture.
- Contains no independent runtime class/function implementation; it provides metadata, entry-point wiring, or compatibility exports.

### `btrfs_ops.py`
Reusable Btrfs operations independent of workflow order.
- `clean_uuid` (function/method): Perform clean uuid for the owning module's workflow boundary.
- `parse_subvolume_show` (function/method): Parse UUID and read-only fields from ``btrfs subvolume show``.
- `parse_subvolume_list_paths` (function/method): Extract raw path fields from ``btrfs subvolume list`` output.
- `BtrfsOps` (class): Btrfs command facade for one local or source endpoint.
- `BtrfsOps.prefix` (property): Expose the calculated prefix value without duplicating it at call sites.
- `BtrfsOps.argv` (function/method): Perform argv for the owning module's workflow boundary.
- `BtrfsOps.run` (function/method): Perform run for the owning module's workflow boundary.
- `BtrfsOps.meta` (function/method): Return exact-path subvolume metadata or ``None`` for an optional miss.
- `_ListedSubvolume` (class): Internal numeric ID, containing-parent ID, and raw-path record from one filesystem-wide Btrfs list.
- `_parse_listed_subvolumes` (function/method): Parse numeric containment records from ``btrfs subvolume list -a -p`` output.
- `_descendant_list_paths` (function/method): Follow numeric parent IDs from the exact configured root and return only true descendant raw paths.
- `BtrfsOps.list_children` (function/method): Return every nested descendant using one ``subvolume list -a -p`` endpoint command, with a root-scoped ``-o`` fallback only when no numeric root ID is available.
- `BtrfsOps.create` (function/method): Perform create for the owning module's workflow boundary.
- `BtrfsOps.delete` (function/method): Perform delete for the owning module's workflow boundary.
- `BtrfsOps.send_command` (function/method): Perform send command for the owning module's workflow boundary.
- `BtrfsOps.receive_command` (function/method): Perform receive command for the owning module's workflow boundary.
- `BtrfsOps.batch_delete` (function/method): Delete exact paths in one endpoint command and validate confirmations.

### `cache_ops.py`
Single source send-cache operation used by sync and recovery.
- `CacheResult` (class): Shared CacheResult model or service used as the single representation for this responsibility.
- `_safe_name` (function/method): Internal safe name helper shared by the owning module so workflows do not duplicate this function/method logic.
- `cache_parent_path` (function/method): Perform cache parent path for the owning module's workflow boundary.
- `cache_child_path` (function/method): Perform cache child path for the owning module's workflow boundary.
- `validate_cache_snapshot` (function/method): Prove an exact cache child is a safe read-only snapshot of ``original``.
- `CacheManager` (class): Ensure exact reusable send snapshots without nested cache creation.
- `CacheManager.__init__` (function/method): Internal init helper shared by the owning module so workflows do not duplicate this function/method logic.
- `CacheManager._ensure_subvolume` (function/method): Internal ensure subvolume helper shared by the owning module so workflows do not duplicate this function/method logic.
- `CacheManager._probe_create_verify` (function/method): Probe, create if absent, and verify exact cache path in one command.
- `CacheManager._probe_create_verify.meta` (function/method): Perform meta for the owning module's workflow boundary.
- `CacheManager.ensure_send_snapshot` (function/method): Return original read-only source or create/reuse one exact cache child.

### `cli.py`
Command-line interface for timeshift-btrfs-sync.
- `new_subparser` (function/method): Perform new subparser for the owning module's workflow boundary.
- `add_config_arg` (function/method): Perform add config arg for the owning module's workflow boundary.
- `add_run_mode_args` (function/method): Perform add run mode args for the owning module's workflow boundary.
- `add_yes_delete_arg` (function/method): Perform add yes delete arg for the owning module's workflow boundary.
- `_load_config_state` (function/method): Load state and resolve all root-relative paths against this config.
- `_failure_exit_code` (function/method): Return a stable CLI exit code for failure notifications.
- `_stderr_tail_for_exception` (function/method): Return the best available recent stderr text for failure notifications.
- `_send_notifications` (function/method): Send optional MQTT/email status without changing the command exit code.
- `_mail_attachment_paths` (function/method): Return current run log paths for optional email attachment.
- `_safe_destroy_log_dir` (function/method): Return a log directory that will survive a destructive cleanup.
- `_with_logging` (function/method): Run a command with optional logging and MQTT notification.
- `_resolve_dry_run` (function/method): Internal resolve dry run helper shared by the owning module so workflows do not duplicate this function/method logic.
- `cmd_init_config` (function/method): Perform cmd init config for the owning module's workflow boundary.
- `cmd_test_ssh` (function/method): Perform cmd test ssh for the owning module's workflow boundary.
- `cmd_test_ssh._run` (function/method): Internal run helper shared by the owning module so workflows do not duplicate this function/method logic.
- `_refresh_state_metadata_from_timeshift` (function/method): Refresh mutable state metadata from one fast Timeshift list read.
- `cmd_list_source` (function/method): List snapshots on the source machine.
- `cmd_list_source._run` (function/method): Internal run helper shared by the owning module so workflows do not duplicate this function/method logic.
- `cmd_sync` (function/method): Perform cmd sync for the owning module's workflow boundary.
- `cmd_sync._run_dry` (function/method): Internal run dry helper shared by the owning module so workflows do not duplicate this function/method logic.
- `cmd_sync._run_locked` (function/method): Internal run locked helper shared by the owning module so workflows do not duplicate this function/method logic.
- `cmd_prune` (function/method): Perform cmd prune for the owning module's workflow boundary.
- `cmd_prune._run_dry` (function/method): Internal run dry helper shared by the owning module so workflows do not duplicate this function/method logic.
- `cmd_prune._run_locked` (function/method): Internal run locked helper shared by the owning module so workflows do not duplicate this function/method logic.
- `cmd_create_manual` (function/method): Perform cmd create manual for the owning module's workflow boundary.
- `cmd_create_manual._run` (function/method): Internal run helper shared by the owning module so workflows do not duplicate this function/method logic.
- `cmd_clear_state` (function/method): Guardedly remove the configured state_file with normal run logging.
- `cmd_clear_state._run` (function/method): Internal run helper shared by the owning module so workflows do not duplicate this function/method logic.
- `cmd_delete_lock` (function/method): Guardedly remove the configured lock_file if it is stale, with logging.
- `cmd_delete_lock._run` (function/method): Internal run helper shared by the owning module so workflows do not duplicate this function/method logic.
- `cmd_destroy_leftovers` (function/method): Destroy configured leftovers with normal run logging enabled.
- `cmd_destroy_leftovers._run` (function/method): Internal run helper shared by the owning module so workflows do not duplicate this function/method logic.
- `cmd_show_state` (function/method): Perform cmd show state for the owning module's workflow boundary.
- `cmd_show_state._run` (function/method): Internal run helper shared by the owning module so workflows do not duplicate this function/method logic.
- `build_parser` (function/method): Create the argparse parser and command-specific flag help.
- `main` (function/method): Perform main for the owning module's workflow boundary.

### `commands.py`
Shared subprocess helpers.
- `CommandError` (class): Raised when an external command exits with a non-zero status.
- `CommandError.__init__` (function/method): Internal init helper shared by the owning module so workflows do not duplicate this function/method logic.
- `Completed` (class): Small command result object.
- `sudo_prefix` (function/method): Split a configured sudo prefix into argv parts.
- `quote_join` (function/method): Quote argv parts into one safe remote-shell command string.
- `remote_double_quote` (function/method): Return a shell-safe double-quoted argument for a remote shell command.
- `_merged_env` (function/method): Merge optional child-process environment variables.
- `run_local` (function/method): Run a local command and capture stdout/stderr.
- `_start_pipeline_readers` (function/method): Start tee readers from compact stream routing specs.
- `_failed_stderr` (function/method): Return captured pipeline stderr for streams that belong in failures.
- `_log_failed_streams` (function/method): Copy captured failed pipeline streams to .err.
- `stream_pipeline` (function/method): Stream left command into optional middle command, then right command.

### `config.py`
TOML configuration loading and validation.
- `ManualSnapshotConfig` (class): Optional source-side Timeshift on-demand snapshot creation and cleanup.
- `SourceConfig` (class): Source Timeshift and Btrfs settings.
- `DestinationConfig` (class): Local/destination receive settings.
- `StreamConfig` (class): Optional pipeline display/buffering settings.
- `StreamConfig.command` (function/method): Return mbuffer command argv or None when disabled.
- `RetentionConfig` (class): Destination retention counts by Timeshift tag.
- `RetentionConfig.counts_by_tag` (function/method): Return retention counts keyed by Timeshift tag letters.
- `AppConfig` (class): Complete validated app configuration.
- `ConfigError` (class): Raised when the TOML config is invalid.
- `_table` (function/method): Internal table helper shared by the owning module so workflows do not duplicate this function/method logic.
- `_optional_str` (function/method): Internal optional str helper shared by the owning module so workflows do not duplicate this function/method logic.
- `_positive_int` (function/method): Internal positive int helper shared by the owning module so workflows do not duplicate this function/method logic.
- `_stripped` (function/method): Internal stripped helper shared by the owning module so workflows do not duplicate this function/method logic.
- `_bool` (function/method): Internal bool helper shared by the owning module so workflows do not duplicate this function/method logic.
- `_int` (function/method): Internal int helper shared by the owning module so workflows do not duplicate this function/method logic.
- `_as_str` (function/method): Internal as str helper shared by the owning module so workflows do not duplicate this function/method logic.
- `_as_path` (function/method): Internal as path helper shared by the owning module so workflows do not duplicate this function/method logic.
- `_as_bool` (function/method): Internal as bool helper shared by the owning module so workflows do not duplicate this function/method logic.
- `_as_int` (function/method): Internal as int helper shared by the owning module so workflows do not duplicate this function/method logic.
- `_string_list` (function/method): Internal string list helper shared by the owning module so workflows do not duplicate this function/method logic.
- `load_config` (function/method): Read and validate TOML config.

### `destroy.py`
Destructive setup retirement using the shared Btrfs tree engine.
- `DestroyResult` (class): Named wrapper around the shared tree-deletion result.
- `DestroyResult.__getattr__` (function/method): Internal getattr helper shared by the owning module so workflows do not duplicate this function/method logic.
- `_safe_cleanup_path` (function/method): Internal safe cleanup path helper shared by the owning module so workflows do not duplicate this function/method logic.
- `_confirm_or_raise` (function/method): Internal confirm or raise helper shared by the owning module so workflows do not duplicate this function/method logic.
- `_mode_text` (function/method): Internal mode text helper shared by the owning module so workflows do not duplicate this function/method logic.
- `_load_payload_state` (function/method): Internal load payload state helper shared by the owning module so workflows do not duplicate this function/method logic.
- `_result_by_label` (function/method): Internal result by label helper shared by the owning module so workflows do not duplicate this function/method logic.
- `_print_payload_match` (function/method): Internal print payload match helper shared by the owning module so workflows do not duplicate this function/method logic.
- `_print_result` (function/method): Internal print result helper shared by the owning module so workflows do not duplicate this function/method logic.
- `destroy_leftovers` (function/method): Plan and execute selected source/destination tree retirement.
- `destroy_leftovers.handle` (function/method): Perform handle for the owning module's workflow boundary.

### `endpoint.py`
Unified command endpoints for local and source-side operations.
- `CommandEndpoint` (class): Execute commands on one local or source-side endpoint.
- `CommandEndpoint.for_source` (function/method): Perform for source for the owning module's workflow boundary.
- `CommandEndpoint.local` (function/method): Perform local for the owning module's workflow boundary.
- `CommandEndpoint.location` (property): Expose the calculated location value without duplicating it at call sites.
- `CommandEndpoint.shell_command` (function/method): Return a safely quoted shell command for this endpoint.
- `CommandEndpoint.command` (function/method): Return process argv for a command executed on this endpoint.
- `CommandEndpoint.run_argv` (function/method): Execute one argv command through the endpoint transport.
- `CommandEndpoint.run_shell` (function/method): Execute one shell script through the endpoint transport.

### `executor.py`
Generic ordered workflow action executor.
- `WorkflowExecutor` (class): Execute or preview a plan using one handler per action kind.
- `WorkflowExecutor.execute` (function/method): Perform execute for the owning module's workflow boundary.

### `inventory.py`
Per-run Btrfs subvolume indexes for fewer SSH calls.
- `BtrfsIndex` (class): In-memory index of Btrfs subvolumes below one root path.
- `BtrfsIndex.add` (function/method): Add or replace one indexed subvolume.
- `BtrfsIndex.discard` (function/method): Remove one path and any known UUID lookup entries for it.
- `BtrfsIndex.contains` (function/method): Return True when ``path`` is an indexed subvolume.
- `BtrfsIndex.meta` (function/method): Return metadata for ``path`` if it was indexed.
- `BtrfsIndex.child_paths` (function/method): Return indexed descendants below ``path``.
- `BtrfsIndex.is_empty` (function/method): Return whether an indexed path has indexed child subvolumes.
- `BtrfsIndex.remove_tree` (function/method): Remove a deleted path and all indexed descendants.
- `SourceInventory` (class): One coherent source-side Timeshift/Btrfs inventory.
- `SourceInventory.snapshot_names` (property): Return Timeshift timestamp names in sorted order.
- `SourceInventory.meta` (function/method): Return source metadata from cache first, then snapshot-root index.
- `SourceInventory.info_json` (function/method): Return captured Timeshift ``info.json`` content for one snapshot.
- `_clean_uuid` (function/method): Normalize Btrfs UUID fields from list/show output.
- `parse_subvolume_list` (function/method): Parse ``btrfs subvolume list -u -q -R`` output for one root.
- `_paths_from_list_output` (function/method): Return absolute subvolume paths parsed from any ``btrfs subvolume list`` output.
- `_mark_readonly_from_list` (function/method): Mark indexed paths read-only using one ``btrfs subvolume list -r`` result.
- `build_local_btrfs_index` (function/method): Build a local Btrfs index with bulk list commands.
- `_remote_bulk_index_script` (function/method): Return a POSIX shell script that bulk-lists source Btrfs metadata.
- `build_source_btrfs_index` (function/method): Build a source Btrfs index in SSH or local mode.
- `build_remote_btrfs_index` (function/method): Build a remote source index using one SSH command.
- `_parse_remote_btrfs_index_result` (function/method): Parse one remote bulk-index section into a :class:`BtrfsIndex`.
- `_parse_remote_btrfs_index_result.flush_list` (function/method): Perform flush list for the owning module's workflow boundary.
- `_parse_remote_btrfs_index_result.flush_readonly` (function/method): Perform flush readonly for the owning module's workflow boundary.
- `_remote_source_inventory_script` (function/method): Return one remote script for Timeshift, info.json, and both Btrfs roots.
- `_extract_snapshot_info_json_frames` (function/method): Remove and parse the ``cat`` payloads from combined SSH output.
- `_extract_snapshot_info_json_frames.replace` (function/method): Perform replace for the owning module's workflow boundary.
- `_split_remote_source_inventory_output` (function/method): Split combined output into identity, Timeshift, info.json, and Btrfs sections.
- `_current_process_identity` (function/method): Return the effective local account name and UID used to read metadata.
- `_read_local_snapshot_info_json` (function/method): Read all local Timeshift control files without spawning commands.
- `_record_missing_info_json_errors` (function/method): Record listed Timeshift dates that had no readable control file.
- `build_source_inventory` (function/method): Build one coherent Timeshift/snapshot/cache source inventory.
- `describe_source_inventory_changes` (function/method): Return concise human-readable differences between two inventories.
- `describe_source_inventory_changes.compare_index` (function/method): Perform compare index for the owning module's workflow boundary.
- `refresh_path` (function/method): Refresh one exact path through the shared Btrfs operation layer.

### `lock.py`
Simple file lock for sync/prune commands.
- `FileLock` (class): flock() based non-blocking exclusive lock.
- `FileLock.__init__` (function/method): Internal init helper shared by the owning module so workflows do not duplicate this function/method logic.
- `FileLock.__enter__` (function/method): Internal enter helper shared by the owning module so workflows do not duplicate this function/method logic.
- `FileLock.__exit__` (function/method): Internal exit helper shared by the owning module so workflows do not duplicate this function/method logic.

### `log.py`
Split run logging for timeshift-btrfs-sync.
- `RunLogger` (class): Owns the split log files for one run.
- `RunLogger.__post_init__` (function/method): Create the log directory and open the run log files.
- `RunLogger.close` (function/method): Close all log files.
- `RunLogger.attachment_paths` (function/method): Return run log files in the order useful for mail attachments.
- `RunLogger._write` (function/method): Write text safely from possible stream-reader threads.
- `RunLogger._remember_stderr` (function/method): Keep a small tail of stderr for failure notifications.
- `RunLogger.last_stderr_tail` (function/method): Return the newest stderr text remembered for MQTT/error reports.
- `RunLogger._line` (function/method): Write exactly one logical line.
- `RunLogger.info` (function/method): Write a normal status line to .log.
- `RunLogger.mbuffer` (function/method): Write one line to the .mbuffer transfer-progress log.
- `RunLogger.btrfs_out` (function/method): Write one line to the .btrfs Btrfs verbose-output log.
- `RunLogger.success` (function/method): Write one line to the .succes human-readable summary log.
- `RunLogger.success_text` (function/method): Write a preformatted block to the .succes summary log.
- `RunLogger.err` (function/method): Write an error/stderr line to .err and remember its tail.
- `RunLogger.command` (function/method): Record a command that is about to run.
- `RunLogger.completed` (function/method): Record the output from a normal captured command.
- `RunLogger.pipeline_commands` (function/method): Record send/buffer/receive commands to the appropriate logs.
- `RunLogger.pipeline_summary` (function/method): Record final pipeline status.
- `RunLogger.stream_text` (function/method): Write live pipeline text to terminal and/or split log files.
- `emit_success_summary` (function/method): Write a readable summary to the real terminal and .succes only.
- `TeeTextIO` (class): Terminal stream wrapper that also writes normal app output to run logs.
- `TeeTextIO.__init__` (function/method): Internal init helper shared by the owning module so workflows do not duplicate this function/method logic.
- `TeeTextIO.write` (function/method): Perform write for the owning module's workflow boundary.
- `TeeTextIO.flush` (function/method): Perform flush for the owning module's workflow boundary.
- `TeeTextIO.isatty` (function/method): Perform isatty for the owning module's workflow boundary.
- `TeeTextIO.fileno` (function/method): Perform fileno for the owning module's workflow boundary.
- `TeeTextIO.writable` (function/method): Perform writable for the owning module's workflow boundary.
- `TeeTextIO.__getattr__` (function/method): Internal getattr helper shared by the owning module so workflows do not duplicate this function/method logic.
- `terminal_stdout` (function/method): Return the real terminal stdout, bypassing the run-log tee wrapper.
- `terminal_stderr` (function/method): Return the real terminal stderr, bypassing the run-log tee wrapper.
- `get_logger` (function/method): Return the active logger, if file logging is enabled.
- `active_logger` (function/method): Temporarily install a run logger and tee app output to files.
- `create_run_logger` (function/method): Create a logger when log_dir is configured; otherwise return None.
- `tee_pipe_to_log` (function/method): Start a thread that reads bytes from a process pipe and logs them live.
- `tee_pipe_to_log._reader` (function/method): Internal reader helper shared by the owning module so workflows do not duplicate this function/method logic.

### `mail.py`
Optional email notifications for timeshift-btrfs-sync.
- `MailConfig` (class): SMTP settings for optional email notifications.
- `MailConfig.resolved_password` (function/method): Return password from config value or password_file.
- `_subject` (function/method): Create a short readable subject line.
- `_body` (function/method): Create a fallback plain-text email body from the status payload.
- `_success_body_from_paths` (function/method): Return the text content of the non-empty .succes file, if present.
- `_filter_attachments` (function/method): Return existing attachment paths and human-readable skipped reasons.
- `_attach_file` (function/method): Attach one file to an EmailMessage.
- `send_status` (function/method): Send one optional SMTP status email.

### `maintenance.py`
Guarded maintenance commands for state and lock files.
- `MaintenanceResult` (class): Structured result for one maintenance-file operation.
- `_confirm_or_raise` (function/method): Require an exact typed confirmation before destructive maintenance.
- `_safe_configured_file` (function/method): Return a normalized configured file path or raise for unsafe targets.
- `_looks_like_state_file` (function/method): Return True when an existing file appears to be ts-btrfs state.
- `_looks_like_lock_file` (function/method): Return True when an existing file looks like this app's simple lock file.
- `_print_header` (function/method): Print the common maintenance command warning block.
- `_require_real_confirmation` (function/method): Require real-mode flags and typed confirmations.
- `clear_state_file` (function/method): Remove the configured state.json file after explicit confirmation.
- `delete_lock_file` (function/method): Delete the configured lock file when no running process holds it.

### `models.py`
Shared dataclasses for snapshots and subvolumes.
- `SubvolumeMeta` (class): Metadata for one Btrfs subvolume inside one Timeshift snapshot.
- `SnapshotMeta` (class): Metadata for one Timeshift snapshot.
- `SnapshotMeta.sort_key` (function/method): Timeshift timestamp names sort oldest-to-newest lexically.
- `tags_text` (function/method): Return compact human text for Timeshift tags.

### `mqtt.py`
Optional MQTT notifications for timeshift-btrfs-sync.
- `MQTTConfig` (class): MQTT broker and publish settings.
- `MQTTConfig.resolved_password` (function/method): Return password from config value or password_file.
- `publish_status` (function/method): Publish one JSON MQTT status message.

### `notify.py`
Shared notification payload helpers.
- `utc_timestamp` (function/method): Return a compact ISO-8601 UTC timestamp for notifications.
- `build_notification_payload` (function/method): Build the shared status payload used by MQTT and email.

### `paths.py`
Canonical path normalization and containment rules.
- `normalize_source_path` (function/method): Normalize POSIX path text while preserving an intentionally empty value.
- `is_same_or_under` (function/method): Return true when ``path`` equals ``root`` or is below it.
- `is_local_same_or_under` (function/method): Return true when one local path resolves to ``root`` or below it.
- `is_under` (function/method): Return true only when ``path`` is strictly below ``root``.
- `listed_path_to_absolute` (function/method): Resolve a Btrfs filesystem-relative list path below a mounted root.
- `sort_deepest_first` (function/method): Deduplicate and order paths for child-before-parent deletion.

### `payload_stats.py`
Normalized source/destination payload statistics for Btrfs snapshot trees.
- `PayloadTreeStats` (class): Normalized payload/container counts for one source or destination tree.
- `PayloadTreeStats.total_payload` (property): Return the number of real cached/received payload subvolumes.
- `PayloadTreeStats.total_cache_payload` (property): Return how many source payloads came from app-owned source cache.
- `PayloadTreeStats.total_direct_payload` (property): Return how many source payloads came from protected Timeshift originals.
- `normalize_path` (function/method): Normalize paths so source/destination comparisons ignore trailing slashes.
- `_relative_parts` (function/method): Return path parts relative to root, or None if path is outside root.
- `_recount_payload` (function/method): Rebuild per-subvolume counters from the normalized payload set.
- `_add_payload` (function/method): Add a payload entry when relative parts end in a configured subvolume name.
- `source_send_cache_stats` (function/method): Classify source send-cache subvolumes into payload and helper counts.
- `destination_payload_stats` (function/method): Classify destination target subvolumes into received payload counts.
- `direct_send_payload_stats` (function/method): Return payload entries streamed directly from protected Timeshift originals.
- `merge_source_payload_stats` (function/method): Merge app-cache and protected direct-send payload into one source view.
- `PayloadMatchStats` (class): Comparison between source send payload and destination received payload.
- `PayloadMatchStats.source_only` (property): Return source payload entries not present on the destination.
- `PayloadMatchStats.destination_only` (property): Return destination payload entries not present on the source side.
- `PayloadMatchStats.ok` (property): Return True when source send payload and destination payload match.
- `compare_payloads` (function/method): Return normalized source/destination payload comparison stats.
- `_format_count_line` (function/method): Return an aligned summary line.
- `render_payload_match` (function/method): Render the source/destination payload comparison block.

### `planning.py`
Pure workflow planning from a combined backup inventory.
- `ActionKind` (class): Shared ActionKind model or service used as the single representation for this responsibility.
- `WorkflowAction` (class): Shared WorkflowAction model or service used as the single representation for this responsibility.
- `WorkflowPlan` (class): Shared WorkflowPlan model or service used as the single representation for this responsibility.
- `WorkflowPlan.add` (function/method): Perform add for the owning module's workflow boundary.
- `plan_sync_queue` (function/method): Plan the oldest-to-newest sync queue without executing operations.
- `plan_snapshot_recovery` (function/method): Plan one whole-date recovery in cache, destination, then state order.
- `plan_prune_snapshot` (function/method): Perform plan prune snapshot for the owning module's workflow boundary.
- `plan_destroy_targets` (function/method): Plan named endpoint/root destruction in the caller-provided order.

### `preflight.py`
Sync path preflight checks.
- `PathPreflightError` (class): Raised before any destructive/creating sync work when required paths fail.
- `PathCheck` (class): One configured path availability result.
- `_shell_words` (function/method): Return a shell-safe string for configured command-prefix words.
- `_parse_path_check_output` (function/method): Parse source-path preflight sentinel lines into structured checks.
- `_source_snapshot_root_script` (function/method): Build a source script that validates Timeshift-owned source.snapshot_root.
- `_cache_root_check_script` (function/method): Build a source script that validates or creates source.cache_root.
- `_combined_source_path_check_script` (function/method): Run both source-root preflight checks inside one source command.
- `_source_path_checks` (function/method): Check/create both source roots with at most one SSH command.
- `_parent_of_path` (function/method): Return the immediate parent path used for exact-path creation checks.
- `_local_btrfs_result` (function/method): Run one local destination sudo+btrfs command for preflight checks.
- `_compact_process_error` (function/method): Return compact stderr/stdout text from a failed subprocess.
- `_compact_os_error` (function/method): Return compact text for local filesystem creation errors.
- `_print_check_block` (function/method): Print one human-readable preflight result block.
- `_raise_for_failed_checks` (function/method): Raise a hard preflight error when any check failed.
- `ensure_local_helper_dir` (function/method): Ensure one local helper directory exists.
- `prepare_lock_path` (function/method): Create/verify the lock directory before other sync/prune directories.
- `prepare_destination_helper_paths` (function/method): Create/verify local destination helper folders used by sync/prune.
- `_local_target_path_check` (function/method): Check/create destination.target_root locally.
- `check_required_sync_paths` (function/method): Verify/create required configured roots before manual snapshot creation or send.

### `remote_index.py`
Compatibility facade for the single authoritative :mod:`inventory` module.
- Contains no independent runtime class/function implementation; it provides metadata, entry-point wiring, or compatibility exports.

### `retention.py`
Destination retention/pruning logic.
- `PrunePlan` (class): Dry-run friendly prune plan.
- `PrunePlan.add_keep` (function/method): Mark a snapshot as kept and remember the human reason.
- `PrunePlan.add_delete` (function/method): Mark a snapshot as deletable only when it is not already protected.
- `_is_app_created_ondemand` (function/method): Return true when a state entry is a tag O snapshot with the app marker.
- `_delete_reason_for_snapshot` (function/method): Explain why a snapshot is outside the active retention rules.
- `_delete_reasons` (function/method): Return delete reasons without the internal prefix.
- `_source_cache_delete_paths` (function/method): Return app-owned source send-cache paths for a prune decision.
- `_protected_timeshift_send_paths` (function/method): Return direct Timeshift send paths that prune must never delete.
- `_destination_delete_paths` (function/method): Return tracked destination subvolume paths for a prune decision.
- `source_snapshot_state` (function/method): Return temporary state-like data from source Timeshift snapshots.
- `initial_sync_keep_names` (function/method): Return source snapshot names that a fresh destination should seed.
- `_cleanup_source_cache_for_pruned_snapshot` (function/method): Delete one pruned snapshot's app-owned cache through the shared tree engine.
- `build_prune_plan` (function/method): Build retention plan from state without deleting anything.
- `_delete_destination_snapshot_for_prune` (function/method): Delete one destination date through the shared tree engine.
- `_delete_prune_item` (function/method): Execute one pure prune plan and remove state after both trees are gone.
- `_delete_prune_item.delete_destination` (function/method): Perform delete destination for the owning module's workflow boundary.
- `_delete_prune_item.delete_cache` (function/method): Perform delete cache for the owning module's workflow boundary.
- `_delete_prune_item.remove_state` (function/method): Perform remove state for the owning module's workflow boundary.
- `print_prune_plan` (function/method): Write an easy-to-read retention summary to terminal and .succes.
- `prune` (function/method): Apply destination retention rules.

### `snapshot_records.py`
Combined per-snapshot view used by every workflow planner.
- `SnapshotRecord` (class): All known source/cache/destination/state data for one snapshot date.
- `SnapshotRecord.source_meta` (function/method): Perform source meta for the owning module's workflow boundary.
- `BackupInventory` (class): Coherent source/cache/destination/state view keyed by snapshot date.
- `BackupInventory.get` (function/method): Perform get for the owning module's workflow boundary.
- `_indexed_children` (function/method): Internal indexed children helper shared by the owning module so workflows do not duplicate this function/method logic.
- `build_backup_inventory` (function/method): Build one combined record set from already-collected bulk inventories.

### `source.py`
Source command runner for SSH and local source modes.
- `SourceRunner` (class): Run source-side commands either over SSH or locally.
- `SourceRunner.from_config` (function/method): Create a source runner from validated app config.
- `SourceRunner.uses_ssh` (property): Return True when source commands are executed through SSH.
- `SourceRunner.location` (property): Return the metadata location label used by Btrfs helpers.
- `SourceRunner.display_location` (property): Return human text for source status output.
- `SourceRunner.command` (function/method): Return argv that runs one source-side shell command.
- `SourceRunner.run` (function/method): Run one source-side command and capture stdout/stderr.
- `SourceRunner.environment` (function/method): Return environment needed for streaming source commands.
- `SourceRunner.test` (function/method): Verify that the source command endpoint is usable.

### `ssh.py`
SSH command construction.
- `_is_relative_to` (function/method): Return True when path is root or below root without broad string matching.
- `validate_control_path_safety` (function/method): Create and validate a private SSH ControlPath socket directory.
- `SSHConfig` (class): Connection and SSH transport settings.
- `SSHConfig.target` (property): Return host or user@host.
- `SSHConfig.uses_password_auth` (property): Return True when sshpass is needed.
- `SSHConfig._read_password` (function/method): Read password from TOML or password_file.
- `SSHConfig.environment` (function/method): Return environment variables required by sshpass.
- `SSHConfig.base_command` (function/method): Build base SSH argv; remote command is appended later.
- `SSHRunner` (class): Run remote commands through SSH.
- `SSHRunner.__init__` (function/method): Internal init helper shared by the owning module so workflows do not duplicate this function/method logic.
- `SSHRunner.command` (function/method): Return argv for one SSH remote command.
- `SSHRunner.run` (function/method): Run a remote command and capture stdout/stderr.
- `SSHRunner.environment` (function/method): Return SSH environment for streaming pipeline calls.
- `SSHRunner.test` (function/method): Verify SSH works and stdout is not polluted by banners.

### `state.py`
Persistent local state for completed transfers.
- `empty_state` (function/method): Return a new empty state document.
- `_safe_relative_path` (function/method): Return a normalized destination-relative path or raise ValueError.
- `_safe_source_relative_path` (function/method): Return a normalized safe POSIX path relative to a configured source root.
- `_normalize_source_root` (function/method): Return one normalized absolute-style POSIX source root.
- `_source_path_relative_to_root` (function/method): Return ``path`` relative to ``root`` when it is currently below that root.
- `_expected_snapshot_relative_path` (function/method): Return the canonical ``<snapshot>/<subvolume>`` source-relative path.
- `_absolute_source_path_ends_with` (function/method): Return True when an old absolute source path has the expected suffix.
- `source_path_to_relative` (function/method): Convert a source-side state path to a configured-root-relative string.
- `resolve_source_path` (function/method): Resolve one source-root-relative state path under the current source root.
- `destination_path_to_relative` (function/method): Convert a destination subvolume path to a target_root-relative string.
- `resolve_destination_path` (function/method): Resolve a state destination_path against the current target_root.
- `send_path_kind_for_state_subvolume` (function/method): Return the safe ownership/root kind for a stored ``send_path``.
- `_source_root_for_kind` (function/method): Return the configured source root used by one stored send-path kind.
- `resolve_state_source_path` (function/method): Resolve stored ``source_path`` under the current snapshot_root.
- `resolve_state_send_path` (function/method): Resolve stored ``send_path`` under its current configured source root.
- `resolve_state_parent_source_path` (function/method): Resolve stored ``parent_source_path`` under its recorded current root.
- `normalize_destination_paths` (function/method): Normalize in-memory destination paths to target_root-relative values.
- `normalize_source_paths` (function/method): Normalize all source-side state paths to configured-root-relative values.
- `normalize_state_paths` (function/method): Normalize destination and source paths in one loaded state document.
- `load_state` (function/method): Load state.json, migrate known paths in memory, or return empty state.
- `save_state` (function/method): Atomically write state.json.
- `refresh_snapshot_metadata_from_source` (function/method): Refresh mutable Timeshift metadata for already-known snapshots.
- `snapshot_is_synced` (function/method): Return True when a snapshot is recorded as fully synced.
- `_kind_for_absolute_source_path` (function/method): Classify a current absolute source path by configured ownership root.
- `mark_subvolume_synced` (function/method): Record one successful send/receive using only root-relative state paths.
- `state_send_path_is_app_cache` (function/method): Return True only when prune may delete the stored send_path.
- `state_send_path_is_protected_timeshift_original` (function/method): Return True when the stored send_path belongs to Timeshift, not the app.
- `remove_snapshot_from_state` (function/method): Remove a pruned snapshot from state.
- `refresh_state_metadata_and_report` (function/method): Refresh only Timeshift tags/comment/created/path, report, and save.
- `latest_synced_before` (function/method): Return newest older synced parent candidate.

### `sync.py`
Main destination-pull sync workflow.
- `SyncError` (class): Raised for sync safety errors.
- `_local_meta` (function/method): Internal local meta helper shared by the owning module so workflows do not duplicate this function/method logic.
- `_source_meta` (function/method): Return source metadata, preferring bulk indexes over one-off probes.
- `_human_blank` (function/method): Print one blank line to separate human-readable status blocks.
- `_human_rule` (function/method): Print a visual separator with blank lines around it.
- `_record_sync_event` (function/method): Add one planned or completed transfer to the run summary.
- `_print_sync_summary` (function/method): Write a terminal-friendly transfer summary to terminal and .succes.
- `prepare_destination` (function/method): Create/validate destination helper folders before writes.
- `list_source_snapshots` (function/method): Discover source Timeshift snapshots.
- `source_snapshot_index` (function/method): Perform source snapshot index for the owning module's workflow boundary.
- `_snapshots_from_source_inventory` (function/method): Build Timeshift snapshot objects from one coherent source inventory.
- `_required_pipeline_source_changes` (function/method): Return identity changes to source paths required by current work.
- `confirm_source_identity_before_manual_snapshot` (function/method): Print and enforce the shared manual-snapshot source identity guard.
- `_is_app_manual_snapshot` (function/method): Return True for source Timeshift O snapshots created by this app.
- `_pending_app_manual_snapshots` (function/method): Return app-created on-demand snapshots that still need syncing.
- `_maybe_create_manual_snapshot` (function/method): Optionally create a source Timeshift tag O snapshot before sync.
- `_snapshots_in_sync_order` (function/method): Return source snapshots oldest-to-newest for Btrfs send.
- `_select_initial_sync_snapshots` (function/method): Return retention-kept source snapshots for a fresh destination seed.
- `print_snapshot_table` (function/method): Print source snapshots in table form.
- `_dest_subvolume_path` (function/method): Return the final local path for one received subvolume.
- `_target_snapshot_dir` (function/method): Return the managed destination date subvolume passed to `btrfs receive`.
- `_destination_info_json_path` (function/method): Return the destination Timeshift control-file path for one snapshot.
- `_ensure_destination_snapshot_subvolume` (function/method): Create or validate one managed destination date subvolume.
- `_validate_destination_snapshot_layout` (function/method): Refuse every existing ordinary/symlinked destination date entry.
- `_atomic_write_snapshot_info_json` (function/method): Atomically write one captured Timeshift ``info.json`` file.
- `_require_snapshot_info_json` (function/method): Return captured control-file content or raise a precise sync error.
- `_sync_snapshot_info_json` (function/method): Create or refresh destination ``info.json`` for one complete snapshot.
- `_destination_has_existing_snapshots` (function/method): Return True when the destination has real received snapshot content.
- `_snapshot_destination_paths_exist` (function/method): Return True only when every expected destination subvolume path exists.
- `_preview_send_path` (function/method): Return the send path that would be used, without creating cache snapshots.
- `_send_path_kind_text` (function/method): Return human text explaining who owns the selected send path.
- `_ensure_source_send_path` (function/method): Resolve one real send path through the shared cache operation.
- `_cleanup_incomplete_destination_receive` (function/method): Delete one exact incomplete destination Btrfs child before retrying.
- `_cleanup_source_cache_snapshot_version` (function/method): Delete one app-owned cache date through the shared tree engine.
- `_cleanup_destination_snapshot_version` (function/method): Delete one destination date through the shared tree engine.
- `_refresh_snapshot_source_subvolumes_live` (function/method): Return configured source subvolumes, preferring the bulk index.
- `_snapshot_destination_has_any_path` (function/method): Return True when the destination date folder or configured children exist.
- `_snapshot_state_is_complete_with_destination` (function/method): Return True only when state and destination contain every configured subvolume.
- `_recover_snapshot_version` (function/method): Remove stale current-version traces from cache, destination, and state.
- `_recover_snapshot_version.handle` (function/method): Perform handle for the owning module's workflow boundary.
- `_prepare_snapshot_for_transfer_or_recover` (function/method): Return True when a snapshot can be transferred, False when skipped.
- `_recover_stale_state_snapshots_missing_from_source` (function/method): Clean incomplete state entries whose Timeshift source name is gone.
- `_read_local_destination_parent_metadata` (function/method): Read metadata for the destination snapshot that would be the receiver parent.
- `_match_source_path_to_destination_received_uuid` (function/method): Check whether a source subvolume UUID matches the destination identity.
- `_select_verified_parent_send_path` (function/method): Select a safe source parent path for incremental send without recreating it.
- `_select_verified_parent_send_path.add_candidate` (function/method): Perform add candidate for the owning module's workflow boundary.
- `_state_uuid_values_for_path` (function/method): Return UUID values that may safely identify the source path.
- `_state_uuid_values_for_path.add_key` (function/method): Perform add key for the owning module's workflow boundary.
- `_find_confirmed_sync_floor` (function/method): Return newest state snapshot that still exists on source and matches UUIDs.
- `_destination_snapshot_names` (function/method): Return destination snapshot folder names sorted oldest-to-newest.
- `_expected_original_source_path` (function/method): Return the Timeshift-owned original source path for one snapshot/subvolume.
- `_source_cache_meta_by_uuid` (function/method): Return coherent indexed source-cache metadata for an exact UUID match.
- `_match_existing_destination_to_source` (function/method): Match one existing destination subvolume to an exact source/cache UUID.
- `_recover_state_from_existing_destination` (function/method): Rebuild missing/empty state.json from proven source/destination matches.
- `_filesystem_parent_candidates` (function/method): Find local destination parent candidates by matching snapshot names.
- `_select_parent` (function/method): Choose the newest valid incremental parent.
- `_verify_sync_viability_before_manual_snapshot` (function/method): Prove sync can start before asking Timeshift to create a snapshot.
- `_verify_sync_viability_before_manual_snapshot.verify_parent_for` (function/method): Perform verify parent for for the owning module's workflow boundary.
- `sync_once` (function/method): Run one sync pass.
- `sync_once.load_source_inventory` (function/method): Build and report one coherent source inventory generation.
- `sync_once.build_snapshot_queue` (function/method): Build one pure oldest-to-newest sync plan, then return its snapshot queue.
- `sync_once.recover_from_source_inventory_change` (function/method): Recover one failed snapshot version and rebuild all source lists.

### `timeshift.py`
Timeshift command wrappers and parser for `timeshift --list`.
- `timeshift_cmd` (function/method): Build a source-side shell command that invokes sudo+timeshift.
- `normalize_tags` (function/method): Return unique Timeshift tag letters found in text.
- `parse_timeshift_list` (function/method): Parse Timeshift snapshot names and tag/comment text.
- `list_source_snapshots` (function/method): Discover source snapshots through SSH or local source commands.
- `list_remote_snapshots` (function/method): Discover source snapshots using only sudo timeshift and sudo btrfs.
- `create_remote_manual_snapshot_cmd` (function/method): Build the Timeshift manual/on-demand snapshot create command.
- `create_source_manual_snapshot` (function/method): Create a source Timeshift on-demand snapshot through SSH or locally.
- `create_remote_manual_snapshot` (function/method): Create a Timeshift on-demand snapshot.

### `tree_ops.py`
Single Btrfs tree discovery, deletion, and post-verification engine.
- `TreeDeleteResult` (class): Shared TreeDeleteResult model or service used as the single representation for this responsibility.
- `TreeDeleteResult.success` (property): Expose the calculated success value without duplicating it at call sites.
- `TreeDeleteResult.path` (property): Expose the calculated path value without duplicating it at call sites.
- `TreeDeleteResult.location` (property): Expose the calculated location value without duplicating it at call sites.
- `TreeDeleteResult.subvolumes` (property): Expose the calculated subvolumes value without duplicating it at call sites.
- `TreeDeleteResult.deleted_subvolumes` (property): Expose the calculated deleted subvolumes value without duplicating it at call sites.
- `TreeDeleteResult.remaining_subvolumes` (property): Expose the calculated remaining subvolumes value without duplicating it at call sites.
- `TreeDeleteResult.exists` (property): Expose the calculated exists value without duplicating it at call sites.
- `_path_exists` (function/method): Internal path exists helper shared by the owning module so workflows do not duplicate this function/method logic.
- `discover_subvolume_tree` (function/method): Discover one Btrfs tree once and return deepest-first paths plus errors.
- `list_direct_entries` (function/method): List exact direct children with shell built-ins on either endpoint.
- `_validate_confirmations` (function/method): Internal validate confirmations helper shared by the owning module so workflows do not duplicate this function/method logic.
- `_verify_absent` (function/method): Internal verify absent helper shared by the owning module so workflows do not duplicate this function/method logic.
- `delete_subvolume_tree` (function/method): Delete one managed tree deepest-first and prove the root is absent.

