# Commented code map

This map describes every current runtime/build class, function, method, property, and CLI command. Each entry states what the symbol does and why that responsibility is kept there.

## `scripts/build_pyinstaller.py`

**Module role:** Build ts-btrfs executables with PyInstaller.

**Why this module exists:** Builds the current package as supported PyInstaller executable formats.

- `build_args` (function, line 23): Return the PyInstaller argument list for one build mode. **Why:** Builds the current package as supported PyInstaller executable formats.

- `run_pyinstaller` (function, line 50): Run PyInstaller with a useful error if it is not installed. **Why:** Builds the current package as supported PyInstaller executable formats.

- `main` (function, line 66): Parse arguments and run the requested build. **Why:** Builds the current package as supported PyInstaller executable formats.

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

- `_parse_listed_subvolumes` (function, line 32): Parse numeric ID, containing-parent ID, and raw path fields. **Why:** Centralizes Btrfs command construction and parsing so every workflow applies the same metadata and deletion rules.

- `_descendant_list_paths` (function, line 56): Return only numeric descendants of ``root_id`` from one full list. **Why:** Centralizes Btrfs command construction and parsing so every workflow applies the same metadata and deletion rules.

- `clean_uuid` (function, line 73): Internal function for clean uuid. **Why:** Centralizes Btrfs command construction and parsing so every workflow applies the same metadata and deletion rules.

- `parse_subvolume_show` (function, line 78): Parse UUID and read-only fields from ``btrfs subvolume show``. **Why:** Centralizes Btrfs command construction and parsing so every workflow applies the same metadata and deletion rules.

- `BtrfsOps` (class, line 104): Btrfs command facade for one local or source endpoint. **Why:** Centralizes Btrfs command construction and parsing so every workflow applies the same metadata and deletion rules.

- `BtrfsOps.prefix` (property, line 112): Internal function for prefix. **Why:** Keeps this operation inside `BtrfsOps` so callers cannot bypass the class's endpoint and validation rules.

- `BtrfsOps.argv` (method, line 115): Internal function for argv. **Why:** Keeps this operation inside `BtrfsOps` so callers cannot bypass the class's endpoint and validation rules.

- `BtrfsOps.run` (method, line 118): Internal function for run. **Why:** Keeps this operation inside `BtrfsOps` so callers cannot bypass the class's endpoint and validation rules.

- `BtrfsOps.meta` (method, line 133): Return exact-path subvolume metadata or ``None`` for an optional miss. **Why:** Keeps this operation inside `BtrfsOps` so callers cannot bypass the class's endpoint and validation rules.

- `BtrfsOps.list_children` (method, line 152): Return all descendants selected from one Btrfs containment graph. **Why:** Keeps this operation inside `BtrfsOps` so callers cannot bypass the class's endpoint and validation rules.

- `BtrfsOps.create` (method, line 171): Internal function for create. **Why:** Keeps this operation inside `BtrfsOps` so callers cannot bypass the class's endpoint and validation rules.

- `BtrfsOps.snapshot` (method, line 174): Create one exact writable or read-only Btrfs snapshot. **Why:** Keeps this operation inside `BtrfsOps` so callers cannot bypass the class's endpoint and validation rules.

- `BtrfsOps.delete` (method, line 190): Internal function for delete. **Why:** Keeps this operation inside `BtrfsOps` so callers cannot bypass the class's endpoint and validation rules.

- `BtrfsOps.send_command` (method, line 205): Internal function for send command. **Why:** Keeps this operation inside `BtrfsOps` so callers cannot bypass the class's endpoint and validation rules.

- `BtrfsOps.receive_command` (method, line 226): Internal function for receive command. **Why:** Keeps this operation inside `BtrfsOps` so callers cannot bypass the class's endpoint and validation rules.

- `BtrfsOps.set_readonly` (method, line 233): Set the Btrfs subvolume read-only property explicitly. **Why:** Keeps this operation inside `BtrfsOps` so callers cannot bypass the class's endpoint and validation rules.

- `BtrfsOps.batch_delete` (method, line 238): Delete exact paths in one endpoint command and validate confirmations. **Why:** Keeps this operation inside `BtrfsOps` so callers cannot bypass the class's endpoint and validation rules.

## `timeshift_btrfs_sync/cache_ops.py`

**Module role:** Single source send-cache operation used by sync and recovery.

**Why this module exists:** Keeps exact send-cache creation and reuse in one place, preventing nested or identity-mismatched cache snapshots.

- `_safe_name` (function, line 14): Internal function for safe name. **Why:** Keeps exact send-cache creation and reuse in one place, preventing nested or identity-mismatched cache snapshots.

- `cache_parent_path` (function, line 20): Internal function for cache parent path. **Why:** Keeps exact send-cache creation and reuse in one place, preventing nested or identity-mismatched cache snapshots.

- `cache_child_path` (function, line 24): Internal function for cache child path. **Why:** Keeps exact send-cache creation and reuse in one place, preventing nested or identity-mismatched cache snapshots.

- `validate_cache_snapshot` (function, line 28): Prove an exact cache child is a safe read-only snapshot of ``original``. **Why:** Prevents stale or unrelated retained cache snapshots from being reused after a destination-only reset.

- `CacheManager` (class, line 61): Ensure exact reusable send snapshots without nested cache creation. **Why:** Keeps exact send-cache creation and reuse in one place, preventing nested or identity-mismatched cache snapshots.

- `CacheManager.__init__` (method, line 64): Internal function for init. **Why:** Keeps this operation inside `CacheManager` so callers cannot bypass the class's endpoint and validation rules.

- `CacheManager._ensure_subvolume` (method, line 69): Internal function for ensure subvolume. **Why:** Keeps this operation inside `CacheManager` so callers cannot bypass the class's endpoint and validation rules.

- `CacheManager._probe_existing_from_parent` (method, line 96): Find one exact cache child from an authoritative parent-scoped list. **Why:** Keeps this operation inside `CacheManager` so callers cannot bypass the class's endpoint and validation rules.

- `CacheManager._probe_create_verify` (method, line 192): Probe, create if absent, and verify exact cache path in one command. **Why:** Keeps this operation inside `CacheManager` so callers cannot bypass the class's endpoint and validation rules.

- `CacheManager.ensure_send_snapshot` (method, line 305): Return original read-only source or create/reuse one exact cache child. **Why:** Keeps this operation inside `CacheManager` so callers cannot bypass the class's endpoint and validation rules.

## `timeshift_btrfs_sync/cli.py`

**Module role:** Command-line interface for timeshift-btrfs-sync.

**Why this module exists:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `new_subparser` (function, line 35): Internal function for new subparser. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `add_config_arg` (function, line 41): Internal function for add config arg. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `add_run_mode_args` (function, line 43): Internal function for add run mode args. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `add_yes_delete_arg` (function, line 49): Internal function for add yes delete arg. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `_load_config_state` (function, line 53): Load state and resolve all root-relative paths against this config. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `_failure_exit_code` (function, line 59): Return a stable CLI exit code for failure notifications. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `_stderr_tail_for_exception` (function, line 75): Return the best available recent stderr text for failure notifications. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `_send_notifications` (function, line 85): Send optional MQTT/email status without changing the command exit code. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `_mail_attachment_paths` (function, line 125): Return current run log paths for optional email attachment. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `_safe_destroy_log_dir` (function, line 135): Return a log directory that will survive a destructive cleanup. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `_with_logging` (function, line 176): Run a command with optional logging and MQTT notification. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `_resolve_dry_run` (function, line 225): Internal function for resolve dry run. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_init_config` (function, line 233): Internal function for cmd init config. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_test_source` (function, line 252): Internal function for cmd test source. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `_refresh_state_metadata_from_timeshift` (function, line 273): Refresh mutable state metadata from one fast Timeshift list read. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_list_source` (function, line 281): List snapshots on the source machine. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_sync` (function, line 304): Internal function for cmd sync. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_prune` (function, line 334): Internal function for cmd prune. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_restore` (function, line 363): Restore one snapshot or the complete post-common backup chain into Timeshift. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_create_manual` (function, line 399): Internal function for cmd create manual. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_clear_state` (function, line 428): Guardedly remove the configured state_file with normal run logging. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_delete_lock` (function, line 456): Guardedly remove the configured lock_file if it is stale, with logging. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_destroy_leftovers` (function, line 473): Destroy configured leftovers with normal run logging enabled. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `cmd_show_state` (function, line 499): Internal function for cmd show state. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `build_parser` (function, line 545): Create the argparse parser and command-specific flag help. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

- `main` (function, line 785): Internal function for main. **Why:** Defines the current command-line interface and coordinates config, locks, logging, and workflow entry points.

## `timeshift_btrfs_sync/commands.py`

**Module role:** Shared subprocess helpers.

**Why this module exists:** Runs commands and streaming pipelines with consistent logging, error capture, and optional buffering.

- `CommandError` (class, line 21): Raised when an external command exits with a non-zero status. **Why:** Runs commands and streaming pipelines with consistent logging, error capture, and optional buffering.

- `CommandError.__init__` (method, line 24): Internal function for init. **Why:** Keeps this operation inside `CommandError` so callers cannot bypass the class's endpoint and validation rules.

- `Completed` (class, line 39): Captured exit status and text streams for one command. **Why:** Runs commands and streaming pipelines with consistent logging, error capture, and optional buffering.

- `sudo_prefix` (function, line 47): Split a configured sudo prefix into argv parts. **Why:** Runs commands and streaming pipelines with consistent logging, error capture, and optional buffering.

- `quote_join` (function, line 55): Quote argv parts into one safe remote-shell command string. **Why:** Runs commands and streaming pipelines with consistent logging, error capture, and optional buffering.

