# Commented code map

This map describes every current runtime/build class, function, method, property, and CLI command. Each entry states what the symbol does and why that responsibility is kept there. It is generated from the current source tree so line numbers and symbol coverage match this release.

## `scripts/build_pyinstaller.py`

**Module role:** Build ts-btrfs executables with PyInstaller. 

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `build_args` (function, line 23): Return the PyInstaller argument list for one build mode. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `run_pyinstaller` (function, line 50): Run PyInstaller with a useful error if it is not installed. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `main` (function, line 66): Parse arguments and run the requested build. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

## `tools/pyinstaller_entry.py`

**Module role:** Small PyInstaller entry point for building the ts-btrfs executable. 

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

No runtime classes or functions are defined in this file.

## `timeshift_btrfs_sync/__init__.py`

**Module role:** Timeshift Btrfs sync package.

**Why this module exists:** Provides the package entry surface without duplicating workflow logic.

No runtime classes or functions are defined in this file.

## `timeshift_btrfs_sync/__main__.py`

**Module role:** Run the CLI with: python -m timeshift_btrfs_sync.

**Why this module exists:** Provides the package entry surface without duplicating workflow logic.

No runtime classes or functions are defined in this file.

## `timeshift_btrfs_sync/btrfs_ops.py`

**Module role:** Reusable Btrfs operations independent of workflow order. 

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_ListedSubvolume` (class, line 24): One numeric containment record from ``btrfs subvolume list -a -p``. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_parse_listed_subvolumes` (function, line 32): Parse numeric ID, containing-parent ID, and raw path fields. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_descendant_list_paths` (function, line 56): Return only numeric descendants of ``root_id`` from one full list. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `clean_uuid` (function, line 73): Return or perform clean uuid. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `parse_subvolume_show` (function, line 78): Parse UUID and read-only fields from ``btrfs subvolume show``. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `BtrfsOps` (class, line 104): Btrfs command facade for one local or source endpoint. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `BtrfsOps.prefix` (property, line 112): Return or perform prefix. **Why:** Keeps this operation inside `BtrfsOps` so callers use the class endpoint, state, and validation rules.

- `BtrfsOps.argv` (method, line 115): Return or perform argv. **Why:** Keeps this operation inside `BtrfsOps` so callers use the class endpoint, state, and validation rules.

- `BtrfsOps.run` (method, line 118): Return or perform run. **Why:** Keeps this operation inside `BtrfsOps` so callers use the class endpoint, state, and validation rules.

- `BtrfsOps.meta` (method, line 133): Return exact-path subvolume metadata or ``None`` for an optional miss. **Why:** Keeps this operation inside `BtrfsOps` so callers use the class endpoint, state, and validation rules.

- `BtrfsOps.list_children` (method, line 152): Return all descendants selected from one Btrfs containment graph.  **Why:** Keeps this operation inside `BtrfsOps` so callers use the class endpoint, state, and validation rules.

- `BtrfsOps.create` (method, line 171): Return or perform create. **Why:** Keeps this operation inside `BtrfsOps` so callers use the class endpoint, state, and validation rules.

- `BtrfsOps.snapshot` (method, line 174): Create one exact writable or read-only Btrfs snapshot. **Why:** Keeps this operation inside `BtrfsOps` so callers use the class endpoint, state, and validation rules.

- `BtrfsOps.delete` (method, line 190): Return or perform delete. **Why:** Keeps this operation inside `BtrfsOps` so callers use the class endpoint, state, and validation rules.

- `BtrfsOps.send_command` (method, line 205): Return or perform send command. **Why:** Keeps this operation inside `BtrfsOps` so callers use the class endpoint, state, and validation rules.

- `BtrfsOps.receive_command` (method, line 226): Return or perform receive command. **Why:** Keeps this operation inside `BtrfsOps` so callers use the class endpoint, state, and validation rules.

- `BtrfsOps.set_readonly` (method, line 233): Set the Btrfs subvolume read-only property explicitly. **Why:** Keeps this operation inside `BtrfsOps` so callers use the class endpoint, state, and validation rules.

- `BtrfsOps.batch_delete` (method, line 238): Delete exact paths in one endpoint command and validate confirmations.  **Why:** Keeps this operation inside `BtrfsOps` so callers use the class endpoint, state, and validation rules.

## `timeshift_btrfs_sync/cache_ops.py`

**Module role:** Single source send-cache operation used by sync and recovery.

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_safe_name` (function, line 14): Return or perform safe name. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `cache_parent_path` (function, line 20): Return or perform cache parent path. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `cache_child_path` (function, line 24): Return or perform cache child path. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `validate_cache_snapshot` (function, line 28): Prove an exact cache child is a safe read-only snapshot of ``original``. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `CacheManager` (class, line 61): Ensure exact reusable send snapshots without nested cache creation. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `CacheManager.__init__` (method, line 64): Return or perform init. **Why:** Keeps this operation inside `CacheManager` so callers use the class endpoint, state, and validation rules.

- `CacheManager._ensure_subvolume` (method, line 69): Return or perform ensure subvolume. **Why:** Keeps this operation inside `CacheManager` so callers use the class endpoint, state, and validation rules.

- `CacheManager._probe_existing_from_parent` (method, line 96): Find one exact cache child from an authoritative parent-scoped list.  **Why:** Keeps this operation inside `CacheManager` so callers use the class endpoint, state, and validation rules.

- `CacheManager._probe_create_verify` (method, line 192): Probe, create if absent, and verify exact cache path in one command. **Why:** Keeps this operation inside `CacheManager` so callers use the class endpoint, state, and validation rules.

- `CacheManager.ensure_send_snapshot` (method, line 305): Return original read-only source or create/reuse one exact cache child. **Why:** Keeps this operation inside `CacheManager` so callers use the class endpoint, state, and validation rules.

## `timeshift_btrfs_sync/cli.py`

**Module role:** Command-line interface for timeshift-btrfs-sync.

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `new_subparser` (function, line 36): Return or perform new subparser. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `add_config_arg` (function, line 42): Return or perform add config arg. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `add_run_mode_args` (function, line 44): Return or perform add run mode args. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `add_yes_delete_arg` (function, line 50): Return or perform add yes delete arg. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_load_config_state` (function, line 54): Load state and resolve all root-relative paths against this config. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_failure_exit_code` (function, line 60): Return a stable CLI exit code for failure notifications.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_stderr_tail_for_exception` (function, line 76): Return the best available recent stderr text for failure notifications. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_send_notifications` (function, line 86): Send optional MQTT/email status without changing the command exit code. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_mail_attachment_paths` (function, line 126): Return current run log paths for optional email attachment. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_safe_destroy_log_dir` (function, line 136): Return a log directory that will survive a destructive cleanup.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_with_logging` (function, line 177): Run a command with optional logging and MQTT notification.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_resolve_dry_run` (function, line 226): Return or perform resolve dry run. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `cmd_init_config` (function, line 234): Return or perform cmd init config. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.
  - **CLI command `init-config`:** Parses that command’s intent and routes it into the shared workflow implementation.

- `cmd_test_source` (function, line 253): Return or perform cmd test source. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.
  - **CLI command `test-source`:** Parses that command’s intent and routes it into the shared workflow implementation.

