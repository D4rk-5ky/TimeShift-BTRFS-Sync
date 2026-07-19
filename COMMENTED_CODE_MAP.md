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

**Why this module exists:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `new_subparser` (function/method, line 35): Perform the new subparser step used by this module. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `add_config_arg` (function/method, line 41): Perform the add config arg step used by this module. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `add_run_mode_args` (function/method, line 43): Perform the add run mode args step used by this module. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `add_yes_delete_arg` (function/method, line 49): Perform the add yes delete arg step used by this module. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `_load_config_state` (function/method, line 53): Load state and resolve all root-relative paths against this config. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `_failure_exit_code` (function/method, line 59): Return a stable CLI exit code for failure notifications. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `_stderr_tail_for_exception` (function/method, line 75): Return the best available recent stderr text for failure notifications. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `_send_notifications` (function/method, line 85): Send optional MQTT/email status without changing the command exit code. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `_mail_attachment_paths` (function/method, line 125): Return current run log paths for optional email attachment. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `_safe_destroy_log_dir` (function/method, line 135): Return a log directory that will survive a destructive cleanup. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `_with_logging` (function/method, line 176): Run a command with optional logging and MQTT notification. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `_resolve_dry_run` (function/method, line 225): Perform the resolve dry run step used by this module. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `cmd_init_config` (function/method, line 233): Perform the cmd init config step used by this module. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `cmd_test_source` (function/method, line 244): Perform the cmd test source step used by this module. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `cmd_test_source._run` (function/method, line 247): Perform the run step used by this module. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `_refresh_state_metadata_from_timeshift` (function/method, line 265): Refresh mutable state metadata from one fast Timeshift list read. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `cmd_list_source` (function/method, line 273): List snapshots on the source machine. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `cmd_list_source._run` (function/method, line 283): Perform the run step used by this module. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `cmd_sync` (function/method, line 296): Perform the cmd sync step used by this module. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `cmd_sync._run_dry` (function/method, line 300): Perform the run dry step used by this module. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `cmd_sync._run_locked` (function/method, line 309): Perform the run locked step used by this module. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `cmd_prune` (function/method, line 326): Perform the cmd prune step used by this module. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `cmd_prune._run_dry` (function/method, line 330): Perform the run dry step used by this module. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `cmd_prune._run_locked` (function/method, line 338): Perform the run locked step used by this module. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `cmd_restore` (function/method, line 355): Restore one snapshot or the complete post-common backup chain into Timeshift. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `cmd_restore._run` (function/method, line 361): Perform the run step used by this module. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `cmd_create_manual` (function/method, line 387): Perform the cmd create manual step used by this module. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `cmd_create_manual._run` (function/method, line 390): Perform the run step used by this module. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `cmd_clear_state` (function/method, line 416): Guardedly remove the configured state_file with normal run logging. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `cmd_clear_state._run` (function/method, line 422): Perform the run step used by this module. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `cmd_delete_lock` (function/method, line 444): Guardedly remove the configured lock_file if it is stale, with logging. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `cmd_delete_lock._run` (function/method, line 450): Perform the run step used by this module. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `cmd_destroy_leftovers` (function/method, line 461): Destroy configured leftovers with normal run logging enabled. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `cmd_destroy_leftovers._run` (function/method, line 475): Perform the run step used by this module. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `cmd_show_state` (function/method, line 487): Perform the cmd show state step used by this module. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `cmd_show_state._run` (function/method, line 490): Perform the run step used by this module. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `build_parser` (function/method, line 533): Create the argparse parser and command-specific flag help. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

- `main` (function/method, line 749): Perform the main step used by this module. **Why:** Connects the current command-line interface to the runtime workflows and shared notification/logging lifecycle.

## `timeshift_btrfs_sync/commands.py`

**Module role:** Shared subprocess helpers.

**Why this module exists:** Provides checked process execution and consistent error reporting for local commands.

- `CommandError` (class, line 21): Raised when an external command exits with a non-zero status. **Why:** Provides checked process execution and consistent error reporting for local commands.

- `CommandError.__init__` (function/method, line 24): Perform the init step used by this module. **Why:** Provides checked process execution and consistent error reporting for local commands.

- `Completed` (class, line 39): Captured exit status and text streams for one command. **Why:** Provides checked process execution and consistent error reporting for local commands.

- `sudo_prefix` (function/method, line 47): Split a configured sudo prefix into argv parts. **Why:** Provides checked process execution and consistent error reporting for local commands.

- `quote_join` (function/method, line 55): Quote argv parts into one safe remote-shell command string. **Why:** Provides checked process execution and consistent error reporting for local commands.

- `remote_double_quote` (function/method, line 61): Return a shell-safe double-quoted argument for a remote shell command. **Why:** Provides checked process execution and consistent error reporting for local commands.

- `_merged_env` (function/method, line 84): Merge optional child-process environment variables. **Why:** Provides checked process execution and consistent error reporting for local commands.

- `run_local` (function/method, line 94): Run a local command and capture stdout/stderr. **Why:** Provides checked process execution and consistent error reporting for local commands.

- `_start_pipeline_readers` (function/method, line 151): Start tee readers from compact stream routing specs. **Why:** Provides checked process execution and consistent error reporting for local commands.

- `_failed_stderr` (function/method, line 170): Return captured pipeline stderr for streams that belong in failures. **Why:** Provides checked process execution and consistent error reporting for local commands.

- `_log_failed_streams` (function/method, line 176): Copy captured failed pipeline streams to .err. **Why:** Provides checked process execution and consistent error reporting for local commands.

- `stream_pipeline` (function/method, line 188): Stream left command into optional middle command, then right command. **Why:** Provides checked process execution and consistent error reporting for local commands.

## `timeshift_btrfs_sync/config.py`

**Module role:** TOML configuration loading and validation.

**Why this module exists:** Defines and validates the complete current configuration surface before filesystem work begins.

- `_reject_unknown_keys` (function/method, line 34): Reject configuration entries that are not part of the current schema. **Why:** Defines and validates the complete current configuration surface before filesystem work begins.

- `ManualSnapshotConfig` (class, line 42): Optional source-side Timeshift on-demand snapshot creation and cleanup. **Why:** Defines and validates the complete current configuration surface before filesystem work begins.

- `SourceConfig` (class, line 76): Source Timeshift and Btrfs settings. **Why:** Defines and validates the complete current configuration surface before filesystem work begins.

- `DestinationConfig` (class, line 117): Local/destination receive settings. **Why:** Defines and validates the complete current configuration surface before filesystem work begins.

- `StreamConfig` (class, line 131): Optional pipeline display/buffering settings. **Why:** Defines and validates the complete current configuration surface before filesystem work begins.

- `StreamConfig.command` (function/method, line 151): Return mbuffer command argv or None when disabled. **Why:** Defines and validates the complete current configuration surface before filesystem work begins.

- `RetentionConfig` (class, line 165): Destination retention counts by Timeshift tag. **Why:** Defines and validates the complete current configuration surface before filesystem work begins.

- `RetentionConfig.counts_by_tag` (function/method, line 184): Return retention counts keyed by Timeshift tag letters. **Why:** Defines and validates the complete current configuration surface before filesystem work begins.

- `AppConfig` (class, line 190): Complete validated app configuration. **Why:** Defines and validates the complete current configuration surface before filesystem work begins.

- `ConfigError` (class, line 208): Raised when the TOML config is invalid. **Why:** Defines and validates the complete current configuration surface before filesystem work begins.

- `_table` (function/method, line 211): Perform the table step used by this module. **Why:** Defines and validates the complete current configuration surface before filesystem work begins.

- `_optional_str` (function/method, line 217): Perform the optional str step used by this module. **Why:** Defines and validates the complete current configuration surface before filesystem work begins.

- `_positive_int` (function/method, line 220): Perform the positive int step used by this module. **Why:** Defines and validates the complete current configuration surface before filesystem work begins.

- `_stripped` (function/method, line 227): Perform the stripped step used by this module. **Why:** Defines and validates the complete current configuration surface before filesystem work begins.

- `_bool` (function/method, line 230): Perform the bool step used by this module. **Why:** Defines and validates the complete current configuration surface before filesystem work begins.

- `_int` (function/method, line 233): Perform the int step used by this module. **Why:** Defines and validates the complete current configuration surface before filesystem work begins.

- `_as_str` (function/method, line 236): Perform the as str step used by this module. **Why:** Defines and validates the complete current configuration surface before filesystem work begins.

- `_as_path` (function/method, line 241): Perform the as path step used by this module. **Why:** Defines and validates the complete current configuration surface before filesystem work begins.

- `_as_bool` (function/method, line 244): Perform the as bool step used by this module. **Why:** Defines and validates the complete current configuration surface before filesystem work begins.