- `remote_double_quote` (function, line 61): Return a shell-safe double-quoted argument for a remote shell command. **Why:** Runs commands and streaming pipelines with consistent logging, error capture, and optional buffering.

- `_merged_env` (function, line 84): Merge optional child-process environment variables. **Why:** Runs commands and streaming pipelines with consistent logging, error capture, and optional buffering.

- `run_local` (function, line 94): Run a local command and capture stdout/stderr. **Why:** Runs commands and streaming pipelines with consistent logging, error capture, and optional buffering.

- `_start_pipeline_readers` (function, line 151): Start tee readers from compact stream routing specs. **Why:** Runs commands and streaming pipelines with consistent logging, error capture, and optional buffering.

- `_failed_stderr` (function, line 170): Return captured pipeline stderr for streams that belong in failures. **Why:** Runs commands and streaming pipelines with consistent logging, error capture, and optional buffering.

- `_log_failed_streams` (function, line 176): Copy captured failed pipeline streams to .err. **Why:** Runs commands and streaming pipelines with consistent logging, error capture, and optional buffering.

- `stream_pipeline` (function, line 188): Stream left command into optional middle command, then right command. **Why:** Runs commands and streaming pipelines with consistent logging, error capture, and optional buffering.

## `timeshift_btrfs_sync/config.py`

**Module role:** TOML configuration loading and validation.

**Why this module exists:** Loads and validates the one current configuration schema used by every command.

- `_reject_unknown_keys` (function, line 35): Reject configuration entries that are not part of the current schema. **Why:** Loads and validates the one current configuration schema used by every command.

- `ManualSnapshotConfig` (class, line 43): Optional source-side Timeshift on-demand snapshot creation and cleanup. **Why:** Loads and validates the one current configuration schema used by every command.

- `SourceConfig` (class, line 77): Timeshift source/restore-target paths that always share one endpoint. **Why:** Loads and validates the one current configuration schema used by every command.

- `DestinationConfig` (class, line 120): Backup repository and normal local receive settings. **Why:** Loads and validates the one current configuration schema used by every command.

- `StreamConfig` (class, line 134): Optional pipeline display/buffering settings. **Why:** Loads and validates the one current configuration schema used by every command.

- `StreamConfig.command` (method, line 154): Return mbuffer command argv or None when disabled. **Why:** Keeps this operation inside `StreamConfig` so callers cannot bypass the class's endpoint and validation rules.

- `RetentionConfig` (class, line 168): Destination retention counts by Timeshift tag. **Why:** Loads and validates the one current configuration schema used by every command.

- `RetentionConfig.counts_by_tag` (method, line 187): Return retention counts keyed by Timeshift tag letters. **Why:** Keeps this operation inside `RetentionConfig` so callers cannot bypass the class's endpoint and validation rules.

- `RestoreConfig` (class, line 193): Restore-only transport direction. **Why:** Loads and validates the one current configuration schema used by every command.

- `RestoreConfig.backup_uses_ssh` (property, line 203): Return True when restore reads the backup repository over SSH. **Why:** Keeps this operation inside `RestoreConfig` so callers cannot bypass the class's endpoint and validation rules.

- `RestoreConfig.timeshift_uses_ssh` (property, line 209): Return True when snapshot_root and cache_root are on the SSH Timeshift host. **Why:** Keeps this operation inside `RestoreConfig` so callers cannot bypass the class's endpoint and validation rules.

- `AppConfig` (class, line 216): Complete validated app configuration. **Why:** Loads and validates the one current configuration schema used by every command.

- `ConfigError` (class, line 235): Raised when the TOML config is invalid. **Why:** Loads and validates the one current configuration schema used by every command.

- `_table` (function, line 238): Internal function for table. **Why:** Loads and validates the one current configuration schema used by every command.

- `_optional_str` (function, line 244): Internal function for optional str. **Why:** Loads and validates the one current configuration schema used by every command.

- `_positive_int` (function, line 247): Internal function for positive int. **Why:** Loads and validates the one current configuration schema used by every command.

- `_stripped` (function, line 254): Internal function for stripped. **Why:** Loads and validates the one current configuration schema used by every command.

- `_bool` (function, line 257): Internal function for bool. **Why:** Loads and validates the one current configuration schema used by every command.

- `_int` (function, line 260): Internal function for int. **Why:** Loads and validates the one current configuration schema used by every command.

- `_as_str` (function, line 263): Internal function for as str. **Why:** Loads and validates the one current configuration schema used by every command.

- `_as_path` (function, line 268): Internal function for as path. **Why:** Loads and validates the one current configuration schema used by every command.

- `_as_bool` (function, line 271): Internal function for as bool. **Why:** Loads and validates the one current configuration schema used by every command.

- `_as_int` (function, line 278): Internal function for as int. **Why:** Loads and validates the one current configuration schema used by every command.

- `_string_list` (function, line 285): Internal function for string list. **Why:** Loads and validates the one current configuration schema used by every command.

- `load_config` (function, line 293): Read and validate the current TOML configuration. **Why:** Loads and validates the one current configuration schema used by every command.

## `timeshift_btrfs_sync/destroy.py`

**Module role:** Destructive setup retirement using the shared Btrfs tree engine.

**Why this module exists:** Implements guarded deletion of selected app-owned source-cache and destination trees.

- `DestroyResult` (class, line 26): Named wrapper around the shared tree-deletion result. **Why:** Implements guarded deletion of selected app-owned source-cache and destination trees.

- `_safe_cleanup_path` (function, line 33): Internal function for safe cleanup path. **Why:** Implements guarded deletion of selected app-owned source-cache and destination trees.

- `_confirm_or_raise` (function, line 46): Internal function for confirm or raise. **Why:** Implements guarded deletion of selected app-owned source-cache and destination trees.

- `_mode_text` (function, line 51): Internal function for mode text. **Why:** Implements guarded deletion of selected app-owned source-cache and destination trees.

- `_load_payload_state` (function, line 57): Internal function for load payload state. **Why:** Implements guarded deletion of selected app-owned source-cache and destination trees.

- `_result_by_label` (function, line 64): Internal function for result by label. **Why:** Implements guarded deletion of selected app-owned source-cache and destination trees.

- `_print_payload_match` (function, line 68): Internal function for print payload match. **Why:** Implements guarded deletion of selected app-owned source-cache and destination trees.

- `_print_result` (function, line 87): Internal function for print result. **Why:** Implements guarded deletion of selected app-owned source-cache and destination trees.

- `destroy_leftovers` (function, line 118): Plan and execute selected source/destination tree retirement. **Why:** Implements guarded deletion of selected app-owned source-cache and destination trees.

## `timeshift_btrfs_sync/endpoint.py`

**Module role:** Unified command endpoints for local, Timeshift, and backup operations.

**Why this module exists:** Provides one local/SSH command transport used by Timeshift, backup, and destination operations.

- `CommandEndpoint` (class, line 19): Execute commands on one local or transported endpoint. **Why:** Provides one local/SSH command transport used by Timeshift, backup, and destination operations.

- `CommandEndpoint.for_source` (method, line 30): Internal function for for source. **Why:** Keeps this operation inside `CommandEndpoint` so callers cannot bypass the class's endpoint and validation rules.

- `CommandEndpoint.local` (method, line 34): Internal function for local. **Why:** Keeps this operation inside `CommandEndpoint` so callers cannot bypass the class's endpoint and validation rules.

- `CommandEndpoint.location` (property, line 38): Internal function for location. **Why:** Keeps this operation inside `CommandEndpoint` so callers cannot bypass the class's endpoint and validation rules.

- `CommandEndpoint.shell_command` (method, line 41): Return a safely quoted shell command for this endpoint. **Why:** Keeps this operation inside `CommandEndpoint` so callers cannot bypass the class's endpoint and validation rules.

- `CommandEndpoint.command` (method, line 46): Return process argv for a command executed on this endpoint. **Why:** Keeps this operation inside `CommandEndpoint` so callers cannot bypass the class's endpoint and validation rules.

- `CommandEndpoint.run_argv` (method, line 54): Execute one argv command through the endpoint transport. **Why:** Keeps this operation inside `CommandEndpoint` so callers cannot bypass the class's endpoint and validation rules.

- `CommandEndpoint.run_shell` (method, line 82): Execute one shell script through the endpoint transport. **Why:** Keeps this operation inside `CommandEndpoint` so callers cannot bypass the class's endpoint and validation rules.

## `timeshift_btrfs_sync/executor.py`

**Module role:** Generic ordered workflow action executor.

**Why this module exists:** Executes ordered workflow actions through the shared operation layers.

- `WorkflowExecutor` (class, line 14): Execute or preview a plan using one handler per action kind. **Why:** Executes ordered workflow actions through the shared operation layers.

- `WorkflowExecutor.execute` (method, line 22): Internal function for execute. **Why:** Keeps this operation inside `WorkflowExecutor` so callers cannot bypass the class's endpoint and validation rules.

## `timeshift_btrfs_sync/inventory.py`

**Module role:** Bulk source/cache Btrfs and Timeshift inventory construction and lookup.

**Why this module exists:** Avoids repeated probes and ensures path, UUID, Parent UUID, Received UUID, and read-only facts come from coherent indexes.

- `BtrfsIndex` (class, line 29): In-memory index of Btrfs subvolumes below one root path. **Why:** Avoids repeated probes and ensures path, UUID, Parent UUID, Received UUID, and read-only facts come from coherent indexes.

- `BtrfsIndex.add` (method, line 40): Add or replace one indexed subvolume. **Why:** Keeps this operation inside `BtrfsIndex` so callers cannot bypass the class's endpoint and validation rules.