- `_refresh_state_metadata_from_timeshift` (function, line 274): Refresh mutable state metadata from one fast Timeshift list read. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `cmd_list_source` (function, line 282): List snapshots on the source machine.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.
  - **CLI command `list-source`:** Parses that command’s intent and routes it into the shared workflow implementation.

- `cmd_sync` (function, line 305): Return or perform cmd sync. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.
  - **CLI command `sync`:** Parses that command’s intent and routes it into the shared workflow implementation.

- `cmd_prune` (function, line 345): Return or perform cmd prune. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.
  - **CLI command `prune`:** Parses that command’s intent and routes it into the shared workflow implementation.

- `cmd_restore` (function, line 374): Restore one snapshot or the complete post-common backup chain into Timeshift. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.
  - **CLI command `restore`:** Parses that command’s intent and routes it into the shared workflow implementation.

- `cmd_create_manual` (function, line 410): Return or perform cmd create manual. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.
  - **CLI command `create-manual`:** Parses that command’s intent and routes it into the shared workflow implementation.

- `cmd_clear_state` (function, line 439): Guardedly remove the configured state_file with normal run logging. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.
  - **CLI command `clear-state`:** Parses that command’s intent and routes it into the shared workflow implementation.

- `cmd_delete_lock` (function, line 467): Guardedly remove the configured lock_file if it is stale, with logging. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.
  - **CLI command `delete-lock`:** Parses that command’s intent and routes it into the shared workflow implementation.

- `cmd_destroy_leftovers` (function, line 484): Destroy configured leftovers with normal run logging enabled. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.
  - **CLI command `destroy-leftovers`:** Parses that command’s intent and routes it into the shared workflow implementation.

- `cmd_show_state` (function, line 510): Return or perform cmd show state. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.
  - **CLI command `show-state`:** Parses that command’s intent and routes it into the shared workflow implementation.

- `build_parser` (function, line 556): Create the argparse parser and command-specific flag help. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `main` (function, line 796): Return or perform main. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

## `timeshift_btrfs_sync/commands.py`

**Module role:** Shared subprocess helpers. 

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `CommandError` (class, line 21): Raised when an external command exits with a non-zero status. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `CommandError.__init__` (method, line 24): Return or perform init. **Why:** Keeps this operation inside `CommandError` so callers use the class endpoint, state, and validation rules.

- `Completed` (class, line 39): Captured exit status and text streams for one command. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `sudo_prefix` (function, line 47): Split a configured sudo prefix into argv parts. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `quote_join` (function, line 55): Quote argv parts into one safe remote-shell command string. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `remote_double_quote` (function, line 61): Return a shell-safe double-quoted argument for a remote shell command.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_merged_env` (function, line 84): Merge optional child-process environment variables. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `run_local` (function, line 94): Run a local command and capture stdout/stderr.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_start_pipeline_readers` (function, line 151): Start tee readers from compact stream routing specs. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_failed_stderr` (function, line 170): Return captured pipeline stderr for streams that belong in failures. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_log_failed_streams` (function, line 176): Copy captured failed pipeline streams to .err. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `stream_pipeline` (function, line 188): Stream left command into optional middle command, then right command.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

## `timeshift_btrfs_sync/config.py`

**Module role:** TOML configuration loading and validation.

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_reject_unknown_keys` (function, line 35): Reject configuration entries that are not part of the current schema. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `ManualSnapshotConfig` (class, line 43): Optional source-side Timeshift on-demand snapshot creation and cleanup. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `SourceConfig` (class, line 77): Timeshift source/restore-target paths that always share one endpoint. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `DestinationConfig` (class, line 120): Backup repository and normal local receive settings. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `StreamConfig` (class, line 134): Optional pipeline display/buffering settings.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `StreamConfig.command` (method, line 154): Return mbuffer command argv or None when disabled. **Why:** Keeps this operation inside `StreamConfig` so callers use the class endpoint, state, and validation rules.

- `RetentionConfig` (class, line 168): Destination retention counts by Timeshift tag. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `RetentionConfig.counts_by_tag` (method, line 187): Return retention counts keyed by Timeshift tag letters. **Why:** Keeps this operation inside `RetentionConfig` so callers use the class endpoint, state, and validation rules.

- `RestoreConfig` (class, line 193): Restore-only transport direction. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `RestoreConfig.backup_uses_ssh` (property, line 203): Return True when restore reads the backup repository over SSH. **Why:** Keeps this operation inside `RestoreConfig` so callers use the class endpoint, state, and validation rules.

- `RestoreConfig.timeshift_uses_ssh` (property, line 209): Return True when snapshot_root and cache_root are on the SSH Timeshift host. **Why:** Keeps this operation inside `RestoreConfig` so callers use the class endpoint, state, and validation rules.

- `AppConfig` (class, line 216): Complete validated app configuration. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `ConfigError` (class, line 235): Raised when the TOML config is invalid. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_table` (function, line 238): Return or perform table. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_optional_str` (function, line 244): Return or perform optional str. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_positive_int` (function, line 247): Return or perform positive int. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_stripped` (function, line 254): Return or perform stripped. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_bool` (function, line 257): Return or perform bool. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_int` (function, line 260): Return or perform int. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_as_str` (function, line 263): Return or perform as str. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_as_path` (function, line 268): Return or perform as path. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_as_bool` (function, line 271): Return or perform as bool. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_as_int` (function, line 278): Return or perform as int. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_string_list` (function, line 285): Return or perform string list. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `load_config` (function, line 293): Read and validate the current TOML configuration. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

## `timeshift_btrfs_sync/destroy.py`