- `_as_int` (function/method, line 251): Perform the as int step used by this module. **Why:** Defines and validates the complete current configuration surface before filesystem work begins.

- `_string_list` (function/method, line 258): Perform the string list step used by this module. **Why:** Defines and validates the complete current configuration surface before filesystem work begins.

- `load_config` (function/method, line 266): Read and validate TOML config. **Why:** Defines and validates the complete current configuration surface before filesystem work begins.

## `timeshift_btrfs_sync/destroy.py`

**Module role:** Destructive setup retirement using the shared Btrfs tree engine.

**Why this module exists:** Applies destructive confirmations and presents results from the shared Btrfs tree engine.

- `DestroyResult` (class, line 26): Named wrapper around the shared tree-deletion result. **Why:** Applies destructive confirmations and presents results from the shared Btrfs tree engine.

- `_safe_cleanup_path` (function/method, line 33): Perform the safe cleanup path step used by this module. **Why:** Applies destructive confirmations and presents results from the shared Btrfs tree engine.

- `_confirm_or_raise` (function/method, line 46): Perform the confirm or raise step used by this module. **Why:** Applies destructive confirmations and presents results from the shared Btrfs tree engine.

- `_mode_text` (function/method, line 51): Perform the mode text step used by this module. **Why:** Applies destructive confirmations and presents results from the shared Btrfs tree engine.

- `_load_payload_state` (function/method, line 57): Perform the load payload state step used by this module. **Why:** Applies destructive confirmations and presents results from the shared Btrfs tree engine.

- `_result_by_label` (function/method, line 64): Perform the result by label step used by this module. **Why:** Applies destructive confirmations and presents results from the shared Btrfs tree engine.

- `_print_payload_match` (function/method, line 68): Perform the print payload match step used by this module. **Why:** Applies destructive confirmations and presents results from the shared Btrfs tree engine.

- `_print_result` (function/method, line 87): Perform the print result step used by this module. **Why:** Applies destructive confirmations and presents results from the shared Btrfs tree engine.

- `destroy_leftovers` (function/method, line 118): Plan and execute selected source/destination tree retirement. **Why:** Applies destructive confirmations and presents results from the shared Btrfs tree engine.

- `destroy_leftovers.handle` (function/method, line 172): Perform the handle step used by this module. **Why:** Applies destructive confirmations and presents results from the shared Btrfs tree engine.

## `timeshift_btrfs_sync/endpoint.py`

**Module role:** Unified command endpoints for local and source-side operations.

**Why this module exists:** Makes local and SSH command transport interchangeable without duplicating Btrfs workflow logic.

- `CommandEndpoint` (class, line 19): Execute commands on one local or source-side endpoint. **Why:** Makes local and SSH command transport interchangeable without duplicating Btrfs workflow logic.

- `CommandEndpoint.for_source` (function/method, line 30): Perform the for source step used by this module. **Why:** Makes local and SSH command transport interchangeable without duplicating Btrfs workflow logic.

- `CommandEndpoint.local` (function/method, line 34): Perform the local step used by this module. **Why:** Makes local and SSH command transport interchangeable without duplicating Btrfs workflow logic.

- `CommandEndpoint.location` (property, line 38): Perform the location step used by this module. **Why:** Makes local and SSH command transport interchangeable without duplicating Btrfs workflow logic.

- `CommandEndpoint.shell_command` (function/method, line 41): Return a safely quoted shell command for this endpoint. **Why:** Makes local and SSH command transport interchangeable without duplicating Btrfs workflow logic.

- `CommandEndpoint.command` (function/method, line 46): Return process argv for a command executed on this endpoint. **Why:** Makes local and SSH command transport interchangeable without duplicating Btrfs workflow logic.

- `CommandEndpoint.run_argv` (function/method, line 54): Execute one argv command through the endpoint transport. **Why:** Makes local and SSH command transport interchangeable without duplicating Btrfs workflow logic.

- `CommandEndpoint.run_shell` (function/method, line 82): Execute one shell script through the endpoint transport. **Why:** Makes local and SSH command transport interchangeable without duplicating Btrfs workflow logic.

## `timeshift_btrfs_sync/executor.py`

**Module role:** Generic ordered workflow action executor.

**Why this module exists:** Runs ordered workflow actions through explicit handlers, keeping plan construction separate from side effects.

- `WorkflowExecutor` (class, line 14): Execute or preview a plan using one handler per action kind. **Why:** Runs ordered workflow actions through explicit handlers, keeping plan construction separate from side effects.

- `WorkflowExecutor.execute` (function/method, line 22): Perform the execute step used by this module. **Why:** Runs ordered workflow actions through explicit handlers, keeping plan construction separate from side effects.

## `timeshift_btrfs_sync/inventory.py`

**Module role:** Per-run Btrfs subvolume indexes for fewer SSH calls.

**Why this module exists:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `BtrfsIndex` (class, line 29): In-memory index of Btrfs subvolumes below one root path. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `BtrfsIndex.add` (function/method, line 40): Add or replace one indexed subvolume. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `BtrfsIndex.discard` (function/method, line 53): Remove one path and any known UUID lookup entries for it. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `BtrfsIndex.contains` (function/method, line 65): Return True when ``path`` is an indexed subvolume. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `BtrfsIndex.meta` (function/method, line 70): Return metadata for ``path`` if it was indexed. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `BtrfsIndex.remove_tree` (function/method, line 75): Remove a deleted path and all indexed descendants. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `SourceInventory` (class, line 85): One coherent source-side Timeshift/Btrfs inventory. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `SourceInventory.snapshot_names` (property, line 105): Return Timeshift timestamp names in sorted order. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `SourceInventory.meta` (function/method, line 111): Return source metadata from cache first, then snapshot-root index. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `_clean_uuid` (function/method, line 122): Normalize Btrfs UUID fields from list/show output. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `parse_subvolume_list` (function/method, line 131): Parse ``btrfs subvolume list -u -q -R`` output for one root. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `_paths_from_list_output` (function/method, line 157): Return absolute subvolume paths parsed from any ``btrfs subvolume list`` output. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `_mark_readonly_from_list` (function/method, line 171): Mark indexed paths read-only using one ``btrfs subvolume list -r`` result. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `build_local_btrfs_index` (function/method, line 187): Build a local Btrfs index with bulk list commands. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `_remote_bulk_index_script` (function/method, line 235): Return a POSIX shell script that bulk-lists source Btrfs metadata. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `build_source_btrfs_index` (function/method, line 281): Build a source Btrfs index in SSH or local mode. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `build_remote_btrfs_index` (function/method, line 313): Build a remote source index using one SSH command. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `_parse_remote_btrfs_index_result` (function/method, line 345): Parse one remote bulk-index section into a :class:`BtrfsIndex`. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `_parse_remote_btrfs_index_result.flush_list` (function/method, line 377): Perform the flush list step used by this module. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `_parse_remote_btrfs_index_result.flush_readonly` (function/method, line 385): Perform the flush readonly step used by this module. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `_remote_source_inventory_script` (function/method, line 445): Return one remote script for Timeshift, info.json, and both Btrfs roots. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `_extract_snapshot_info_json_frames` (function/method, line 527): Remove and parse the ``cat`` payloads from combined SSH output. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `_extract_snapshot_info_json_frames.replace` (function/method, line 544): Perform the replace step used by this module. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `_split_remote_source_inventory_output` (function/method, line 561): Split combined output into identity, Timeshift, info.json, and Btrfs sections. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `_current_process_identity` (function/method, line 634): Return the effective local account name and UID used to read metadata. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `_read_local_snapshot_info_json` (function/method, line 645): Read all local Timeshift control files without spawning commands. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `_record_missing_info_json_errors` (function/method, line 672): Record listed Timeshift dates that had no readable control file. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `build_source_inventory` (function/method, line 686): Build one coherent Timeshift/snapshot/cache source inventory. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `describe_source_inventory_changes` (function/method, line 809): Return concise human-readable differences between two inventories. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `describe_source_inventory_changes.compare_index` (function/method, line 822): Perform the compare index step used by this module. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

- `refresh_path` (function/method, line 861): Refresh one exact path through the shared Btrfs operation layer. **Why:** Builds one coherent view of Timeshift metadata and Btrfs identities for source, cache, and destination decisions.

## `timeshift_btrfs_sync/lock.py`

**Module role:** Simple file lock for sync/prune commands.

**Why this module exists:** Prevents concurrent jobs from modifying the same configured backup state.

- `FileLock` (class, line 9): flock() based non-blocking exclusive lock. **Why:** Prevents concurrent jobs from modifying the same configured backup state.

