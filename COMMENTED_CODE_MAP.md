# Commented code map

This map describes only the current runtime and build entry points. Each symbol is listed once with what it does and why its module owns that responsibility.

## `scripts/build_pyinstaller.py`

**Module role:** Build ts-btrfs executables with PyInstaller.

**Why this module exists:** Builds the current package as supported PyInstaller executable formats.

- `build_args` (function/method, line 23): Return the PyInstaller argument list for one build mode. **Why:** Builds the current package as supported PyInstaller executable formats.

- `run_pyinstaller` (function/method, line 50): Run PyInstaller with a useful error if it is not installed. **Why:** Builds the current package as supported PyInstaller executable formats.

- `main` (function/method, line 66): Parse arguments and run the requested build. **Why:** Builds the current package as supported PyInstaller executable formats.

## `timeshift_btrfs_sync/__init__.py`

**Module role:** Timeshift Btrfs sync package.

**Why this module exists:** Exposes package version information.

No runtime classes or functions are defined in this file.

## `timeshift_btrfs_sync/__main__.py`

**Module role:** Run the CLI with: python -m timeshift_btrfs_sync.

**Why this module exists:** Runs the current CLI through Python module execution.

No runtime classes or functions are defined in this file.

## `timeshift_btrfs_sync/btrfs_ops.py`

**Module role:** Reusable Btrfs operations independent of workflow order.

**Why this module exists:** Centralizes Btrfs command construction and parsing so every workflow applies the same metadata and deletion rules.

- `_ListedSubvolume` (class, line 24): One numeric containment record from ``btrfs subvolume list -a -p``. **Why:** Centralizes Btrfs command construction and parsing so every workflow applies the same metadata and deletion rules.

- `_parse_listed_subvolumes` (function/method, line 32): Parse numeric ID, containing-parent ID, and raw path fields. **Why:** Centralizes Btrfs command construction and parsing so every workflow applies the same metadata and deletion rules.

- `_descendant_list_paths` (function/method, line 56): Return only numeric descendants of ``root_id`` from one full list. **Why:** Centralizes Btrfs command construction and parsing so every workflow applies the same metadata and deletion rules.

- `clean_uuid` (function/method, line 73): Perform the clean uuid step used by this module. **Why:** Centralizes Btrfs command construction and parsing so every workflow applies the same metadata and deletion rules.

- `parse_subvolume_show` (function/method, line 78): Parse UUID and read-only fields from ``btrfs subvolume show``. **Why:** Centralizes Btrfs command construction and parsing so every workflow applies the same metadata and deletion rules.

- `BtrfsOps` (class, line 104): Btrfs command facade for one local or source endpoint. **Why:** Centralizes Btrfs command construction and parsing so every workflow applies the same metadata and deletion rules.

- `BtrfsOps.prefix` (property, line 112): Perform the prefix step used by this module. **Why:** Centralizes Btrfs command construction and parsing so every workflow applies the same metadata and deletion rules.

- `BtrfsOps.argv` (function/method, line 115): Perform the argv step used by this module. **Why:** Centralizes Btrfs command construction and parsing so every workflow applies the same metadata and deletion rules.

- `BtrfsOps.run` (function/method, line 118): Perform the run step used by this module. **Why:** Centralizes Btrfs command construction and parsing so every workflow applies the same metadata and deletion rules.

- `BtrfsOps.meta` (function/method, line 133): Return exact-path subvolume metadata or ``None`` for an optional miss. **Why:** Centralizes Btrfs command construction and parsing so every workflow applies the same metadata and deletion rules.

- `BtrfsOps.list_children` (function/method, line 152): Return all descendants selected from one Btrfs containment graph. **Why:** Centralizes Btrfs command construction and parsing so every workflow applies the same metadata and deletion rules.

- `BtrfsOps.create` (function/method, line 171): Perform the create step used by this module. **Why:** Centralizes Btrfs command construction and parsing so every workflow applies the same metadata and deletion rules.

- `BtrfsOps.snapshot` (function/method, line 174): Create one exact writable or read-only Btrfs snapshot. **Why:** Centralizes Btrfs command construction and parsing so every workflow applies the same metadata and deletion rules.

- `BtrfsOps.delete` (function/method, line 190): Perform the delete step used by this module. **Why:** Centralizes Btrfs command construction and parsing so every workflow applies the same metadata and deletion rules.

- `BtrfsOps.send_command` (function/method, line 205): Perform the send command step used by this module. **Why:** Centralizes Btrfs command construction and parsing so every workflow applies the same metadata and deletion rules.

- `BtrfsOps.receive_command` (function/method, line 226): Perform the receive command step used by this module. **Why:** Centralizes Btrfs command construction and parsing so every workflow applies the same metadata and deletion rules.

- `BtrfsOps.set_readonly` (function/method, line 233): Set the Btrfs subvolume read-only property explicitly. **Why:** Centralizes Btrfs command construction and parsing so every workflow applies the same metadata and deletion rules.

- `BtrfsOps.batch_delete` (function/method, line 238): Delete exact paths in one endpoint command and validate confirmations. **Why:** Centralizes Btrfs command construction and parsing so every workflow applies the same metadata and deletion rules.

## `timeshift_btrfs_sync/cache_ops.py`

**Module role:** Single source send-cache operation used by sync and recovery.

**Why this module exists:** Keeps exact send-cache creation and reuse in one place, preventing nested or identity-mismatched cache snapshots.

- `_safe_name` (function/method, line 16): Perform the safe name step used by this module. **Why:** Keeps exact send-cache creation and reuse in one place, preventing nested or identity-mismatched cache snapshots.

- `cache_parent_path` (function/method, line 22): Perform the cache parent path step used by this module. **Why:** Keeps exact send-cache creation and reuse in one place, preventing nested or identity-mismatched cache snapshots.

- `cache_child_path` (function/method, line 26): Perform the cache child path step used by this module. **Why:** Keeps exact send-cache creation and reuse in one place, preventing nested or identity-mismatched cache snapshots.

- `validate_cache_snapshot` (function/method, line 30): Prove an exact cache child is a safe read-only snapshot of ``original``. **Why:** Keeps exact send-cache creation and reuse in one place, preventing nested or identity-mismatched cache snapshots.

- `CacheManager` (class, line 50): Ensure exact reusable send snapshots without nested cache creation. **Why:** Keeps exact send-cache creation and reuse in one place, preventing nested or identity-mismatched cache snapshots.

- `CacheManager.__init__` (function/method, line 53): Perform the init step used by this module. **Why:** Keeps exact send-cache creation and reuse in one place, preventing nested or identity-mismatched cache snapshots.

- `CacheManager._ensure_subvolume` (function/method, line 58): Perform the ensure subvolume step used by this module. **Why:** Keeps exact send-cache creation and reuse in one place, preventing nested or identity-mismatched cache snapshots.

- `CacheManager._probe_create_verify` (function/method, line 85): Probe, create if absent, and verify exact cache path in one command. **Why:** Keeps exact send-cache creation and reuse in one place, preventing nested or identity-mismatched cache snapshots.

- `CacheManager._probe_create_verify.meta` (function/method, line 165): Perform the meta step used by this module. **Why:** Keeps exact send-cache creation and reuse in one place, preventing nested or identity-mismatched cache snapshots.

- `CacheManager.ensure_send_snapshot` (function/method, line 192): Return original read-only source or create/reuse one exact cache child. **Why:** Keeps exact send-cache creation and reuse in one place, preventing nested or identity-mismatched cache snapshots.

## `timeshift_btrfs_sync/cli.py`

**Module role:** Command-line interface for timeshift-btrfs-sync.