- `BtrfsIndex.discard` (method, line 53): Remove one path and any known UUID lookup entries for it. **Why:** Keeps this operation inside `BtrfsIndex` so callers cannot bypass the class's endpoint and validation rules.

- `BtrfsIndex.contains` (method, line 65): Return True when ``path`` is an indexed subvolume. **Why:** Keeps this operation inside `BtrfsIndex` so callers cannot bypass the class's endpoint and validation rules.

- `BtrfsIndex.meta` (method, line 70): Return metadata for ``path`` if it was indexed. **Why:** Keeps this operation inside `BtrfsIndex` so callers cannot bypass the class's endpoint and validation rules.

- `BtrfsIndex.find_send_uuid` (method, line 75): Return a subvolume whose Btrfs send-stream identity equals ``uuid``. **Why:** Lets sync and restore find a source by the identity Btrfs will actually put in the stream, whether native or previously received.

- `BtrfsIndex.remove_tree` (method, line 91): Remove a deleted path and all indexed descendants. **Why:** Keeps this operation inside `BtrfsIndex` so callers cannot bypass the class's endpoint and validation rules.

- `SourceInventory` (class, line 101): One coherent source-side Timeshift/Btrfs inventory. **Why:** Avoids repeated probes and ensures path, UUID, Parent UUID, Received UUID, and read-only facts come from coherent indexes.

- `SourceInventory.snapshot_names` (property, line 121): Return Timeshift timestamp names in sorted order. **Why:** Keeps this operation inside `SourceInventory` so callers cannot bypass the class's endpoint and validation rules.

- `SourceInventory.meta` (method, line 127): Return source metadata from cache first, then snapshot-root index. **Why:** Keeps this operation inside `SourceInventory` so callers cannot bypass the class's endpoint and validation rules.

- `_clean_uuid` (function, line 138): Normalize Btrfs UUID fields from list/show output. **Why:** Avoids repeated probes and ensures path, UUID, Parent UUID, Received UUID, and read-only facts come from coherent indexes.

- `parse_subvolume_list` (function, line 147): Parse ``btrfs subvolume list -u -q -R`` output for one root. **Why:** Avoids repeated probes and ensures path, UUID, Parent UUID, Received UUID, and read-only facts come from coherent indexes.

- `parse_subvolume_paths` (function, line 173): Return root-scoped absolute paths from ``btrfs subvolume list`` output. **Why:** Avoids repeated probes and ensures path, UUID, Parent UUID, Received UUID, and read-only facts come from coherent indexes.

- `_mark_readonly_from_list` (function, line 187): Mark indexed paths read-only using one ``btrfs subvolume list -r`` result. **Why:** Avoids repeated probes and ensures path, UUID, Parent UUID, Received UUID, and read-only facts come from coherent indexes.

- `build_local_btrfs_index` (function, line 203): Build a local Btrfs index with bulk list commands. **Why:** Avoids repeated probes and ensures path, UUID, Parent UUID, Received UUID, and read-only facts come from coherent indexes.

- `_remote_bulk_index_script` (function, line 251): Return a POSIX shell script that bulk-lists source Btrfs metadata. **Why:** Avoids repeated probes and ensures path, UUID, Parent UUID, Received UUID, and read-only facts come from coherent indexes.

- `build_source_btrfs_index` (function, line 297): Build a source Btrfs index in SSH or local mode. **Why:** Avoids repeated probes and ensures path, UUID, Parent UUID, Received UUID, and read-only facts come from coherent indexes.

- `build_remote_btrfs_index` (function, line 329): Build a remote source index using one SSH command. **Why:** Avoids repeated probes and ensures path, UUID, Parent UUID, Received UUID, and read-only facts come from coherent indexes.

- `_parse_remote_btrfs_index_result` (function, line 361): Parse one remote bulk-index section into a :class:`BtrfsIndex`. **Why:** Avoids repeated probes and ensures path, UUID, Parent UUID, Received UUID, and read-only facts come from coherent indexes.

- `_remote_source_inventory_script` (function, line 461): Return one remote script for Timeshift, info.json, and both Btrfs roots. **Why:** Avoids repeated probes and ensures path, UUID, Parent UUID, Received UUID, and read-only facts come from coherent indexes.

- `_extract_snapshot_info_json_frames` (function, line 543): Remove and parse the ``cat`` payloads from combined SSH output. **Why:** Avoids repeated probes and ensures path, UUID, Parent UUID, Received UUID, and read-only facts come from coherent indexes.

- `_split_remote_source_inventory_output` (function, line 577): Split combined output into identity, Timeshift, info.json, and Btrfs sections. **Why:** Avoids repeated probes and ensures path, UUID, Parent UUID, Received UUID, and read-only facts come from coherent indexes.

- `_current_process_identity` (function, line 650): Return the effective local account name and UID used to read metadata. **Why:** Avoids repeated probes and ensures path, UUID, Parent UUID, Received UUID, and read-only facts come from coherent indexes.

- `_read_local_snapshot_info_json` (function, line 661): Read all local Timeshift control files without spawning commands. **Why:** Avoids repeated probes and ensures path, UUID, Parent UUID, Received UUID, and read-only facts come from coherent indexes.

- `_record_missing_info_json_errors` (function, line 688): Record listed Timeshift dates that had no readable control file. **Why:** Avoids repeated probes and ensures path, UUID, Parent UUID, Received UUID, and read-only facts come from coherent indexes.

- `build_source_inventory` (function, line 702): Build one coherent Timeshift/snapshot/cache source inventory. **Why:** Avoids repeated probes and ensures path, UUID, Parent UUID, Received UUID, and read-only facts come from coherent indexes.

- `describe_source_inventory_changes` (function, line 825): Return concise human-readable differences between two inventories. **Why:** Avoids repeated probes and ensures path, UUID, Parent UUID, Received UUID, and read-only facts come from coherent indexes.

- `refresh_path` (function, line 877): Refresh one exact path through the shared Btrfs operation layer. **Why:** Avoids repeated probes and ensures path, UUID, Parent UUID, Received UUID, and read-only facts come from coherent indexes.

## `timeshift_btrfs_sync/lock.py`

**Module role:** Local advisory file locking for coordinated operations.

**Why this module exists:** Prevents concurrent restore, sync, prune, or maintenance operations from overlapping on the machine running the command.

- `FileLock` (class, line 10): flock() based non-blocking exclusive lock on the local machine. **Why:** Prevents concurrent restore, sync, prune, or maintenance operations from overlapping on the machine running the command.

- `FileLock.__init__` (method, line 13): Internal function for init. **Why:** Keeps this operation inside `FileLock` so callers cannot bypass the class's endpoint and validation rules.

- `FileLock.__enter__` (method, line 17): Internal function for enter. **Why:** Keeps this operation inside `FileLock` so callers cannot bypass the class's endpoint and validation rules.

- `FileLock.__exit__` (method, line 29): Internal function for exit. **Why:** Keeps this operation inside `FileLock` so callers cannot bypass the class's endpoint and validation rules.

## `timeshift_btrfs_sync/log.py`

**Module role:** Split run logging for timeshift-btrfs-sync.

**Why this module exists:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `RunLogger` (class, line 32): Owns the split log files for one run. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `RunLogger.__post_init__` (method, line 38): Create the log directory and open the run log files. **Why:** Keeps this operation inside `RunLogger` so callers cannot bypass the class's endpoint and validation rules.

- `RunLogger.close` (method, line 71): Close all log files. **Why:** Keeps this operation inside `RunLogger` so callers cannot bypass the class's endpoint and validation rules.

- `RunLogger.attachment_paths` (method, line 81): Return run log files in the order useful for mail attachments. **Why:** Keeps this operation inside `RunLogger` so callers cannot bypass the class's endpoint and validation rules.

- `RunLogger._write` (method, line 91): Write text safely from possible stream-reader threads. **Why:** Keeps this operation inside `RunLogger` so callers cannot bypass the class's endpoint and validation rules.

- `RunLogger._remember_stderr` (method, line 98): Keep a small tail of stderr for failure notifications. **Why:** Keeps this operation inside `RunLogger` so callers cannot bypass the class's endpoint and validation rules.

- `RunLogger.last_stderr_tail` (method, line 106): Return the newest stderr text remembered for MQTT/error reports. **Why:** Keeps this operation inside `RunLogger` so callers cannot bypass the class's endpoint and validation rules.

- `RunLogger._line` (method, line 112): Write exactly one logical line. **Why:** Keeps this operation inside `RunLogger` so callers cannot bypass the class's endpoint and validation rules.

- `RunLogger.info` (method, line 119): Write a normal status line to .log. **Why:** Keeps this operation inside `RunLogger` so callers cannot bypass the class's endpoint and validation rules.

- `RunLogger.mbuffer` (method, line 124): Write one line to the .mbuffer transfer-progress log. **Why:** Keeps this operation inside `RunLogger` so callers cannot bypass the class's endpoint and validation rules.

- `RunLogger.btrfs_out` (method, line 129): Write one line to the .btrfs Btrfs verbose-output log. **Why:** Keeps this operation inside `RunLogger` so callers cannot bypass the class's endpoint and validation rules.

- `RunLogger.success` (method, line 134): Write one line to the .succes human-readable summary log. **Why:** Keeps this operation inside `RunLogger` so callers cannot bypass the class's endpoint and validation rules.

- `RunLogger.success_text` (method, line 139): Write a preformatted block to the .succes summary log. **Why:** Keeps this operation inside `RunLogger` so callers cannot bypass the class's endpoint and validation rules.

- `RunLogger.err` (method, line 146): Write an error/stderr line to .err and remember its tail. **Why:** Keeps this operation inside `RunLogger` so callers cannot bypass the class's endpoint and validation rules.