- `FileLock.__init__` (function/method, line 12): Perform the init step used by this module. **Why:** Prevents concurrent jobs from modifying the same configured backup state.

- `FileLock.__enter__` (function/method, line 16): Perform the enter step used by this module. **Why:** Prevents concurrent jobs from modifying the same configured backup state.

- `FileLock.__exit__` (function/method, line 28): Perform the exit step used by this module. **Why:** Prevents concurrent jobs from modifying the same configured backup state.

## `timeshift_btrfs_sync/log.py`

**Module role:** Split run logging for timeshift-btrfs-sync.

**Why this module exists:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `RunLogger` (class, line 32): Owns the split log files for one run. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `RunLogger.__post_init__` (function/method, line 38): Create the log directory and open the run log files. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `RunLogger.close` (function/method, line 71): Close all log files. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `RunLogger.attachment_paths` (function/method, line 81): Return run log files in the order useful for mail attachments. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `RunLogger._write` (function/method, line 91): Write text safely from possible stream-reader threads. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `RunLogger._remember_stderr` (function/method, line 98): Keep a small tail of stderr for failure notifications. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `RunLogger.last_stderr_tail` (function/method, line 106): Return the newest stderr text remembered for MQTT/error reports. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `RunLogger._line` (function/method, line 112): Write exactly one logical line. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `RunLogger.info` (function/method, line 119): Write a normal status line to .log. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `RunLogger.mbuffer` (function/method, line 124): Write one line to the .mbuffer transfer-progress log. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `RunLogger.btrfs_out` (function/method, line 129): Write one line to the .btrfs Btrfs verbose-output log. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `RunLogger.success` (function/method, line 134): Write one line to the .succes human-readable summary log. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `RunLogger.success_text` (function/method, line 139): Write a preformatted block to the .succes summary log. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `RunLogger.err` (function/method, line 146): Write an error/stderr line to .err and remember its tail. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `RunLogger.command` (function/method, line 153): Record a command that is about to run. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `RunLogger.completed` (function/method, line 176): Record the output from a normal captured command. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `RunLogger.pipeline_commands` (function/method, line 207): Record send/buffer/receive commands to the appropriate logs. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `RunLogger.pipeline_summary` (function/method, line 218): Record final pipeline status. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `RunLogger.stream_text` (function/method, line 226): Write live pipeline text to terminal and/or split log files. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `emit_success_summary` (function/method, line 254): Write a readable summary to the real terminal and .succes only. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `TeeTextIO` (class, line 270): Terminal stream wrapper that also writes normal app output to run logs. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `TeeTextIO.__init__` (function/method, line 283): Perform the init step used by this module. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `TeeTextIO.write` (function/method, line 290): Perform the write step used by this module. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `TeeTextIO.flush` (function/method, line 303): Perform the flush step used by this module. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `TeeTextIO.isatty` (function/method, line 306): Perform the isatty step used by this module. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `TeeTextIO.fileno` (function/method, line 309): Perform the fileno step used by this module. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `TeeTextIO.writable` (function/method, line 312): Perform the writable step used by this module. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `TeeTextIO.__getattr__` (function/method, line 315): Perform the getattr step used by this module. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `terminal_stdout` (function/method, line 323): Return the real terminal stdout, bypassing the run-log tee wrapper. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `terminal_stderr` (function/method, line 329): Return the real terminal stderr, bypassing the run-log tee wrapper. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `get_logger` (function/method, line 337): Return the active logger, if file logging is enabled. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `active_logger` (function/method, line 344): Temporarily install a run logger and tee app output to files. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `create_run_logger` (function/method, line 380): Create a logger when log_dir is configured; otherwise return None. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `tee_pipe_to_log` (function/method, line 402): Start a thread that reads bytes from a process pipe and logs them live. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

- `tee_pipe_to_log._reader` (function/method, line 421): Perform the reader step used by this module. **Why:** Separates normal, error, transfer, and success output while preserving terminal behavior.

## `timeshift_btrfs_sync/mail.py`

**Module role:** Optional email notifications for timeshift-btrfs-sync.

**Why this module exists:** Builds and sends optional SMTP status notifications from current run results.

- `MailConfig` (class, line 20): SMTP settings for optional email notifications. **Why:** Builds and sends optional SMTP status notifications from current run results.

- `MailConfig.resolved_password` (function/method, line 52): Return password from config value or password_file. **Why:** Builds and sends optional SMTP status notifications from current run results.

- `_subject` (function/method, line 61): Create a short readable subject line. **Why:** Builds and sends optional SMTP status notifications from current run results.

- `_body` (function/method, line 72): Create a fallback plain-text email body from the status payload. **Why:** Builds and sends optional SMTP status notifications from current run results.

- `_success_body_from_paths` (function/method, line 101): Return the text content of the non-empty .succes file, if present. **Why:** Builds and sends optional SMTP status notifications from current run results.

- `_filter_attachments` (function/method, line 118): Return existing attachment paths and human-readable skipped reasons. **Why:** Builds and sends optional SMTP status notifications from current run results.

- `_attach_file` (function/method, line 148): Attach one file to an EmailMessage. **Why:** Builds and sends optional SMTP status notifications from current run results.

- `send_status` (function/method, line 159): Send one optional SMTP status email. **Why:** Builds and sends optional SMTP status notifications from current run results.

## `timeshift_btrfs_sync/maintenance.py`

**Module role:** Guarded maintenance commands for state and lock files.

**Why this module exists:** Implements explicit state and stale-lock maintenance commands.

- `_confirm_or_raise` (function/method, line 21): Require an exact typed confirmation before destructive maintenance. **Why:** Implements explicit state and stale-lock maintenance commands.

- `_safe_configured_file` (function/method, line 29): Return a normalized configured file path or raise for unsafe targets. **Why:** Implements explicit state and stale-lock maintenance commands.

- `_looks_like_state_file` (function/method, line 44): Return True when an existing file appears to be ts-btrfs state. **Why:** Implements explicit state and stale-lock maintenance commands.

- `_looks_like_lock_file` (function/method, line 63): Return True when an existing file looks like this app's simple lock file. **Why:** Implements explicit state and stale-lock maintenance commands.

- `_print_header` (function/method, line 77): Print the common maintenance command warning block. **Why:** Implements explicit state and stale-lock maintenance commands.

- `_require_real_confirmation` (function/method, line 90): Require real-mode flags and typed confirmations. **Why:** Implements explicit state and stale-lock maintenance commands.

- `clear_state_file` (function/method, line 110): Remove the configured state.json file after explicit confirmation. **Why:** Implements explicit state and stale-lock maintenance commands.

- `delete_lock_file` (function/method, line 160): Delete the configured lock file when no running process holds it. **Why:** Implements explicit state and stale-lock maintenance commands.

## `timeshift_btrfs_sync/models.py`

**Module role:** Shared dataclasses for snapshots and subvolumes.

**Why this module exists:** Carries the Btrfs and Timeshift identity data shared by inventory, sync, retention, and state.

- `SubvolumeMeta` (class, line 9): Metadata for one Btrfs subvolume inside one Timeshift snapshot. **Why:** Carries the Btrfs and Timeshift identity data shared by inventory, sync, retention, and state.

- `SnapshotMeta` (class, line 22): Metadata for one Timeshift snapshot. **Why:** Carries the Btrfs and Timeshift identity data shared by inventory, sync, retention, and state.

- `SnapshotMeta.sort_key` (function/method, line 32): Timeshift timestamp names sort oldest-to-newest lexically. **Why:** Carries the Btrfs and Timeshift identity data shared by inventory, sync, retention, and state.

- `tags_text` (function/method, line 38): Return compact human text for Timeshift tags. **Why:** Carries the Btrfs and Timeshift identity data shared by inventory, sync, retention, and state.

## `timeshift_btrfs_sync/mqtt.py`

**Module role:** Optional MQTT notifications for timeshift-btrfs-sync.

**Why this module exists:** Publishes optional MQTT status notifications from current run results.

- `MQTTConfig` (class, line 19): MQTT broker and publish settings. **Why:** Publishes optional MQTT status notifications from current run results.

- `MQTTConfig.resolved_password` (function/method, line 41): Return password from config value or password_file. **Why:** Publishes optional MQTT status notifications from current run results.

- `publish_status` (function/method, line 51): Publish one JSON MQTT status message. **Why:** Publishes optional MQTT status notifications from current run results.

## `timeshift_btrfs_sync/notify.py`

**Module role:** Shared notification payload helpers.

**Why this module exists:** Creates one normalized notification payload for terminal, MQTT, and mail consumers.

- `utc_timestamp` (function/method, line 10): Return a compact ISO-8601 UTC timestamp for notifications. **Why:** Creates one normalized notification payload for terminal, MQTT, and mail consumers.