**Module role:** Destructive setup retirement using the shared Btrfs tree engine.

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `DestroyResult` (class, line 26): Named wrapper around the shared tree-deletion result. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_safe_cleanup_path` (function, line 33): Return or perform safe cleanup path. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_confirm_or_raise` (function, line 46): Return or perform confirm or raise. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_mode_text` (function, line 51): Return or perform mode text. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_load_payload_state` (function, line 57): Return or perform load payload state. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_result_by_label` (function, line 64): Return or perform result by label. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_print_payload_match` (function, line 68): Return or perform print payload match. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_print_result` (function, line 87): Return or perform print result. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `destroy_leftovers` (function, line 118): Plan and execute selected source/destination tree retirement. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

## `timeshift_btrfs_sync/endpoint.py`

**Module role:** Unified command endpoints for local, Timeshift, and backup operations. 

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `CommandEndpoint` (class, line 19): Execute commands on one local or transported endpoint.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `CommandEndpoint.for_source` (method, line 30): Return or perform for source. **Why:** Keeps this operation inside `CommandEndpoint` so callers use the class endpoint, state, and validation rules.

- `CommandEndpoint.local` (method, line 34): Return or perform local. **Why:** Keeps this operation inside `CommandEndpoint` so callers use the class endpoint, state, and validation rules.

- `CommandEndpoint.location` (property, line 38): Return or perform location. **Why:** Keeps this operation inside `CommandEndpoint` so callers use the class endpoint, state, and validation rules.

- `CommandEndpoint.shell_command` (method, line 41): Return a safely quoted shell command for this endpoint. **Why:** Keeps this operation inside `CommandEndpoint` so callers use the class endpoint, state, and validation rules.

- `CommandEndpoint.command` (method, line 46): Return process argv for a command executed on this endpoint. **Why:** Keeps this operation inside `CommandEndpoint` so callers use the class endpoint, state, and validation rules.

- `CommandEndpoint.run_argv` (method, line 54): Execute one argv command through the endpoint transport. **Why:** Keeps this operation inside `CommandEndpoint` so callers use the class endpoint, state, and validation rules.

- `CommandEndpoint.run_shell` (method, line 82): Execute one shell script through the endpoint transport. **Why:** Keeps this operation inside `CommandEndpoint` so callers use the class endpoint, state, and validation rules.

## `timeshift_btrfs_sync/executor.py`

**Module role:** Generic ordered workflow action executor.

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `WorkflowExecutor` (class, line 14): Execute or preview a plan using one handler per action kind. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `WorkflowExecutor.execute` (method, line 22): Return or perform execute. **Why:** Keeps this operation inside `WorkflowExecutor` so callers use the class endpoint, state, and validation rules.

## `timeshift_btrfs_sync/inventory.py`

**Module role:** Per-run Btrfs subvolume indexes for fewer SSH calls. 

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `BtrfsIndex` (class, line 29): In-memory index of Btrfs subvolumes below one root path. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `BtrfsIndex.add` (method, line 40): Add or replace one indexed subvolume. **Why:** Keeps this operation inside `BtrfsIndex` so callers use the class endpoint, state, and validation rules.

- `BtrfsIndex.discard` (method, line 53): Remove one path and any known UUID lookup entries for it. **Why:** Keeps this operation inside `BtrfsIndex` so callers use the class endpoint, state, and validation rules.

- `BtrfsIndex.contains` (method, line 65): Return True when ``path`` is an indexed subvolume. **Why:** Keeps this operation inside `BtrfsIndex` so callers use the class endpoint, state, and validation rules.

- `BtrfsIndex.meta` (method, line 70): Return metadata for ``path`` if it was indexed. **Why:** Keeps this operation inside `BtrfsIndex` so callers use the class endpoint, state, and validation rules.

- `BtrfsIndex.find_send_uuid` (method, line 75): Return a subvolume whose Btrfs send-stream identity equals ``uuid``.  **Why:** Keeps this operation inside `BtrfsIndex` so callers use the class endpoint, state, and validation rules.

- `BtrfsIndex.remove_tree` (method, line 91): Remove a deleted path and all indexed descendants. **Why:** Keeps this operation inside `BtrfsIndex` so callers use the class endpoint, state, and validation rules.

- `SourceInventory` (class, line 101): One coherent source-side Timeshift/Btrfs inventory.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `SourceInventory.snapshot_names` (property, line 121): Return Timeshift timestamp names in sorted order. **Why:** Keeps this operation inside `SourceInventory` so callers use the class endpoint, state, and validation rules.

- `SourceInventory.meta` (method, line 127): Return source metadata from cache first, then snapshot-root index. **Why:** Keeps this operation inside `SourceInventory` so callers use the class endpoint, state, and validation rules.

- `_clean_uuid` (function, line 138): Normalize Btrfs UUID fields from list/show output. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `parse_subvolume_list` (function, line 147): Parse ``btrfs subvolume list -u -q -R`` output for one root. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `parse_subvolume_paths` (function, line 173): Return root-scoped absolute paths from ``btrfs subvolume list`` output. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_mark_readonly_from_list` (function, line 187): Mark indexed paths read-only using one ``btrfs subvolume list -r`` result. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `build_local_btrfs_index` (function, line 203): Build a local Btrfs index with bulk list commands.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_remote_bulk_index_script` (function, line 251): Return a POSIX shell script that bulk-lists source Btrfs metadata.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `build_source_btrfs_index` (function, line 297): Build a source Btrfs index in SSH or local mode. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `build_remote_btrfs_index` (function, line 329): Build a remote source index using one SSH command.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_parse_remote_btrfs_index_result` (function, line 361): Parse one remote bulk-index section into a :class:`BtrfsIndex`.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_remote_source_inventory_script` (function, line 461): Return one remote script for Timeshift, info.json, and both Btrfs roots.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_extract_snapshot_info_json_frames` (function, line 543): Remove and parse the ``cat`` payloads from combined SSH output.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_split_remote_source_inventory_output` (function, line 577): Split combined output into identity, Timeshift, info.json, and Btrfs sections. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_current_process_identity` (function, line 650): Return the effective local account name and UID used to read metadata. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_read_local_snapshot_info_json` (function, line 661): Read all local Timeshift control files without spawning commands. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_record_missing_info_json_errors` (function, line 688): Record listed Timeshift dates that had no readable control file. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `build_source_inventory` (function, line 702): Build one coherent Timeshift/snapshot/cache source inventory.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `describe_source_inventory_changes` (function, line 825): Return concise human-readable differences between two inventories. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `refresh_path` (function, line 877): Refresh one exact path through the shared Btrfs operation layer. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

## `timeshift_btrfs_sync/lock.py`

**Module role:** Local advisory file locking for coordinated operations.

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `FileLock` (class, line 10): flock() based non-blocking exclusive lock on the local machine. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `FileLock.__init__` (method, line 13): Return or perform init. **Why:** Keeps this operation inside `FileLock` so callers use the class endpoint, state, and validation rules.

- `FileLock.__enter__` (method, line 17): Return or perform enter. **Why:** Keeps this operation inside `FileLock` so callers use the class endpoint, state, and validation rules.

- `FileLock.__exit__` (method, line 29): Return or perform exit. **Why:** Keeps this operation inside `FileLock` so callers use the class endpoint, state, and validation rules.

## `timeshift_btrfs_sync/log.py`

**Module role:** Split run logging for timeshift-btrfs-sync. 

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `RunLogger` (class, line 32): Owns the split log files for one run. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `RunLogger.__post_init__` (method, line 38): Create the log directory and open the run log files. **Why:** Keeps this operation inside `RunLogger` so callers use the class endpoint, state, and validation rules.

- `RunLogger.close` (method, line 71): Close all log files. **Why:** Keeps this operation inside `RunLogger` so callers use the class endpoint, state, and validation rules.

- `RunLogger.attachment_paths` (method, line 81): Return run log files in the order useful for mail attachments.  **Why:** Keeps this operation inside `RunLogger` so callers use the class endpoint, state, and validation rules.

- `RunLogger._write` (method, line 91): Write text safely from possible stream-reader threads. **Why:** Keeps this operation inside `RunLogger` so callers use the class endpoint, state, and validation rules.

- `RunLogger._remember_stderr` (method, line 98): Keep a small tail of stderr for failure notifications. **Why:** Keeps this operation inside `RunLogger` so callers use the class endpoint, state, and validation rules.

- `RunLogger.last_stderr_tail` (method, line 106): Return the newest stderr text remembered for MQTT/error reports. **Why:** Keeps this operation inside `RunLogger` so callers use the class endpoint, state, and validation rules.

- `RunLogger._line` (method, line 112): Write exactly one logical line. **Why:** Keeps this operation inside `RunLogger` so callers use the class endpoint, state, and validation rules.

- `RunLogger.info` (method, line 119): Write a normal status line to .log. **Why:** Keeps this operation inside `RunLogger` so callers use the class endpoint, state, and validation rules.

- `RunLogger.mbuffer` (method, line 124): Write one line to the .mbuffer transfer-progress log. **Why:** Keeps this operation inside `RunLogger` so callers use the class endpoint, state, and validation rules.