- `RunLogger.command` (method, line 153): Record a command that is about to run. **Why:** Keeps this operation inside `RunLogger` so callers cannot bypass the class's endpoint and validation rules.

- `RunLogger.completed` (method, line 176): Record the output from a normal captured command. **Why:** Keeps this operation inside `RunLogger` so callers cannot bypass the class's endpoint and validation rules.

- `RunLogger.pipeline_commands` (method, line 207): Record send/buffer/receive commands to the appropriate logs. **Why:** Keeps this operation inside `RunLogger` so callers cannot bypass the class's endpoint and validation rules.

- `RunLogger.pipeline_summary` (method, line 218): Record final pipeline status. **Why:** Keeps this operation inside `RunLogger` so callers cannot bypass the class's endpoint and validation rules.

- `RunLogger.stream_text` (method, line 226): Write live pipeline text to terminal and/or split log files. **Why:** Keeps this operation inside `RunLogger` so callers cannot bypass the class's endpoint and validation rules.

- `emit_success_summary` (function, line 254): Write a readable summary to the real terminal and .succes only. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `TeeTextIO` (class, line 270): Terminal stream wrapper that also writes normal app output to run logs. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `TeeTextIO.__init__` (method, line 283): Internal function for init. **Why:** Keeps this operation inside `TeeTextIO` so callers cannot bypass the class's endpoint and validation rules.

- `TeeTextIO.write` (method, line 290): Internal function for write. **Why:** Keeps this operation inside `TeeTextIO` so callers cannot bypass the class's endpoint and validation rules.

- `TeeTextIO.flush` (method, line 303): Internal function for flush. **Why:** Keeps this operation inside `TeeTextIO` so callers cannot bypass the class's endpoint and validation rules.

- `TeeTextIO.isatty` (method, line 306): Internal function for isatty. **Why:** Keeps this operation inside `TeeTextIO` so callers cannot bypass the class's endpoint and validation rules.

- `TeeTextIO.fileno` (method, line 309): Internal function for fileno. **Why:** Keeps this operation inside `TeeTextIO` so callers cannot bypass the class's endpoint and validation rules.

- `TeeTextIO.writable` (method, line 312): Internal function for writable. **Why:** Keeps this operation inside `TeeTextIO` so callers cannot bypass the class's endpoint and validation rules.

- `TeeTextIO.__getattr__` (method, line 315): Internal function for getattr. **Why:** Keeps this operation inside `TeeTextIO` so callers cannot bypass the class's endpoint and validation rules.

- `terminal_stdout` (function, line 323): Return the real terminal stdout, bypassing the run-log tee wrapper. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `terminal_stderr` (function, line 329): Return the real terminal stderr, bypassing the run-log tee wrapper. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `get_logger` (function, line 337): Return the active logger, if file logging is enabled. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `active_logger` (function, line 344): Temporarily install a run logger and tee app output to files. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `create_run_logger` (function, line 380): Create a logger when log_dir is configured; otherwise return None. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

- `tee_pipe_to_log` (function, line 402): Start a thread that reads bytes from a process pipe and logs them live. **Why:** Writes the current split command, error, Btrfs, mbuffer, and success logs.

## `timeshift_btrfs_sync/mail.py`

**Module role:** Optional email notifications for timeshift-btrfs-sync.

**Why this module exists:** Sends optional email notifications using the current run result and log attachments.

- `MailConfig` (class, line 20): SMTP settings for optional email notifications. **Why:** Sends optional email notifications using the current run result and log attachments.

- `MailConfig.resolved_password` (method, line 52): Return password from config value or password_file. **Why:** Keeps this operation inside `MailConfig` so callers cannot bypass the class's endpoint and validation rules.

- `_subject` (function, line 61): Create a short readable subject line. **Why:** Sends optional email notifications using the current run result and log attachments.

- `_body` (function, line 72): Create a fallback plain-text email body from the status payload. **Why:** Sends optional email notifications using the current run result and log attachments.

- `_success_body_from_paths` (function, line 101): Return the text content of the non-empty .succes file, if present. **Why:** Sends optional email notifications using the current run result and log attachments.

- `_filter_attachments` (function, line 118): Return existing attachment paths and human-readable skipped reasons. **Why:** Sends optional email notifications using the current run result and log attachments.

- `_attach_file` (function, line 148): Attach one file to an EmailMessage. **Why:** Sends optional email notifications using the current run result and log attachments.

- `send_status` (function, line 159): Send one optional SMTP status email. **Why:** Sends optional email notifications using the current run result and log attachments.

## `timeshift_btrfs_sync/maintenance.py`

**Module role:** Guarded maintenance commands for state and lock files.

**Why this module exists:** Implements guarded state and lock maintenance commands.

- `_confirm_or_raise` (function, line 21): Require an exact typed confirmation before destructive maintenance. **Why:** Implements guarded state and lock maintenance commands.

- `_safe_configured_file` (function, line 29): Return a normalized configured file path or raise for unsafe targets. **Why:** Implements guarded state and lock maintenance commands.

- `_looks_like_state_file` (function, line 44): Return True when an existing file appears to be ts-btrfs state. **Why:** Implements guarded state and lock maintenance commands.

- `_looks_like_lock_file` (function, line 63): Return True when an existing file looks like this app's simple lock file. **Why:** Implements guarded state and lock maintenance commands.

- `_print_header` (function, line 77): Print the common maintenance command warning block. **Why:** Implements guarded state and lock maintenance commands.

- `_require_real_confirmation` (function, line 90): Require real-mode flags and typed confirmations. **Why:** Implements guarded state and lock maintenance commands.

- `clear_state_file` (function, line 110): Remove the configured state.json file after explicit confirmation. **Why:** Implements guarded state and lock maintenance commands.

- `delete_lock_file` (function, line 160): Delete the configured lock file when no running process holds it. **Why:** Implements guarded state and lock maintenance commands.

## `timeshift_btrfs_sync/models.py`

**Module role:** Shared immutable metadata models and Btrfs stream-identity helpers.

**Why this module exists:** Gives every workflow one definition of snapshot metadata and the identity carried by a Btrfs send stream.

- `SubvolumeMeta` (class, line 9): Metadata for one Btrfs subvolume inside one Timeshift snapshot. **Why:** Gives every workflow one definition of snapshot metadata and the identity carried by a Btrfs send stream.

- `send_stream_uuid` (function, line 21): Return the UUID identity carried when ``meta`` is sent by Btrfs. **Why:** Prevents received snapshots from being recorded or matched by the wrong new local UUID.

- `SnapshotMeta` (class, line 35): Metadata for one Timeshift snapshot. **Why:** Gives every workflow one definition of snapshot metadata and the identity carried by a Btrfs send stream.

- `SnapshotMeta.sort_key` (method, line 45): Timeshift timestamp names sort oldest-to-newest lexically. **Why:** Keeps this operation inside `SnapshotMeta` so callers cannot bypass the class's endpoint and validation rules.

- `tags_text` (function, line 51): Return compact human text for Timeshift tags. **Why:** Gives every workflow one definition of snapshot metadata and the identity carried by a Btrfs send stream.

## `timeshift_btrfs_sync/mqtt.py`

**Module role:** Optional MQTT notifications for timeshift-btrfs-sync.

**Why this module exists:** Publishes optional structured MQTT status messages.

- `MQTTConfig` (class, line 19): MQTT broker and publish settings. **Why:** Publishes optional structured MQTT status messages.

- `MQTTConfig.resolved_password` (method, line 41): Return password from config value or password_file. **Why:** Keeps this operation inside `MQTTConfig` so callers cannot bypass the class's endpoint and validation rules.

- `publish_status` (function, line 51): Publish one JSON MQTT status message. **Why:** Publishes optional structured MQTT status messages.

## `timeshift_btrfs_sync/notify.py`

**Module role:** Shared notification payload helpers.

**Why this module exists:** Combines terminal/run results with configured MQTT and email notifications.

- `utc_timestamp` (function, line 10): Return a compact ISO-8601 UTC timestamp for notifications. **Why:** Combines terminal/run results with configured MQTT and email notifications.

- `build_notification_payload` (function, line 16): Build the shared status payload used by MQTT and email. **Why:** Combines terminal/run results with configured MQTT and email notifications.

## `timeshift_btrfs_sync/paths.py`

**Module role:** Canonical path normalization and containment rules.

**Why this module exists:** Normalizes, maps, and validates managed local and remote paths safely.

- `normalize_source_path` (function, line 13): Normalize POSIX path text while preserving an intentionally empty value. **Why:** Normalizes, maps, and validates managed local and remote paths safely.

- `is_same_or_under` (function, line 23): Return true when ``path`` equals ``root`` or is below it. **Why:** Normalizes, maps, and validates managed local and remote paths safely.

- `is_local_same_or_under` (function, line 35): Return true when one local path resolves to ``root`` or below it. **Why:** Normalizes, maps, and validates managed local and remote paths safely.

- `is_under` (function, line 55): Return true only when ``path`` is strictly below ``root``. **Why:** Normalizes, maps, and validates managed local and remote paths safely.

- `listed_path_to_absolute` (function, line 67): Resolve one Btrfs-list path below a mounted root. **Why:** Normalizes, maps, and validates managed local and remote paths safely.

- `sort_deepest_first` (function, line 115): Deduplicate and order paths for child-before-parent deletion. **Why:** Normalizes, maps, and validates managed local and remote paths safely.

## `timeshift_btrfs_sync/payload_stats.py`

**Module role:** Normalized source/destination payload statistics for Btrfs snapshot trees.

**Why this module exists:** Calculates readable transfer and retention payload statistics.