- `build_notification_payload` (function/method, line 16): Build the shared status payload used by MQTT and email. **Why:** Creates one normalized notification payload for terminal, MQTT, and mail consumers.

## `timeshift_btrfs_sync/paths.py`

**Module role:** Canonical path normalization and containment rules.

**Why this module exists:** Keeps path normalization, containment, and Btrfs listed-path mapping consistent across safety checks.

- `normalize_source_path` (function/method, line 13): Normalize POSIX path text while preserving an intentionally empty value. **Why:** Keeps path normalization, containment, and Btrfs listed-path mapping consistent across safety checks.

- `is_same_or_under` (function/method, line 23): Return true when ``path`` equals ``root`` or is below it. **Why:** Keeps path normalization, containment, and Btrfs listed-path mapping consistent across safety checks.

- `is_local_same_or_under` (function/method, line 35): Return true when one local path resolves to ``root`` or below it. **Why:** Keeps path normalization, containment, and Btrfs listed-path mapping consistent across safety checks.

- `is_under` (function/method, line 55): Return true only when ``path`` is strictly below ``root``. **Why:** Keeps path normalization, containment, and Btrfs listed-path mapping consistent across safety checks.

- `listed_path_to_absolute` (function/method, line 67): Resolve a Btrfs filesystem-relative list path below a mounted root. **Why:** Keeps path normalization, containment, and Btrfs listed-path mapping consistent across safety checks.

- `sort_deepest_first` (function/method, line 103): Deduplicate and order paths for child-before-parent deletion. **Why:** Keeps path normalization, containment, and Btrfs listed-path mapping consistent across safety checks.

## `timeshift_btrfs_sync/payload_stats.py`

**Module role:** Normalized source/destination payload statistics for Btrfs snapshot trees.

**Why this module exists:** Compares source and destination payload inventories for destroy reporting.

- `PayloadTreeStats` (class, line 30): Normalized payload/container counts for one source or destination tree. **Why:** Compares source and destination payload inventories for destroy reporting.

- `PayloadTreeStats.total_payload` (property, line 47): Return the number of real cached/received payload subvolumes. **Why:** Compares source and destination payload inventories for destroy reporting.

- `PayloadTreeStats.total_cache_payload` (property, line 53): Return how many source payloads came from app-owned source cache. **Why:** Compares source and destination payload inventories for destroy reporting.

- `PayloadTreeStats.total_direct_payload` (property, line 59): Return how many source payloads came from protected Timeshift originals. **Why:** Compares source and destination payload inventories for destroy reporting.

- `normalize_path` (function/method, line 65): Normalize paths so source/destination comparisons ignore trailing slashes. **Why:** Compares source and destination payload inventories for destroy reporting.

- `_relative_parts` (function/method, line 71): Return path parts relative to root, or None if path is outside root. **Why:** Compares source and destination payload inventories for destroy reporting.

- `_recount_payload` (function/method, line 85): Rebuild per-subvolume counters from the normalized payload set. **Why:** Compares source and destination payload inventories for destroy reporting.

- `_add_payload` (function/method, line 93): Add a payload entry when relative parts end in a configured subvolume name. **Why:** Compares source and destination payload inventories for destroy reporting.

- `source_send_cache_stats` (function/method, line 106): Classify source send-cache subvolumes into payload and helper counts. **Why:** Compares source and destination payload inventories for destroy reporting.

- `destination_payload_stats` (function/method, line 129): Classify destination target subvolumes into received payload counts. **Why:** Compares source and destination payload inventories for destroy reporting.

- `direct_send_payload_stats` (function/method, line 152): Return payload entries streamed directly from protected Timeshift originals. **Why:** Compares source and destination payload inventories for destroy reporting.

- `merge_source_payload_stats` (function/method, line 184): Merge app-cache and protected direct-send payload into one source view. **Why:** Compares source and destination payload inventories for destroy reporting.

- `PayloadMatchStats` (class, line 207): Comparison between source send payload and destination received payload. **Why:** Compares source and destination payload inventories for destroy reporting.

- `PayloadMatchStats.source_only` (property, line 214): Return source payload entries not present on the destination. **Why:** Compares source and destination payload inventories for destroy reporting.

- `PayloadMatchStats.destination_only` (property, line 220): Return destination payload entries not present on the source side. **Why:** Compares source and destination payload inventories for destroy reporting.

- `PayloadMatchStats.ok` (property, line 226): Return True when source send payload and destination payload match. **Why:** Compares source and destination payload inventories for destroy reporting.

- `compare_payloads` (function/method, line 232): Return normalized source/destination payload comparison stats. **Why:** Compares source and destination payload inventories for destroy reporting.

- `_format_count_line` (function/method, line 238): Return an aligned summary line. **Why:** Compares source and destination payload inventories for destroy reporting.

- `render_payload_match` (function/method, line 244): Render the source/destination payload comparison block. **Why:** Compares source and destination payload inventories for destroy reporting.

## `timeshift_btrfs_sync/planning.py`

**Module role:** Pure workflow planning from a combined backup inventory.

**Why this module exists:** Creates ordered action plans without touching the filesystem.

- `ActionKind` (class, line 17): Perform the ActionKind step used by this module. **Why:** Creates ordered action plans without touching the filesystem.

- `WorkflowAction` (class, line 28): Perform the WorkflowAction step used by this module. **Why:** Creates ordered action plans without touching the filesystem.

- `WorkflowPlan` (class, line 36): Perform the WorkflowPlan step used by this module. **Why:** Creates ordered action plans without touching the filesystem.

- `WorkflowPlan.add` (function/method, line 40): Perform the add step used by this module. **Why:** Creates ordered action plans without touching the filesystem.

- `plan_sync_queue` (function/method, line 52): Plan the oldest-to-newest sync queue without executing operations. **Why:** Creates ordered action plans without touching the filesystem.

- `plan_snapshot_recovery` (function/method, line 79): Plan one whole-date recovery in cache, destination, then state order. **Why:** Creates ordered action plans without touching the filesystem.

- `plan_prune_snapshot` (function/method, line 89): Perform the plan prune snapshot step used by this module. **Why:** Creates ordered action plans without touching the filesystem.

- `plan_destroy_targets` (function/method, line 102): Plan named endpoint/root destruction in the caller-provided order. **Why:** Creates ordered action plans without touching the filesystem.

## `timeshift_btrfs_sync/preflight.py`

**Module role:** Sync path preflight checks.

**Why this module exists:** Validates required paths, permissions, commands, and Btrfs layout before a real workflow changes data.

- `PathPreflightError` (class, line 44): Raised before any destructive/creating sync work when required paths fail. **Why:** Validates required paths, permissions, commands, and Btrfs layout before a real workflow changes data.

- `PathCheck` (class, line 49): One configured path availability result. **Why:** Validates required paths, permissions, commands, and Btrfs layout before a real workflow changes data.

- `_shell_words` (function/method, line 60): Return a shell-safe string for configured command-prefix words. **Why:** Validates required paths, permissions, commands, and Btrfs layout before a real workflow changes data.

- `_parse_path_check_output` (function/method, line 66): Parse source-path preflight sentinel lines into structured checks. **Why:** Validates required paths, permissions, commands, and Btrfs layout before a real workflow changes data.

- `_source_snapshot_root_script` (function/method, line 99): Build a source script that validates Timeshift-owned source.snapshot_root. **Why:** Validates required paths, permissions, commands, and Btrfs layout before a real workflow changes data.

- `_cache_root_check_script` (function/method, line 167): Build a source script that validates or creates source.cache_root. **Why:** Validates required paths, permissions, commands, and Btrfs layout before a real workflow changes data.

- `_combined_source_path_check_script` (function/method, line 243): Run both source-root preflight checks inside one source command. **Why:** Validates required paths, permissions, commands, and Btrfs layout before a real workflow changes data.

- `_source_path_checks` (function/method, line 275): Check/create both source roots with at most one SSH command. **Why:** Validates required paths, permissions, commands, and Btrfs layout before a real workflow changes data.

- `_parent_of_path` (function/method, line 354): Return the immediate parent path used for exact-path creation checks. **Why:** Validates required paths, permissions, commands, and Btrfs layout before a real workflow changes data.

- `_local_btrfs_result` (function/method, line 361): Run one local destination sudo+btrfs command for preflight checks. **Why:** Validates required paths, permissions, commands, and Btrfs layout before a real workflow changes data.

- `_compact_process_error` (function/method, line 373): Return compact stderr/stdout text from a failed subprocess. **Why:** Validates required paths, permissions, commands, and Btrfs layout before a real workflow changes data.

- `_compact_os_error` (function/method, line 380): Return compact text for local filesystem creation errors. **Why:** Validates required paths, permissions, commands, and Btrfs layout before a real workflow changes data.