**Why this module exists:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `new_subparser` (function/method, line 36): Handle the new subparser step used by this module. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `add_config_arg` (function/method, line 42): Handle the add config arg step used by this module. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `add_run_mode_args` (function/method, line 44): Handle the add run mode args step used by this module. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `add_yes_delete_arg` (function/method, line 50): Handle the add yes delete arg step used by this module. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `_load_config_state` (function/method, line 54): Load state and resolve all root-relative paths against this config. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `_failure_exit_code` (function/method, line 60): Return a stable CLI exit code for failure notifications. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `_stderr_tail_for_exception` (function/method, line 76): Return the best available recent stderr text for failure notifications. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `_send_notifications` (function/method, line 86): Send optional MQTT/email status without changing the command exit code. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `_mail_attachment_paths` (function/method, line 126): Return current run log paths for optional email attachment. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `_safe_destroy_log_dir` (function/method, line 136): Return a log directory that will survive a destructive cleanup. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `_with_logging` (function/method, line 177): Run a command with optional logging and MQTT notification. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `_resolve_dry_run` (function/method, line 226): Handle the resolve dry run step used by this module. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_init_config` (function/method, line 234): Write the selected complete packaged config profile. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_test_source` (function/method, line 253): Handle the cmd test source step used by this module. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_test_source._run` (function/method, line 256): Handle the run step used by this module. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `_refresh_state_metadata_from_timeshift` (function/method, line 274): Refresh mutable state metadata from one fast Timeshift list read. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_list_source` (function/method, line 282): List snapshots on the source machine. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_list_source._run` (function/method, line 292): Handle the run step used by this module. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_sync` (function/method, line 305): Handle the cmd sync step used by this module. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_sync._run_dry` (function/method, line 309): Handle the run dry step used by this module. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_sync._run_locked` (function/method, line 318): Handle the run locked step used by this module. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_prune` (function/method, line 335): Handle the cmd prune step used by this module. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_prune._run_dry` (function/method, line 339): Handle the run dry step used by this module. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_prune._run_locked` (function/method, line 347): Handle the run locked step used by this module. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_restore` (function/method, line 364): Restore one snapshot or the complete post-common backup chain into Timeshift. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_restore._run` (function/method, line 370): Handle the run step used by this module. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_create_manual` (function/method, line 421): Handle the cmd create manual step used by this module. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_create_manual._run` (function/method, line 424): Handle the run step used by this module. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_clear_state` (function/method, line 450): Guardedly remove the configured state_file with normal run logging. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_clear_state._run` (function/method, line 456): Handle the run step used by this module. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_delete_lock` (function/method, line 478): Guardedly remove the configured lock_file if it is stale, with logging. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_delete_lock._run` (function/method, line 484): Handle the run step used by this module. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_destroy_leftovers` (function/method, line 495): Destroy configured leftovers with normal run logging enabled. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_destroy_leftovers._run` (function/method, line 509): Handle the run step used by this module. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_show_state` (function/method, line 521): Handle the cmd show state step used by this module. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_show_state._run` (function/method, line 524): Handle the run step used by this module. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `build_parser` (function/method, line 567): Create the argparse parser and command-specific flag help. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `main` (function/method, line 805): Handle the main step used by this module. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

## `timeshift_btrfs_sync/commands.py`

**Module role:** Shared subprocess helpers.

**Why this module exists:** Runs commands and streaming pipelines with consistent logging, error capture, and optional buffering.

- `CommandError` (class, line 21): Raised when an external command exits with a non-zero status. **Why:** Runs commands and streaming pipelines with consistent logging, error capture, and optional buffering.

- `CommandError.__init__` (function/method, line 24): Perform the init step used by this module. **Why:** Runs commands and streaming pipelines with consistent logging, error capture, and optional buffering.

- `Completed` (class, line 39): Captured exit status and text streams for one command. **Why:** Runs commands and streaming pipelines with consistent logging, error capture, and optional buffering.

- `sudo_prefix` (function/method, line 47): Split a configured sudo prefix into argv parts. **Why:** Runs commands and streaming pipelines with consistent logging, error capture, and optional buffering.

- `quote_join` (function/method, line 55): Quote argv parts into one safe remote-shell command string. **Why:** Runs commands and streaming pipelines with consistent logging, error capture, and optional buffering.

- `remote_double_quote` (function/method, line 61): Return a shell-safe double-quoted argument for a remote shell command. **Why:** Runs commands and streaming pipelines with consistent logging, error capture, and optional buffering.

- `_merged_env` (function/method, line 84): Merge optional child-process environment variables. **Why:** Runs commands and streaming pipelines with consistent logging, error capture, and optional buffering.

- `run_local` (function/method, line 94): Run a local command and capture stdout/stderr. **Why:** Runs commands and streaming pipelines with consistent logging, error capture, and optional buffering.

- `_start_pipeline_readers` (function/method, line 151): Start tee readers from compact stream routing specs. **Why:** Runs commands and streaming pipelines with consistent logging, error capture, and optional buffering.

- `_failed_stderr` (function/method, line 170): Return captured pipeline stderr for streams that belong in failures. **Why:** Runs commands and streaming pipelines with consistent logging, error capture, and optional buffering.

- `_log_failed_streams` (function/method, line 176): Copy captured failed pipeline streams to .err. **Why:** Runs commands and streaming pipelines with consistent logging, error capture, and optional buffering.

- `stream_pipeline` (function/method, line 188): Stream left command into optional middle command, then right command. **Why:** Runs commands and streaming pipelines with consistent logging, error capture, and optional buffering.

## `timeshift_btrfs_sync/config.py`

**Module role:** TOML configuration loading and validation.

**Why this module exists:** Loads and validates the one current configuration schema used by every command.

- `_reject_unknown_keys` (function/method, line 34): Reject configuration entries that are not part of the current schema. **Why:** Loads and validates the one current configuration schema used by every command.

- `ManualSnapshotConfig` (class, line 42): Optional source-side Timeshift on-demand snapshot creation and cleanup. **Why:** Loads and validates the one current configuration schema used by every command.

- `SourceConfig` (class, line 76): Timeshift source and restore-target settings. **Why:** Loads and validates the one current configuration schema used by every command.

- `DestinationConfig` (class, line 117): Backup repository and normal local receive settings. **Why:** Loads and validates the one current configuration schema used by every command.

- `StreamConfig` (class, line 131): Optional pipeline display/buffering settings. **Why:** Loads and validates the one current configuration schema used by every command.

- `StreamConfig.command` (function/method, line 151): Return mbuffer command argv or None when disabled. **Why:** Loads and validates the one current configuration schema used by every command.

- `RetentionConfig` (class, line 165): Destination retention counts by Timeshift tag. **Why:** Loads and validates the one current configuration schema used by every command.

- `RetentionConfig.counts_by_tag` (function/method, line 184): Return retention counts keyed by Timeshift tag letters. **Why:** Loads and validates the one current configuration schema used by every command.

- `AppConfig` (class, line 190): Complete validated app configuration. **Why:** Loads and validates the one current configuration schema used by every command.

- `ConfigError` (class, line 208): Raised when the TOML config is invalid. **Why:** Loads and validates the one current configuration schema used by every command.

- `_table` (function/method, line 211): Perform the table step used by this module. **Why:** Loads and validates the one current configuration schema used by every command.

- `_optional_str` (function/method, line 217): Perform the optional str step used by this module. **Why:** Loads and validates the one current configuration schema used by every command.

- `_positive_int` (function/method, line 220): Perform the positive int step used by this module. **Why:** Loads and validates the one current configuration schema used by every command.

- `_stripped` (function/method, line 227): Perform the stripped step used by this module. **Why:** Loads and validates the one current configuration schema used by every command.

- `_bool` (function/method, line 230): Perform the bool step used by this module. **Why:** Loads and validates the one current configuration schema used by every command.

- `_int` (function/method, line 233): Perform the int step used by this module. **Why:** Loads and validates the one current configuration schema used by every command.

- `_as_str` (function/method, line 236): Perform the as str step used by this module. **Why:** Loads and validates the one current configuration schema used by every command.

- `_as_path` (function/method, line 241): Perform the as path step used by this module. **Why:** Loads and validates the one current configuration schema used by every command.

- `_as_bool` (function/method, line 244): Perform the as bool step used by this module. **Why:** Loads and validates the one current configuration schema used by every command.

- `_as_int` (function/method, line 251): Perform the as int step used by this module. **Why:** Loads and validates the one current configuration schema used by every command.

- `_string_list` (function/method, line 258): Perform the string list step used by this module. **Why:** Loads and validates the one current configuration schema used by every command.

- `load_config` (function/method, line 266): Read and validate TOML config. **Why:** Loads and validates the one current configuration schema used by every command.

## `timeshift_btrfs_sync/destroy.py`

**Module role:** Destructive setup retirement using the shared Btrfs tree engine.

**Why this module exists:** Implements guarded deletion of selected app-owned source-cache and destination trees.

- `DestroyResult` (class, line 26): Named wrapper around the shared tree-deletion result. **Why:** Implements guarded deletion of selected app-owned source-cache and destination trees.

- `_safe_cleanup_path` (function/method, line 33): Perform the safe cleanup path step used by this module. **Why:** Implements guarded deletion of selected app-owned source-cache and destination trees.

- `_confirm_or_raise` (function/method, line 46): Perform the confirm or raise step used by this module. **Why:** Implements guarded deletion of selected app-owned source-cache and destination trees.

- `_mode_text` (function/method, line 51): Perform the mode text step used by this module. **Why:** Implements guarded deletion of selected app-owned source-cache and destination trees.

- `_load_payload_state` (function/method, line 57): Perform the load payload state step used by this module. **Why:** Implements guarded deletion of selected app-owned source-cache and destination trees.

- `_result_by_label` (function/method, line 64): Perform the result by label step used by this module. **Why:** Implements guarded deletion of selected app-owned source-cache and destination trees.

- `_print_payload_match` (function/method, line 68): Perform the print payload match step used by this module. **Why:** Implements guarded deletion of selected app-owned source-cache and destination trees.

- `_print_result` (function/method, line 87): Perform the print result step used by this module. **Why:** Implements guarded deletion of selected app-owned source-cache and destination trees.

- `destroy_leftovers` (function/method, line 118): Plan and execute selected source/destination tree retirement. **Why:** Implements guarded deletion of selected app-owned source-cache and destination trees.

- `destroy_leftovers.handle` (function/method, line 172): Perform the handle step used by this module. **Why:** Implements guarded deletion of selected app-owned source-cache and destination trees.

## `timeshift_btrfs_sync/endpoint.py`

**Module role:** Unified command endpoints for local, Timeshift, and backup operations.

**Why this module exists:** Provides one local/SSH command transport used by Timeshift, backup, and destination operations.

- `CommandEndpoint` (class, line 19): Execute commands on one local or transported endpoint. **Why:** Provides one local/SSH command transport used by Timeshift, backup, and destination operations.

- `CommandEndpoint.for_source` (function/method, line 30): Perform the for source step used by this module. **Why:** Provides one local/SSH command transport used by Timeshift, backup, and destination operations.

- `CommandEndpoint.local` (function/method, line 34): Perform the local step used by this module. **Why:** Provides one local/SSH command transport used by Timeshift, backup, and destination operations.

- `CommandEndpoint.location` (property, line 38): Perform the location step used by this module. **Why:** Provides one local/SSH command transport used by Timeshift, backup, and destination operations.

- `CommandEndpoint.shell_command` (function/method, line 41): Return a safely quoted shell command for this endpoint. **Why:** Provides one local/SSH command transport used by Timeshift, backup, and destination operations.

- `CommandEndpoint.command` (function/method, line 46): Return process argv for a command executed on this endpoint. **Why:** Provides one local/SSH command transport used by Timeshift, backup, and destination operations.

- `CommandEndpoint.run_argv` (function/method, line 54): Execute one argv command through the endpoint transport. **Why:** Provides one local/SSH command transport used by Timeshift, backup, and destination operations.

- `CommandEndpoint.run_shell` (function/method, line 82): Execute one shell script through the endpoint transport. **Why:** Provides one local/SSH command transport used by Timeshift, backup, and destination operations.

## `timeshift_btrfs_sync/executor.py`

**Module role:** Generic ordered workflow action executor.

**Why this module exists:** Executes ordered workflow actions through the shared operation layers.

- `WorkflowExecutor` (class, line 14): Execute or preview a plan using one handler per action kind. **Why:** Executes ordered workflow actions through the shared operation layers.

- `WorkflowExecutor.execute` (function/method, line 22): Perform the execute step used by this module. **Why:** Executes ordered workflow actions through the shared operation layers.

## `timeshift_btrfs_sync/inventory.py`

**Module role:** Per-run Btrfs subvolume indexes for fewer SSH calls.

**Why this module exists:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `BtrfsIndex` (class, line 29): In-memory index of Btrfs subvolumes below one root path. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `BtrfsIndex.add` (function/method, line 40): Add or replace one indexed subvolume. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `BtrfsIndex.discard` (function/method, line 53): Remove one path and any known UUID lookup entries for it. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `BtrfsIndex.contains` (function/method, line 65): Return True when ``path`` is an indexed subvolume. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `BtrfsIndex.meta` (function/method, line 70): Return metadata for ``path`` if it was indexed. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `BtrfsIndex.remove_tree` (function/method, line 75): Remove a deleted path and all indexed descendants. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `SourceInventory` (class, line 85): One coherent source-side Timeshift/Btrfs inventory. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `SourceInventory.snapshot_names` (property, line 105): Return Timeshift timestamp names in sorted order. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `SourceInventory.meta` (function/method, line 111): Return source metadata from cache first, then snapshot-root index. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `_clean_uuid` (function/method, line 122): Normalize Btrfs UUID fields from list/show output. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `parse_subvolume_list` (function/method, line 131): Parse ``btrfs subvolume list -u -q -R`` output for one root. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `_paths_from_list_output` (function/method, line 157): Return absolute subvolume paths parsed from any ``btrfs subvolume list`` output. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `_mark_readonly_from_list` (function/method, line 171): Mark indexed paths read-only using one ``btrfs subvolume list -r`` result. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `build_local_btrfs_index` (function/method, line 187): Build a local Btrfs index with bulk list commands. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `_remote_bulk_index_script` (function/method, line 235): Return a POSIX shell script that bulk-lists source Btrfs metadata. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `build_source_btrfs_index` (function/method, line 281): Build a source Btrfs index in SSH or local mode. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `build_remote_btrfs_index` (function/method, line 313): Build a remote source index using one SSH command. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `_parse_remote_btrfs_index_result` (function/method, line 345): Parse one remote bulk-index section into a :class:`BtrfsIndex`. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `_parse_remote_btrfs_index_result.flush_list` (function/method, line 377): Perform the flush list step used by this module. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `_parse_remote_btrfs_index_result.flush_readonly` (function/method, line 385): Perform the flush readonly step used by this module. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `_remote_source_inventory_script` (function/method, line 445): Return one remote script for Timeshift, info.json, and both Btrfs roots. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `_extract_snapshot_info_json_frames` (function/method, line 527): Remove and parse the ``cat`` payloads from combined SSH output. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `_extract_snapshot_info_json_frames.replace` (function/method, line 544): Perform the replace step used by this module. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `_split_remote_source_inventory_output` (function/method, line 561): Split combined output into identity, Timeshift, info.json, and Btrfs sections. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `_current_process_identity` (function/method, line 634): Return the effective local account name and UID used to read metadata. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `_read_local_snapshot_info_json` (function/method, line 645): Read all local Timeshift control files without spawning commands. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `_record_missing_info_json_errors` (function/method, line 672): Record listed Timeshift dates that had no readable control file. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `build_source_inventory` (function/method, line 686): Build one coherent Timeshift/snapshot/cache source inventory. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `describe_source_inventory_changes` (function/method, line 809): Return concise human-readable differences between two inventories. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `describe_source_inventory_changes.compare_index` (function/method, line 822): Perform the compare index step used by this module. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

- `refresh_path` (function/method, line 861): Refresh one exact path through the shared Btrfs operation layer. **Why:** Builds authoritative Timeshift, source-cache, and destination inventories with bulk metadata reads.

## `timeshift_btrfs_sync/lock.py`

**Module role:** Local and SSH-held file locks for backup operations.

**Why this module exists:** Prevents concurrent local or remote operations from changing the same backup repository.

- `FileLock` (class, line 14): flock() based non-blocking exclusive lock on the local machine. **Why:** Prevents concurrent local or remote operations from changing the same backup repository.

- `FileLock.__init__` (function/method, line 17): Perform the init step used by this module. **Why:** Prevents concurrent local or remote operations from changing the same backup repository.

- `FileLock.__enter__` (function/method, line 21): Perform the enter step used by this module. **Why:** Prevents concurrent local or remote operations from changing the same backup repository.

- `FileLock.__exit__` (function/method, line 33): Perform the exit step used by this module. **Why:** Prevents concurrent local or remote operations from changing the same backup repository.

- `RemoteFileLock` (class, line 39): Hold the configured backup lock through one persistent SSH command. **Why:** Prevents concurrent local or remote operations from changing the same backup repository.

- `RemoteFileLock.__init__` (function/method, line 51): Perform the init step used by this module. **Why:** Prevents concurrent local or remote operations from changing the same backup repository.

- `RemoteFileLock.__enter__` (function/method, line 59): Perform the enter step used by this module. **Why:** Prevents concurrent local or remote operations from changing the same backup repository.

- `RemoteFileLock._terminate` (function/method, line 98): Perform the terminate step used by this module. **Why:** Prevents concurrent local or remote operations from changing the same backup repository.

- `RemoteFileLock.__exit__` (function/method, line 118): Perform the exit step used by this module. **Why:** Prevents concurrent local or remote operations from changing the same backup repository.

## `timeshift_btrfs_sync/log.py`

**Module role:** Split run logging for timeshift-btrfs-sync.

**Why this module exists:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `RunLogger` (class, line 32): Owns the split log files for one run. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `RunLogger.__post_init__` (function/method, line 38): Create the log directory and open the run log files. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `RunLogger.close` (function/method, line 71): Close all log files. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `RunLogger.attachment_paths` (function/method, line 81): Return run log files in the order useful for mail attachments. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `RunLogger._write` (function/method, line 91): Write text safely from possible stream-reader threads. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `RunLogger._remember_stderr` (function/method, line 98): Keep a small tail of stderr for failure notifications. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `RunLogger.last_stderr_tail` (function/method, line 106): Return the newest stderr text remembered for MQTT/error reports. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `RunLogger._line` (function/method, line 112): Write exactly one logical line. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `RunLogger.info` (function/method, line 119): Write a normal status line to .log. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `RunLogger.mbuffer` (function/method, line 124): Write one line to the .mbuffer transfer-progress log. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `RunLogger.btrfs_out` (function/method, line 129): Write one line to the .btrfs Btrfs verbose-output log. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `RunLogger.success` (function/method, line 134): Write one line to the .succes human-readable summary log. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `RunLogger.success_text` (function/method, line 139): Write a preformatted block to the .succes summary log. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `RunLogger.err` (function/method, line 146): Write an error/stderr line to .err and remember its tail. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `RunLogger.command` (function/method, line 153): Record a command that is about to run. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `RunLogger.completed` (function/method, line 176): Record the output from a normal captured command. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `RunLogger.pipeline_commands` (function/method, line 207): Record send/buffer/receive commands to the appropriate logs. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `RunLogger.pipeline_summary` (function/method, line 218): Record final pipeline status. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `RunLogger.stream_text` (function/method, line 226): Write live pipeline text to terminal and/or split log files. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `emit_success_summary` (function/method, line 254): Write a readable summary to the real terminal and .succes only. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `TeeTextIO` (class, line 270): Terminal stream wrapper that also writes normal app output to run logs. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `TeeTextIO.__init__` (function/method, line 283): Perform the init step used by this module. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `TeeTextIO.write` (function/method, line 290): Perform the write step used by this module. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `TeeTextIO.flush` (function/method, line 303): Perform the flush step used by this module. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `TeeTextIO.isatty` (function/method, line 306): Perform the isatty step used by this module. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `TeeTextIO.fileno` (function/method, line 309): Perform the fileno step used by this module. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `TeeTextIO.writable` (function/method, line 312): Perform the writable step used by this module. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `TeeTextIO.__getattr__` (function/method, line 315): Perform the getattr step used by this module. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `terminal_stdout` (function/method, line 323): Return the real terminal stdout, bypassing the run-log tee wrapper. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `terminal_stderr` (function/method, line 329): Return the real terminal stderr, bypassing the run-log tee wrapper. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `get_logger` (function/method, line 337): Return the active logger, if file logging is enabled. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `active_logger` (function/method, line 344): Temporarily install a run logger and tee app output to files. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `create_run_logger` (function/method, line 380): Create a logger when log_dir is configured; otherwise return None. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `tee_pipe_to_log` (function/method, line 402): Start a thread that reads bytes from a process pipe and logs them live. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `tee_pipe_to_log._reader` (function/method, line 421): Perform the reader step used by this module. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

## `timeshift_btrfs_sync/mail.py`

**Module role:** Optional email notifications for timeshift-btrfs-sync.

**Why this module exists:** Sends optional email notifications using the current run result and log attachments.

- `MailConfig` (class, line 20): SMTP settings for optional email notifications. **Why:** Sends optional email notifications using the current run result and log attachments.

- `MailConfig.resolved_password` (function/method, line 52): Return password from config value or password_file. **Why:** Sends optional email notifications using the current run result and log attachments.

- `_subject` (function/method, line 61): Create a short readable subject line. **Why:** Sends optional email notifications using the current run result and log attachments.

- `_body` (function/method, line 72): Create a fallback plain-text email body from the status payload. **Why:** Sends optional email notifications using the current run result and log attachments.

- `_success_body_from_paths` (function/method, line 101): Return the text content of the non-empty .succes file, if present. **Why:** Sends optional email notifications using the current run result and log attachments.

- `_filter_attachments` (function/method, line 118): Return existing attachment paths and human-readable skipped reasons. **Why:** Sends optional email notifications using the current run result and log attachments.

- `_attach_file` (function/method, line 148): Attach one file to an EmailMessage. **Why:** Sends optional email notifications using the current run result and log attachments.

- `send_status` (function/method, line 159): Send one optional SMTP status email. **Why:** Sends optional email notifications using the current run result and log attachments.

## `timeshift_btrfs_sync/maintenance.py`

**Module role:** Guarded maintenance commands for state and lock files.

**Why this module exists:** Implements guarded state and lock maintenance commands.

- `_confirm_or_raise` (function/method, line 21): Require an exact typed confirmation before destructive maintenance. **Why:** Implements guarded state and lock maintenance commands.

- `_safe_configured_file` (function/method, line 29): Return a normalized configured file path or raise for unsafe targets. **Why:** Implements guarded state and lock maintenance commands.

- `_looks_like_state_file` (function/method, line 44): Return True when an existing file appears to be ts-btrfs state. **Why:** Implements guarded state and lock maintenance commands.

- `_looks_like_lock_file` (function/method, line 63): Return True when an existing file looks like this app's simple lock file. **Why:** Implements guarded state and lock maintenance commands.

- `_print_header` (function/method, line 77): Print the common maintenance command warning block. **Why:** Implements guarded state and lock maintenance commands.

- `_require_real_confirmation` (function/method, line 90): Require real-mode flags and typed confirmations. **Why:** Implements guarded state and lock maintenance commands.

- `clear_state_file` (function/method, line 110): Remove the configured state.json file after explicit confirmation. **Why:** Implements guarded state and lock maintenance commands.

- `delete_lock_file` (function/method, line 160): Delete the configured lock file when no running process holds it. **Why:** Implements guarded state and lock maintenance commands.

## `timeshift_btrfs_sync/models.py`

**Module role:** Shared dataclasses for snapshots and subvolumes.

**Why this module exists:** Defines shared immutable and mutable data records used across workflows.

- `SubvolumeMeta` (class, line 9): Metadata for one Btrfs subvolume inside one Timeshift snapshot. **Why:** Defines shared immutable and mutable data records used across workflows.

- `SnapshotMeta` (class, line 22): Metadata for one Timeshift snapshot. **Why:** Defines shared immutable and mutable data records used across workflows.

- `SnapshotMeta.sort_key` (function/method, line 32): Timeshift timestamp names sort oldest-to-newest lexically. **Why:** Defines shared immutable and mutable data records used across workflows.

- `tags_text` (function/method, line 38): Return compact human text for Timeshift tags. **Why:** Defines shared immutable and mutable data records used across workflows.

## `timeshift_btrfs_sync/mqtt.py`

**Module role:** Optional MQTT notifications for timeshift-btrfs-sync.

**Why this module exists:** Publishes optional structured MQTT status messages.

- `MQTTConfig` (class, line 19): MQTT broker and publish settings. **Why:** Publishes optional structured MQTT status messages.

- `MQTTConfig.resolved_password` (function/method, line 41): Return password from config value or password_file. **Why:** Publishes optional structured MQTT status messages.

- `publish_status` (function/method, line 51): Publish one JSON MQTT status message. **Why:** Publishes optional structured MQTT status messages.

## `timeshift_btrfs_sync/notify.py`

**Module role:** Shared notification payload helpers.

**Why this module exists:** Combines terminal/run results with configured MQTT and email notifications.

- `utc_timestamp` (function/method, line 10): Return a compact ISO-8601 UTC timestamp for notifications. **Why:** Combines terminal/run results with configured MQTT and email notifications.

- `build_notification_payload` (function/method, line 16): Build the shared status payload used by MQTT and email. **Why:** Combines terminal/run results with configured MQTT and email notifications.

## `timeshift_btrfs_sync/paths.py`

**Module role:** Canonical path normalization and containment rules.

**Why this module exists:** Normalizes, maps, and validates managed local and remote paths safely.

- `normalize_source_path` (function/method, line 13): Normalize POSIX path text while preserving an intentionally empty value. **Why:** Normalizes, maps, and validates managed local and remote paths safely.

- `is_same_or_under` (function/method, line 23): Return true when ``path`` equals ``root`` or is below it. **Why:** Normalizes, maps, and validates managed local and remote paths safely.

- `is_local_same_or_under` (function/method, line 35): Return true when one local path resolves to ``root`` or below it. **Why:** Normalizes, maps, and validates managed local and remote paths safely.

- `is_under` (function/method, line 55): Return true only when ``path`` is strictly below ``root``. **Why:** Normalizes, maps, and validates managed local and remote paths safely.

- `listed_path_to_absolute` (function/method, line 67): Resolve a Btrfs filesystem-relative list path below a mounted root. **Why:** Normalizes, maps, and validates managed local and remote paths safely.

- `sort_deepest_first` (function/method, line 103): Deduplicate and order paths for child-before-parent deletion. **Why:** Normalizes, maps, and validates managed local and remote paths safely.

## `timeshift_btrfs_sync/payload_stats.py`

**Module role:** Normalized source/destination payload statistics for Btrfs snapshot trees.

**Why this module exists:** Calculates readable transfer and retention payload statistics.

- `PayloadTreeStats` (class, line 30): Normalized payload/container counts for one source or destination tree. **Why:** Calculates readable transfer and retention payload statistics.

- `PayloadTreeStats.total_payload` (property, line 47): Return the number of real cached/received payload subvolumes. **Why:** Calculates readable transfer and retention payload statistics.

- `PayloadTreeStats.total_cache_payload` (property, line 53): Return how many source payloads came from app-owned source cache. **Why:** Calculates readable transfer and retention payload statistics.

- `PayloadTreeStats.total_direct_payload` (property, line 59): Return how many source payloads came from protected Timeshift originals. **Why:** Calculates readable transfer and retention payload statistics.

- `normalize_path` (function/method, line 65): Normalize paths so source/destination comparisons ignore trailing slashes. **Why:** Calculates readable transfer and retention payload statistics.

- `_relative_parts` (function/method, line 71): Return path parts relative to root, or None if path is outside root. **Why:** Calculates readable transfer and retention payload statistics.

- `_recount_payload` (function/method, line 85): Rebuild per-subvolume counters from the normalized payload set. **Why:** Calculates readable transfer and retention payload statistics.

- `_add_payload` (function/method, line 93): Add a payload entry when relative parts end in a configured subvolume name. **Why:** Calculates readable transfer and retention payload statistics.

- `source_send_cache_stats` (function/method, line 106): Classify source send-cache subvolumes into payload and helper counts. **Why:** Calculates readable transfer and retention payload statistics.

- `destination_payload_stats` (function/method, line 129): Classify destination target subvolumes into received payload counts. **Why:** Calculates readable transfer and retention payload statistics.

- `direct_send_payload_stats` (function/method, line 152): Return payload entries streamed directly from protected Timeshift originals. **Why:** Calculates readable transfer and retention payload statistics.

- `merge_source_payload_stats` (function/method, line 184): Merge app-cache and protected direct-send payload into one source view. **Why:** Calculates readable transfer and retention payload statistics.

- `PayloadMatchStats` (class, line 207): Comparison between source send payload and destination received payload. **Why:** Calculates readable transfer and retention payload statistics.

- `PayloadMatchStats.source_only` (property, line 214): Return source payload entries not present on the destination. **Why:** Calculates readable transfer and retention payload statistics.

- `PayloadMatchStats.destination_only` (property, line 220): Return destination payload entries not present on the source side. **Why:** Calculates readable transfer and retention payload statistics.

- `PayloadMatchStats.ok` (property, line 226): Return True when source send payload and destination payload match. **Why:** Calculates readable transfer and retention payload statistics.

- `compare_payloads` (function/method, line 232): Return normalized source/destination payload comparison stats. **Why:** Calculates readable transfer and retention payload statistics.

- `_format_count_line` (function/method, line 238): Return an aligned summary line. **Why:** Calculates readable transfer and retention payload statistics.

- `render_payload_match` (function/method, line 244): Render the source/destination payload comparison block. **Why:** Calculates readable transfer and retention payload statistics.

## `timeshift_btrfs_sync/planning.py`

**Module role:** Pure workflow planning from a combined backup inventory.

**Why this module exists:** Builds side-effect-free ordered plans for sync, recovery, prune, and destructive cleanup.

- `ActionKind` (class, line 17): Define the ActionKind data or behavior used by this module. **Why:** Builds side-effect-free ordered plans for sync, recovery, prune, and destructive cleanup.

- `WorkflowAction` (class, line 28): Define the WorkflowAction data or behavior used by this module. **Why:** Builds side-effect-free ordered plans for sync, recovery, prune, and destructive cleanup.

- `WorkflowPlan` (class, line 36): Define the WorkflowPlan data or behavior used by this module. **Why:** Builds side-effect-free ordered plans for sync, recovery, prune, and destructive cleanup.

- `WorkflowPlan.add` (function/method, line 40): Perform the add step used by this module. **Why:** Builds side-effect-free ordered plans for sync, recovery, prune, and destructive cleanup.

- `plan_sync_queue` (function/method, line 52): Plan the oldest-to-newest sync queue without executing operations. **Why:** Builds side-effect-free ordered plans for sync, recovery, prune, and destructive cleanup.

- `plan_snapshot_recovery` (function/method, line 79): Plan one whole-date recovery in cache, destination, then state order. **Why:** Builds side-effect-free ordered plans for sync, recovery, prune, and destructive cleanup.

- `plan_prune_snapshot` (function/method, line 89): Perform the plan prune snapshot step used by this module. **Why:** Builds side-effect-free ordered plans for sync, recovery, prune, and destructive cleanup.

- `plan_destroy_targets` (function/method, line 102): Plan named endpoint/root destruction in the caller-provided order. **Why:** Builds side-effect-free ordered plans for sync, recovery, prune, and destructive cleanup.

## `timeshift_btrfs_sync/preflight.py`

**Module role:** Sync path preflight checks.

**Why this module exists:** Validates or creates only the paths each workflow is allowed to own.

- `PathPreflightError` (class, line 44): Raised before any destructive/creating sync work when required paths fail. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `PathCheck` (class, line 49): One configured path availability result. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `_shell_words` (function/method, line 60): Return a shell-safe string for configured command-prefix words. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `_parse_path_check_output` (function/method, line 66): Parse source-path preflight sentinel lines into structured checks. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `_source_snapshot_root_script` (function/method, line 99): Build a source script that validates Timeshift-owned source.snapshot_root. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `_cache_root_check_script` (function/method, line 167): Build a source script that validates or creates source.cache_root. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `_combined_source_path_check_script` (function/method, line 243): Run both source-root preflight checks inside one source command. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `_source_path_checks` (function/method, line 275): Check/create both source roots with at most one SSH command. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `_parent_of_path` (function/method, line 354): Return the immediate parent path used for exact-path creation checks. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `_local_btrfs_result` (function/method, line 361): Run one local destination sudo+btrfs command for preflight checks. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `_compact_process_error` (function/method, line 373): Return compact stderr/stdout text from a failed subprocess. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `_compact_os_error` (function/method, line 380): Return compact text for local filesystem creation errors. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `_print_check_block` (function/method, line 386): Print one human-readable preflight result block. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `_raise_for_failed_checks` (function/method, line 401): Raise a hard preflight error when any check failed. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `ensure_local_helper_dir` (function/method, line 411): Ensure one local helper directory exists. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `prepare_lock_path` (function/method, line 565): Create/verify the lock directory before other sync/prune directories. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `prepare_destination_helper_paths` (function/method, line 597): Create/verify local destination helper folders used by sync/prune. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `_local_target_path_check` (function/method, line 644): Check/create destination.target_root locally. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `check_required_sync_paths` (function/method, line 786): Verify/create required configured roots before manual snapshot creation or send. **Why:** Validates or creates only the paths each workflow is allowed to own.

## `timeshift_btrfs_sync/restore.py`

**Module role:** Restore backed-up snapshots into Timeshift's native Btrfs layout.

**Why this module exists:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `RestoreError` (class, line 40): Raised when backups cannot be imported safely into Timeshift. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `TimeshiftOsIdentity` (class, line 45): Stable Timeshift metadata used to identify one OS installation. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `BackupSnapshot` (class, line 54): One validated local or SSH backup snapshot available for restore. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `BackupDirectoryRecord` (class, line 65): Ordinary filesystem facts for one backup timestamp directory. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `BackupRepository` (class, line 76): Access one local or SSH backup repository through one transport layer. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `BackupRepository.from_config` (function/method, line 85): Perform the from config step used by this module. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `BackupRepository.root` (property, line 97): Perform the root step used by this module. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `BackupRepository.snapshots_root` (property, line 101): Perform the snapshots root step used by this module. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `BackupRepository.environment` (property, line 105): Perform the environment step used by this module. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `BackupRepository.location_label` (property, line 109): Perform the location label step used by this module. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `BackupRepository.load_state` (function/method, line 112): Read and validate state.json from the same endpoint as the backup. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `BackupRepository.scan_directories` (function/method, line 164): Read direct date entries and all info.json files in one endpoint call. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `BackupRepository.btrfs_index` (function/method, line 233): Build one local or SSH Btrfs index for the complete backup tree. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `_effective_send_uuid` (function/method, line 251): Return the UUID identity carried by a Btrfs send stream. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `_info_os_identity` (function/method, line 265): Return stable Timeshift OS identity while ignoring per-snapshot fields. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `_parse_info_json` (function/method, line 285): Parse one Timeshift control file and extract its stable OS identity. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `_same_os_identity` (function/method, line 297): Return whether two Timeshift identities prove the same OS installation. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `_consistent_backup_identity` (function/method, line 308): Require one non-conflicting OS identity across the selected backup set. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `_source_info_identities` (function/method, line 335): Parse stable OS identities from the coherent source info.json inventory. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `_compare_repository_os_identity` (function/method, line 348): Compare one backup identity with all current Timeshift control files. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `RestorePlan` (class, line 376): A side-effect-free single or chain restore plan. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `RestorePlan.seed_name` (property, line 393): Perform the seed name step used by this module. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `_source_path_exists` (function/method, line 397): Perform the source path exists step used by this module. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `_privileged_argv` (function/method, line 411): Perform the privileged argv step used by this module. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `_write_source_info_json` (function/method, line 415): Write exact captured metadata through the configured source privilege prefix. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `_validate_backup_snapshot` (function/method, line 456): Validate one backup date, payload set, metadata file, and Btrfs identity. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `_discover_backups` (function/method, line 518): Return selected or all valid backups ordered by Timeshift timestamp. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `_source_snapshots` (function/method, line 543): Read one coherent source Timeshift/Btrfs/info.json inventory. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `_find_latest_common_parent` (function/method, line 572): Find the newest date proven common by UUID state and info.json identity. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `_find_reusable_receive_parent` (function/method, line 639): Find the exact read-only source subvolumes required for first incremental receive. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `_build_restore_plan` (function/method, line 705): Build a single or complete-chain restore plan without changing either side. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `_remove_restore_directory` (function/method, line 802): Remove one exact app-created ordinary restore directory and its payloads. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `_cleanup_restore_attempt` (function/method, line 856): Roll back only directories created by the current restore attempt. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `_print_restored_snapshot_retention_warning` (function/method, line 916): Explain that restored Timeshift tags remain subject to normal retention. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `_print_restore_plan` (function/method, line 933): Perform the print restore plan step used by this module. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

- `restore_backups` (function/method, line 999): Restore one snapshot or a complete backup chain into Timeshift. **Why:** Restores local or SSH backup repositories into local or SSH Timeshift layouts through one shared planner and execution loop.

## `timeshift_btrfs_sync/retention.py`

**Module role:** Destination retention/pruning logic.

**Why this module exists:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `PrunePlan` (class, line 32): Dry-run friendly prune plan. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `PrunePlan.add_keep` (function/method, line 39): Mark a snapshot as kept and remember the human reason. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `PrunePlan.add_delete` (function/method, line 46): Mark a snapshot as deletable only when it is not already protected. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `_is_app_created_ondemand` (function/method, line 54): Return true when a state entry is a tag O snapshot with the app marker. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `_delete_reason_for_snapshot` (function/method, line 66): Explain why a snapshot is outside the active retention rules. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `_delete_reasons` (function/method, line 102): Return delete reasons without the internal prefix. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `_source_cache_delete_paths` (function/method, line 111): Return app-owned source send-cache paths for a prune decision. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `_protected_timeshift_send_paths` (function/method, line 156): Return direct Timeshift send paths that prune must never delete. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `_destination_delete_paths` (function/method, line 186): Return tracked destination subvolume paths for a prune decision. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `source_snapshot_state` (function/method, line 197): Return temporary state-like data from source Timeshift snapshots. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `initial_sync_keep_names` (function/method, line 222): Return source snapshot names that a fresh destination should seed. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `_cleanup_source_cache_for_pruned_snapshot` (function/method, line 233): Delete one pruned snapshot's app-owned cache through the shared tree engine. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `build_prune_plan` (function/method, line 280): Build retention plan from state without deleting anything. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `_delete_destination_snapshot_for_prune` (function/method, line 365): Delete one destination date through the shared tree engine. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `_delete_prune_item` (function/method, line 391): Execute one pure prune plan and remove state after both trees are gone. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `_delete_prune_item.delete_destination` (function/method, line 417): Perform the delete destination step used by this module. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `_delete_prune_item.delete_cache` (function/method, line 422): Perform the delete cache step used by this module. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `_delete_prune_item.remove_state` (function/method, line 434): Perform the remove state step used by this module. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `print_prune_plan` (function/method, line 451): Write an easy-to-read retention summary to terminal and .succes. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `prune` (function/method, line 497): Apply destination retention rules. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

## `timeshift_btrfs_sync/source.py`

**Module role:** Command runner for local or SSH Timeshift and backup endpoints.

**Why this module exists:** Provides the shared local/SSH transport used for Timeshift and remote-backup endpoints.

- `SourceRunner` (class, line 12): Run commands through one local or SSH endpoint. **Why:** Provides the shared local/SSH transport used for Timeshift and remote-backup endpoints.

- `SourceRunner.from_mode` (function/method, line 24): Create a local or SSH command runner from one validated mode. **Why:** Provides the shared local/SSH transport used for Timeshift and remote-backup endpoints.

- `SourceRunner.from_config` (function/method, line 36): Create the configured Timeshift source runner. **Why:** Provides the shared local/SSH transport used for Timeshift and remote-backup endpoints.

- `SourceRunner.uses_ssh` (property, line 42): Return True when source commands are executed through SSH. **Why:** Provides the shared local/SSH transport used for Timeshift and remote-backup endpoints.

- `SourceRunner.location` (property, line 48): Return the metadata location label used by Btrfs helpers. **Why:** Provides the shared local/SSH transport used for Timeshift and remote-backup endpoints.

- `SourceRunner.command` (function/method, line 53): Return argv that runs one source-side shell command. **Why:** Provides the shared local/SSH transport used for Timeshift and remote-backup endpoints.

- `SourceRunner.run` (function/method, line 60): Run one source-side command and capture stdout/stderr. **Why:** Provides the shared local/SSH transport used for Timeshift and remote-backup endpoints.

- `SourceRunner.environment` (function/method, line 87): Return environment needed for streaming source commands. **Why:** Provides the shared local/SSH transport used for Timeshift and remote-backup endpoints.

- `SourceRunner.test` (function/method, line 94): Verify that the source command endpoint is usable. **Why:** Provides the shared local/SSH transport used for Timeshift and remote-backup endpoints.

## `timeshift_btrfs_sync/ssh.py`

**Module role:** SSH command construction.

**Why this module exists:** Builds and validates SSH commands, authentication, and optional connection reuse.

- `_is_relative_to` (function/method, line 15): Return True when path is root or below root without broad string matching. **Why:** Builds and validates SSH commands, authentication, and optional connection reuse.

- `validate_control_path_safety` (function/method, line 25): Create and validate a private SSH ControlPath socket directory. **Why:** Builds and validates SSH commands, authentication, and optional connection reuse.

- `SSHConfig` (class, line 95): Connection and SSH transport settings. **Why:** Builds and validates SSH commands, authentication, and optional connection reuse.

- `SSHConfig.target` (property, line 112): Return host or user@host. **Why:** Builds and validates SSH commands, authentication, and optional connection reuse.

- `SSHConfig.uses_password_auth` (property, line 118): Return True when sshpass is needed. **Why:** Builds and validates SSH commands, authentication, and optional connection reuse.

- `SSHConfig._read_password` (function/method, line 123): Read password from TOML or password_file. **Why:** Builds and validates SSH commands, authentication, and optional connection reuse.

- `SSHConfig.environment` (function/method, line 132): Return environment variables required by sshpass. **Why:** Builds and validates SSH commands, authentication, and optional connection reuse.

- `SSHConfig.base_command` (function/method, line 140): Build base SSH argv; remote command is appended later. **Why:** Builds and validates SSH commands, authentication, and optional connection reuse.

- `SSHRunner` (class, line 165): Run remote commands through SSH. **Why:** Builds and validates SSH commands, authentication, and optional connection reuse.

- `SSHRunner.__init__` (function/method, line 168): Perform the init step used by this module. **Why:** Builds and validates SSH commands, authentication, and optional connection reuse.

- `SSHRunner.command` (function/method, line 171): Return argv for one SSH remote command. **Why:** Builds and validates SSH commands, authentication, and optional connection reuse.

- `SSHRunner.run` (function/method, line 176): Run a remote command and capture stdout/stderr. **Why:** Builds and validates SSH commands, authentication, and optional connection reuse.

- `SSHRunner.environment` (function/method, line 202): Return SSH environment for streaming pipeline calls. **Why:** Builds and validates SSH commands, authentication, and optional connection reuse.

- `SSHRunner.test` (function/method, line 207): Verify SSH works and stdout is not polluted by banners. **Why:** Builds and validates SSH commands, authentication, and optional connection reuse.

## `timeshift_btrfs_sync/state.py`

**Module role:** Persistent local state for completed transfers.

**Why this module exists:** Validates, resolves, reads, and writes the current state schema.

- `empty_state` (function/method, line 28): Return a new empty state document. **Why:** Validates, resolves, reads, and writes the current state schema.

- `_safe_relative_path` (function/method, line 34): Return a normalized destination-relative path or raise ValueError. **Why:** Validates, resolves, reads, and writes the current state schema.

- `_safe_source_relative_path` (function/method, line 46): Return a normalized safe POSIX path relative to a configured source root. **Why:** Validates, resolves, reads, and writes the current state schema.

- `_normalize_source_root` (function/method, line 65): Return one normalized absolute-style POSIX source root. **Why:** Validates, resolves, reads, and writes the current state schema.

- `_source_path_relative_to_root` (function/method, line 72): Return ``path`` relative to ``root`` when it is currently below that root. **Why:** Validates, resolves, reads, and writes the current state schema.

- `_expected_snapshot_relative_path` (function/method, line 90): Return the canonical ``<snapshot>/<subvolume>`` source-relative path. **Why:** Validates, resolves, reads, and writes the current state schema.

- `source_path_to_relative` (function/method, line 98): Convert a current source path to canonical configured-root-relative state form. **Why:** Validates, resolves, reads, and writes the current state schema.

- `resolve_source_path` (function/method, line 124): Resolve a current root-relative state path under its configured source root. **Why:** Validates, resolves, reads, and writes the current state schema.

- `destination_path_to_relative` (function/method, line 143): Convert a current destination path to target-root-relative state form. **Why:** Validates, resolves, reads, and writes the current state schema.

- `resolve_destination_path` (function/method, line 155): Resolve a current target-root-relative state destination path. **Why:** Validates, resolves, reads, and writes the current state schema.

- `send_path_kind_for_state_subvolume` (function/method, line 160): Return the explicitly stored current send-path ownership kind. **Why:** Validates, resolves, reads, and writes the current state schema.

- `_source_root_for_kind` (function/method, line 168): Return the configured source root used by one stored send-path kind. **Why:** Validates, resolves, reads, and writes the current state schema.

- `resolve_state_send_path` (function/method, line 180): Resolve stored ``send_path`` under its current configured source root. **Why:** Validates, resolves, reads, and writes the current state schema.

- `_reject_unknown_state_keys` (function/method, line 213): Perform the reject unknown state keys step used by this module. **Why:** Validates, resolves, reads, and writes the current state schema.

- `validate_state_document` (function/method, line 219): Validate the complete current state schema before any workflow uses it. **Why:** Validates, resolves, reads, and writes the current state schema.

- `load_state` (function/method, line 297): Load and validate the current state document, or return an empty one when absent. **Why:** Validates, resolves, reads, and writes the current state schema.

- `save_state` (function/method, line 309): Validate and atomically write the current state document. **Why:** Validates, resolves, reads, and writes the current state schema.

- `refresh_snapshot_metadata_from_source` (function/method, line 328): Refresh mutable Timeshift metadata for already-known snapshots. **Why:** Validates, resolves, reads, and writes the current state schema.

- `snapshot_is_synced` (function/method, line 355): Return True when a snapshot is recorded as fully synced. **Why:** Validates, resolves, reads, and writes the current state schema.

- `_kind_for_absolute_source_path` (function/method, line 367): Classify a current absolute source path by configured ownership root. **Why:** Validates, resolves, reads, and writes the current state schema.

- `mark_subvolume_synced` (function/method, line 384): Record one successful send/receive using only root-relative state paths. **Why:** Validates, resolves, reads, and writes the current state schema.

- `state_send_path_is_app_cache` (function/method, line 499): Return True when the stored send path belongs to the app cache. **Why:** Validates, resolves, reads, and writes the current state schema.

- `state_send_path_is_protected_timeshift_original` (function/method, line 504): Return True when the stored send path belongs to Timeshift. **Why:** Validates, resolves, reads, and writes the current state schema.

- `remove_snapshot_from_state` (function/method, line 509): Remove a pruned snapshot from state. **Why:** Validates, resolves, reads, and writes the current state schema.

- `refresh_state_metadata_and_report` (function/method, line 515): Refresh only Timeshift tags/comment/created/path, report, and save. **Why:** Validates, resolves, reads, and writes the current state schema.

- `latest_synced_before` (function/method, line 539): Return newest older synced parent candidate. **Why:** Validates, resolves, reads, and writes the current state schema.

## `timeshift_btrfs_sync/sync.py`

**Module role:** Main destination-pull sync workflow.

**Why this module exists:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `SyncError` (class, line 47): Raised for sync safety errors. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_local_meta` (function/method, line 51): Perform the local meta step used by this module. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_source_meta` (function/method, line 57): Return source metadata, preferring bulk indexes over one-off probes. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_human_blank` (function/method, line 81): Print one blank line to separate human-readable status blocks. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_human_rule` (function/method, line 87): Print a visual separator with blank lines around it. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_record_sync_event` (function/method, line 96): Add one planned or completed transfer to the run summary. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_print_sync_summary` (function/method, line 125): Write a terminal-friendly transfer summary to terminal and .succes. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `prepare_destination` (function/method, line 171): Create/validate destination helper folders before writes. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `list_source_snapshots` (function/method, line 191): Discover source Timeshift snapshots. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `source_snapshot_index` (function/method, line 214): Perform the source snapshot index step used by this module. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_snapshots_from_source_inventory` (function/method, line 218): Build Timeshift snapshot objects from one coherent source inventory. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_required_pipeline_source_changes` (function/method, line 236): Return identity changes to source paths required by current work. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `confirm_source_identity_before_manual_snapshot` (function/method, line 275): Print and enforce the shared manual-snapshot source identity guard. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_is_app_manual_snapshot` (function/method, line 327): Return True for source Timeshift O snapshots created by this app. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_pending_app_manual_snapshots` (function/method, line 343): Return app-created on-demand snapshots that still need syncing. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_maybe_create_manual_snapshot` (function/method, line 368): Optionally create a source Timeshift tag O snapshot before sync. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_snapshots_in_sync_order` (function/method, line 457): Return source snapshots oldest-to-newest for Btrfs send. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_select_initial_sync_snapshots` (function/method, line 463): Return retention-kept source snapshots for a fresh destination seed. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `print_snapshot_table` (function/method, line 482): Print source snapshots in table form. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_dest_subvolume_path` (function/method, line 493): Return the final local path for one received subvolume. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_target_snapshot_dir` (function/method, line 503): Return the managed destination date subvolume passed to `btrfs receive`. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_destination_info_json_path` (function/method, line 513): Return the destination Timeshift control-file path for one snapshot. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_ensure_destination_snapshot_subvolume` (function/method, line 519): Create or validate one managed destination date subvolume. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_validate_destination_snapshot_layout` (function/method, line 569): Refuse ordinary/symlinked date entries after exact Btrfs verification. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_atomic_write_snapshot_info_json` (function/method, line 630): Atomically write one captured Timeshift ``info.json`` file. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_require_snapshot_info_json` (function/method, line 663): Return captured control-file content or raise a precise sync error. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_sync_snapshot_info_json` (function/method, line 697): Create or refresh destination ``info.json`` for one complete snapshot. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_destination_has_existing_snapshots` (function/method, line 737): Return true only when a date directory contains a configured payload subvolume. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_snapshot_destination_paths_exist` (function/method, line 758): Return True only when every expected destination subvolume path exists. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_preview_send_path` (function/method, line 763): Return the send path that would be used, without creating cache snapshots. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_send_path_kind_text` (function/method, line 777): Return human text explaining who owns the selected send path. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_ensure_source_send_path` (function/method, line 787): Resolve one real send path through the shared cache operation. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_cleanup_incomplete_destination_receive` (function/method, line 814): Delete one exact incomplete destination Btrfs child before retrying. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_cleanup_source_cache_snapshot_version` (function/method, line 844): Delete one app-owned cache date through the shared tree engine. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_cleanup_destination_snapshot_version` (function/method, line 875): Delete one destination date through the shared tree engine. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_refresh_snapshot_source_subvolumes_live` (function/method, line 904): Return configured source subvolumes, preferring the bulk index. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_snapshot_destination_has_any_path` (function/method, line 933): Return True when the destination date folder or configured children exist. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_snapshot_state_is_complete_with_destination` (function/method, line 942): Return True only when state and destination contain every configured subvolume. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_recover_snapshot_version` (function/method, line 949): Remove stale current-version traces from cache, destination, and state. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_recover_snapshot_version.handle` (function/method, line 982): Perform the handle step used by this module. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_prepare_snapshot_for_transfer_or_recover` (function/method, line 1004): Return True when a snapshot can be transferred, False when skipped. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_recover_stale_state_snapshots_missing_from_source` (function/method, line 1078): Clean incomplete state entries whose Timeshift source name is gone. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_read_local_destination_parent_metadata` (function/method, line 1110): Read metadata for the destination snapshot that would be the receiver parent. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_match_source_path_to_destination_received_uuid` (function/method, line 1132): Check whether a source subvolume UUID matches the destination identity. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_select_verified_parent_send_path` (function/method, line 1186): Select a safe source parent path for incremental send without recreating it. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_select_verified_parent_send_path.add_candidate` (function/method, line 1216): Perform the add candidate step used by this module. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_state_uuid_values_for_path` (function/method, line 1294): Return the current state UUID that identifies one source candidate. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_find_confirmed_sync_floor` (function/method, line 1311): Return newest state snapshot that still exists on source and matches UUIDs. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_destination_snapshot_names` (function/method, line 1438): Return destination snapshot folder names sorted oldest-to-newest. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_expected_original_source_path` (function/method, line 1447): Return the Timeshift-owned original source path for one snapshot/subvolume. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_source_cache_meta_by_uuid` (function/method, line 1453): Return indexed read-only source-cache metadata for an exact UUID match. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_match_existing_destination_to_source` (function/method, line 1472): Match one existing destination subvolume to an exact source/cache UUID. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_recover_state_from_existing_destination` (function/method, line 1543): Rebuild missing/empty state.json from proven source/destination matches. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_filesystem_parent_candidates` (function/method, line 1668): Find local destination parent candidates by matching snapshot names. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_select_parent` (function/method, line 1692): Choose the newest valid incremental parent. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_verify_sync_viability_before_manual_snapshot` (function/method, line 1836): Prove sync can start before asking Timeshift to create a snapshot. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `_verify_sync_viability_before_manual_snapshot.verify_parent_for` (function/method, line 1893): Perform the verify parent for step used by this module. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `sync_once` (function/method, line 1964): Run one sync pass. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `sync_once.load_source_inventory` (function/method, line 2006): Build and report one coherent source inventory generation. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `sync_once.build_snapshot_queue` (function/method, line 2165): Build one pure oldest-to-newest sync plan, then return its snapshot queue. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

- `sync_once.recover_from_source_inventory_change` (function/method, line 2208): Recover one failed snapshot version and rebuild all source lists. **Why:** Coordinates complete source discovery, full/incremental transfer, recovery, metadata, and optional prune.

## `timeshift_btrfs_sync/timeshift.py`

**Module role:** Timeshift command wrappers and parser for `timeshift --list`.

**Why this module exists:** Parses Timeshift output and constructs current Timeshift commands and metadata.

- `timeshift_cmd` (function/method, line 17): Build a source-side shell command that invokes sudo+timeshift. **Why:** Parses Timeshift output and constructs current Timeshift commands and metadata.

- `normalize_tags` (function/method, line 23): Return unique Timeshift tag letters found in text. **Why:** Parses Timeshift output and constructs current Timeshift commands and metadata.

- `parse_timeshift_list` (function/method, line 33): Parse Timeshift snapshot names and tag/comment text. **Why:** Parses Timeshift output and constructs current Timeshift commands and metadata.

- `list_source_snapshots` (function/method, line 66): Discover source snapshots through SSH or local source commands. **Why:** Parses Timeshift output and constructs current Timeshift commands and metadata.

- `create_remote_manual_snapshot_cmd` (function/method, line 107): Build the Timeshift manual/on-demand snapshot create command. **Why:** Parses Timeshift output and constructs current Timeshift commands and metadata.

- `create_source_manual_snapshot` (function/method, line 126): Create a source Timeshift on-demand snapshot through SSH or locally. **Why:** Parses Timeshift output and constructs current Timeshift commands and metadata.

## `timeshift_btrfs_sync/tree_ops.py`

**Module role:** Single Btrfs tree discovery, deletion, and post-verification engine.

**Why this module exists:** Discovers and deletes complete Btrfs trees deepest-first with strict verification.

- `TreeDeleteResult` (class, line 15): Define the TreeDeleteResult data or behavior used by this module. **Why:** Discovers and deletes complete Btrfs trees deepest-first with strict verification.

- `TreeDeleteResult.success` (property, line 26): Perform the success step used by this module. **Why:** Discovers and deletes complete Btrfs trees deepest-first with strict verification.

- `_path_exists` (function/method, line 31): Perform the path exists step used by this module. **Why:** Discovers and deletes complete Btrfs trees deepest-first with strict verification.

- `discover_subvolume_tree` (function/method, line 42): Discover a complete nested Btrfs tree in one endpoint list command. **Why:** Discovers and deletes complete Btrfs trees deepest-first with strict verification.

- `list_direct_entries` (function/method, line 68): List exact direct children with shell built-ins on either endpoint. **Why:** Discovers and deletes complete Btrfs trees deepest-first with strict verification.

- `_validate_confirmations` (function/method, line 84): Perform the validate confirmations step used by this module. **Why:** Discovers and deletes complete Btrfs trees deepest-first with strict verification.

- `_verify_absent` (function/method, line 101): Perform the verify absent step used by this module. **Why:** Discovers and deletes complete Btrfs trees deepest-first with strict verification.

- `delete_subvolume_tree` (function/method, line 118): Delete one managed tree deepest-first and prove the root is absent. **Why:** Discovers and deletes complete Btrfs trees deepest-first with strict verification.

## `tools/pyinstaller_entry.py`

**Module role:** Small PyInstaller entry point for building the ts-btrfs executable.

**Why this module exists:** Provides the executable entry point used by PyInstaller builds.

No runtime classes or functions are defined in this file.