- `PayloadTreeStats` (class, line 30): Normalized payload/container counts for one source or destination tree. **Why:** Calculates readable transfer and retention payload statistics.

- `PayloadTreeStats.total_payload` (property, line 47): Return the number of real cached/received payload subvolumes. **Why:** Keeps this operation inside `PayloadTreeStats` so callers cannot bypass the class's endpoint and validation rules.

- `PayloadTreeStats.total_cache_payload` (property, line 53): Return how many source payloads came from app-owned source cache. **Why:** Keeps this operation inside `PayloadTreeStats` so callers cannot bypass the class's endpoint and validation rules.

- `PayloadTreeStats.total_direct_payload` (property, line 59): Return how many source payloads came from protected Timeshift originals. **Why:** Keeps this operation inside `PayloadTreeStats` so callers cannot bypass the class's endpoint and validation rules.

- `normalize_path` (function, line 65): Normalize paths so source/destination comparisons ignore trailing slashes. **Why:** Calculates readable transfer and retention payload statistics.

- `_relative_parts` (function, line 71): Return path parts relative to root, or None if path is outside root. **Why:** Calculates readable transfer and retention payload statistics.

- `_recount_payload` (function, line 85): Rebuild per-subvolume counters from the normalized payload set. **Why:** Calculates readable transfer and retention payload statistics.

- `_add_payload` (function, line 93): Add a payload entry when relative parts end in a configured subvolume name. **Why:** Calculates readable transfer and retention payload statistics.

- `source_send_cache_stats` (function, line 106): Classify source send-cache subvolumes into payload and helper counts. **Why:** Calculates readable transfer and retention payload statistics.

- `destination_payload_stats` (function, line 129): Classify destination target subvolumes into received payload counts. **Why:** Calculates readable transfer and retention payload statistics.

- `direct_send_payload_stats` (function, line 152): Return payload entries streamed directly from protected Timeshift originals. **Why:** Calculates readable transfer and retention payload statistics.

- `merge_source_payload_stats` (function, line 184): Merge app-cache and protected direct-send payload into one source view. **Why:** Calculates readable transfer and retention payload statistics.

- `PayloadMatchStats` (class, line 207): Comparison between source send payload and destination received payload. **Why:** Calculates readable transfer and retention payload statistics.

- `PayloadMatchStats.source_only` (property, line 214): Return source payload entries not present on the destination. **Why:** Keeps this operation inside `PayloadMatchStats` so callers cannot bypass the class's endpoint and validation rules.

- `PayloadMatchStats.destination_only` (property, line 220): Return destination payload entries not present on the source side. **Why:** Keeps this operation inside `PayloadMatchStats` so callers cannot bypass the class's endpoint and validation rules.

- `PayloadMatchStats.ok` (property, line 226): Return True when source send payload and destination payload match. **Why:** Keeps this operation inside `PayloadMatchStats` so callers cannot bypass the class's endpoint and validation rules.

- `compare_payloads` (function, line 232): Return normalized source/destination payload comparison stats. **Why:** Calculates readable transfer and retention payload statistics.

- `_format_count_line` (function, line 238): Return an aligned summary line. **Why:** Calculates readable transfer and retention payload statistics.

- `render_payload_match` (function, line 244): Render the source/destination payload comparison block. **Why:** Calculates readable transfer and retention payload statistics.

## `timeshift_btrfs_sync/planning.py`

**Module role:** Pure workflow planning from a combined backup inventory.

**Why this module exists:** Builds side-effect-free ordered plans for sync, recovery, prune, and destructive cleanup.

- `ActionKind` (class, line 17): Internal class for ActionKind. **Why:** Builds side-effect-free ordered plans for sync, recovery, prune, and destructive cleanup.

- `WorkflowAction` (class, line 28): Internal class for WorkflowAction. **Why:** Builds side-effect-free ordered plans for sync, recovery, prune, and destructive cleanup.

- `WorkflowPlan` (class, line 36): Internal class for WorkflowPlan. **Why:** Builds side-effect-free ordered plans for sync, recovery, prune, and destructive cleanup.

- `WorkflowPlan.add` (method, line 40): Internal function for add. **Why:** Keeps this operation inside `WorkflowPlan` so callers cannot bypass the class's endpoint and validation rules.

- `plan_sync_queue` (function, line 52): Plan the oldest-to-newest sync queue without executing operations. **Why:** Builds side-effect-free ordered plans for sync, recovery, prune, and destructive cleanup.

- `plan_snapshot_recovery` (function, line 79): Plan one whole-date recovery in cache, destination, then state order. **Why:** Builds side-effect-free ordered plans for sync, recovery, prune, and destructive cleanup.

- `plan_prune_snapshot` (function, line 89): Internal function for plan prune snapshot. **Why:** Builds side-effect-free ordered plans for sync, recovery, prune, and destructive cleanup.

- `plan_destroy_targets` (function, line 102): Plan named endpoint/root destruction in the caller-provided order. **Why:** Builds side-effect-free ordered plans for sync, recovery, prune, and destructive cleanup.

## `timeshift_btrfs_sync/preflight.py`

**Module role:** Sync path preflight checks.

**Why this module exists:** Validates or creates only the paths each workflow is allowed to own.

- `PathPreflightError` (class, line 44): Raised before any destructive/creating sync work when required paths fail. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `PathCheck` (class, line 49): One configured path availability result. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `_shell_words` (function, line 60): Return a shell-safe string for configured command-prefix words. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `_parse_path_check_output` (function, line 66): Parse source-path preflight sentinel lines into structured checks. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `_source_snapshot_root_script` (function, line 99): Build a source script that validates Timeshift-owned source.snapshot_root. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `_cache_root_check_script` (function, line 167): Build a source script that validates or creates source.cache_root. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `_combined_source_path_check_script` (function, line 243): Run both source-root preflight checks inside one source command. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `_source_path_checks` (function, line 275): Check/create both source roots with at most one SSH command. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `_parent_of_path` (function, line 354): Return the immediate parent path used for exact-path creation checks. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `_local_btrfs_result` (function, line 361): Run one local destination sudo+btrfs command for preflight checks. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `_compact_process_error` (function, line 373): Return compact stderr/stdout text from a failed subprocess. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `_compact_os_error` (function, line 380): Return compact text for local filesystem creation errors. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `_print_check_block` (function, line 386): Print one human-readable preflight result block. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `_raise_for_failed_checks` (function, line 401): Raise a hard preflight error when any check failed. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `ensure_local_helper_dir` (function, line 411): Ensure one local helper directory exists. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `prepare_lock_path` (function, line 565): Create/verify the lock directory before other sync/prune directories. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `prepare_destination_helper_paths` (function, line 597): Create/verify local destination helper folders used by sync/prune. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `_local_target_path_check` (function, line 644): Check/create destination.target_root locally. **Why:** Validates or creates only the paths each workflow is allowed to own.

- `check_required_sync_paths` (function, line 786): Verify/create required configured roots before manual snapshot creation or send. **Why:** Validates or creates only the paths each workflow is allowed to own.

## `timeshift_btrfs_sync/restore.py`

**Module role:** Restore planning, physical repository discovery, identity proof, transfer, staging, verification, and cleanup for all three restore topologies.

**Why this module exists:** Keeps local backup → local Timeshift, SSH backup → local Timeshift pull, and local backup → SSH Timeshift on one safety-checked implementation so transport differences cannot change candidate selection, identity proof, receive-parent construction, or cleanup rules.

- `RestoreError` (class, line 49): Raised when a backup cannot be imported safely into Timeshift. **Why:** Gives restore-specific failures one controlled path through CLI reporting and notifications.

- `TimeshiftOsIdentity` (class, line 54): Stable `info.json` identity fields for one snapshot: `sys-uuid`, Btrfs `type`, and diagnostic `sys-distro`. **Why:** Separates stable same-OS proof from mutable tags, comments, counters, and timestamps.

- `BackupSnapshot` (class, line 63): One fully validated local or SSH backup date with exact metadata and Btrfs payload facts. **Why:** Prevents later planning and transfer code from operating on unvalidated paths.

- `BackupDirectoryRecord` (class, line 74): Read-only filesystem facts for one timestamp directory, its entries, and its `info.json`. **Why:** Keeps ordinary-directory validation separate from Btrfs subvolume validation.

- `BackupRepository` (class, line 85): Access one local or SSH backup repository through a common endpoint. **Why:** Makes all restore modes use the same state, physical scan, Btrfs inventory, and send rules.

- `BackupRepository.from_config` (method, line 94): Select the backup endpoint from `[restore] mode`. **Why:** Ensures `local`, `ssh`, and `ssh-target` interpret backup paths consistently.

- `BackupRepository.root` (property, line 108): Return configured `destination.target_root`. **Why:** Centralizes the repository root used by every backup-side operation.

- `BackupRepository.snapshots_root` (property, line 112): Return `<target_root>/snapshots`. **Why:** Avoids duplicated path construction and topology-specific drift.

- `BackupRepository.environment` (property, line 116): Return the endpoint environment used by streaming commands. **Why:** Preserves SSH password/control settings when the backup side sends data.

- `BackupRepository.location_label` (property, line 120): Return a readable local/SSH backup label. **Why:** Makes diagnostics identify which machine and side failed.

- `BackupRepository.load_state` (method, line 123): Read and validate backup-side `state.json` through `destination.sudo`, returning empty history when the file is absent. **Why:** Makes optional state evidence readable in local and SSH pull layouts without requiring ordinary-account access or trusting invalid metadata.

- `BackupRepository.scan_directories` (method, line 145): Physically scan backup timestamp directories and control files through `destination.sudo`. **Why:** Makes the configured backup root—not `state.json` names—the authority for what can be restored.