- `_print_check_block` (function/method, line 386): Print one human-readable preflight result block. **Why:** Validates required paths, permissions, commands, and Btrfs layout before a real workflow changes data.

- `_raise_for_failed_checks` (function/method, line 401): Raise a hard preflight error when any check failed. **Why:** Validates required paths, permissions, commands, and Btrfs layout before a real workflow changes data.

- `ensure_local_helper_dir` (function/method, line 411): Ensure one local helper directory exists. **Why:** Validates required paths, permissions, commands, and Btrfs layout before a real workflow changes data.

- `prepare_lock_path` (function/method, line 565): Create/verify the lock directory before other sync/prune directories. **Why:** Validates required paths, permissions, commands, and Btrfs layout before a real workflow changes data.

- `prepare_destination_helper_paths` (function/method, line 597): Create/verify local destination helper folders used by sync/prune. **Why:** Validates required paths, permissions, commands, and Btrfs layout before a real workflow changes data.

- `_local_target_path_check` (function/method, line 644): Check/create destination.target_root locally. **Why:** Validates required paths, permissions, commands, and Btrfs layout before a real workflow changes data.

- `check_required_sync_paths` (function/method, line 786): Verify/create required configured roots before manual snapshot creation or send. **Why:** Validates required paths, permissions, commands, and Btrfs layout before a real workflow changes data.

## `timeshift_btrfs_sync/restore.py`

**Module role:** Restore one backed-up snapshot or a complete full-plus-incremental chain into the source Timeshift repository.

**Why this module exists:** Owns one shared local/SSH restore implementation, native Timeshift layout validation, stable info.json OS identity checks, UUID-confirmed common-parent selection, exact receive-parent reuse, justified full-seed fallback, writable CoW exposure, mandatory risk acknowledgements, staged commit, and exact failed-attempt cleanup.

- `RestoreError` (class, line 40): Raised when backups cannot be imported safely into Timeshift. **Why:** Owns one shared local/SSH restore implementation, native Timeshift layout validation, stable info.json OS identity checks, UUID-confirmed common-parent selection, exact receive-parent reuse, justified full-seed fallback, writable CoW exposure, mandatory risk acknowledgements, staged commit, and exact failed-attempt cleanup.

- `TimeshiftOsIdentity` (class, line 45): Stable Timeshift metadata used to identify one OS installation. **Why:** Owns one shared local/SSH restore implementation, native Timeshift layout validation, stable info.json OS identity checks, UUID-confirmed common-parent selection, exact receive-parent reuse, justified full-seed fallback, writable CoW exposure, mandatory risk acknowledgements, staged commit, and exact failed-attempt cleanup.

- `BackupSnapshot` (class, line 54): One validated destination snapshot available for restore. **Why:** Owns one shared local/SSH restore implementation, native Timeshift layout validation, stable info.json OS identity checks, UUID-confirmed common-parent selection, exact receive-parent reuse, justified full-seed fallback, writable CoW exposure, mandatory risk acknowledgements, staged commit, and exact failed-attempt cleanup.

- `_effective_send_uuid` (function/method, line 64): Return the UUID identity carried by a Btrfs send stream. **Why:** Owns one shared local/SSH restore implementation, native Timeshift layout validation, stable info.json OS identity checks, UUID-confirmed common-parent selection, exact receive-parent reuse, justified full-seed fallback, writable CoW exposure, mandatory risk acknowledgements, staged commit, and exact failed-attempt cleanup.

- `_info_os_identity` (function/method, line 78): Return stable Timeshift OS identity while ignoring per-snapshot fields. **Why:** Owns one shared local/SSH restore implementation, native Timeshift layout validation, stable info.json OS identity checks, UUID-confirmed common-parent selection, exact receive-parent reuse, justified full-seed fallback, writable CoW exposure, mandatory risk acknowledgements, staged commit, and exact failed-attempt cleanup.

- `_parse_info_json` (function/method, line 98): Parse one Timeshift control file and extract its stable OS identity. **Why:** Owns one shared local/SSH restore implementation, native Timeshift layout validation, stable info.json OS identity checks, UUID-confirmed common-parent selection, exact receive-parent reuse, justified full-seed fallback, writable CoW exposure, mandatory risk acknowledgements, staged commit, and exact failed-attempt cleanup.

- `_same_os_identity` (function/method, line 110): Return whether two Timeshift identities prove the same OS installation. **Why:** Owns one shared local/SSH restore implementation, native Timeshift layout validation, stable info.json OS identity checks, UUID-confirmed common-parent selection, exact receive-parent reuse, justified full-seed fallback, writable CoW exposure, mandatory risk acknowledgements, staged commit, and exact failed-attempt cleanup.

- `_consistent_backup_identity` (function/method, line 121): Require one non-conflicting OS identity across the selected backup set. **Why:** Owns one shared local/SSH restore implementation, native Timeshift layout validation, stable info.json OS identity checks, UUID-confirmed common-parent selection, exact receive-parent reuse, justified full-seed fallback, writable CoW exposure, mandatory risk acknowledgements, staged commit, and exact failed-attempt cleanup.

- `_source_info_identities` (function/method, line 148): Parse stable OS identities from the coherent source info.json inventory. **Why:** Owns one shared local/SSH restore implementation, native Timeshift layout validation, stable info.json OS identity checks, UUID-confirmed common-parent selection, exact receive-parent reuse, justified full-seed fallback, writable CoW exposure, mandatory risk acknowledgements, staged commit, and exact failed-attempt cleanup.

- `_compare_repository_os_identity` (function/method, line 161): Compare one backup identity with all current Timeshift control files. **Why:** Owns one shared local/SSH restore implementation, native Timeshift layout validation, stable info.json OS identity checks, UUID-confirmed common-parent selection, exact receive-parent reuse, justified full-seed fallback, writable CoW exposure, mandatory risk acknowledgements, staged commit, and exact failed-attempt cleanup.

- `RestorePlan` (class, line 189): A side-effect-free single or chain restore plan. **Why:** Owns one shared local/SSH restore implementation, native Timeshift layout validation, stable info.json OS identity checks, UUID-confirmed common-parent selection, exact receive-parent reuse, justified full-seed fallback, writable CoW exposure, mandatory risk acknowledgements, staged commit, and exact failed-attempt cleanup.

- `RestorePlan.seed_name` (property, line 206): Perform the seed name step used by this module. **Why:** Owns one shared local/SSH restore implementation, native Timeshift layout validation, stable info.json OS identity checks, UUID-confirmed common-parent selection, exact receive-parent reuse, justified full-seed fallback, writable CoW exposure, mandatory risk acknowledgements, staged commit, and exact failed-attempt cleanup.

- `_source_path_exists` (function/method, line 210): Perform the source path exists step used by this module. **Why:** Owns one shared local/SSH restore implementation, native Timeshift layout validation, stable info.json OS identity checks, UUID-confirmed common-parent selection, exact receive-parent reuse, justified full-seed fallback, writable CoW exposure, mandatory risk acknowledgements, staged commit, and exact failed-attempt cleanup.

- `_privileged_argv` (function/method, line 224): Perform the privileged argv step used by this module. **Why:** Owns one shared local/SSH restore implementation, native Timeshift layout validation, stable info.json OS identity checks, UUID-confirmed common-parent selection, exact receive-parent reuse, justified full-seed fallback, writable CoW exposure, mandatory risk acknowledgements, staged commit, and exact failed-attempt cleanup.

- `_write_source_info_json` (function/method, line 228): Write exact captured metadata through the configured source privilege prefix. **Why:** Owns one shared local/SSH restore implementation, native Timeshift layout validation, stable info.json OS identity checks, UUID-confirmed common-parent selection, exact receive-parent reuse, justified full-seed fallback, writable CoW exposure, mandatory risk acknowledgements, staged commit, and exact failed-attempt cleanup.

- `_validate_backup_snapshot` (function/method, line 269): Validate one backup date, payload set, metadata file, and Btrfs identity. **Why:** Owns one shared local/SSH restore implementation, native Timeshift layout validation, stable info.json OS identity checks, UUID-confirmed common-parent selection, exact receive-parent reuse, justified full-seed fallback, writable CoW exposure, mandatory risk acknowledgements, staged commit, and exact failed-attempt cleanup.

- `_discover_backups` (function/method, line 322): Return every valid destination backup ordered by Timeshift timestamp. **Why:** Owns one shared local/SSH restore implementation, native Timeshift layout validation, stable info.json OS identity checks, UUID-confirmed common-parent selection, exact receive-parent reuse, justified full-seed fallback, writable CoW exposure, mandatory risk acknowledgements, staged commit, and exact failed-attempt cleanup.