- `RunLogger.btrfs_out` (method, line 129): Write one line to the .btrfs Btrfs verbose-output log. **Why:** Keeps this operation inside `RunLogger` so callers use the class endpoint, state, and validation rules.

- `RunLogger.success` (method, line 134): Write one line to the .succes human-readable summary log. **Why:** Keeps this operation inside `RunLogger` so callers use the class endpoint, state, and validation rules.

- `RunLogger.success_text` (method, line 139): Write a preformatted block to the .succes summary log. **Why:** Keeps this operation inside `RunLogger` so callers use the class endpoint, state, and validation rules.

- `RunLogger.err` (method, line 146): Write an error/stderr line to .err and remember its tail. **Why:** Keeps this operation inside `RunLogger` so callers use the class endpoint, state, and validation rules.

- `RunLogger.command` (method, line 153): Record a command that is about to run.  **Why:** Keeps this operation inside `RunLogger` so callers use the class endpoint, state, and validation rules.

- `RunLogger.completed` (method, line 176): Record the output from a normal captured command.  **Why:** Keeps this operation inside `RunLogger` so callers use the class endpoint, state, and validation rules.

- `RunLogger.pipeline_commands` (method, line 207): Record send/buffer/receive commands to the appropriate logs. **Why:** Keeps this operation inside `RunLogger` so callers use the class endpoint, state, and validation rules.

- `RunLogger.pipeline_summary` (method, line 218): Record final pipeline status. **Why:** Keeps this operation inside `RunLogger` so callers use the class endpoint, state, and validation rules.

- `RunLogger.stream_text` (method, line 226): Write live pipeline text to terminal and/or split log files. **Why:** Keeps this operation inside `RunLogger` so callers use the class endpoint, state, and validation rules.

- `emit_success_summary` (function, line 254): Write a readable summary to the real terminal and .succes only.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `TeeTextIO` (class, line 270): Terminal stream wrapper that also writes normal app output to run logs.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `TeeTextIO.__init__` (method, line 283): Return or perform init. **Why:** Keeps this operation inside `TeeTextIO` so callers use the class endpoint, state, and validation rules.

- `TeeTextIO.write` (method, line 290): Return or perform write. **Why:** Keeps this operation inside `TeeTextIO` so callers use the class endpoint, state, and validation rules.

- `TeeTextIO.flush` (method, line 303): Return or perform flush. **Why:** Keeps this operation inside `TeeTextIO` so callers use the class endpoint, state, and validation rules.

- `TeeTextIO.isatty` (method, line 306): Return or perform isatty. **Why:** Keeps this operation inside `TeeTextIO` so callers use the class endpoint, state, and validation rules.

- `TeeTextIO.fileno` (method, line 309): Return or perform fileno. **Why:** Keeps this operation inside `TeeTextIO` so callers use the class endpoint, state, and validation rules.

- `TeeTextIO.writable` (method, line 312): Return or perform writable. **Why:** Keeps this operation inside `TeeTextIO` so callers use the class endpoint, state, and validation rules.

- `TeeTextIO.__getattr__` (method, line 315): Return or perform getattr. **Why:** Keeps this operation inside `TeeTextIO` so callers use the class endpoint, state, and validation rules.

- `terminal_stdout` (function, line 323): Return the real terminal stdout, bypassing the run-log tee wrapper. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `terminal_stderr` (function, line 329): Return the real terminal stderr, bypassing the run-log tee wrapper. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `get_logger` (function, line 337): Return the active logger, if file logging is enabled. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `active_logger` (function, line 344): Temporarily install a run logger and tee app output to files.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `create_run_logger` (function, line 380): Create a logger when log_dir is configured; otherwise return None.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `tee_pipe_to_log` (function, line 402): Start a thread that reads bytes from a process pipe and logs them live.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

## `timeshift_btrfs_sync/mail.py`

**Module role:** Optional email notifications for timeshift-btrfs-sync. 

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `MailConfig` (class, line 20): SMTP settings for optional email notifications.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `MailConfig.resolved_password` (method, line 52): Return password from config value or password_file. **Why:** Keeps this operation inside `MailConfig` so callers use the class endpoint, state, and validation rules.

- `_subject` (function, line 61): Create a short readable subject line. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_body` (function, line 72): Create a fallback plain-text email body from the status payload. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_success_body_from_paths` (function, line 101): Return the text content of the non-empty .succes file, if present. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_filter_attachments` (function, line 118): Return existing attachment paths and human-readable skipped reasons. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_attach_file` (function, line 148): Attach one file to an EmailMessage. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `send_status` (function, line 159): Send one optional SMTP status email.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

## `timeshift_btrfs_sync/maintenance.py`

**Module role:** Guarded maintenance commands for state and lock files. 

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_confirm_or_raise` (function, line 21): Require an exact typed confirmation before destructive maintenance. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_safe_configured_file` (function, line 29): Return a normalized configured file path or raise for unsafe targets.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_looks_like_state_file` (function, line 44): Return True when an existing file appears to be ts-btrfs state.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_looks_like_lock_file` (function, line 63): Return True when an existing file looks like this app's simple lock file. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_print_header` (function, line 77): Print the common maintenance command warning block. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_require_real_confirmation` (function, line 90): Require real-mode flags and typed confirmations. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `clear_state_file` (function, line 110): Remove the configured state.json file after explicit confirmation.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `delete_lock_file` (function, line 160): Delete the configured lock file when no running process holds it.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

## `timeshift_btrfs_sync/models.py`

**Module role:** Shared dataclasses for snapshots and subvolumes.

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `SubvolumeMeta` (class, line 9): Metadata for one Btrfs subvolume inside one Timeshift snapshot. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `send_stream_uuid` (function, line 21): Return the UUID identity carried when ``meta`` is sent by Btrfs.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `SnapshotMeta` (class, line 35): Metadata for one Timeshift snapshot. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `SnapshotMeta.sort_key` (method, line 45): Timeshift timestamp names sort oldest-to-newest lexically. **Why:** Keeps this operation inside `SnapshotMeta` so callers use the class endpoint, state, and validation rules.

- `tags_text` (function, line 51): Return compact human text for Timeshift tags. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

## `timeshift_btrfs_sync/mqtt.py`

**Module role:** Optional MQTT notifications for timeshift-btrfs-sync. 

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `MQTTConfig` (class, line 19): MQTT broker and publish settings.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `MQTTConfig.resolved_password` (method, line 41): Return password from config value or password_file. **Why:** Keeps this operation inside `MQTTConfig` so callers use the class endpoint, state, and validation rules.

- `publish_status` (function, line 51): Publish one JSON MQTT status message.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

## `timeshift_btrfs_sync/notify.py`

**Module role:** Shared notification payload helpers.

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `utc_timestamp` (function, line 10): Return a compact ISO-8601 UTC timestamp for notifications. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `build_notification_payload` (function, line 16): Build the shared status payload used by MQTT and email. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

## `timeshift_btrfs_sync/paths.py`

**Module role:** Canonical path normalization and containment rules. 

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `normalize_source_path` (function, line 13): Normalize POSIX path text while preserving an intentionally empty value. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `is_same_or_under` (function, line 23): Return true when ``path`` equals ``root`` or is below it. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `is_local_same_or_under` (function, line 35): Return true when one local path resolves to ``root`` or below it.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `is_under` (function, line 55): Return true only when ``path`` is strictly below ``root``. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `listed_path_to_absolute` (function, line 67): Resolve one Btrfs-list path below a mounted root.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `sort_deepest_first` (function, line 115): Deduplicate and order paths for child-before-parent deletion. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