- `BackupRepository.btrfs_index` (method, line 155): Build one Btrfs metadata index for the complete backup tree. **Why:** Validates date containers and payloads in bulk before targeted fallback probes.

- `_scan_snapshot_directories` (function, line 173): Scan physical timestamp directories, entry types, and `info.json` through individually privileged `test`, `ls`, and `base64` commands. **Why:** Gives local, pull, and SSH-target restore the same authoritative physical view without invoking a privileged shell.

- `_read_privileged_file` (function, line 281): Read one regular non-symlink control file through individually privileged `test` and `base64` commands. **Why:** Lets restore inspect remote/local state and verify restored metadata without granting a privileged shell or depending on ordinary-account read access.

- `_effective_send_uuid` (function, line 352): Return the UUID identity carried by a Btrfs send stream. **Why:** Uses `Received UUID` for re-sent received subvolumes and local UUID for native snapshots.

- `_info_os_identity` (function, line 366): Extract stable `sys-uuid`/`type` identity while ignoring mutable metadata. **Why:** Allows secure same-date fallback after tags or comments change.

- `_parse_info_json` (function, line 388): Parse and validate one Timeshift control file. **Why:** Refuses malformed or non-object metadata before it can influence restore planning.

- `_same_os_identity` (function, line 400): Compare only stable Timeshift identity fields. **Why:** Avoids whole-file equality that would fail after normal retagging or statistics updates.

- `_consistent_backup_identity` (function, line 411): Require one non-conflicting OS identity across the selected backup set. **Why:** Refuses a chain assembled from multiple source filesystems or snapshot backends.

- `_timeshift_info_identities` (function, line 438): Parse same-date identities from the privileged physical Timeshift scan. **Why:** Supplies candidate-specific metadata proof rather than borrowing identity from an unrelated timestamp.

- `_timeshift_info_diagnostic` (function, line 451): Summarize missing/unreadable source control files and effective reader details. **Why:** Makes permission and wrong-root failures actionable.

- `_compare_repository_os_identity` (function, line 477): Compare the selected backup identity with current Timeshift identities for the repository-wide cross-OS warning. **Why:** Keeps the general danger warning separate from candidate-specific common-parent proof.

- `RestorePlan` (class, line 510): Side-effect-free plan containing backups, common timestamp, hidden seed, restore dates, and identity explanations. **Why:** Lets every safety decision be printed and checked before Timeshift is modified.

- `RestorePlan.seed_name` (property, line 525): Return the first hidden-chain backup. **Why:** Gives transfer code one unambiguous seed for full receive.

- `_source_path_exists` (function, line 529): Probe one Timeshift-side path through `source.sudo` without modifying it. **Why:** Prevents false missing-path results and overwrite/staging collisions when an SSH Timeshift target is not traversable by the ordinary account.

- `_privileged_argv` (function, line 549): Build source-side argv using configured `source.sudo`. **Why:** Keeps exact privileged commands consistent and avoids shell interpolation.

- `_write_source_info_json` (function, line 553): Atomically write the exact saved control file through narrow source-side commands. **Why:** Preserves original Timeshift metadata while preventing partial final files.

- `_validate_backup_snapshot` (function, line 594): Validate timestamp syntax, date-container type, expected entries, metadata, read-only payloads, and Btrfs UUIDs. **Why:** Refuses malformed, misrouted, symlinked, writable, or mixed-layout backup dates before planning.

- `_discover_backups` (function, line 672): Return one selected backup or all validated backup dates in timestamp order. **Why:** Creates the only restore candidate set from the configured physical backup repository.

- `_timeshift_snapshots` (function, line 697): Combine a privileged physical `snapshot_root` scan with Timeshift tags/comments and Btrfs/cache inventory. **Why:** Makes physical dates and readable same-date `info.json` authoritative even when `timeshift --list` omits a date or the ordinary account cannot read it.

- `_exact_timeshift_payload_meta` (function, line 775): Exact-probe a current Timeshift payload when the bulk index lacks it. **Why:** Avoids false “missing payload” results caused by mount-relative Btrfs listing paths or scan timing.

- `_state_payload_proof` (function, line 798): Validate current Timeshift UUID → `original_source_uuid` and backup Received UUID → `send_source_uuid`. **Why:** Uses completed state as strong per-payload evidence without trusting names alone.

- `_live_payload_proof` (function, line 828): Validate direct read-only identity or current Timeshift UUID → retained-cache Parent UUID → backup Received UUID. **Why:** Proves a fresh backup after destination-only cleanup removed old state while intentionally preserving cache.

- `_find_latest_common_parent` (function, line 890): Intersect physical dates newest-first and select the first candidate proven by exact Btrfs lineage or matching same-date `info.json` identity with real payloads. **Why:** Finds the newest safe skip point without requiring state/cache evidence that may legitimately have been removed and without accepting a date name alone.

- `_build_restore_plan` (function, line 1061): Build one single-snapshot or complete-chain plan without changing either endpoint. **Why:** Applies identical candidate, OS warning, hidden-seed, and restore-range rules to all transports.

- `_remove_restore_directory` (function, line 1189): Remove one exact app-created staging directory and its Btrfs payloads. **Why:** Never uses recursive deletion against a normal Timeshift tree.

- `_cleanup_restore_attempt` (function, line 1243): Roll back only paths created by the current failed attempt. **Why:** Preserves pre-existing and already committed Timeshift snapshots for manual inspection.

- `_create_pre_restore_snapshot` (function, line 1303): Create and verify one restore-target on-demand safety snapshot. **Why:** Provides a local rollback point before any backup data is received.

- `_print_restored_snapshot_retention_warning` (function, line 1400): Explain retained H/D/W/M tag deletion risk. **Why:** Requires informed acknowledgement before restored metadata can interact with normal Timeshift retention.

- `_print_restore_plan` (function, line 1417): Print topology, identity method, common timestamp, seed, range, and danger warnings. **Why:** Exposes the complete decision before confirmation or transfer.

- `_is_missing_incremental_parent_error` (function, line 1484): Recognize only Btrfs parent/clone-source lookup failures. **Why:** Restricts full-stream fallback to the error family it can safely correct.

- `_remove_partial_received_payload` (function, line 1504): Delete only the exact partial Btrfs child from a failed receive. **Why:** Avoids broad cleanup before the one allowed full retry.

- `_run_restore_stream` (function, line 1530): Build and run one backup-send → optional mbuffer → Timeshift-receive pipeline for any topology. **Why:** Keeps local, pull, and SSH-target transport semantics in one implementation.

- `_receive_restore_payload` (function, line 1561): Verify hidden parent identity, receive one payload, narrowly retry a missing-parent failure, and verify the result. **Why:** Guarantees every incremental has an actual receiver-side parent and expected Received UUID.

- `restore_backups` (function, line 1654): Coordinate planning, warnings, overrides, typed confirmations, hidden-chain receive, writable CoW exposure, Timeshift verification, and cleanup. **Why:** Keeps destructive ordering and rollback boundaries explicit for every restore mode.

## `timeshift_btrfs_sync/retention.py`

**Module role:** Destination retention/pruning logic.

**Why this module exists:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `PrunePlan` (class, line 32): Dry-run friendly prune plan. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `PrunePlan.add_keep` (method, line 39): Mark a snapshot as kept and remember the human reason. **Why:** Keeps this operation inside `PrunePlan` so callers cannot bypass the class's endpoint and validation rules.

- `PrunePlan.add_delete` (method, line 46): Mark a snapshot as deletable only when it is not already protected. **Why:** Keeps this operation inside `PrunePlan` so callers cannot bypass the class's endpoint and validation rules.

- `_is_app_created_ondemand` (function, line 54): Return true when a state entry is a tag O snapshot with the app marker. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `_delete_reason_for_snapshot` (function, line 66): Explain why a snapshot is outside the active retention rules. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `_delete_reasons` (function, line 102): Return delete reasons without the internal prefix. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `_source_cache_delete_paths` (function, line 111): Return app-owned source send-cache paths for a prune decision. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `_protected_timeshift_send_paths` (function, line 156): Return direct Timeshift send paths that prune must never delete. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `_destination_delete_paths` (function, line 186): Return tracked destination subvolume paths for a prune decision. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `source_snapshot_state` (function, line 197): Return temporary state-like data from source Timeshift snapshots. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `initial_sync_keep_names` (function, line 222): Return source snapshot names that a fresh destination should seed. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `_cleanup_source_cache_for_pruned_snapshot` (function, line 233): Delete one pruned snapshot's app-owned cache through the shared tree engine. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `build_prune_plan` (function, line 280): Build retention plan from state without deleting anything. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `_delete_destination_snapshot_for_prune` (function, line 365): Delete one destination date through the shared tree engine. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `_delete_prune_item` (function, line 391): Execute one pure prune plan and remove state after both trees are gone. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `print_prune_plan` (function, line 451): Write an easy-to-read retention summary to terminal and .succes. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

- `prune` (function, line 497): Apply destination retention rules. **Why:** Selects retained snapshots and applies guarded destination/cache/state pruning.

## `timeshift_btrfs_sync/source.py`

**Module role:** Command runner for local or SSH Timeshift and backup endpoints.

**Why this module exists:** Provides the shared local/SSH transport used for Timeshift and remote-backup endpoints.

- `SourceRunner` (class, line 12): Run commands through one local or SSH endpoint. **Why:** Provides the shared local/SSH transport used for Timeshift and remote-backup endpoints.

- `SourceRunner.from_mode` (method, line 24): Create a local or SSH command runner from one validated mode. **Why:** Keeps this operation inside `SourceRunner` so callers cannot bypass the class's endpoint and validation rules.