- `_source_snapshots` (function/method, line 338): Read one coherent source Timeshift/Btrfs/info.json inventory. **Why:** Owns one shared local/SSH restore implementation, native Timeshift layout validation, stable info.json OS identity checks, UUID-confirmed common-parent selection, exact receive-parent reuse, justified full-seed fallback, writable CoW exposure, mandatory risk acknowledgements, staged commit, and exact failed-attempt cleanup.

- `_find_latest_common_parent` (function/method, line 367): Find the newest date proven common by UUID state and info.json identity. **Why:** Owns one shared local/SSH restore implementation, native Timeshift layout validation, stable info.json OS identity checks, UUID-confirmed common-parent selection, exact receive-parent reuse, justified full-seed fallback, writable CoW exposure, mandatory risk acknowledgements, staged commit, and exact failed-attempt cleanup.

- `_find_reusable_receive_parent` (function/method, line 434): Find the exact read-only source subvolumes required for first incremental receive. **Why:** Owns one shared local/SSH restore implementation, native Timeshift layout validation, stable info.json OS identity checks, UUID-confirmed common-parent selection, exact receive-parent reuse, justified full-seed fallback, writable CoW exposure, mandatory risk acknowledgements, staged commit, and exact failed-attempt cleanup.

- `_build_restore_plan` (function/method, line 500): Build a single or complete-chain restore plan without changing either side. **Why:** Owns one shared local/SSH restore implementation, native Timeshift layout validation, stable info.json OS identity checks, UUID-confirmed common-parent selection, exact receive-parent reuse, justified full-seed fallback, writable CoW exposure, mandatory risk acknowledgements, staged commit, and exact failed-attempt cleanup.

- `_remove_restore_directory` (function/method, line 597): Remove one exact app-created ordinary restore directory and its payloads. **Why:** Owns one shared local/SSH restore implementation, native Timeshift layout validation, stable info.json OS identity checks, UUID-confirmed common-parent selection, exact receive-parent reuse, justified full-seed fallback, writable CoW exposure, mandatory risk acknowledgements, staged commit, and exact failed-attempt cleanup.

- `_cleanup_restore_attempt` (function/method, line 651): Roll back only directories created by the current restore attempt. **Why:** Owns one shared local/SSH restore implementation, native Timeshift layout validation, stable info.json OS identity checks, UUID-confirmed common-parent selection, exact receive-parent reuse, justified full-seed fallback, writable CoW exposure, mandatory risk acknowledgements, staged commit, and exact failed-attempt cleanup.

- `_print_restored_snapshot_retention_warning` (function/method, line 711): Explain that restored Timeshift tags remain subject to normal retention. **Why:** Owns one shared local/SSH restore implementation, native Timeshift layout validation, stable info.json OS identity checks, UUID-confirmed common-parent selection, exact receive-parent reuse, justified full-seed fallback, writable CoW exposure, mandatory risk acknowledgements, staged commit, and exact failed-attempt cleanup.

- `_print_restore_plan` (function/method, line 728): Perform the print restore plan step used by this module. **Why:** Owns one shared local/SSH restore implementation, native Timeshift layout validation, stable info.json OS identity checks, UUID-confirmed common-parent selection, exact receive-parent reuse, justified full-seed fallback, writable CoW exposure, mandatory risk acknowledgements, staged commit, and exact failed-attempt cleanup.

- `restore_backups` (function/method, line 790): Restore one snapshot or a complete backup chain into Timeshift. **Why:** Owns one shared local/SSH restore implementation, native Timeshift layout validation, stable info.json OS identity checks, UUID-confirmed common-parent selection, exact receive-parent reuse, justified full-seed fallback, writable CoW exposure, mandatory risk acknowledgements, staged commit, and exact failed-attempt cleanup.

## `timeshift_btrfs_sync/retention.py`

**Module role:** Destination retention/pruning logic.

**Why this module exists:** Selects retained snapshots and executes safe destination/cache/state pruning in the required order.

- `PrunePlan` (class, line 32): Dry-run friendly prune plan. **Why:** Selects retained snapshots and executes safe destination/cache/state pruning in the required order.

- `PrunePlan.add_keep` (function/method, line 39): Mark a snapshot as kept and remember the human reason. **Why:** Selects retained snapshots and executes safe destination/cache/state pruning in the required order.

- `PrunePlan.add_delete` (function/method, line 46): Mark a snapshot as deletable only when it is not already protected. **Why:** Selects retained snapshots and executes safe destination/cache/state pruning in the required order.

- `_is_app_created_ondemand` (function/method, line 54): Return true when a state entry is a tag O snapshot with the app marker. **Why:** Selects retained snapshots and executes safe destination/cache/state pruning in the required order.

- `_delete_reason_for_snapshot` (function/method, line 66): Explain why a snapshot is outside the active retention rules. **Why:** Selects retained snapshots and executes safe destination/cache/state pruning in the required order.

- `_delete_reasons` (function/method, line 102): Return delete reasons without the internal prefix. **Why:** Selects retained snapshots and executes safe destination/cache/state pruning in the required order.

- `_source_cache_delete_paths` (function/method, line 111): Return app-owned source send-cache paths for a prune decision. **Why:** Selects retained snapshots and executes safe destination/cache/state pruning in the required order.

- `_protected_timeshift_send_paths` (function/method, line 156): Return direct Timeshift send paths that prune must never delete. **Why:** Selects retained snapshots and executes safe destination/cache/state pruning in the required order.

- `_destination_delete_paths` (function/method, line 186): Return tracked destination subvolume paths for a prune decision. **Why:** Selects retained snapshots and executes safe destination/cache/state pruning in the required order.

- `source_snapshot_state` (function/method, line 197): Return temporary state-like data from source Timeshift snapshots. **Why:** Selects retained snapshots and executes safe destination/cache/state pruning in the required order.

- `initial_sync_keep_names` (function/method, line 222): Return source snapshot names that a fresh destination should seed. **Why:** Selects retained snapshots and executes safe destination/cache/state pruning in the required order.

- `_cleanup_source_cache_for_pruned_snapshot` (function/method, line 233): Delete one pruned snapshot's app-owned cache through the shared tree engine. **Why:** Selects retained snapshots and executes safe destination/cache/state pruning in the required order.

- `build_prune_plan` (function/method, line 280): Build retention plan from state without deleting anything. **Why:** Selects retained snapshots and executes safe destination/cache/state pruning in the required order.

- `_delete_destination_snapshot_for_prune` (function/method, line 365): Delete one destination date through the shared tree engine. **Why:** Selects retained snapshots and executes safe destination/cache/state pruning in the required order.

- `_delete_prune_item` (function/method, line 391): Execute one pure prune plan and remove state after both trees are gone. **Why:** Selects retained snapshots and executes safe destination/cache/state pruning in the required order.

- `_delete_prune_item.delete_destination` (function/method, line 417): Perform the delete destination step used by this module. **Why:** Selects retained snapshots and executes safe destination/cache/state pruning in the required order.

- `_delete_prune_item.delete_cache` (function/method, line 422): Perform the delete cache step used by this module. **Why:** Selects retained snapshots and executes safe destination/cache/state pruning in the required order.

- `_delete_prune_item.remove_state` (function/method, line 434): Perform the remove state step used by this module. **Why:** Selects retained snapshots and executes safe destination/cache/state pruning in the required order.

- `print_prune_plan` (function/method, line 451): Write an easy-to-read retention summary to terminal and .succes. **Why:** Selects retained snapshots and executes safe destination/cache/state pruning in the required order.

- `prune` (function/method, line 497): Apply destination retention rules. **Why:** Selects retained snapshots and executes safe destination/cache/state pruning in the required order.

## `timeshift_btrfs_sync/source.py`

**Module role:** Source command runner for SSH and local source modes.

**Why this module exists:** Constructs the configured local or SSH source command runner.

- `SourceRunner` (class, line 12): Run source-side commands either over SSH or locally. **Why:** Constructs the configured local or SSH source command runner.

- `SourceRunner.from_config` (function/method, line 25): Create a source runner from validated app config. **Why:** Constructs the configured local or SSH source command runner.

- `SourceRunner.uses_ssh` (property, line 35): Return True when source commands are executed through SSH. **Why:** Constructs the configured local or SSH source command runner.

- `SourceRunner.location` (property, line 41): Return the metadata location label used by Btrfs helpers. **Why:** Constructs the configured local or SSH source command runner.

- `SourceRunner.command` (function/method, line 46): Return argv that runs one source-side shell command. **Why:** Constructs the configured local or SSH source command runner.

- `SourceRunner.run` (function/method, line 53): Run one source-side command and capture stdout/stderr. **Why:** Constructs the configured local or SSH source command runner.