## `timeshift_btrfs_sync/payload_stats.py`

**Module role:** Normalized source/destination payload statistics for Btrfs snapshot trees. 

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `PayloadTreeStats` (class, line 30): Normalized payload/container counts for one source or destination tree. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `PayloadTreeStats.total_payload` (property, line 47): Return the number of real cached/received payload subvolumes. **Why:** Keeps this operation inside `PayloadTreeStats` so callers use the class endpoint, state, and validation rules.

- `PayloadTreeStats.total_cache_payload` (property, line 53): Return how many source payloads came from app-owned source cache. **Why:** Keeps this operation inside `PayloadTreeStats` so callers use the class endpoint, state, and validation rules.

- `PayloadTreeStats.total_direct_payload` (property, line 59): Return how many source payloads came from protected Timeshift originals. **Why:** Keeps this operation inside `PayloadTreeStats` so callers use the class endpoint, state, and validation rules.

- `normalize_path` (function, line 65): Normalize paths so source/destination comparisons ignore trailing slashes. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_relative_parts` (function, line 71): Return path parts relative to root, or None if path is outside root. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_recount_payload` (function, line 85): Rebuild per-subvolume counters from the normalized payload set. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_add_payload` (function, line 93): Add a payload entry when relative parts end in a configured subvolume name. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `source_send_cache_stats` (function, line 106): Classify source send-cache subvolumes into payload and helper counts. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `destination_payload_stats` (function, line 129): Classify destination target subvolumes into received payload counts. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `direct_send_payload_stats` (function, line 152): Return payload entries streamed directly from protected Timeshift originals.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `merge_source_payload_stats` (function, line 184): Merge app-cache and protected direct-send payload into one source view. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `PayloadMatchStats` (class, line 207): Comparison between source send payload and destination received payload. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `PayloadMatchStats.source_only` (property, line 214): Return source payload entries not present on the destination. **Why:** Keeps this operation inside `PayloadMatchStats` so callers use the class endpoint, state, and validation rules.

- `PayloadMatchStats.destination_only` (property, line 220): Return destination payload entries not present on the source side. **Why:** Keeps this operation inside `PayloadMatchStats` so callers use the class endpoint, state, and validation rules.

- `PayloadMatchStats.ok` (property, line 226): Return True when source send payload and destination payload match. **Why:** Keeps this operation inside `PayloadMatchStats` so callers use the class endpoint, state, and validation rules.

- `compare_payloads` (function, line 232): Return normalized source/destination payload comparison stats. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_format_count_line` (function, line 238): Return an aligned summary line. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `render_payload_match` (function, line 244): Render the source/destination payload comparison block. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

## `timeshift_btrfs_sync/planning.py`

**Module role:** Pure workflow planning from a combined backup inventory. 

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `ActionKind` (class, line 17): Represent ActionKind. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `WorkflowAction` (class, line 28): Represent WorkflowAction. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `WorkflowPlan` (class, line 36): Represent WorkflowPlan. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `WorkflowPlan.add` (method, line 40): Return or perform add. **Why:** Keeps this operation inside `WorkflowPlan` so callers use the class endpoint, state, and validation rules.

- `plan_sync_queue` (function, line 52): Plan the oldest-to-newest sync queue without executing operations. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `plan_snapshot_recovery` (function, line 79): Plan one whole-date recovery in cache, destination, then state order. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `plan_prune_snapshot` (function, line 89): Return or perform plan prune snapshot. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `plan_destroy_targets` (function, line 102): Plan named endpoint/root destruction in the caller-provided order. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

## `timeshift_btrfs_sync/preflight.py`

**Module role:** Sync path preflight checks. 

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `PathPreflightError` (class, line 44): Raised before any destructive/creating sync work when required paths fail. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `PathCheck` (class, line 49): One configured path availability result. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_shell_words` (function, line 60): Return a shell-safe string for configured command-prefix words. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_parse_path_check_output` (function, line 66): Parse source-path preflight sentinel lines into structured checks.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_source_snapshot_root_script` (function, line 99): Build a source script that validates Timeshift-owned source.snapshot_root.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_cache_root_check_script` (function, line 167): Build a source script that validates or creates source.cache_root. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_combined_source_path_check_script` (function, line 243): Run both source-root preflight checks inside one source command.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_source_path_checks` (function, line 275): Check/create both source roots with at most one SSH command. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_parent_of_path` (function, line 354): Return the immediate parent path used for exact-path creation checks. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_local_btrfs_result` (function, line 361): Run one local destination sudo+btrfs command for preflight checks. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_compact_process_error` (function, line 373): Return compact stderr/stdout text from a failed subprocess. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_compact_os_error` (function, line 380): Return compact text for local filesystem creation errors. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_print_check_block` (function, line 386): Print one human-readable preflight result block. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_raise_for_failed_checks` (function, line 401): Raise a hard preflight error when any check failed. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `ensure_local_helper_dir` (function, line 411): Ensure one local helper directory exists.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `prepare_lock_path` (function, line 565): Create/verify the lock directory before other sync/prune directories.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `prepare_destination_helper_paths` (function, line 597): Create/verify local destination helper folders used by sync/prune.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_local_target_path_check` (function, line 644): Check/create destination.target_root locally.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `check_required_sync_paths` (function, line 786): Verify/create required configured roots before manual snapshot creation or send.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

## `timeshift_btrfs_sync/restore.py`

**Module role:** Restore backed-up snapshots into Timeshift's native Btrfs layout. 

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `RestoreError` (class, line 50): Raised when backups cannot be imported safely into Timeshift. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `TimeshiftOsIdentity` (class, line 55): Timeshift ``info.json`` provenance metadata for one snapshot. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `BackupSnapshot` (class, line 64): One validated local or SSH backup snapshot available for restore. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `BackupDirectoryRecord` (class, line 75): Ordinary filesystem facts for one backup timestamp directory. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `BackupRepository` (class, line 86): Access one local or SSH backup repository through one transport layer. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `BackupRepository.from_config` (method, line 95): Create the backup endpoint selected by restore.mode. **Why:** Keeps this operation inside `BackupRepository` so callers use the class endpoint, state, and validation rules.

- `BackupRepository.root` (property, line 109): Return or perform root. **Why:** Keeps this operation inside `BackupRepository` so callers use the class endpoint, state, and validation rules.

- `BackupRepository.snapshots_root` (property, line 113): Return or perform snapshots root. **Why:** Keeps this operation inside `BackupRepository` so callers use the class endpoint, state, and validation rules.

- `BackupRepository.environment` (property, line 117): Return or perform environment. **Why:** Keeps this operation inside `BackupRepository` so callers use the class endpoint, state, and validation rules.

- `BackupRepository.location_label` (property, line 121): Return or perform location label. **Why:** Keeps this operation inside `BackupRepository` so callers use the class endpoint, state, and validation rules.

- `BackupRepository.load_state` (method, line 124): Read and validate state.json from the same endpoint as the backup. **Why:** Keeps this operation inside `BackupRepository` so callers use the class endpoint, state, and validation rules.

- `BackupRepository.scan_directories` (method, line 146): Read direct date entries and all info.json files with backup privilege. **Why:** Keeps this operation inside `BackupRepository` so callers use the class endpoint, state, and validation rules.

- `BackupRepository.btrfs_index` (method, line 156): Build one local or SSH Btrfs index for the complete backup tree. **Why:** Keeps this operation inside `BackupRepository` so callers use the class endpoint, state, and validation rules.

- `_scan_snapshot_directories` (function, line 174): Scan physical Timeshift-style date directories and their control files.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_read_privileged_file` (function, line 282): Read one regular non-symlink file through individually privileged commands. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_effective_send_uuid` (function, line 353): Return the UUID identity carried by a Btrfs send stream.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_info_os_identity` (function, line 367): Return Timeshift provenance identity while ignoring mutable fields.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_parse_info_json` (function, line 389): Parse one Timeshift control file and extract its provenance identity. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_same_os_identity` (function, line 401): Return whether two Timeshift control files have matching provenance. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_consistent_backup_identity` (function, line 412): Require one non-conflicting provenance identity across the backup set. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_timeshift_info_identities` (function, line 439): Parse provenance identities from the coherent source info.json inventory. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_timeshift_info_diagnostic` (function, line 452): Return a concise reason when source ``info.json`` provenance is unavailable. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_compare_repository_os_identity` (function, line 478): Compare backup provenance with currently readable Timeshift control files.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `RestorePlan` (class, line 511): A side-effect-free single or chain restore plan. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `RestorePlan.seed_name` (property, line 526): Return or perform seed name. **Why:** Keeps this operation inside `RestorePlan` so callers use the class endpoint, state, and validation rules.