- `SourceRunner.from_config` (method, line 36): Create the configured Timeshift source runner. **Why:** Keeps this operation inside `SourceRunner` so callers cannot bypass the class's endpoint and validation rules.

- `SourceRunner.uses_ssh` (property, line 42): Return True when source commands are executed through SSH. **Why:** Keeps this operation inside `SourceRunner` so callers cannot bypass the class's endpoint and validation rules.

- `SourceRunner.location` (property, line 48): Return the metadata location label used by Btrfs helpers. **Why:** Keeps this operation inside `SourceRunner` so callers cannot bypass the class's endpoint and validation rules.

- `SourceRunner.command` (method, line 53): Return argv that runs one source-side shell command. **Why:** Keeps this operation inside `SourceRunner` so callers cannot bypass the class's endpoint and validation rules.

- `SourceRunner.run` (method, line 60): Run one source-side command and capture stdout/stderr. **Why:** Keeps this operation inside `SourceRunner` so callers cannot bypass the class's endpoint and validation rules.

- `SourceRunner.environment` (method, line 87): Return environment needed for streaming source commands. **Why:** Keeps this operation inside `SourceRunner` so callers cannot bypass the class's endpoint and validation rules.

- `SourceRunner.test` (method, line 94): Verify that the source command endpoint is usable. **Why:** Keeps this operation inside `SourceRunner` so callers cannot bypass the class's endpoint and validation rules.

## `timeshift_btrfs_sync/ssh.py`

**Module role:** SSH command construction.

**Why this module exists:** Builds and validates SSH commands, authentication, and optional connection reuse.

- `_is_relative_to` (function, line 15): Return True when path is root or below root without broad string matching. **Why:** Builds and validates SSH commands, authentication, and optional connection reuse.

- `validate_control_path_safety` (function, line 25): Create and validate a private SSH ControlPath socket directory. **Why:** Builds and validates SSH commands, authentication, and optional connection reuse.

- `SSHConfig` (class, line 95): Connection and SSH transport settings. **Why:** Builds and validates SSH commands, authentication, and optional connection reuse.

- `SSHConfig.target` (property, line 112): Return host or user@host. **Why:** Keeps this operation inside `SSHConfig` so callers cannot bypass the class's endpoint and validation rules.

- `SSHConfig.uses_password_auth` (property, line 118): Return True when sshpass is needed. **Why:** Keeps this operation inside `SSHConfig` so callers cannot bypass the class's endpoint and validation rules.

- `SSHConfig._read_password` (method, line 123): Read password from TOML or password_file. **Why:** Keeps this operation inside `SSHConfig` so callers cannot bypass the class's endpoint and validation rules.

- `SSHConfig.environment` (method, line 132): Return environment variables required by sshpass. **Why:** Keeps this operation inside `SSHConfig` so callers cannot bypass the class's endpoint and validation rules.

- `SSHConfig.base_command` (method, line 140): Build base SSH argv; remote command is appended later. **Why:** Keeps this operation inside `SSHConfig` so callers cannot bypass the class's endpoint and validation rules.

- `SSHRunner` (class, line 165): Run remote commands through SSH. **Why:** Builds and validates SSH commands, authentication, and optional connection reuse.

- `SSHRunner.__init__` (method, line 168): Internal function for init. **Why:** Keeps this operation inside `SSHRunner` so callers cannot bypass the class's endpoint and validation rules.

- `SSHRunner.command` (method, line 171): Return argv for one SSH remote command. **Why:** Keeps this operation inside `SSHRunner` so callers cannot bypass the class's endpoint and validation rules.

- `SSHRunner.run` (method, line 176): Run a remote command and capture stdout/stderr. **Why:** Keeps this operation inside `SSHRunner` so callers cannot bypass the class's endpoint and validation rules.

- `SSHRunner.environment` (method, line 202): Return SSH environment for streaming pipeline calls. **Why:** Keeps this operation inside `SSHRunner` so callers cannot bypass the class's endpoint and validation rules.

- `SSHRunner.test` (method, line 207): Verify SSH works and stdout is not polluted by banners. **Why:** Keeps this operation inside `SSHRunner` so callers cannot bypass the class's endpoint and validation rules.

## `timeshift_btrfs_sync/state.py`

**Module role:** Persistent local state for completed transfers.

**Why this module exists:** Validates, resolves, reads, and writes the current state schema.

- `empty_state` (function, line 28): Return a new empty state document. **Why:** Validates, resolves, reads, and writes the current state schema.

- `_safe_relative_path` (function, line 34): Return a normalized destination-relative path or raise ValueError. **Why:** Validates, resolves, reads, and writes the current state schema.

- `_safe_source_relative_path` (function, line 46): Return a normalized safe POSIX path relative to a configured source root. **Why:** Validates, resolves, reads, and writes the current state schema.

- `_normalize_source_root` (function, line 65): Return one normalized absolute-style POSIX source root. **Why:** Validates, resolves, reads, and writes the current state schema.

- `_source_path_relative_to_root` (function, line 72): Return ``path`` relative to ``root`` when it is currently below that root. **Why:** Validates, resolves, reads, and writes the current state schema.

- `_expected_snapshot_relative_path` (function, line 90): Return the canonical ``<snapshot>/<subvolume>`` source-relative path. **Why:** Validates, resolves, reads, and writes the current state schema.

- `source_path_to_relative` (function, line 98): Convert a current source path to canonical configured-root-relative state form. **Why:** Validates, resolves, reads, and writes the current state schema.

- `resolve_source_path` (function, line 124): Resolve a current root-relative state path under its configured source root. **Why:** Validates, resolves, reads, and writes the current state schema.

- `destination_path_to_relative` (function, line 143): Convert a current destination path to target-root-relative state form. **Why:** Validates, resolves, reads, and writes the current state schema.

- `resolve_destination_path` (function, line 155): Resolve a current target-root-relative state destination path. **Why:** Validates, resolves, reads, and writes the current state schema.

- `send_path_kind_for_state_subvolume` (function, line 160): Return the explicitly stored current send-path ownership kind. **Why:** Validates, resolves, reads, and writes the current state schema.

- `_source_root_for_kind` (function, line 168): Return the configured source root used by one stored send-path kind. **Why:** Validates, resolves, reads, and writes the current state schema.

- `resolve_state_send_path` (function, line 180): Resolve stored ``send_path`` under its current configured source root. **Why:** Validates, resolves, reads, and writes the current state schema.

- `_reject_unknown_state_keys` (function, line 213): Internal function for reject unknown state keys. **Why:** Validates, resolves, reads, and writes the current state schema.

- `validate_state_document` (function, line 219): Validate the complete current state schema before any workflow uses it. **Why:** Validates, resolves, reads, and writes the current state schema.

- `load_state` (function, line 297): Load and validate the current state document, or return an empty one when absent. **Why:** Validates, resolves, reads, and writes the current state schema.

- `save_state` (function, line 309): Validate and atomically write the current state document. **Why:** Validates, resolves, reads, and writes the current state schema.

- `refresh_snapshot_metadata_from_source` (function, line 328): Refresh mutable Timeshift metadata for already-known snapshots. **Why:** Validates, resolves, reads, and writes the current state schema.

- `snapshot_is_synced` (function, line 355): Return True when a snapshot is recorded as fully synced. **Why:** Validates, resolves, reads, and writes the current state schema.

- `_kind_for_absolute_source_path` (function, line 367): Classify a current absolute source path by configured ownership root. **Why:** Validates, resolves, reads, and writes the current state schema.

- `mark_subvolume_synced` (function, line 384): Record one successful send/receive using only root-relative state paths. **Why:** Validates, resolves, reads, and writes the current state schema.

- `state_send_path_is_app_cache` (function, line 499): Return True when the stored send path belongs to the app cache. **Why:** Validates, resolves, reads, and writes the current state schema.

- `state_send_path_is_protected_timeshift_original` (function, line 504): Return True when the stored send path belongs to Timeshift. **Why:** Validates, resolves, reads, and writes the current state schema.

- `remove_snapshot_from_state` (function, line 509): Remove a pruned snapshot from state. **Why:** Validates, resolves, reads, and writes the current state schema.

- `refresh_state_metadata_and_report` (function, line 515): Refresh only Timeshift tags/comment/created/path, report, and save. **Why:** Validates, resolves, reads, and writes the current state schema.

- `latest_synced_before` (function, line 539): Return newest older synced parent candidate. **Why:** Validates, resolves, reads, and writes the current state schema.

## `timeshift_btrfs_sync/sync.py`

**Module role:** Normal backup planning, full/incremental send, recovery, metadata, and state updates.