- `SourceRunner.environment` (function/method, line 80): Return environment needed for streaming source commands. **Why:** Constructs the configured local or SSH source command runner.

- `SourceRunner.test` (function/method, line 87): Verify that the source command endpoint is usable. **Why:** Constructs the configured local or SSH source command runner.

## `timeshift_btrfs_sync/ssh.py`

**Module role:** SSH command construction.

**Why this module exists:** Builds SSH commands and connection options for destination-pull source access.

- `_is_relative_to` (function/method, line 15): Return True when path is root or below root without broad string matching. **Why:** Builds SSH commands and connection options for destination-pull source access.

- `validate_control_path_safety` (function/method, line 25): Create and validate a private SSH ControlPath socket directory. **Why:** Builds SSH commands and connection options for destination-pull source access.

- `SSHConfig` (class, line 95): Connection and SSH transport settings. **Why:** Builds SSH commands and connection options for destination-pull source access.

- `SSHConfig.target` (property, line 112): Return host or user@host. **Why:** Builds SSH commands and connection options for destination-pull source access.

- `SSHConfig.uses_password_auth` (property, line 118): Return True when sshpass is needed. **Why:** Builds SSH commands and connection options for destination-pull source access.

- `SSHConfig._read_password` (function/method, line 123): Read password from TOML or password_file. **Why:** Builds SSH commands and connection options for destination-pull source access.

- `SSHConfig.environment` (function/method, line 132): Return environment variables required by sshpass. **Why:** Builds SSH commands and connection options for destination-pull source access.

- `SSHConfig.base_command` (function/method, line 140): Build base SSH argv; remote command is appended later. **Why:** Builds SSH commands and connection options for destination-pull source access.

- `SSHRunner` (class, line 165): Run remote commands through SSH. **Why:** Builds SSH commands and connection options for destination-pull source access.

- `SSHRunner.__init__` (function/method, line 168): Perform the init step used by this module. **Why:** Builds SSH commands and connection options for destination-pull source access.

- `SSHRunner.command` (function/method, line 171): Return argv for one SSH remote command. **Why:** Builds SSH commands and connection options for destination-pull source access.

- `SSHRunner.run` (function/method, line 176): Run a remote command and capture stdout/stderr. **Why:** Builds SSH commands and connection options for destination-pull source access.

- `SSHRunner.environment` (function/method, line 202): Return SSH environment for streaming pipeline calls. **Why:** Builds SSH commands and connection options for destination-pull source access.

- `SSHRunner.test` (function/method, line 207): Verify SSH works and stdout is not polluted by banners. **Why:** Builds SSH commands and connection options for destination-pull source access.

## `timeshift_btrfs_sync/state.py`

**Module role:** Persistent local state for completed transfers.

**Why this module exists:** Validates and writes the exact current state schema used for completed transfer identities.

- `empty_state` (function/method, line 28): Return a new empty state document. **Why:** Validates and writes the exact current state schema used for completed transfer identities.

- `_safe_relative_path` (function/method, line 34): Return a normalized destination-relative path or raise ValueError. **Why:** Validates and writes the exact current state schema used for completed transfer identities.

- `_safe_source_relative_path` (function/method, line 46): Return a normalized safe POSIX path relative to a configured source root. **Why:** Validates and writes the exact current state schema used for completed transfer identities.

- `_normalize_source_root` (function/method, line 65): Return one normalized absolute-style POSIX source root. **Why:** Validates and writes the exact current state schema used for completed transfer identities.

- `_source_path_relative_to_root` (function/method, line 72): Return ``path`` relative to ``root`` when it is currently below that root. **Why:** Validates and writes the exact current state schema used for completed transfer identities.

- `_expected_snapshot_relative_path` (function/method, line 90): Return the canonical ``<snapshot>/<subvolume>`` source-relative path. **Why:** Validates and writes the exact current state schema used for completed transfer identities.

- `source_path_to_relative` (function/method, line 98): Convert a current source path to canonical configured-root-relative state form. **Why:** Validates and writes the exact current state schema used for completed transfer identities.

- `resolve_source_path` (function/method, line 124): Resolve a current root-relative state path under its configured source root. **Why:** Validates and writes the exact current state schema used for completed transfer identities.

- `destination_path_to_relative` (function/method, line 143): Convert a current destination path to target-root-relative state form. **Why:** Validates and writes the exact current state schema used for completed transfer identities.

- `resolve_destination_path` (function/method, line 155): Resolve a current target-root-relative state destination path. **Why:** Validates and writes the exact current state schema used for completed transfer identities.

- `send_path_kind_for_state_subvolume` (function/method, line 160): Return the explicitly stored current send-path ownership kind. **Why:** Validates and writes the exact current state schema used for completed transfer identities.

- `_source_root_for_kind` (function/method, line 168): Return the configured source root used by one stored send-path kind. **Why:** Validates and writes the exact current state schema used for completed transfer identities.

- `resolve_state_send_path` (function/method, line 180): Resolve stored ``send_path`` under its current configured source root. **Why:** Validates and writes the exact current state schema used for completed transfer identities.

- `_reject_unknown_state_keys` (function/method, line 213): Perform the reject unknown state keys step used by this module. **Why:** Validates and writes the exact current state schema used for completed transfer identities.

- `validate_state_document` (function/method, line 219): Validate the complete current state schema before any workflow uses it. **Why:** Validates and writes the exact current state schema used for completed transfer identities.

- `load_state` (function/method, line 297): Load and validate the current state document, or return an empty one when absent. **Why:** Validates and writes the exact current state schema used for completed transfer identities.

- `save_state` (function/method, line 309): Validate and atomically write the current state document. **Why:** Validates and writes the exact current state schema used for completed transfer identities.

- `refresh_snapshot_metadata_from_source` (function/method, line 328): Refresh mutable Timeshift metadata for already-known snapshots. **Why:** Validates and writes the exact current state schema used for completed transfer identities.

- `snapshot_is_synced` (function/method, line 355): Return True when a snapshot is recorded as fully synced. **Why:** Validates and writes the exact current state schema used for completed transfer identities.

- `_kind_for_absolute_source_path` (function/method, line 367): Classify a current absolute source path by configured ownership root. **Why:** Validates and writes the exact current state schema used for completed transfer identities.

- `mark_subvolume_synced` (function/method, line 384): Record one successful send/receive using only root-relative state paths. **Why:** Validates and writes the exact current state schema used for completed transfer identities.

- `state_send_path_is_app_cache` (function/method, line 499): Return True when the stored send path belongs to the app cache. **Why:** Validates and writes the exact current state schema used for completed transfer identities.

- `state_send_path_is_protected_timeshift_original` (function/method, line 504): Return True when the stored send path belongs to Timeshift. **Why:** Validates and writes the exact current state schema used for completed transfer identities.

- `remove_snapshot_from_state` (function/method, line 509): Remove a pruned snapshot from state. **Why:** Validates and writes the exact current state schema used for completed transfer identities.

- `refresh_state_metadata_and_report` (function/method, line 515): Refresh only Timeshift tags/comment/created/path, report, and save. **Why:** Validates and writes the exact current state schema used for completed transfer identities.

- `latest_synced_before` (function/method, line 539): Return newest older synced parent candidate. **Why:** Validates and writes the exact current state schema used for completed transfer identities.

## `timeshift_btrfs_sync/sync.py`

**Module role:** Main destination-pull sync workflow.