- `_source_path_exists` (function, line 530): Check one Timeshift-side path through the configured source privilege. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_privileged_argv` (function, line 550): Return or perform privileged argv. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_write_source_info_json` (function, line 554): Write exact captured metadata through the configured source privilege prefix. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_validate_backup_snapshot` (function, line 595): Validate one backup date, payload set, metadata file, and Btrfs identity. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_discover_backups` (function, line 673): Return selected or all valid backups ordered by Timeshift timestamp. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_timeshift_snapshots` (function, line 698): Read one coherent Timeshift repository/cache/info inventory.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_exact_timeshift_payload_meta` (function, line 776): Return exact live metadata for one Timeshift payload.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_state_payload_proof` (function, line 799): Check the two UUID links recorded for one completed transfer. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_live_payload_proof` (function, line 829): Prove one payload directly from current Btrfs metadata.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_find_latest_common_parent` (function, line 891): Find the newest safely confirmed timestamp present in both repositories.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_build_restore_plan` (function, line 1070): Build a single or complete-chain restore plan without changing either side. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_remove_restore_directory` (function, line 1198): Remove one exact app-created ordinary restore directory and its payloads. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_cleanup_restore_attempt` (function, line 1252): Roll back only directories created by the current restore attempt. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_create_pre_restore_snapshot` (function, line 1312): Create and verify one safety snapshot on the Timeshift restore target.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_print_restored_snapshot_retention_warning` (function, line 1409): Explain that restored Timeshift tags remain subject to normal retention. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_print_restore_plan` (function, line 1426): Return or perform print restore plan. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_is_missing_incremental_parent_error` (function, line 1495): Return whether Btrfs failed because a parent/clone UUID was unavailable.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_remove_partial_received_payload` (function, line 1515): Delete only a failed receive's exact partial Btrfs child before retry. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_run_restore_stream` (function, line 1541): Run one topology-independent backup-send to Timeshift-receive stream. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_receive_restore_payload` (function, line 1572): Receive and verify one hidden-chain payload for every restore topology.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `restore_backups` (function, line 1665): Restore one snapshot or a complete backup chain into Timeshift. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

## `timeshift_btrfs_sync/retention.py`

**Module role:** Destination retention/pruning logic.

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `PrunePlan` (class, line 32): Dry-run friendly prune plan. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `PrunePlan.add_keep` (method, line 39): Mark a snapshot as kept and remember the human reason. **Why:** Keeps this operation inside `PrunePlan` so callers use the class endpoint, state, and validation rules.

- `PrunePlan.add_delete` (method, line 46): Mark a snapshot as deletable only when it is not already protected. **Why:** Keeps this operation inside `PrunePlan` so callers use the class endpoint, state, and validation rules.

- `_is_app_created_ondemand` (function, line 54): Return true when a state entry is a tag O snapshot with the app marker. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_delete_reason_for_snapshot` (function, line 66): Explain why a snapshot is outside the active retention rules. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_delete_reasons` (function, line 102): Return delete reasons without the internal prefix. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_source_cache_delete_paths` (function, line 111): Return app-owned source send-cache paths for a prune decision.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_protected_timeshift_send_paths` (function, line 156): Return direct Timeshift send paths that prune must never delete. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_destination_delete_paths` (function, line 186): Return tracked destination subvolume paths for a prune decision. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `source_snapshot_state` (function, line 197): Return temporary state-like data from source Timeshift snapshots.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `initial_sync_keep_names` (function, line 222): Return source snapshot names that a fresh destination should seed.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_cleanup_source_cache_for_pruned_snapshot` (function, line 233): Delete one pruned snapshot's app-owned cache through the shared tree engine. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `build_prune_plan` (function, line 280): Build retention plan from state without deleting anything.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_delete_destination_snapshot_for_prune` (function, line 365): Delete one destination date through the shared tree engine. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_delete_prune_item` (function, line 391): Execute one pure prune plan and remove state after both trees are gone. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `print_prune_plan` (function, line 451): Write an easy-to-read retention summary to terminal and .succes. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `prune` (function, line 497): Apply destination retention rules. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

## `timeshift_btrfs_sync/source.py`

**Module role:** Command runner for local or SSH Timeshift and backup endpoints.

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `SourceRunner` (class, line 12): Run commands through one local or SSH endpoint.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `SourceRunner.from_mode` (method, line 24): Create a local or SSH command runner from one validated mode. **Why:** Keeps this operation inside `SourceRunner` so callers use the class endpoint, state, and validation rules.

- `SourceRunner.from_config` (method, line 36): Create the configured Timeshift source runner. **Why:** Keeps this operation inside `SourceRunner` so callers use the class endpoint, state, and validation rules.

- `SourceRunner.uses_ssh` (property, line 42): Return True when source commands are executed through SSH. **Why:** Keeps this operation inside `SourceRunner` so callers use the class endpoint, state, and validation rules.

- `SourceRunner.location` (property, line 48): Return the metadata location label used by Btrfs helpers. **Why:** Keeps this operation inside `SourceRunner` so callers use the class endpoint, state, and validation rules.

- `SourceRunner.command` (method, line 53): Return argv that runs one source-side shell command. **Why:** Keeps this operation inside `SourceRunner` so callers use the class endpoint, state, and validation rules.

- `SourceRunner.run` (method, line 60): Run one source-side command and capture stdout/stderr. **Why:** Keeps this operation inside `SourceRunner` so callers use the class endpoint, state, and validation rules.

- `SourceRunner.environment` (method, line 87): Return environment needed for streaming source commands. **Why:** Keeps this operation inside `SourceRunner` so callers use the class endpoint, state, and validation rules.

- `SourceRunner.test` (method, line 94): Verify that the source command endpoint is usable. **Why:** Keeps this operation inside `SourceRunner` so callers use the class endpoint, state, and validation rules.

## `timeshift_btrfs_sync/ssh.py`

**Module role:** SSH command construction and non-interactive authentication dispatch.

**Why this module exists:** Keeps key, key-passphrase, account-password, ControlMaster, and command-line behavior identical for normal SSH commands and Btrfs streaming pipelines.

- `_is_relative_to` (function, line 46): Return True when a path is equal to or below a root. **Why:** Validates private ControlPath locations without unsafe string-prefix matching.

- `_cleanup_askpass_helper` (function, line 56): Remove the process-private askpass helper directory during normal interpreter shutdown. **Why:** Avoids leaving generated authentication helper files behind after the process exits.

- `_ensure_askpass_helper` (function, line 67): Create one owner-only prompt-dispatch helper containing no secrets. **Why:** Lets OpenSSH receive a private-key passphrase and a separate remote account password while refusing unknown prompts such as host-key confirmation.

- `validate_control_path_safety` (function, line 102): Create and validate a private SSH ControlPath socket directory. **Why:** Prevents other local users from reusing a multiplexed authenticated connection.

- `SSHConfig` (class, line 172): Store one validated SSH connection and authentication configuration. **Why:** Gives every sync and restore transport the same command and environment construction.

- `SSHConfig.target` (property, line 191): Return `host` or `user@host`. **Why:** Centralizes SSH target formatting.

- `SSHConfig.uses_password_auth` (property, line 197): Report whether a remote account password is configured. **Why:** Selects the established password-only `sshpass` path when no identity passphrase is needed.

- `SSHConfig.uses_identity_passphrase` (property, line 203): Report whether an encrypted private-key passphrase is configured. **Why:** Keeps key unlocking separate from remote account authentication.

- `SSHConfig.uses_askpass` (property, line 209): Report whether prompt-aware askpass dispatch is required. **Why:** Avoids wrapping encrypted-key authentication with password-only `sshpass` behavior.

- `SSHConfig._read_secret` (method, line 215): Read one direct or file-backed secret and refuse empty content. **Why:** Applies the same file newline handling and empty-secret safety to both authentication families.

- `SSHConfig._read_password` (method, line 228): Resolve the remote SSH account password. **Why:** Ensures `password` and `password_file` are never confused with the local key passphrase.

- `SSHConfig._read_identity_passphrase` (method, line 233): Resolve the encrypted private-key passphrase. **Why:** Supports both direct and owner-only file-backed key unlocking.

- `SSHConfig.environment` (method, line 242): Build the child environment for `sshpass` or prompt-aware OpenSSH askpass. **Why:** Supplies secrets without adding them to the logged command line and can answer two distinct prompts with two distinct values.

- `SSHConfig.base_command` (method, line 267): Build base SSH argv before the remote command is appended. **Why:** Reuses `sshpass` only for password-only authentication and otherwise lets OpenSSH askpass handle encrypted identities.

- `SSHRunner` (class, line 295): Run remote commands through one `SSHConfig`. **Why:** Provides a shared transport layer for sync, pull restore, and push restore.

- `SSHRunner.__init__` (method, line 298): Store the validated SSH configuration. **Why:** Keeps command and environment generation tied to the same endpoint.

- `SSHRunner.command` (method, line 301): Return argv for one SSH remote command. **Why:** Appends remote shell work to the shared authenticated base command.

- `SSHRunner.run` (method, line 306): Run a remote command and capture its output. **Why:** Applies identical authentication and logging behavior to metadata and maintenance commands.

- `SSHRunner.environment` (method, line 332): Return SSH authentication environment for streaming pipeline calls. **Why:** Makes Btrfs send/receive pipelines use the same key/passphrase/password behavior as ordinary SSH probes.

- `SSHRunner.test` (method, line 337): Verify SSH connectivity and clean stdout. **Why:** Detects authentication failures and banner pollution before backup or restore work starts.

## `timeshift_btrfs_sync/state.py`

**Module role:** Persistent local state for completed transfers.

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `empty_state` (function, line 28): Return a new empty state document. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_safe_relative_path` (function, line 34): Return a normalized destination-relative path or raise ValueError. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_safe_source_relative_path` (function, line 46): Return a normalized safe POSIX path relative to a configured source root.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_normalize_source_root` (function, line 65): Return one normalized absolute-style POSIX source root. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_source_path_relative_to_root` (function, line 72): Return ``path`` relative to ``root`` when it is currently below that root. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_expected_snapshot_relative_path` (function, line 90): Return the canonical ``<snapshot>/<subvolume>`` source-relative path. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `source_path_to_relative` (function, line 98): Convert a current source path to canonical configured-root-relative state form. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `resolve_source_path` (function, line 124): Resolve a current root-relative state path under its configured source root. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `destination_path_to_relative` (function, line 143): Convert a current destination path to target-root-relative state form. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `resolve_destination_path` (function, line 155): Resolve a current target-root-relative state destination path. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `send_path_kind_for_state_subvolume` (function, line 160): Return the explicitly stored current send-path ownership kind. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_source_root_for_kind` (function, line 168): Return the configured source root used by one stored send-path kind. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `resolve_state_send_path` (function, line 180): Resolve stored ``send_path`` under its current configured source root. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_reject_unknown_state_keys` (function, line 213): Return or perform reject unknown state keys. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `validate_state_document` (function, line 219): Validate the complete current state schema before any workflow uses it. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `load_state` (function, line 297): Load and validate the current state document, or return an empty one when absent. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `save_state` (function, line 309): Validate and atomically write the current state document. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `refresh_snapshot_metadata_from_source` (function, line 328): Refresh mutable Timeshift metadata for already-known snapshots. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `snapshot_is_synced` (function, line 355): Return True when a snapshot is recorded as fully synced. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_kind_for_absolute_source_path` (function, line 367): Classify a current absolute source path by configured ownership root. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `mark_subvolume_synced` (function, line 384): Record one successful send/receive using only root-relative state paths.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `state_send_path_is_app_cache` (function, line 499): Return True when the stored send path belongs to the app cache. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `state_send_path_is_protected_timeshift_original` (function, line 504): Return True when the stored send path belongs to Timeshift. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `remove_snapshot_from_state` (function, line 509): Remove a pruned snapshot from state. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `refresh_state_metadata_and_report` (function, line 515): Refresh only Timeshift tags/comment/created/path, report, and save. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `latest_synced_before` (function, line 539): Return newest older synced parent candidate. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

## `timeshift_btrfs_sync/sync.py`

**Module role:** Main destination-pull sync workflow. 

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `SyncError` (class, line 47): Raised for sync safety errors. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_local_meta` (function, line 51): Return or perform local meta. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_source_meta` (function, line 57): Return source metadata, preferring bulk indexes over one-off probes. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_human_blank` (function, line 81): Print one blank line to separate human-readable status blocks. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_human_rule` (function, line 87): Print a visual separator with blank lines around it. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_record_sync_event` (function, line 96): Add one planned or completed transfer to the run summary. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_print_sync_summary` (function, line 125): Write a terminal-friendly transfer summary to terminal and .succes.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `prepare_destination` (function, line 171): Create/validate destination helper folders before writes.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `list_source_snapshots` (function, line 191): Discover source Timeshift snapshots. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `source_snapshot_index` (function, line 214): Return or perform source snapshot index. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_snapshots_from_source_inventory` (function, line 218): Build Timeshift snapshot objects from one coherent source inventory. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_required_pipeline_source_changes` (function, line 236): Return identity changes to source paths required by current work.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `confirm_source_identity_before_manual_snapshot` (function, line 275): Print and enforce the shared manual-snapshot source identity guard. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_is_app_manual_snapshot` (function, line 327): Return True for source Timeshift O snapshots created by this app.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_pending_app_manual_snapshots` (function, line 343): Return app-created on-demand snapshots that still need syncing.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_maybe_create_manual_snapshot` (function, line 368): Optionally create a source Timeshift tag O snapshot before sync.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_snapshots_in_sync_order` (function, line 457): Return source snapshots oldest-to-newest for Btrfs send. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_select_initial_sync_snapshots` (function, line 463): Return retention-kept source snapshots for a fresh destination seed. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `print_snapshot_table` (function, line 482): Print source snapshots in table form. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_dest_subvolume_path` (function, line 493): Return the final local path for one received subvolume.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_target_snapshot_dir` (function, line 503): Return the managed destination date subvolume passed to `btrfs receive`.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_destination_info_json_path` (function, line 513): Return the destination Timeshift control-file path for one snapshot. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_ensure_destination_snapshot_subvolume` (function, line 519): Create or validate one managed destination date subvolume.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_validate_destination_snapshot_layout` (function, line 569): Refuse ordinary/symlinked date entries after exact Btrfs verification.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_atomic_write_snapshot_info_json` (function, line 630): Atomically write one captured Timeshift ``info.json`` file.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_require_snapshot_info_json` (function, line 663): Return captured control-file content or raise a precise sync error. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_sync_snapshot_info_json` (function, line 697): Create or refresh destination ``info.json`` for one complete snapshot.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_destination_has_existing_snapshots` (function, line 737): Return true only when a date directory contains a configured payload subvolume.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_snapshot_destination_paths_exist` (function, line 758): Return True only when every expected destination subvolume path exists. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_preview_send_path` (function, line 763): Return the send path that would be used, without creating cache snapshots.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_send_path_kind_text` (function, line 777): Return human text explaining who owns the selected send path. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_ensure_source_send_path` (function, line 787): Resolve one real send path through the shared cache operation. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_cleanup_incomplete_destination_receive` (function, line 814): Delete one exact incomplete destination Btrfs child before retrying. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_cleanup_source_cache_snapshot_version` (function, line 844): Delete one app-owned cache date through the shared tree engine. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_cleanup_destination_snapshot_version` (function, line 875): Delete one destination date through the shared tree engine. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_refresh_snapshot_source_subvolumes_live` (function, line 904): Return configured source subvolumes, preferring the bulk index.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_snapshot_destination_has_any_path` (function, line 933): Return True when the destination date folder or configured children exist. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_snapshot_state_is_complete_with_destination` (function, line 942): Return True only when state and destination contain every configured subvolume. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_recover_snapshot_version` (function, line 949): Remove stale current-version traces from cache, destination, and state. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_prepare_snapshot_for_transfer_or_recover` (function, line 1004): Return True when a snapshot can be transferred, False when skipped.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_recover_stale_state_snapshots_missing_from_source` (function, line 1078): Clean incomplete state entries whose Timeshift source name is gone. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_read_local_destination_parent_metadata` (function, line 1110): Read metadata for the destination snapshot that would be the receiver parent. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_match_source_path_to_destination_received_uuid` (function, line 1132): Check whether a source send-stream UUID matches destination identity.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_select_verified_parent_send_path` (function, line 1194): Select a safe source parent path for incremental send without recreating it.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_state_uuid_values_for_path` (function, line 1301): Return the current state UUID that identifies one source candidate. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_find_confirmed_sync_floor` (function, line 1318): Return newest state snapshot that still exists on source and matches UUIDs.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_destination_snapshot_names` (function, line 1445): Return destination snapshot folder names sorted oldest-to-newest. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_expected_original_source_path` (function, line 1454): Return the Timeshift-owned original source path for one snapshot/subvolume. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_source_cache_meta_by_uuid` (function, line 1460): Return indexed read-only source-cache metadata for one send UUID.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_match_existing_destination_to_source` (function, line 1479): Match one existing destination subvolume to an exact source/cache UUID.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_recover_state_from_existing_destination` (function, line 1557): Rebuild missing/empty state.json from proven source/destination matches.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_filesystem_parent_candidates` (function, line 1682): Find local destination parent candidates by matching snapshot names.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_select_parent` (function, line 1706): Choose the newest valid incremental parent.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_verify_sync_viability_before_manual_snapshot` (function, line 1850): Prove sync can start before asking Timeshift to create a snapshot.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `sync_once` (function, line 1978): Run one sync pass.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

## `timeshift_btrfs_sync/timeshift.py`

**Module role:** Timeshift command wrappers and parser for `timeshift --list`.

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `timeshift_cmd` (function, line 17): Build a source-side shell command that invokes sudo+timeshift. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `normalize_tags` (function, line 23): Return unique Timeshift tag letters found in text. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `parse_timeshift_list` (function, line 33): Parse Timeshift snapshot names and tag/comment text. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `list_source_snapshots` (function, line 66): Discover source snapshots through SSH or local source commands.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `create_remote_manual_snapshot_cmd` (function, line 107): Build the Timeshift manual/on-demand snapshot create command.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `create_source_manual_snapshot` (function, line 126): Create a source Timeshift on-demand snapshot through SSH or locally. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

## `timeshift_btrfs_sync/topology.py`

**Module role:** Command topology descriptions and safety checks. 

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `TopologyError` (class, line 21): Raised when a command/config combination would use unintended hosts. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `TopologyDescription` (class, line 26): Human-readable endpoint ownership for one command. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_ssh_target` (function, line 34): Return or perform ssh target. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `describe_sync_topology` (function, line 42): Return the endpoints actually used by ``sync``. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `describe_restore_topology` (function, line 57): Return the endpoints actually used by ``restore``. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `reject_pull_restore_profile_for_sync` (function, line 79): Refuse ``sync`` with a profile whose restore backup lives over SSH.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

## `timeshift_btrfs_sync/tree_ops.py`

**Module role:** Single Btrfs tree discovery, deletion, and post-verification engine.

**Why this module exists:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `TreeDeleteResult` (class, line 15): Represent TreeDeleteResult. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `TreeDeleteResult.success` (property, line 26): Return or perform success. **Why:** Keeps this operation inside `TreeDeleteResult` so callers use the class endpoint, state, and validation rules.

- `_path_exists` (function, line 31): Return or perform path exists. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `discover_subvolume_tree` (function, line 42): Discover a complete nested Btrfs tree in one endpoint list command.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `list_direct_entries` (function, line 68): List exact direct children with shell built-ins on either endpoint. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_validate_confirmations` (function, line 84): Return or perform validate confirmations. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `_verify_absent` (function, line 101): Return or perform verify absent. **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.

- `delete_subvolume_tree` (function, line 118): Delete one managed tree deepest-first and prove the root is absent.  **Why:** Keeps this responsibility in one module so command paths reuse the same behavior and safety rules.