**Why this module exists:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `SyncError` (class, line 47): Raised for sync safety errors. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_local_meta` (function, line 51): Internal function for local meta. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_source_meta` (function, line 57): Return source metadata, preferring bulk indexes over one-off probes. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_human_blank` (function, line 81): Print one blank line to separate human-readable status blocks. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_human_rule` (function, line 87): Print a visual separator with blank lines around it. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_record_sync_event` (function, line 96): Add one planned or completed transfer to the run summary. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_print_sync_summary` (function, line 125): Write a terminal-friendly transfer summary to terminal and .succes. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `prepare_destination` (function, line 171): Create/validate destination helper folders before writes. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `list_source_snapshots` (function, line 191): Discover source Timeshift snapshots. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `source_snapshot_index` (function, line 214): Internal function for source snapshot index. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_snapshots_from_source_inventory` (function, line 218): Build Timeshift snapshot objects from one coherent source inventory. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_required_pipeline_source_changes` (function, line 236): Return identity changes to source paths required by current work. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `confirm_source_identity_before_manual_snapshot` (function, line 275): Print and enforce the shared manual-snapshot source identity guard. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_is_app_manual_snapshot` (function, line 327): Return True for source Timeshift O snapshots created by this app. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_pending_app_manual_snapshots` (function, line 343): Return app-created on-demand snapshots that still need syncing. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_maybe_create_manual_snapshot` (function, line 368): Optionally create a source Timeshift tag O snapshot before sync. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_snapshots_in_sync_order` (function, line 457): Return source snapshots oldest-to-newest for Btrfs send. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_select_initial_sync_snapshots` (function, line 463): Return retention-kept source snapshots for a fresh destination seed. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `print_snapshot_table` (function, line 482): Print source snapshots in table form. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_dest_subvolume_path` (function, line 493): Return the final local path for one received subvolume. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_target_snapshot_dir` (function, line 503): Return the managed destination date subvolume passed to `btrfs receive`. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_destination_info_json_path` (function, line 513): Return the destination Timeshift control-file path for one snapshot. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_ensure_destination_snapshot_subvolume` (function, line 519): Create or validate one managed destination date subvolume. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_validate_destination_snapshot_layout` (function, line 569): Refuse ordinary/symlinked date entries after exact Btrfs verification. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_atomic_write_snapshot_info_json` (function, line 630): Atomically write one captured Timeshift ``info.json`` file. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_require_snapshot_info_json` (function, line 663): Return captured control-file content or raise a precise sync error. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_sync_snapshot_info_json` (function, line 697): Create or refresh destination ``info.json`` for one complete snapshot. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_destination_has_existing_snapshots` (function, line 737): Return true only when a date directory contains a configured payload subvolume. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_snapshot_destination_paths_exist` (function, line 758): Return True only when every expected destination subvolume path exists. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_preview_send_path` (function, line 763): Return the send path that would be used, without creating cache snapshots. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_send_path_kind_text` (function, line 777): Return human text explaining who owns the selected send path. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_ensure_source_send_path` (function, line 787): Resolve one real send path through the shared cache operation. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_cleanup_incomplete_destination_receive` (function, line 814): Delete one exact incomplete destination Btrfs child before retrying. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_cleanup_source_cache_snapshot_version` (function, line 844): Delete one app-owned cache date through the shared tree engine. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_cleanup_destination_snapshot_version` (function, line 875): Delete one destination date through the shared tree engine. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_refresh_snapshot_source_subvolumes_live` (function, line 904): Return configured source subvolumes, preferring the bulk index. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_snapshot_destination_has_any_path` (function, line 933): Return True when the destination date folder or configured children exist. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_snapshot_state_is_complete_with_destination` (function, line 942): Return True only when state and destination contain every configured subvolume. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_recover_snapshot_version` (function, line 949): Remove stale current-version traces from cache, destination, and state. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_prepare_snapshot_for_transfer_or_recover` (function, line 1004): Return True when a snapshot can be transferred, False when skipped. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_recover_stale_state_snapshots_missing_from_source` (function, line 1078): Clean incomplete state entries whose Timeshift source name is gone. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_read_local_destination_parent_metadata` (function, line 1110): Read metadata for the destination snapshot that would be the receiver parent. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_match_source_path_to_destination_received_uuid` (function, line 1132): Check whether a source send-stream UUID matches destination identity. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_select_verified_parent_send_path` (function, line 1194): Select a safe source parent path for incremental send without recreating it. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_state_uuid_values_for_path` (function, line 1301): Return the current state UUID that identifies one source candidate. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_find_confirmed_sync_floor` (function, line 1318): Return newest state snapshot that still exists on source and matches UUIDs. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_destination_snapshot_names` (function, line 1445): Return destination snapshot folder names sorted oldest-to-newest. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_expected_original_source_path` (function, line 1454): Return the Timeshift-owned original source path for one snapshot/subvolume. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_source_cache_meta_by_uuid` (function, line 1460): Return indexed read-only source-cache metadata for one send UUID. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_match_existing_destination_to_source` (function, line 1479): Match one existing destination subvolume to an exact source/cache UUID. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_recover_state_from_existing_destination` (function, line 1557): Rebuild missing/empty state.json from proven source/destination matches. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_filesystem_parent_candidates` (function, line 1682): Find local destination parent candidates by matching snapshot names. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_select_parent` (function, line 1706): Choose the newest valid incremental parent. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `_verify_sync_viability_before_manual_snapshot` (function, line 1850): Prove sync can start before asking Timeshift to create a snapshot. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

- `sync_once` (function, line 1978): Run one sync pass. **Why:** Keeps backup creation, recovery, parent selection, cache reuse, state recording, and metadata copying consistent.

## `timeshift_btrfs_sync/timeshift.py`

**Module role:** Timeshift command wrappers and parser for `timeshift --list`.

**Why this module exists:** Parses Timeshift output and constructs current Timeshift commands and metadata.

- `timeshift_cmd` (function, line 17): Build a source-side shell command that invokes sudo+timeshift. **Why:** Parses Timeshift output and constructs current Timeshift commands and metadata.

- `normalize_tags` (function, line 23): Return unique Timeshift tag letters found in text. **Why:** Parses Timeshift output and constructs current Timeshift commands and metadata.

- `parse_timeshift_list` (function, line 33): Parse Timeshift snapshot names and tag/comment text. **Why:** Parses Timeshift output and constructs current Timeshift commands and metadata.

- `list_source_snapshots` (function, line 66): Discover source snapshots through SSH or local source commands. **Why:** Parses Timeshift output and constructs current Timeshift commands and metadata.

- `create_remote_manual_snapshot_cmd` (function, line 107): Build the Timeshift manual/on-demand snapshot create command. **Why:** Parses Timeshift output and constructs current Timeshift commands and metadata.

- `create_source_manual_snapshot` (function, line 126): Create a source Timeshift on-demand snapshot through SSH or locally. **Why:** Parses Timeshift output and constructs current Timeshift commands and metadata.

## `timeshift_btrfs_sync/tree_ops.py`

**Module role:** Single Btrfs tree discovery, deletion, and post-verification engine.

**Why this module exists:** Discovers and deletes complete Btrfs trees deepest-first with strict verification.

- `TreeDeleteResult` (class, line 15): Internal class for TreeDeleteResult. **Why:** Discovers and deletes complete Btrfs trees deepest-first with strict verification.

- `TreeDeleteResult.success` (property, line 26): Internal function for success. **Why:** Keeps this operation inside `TreeDeleteResult` so callers cannot bypass the class's endpoint and validation rules.

- `_path_exists` (function, line 31): Internal function for path exists. **Why:** Discovers and deletes complete Btrfs trees deepest-first with strict verification.

- `discover_subvolume_tree` (function, line 42): Discover a complete nested Btrfs tree in one endpoint list command. **Why:** Discovers and deletes complete Btrfs trees deepest-first with strict verification.

- `list_direct_entries` (function, line 68): List exact direct children with shell built-ins on either endpoint. **Why:** Discovers and deletes complete Btrfs trees deepest-first with strict verification.

- `_validate_confirmations` (function, line 84): Internal function for validate confirmations. **Why:** Discovers and deletes complete Btrfs trees deepest-first with strict verification.

- `_verify_absent` (function, line 101): Internal function for verify absent. **Why:** Discovers and deletes complete Btrfs trees deepest-first with strict verification.

- `delete_subvolume_tree` (function, line 118): Delete one managed tree deepest-first and prove the root is absent. **Why:** Discovers and deletes complete Btrfs trees deepest-first with strict verification.

## `tools/pyinstaller_entry.py`

**Module role:** Small PyInstaller entry point for building the ts-btrfs executable.

**Why this module exists:** Provides the executable entry point used by PyInstaller builds.

No runtime classes or functions are defined in this file.

## CLI commands

**Module role:** User-facing command surface created by `timeshift_btrfs_sync.cli.build_parser`.

**Why this section exists:** Commands are operational entry points rather than Python definitions, so they are listed explicitly with their safety purpose.

- `init-config`: Writes a complete commented sync or restore-pull TOML profile. **Why:** Keeps users on the current validated configuration schema instead of incomplete hand-written examples.

- `test-source`: Tests local/SSH source access and required Timeshift/Btrfs commands. **Why:** Finds endpoint and sudo failures before backup or restore work.

- `list-source`: Lists Timeshift snapshots, with optional exact Btrfs verification. **Why:** Separates fast visibility from slower payload validation.

- `sync`: Creates or reuses safe send snapshots and transfers missing backup payloads oldest-to-newest. **Why:** Provides the normal guarded backup workflow.

- `prune`: Applies configured destination retention and matching cache/state cleanup. **Why:** Keeps deletion separate, previewable, and confirmation-gated.

- `restore`: Restores one backup or a validated chain in local, SSH-backup pull, or SSH-target mode. **Why:** Uses one common-parent and hidden-chain implementation for every transport topology.

- `create-manual`: Creates a source Timeshift on-demand snapshot after continuity preflight. **Why:** Avoids creating snapshots when the current backup chain cannot safely continue.

- `destroy-leftovers`: Deletes the configured app-owned source cache and/or destination Btrfs trees. **Why:** Provides a deliberate reset path without ever deleting the Timeshift-owned snapshot root.

- `clear-state`: Removes the configured state file with lock and typed confirmations. **Why:** Makes state reset explicit because incremental continuity must later be rebuilt from UUID evidence.

- `delete-lock`: Removes only a stale configured lock after guarded checks. **Why:** Prevents lock deletion from being used to interrupt an active process.

- `show-state`: Displays current transfer state in table or JSON form. **Why:** Lets operators inspect recorded original/send identities and completed snapshots.