**Why this module exists:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `SyncError` (class, line 47): Raised for sync safety errors. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_local_meta` (function/method, line 51): Perform the local meta step used by this module. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_source_meta` (function/method, line 57): Return source metadata, preferring bulk indexes over one-off probes. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_human_blank` (function/method, line 81): Print one blank line to separate human-readable status blocks. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_human_rule` (function/method, line 87): Print a visual separator with blank lines around it. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_record_sync_event` (function/method, line 96): Add one planned or completed transfer to the run summary. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_print_sync_summary` (function/method, line 125): Write a terminal-friendly transfer summary to terminal and .succes. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `prepare_destination` (function/method, line 171): Create/validate destination helper folders before writes. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `list_source_snapshots` (function/method, line 191): Discover source Timeshift snapshots. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `source_snapshot_index` (function/method, line 214): Perform the source snapshot index step used by this module. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_snapshots_from_source_inventory` (function/method, line 218): Build Timeshift snapshot objects from one coherent source inventory. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_required_pipeline_source_changes` (function/method, line 236): Return identity changes to source paths required by current work. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `confirm_source_identity_before_manual_snapshot` (function/method, line 275): Print and enforce the shared manual-snapshot source identity guard. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_is_app_manual_snapshot` (function/method, line 327): Return True for source Timeshift O snapshots created by this app. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_pending_app_manual_snapshots` (function/method, line 343): Return app-created on-demand snapshots that still need syncing. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_maybe_create_manual_snapshot` (function/method, line 368): Optionally create a source Timeshift tag O snapshot before sync. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_snapshots_in_sync_order` (function/method, line 457): Return source snapshots oldest-to-newest for Btrfs send. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_select_initial_sync_snapshots` (function/method, line 463): Return retention-kept source snapshots for a fresh destination seed. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `print_snapshot_table` (function/method, line 482): Print source snapshots in table form. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_dest_subvolume_path` (function/method, line 493): Return the final local path for one received subvolume. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_target_snapshot_dir` (function/method, line 503): Return the managed destination date subvolume passed to `btrfs receive`. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_destination_info_json_path` (function/method, line 513): Return the destination Timeshift control-file path for one snapshot. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_ensure_destination_snapshot_subvolume` (function/method, line 519): Create or validate one managed destination date subvolume. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_validate_destination_snapshot_layout` (function/method, line 569): Refuse ordinary/symlinked date entries after exact Btrfs verification. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_atomic_write_snapshot_info_json` (function/method, line 630): Atomically write one captured Timeshift ``info.json`` file. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_require_snapshot_info_json` (function/method, line 663): Return captured control-file content or raise a precise sync error. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_sync_snapshot_info_json` (function/method, line 697): Create or refresh destination ``info.json`` for one complete snapshot. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_destination_has_existing_snapshots` (function/method, line 737): Return true only when a date directory contains a configured payload subvolume. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_snapshot_destination_paths_exist` (function/method, line 758): Return True only when every expected destination subvolume path exists. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_preview_send_path` (function/method, line 763): Return the send path that would be used, without creating cache snapshots. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_send_path_kind_text` (function/method, line 777): Return human text explaining who owns the selected send path. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_ensure_source_send_path` (function/method, line 787): Resolve one real send path through the shared cache operation. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_cleanup_incomplete_destination_receive` (function/method, line 814): Delete one exact incomplete destination Btrfs child before retrying. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_cleanup_source_cache_snapshot_version` (function/method, line 844): Delete one app-owned cache date through the shared tree engine. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_cleanup_destination_snapshot_version` (function/method, line 875): Delete one destination date through the shared tree engine. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_refresh_snapshot_source_subvolumes_live` (function/method, line 904): Return configured source subvolumes, preferring the bulk index. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_snapshot_destination_has_any_path` (function/method, line 933): Return True when the destination date folder or configured children exist. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_snapshot_state_is_complete_with_destination` (function/method, line 942): Return True only when state and destination contain every configured subvolume. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_recover_snapshot_version` (function/method, line 949): Remove stale current-version traces from cache, destination, and state. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_recover_snapshot_version.handle` (function/method, line 982): Perform the handle step used by this module. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_prepare_snapshot_for_transfer_or_recover` (function/method, line 1004): Return True when a snapshot can be transferred, False when skipped. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_recover_stale_state_snapshots_missing_from_source` (function/method, line 1078): Clean incomplete state entries whose Timeshift source name is gone. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_read_local_destination_parent_metadata` (function/method, line 1110): Read metadata for the destination snapshot that would be the receiver parent. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_match_source_path_to_destination_received_uuid` (function/method, line 1132): Check whether a source subvolume UUID matches the destination identity. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_select_verified_parent_send_path` (function/method, line 1186): Select a safe source parent path for incremental send without recreating it. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_select_verified_parent_send_path.add_candidate` (function/method, line 1216): Perform the add candidate step used by this module. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_state_uuid_values_for_path` (function/method, line 1294): Return the current state UUID that identifies one source candidate. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_find_confirmed_sync_floor` (function/method, line 1311): Return newest state snapshot that still exists on source and matches UUIDs. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_destination_snapshot_names` (function/method, line 1438): Return destination snapshot folder names sorted oldest-to-newest. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_expected_original_source_path` (function/method, line 1447): Return the Timeshift-owned original source path for one snapshot/subvolume. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_source_cache_meta_by_uuid` (function/method, line 1453): Return indexed read-only source-cache metadata for an exact UUID match. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_match_existing_destination_to_source` (function/method, line 1472): Match one existing destination subvolume to an exact source/cache UUID. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_recover_state_from_existing_destination` (function/method, line 1543): Rebuild missing/empty state.json from proven source/destination matches. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_filesystem_parent_candidates` (function/method, line 1668): Find local destination parent candidates by matching snapshot names. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_select_parent` (function/method, line 1692): Choose the newest valid incremental parent. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_verify_sync_viability_before_manual_snapshot` (function/method, line 1836): Prove sync can start before asking Timeshift to create a snapshot. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `_verify_sync_viability_before_manual_snapshot.verify_parent_for` (function/method, line 1893): Perform the verify parent for step used by this module. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `sync_once` (function/method, line 1964): Run one sync pass. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `sync_once.load_source_inventory` (function/method, line 2006): Build and report one coherent source inventory generation. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `sync_once.build_snapshot_queue` (function/method, line 2165): Build one pure oldest-to-newest sync plan, then return its snapshot queue. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

- `sync_once.recover_from_source_inventory_change` (function/method, line 2208): Recover one failed snapshot version and rebuild all source lists. **Why:** Orchestrates discovery, retention selection, cache preparation, UUID-safe transfer, recovery, and state updates.

## `timeshift_btrfs_sync/timeshift.py`

**Module role:** Timeshift command wrappers and parser for `timeshift --list`.

**Why this module exists:** Parses Timeshift metadata and creates current on-demand snapshots when configured.

- `timeshift_cmd` (function/method, line 17): Build a source-side shell command that invokes sudo+timeshift. **Why:** Parses Timeshift metadata and creates current on-demand snapshots when configured.

- `normalize_tags` (function/method, line 23): Return unique Timeshift tag letters found in text. **Why:** Parses Timeshift metadata and creates current on-demand snapshots when configured.

- `parse_timeshift_list` (function/method, line 33): Parse Timeshift snapshot names and tag/comment text. **Why:** Parses Timeshift metadata and creates current on-demand snapshots when configured.

- `list_source_snapshots` (function/method, line 66): Discover source snapshots through SSH or local source commands. **Why:** Parses Timeshift metadata and creates current on-demand snapshots when configured.

- `create_remote_manual_snapshot_cmd` (function/method, line 107): Build the Timeshift manual/on-demand snapshot create command. **Why:** Parses Timeshift metadata and creates current on-demand snapshots when configured.

- `create_source_manual_snapshot` (function/method, line 126): Create a source Timeshift on-demand snapshot through SSH or locally. **Why:** Parses Timeshift metadata and creates current on-demand snapshots when configured.

## `timeshift_btrfs_sync/tree_ops.py`

**Module role:** Single Btrfs tree discovery, deletion, and post-verification engine.

**Why this module exists:** Discovers complete nested Btrfs trees, deletes deepest-first, and verifies the configured root is absent.

- `TreeDeleteResult` (class, line 15): Perform the TreeDeleteResult step used by this module. **Why:** Discovers complete nested Btrfs trees, deletes deepest-first, and verifies the configured root is absent.

- `TreeDeleteResult.success` (property, line 26): Perform the success step used by this module. **Why:** Discovers complete nested Btrfs trees, deletes deepest-first, and verifies the configured root is absent.

- `_path_exists` (function/method, line 31): Perform the path exists step used by this module. **Why:** Discovers complete nested Btrfs trees, deletes deepest-first, and verifies the configured root is absent.

- `discover_subvolume_tree` (function/method, line 42): Discover a complete nested Btrfs tree in one endpoint list command. **Why:** Discovers complete nested Btrfs trees, deletes deepest-first, and verifies the configured root is absent.

- `list_direct_entries` (function/method, line 68): List exact direct children with shell built-ins on either endpoint. **Why:** Discovers complete nested Btrfs trees, deletes deepest-first, and verifies the configured root is absent.

- `_validate_confirmations` (function/method, line 84): Perform the validate confirmations step used by this module. **Why:** Discovers complete nested Btrfs trees, deletes deepest-first, and verifies the configured root is absent.

- `_verify_absent` (function/method, line 101): Perform the verify absent step used by this module. **Why:** Discovers complete nested Btrfs trees, deletes deepest-first, and verifies the configured root is absent.

- `delete_subvolume_tree` (function/method, line 118): Delete one managed tree deepest-first and prove the root is absent. **Why:** Discovers complete nested Btrfs trees, deletes deepest-first, and verifies the configured root is absent.

## `tools/pyinstaller_entry.py`

**Module role:** Small PyInstaller entry point for building the ts-btrfs executable.

**Why this module exists:** Provides the packaged executable entry point.

No runtime classes or functions are defined in this file.
