# Commented code map — TimeShift-BTRFS-Sync 0.2.0

This file explains every Python class, function, method and nested callback in the current project, plus application commands and supplied shell/integration commands. Line numbers refer to this release. COMMENTED_CODE_MAP.md is the canonical code map; VERSIONING.md is the canonical version ledger.

The active package is timeshift_btrfs_sync/, selected by pyproject.toml. Current tests, docs, build helpers and integration examples live at the root. The older nested project was removed as requested; former paths are listed in REMOVED_NESTED_SOURCES.md.

Runtime layers reuse CommandEndpoint, BtrfsOps, CacheManager, inventory, WorkflowPlan/WorkflowExecutor and delete_subvolume_tree. Timeshift original snapshots remain protected; only freshly verified app-created on-demand retention uses Timeshift deletion. Parent recovery now uses live read-only/UUID proof and retention protects the newest complete proven shared date. Ordinary source H/D/W/M/B retention remains managed by Timeshift.

## `scripts/build_pyinstaller.py`

**Role:** Current source/build entry. Build ts-btrfs executables with PyInstaller.

**Why:** Builds the existing CLI entry point with complete config data and optional MQTT support instead of introducing another application implementation.

- `build_args` (function/method, line 28): Return the PyInstaller argument list for one build mode. **Why:** Builds the existing CLI entry point with complete config data and optional MQTT support instead of introducing another application implementation.

- `run_pyinstaller` (function/method, line 55): Run PyInstaller with a useful error if it is not installed. **Why:** Builds the existing CLI entry point with complete config data and optional MQTT support instead of introducing another application implementation.

- `main` (function/method, line 71): Parse arguments and run the requested build. **Why:** Builds the existing CLI entry point with complete config data and optional MQTT support instead of introducing another application implementation.

## `tests/test_btrfs_only_layout.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `DestinationDateSubvolumeTests` (class, line 19): Groups DestinationDateSubvolume regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `DestinationDateSubvolumeTests.make_config` (function/method, line 20): Test support: make config; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationDateSubvolumeTests` to use its existing endpoint, state or callback context.

- `DestinationDateSubvolumeTests.test_new_date_path_is_created_as_btrfs_subvolume_once` (function/method, line 26): Regression assertion: new date path is created as btrfs subvolume once. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationDateSubvolumeTests` to use its existing endpoint, state or callback context.

- `DestinationDateSubvolumeTests.test_new_date_path_is_created_as_btrfs_subvolume_once.fake_create` (function/method, line 36): Test support: fake create; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationDateSubvolumeTests.test_new_date_path_is_created_as_btrfs_subvolume_once` to use its existing endpoint, state or callback context.

- `DestinationDateSubvolumeTests.test_new_date_path_is_created_as_btrfs_subvolume_once.fake_refresh` (function/method, line 40): Test support: fake refresh; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationDateSubvolumeTests.test_new_date_path_is_created_as_btrfs_subvolume_once` to use its existing endpoint, state or callback context.

- `DestinationDateSubvolumeTests.test_existing_ordinary_date_folder_is_refused` (function/method, line 56): Regression assertion: existing ordinary date folder is refused. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationDateSubvolumeTests` to use its existing endpoint, state or callback context.

- `DestroyBtrfsOnlyTests` (class, line 66): Groups DestroyBtrfsOnly regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `DestroyBtrfsOnlyTests.test_nonempty_ordinary_root_is_refused_by_shared_tree_engine` (function/method, line 67): Regression assertion: nonempty ordinary root is refused by shared tree engine. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestroyBtrfsOnlyTests` to use its existing endpoint, state or callback context.

- `DestroyBtrfsOnlyTests.test_batch_delete_uses_only_btrfs_and_rejects_bad_confirmations` (function/method, line 80): Regression assertion: batch delete uses only btrfs and rejects bad confirmations. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestroyBtrfsOnlyTests` to use its existing endpoint, state or callback context.

- `DestroyBtrfsOnlyTests.test_batch_delete_uses_only_btrfs_and_rejects_bad_confirmations.fake_run` (function/method, line 90): Test support: fake run; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestroyBtrfsOnlyTests.test_batch_delete_uses_only_btrfs_and_rejects_bad_confirmations` to use its existing endpoint, state or callback context.

- `DestroyBtrfsOnlyTests.test_runtime_package_contains_no_recursive_rm_fallback` (function/method, line 101): Regression assertion: runtime package contains no recursive rm fallback. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestroyBtrfsOnlyTests` to use its existing endpoint, state or callback context.

## `tests/test_cache_exact_reuse.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `FakeSource` (class, line 13): Groups FakeSource regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `FakeSource.__init__` (function/method, line 17): Test support: init; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `FakeSource` to use its existing endpoint, state or callback context.

- `FakeSource.run` (function/method, line 21): Test support: run; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `FakeSource` to use its existing endpoint, state or callback context.

- `make_index` (function/method, line 28): Test support: make index; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `CacheExactReuseTests` (class, line 35): Groups CacheExactReuse regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `CacheExactReuseTests.test_stale_bulk_index_reuses_exact_existing_cache_snapshot_without_nested_name` (function/method, line 36): Regression assertion: stale bulk index reuses exact existing cache snapshot without nested name. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CacheExactReuseTests` to use its existing endpoint, state or callback context.

- `CacheExactReuseTests.test_root_scoped_bare_relative_cache_child_is_indexed_and_reused` (function/method, line 87): Regression assertion: root scoped bare relative cache child is indexed and reused. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CacheExactReuseTests` to use its existing endpoint, state or callback context.

- `CacheExactReuseTests.test_existing_cache_without_parent_uuid_is_refused` (function/method, line 103): Regression assertion: existing cache without parent uuid is refused. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CacheExactReuseTests` to use its existing endpoint, state or callback context.

- `CacheExactReuseTests.test_existing_non_subvolume_target_is_refused_before_snapshot_creation` (function/method, line 109): Regression assertion: existing non subvolume target is refused before snapshot creation. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CacheExactReuseTests` to use its existing endpoint, state or callback context.

- `CacheExactReuseTests.test_concurrent_exact_cache_creator_is_reused_after_create_failure` (function/method, line 131): Regression assertion: concurrent exact cache creator is reused after create failure. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CacheExactReuseTests` to use its existing endpoint, state or callback context.

- `MountedSubvolumePathResolutionTests` (class, line 166): Groups MountedSubvolumePathResolution regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `MountedSubvolumePathResolutionTests.test_bulk_index_resolves_on_disk_prefix_absent_from_mount_path` (function/method, line 167): Regression assertion: bulk index resolves on disk prefix absent from mount path. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `MountedSubvolumePathResolutionTests` to use its existing endpoint, state or callback context.

- `MountedSubvolumePathResolutionTests.test_parse_bulk_list_keeps_existing_cache_child_after_remount` (function/method, line 173): Regression assertion: parse bulk list keeps existing cache child after remount. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `MountedSubvolumePathResolutionTests` to use its existing endpoint, state or callback context.

## `tests/test_cleanup_superseded_cache_modes.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `CleanupSupersededCacheModeTests` (class, line 16): Groups CleanupSupersededCacheMode regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `CleanupSupersededCacheModeTests._config_path` (function/method, line 17): Test support: config path; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CleanupSupersededCacheModeTests` to use its existing endpoint, state or callback context.

- `CleanupSupersededCacheModeTests.test_current_option_loads_for_local_and_ssh_sources` (function/method, line 35): Regression assertion: current option loads for local and ssh sources. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CleanupSupersededCacheModeTests` to use its existing endpoint, state or callback context.

- `CleanupSupersededCacheModeTests.test_sync_accepts_option_for_local_and_remote_transfer_modes` (function/method, line 43): Regression assertion: sync accepts option for local and remote transfer modes. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CleanupSupersededCacheModeTests` to use its existing endpoint, state or callback context.

- `CleanupSupersededCacheModeTests.test_sync_accepts_option_for_local_and_remote_transfer_modes.fake_sync` (function/method, line 61): Test support: fake sync; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CleanupSupersededCacheModeTests.test_sync_accepts_option_for_local_and_remote_transfer_modes` to use its existing endpoint, state or callback context.

- `CleanupSupersededCacheModeTests.test_prune_after_transfer_builds_correct_local_or_ssh_cache_runner` (function/method, line 78): Regression assertion: prune after transfer builds correct local or ssh cache runner. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CleanupSupersededCacheModeTests` to use its existing endpoint, state or callback context.

- `CleanupSupersededCacheModeTests.test_prune_after_transfer_builds_correct_local_or_ssh_cache_runner.fake_delete` (function/method, line 92): Test support: fake delete; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CleanupSupersededCacheModeTests.test_prune_after_transfer_builds_correct_local_or_ssh_cache_runner` to use its existing endpoint, state or callback context.

- `CleanupSupersededCacheModeTests.test_destroy_leftovers_accepts_option_for_all_targets_in_both_modes` (function/method, line 109): Regression assertion: destroy leftovers accepts option for all targets in both modes. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CleanupSupersededCacheModeTests` to use its existing endpoint, state or callback context.

- `CleanupSupersededCacheModeTests.test_destroy_leftovers_accepts_option_for_all_targets_in_both_modes.fake_destroy` (function/method, line 135): Test support: fake destroy; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CleanupSupersededCacheModeTests.test_destroy_leftovers_accepts_option_for_all_targets_in_both_modes` to use its existing endpoint, state or callback context.

- `CleanupSupersededCacheModeTests.test_accidental_rename_is_not_part_of_current_config_schema` (function/method, line 160): Regression assertion: accidental rename is not part of current config schema. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CleanupSupersededCacheModeTests` to use its existing endpoint, state or callback context.

- `CleanupSupersededCacheModeTests.test_disabled_option_skips_cache_runner_in_both_modes` (function/method, line 172): Regression assertion: disabled option skips cache runner in both modes. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CleanupSupersededCacheModeTests` to use its existing endpoint, state or callback context.

- `CleanupSupersededCacheModeTests.test_disabled_option_skips_cache_runner_in_both_modes.fake_delete` (function/method, line 185): Test support: fake delete; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CleanupSupersededCacheModeTests.test_disabled_option_skips_cache_runner_in_both_modes` to use its existing endpoint, state or callback context.

## `tests/test_cli_help_contract.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `_subparsers` (function/method, line 18): Test support: subparsers; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `CliHelpContractTests` (class, line 26): Groups CliHelpContract regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `CliHelpContractTests.test_top_level_help_is_self_contained_and_shows_version` (function/method, line 27): Regression assertion: top level help is self contained and shows version. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CliHelpContractTests` to use its existing endpoint, state or callback context.

- `CliHelpContractTests.test_every_public_option_has_meaningful_help_and_is_rendered` (function/method, line 38): Regression assertion: every public option has meaningful help and is rendered. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CliHelpContractTests` to use its existing endpoint, state or callback context.

- `CliHelpContractTests.test_every_subcommand_help_shows_version_relationships_or_examples` (function/method, line 56): Regression assertion: every subcommand help shows version relationships or examples. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CliHelpContractTests` to use its existing endpoint, state or callback context.

- `CliHelpContractTests.test_version_works_top_level_and_after_every_subcommand` (function/method, line 69): Regression assertion: version works top level and after every subcommand. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CliHelpContractTests` to use its existing endpoint, state or callback context.

- `CliHelpContractTests.test_help_action_exits_successfully_before_required_command_flags` (function/method, line 86): Regression assertion: help action exits successfully before required command flags. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CliHelpContractTests` to use its existing endpoint, state or callback context.

## `tests/test_config_attribute_surface.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `ConfigAttributeSurfaceTests` (class, line 10): Groups ConfigAttributeSurface regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `ConfigAttributeSurfaceTests.test_runtime_config_section_attributes_exist` (function/method, line 11): Catch stale config attributes left behind by refactors. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ConfigAttributeSurfaceTests` to use its existing endpoint, state or callback context.

## `tests/test_config_profiles.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `ConfigProfileTests` (class, line 42): Groups ConfigProfile regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `ConfigProfileTests._write_profile` (function/method, line 43): Test support: write profile; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ConfigProfileTests` to use its existing endpoint, state or callback context.

- `ConfigProfileTests.test_all_profiles_are_packaged_resources` (function/method, line 55): Regression assertion: all profiles are packaged resources. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ConfigProfileTests` to use its existing endpoint, state or callback context.

- `ConfigProfileTests.test_init_config_sync_profile_matches_packaged_template` (function/method, line 63): Regression assertion: init config sync profile matches packaged template. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ConfigProfileTests` to use its existing endpoint, state or callback context.

- `ConfigProfileTests.test_init_config_restore_pull_profile_matches_packaged_template` (function/method, line 69): Regression assertion: init config restore pull profile matches packaged template. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ConfigProfileTests` to use its existing endpoint, state or callback context.

- `ConfigProfileTests.test_init_config_remote_roundtrip_profile_matches_packaged_template` (function/method, line 76): Regression assertion: init config remote roundtrip profile matches packaged template. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ConfigProfileTests` to use its existing endpoint, state or callback context.

- `ConfigProfileTests.test_remote_roundtrip_profile_uses_same_ssh_host_for_sync_and_push_restore` (function/method, line 82): Regression assertion: remote roundtrip profile uses same ssh host for sync and push restore. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ConfigProfileTests` to use its existing endpoint, state or callback context.

- `ConfigProfileTests.test_restore_pull_profile_loads_remote_backup_ssh_settings` (function/method, line 88): Regression assertion: restore pull profile loads remote backup ssh settings. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ConfigProfileTests` to use its existing endpoint, state or callback context.

- `ConfigProfileTests.test_sync_profile_keeps_local_backup_transport_default` (function/method, line 105): Regression assertion: sync profile keeps local backup transport default. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ConfigProfileTests` to use its existing endpoint, state or callback context.

- `ConfigProfileTests.test_every_current_option_is_documented_in_all_profiles` (function/method, line 109): Regression assertion: every current option is documented in all profiles. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ConfigProfileTests` to use its existing endpoint, state or callback context.

- `ConfigProfileTests.test_ssh_password_and_connection_examples_are_commented` (function/method, line 146): Regression assertion: ssh password and connection examples are commented. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ConfigProfileTests` to use its existing endpoint, state or callback context.

## `tests/test_current_surface.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `CurrentPublicSurfaceTests` (class, line 32): Groups CurrentPublicSurface regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `CurrentPublicSurfaceTests.test_cli_contains_only_current_commands` (function/method, line 33): Regression assertion: cli contains only current commands. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CurrentPublicSurfaceTests` to use its existing endpoint, state or callback context.

- `CurrentPublicSurfaceTests.test_runtime_package_contains_only_current_modules` (function/method, line 41): Regression assertion: runtime package contains only current modules. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CurrentPublicSurfaceTests` to use its existing endpoint, state or callback context.

- `CurrentPublicSurfaceTests.test_state_schema_contains_only_current_fields` (function/method, line 46): Regression assertion: state schema contains only current fields. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CurrentPublicSurfaceTests` to use its existing endpoint, state or callback context.

- `CurrentPublicSurfaceTests.test_local_config_does_not_construct_ssh_settings` (function/method, line 50): Regression assertion: local config does not construct ssh settings. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CurrentPublicSurfaceTests` to use its existing endpoint, state or callback context.

- `CurrentPublicSurfaceTests.test_unknown_config_key_is_rejected` (function/method, line 59): Regression assertion: unknown config key is rejected. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CurrentPublicSurfaceTests` to use its existing endpoint, state or callback context.

## `tests/test_destination_inventory_regression.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `DestinationInventoryRegressionTests` (class, line 21): Groups DestinationInventoryRegression regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `DestinationInventoryRegressionTests.make_config` (function/method, line 22): Test support: make config; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationInventoryRegressionTests` to use its existing endpoint, state or callback context.

- `DestinationInventoryRegressionTests.test_mounted_destination_list_path_maps_from_snapshots_root` (function/method, line 30): Regression assertion: mounted destination list path maps from snapshots root. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationInventoryRegressionTests` to use its existing endpoint, state or callback context.

- `DestinationInventoryRegressionTests.test_sync_builds_destination_index_from_snapshots_subvolume` (function/method, line 44): Regression assertion: sync builds destination index from snapshots subvolume. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationInventoryRegressionTests` to use its existing endpoint, state or callback context.

- `DestinationInventoryRegressionTests.test_sync_builds_destination_index_from_snapshots_subvolume.StopAfterIndex` (class, line 45): Groups StopAfterIndex regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `DestinationInventoryRegressionTests.test_sync_builds_destination_index_from_snapshots_subvolume.LocalSource` (class, line 48): Groups LocalSource regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `DestinationInventoryRegressionTests.test_sync_builds_destination_index_from_snapshots_subvolume.stop_index` (function/method, line 56): Test support: stop index; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationInventoryRegressionTests.test_sync_builds_destination_index_from_snapshots_subvolume` to use its existing endpoint, state or callback context.

- `DestinationInventoryRegressionTests.test_bulk_index_miss_is_exact_probed_before_layout_rejection` (function/method, line 71): Regression assertion: bulk index miss is exact probed before layout rejection. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationInventoryRegressionTests` to use its existing endpoint, state or callback context.

- `DestinationInventoryRegressionTests.test_exact_probe_still_refuses_real_ordinary_date_directory` (function/method, line 84): Regression assertion: exact probe still refuses real ordinary date directory. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationInventoryRegressionTests` to use its existing endpoint, state or callback context.

- `DestinationInventoryRegressionTests.test_destination_snapshots_never_falls_back_to_mkdir` (function/method, line 95): Regression assertion: destination snapshots never falls back to mkdir. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationInventoryRegressionTests` to use its existing endpoint, state or callback context.

- `DestinationInventoryRegressionTests.test_btrfs_create_operation_uses_subvolume_create` (function/method, line 123): Regression assertion: btrfs create operation uses subvolume create. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationInventoryRegressionTests` to use its existing endpoint, state or callback context.

- `DestinationInventoryRegressionTests.test_btrfs_create_operation_uses_subvolume_create.fake_run` (function/method, line 126): Test support: fake run; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationInventoryRegressionTests.test_btrfs_create_operation_uses_subvolume_create` to use its existing endpoint, state or callback context.

## `tests/test_destroy_both_payload_match.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `DestroyBothPayloadMatchTests` (class, line 18): Groups DestroyBothPayloadMatch regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `DestroyBothPayloadMatchTests._config` (function/method, line 19): Test support: config; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestroyBothPayloadMatchTests` to use its existing endpoint, state or callback context.

- `DestroyBothPayloadMatchTests._successful_tree` (function/method, line 36): Test support: successful tree; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestroyBothPayloadMatchTests` to use its existing endpoint, state or callback context.

- `DestroyBothPayloadMatchTests.test_delete_both_completes_payload_comparison_for_local_and_ssh_sources` (function/method, line 46): Regression assertion: delete both completes payload comparison for local and ssh sources. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestroyBothPayloadMatchTests` to use its existing endpoint, state or callback context.

- `DestroyBothPayloadMatchTests.test_delete_both_completes_payload_comparison_for_local_and_ssh_sources.fake_delete` (function/method, line 68): Test support: fake delete; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestroyBothPayloadMatchTests.test_delete_both_completes_payload_comparison_for_local_and_ssh_sources` to use its existing endpoint, state or callback context.

- `DestroyBothPayloadMatchTests.test_every_destroy_source_config_attribute_exists` (function/method, line 99): Regression assertion: every destroy source config attribute exists. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestroyBothPayloadMatchTests` to use its existing endpoint, state or callback context.

## `tests/test_destroy_post_verification.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `ops` (function/method, line 19): Test support: ops; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `SharedTreePostVerificationTests` (class, line 23): Groups SharedTreePostVerification regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `SharedTreePostVerificationTests.test_zero_confirmed_deletions_and_existing_root_is_incomplete` (function/method, line 24): Regression assertion: zero confirmed deletions and existing root is incomplete. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SharedTreePostVerificationTests` to use its existing endpoint, state or callback context.

- `SharedTreePostVerificationTests.test_all_confirmed_and_absent_root_is_complete` (function/method, line 40): Regression assertion: all confirmed and absent root is complete. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SharedTreePostVerificationTests` to use its existing endpoint, state or callback context.

- `SharedTreePostVerificationTests.test_partial_confirmations_remain_incomplete_even_if_root_is_absent` (function/method, line 53): Regression assertion: partial confirmations remain incomplete even if root is absent. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SharedTreePostVerificationTests` to use its existing endpoint, state or callback context.

- `SharedTreePostVerificationTests.test_failed_final_existence_check_is_incomplete` (function/method, line 66): Regression assertion: failed final existence check is incomplete. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SharedTreePostVerificationTests` to use its existing endpoint, state or callback context.

- `DestroySummaryVerificationTests` (class, line 79): Groups DestroySummaryVerification regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `DestroySummaryVerificationTests.test_dry_run_blocking_error_is_reported_incomplete` (function/method, line 80): Regression assertion: dry run blocking error is reported incomplete. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestroySummaryVerificationTests` to use its existing endpoint, state or callback context.

- `DestroySummaryVerificationTests.test_unverified_tree_is_counted_incomplete` (function/method, line 110): Regression assertion: unverified tree is counted incomplete. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestroySummaryVerificationTests` to use its existing endpoint, state or callback context.

## `tests/test_incremental_parent_recovery.py`

**Role:** Regression tests. Regression scenarios for snapshot churn, live UUID proof and retention.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `IncrementalParentRecoveryTests` (class, line 18): Groups IncrementalParentRecovery regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `IncrementalParentRecoveryTests.setUp` (function/method, line 19): Build isolated inventories so tests never run Btrfs, sudo or SSH. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `IncrementalParentRecoveryTests` to use its existing endpoint, state or callback context.

- `IncrementalParentRecoveryTests.add_pair` (function/method, line 33): Represent an immutable send-cache and its completed received copy. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `IncrementalParentRecoveryTests` to use its existing endpoint, state or callback context.

- `IncrementalParentRecoveryTests.select_parent` (function/method, line 54): Choose a parent using only the fake filesystem metadata. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `IncrementalParentRecoveryTests` to use its existing endpoint, state or callback context.

- `IncrementalParentRecoveryTests.test_newest_cache_match_wins_when_original_hourly_is_gone` (function/method, line 67): Regression assertion: newest cache match wins when original hourly is gone. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `IncrementalParentRecoveryTests` to use its existing endpoint, state or callback context.

- `IncrementalParentRecoveryTests.test_newer_filesystem_match_wins_over_older_state_parent` (function/method, line 72): Regression assertion: newer filesystem match wins over older state parent. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `IncrementalParentRecoveryTests` to use its existing endpoint, state or callback context.

- `IncrementalParentRecoveryTests.test_missing_newer_destination_falls_back_to_daily` (function/method, line 78): Regression assertion: missing newer destination falls back to daily. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `IncrementalParentRecoveryTests` to use its existing endpoint, state or callback context.

- `IncrementalParentRecoveryTests.test_stale_state_uuid_cannot_override_actual_destination` (function/method, line 85): Regression assertion: stale state uuid cannot override actual destination. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `IncrementalParentRecoveryTests` to use its existing endpoint, state or callback context.

- `IncrementalParentRecoveryTests.test_unknown_source_readonly_is_not_a_verified_parent` (function/method, line 96): Regression assertion: unknown source readonly is not a verified parent. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `IncrementalParentRecoveryTests` to use its existing endpoint, state or callback context.

- `IncrementalParentRecoveryTests.test_writable_destination_is_not_a_verified_parent` (function/method, line 102): Regression assertion: writable destination is not a verified parent. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `IncrementalParentRecoveryTests` to use its existing endpoint, state or callback context.

- `IncrementalParentRecoveryTests.test_state_adoption_rejects_unproven_cache_or_receiver` (function/method, line 108): Regression assertion: state adoption rejects unproven cache or receiver. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `IncrementalParentRecoveryTests` to use its existing endpoint, state or callback context.

- `IncrementalParentRecoveryTests.test_floor_requires_all_configured_payloads` (function/method, line 122): Regression assertion: floor requires all configured payloads. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `IncrementalParentRecoveryTests` to use its existing endpoint, state or callback context.

- `IncrementalParentRecoveryTests.test_floor_finds_relocated_cache_by_uuid_after_original_disappears` (function/method, line 132): Regression assertion: floor finds relocated cache by uuid after original disappears. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `IncrementalParentRecoveryTests` to use its existing endpoint, state or callback context.

- `IncrementalParentRecoveryTests.test_tag_changes_do_not_change_verified_parent` (function/method, line 144): Regression assertion: tag changes do not change verified parent. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `IncrementalParentRecoveryTests` to use its existing endpoint, state or callback context.

- `IncrementalParentRecoveryTests.test_hourly_without_original_or_cache_falls_back_to_daily` (function/method, line 149): Regression assertion: hourly without original or cache falls back to daily. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `IncrementalParentRecoveryTests` to use its existing endpoint, state or callback context.

- `IncrementalParentRecoveryTests.test_existing_destination_cannot_silently_full_send_without_parent` (function/method, line 155): Regression assertion: existing destination cannot silently full send without parent. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `IncrementalParentRecoveryTests` to use its existing endpoint, state or callback context.

- `IncrementalParentRecoveryTests.test_full_seed_is_allowed_only_with_explicit_empty_start_permission` (function/method, line 161): Regression assertion: full seed is allowed only with explicit empty start permission. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `IncrementalParentRecoveryTests` to use its existing endpoint, state or callback context.

- `IncrementalParentRecoveryTests.test_verified_daily_survives_retention_when_newest_hourly_is_not_shared` (function/method, line 168): Regression assertion: verified daily survives retention when newest hourly is not shared. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `IncrementalParentRecoveryTests` to use its existing endpoint, state or callback context.

- `IncrementalParentRecoveryTests.test_prune_anchor_uses_the_same_live_floor_proof` (function/method, line 178): Regression assertion: prune anchor uses the same live floor proof. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `IncrementalParentRecoveryTests` to use its existing endpoint, state or callback context.

- `IncrementalParentRecoveryTests.test_prune_without_proven_anchor_stops_before_any_delete` (function/method, line 191): Regression assertion: prune without proven anchor stops before any delete. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `IncrementalParentRecoveryTests` to use its existing endpoint, state or callback context.

- `IncrementalParentRecoveryTests.test_retention_selection_avoids_sending_unneeded_hourlies` (function/method, line 204): Regression assertion: retention selection avoids sending unneeded hourlies. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `IncrementalParentRecoveryTests` to use its existing endpoint, state or callback context.

- `IncrementalParentRecoveryTests.test_completed_outside_retention_is_kept_in_queue_for_metadata_refresh` (function/method, line 213): Regression assertion: completed outside retention is kept in queue for metadata refresh. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `IncrementalParentRecoveryTests` to use its existing endpoint, state or callback context.

## `tests/test_manual_snapshot_retention.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `_config` (function/method, line 25): Test support: config; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `_name` (function/method, line 65): Test support: name; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `_source_snapshot` (function/method, line 69): Test support: source snapshot; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `_synced_state_entry` (function/method, line 80): Test support: synced state entry; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `_state` (function/method, line 104): Test support: state; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `_destination_index` (function/method, line 111): Test support: destination index; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `ManualSnapshotRetentionTests` (class, line 119): Groups ManualSnapshotRetention regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `ManualSnapshotRetentionTests.test_app_created_source_retention_keeps_newest_ten` (function/method, line 120): Regression assertion: app created source retention keeps newest ten. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ManualSnapshotRetentionTests` to use its existing endpoint, state or callback context.

- `ManualSnapshotRetentionTests.test_destination_app_retention_keeps_the_same_newest_ten` (function/method, line 128): Regression assertion: destination app retention keeps the same newest ten. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ManualSnapshotRetentionTests` to use its existing endpoint, state or callback context.

- `ManualSnapshotRetentionTests.test_marker_without_o_tag_is_not_a_source_delete_candidate` (function/method, line 135): Regression assertion: marker without o tag is not a source delete candidate. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ManualSnapshotRetentionTests` to use its existing endpoint, state or callback context.

- `ManualSnapshotRetentionTests.test_cleanup_disabled_never_creates_source_delete_candidates` (function/method, line 143): Regression assertion: cleanup disabled never creates source delete candidates. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ManualSnapshotRetentionTests` to use its existing endpoint, state or callback context.

- `ManualSnapshotRetentionTests.test_normal_user_created_ondemand_is_never_source_app_candidate` (function/method, line 148): Regression assertion: normal user created ondemand is never source app candidate. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ManualSnapshotRetentionTests` to use its existing endpoint, state or callback context.

- `ManualSnapshotRetentionTests.test_tracked_source_delete_requires_complete_live_backup` (function/method, line 156): Regression assertion: tracked source delete requires complete live backup. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ManualSnapshotRetentionTests` to use its existing endpoint, state or callback context.

- `ManualSnapshotRetentionTests.test_legacy_01373_source_only_backlog_is_allowed_after_retained_window_is_proven` (function/method, line 168): Regression assertion: legacy 01373 source only backlog is allowed after retained window is proven. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ManualSnapshotRetentionTests` to use its existing endpoint, state or callback context.

- `ManualSnapshotRetentionTests.test_legacy_backlog_is_blocked_when_one_retained_backup_is_not_proven` (function/method, line 181): Regression assertion: legacy backlog is blocked when one retained backup is not proven. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ManualSnapshotRetentionTests` to use its existing endpoint, state or callback context.

- `ManualSnapshotRetentionTests.test_source_timeshift_delete_revalidates_current_o_tag_and_marker` (function/method, line 194): Regression assertion: source timeshift delete revalidates current o tag and marker. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ManualSnapshotRetentionTests` to use its existing endpoint, state or callback context.

- `ManualSnapshotRetentionTests.test_timeshift_delete_command_uses_timeshift_not_raw_btrfs_or_rm` (function/method, line 206): Regression assertion: timeshift delete command uses timeshift not raw btrfs or rm. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ManualSnapshotRetentionTests` to use its existing endpoint, state or callback context.

- `ManualSnapshotRetentionTests.test_timeshift_delete_verifies_snapshot_is_absent_after_delete` (function/method, line 215): Regression assertion: timeshift delete verifies snapshot is absent after delete. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ManualSnapshotRetentionTests` to use its existing endpoint, state or callback context.

- `ManualSnapshotRetentionTests.test_timeshift_delete_fails_if_snapshot_is_still_listed` (function/method, line 230): Regression assertion: timeshift delete fails if snapshot is still listed. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ManualSnapshotRetentionTests` to use its existing endpoint, state or callback context.

- `ManualSnapshotRetentionTests.test_failed_source_timeshift_delete_leaves_destination_untouched_for_retry` (function/method, line 246): Regression assertion: failed source timeshift delete leaves destination untouched for retry. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ManualSnapshotRetentionTests` to use its existing endpoint, state or callback context.

- `ManualSnapshotRetentionTests.test_successful_source_delete_allows_destination_cleanup` (function/method, line 271): Regression assertion: successful source delete allows destination cleanup. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ManualSnapshotRetentionTests` to use its existing endpoint, state or callback context.

- `ManualSnapshotRetentionTests.test_successful_source_delete_allows_destination_cleanup.source_ok` (function/method, line 280): Test support: source ok; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ManualSnapshotRetentionTests.test_successful_source_delete_allows_destination_cleanup` to use its existing endpoint, state or callback context.

- `ManualSnapshotRetentionTests.test_successful_source_delete_allows_destination_cleanup.destination_ok` (function/method, line 285): Test support: destination ok; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ManualSnapshotRetentionTests.test_successful_source_delete_allows_destination_cleanup` to use its existing endpoint, state or callback context.

- `ManualSnapshotRetentionTests.test_prune_action_order_preserves_backup_until_source_delete_is_confirmed` (function/method, line 306): Regression assertion: prune action order preserves backup until source delete is confirmed. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ManualSnapshotRetentionTests` to use its existing endpoint, state or callback context.

## `tests/test_pipeline_failure_diagnostics.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `PipelineFailureDiagnosticsTests` (class, line 18): Groups PipelineFailureDiagnostics regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `PipelineFailureDiagnosticsTests.test_enospc_from_receive_is_terminal_destination_failure` (function/method, line 19): Regression assertion: enospc from receive is terminal destination failure. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `PipelineFailureDiagnosticsTests` to use its existing endpoint, state or callback context.

- `PipelineFailureDiagnosticsTests.test_stream_pipeline_preserves_receive_stage_failure_details` (function/method, line 37): Regression assertion: stream pipeline preserves receive stage failure details. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `PipelineFailureDiagnosticsTests` to use its existing endpoint, state or callback context.

- `PipelineFailureDiagnosticsTests.test_broken_pipe_without_receive_storage_signature_is_not_terminal_destination_failure` (function/method, line 54): Regression assertion: broken pipe without receive storage signature is not terminal destination failure. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `PipelineFailureDiagnosticsTests` to use its existing endpoint, state or callback context.

- `PipelineFailureDiagnosticsTests.test_exact_probe_repairs_bulk_cache_omission_before_change_detection` (function/method, line 67): Regression assertion: exact probe repairs bulk cache omission before change detection. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `PipelineFailureDiagnosticsTests` to use its existing endpoint, state or callback context.

- `PipelineFailureDiagnosticsTests.test_exact_probe_repairs_bulk_cache_omission_before_change_detection.fake_refresh` (function/method, line 79): Test support: fake refresh; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `PipelineFailureDiagnosticsTests.test_exact_probe_repairs_bulk_cache_omission_before_change_detection` to use its existing endpoint, state or callback context.

- `PipelineFailureDiagnosticsTests.test_exact_probe_confirmed_absence_remains_a_source_change` (function/method, line 107): Regression assertion: exact probe confirmed absence remains a source change. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `PipelineFailureDiagnosticsTests` to use its existing endpoint, state or callback context.

## `tests/test_pre_restore_snapshot.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `FakeTargetSource` (class, line 20): Groups FakeTargetSource regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `FakeTargetSource.__init__` (function/method, line 21): Test support: init; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `FakeTargetSource` to use its existing endpoint, state or callback context.

- `FakeTargetSource.command` (function/method, line 28): Test support: command; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `FakeTargetSource` to use its existing endpoint, state or callback context.

- `FakeTargetSource.run` (function/method, line 31): Test support: run; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `FakeTargetSource` to use its existing endpoint, state or callback context.

- `FakeTargetSource.environment` (function/method, line 45): Test support: environment; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `FakeTargetSource` to use its existing endpoint, state or callback context.

- `FakeOps` (class, line 49): Groups FakeOps regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `FakeOps.__init__` (function/method, line 50): Test support: init; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `FakeOps` to use its existing endpoint, state or callback context.

- `FakeOps.meta` (function/method, line 53): Test support: meta; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `FakeOps` to use its existing endpoint, state or callback context.

- `PreRestoreSnapshotTests` (class, line 58): Groups PreRestoreSnapshot regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `PreRestoreSnapshotTests.make_config` (function/method, line 59): Test support: make config; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `PreRestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `PreRestoreSnapshotTests.test_shared_helper_creates_and_verifies_snapshot_on_local_and_ssh_targets` (function/method, line 72): Regression assertion: shared helper creates and verifies snapshot on local and ssh targets. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `PreRestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `PreRestoreSnapshotTests.test_failed_safety_snapshot_aborts_before_any_restore_stream` (function/method, line 95): Regression assertion: failed safety snapshot aborts before any restore stream. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `PreRestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `PreRestoreSnapshotTests.test_pull_restore_uses_local_timeshift_target_not_remote_backup_for_safety_snapshot` (function/method, line 106): Regression assertion: pull restore uses local timeshift target not remote backup for safety snapshot. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `PreRestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `PreRestoreSnapshotTests.test_pull_restore_uses_local_timeshift_target_not_remote_backup_for_safety_snapshot.safety` (function/method, line 158): Test support: safety; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `PreRestoreSnapshotTests.test_pull_restore_uses_local_timeshift_target_not_remote_backup_for_safety_snapshot` to use its existing endpoint, state or callback context.

- `PreRestoreSnapshotTests.test_pull_restore_uses_local_timeshift_target_not_remote_backup_for_safety_snapshot.stop_stream` (function/method, line 162): Test support: stop stream; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `PreRestoreSnapshotTests.test_pull_restore_uses_local_timeshift_target_not_remote_backup_for_safety_snapshot` to use its existing endpoint, state or callback context.

- `PreRestoreSnapshotTests.test_dry_run_reports_safety_snapshot_without_creating_it` (function/method, line 195): Regression assertion: dry run reports safety snapshot without creating it. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `PreRestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `PreRestoreSnapshotTests.test_restore_cli_exposes_pre_restore_snapshot_flag` (function/method, line 259): Regression assertion: restore cli exposes pre restore snapshot flag. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `PreRestoreSnapshotTests` to use its existing endpoint, state or callback context.

## `tests/test_profiles_and_packaging.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `ConfigProfileTests` (class, line 31): Groups ConfigProfile regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `ConfigProfileTests.test_all_packaged_profiles_exist_and_load` (function/method, line 32): Regression assertion: all packaged profiles exist and load. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ConfigProfileTests` to use its existing endpoint, state or callback context.

- `ConfigProfileTests.test_every_profile_mentions_every_current_config_option` (function/method, line 57): Regression assertion: every profile mentions every current config option. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ConfigProfileTests` to use its existing endpoint, state or callback context.

- `ConfigProfileTests.test_init_config_generates_every_profile` (function/method, line 77): Regression assertion: init config generates every profile. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ConfigProfileTests` to use its existing endpoint, state or callback context.

- `ConfigProfileTests.test_init_config_help_describes_every_profile` (function/method, line 107): Regression assertion: init config help describes every profile. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ConfigProfileTests` to use its existing endpoint, state or callback context.

- `ConfigProfileTests.test_pyproject_package_data_lists_every_profile` (function/method, line 121): Regression assertion: pyproject package data lists every profile. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ConfigProfileTests` to use its existing endpoint, state or callback context.

- `ConfigProfileTests.test_pyinstaller_bundles_the_complete_data_directory` (function/method, line 130): Regression assertion: pyinstaller bundles the complete data directory. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ConfigProfileTests` to use its existing endpoint, state or callback context.

- `ConfigProfileTests.test_profile_headers_match_package_version` (function/method, line 151): Regression assertion: profile headers match package version. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ConfigProfileTests` to use its existing endpoint, state or callback context.

## `tests/test_recursive_bulk_deletion.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `RecursiveBulkListTests` (class, line 21): Groups RecursiveBulkList regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `RecursiveBulkListTests.test_cache_tree_includes_date_payload_children_from_one_all_filesystem_list` (function/method, line 22): Regression assertion: cache tree includes date payload children from one all filesystem list. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RecursiveBulkListTests` to use its existing endpoint, state or callback context.

- `RecursiveBulkListTests.test_cache_tree_includes_date_payload_children_from_one_all_filesystem_list.run_argv` (function/method, line 36): Test support: run argv; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RecursiveBulkListTests.test_cache_tree_includes_date_payload_children_from_one_all_filesystem_list` to use its existing endpoint, state or callback context.

- `RecursiveBulkListTests.test_destination_tree_includes_payload_children_before_all_parent_containers` (function/method, line 59): Regression assertion: destination tree includes payload children before all parent containers. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RecursiveBulkListTests` to use its existing endpoint, state or callback context.

- `RecursiveBulkListTests.test_ssh_source_uses_same_single_graph_command` (function/method, line 84): Regression assertion: ssh source uses same single graph command. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RecursiveBulkListTests` to use its existing endpoint, state or callback context.

- `RecursiveBulkListTests.test_ssh_source_uses_same_single_graph_command.run` (function/method, line 94): Test support: run; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RecursiveBulkListTests.test_ssh_source_uses_same_single_graph_command` to use its existing endpoint, state or callback context.

- `RecursiveBulkListTests.test_subvolume_show_parses_numeric_containment_ids` (function/method, line 112): Regression assertion: subvolume show parses numeric containment ids. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RecursiveBulkListTests` to use its existing endpoint, state or callback context.

- `RecursiveBulkListTests.test_shared_delete_engine_passes_complete_deepest_first_plan_to_one_batch` (function/method, line 122): Regression assertion: shared delete engine passes complete deepest first plan to one batch. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RecursiveBulkListTests` to use its existing endpoint, state or callback context.

## `tests/test_release_hygiene.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `ReleaseHygieneTests` (class, line 31): Groups ReleaseHygiene regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `ReleaseHygieneTests.test_preserved_helper_is_separate_from_runtime` (function/method, line 32): Regression assertion: preserved helper is separate from runtime. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ReleaseHygieneTests` to use its existing endpoint, state or callback context.

- `ReleaseHygieneTests.test_runtime_success_logs_are_ignored_and_not_shipped` (function/method, line 37): Regression assertion: runtime success logs are ignored and not shipped. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ReleaseHygieneTests` to use its existing endpoint, state or callback context.

- `ReleaseHygieneTests.test_version_metadata_is_consistent` (function/method, line 53): Regression assertion: version metadata is consistent. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ReleaseHygieneTests` to use its existing endpoint, state or callback context.

- `ReleaseHygieneTests.test_readme_documents_every_cli_command` (function/method, line 59): Regression assertion: readme documents every cli command. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ReleaseHygieneTests` to use its existing endpoint, state or callback context.

- `ReleaseHygieneTests.test_parser_command_set_matches_documented_command_set` (function/method, line 65): Regression assertion: parser command set matches documented command set. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ReleaseHygieneTests` to use its existing endpoint, state or callback context.

- `ReleaseHygieneTests.test_readme_mentions_every_public_parser_option` (function/method, line 75): Regression assertion: readme mentions every public parser option. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ReleaseHygieneTests` to use its existing endpoint, state or callback context.

- `ReleaseHygieneTests.test_code_map_names_every_runtime_and_build_symbol` (function/method, line 91): Regression assertion: code map names every runtime and build symbol. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ReleaseHygieneTests` to use its existing endpoint, state or callback context.

- `ReleaseHygieneTests.test_no_python_cache_or_build_cache_is_present_in_source_tree` (function/method, line 107): Regression assertion: no python cache or build cache is present in source tree. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ReleaseHygieneTests` to use its existing endpoint, state or callback context.

## `tests/test_remote_file_lock.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `FakeRunner` (class, line 14): Groups FakeRunner regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `FakeRunner.__init__` (function/method, line 17): Test support: init; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `FakeRunner` to use its existing endpoint, state or callback context.

- `FakeRunner.command` (function/method, line 20): Test support: command; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `FakeRunner` to use its existing endpoint, state or callback context.

- `FakeRunner.environment` (function/method, line 24): Test support: environment; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `FakeRunner` to use its existing endpoint, state or callback context.

- `FakeStdin` (class, line 28): Groups FakeStdin regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `FakeProcess` (class, line 32): Groups FakeProcess regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `FakeProcess.__init__` (function/method, line 33): Test support: init; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `FakeProcess` to use its existing endpoint, state or callback context.

- `FakeProcess.wait` (function/method, line 42): Test support: wait; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `FakeProcess` to use its existing endpoint, state or callback context.

- `FakeProcess.terminate` (function/method, line 46): Test support: terminate; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `FakeProcess` to use its existing endpoint, state or callback context.

- `FakeProcess.kill` (function/method, line 49): Test support: kill; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `FakeProcess` to use its existing endpoint, state or callback context.

- `RemoteFileLockTests` (class, line 54): Groups RemoteFileLock regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `RemoteFileLockTests.test_holds_remote_flock_until_context_exit` (function/method, line 55): Regression assertion: holds remote flock until context exit. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteFileLockTests` to use its existing endpoint, state or callback context.

- `RemoteFileLockTests.test_busy_remote_lock_raises_blocking_error` (function/method, line 74): Regression assertion: busy remote lock raises blocking error. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteFileLockTests` to use its existing endpoint, state or callback context.

- `RemoteFileLockTests.test_timeout_terminates_remote_lock_process` (function/method, line 85): Regression assertion: timeout terminates remote lock process. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteFileLockTests` to use its existing endpoint, state or callback context.

- `RemoteFileLockTests.test_requires_ssh_runner` (function/method, line 97): Regression assertion: requires ssh runner. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteFileLockTests` to use its existing endpoint, state or callback context.

## `tests/test_repository_reconciliation.py`

**Role:** Regression tests. State repair and bounded cache cleanup with actual ordinary files and simulated Btrfs.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `RepositoryReconciliationTests` (class, line 27): Prevent state gaps or cache leaks without ever deleting real Btrfs snapshots. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `RepositoryReconciliationTests.setUp` (function/method, line 30): Create readable ordinary fixtures and isolated immutable identity indexes. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.add_cache` (function/method, line 54): Model a native app-cache container and two readonly snapshots of known originals. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.add_pair` (function/method, line 66): Build a complete matching received pair with valid current state when requested. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.recover` (function/method, line 93): Run real whole-date recovery against fixtures while observing state writes. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.cleanup` (function/method, line 102): Mock only storage metadata/deletion while exercising actual ordinary filesystem safety checks. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.cleanup.meta` (function/method, line 105): Return current metadata without invoking sudo or Btrfs. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests.cleanup` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.add_window` (function/method, line 118): Retain two proven bounds around a missing cache-only middle date. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_populated_state_recovers_missing_complete_pair_without_overwrite` (function/method, line 124): Regression assertion: populated state recovers missing complete pair without overwrite. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_empty_state_recovers_expired_original_from_cache_and_target_json` (function/method, line 135): Regression assertion: empty state recovers expired original from cache and target json. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_partial_or_mismatched_pairs_never_create_partial_state` (function/method, line 144): Regression assertion: partial or mismatched pairs never create partial state. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_unknown_retention_metadata_preserves_untracked_expired_pair` (function/method, line 158): Regression assertion: unknown retention metadata preserves untracked expired pair. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_changed_original_cannot_be_mislabelled_as_already_backed_up` (function/method, line 164): Regression assertion: changed original cannot be mislabelled as already backed up. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_ordinary_or_symlinked_destination_container_is_not_adopted` (function/method, line 170): Regression assertion: ordinary or symlinked destination container is not adopted. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_relocated_cache_identity_is_not_relabelled_as_another_date` (function/method, line 183): Regression assertion: relocated cache identity is not relabelled as another date. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_dry_recovery_uses_memory_without_writing_state` (function/method, line 191): Regression assertion: dry recovery uses memory without writing state. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_existing_partial_state_is_preserved_for_normal_recovery` (function/method, line 197): Regression assertion: existing partial state is preserved for normal recovery. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_incomplete_index_blocks_state_recovery` (function/method, line 204): Regression assertion: incomplete index blocks state recovery. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_redundant_middle_cache_is_deleted_without_destination_or_state_deletion` (function/method, line 211): Regression assertion: redundant middle cache is deleted without destination or state deletion. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_user_29_cache_17_destination_case_retires_only_12_middle_leftovers` (function/method, line 221): Regression assertion: user 29 cache 17 destination case retires only 12 middle leftovers. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_newer_cache_remains_and_explicitly_protected_older_cache_is_preserved` (function/method, line 232): Regression assertion: newer cache remains and explicitly protected older cache is preserved. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_existing_destination_or_unknown_absence_blocks_cleanup` (function/method, line 241): Regression assertion: existing destination or unknown absence blocks cleanup. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_receiver_appearing_during_checks_is_preserved` (function/method, line 251): Regression assertion: receiver appearing during checks is preserved. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_owned_native_date_contents_do_not_require_ordinary_listing` (function/method, line 257): Regression assertion: owned native date contents do not require ordinary listing. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_changed_writable_or_foreign_cache_uuid_blocks_cleanup` (function/method, line 273): Regression assertion: changed writable or foreign cache uuid blocks cleanup. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_changed_writable_or_foreign_cache_uuid_blocks_cleanup.live` (function/method, line 276): Alter one live payload to exercise identity and ownership refusal. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests.test_changed_writable_or_foreign_cache_uuid_blocks_cleanup` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_incomplete_transfer_parent_is_protected` (function/method, line 286): Regression assertion: incomplete transfer parent is protected. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_disabled_option_master_switch_and_dry_run_never_delete` (function/method, line 295): Regression assertion: disabled option master switch and dry run never delete. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_real_cleanup_requires_existing_yes_delete_consent` (function/method, line 307): Regression assertion: real cleanup requires existing yes delete consent. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_failed_deletion_stays_pending_for_next_run` (function/method, line 312): Regression assertion: failed deletion stays pending for next run. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_prune_reconciles_then_cleans_even_with_zero_paired_candidates` (function/method, line 318): Regression assertion: prune reconciles then cleans even with zero paired candidates. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_config_option_defaults_true_can_disable_and_rejects_non_boolean` (function/method, line 331): Regression assertion: config option defaults true can disable and rejects non boolean. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_no_confirmed_state_window_preserves_all_cache` (function/method, line 342): Regression assertion: no confirmed state window preserves all cache. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_cache_payload_symlink_and_changed_container_are_preserved` (function/method, line 350): Regression assertion: cache payload symlink and changed container are preserved. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_cache_payload_symlink_and_changed_container_are_preserved.live` (function/method, line 360): Simulate replacement of a date container after the inventory was collected. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests.test_cache_payload_symlink_and_changed_container_are_preserved` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_partial_nested_inventory_stops_reconciliation_before_adoption` (function/method, line 368): Regression assertion: partial nested inventory stops reconciliation before adoption. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_wrong_timeshift_filesystem_stops_reconciliation_before_state_or_deletes` (function/method, line 376): Regression assertion: wrong timeshift filesystem stops reconciliation before state or deletes. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_summary_does_not_claim_full_success_when_extra_cache_is_blocked` (function/method, line 384): Regression assertion: summary does not claim full success when extra cache is blocked. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_real_redundant_cleanup_requires_current_successful_sync` (function/method, line 395): Regression assertion: real redundant cleanup requires current successful sync. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_proven_root_cleanup_does_not_run_ordinary_cache_checks` (function/method, line 402): Regression assertion: proven root cleanup does not run ordinary cache checks. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_date_style_readonly_snapshot_and_partial_cache_are_stale_candidates` (function/method, line 410): Regression assertion: date style readonly snapshot and partial cache are stale candidates. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_older_than_first_pair_is_removed_but_newer_is_preserved` (function/method, line 424): Regression assertion: older than first pair is removed but newer is preserved. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_root_state_uuid_mismatch_foreign_root_and_incomplete_state_preserve_cache` (function/method, line 433): Regression assertion: root state uuid mismatch foreign root and incomplete state preserve cache. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_writable_nested_cache_subvolume_blocks_only_its_date` (function/method, line 447): Regression assertion: writable nested cache subvolume blocks only its date. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `RepositoryReconciliationTests.test_36_cache_17_pairs_remove_19_stale_dates_without_ordinary_cache_access` (function/method, line 455): Regression assertion: 36 cache 17 pairs remove 19 stale dates without ordinary cache access. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RepositoryReconciliationTests` to use its existing endpoint, state or callback context.

- `NativeCacheTreeTests` (class, line 468): Exercise numeric deletion and privileged final proof with simulated Btrfs commands only. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `NativeCacheTreeTests._run` (function/method, line 471): Model a native root/date/payload ID graph; ordinary readers must never be called. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `NativeCacheTreeTests` to use its existing endpoint, state or callback context.

- `NativeCacheTreeTests._run.meta` (function/method, line 482): Return stable live native metadata, with optional replacement refusal. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `NativeCacheTreeTests._run` to use its existing endpoint, state or callback context.

- `NativeCacheTreeTests._run.run` (function/method, line 486): Only simulated native Btrfs list/delete commands are supported. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `NativeCacheTreeTests._run` to use its existing endpoint, state or callback context.

- `NativeCacheTreeTests.test_numeric_delete_proves_absence_without_any_ordinary_reader` (function/method, line 504): Regression assertion: numeric delete proves absence without any ordinary reader. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `NativeCacheTreeTests` to use its existing endpoint, state or callback context.

- `NativeCacheTreeTests.test_uuid_replacement_or_unexpected_subvolume_blocks_before_delete` (function/method, line 510): Regression assertion: uuid replacement or unexpected subvolume blocks before delete. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `NativeCacheTreeTests` to use its existing endpoint, state or callback context.

- `NativeCacheTreeTests.test_failed_delete_remaining_ids_and_unsupported_tool_never_claim_success` (function/method, line 516): Regression assertion: failed delete remaining ids and unsupported tool never claim success. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `NativeCacheTreeTests` to use its existing endpoint, state or callback context.

- `PostSyncCleanupOrderTests` (class, line 523): Keep real extra cleanup behind the successful sync return, including verified no-op runs. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `PostSyncCleanupOrderTests.test_successful_noop_sync_passes_gate_and_failed_sync_never_calls_prune` (function/method, line 526): Regression assertion: successful noop sync passes gate and failed sync never calls prune. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `PostSyncCleanupOrderTests` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests` (class, line 541): Exercise bounded receiver-only cleanup without mutating actual storage. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `DestinationReconciliationTests.setUp` (function/method, line 544): Reuse repository fixtures and give receiver roots/payloads exact native identities. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.add_receiver` (function/method, line 559): Add a dated native receiver tree whose sending cache has disappeared. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.cleanup` (function/method, line 573): Mock native storage while using real cleanup/ownership/range logic. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.cleanup.meta` (function/method, line 576): Return indexed identities or an explicitly simulated changed native path. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests.cleanup` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.cleanup.tree` (function/method, line 581): Return scoped containment below the selected native repository root. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests.cleanup` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.cleanup.index` (function/method, line 584): Return complete source/receiver views or a scheduled race/failure fixture. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests.cleanup` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.test_destination_only_middle_deleted_without_changing_state_or_cache` (function/method, line 594): Regression assertion: destination only middle deleted without changing state or cache. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.test_destination_upper_limit_includes_older_but_preserves_newer_bad_dates_and_names` (function/method, line 605): Regression assertion: destination upper limit includes older but preserves newer bad dates and names. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.test_source_counterpart_protected_even_if_missing_from_state` (function/method, line 614): Regression assertion: source counterpart protected even if missing from state. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.test_tracked_and_explicitly_protected_receiver_dates_preserved` (function/method, line 620): Regression assertion: tracked and explicitly protected receiver dates preserved. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.test_no_successful_sync_skip_and_dry_preview_no_delete` (function/method, line 631): Regression assertion: no successful sync skip and dry preview no delete. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.test_destination_option_independent_of_source_cleanup_switches` (function/method, line 640): Regression assertion: destination option independent of source cleanup switches. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.test_disabled_destination_option_does_not_call_storage` (function/method, line 647): Regression assertion: disabled destination option does not call storage. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.test_real_delete_requires_explicit_yes_delete` (function/method, line 654): Regression assertion: real delete requires explicit yes delete. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.test_incomplete_or_missing_cache_inventory_preserves_receivers` (function/method, line 658): Regression assertion: incomplete or missing cache inventory preserves receivers. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.test_missing_cache_configuration_preserves_receivers` (function/method, line 669): Regression assertion: missing cache configuration preserves receivers. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.test_writable_unknown_or_changed_payload_cannot_be_deleted` (function/method, line 675): Regression assertion: writable unknown or changed payload cannot be deleted. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.test_replaced_or_snapshot_destination_root_blocks_cleanup` (function/method, line 685): Regression assertion: replaced or snapshot destination root blocks cleanup. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.test_mismatched_state_pair_blocks_receiver_ownership` (function/method, line 691): Regression assertion: mismatched state pair blocks receiver ownership. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.test_cache_appearing_immediately_before_delete_blocks_receiver_removal` (function/method, line 697): Regression assertion: cache appearing immediately before delete blocks receiver removal. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.test_cache_appearing_immediately_before_delete_blocks_receiver_removal.race` (function/method, line 699): Create a source counterpart after the first complete absence check. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests.test_cache_appearing_immediately_before_delete_blocks_receiver_removal` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.test_cache_becoming_unreadable_before_delete_blocks_receiver_removal` (function/method, line 711): Regression assertion: cache becoming unreadable before delete blocks receiver removal. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.test_cache_becoming_unreadable_before_delete_blocks_receiver_removal.race` (function/method, line 713): Simulate an unavailable cache between checks without claiming absence. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests.test_cache_becoming_unreadable_before_delete_blocks_receiver_removal` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.test_bare_and_partial_readonly_receiver_dates_use_shared_tree_engine` (function/method, line 724): Regression assertion: bare and partial readonly receiver dates use shared tree engine. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.test_known_source_uuid_under_another_date_preserves_receiver` (function/method, line 733): Regression assertion: known source uuid under another date preserves receiver. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.test_deletion_not_confirmed_is_retry_without_state_loss` (function/method, line 740): Regression assertion: deletion not confirmed is retry without state loss. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.test_destination_boolean_default_disable_and_strict_validation` (function/method, line 748): Regression assertion: destination boolean default disable and strict validation. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.test_receiver_only_counters_do_not_inflate_paired_state_cleanup` (function/method, line 761): Regression assertion: receiver only counters do not inflate paired state cleanup. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.test_all_older_valid_dates_are_candidates_without_a_lower_limit` (function/method, line 775): Regression assertion: all older valid dates are candidates without a lower limit. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.test_older_receiver_preserved_when_ownership_uuid_pair_is_invalid` (function/method, line 785): Regression assertion: older receiver preserved when ownership uuid pair is invalid. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.test_older_excluded_or_writable_snapshots_remain_protected` (function/method, line 795): Regression assertion: older excluded or writable snapshots remain protected. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests` to use its existing endpoint, state or callback context.

- `DestinationReconciliationTests.test_dry_preview_includes_older_snapshots_but_never_newer_snapshots` (function/method, line 810): Regression assertion: dry preview includes older snapshots but never newer snapshots. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationReconciliationTests` to use its existing endpoint, state or callback context.

## `tests/test_restore_remote_backup.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `FakeRunner` (class, line 22): Groups FakeRunner regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `FakeRunner.__init__` (function/method, line 23): Test support: init; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `FakeRunner` to use its existing endpoint, state or callback context.

- `FakeRunner.command` (function/method, line 29): Test support: command; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `FakeRunner` to use its existing endpoint, state or callback context.

- `FakeRunner.run` (function/method, line 32): Test support: run; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `FakeRunner` to use its existing endpoint, state or callback context.

- `FakeRunner.environment` (function/method, line 40): Test support: environment; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `FakeRunner` to use its existing endpoint, state or callback context.

- `FakeEndpoint` (class, line 44): Groups FakeEndpoint regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `FakeEndpoint.__init__` (function/method, line 45): Test support: init; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `FakeEndpoint` to use its existing endpoint, state or callback context.

- `FakeEndpoint.run_shell` (function/method, line 51): Test support: run shell; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `FakeEndpoint` to use its existing endpoint, state or callback context.

- `FakeEndpoint.run_argv` (function/method, line 55): Test support: run argv; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `FakeEndpoint` to use its existing endpoint, state or callback context.

- `RemoteBackupRestoreTests` (class, line 60): Groups RemoteBackupRestore regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `RemoteBackupRestoreTests.make_config` (function/method, line 61): Test support: make config; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteBackupRestoreTests` to use its existing endpoint, state or callback context.

- `RemoteBackupRestoreTests.plan` (function/method, line 85): Test support: plan; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteBackupRestoreTests` to use its existing endpoint, state or callback context.

- `RemoteBackupRestoreTests.source_meta` (function/method, line 109): Test support: source meta; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteBackupRestoreTests` to use its existing endpoint, state or callback context.

- `RemoteBackupRestoreTests.test_remote_backup_streams_ssh_send_into_local_receive` (function/method, line 128): Regression assertion: remote backup streams ssh send into local receive. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteBackupRestoreTests` to use its existing endpoint, state or callback context.

- `RemoteBackupRestoreTests.test_remote_backup_streams_ssh_send_into_local_receive.capture` (function/method, line 142): Test support: capture; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteBackupRestoreTests.test_remote_backup_streams_ssh_send_into_local_receive` to use its existing endpoint, state or callback context.

- `RemoteBackupRestoreTests.test_remote_backup_all_uses_remote_incremental_parent_paths` (function/method, line 183): Regression assertion: remote backup all uses remote incremental parent paths. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteBackupRestoreTests` to use its existing endpoint, state or callback context.

- `RemoteBackupRestoreTests.test_remote_backup_all_uses_remote_incremental_parent_paths.capture` (function/method, line 220): Test support: capture; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteBackupRestoreTests.test_remote_backup_all_uses_remote_incremental_parent_paths` to use its existing endpoint, state or callback context.

- `RemoteBackupRestoreTests.test_remote_backup_mode_ignores_sync_source_mode_and_targets_local_timeshift` (function/method, line 258): Regression assertion: remote backup mode ignores sync source mode and targets local timeshift. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteBackupRestoreTests` to use its existing endpoint, state or callback context.

- `RemoteBackupRestoreTests.test_pull_restore_indexes_snapshot_and_cache_on_local_timeshift_runner` (function/method, line 279): Regression assertion: pull restore indexes snapshot and cache on local timeshift runner. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteBackupRestoreTests` to use its existing endpoint, state or callback context.

- `RemoteBackupRestoreTests.test_pull_restore_live_common_proof_probes_local_timeshift_cache_path` (function/method, line 306): Regression assertion: pull restore live common proof probes local timeshift cache path. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteBackupRestoreTests` to use its existing endpoint, state or callback context.

- `RemoteBackupRestoreTests.test_pull_restore_live_common_proof_probes_local_timeshift_cache_path.CapturingOps` (class, line 315): Groups CapturingOps regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `RemoteBackupRestoreTests.test_pull_restore_live_common_proof_probes_local_timeshift_cache_path.CapturingOps.__init__` (function/method, line 316): Test support: init; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteBackupRestoreTests.test_pull_restore_live_common_proof_probes_local_timeshift_cache_path.CapturingOps` to use its existing endpoint, state or callback context.

- `RemoteBackupRestoreTests.test_pull_restore_live_common_proof_probes_local_timeshift_cache_path.CapturingOps.meta` (function/method, line 319): Test support: meta; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteBackupRestoreTests.test_pull_restore_live_common_proof_probes_local_timeshift_cache_path.CapturingOps` to use its existing endpoint, state or callback context.

- `RemoteBackupRestoreTests.test_remote_backup_scan_never_uses_local_timeshift_cache_root` (function/method, line 352): Regression assertion: remote backup scan never uses local timeshift cache root. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteBackupRestoreTests` to use its existing endpoint, state or callback context.

- `RemoteBackupRestoreTests.test_timeshift_path_probe_uses_source_privilege_prefix` (function/method, line 371): Regression assertion: timeshift path probe uses source privilege prefix. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteBackupRestoreTests` to use its existing endpoint, state or callback context.

- `RemoteBackupRestoreTests.test_repository_scan_uses_configured_privilege_prefix` (function/method, line 389): Regression assertion: repository scan uses configured privilege prefix. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteBackupRestoreTests` to use its existing endpoint, state or callback context.

- `RemoteBackupRestoreTests.test_local_physical_scanner_executes_and_preserves_info_json` (function/method, line 411): Regression assertion: local physical scanner executes and preserves info json. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteBackupRestoreTests` to use its existing endpoint, state or callback context.

- `RemoteBackupRestoreTests.test_remote_backup_scan_reads_entries_and_info_in_one_command` (function/method, line 435): Regression assertion: remote backup scan reads entries and info in one command. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteBackupRestoreTests` to use its existing endpoint, state or callback context.

- `RemoteBackupRestoreTests.test_privileged_file_reader_executes_and_preserves_content` (function/method, line 454): Regression assertion: privileged file reader executes and preserves content. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteBackupRestoreTests` to use its existing endpoint, state or callback context.

- `RemoteBackupRestoreTests.test_remote_backup_state_is_read_and_validated_on_backup_endpoint` (function/method, line 469): Regression assertion: remote backup state is read and validated on backup endpoint. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteBackupRestoreTests` to use its existing endpoint, state or callback context.

- `RemoteBackupRestoreTests.test_restore_mode_ssh_loads_ssh_even_when_sync_source_mode_is_local` (function/method, line 481): Regression assertion: restore mode ssh loads ssh even when sync source mode is local. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteBackupRestoreTests` to use its existing endpoint, state or callback context.

- `RemoteBackupRestoreTests.test_real_pull_restore_uses_local_process_lock` (function/method, line 492): Regression assertion: real pull restore uses local process lock. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteBackupRestoreTests` to use its existing endpoint, state or callback context.

- `RemoteBackupRestoreTests.test_real_pull_restore_uses_local_process_lock.FakeLock` (class, line 500): Groups FakeLock regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `RemoteBackupRestoreTests.test_real_pull_restore_uses_local_process_lock.FakeLock.__init__` (function/method, line 501): Test support: init; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteBackupRestoreTests.test_real_pull_restore_uses_local_process_lock.FakeLock` to use its existing endpoint, state or callback context.

- `RemoteBackupRestoreTests.test_real_pull_restore_uses_local_process_lock.FakeLock.__enter__` (function/method, line 504): Test support: enter; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteBackupRestoreTests.test_real_pull_restore_uses_local_process_lock.FakeLock` to use its existing endpoint, state or callback context.

- `RemoteBackupRestoreTests.test_real_pull_restore_uses_local_process_lock.FakeLock.__exit__` (function/method, line 508): Test support: exit; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteBackupRestoreTests.test_real_pull_restore_uses_local_process_lock.FakeLock` to use its existing endpoint, state or callback context.

- `RemoteBackupRestoreTests.test_pull_restore_does_not_require_remote_lock_directory` (function/method, line 542): Regression assertion: pull restore does not require remote lock directory. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteBackupRestoreTests` to use its existing endpoint, state or callback context.

- `RemoteBackupRestoreTests.test_restore_refuses_missing_local_lock_directory` (function/method, line 574): Regression assertion: restore refuses missing local lock directory. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteBackupRestoreTests` to use its existing endpoint, state or callback context.

- `RemoteBackupRestoreTests.test_restore_cli_uses_config_selected_transport` (function/method, line 597): Regression assertion: restore cli uses config selected transport. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RemoteBackupRestoreTests` to use its existing endpoint, state or callback context.

## `tests/test_restore_snapshot.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `info` (function/method, line 21): Test support: info; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `FakeSource` (class, line 29): Groups FakeSource regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `FakeSource.__init__` (function/method, line 30): Test support: init; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `FakeSource` to use its existing endpoint, state or callback context.

- `FakeSource.command` (function/method, line 36): Test support: command; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `FakeSource` to use its existing endpoint, state or callback context.

- `FakeSource.run` (function/method, line 39): Test support: run; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `FakeSource` to use its existing endpoint, state or callback context.

- `FakeSource.environment` (function/method, line 49): Test support: environment; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `FakeSource` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests` (class, line 53): Groups RestoreSnapshot regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `RestoreSnapshotTests.make_config` (function/method, line 54): Test support: make config; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.backup` (function/method, line 84): Test support: backup; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.single_plan` (function/method, line 97): Test support: single plan; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.chain_plan` (function/method, line 108): Test support: chain plan; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.meta_side_effect` (function/method, line 119): Test support: meta side effect; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.run_execution` (function/method, line 137): Test support: run execution; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.run_execution.capture_pipeline` (function/method, line 141): Test support: capture pipeline; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests.run_execution` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_single_local_restore_uses_full_receive_then_writable_cow_snapshot` (function/method, line 170): Regression assertion: single local restore uses full receive then writable cow snapshot. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_single_remote_restore_uses_same_flow_over_ssh` (function/method, line 185): Regression assertion: single remote restore uses same flow over ssh. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_restore_cli_requires_exactly_one_selection_and_exposes_no_common_override` (function/method, line 198): Regression assertion: restore cli requires exactly one selection and exposes no common override. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_common_parent_chain_full_seeds_common_then_sends_incrementals` (function/method, line 216): Regression assertion: common parent chain full seeds common then sends incrementals. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_no_common_parent_full_restores_oldest_then_incrementals` (function/method, line 235): Regression assertion: no common parent full restores oldest then incrementals. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_no_common_parent_real_restore_requires_explicit_override` (function/method, line 248): Regression assertion: no common parent real restore requires explicit override. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_all_with_one_backup_still_warns_when_no_common_parent_exists` (function/method, line 269): Regression assertion: all with one backup still warns when no common parent exists. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_restore_retention_confirmation_sentence_is_exact` (function/method, line 288): Regression assertion: restore retention confirmation sentence is exact. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_restore_plan_warns_that_timeshift_retention_can_delete_restored_snapshots` (function/method, line 294): Regression assertion: restore plan warns that timeshift retention can delete restored snapshots. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_real_restore_rejects_missing_retention_risk_sentence_before_streaming` (function/method, line 315): Regression assertion: real restore rejects missing retention risk sentence before streaming. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_dry_run_warns_without_common_parent_and_does_not_stream` (function/method, line 340): Regression assertion: dry run warns without common parent and does not stream. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_build_all_plan_restores_only_snapshots_after_newest_common_parent` (function/method, line 368): Regression assertion: build all plan restores only snapshots after newest common parent. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_build_all_plan_with_retained_cache_full_seeds_exact_common_backup` (function/method, line 413): Destination-only reset keeps cache but still needs a receiver-side full seed. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_same_date_info_identity_fallback_ignores_changed_tags_and_comments` (function/method, line 471): Regression assertion: same date info identity fallback ignores changed tags and comments. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_invalid_state_is_ignored_when_same_date_info_proves_common_parent` (function/method, line 511): Regression assertion: invalid state is ignored when same date info proves common parent. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_older_unreadable_dates_do_not_hide_newest_same_date_common_parent` (function/method, line 553): Old source metadata failures must not overwrite a newer valid overlap. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_build_all_plan_with_newest_common_parent_has_nothing_to_restore` (function/method, line 598): Regression assertion: build all plan with newest common parent has nothing to restore. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_latest_common_parent_uses_state_and_live_endpoint_uuid_identity` (function/method, line 642): Regression assertion: latest common parent uses state and live endpoint uuid identity. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_latest_common_parent_rejects_newer_candidate_when_uuid_and_info_proofs_both_fail` (function/method, line 711): Regression assertion: latest common parent rejects newer candidate when uuid and info proofs both fail. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_latest_common_parent_does_not_fail_on_info_json_provenance_change` (function/method, line 759): Scheduled/retained metadata must not overrule exact Btrfs lineage. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_uuid_proven_common_parent_overrides_repository_info_json_mismatch` (function/method, line 824): Regression assertion: uuid proven common parent overrides repository info json mismatch. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_existing_restore_target_is_never_overwritten` (function/method, line 890): Regression assertion: existing restore target is never overwritten. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_real_timeshift_info_json_without_date_is_accepted` (function/method, line 912): Regression assertion: real timeshift info json without date is accepted. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_real_timeshift_info_json_without_date_is_accepted.meta` (function/method, line 924): Test support: meta; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests.test_real_timeshift_info_json_without_date_is_accepted` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_restore_all_discovers_multiple_real_timeshift_info_files_without_date` (function/method, line 939): Regression assertion: restore all discovers multiple real timeshift info files without date. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_restore_all_discovers_multiple_real_timeshift_info_files_without_date.meta` (function/method, line 951): Test support: meta; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests.test_restore_all_discovers_multiple_real_timeshift_info_files_without_date` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_common_parent_always_full_seeds_hidden_chain_in_local_and_ssh_target_modes` (function/method, line 968): Regression assertion: common parent always full seeds hidden chain in local and ssh target modes. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_restore_inventory_includes_physical_snapshot_omitted_by_timeshift_list` (function/method, line 1002): Regression assertion: restore inventory includes physical snapshot omitted by timeshift list. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_ssh_target_inventory_keeps_snapshot_and_cache_on_same_remote_runner` (function/method, line 1044): Regression assertion: ssh target inventory keeps snapshot and cache on same remote runner. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_live_common_proof_requires_exact_readonly_cache_parent_chain` (function/method, line 1073): Regression assertion: live common proof requires exact readonly cache parent chain. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_missing_clone_source_retries_only_exact_payload_once_as_full` (function/method, line 1124): Regression assertion: missing clone source retries only exact payload once as full. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_missing_clone_source_retries_only_exact_payload_once_as_full.FakeOps` (class, line 1133): Groups FakeOps regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `RestoreSnapshotTests.test_missing_clone_source_retries_only_exact_payload_once_as_full.FakeOps.__init__` (function/method, line 1134): Test support: init; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests.test_missing_clone_source_retries_only_exact_payload_once_as_full.FakeOps` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_missing_clone_source_retries_only_exact_payload_once_as_full.FakeOps.meta` (function/method, line 1139): Test support: meta; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests.test_missing_clone_source_retries_only_exact_payload_once_as_full.FakeOps` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_missing_clone_source_retries_only_exact_payload_once_as_full.FakeOps.delete` (function/method, line 1162): Test support: delete; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests.test_missing_clone_source_retries_only_exact_payload_once_as_full.FakeOps` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_unrelated_incremental_receive_failure_is_not_retried_as_full` (function/method, line 1194): Regression assertion: unrelated incremental receive failure is not retried as full. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_unrelated_incremental_receive_failure_is_not_retried_as_full.FakeOps` (class, line 1202): Groups FakeOps regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `RestoreSnapshotTests.test_unrelated_incremental_receive_failure_is_not_retried_as_full.FakeOps.meta` (function/method, line 1205): Test support: meta; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests.test_unrelated_incremental_receive_failure_is_not_retried_as_full.FakeOps` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_unrelated_incremental_receive_failure_is_not_retried_as_full.FakeOps.delete` (function/method, line 1215): Test support: delete; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests.test_unrelated_incremental_receive_failure_is_not_retried_as_full.FakeOps` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_info_json_os_identity_ignores_snapshot_specific_fields` (function/method, line 1239): Regression assertion: info json os identity ignores snapshot specific fields. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_real_restore_requires_explicit_override_when_info_json_os_identity_is_not_proven` (function/method, line 1255): Regression assertion: real restore requires explicit override when info json os identity is not proven. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_os_identity_override_requires_exact_sentence_before_streaming` (function/method, line 1278): Regression assertion: os identity override requires exact sentence before streaming. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_effective_send_uuid_prefers_received_uuid_for_received_backups` (function/method, line 1309): Regression assertion: effective send uuid prefers received uuid for received backups. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

- `RestoreSnapshotTests.test_btrfs_snapshot_operation_builds_writable_and_readonly_commands` (function/method, line 1315): Regression assertion: btrfs snapshot operation builds writable and readonly commands. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreSnapshotTests` to use its existing endpoint, state or callback context.

## `tests/test_restore_timeshift_layout.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `TimeshiftNativeLayoutTests` (class, line 15): Groups TimeshiftNativeLayout regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `TimeshiftNativeLayoutTests.test_home_only_or_custom_payload_restore_is_rejected_before_commands` (function/method, line 16): Regression assertion: home only or custom payload restore is rejected before commands. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `TimeshiftNativeLayoutTests` to use its existing endpoint, state or callback context.

- `TimeshiftNativeLayoutTests.test_misrouted_native_timeshift_date_gets_transport_guidance` (function/method, line 26): Regression assertion: misrouted native timeshift date gets transport guidance. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `TimeshiftNativeLayoutTests` to use its existing endpoint, state or callback context.

- `TimeshiftNativeLayoutTests.test_pull_profile_transport_is_enabled_without_cli_flag` (function/method, line 60): Regression assertion: pull profile transport is enabled without cli flag. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `TimeshiftNativeLayoutTests` to use its existing endpoint, state or callback context.

## `tests/test_restore_topology_regressions.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `_UnusedTimeshiftOps` (class, line 29): Groups _UnusedTimeshiftOps regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `_UnusedTimeshiftOps.meta` (function/method, line 30): Test support: meta; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `_UnusedTimeshiftOps` to use its existing endpoint, state or callback context.

- `_CapturingEndpoint` (class, line 34): Groups _CapturingEndpoint regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `_CapturingEndpoint.__init__` (function/method, line 35): Test support: init; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `_CapturingEndpoint` to use its existing endpoint, state or callback context.

- `_CapturingEndpoint.run_shell` (function/method, line 39): Test support: run shell; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `_CapturingEndpoint` to use its existing endpoint, state or callback context.

- `RestoreTopologyRegressionTests` (class, line 44): Groups RestoreTopologyRegression regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `RestoreTopologyRegressionTests.test_pull_restore_profile_is_refused_for_sync` (function/method, line 45): Regression assertion: pull restore profile is refused for sync. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreTopologyRegressionTests` to use its existing endpoint, state or callback context.

- `RestoreTopologyRegressionTests.test_remote_roundtrip_uses_one_ssh_timeshift_host_in_both_directions` (function/method, line 50): Regression assertion: remote roundtrip uses one ssh timeshift host in both directions. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreTopologyRegressionTests` to use its existing endpoint, state or callback context.

- `RestoreTopologyRegressionTests.test_pull_and_push_restore_directions_are_described_separately` (function/method, line 62): Regression assertion: pull and push restore directions are described separately. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreTopologyRegressionTests` to use its existing endpoint, state or callback context.

- `RestoreTopologyRegressionTests.test_no_overlap_diagnostic_reports_counts_and_newest_dates` (function/method, line 72): Regression assertion: no overlap diagnostic reports counts and newest dates. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreTopologyRegressionTests` to use its existing endpoint, state or callback context.

- `RestoreTopologyRegressionTests.test_same_date_info_identity_recovers_when_state_and_cache_proof_are_missing` (function/method, line 94): Regression assertion: same date info identity recovers when state and cache proof are missing. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreTopologyRegressionTests` to use its existing endpoint, state or callback context.

- `RestoreTopologyRegressionTests.test_exact_state_uuid_proof_remains_authoritative` (function/method, line 133): Regression assertion: exact state uuid proof remains authoritative. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreTopologyRegressionTests` to use its existing endpoint, state or callback context.

- `RestoreTopologyRegressionTests.test_os_identity_matching_ignores_distro_text` (function/method, line 179): Regression assertion: os identity matching ignores distro text. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreTopologyRegressionTests` to use its existing endpoint, state or callback context.

- `RestoreTopologyRegressionTests.test_privileged_physical_scanner_prefixes_individual_read_only_commands` (function/method, line 193): Regression assertion: privileged physical scanner prefixes individual read only commands. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestoreTopologyRegressionTests` to use its existing endpoint, state or callback context.

## `tests/test_restricted_snapshot_listing.py`

**Role:** Regression tests. Restricted sudo discovery and truthful metadata fallbacks for service accounts.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `_row` (function/method, line 23): Build a two-payload observed date with exact source/received stream identities. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `RestrictedSnapshotListingTests` (class, line 33): Check the user's Btrfs/Timeshift-only sudo model without requiring a root login. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `RestrictedSnapshotListingTests.test_timeshift_is_primary_only_for_originals` (function/method, line 36): Current Timeshift tags replace source observations while own cache/target tags stay independent. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestrictedSnapshotListingTests` to use its existing endpoint, state or callback context.

- `RestrictedSnapshotListingTests.test_source_metadata_reads_skip_only_compatible_timeshift_names` (function/method, line 49): Avoid rereading known source JSON, but retain ordinary reads for omitted dates or a mismatched root. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestrictedSnapshotListingTests` to use its existing endpoint, state or callback context.

- `RestrictedSnapshotListingTests.test_failed_ordinary_scan_still_skips_known_source_json` (function/method, line 60): A Btrfs-only physical inventory does not trigger redundant reads of Timeshift-supplied JSON. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestrictedSnapshotListingTests` to use its existing endpoint, state or callback context.

- `RestrictedSnapshotListingTests.test_ordinary_json_fallback_reads_only_unlisted_dates` (function/method, line 68): Read omitted-date metadata as the login user without opening the known date's file. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestrictedSnapshotListingTests` to use its existing endpoint, state or callback context.

- `RestrictedSnapshotListingTests.test_skipping_source_json_preserves_restore_scanner_default` (function/method, line 87): Listing can skip file contents while restore's default still reads the original JSON and entries. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestrictedSnapshotListingTests` to use its existing endpoint, state or callback context.

- `RestrictedSnapshotListingTests._collect` (function/method, line 101): Isolate transport reads while retaining the real merge, proof and table ordering. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestrictedSnapshotListingTests` to use its existing endpoint, state or callback context.

- `RestrictedSnapshotListingTests.test_default_order_and_timeshift_metadata_survive_denied_json` (function/method, line 111): Regression assertion: default order and timeshift metadata survive denied json. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestrictedSnapshotListingTests` to use its existing endpoint, state or callback context.

- `RestrictedSnapshotListingTests.test_timeshift_failure_keeps_physical_rows_and_other_sides` (function/method, line 126): Regression assertion: timeshift failure keeps physical rows and other sides. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestrictedSnapshotListingTests` to use its existing endpoint, state or callback context.

- `RestrictedSnapshotListingTests.test_wrong_timeshift_filesystem_cannot_supply_tags` (function/method, line 136): Regression assertion: wrong timeshift filesystem cannot supply tags. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestrictedSnapshotListingTests` to use its existing endpoint, state or callback context.

- `RestrictedSnapshotListingTests.test_expired_original_cache_uses_verified_target_metadata` (function/method, line 144): Regression assertion: expired original cache uses verified target metadata. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestrictedSnapshotListingTests` to use its existing endpoint, state or callback context.

- `RestrictedSnapshotListingTests.test_mismatch_missing_or_writable_sibling_blocks_metadata_borrowing` (function/method, line 153): Regression assertion: mismatch missing or writable sibling blocks metadata borrowing. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestrictedSnapshotListingTests` to use its existing endpoint, state or callback context.

- `RestrictedSnapshotListingTests.test_btrfs_discovery_queries_nested_date_containers_with_only_approved_commands` (function/method, line 168): Regression assertion: btrfs discovery queries nested date containers with only approved commands. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestrictedSnapshotListingTests` to use its existing endpoint, state or callback context.

- `RestrictedSnapshotListingTests.test_btrfs_discovery_queries_nested_date_containers_with_only_approved_commands.batches` (function/method, line 171): Simulate root-only enumeration and second-level readonly payloads. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestrictedSnapshotListingTests.test_btrfs_discovery_queries_nested_date_containers_with_only_approved_commands` to use its existing endpoint, state or callback context.

- `RestrictedSnapshotListingTests.test_denied_ls_does_not_prevent_complete_btrfs_inventory` (function/method, line 191): Regression assertion: denied ls does not prevent complete btrfs inventory. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestrictedSnapshotListingTests` to use its existing endpoint, state or callback context.

- `RestrictedSnapshotListingTests.test_failed_date_query_retains_other_dates_and_reports_partial_inventory` (function/method, line 205): Regression assertion: failed date query retains other dates and reports partial inventory. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestrictedSnapshotListingTests` to use its existing endpoint, state or callback context.

- `RestrictedSnapshotListingTests.test_failed_date_query_retains_other_dates_and_reports_partial_inventory.batches` (function/method, line 207): Simulate one vanished date without losing a different successful date. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestrictedSnapshotListingTests.test_failed_date_query_retains_other_dates_and_reports_partial_inventory` to use its existing endpoint, state or callback context.

- `RestrictedSnapshotListingTests.test_df_denial_falls_back_to_sudo_btrfs_usage` (function/method, line 224): Regression assertion: df denial falls back to sudo btrfs usage. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestrictedSnapshotListingTests` to use its existing endpoint, state or callback context.

- `RestrictedSnapshotListingTests.test_json_reads_are_unprivileged_and_refuse_symlinks` (function/method, line 238): Regression assertion: json reads are unprivileged and refuse symlinks. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestrictedSnapshotListingTests` to use its existing endpoint, state or callback context.

- `RestrictedSnapshotListingTests.test_unconfirmed_timeshift_dates_are_visible_and_not_counted_as_verified` (function/method, line 255): Regression assertion: unconfirmed timeshift dates are visible and not counted as verified. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RestrictedSnapshotListingTests` to use its existing endpoint, state or callback context.

## `tests/test_retention_cleanup_accounting.py`

**Role:** Regression tests. Verify each retention side is counted without changing deletion safety.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `RetentionCleanupAccountingTests` (class, line 13): Groups RetentionCleanupAccounting regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `RetentionCleanupAccountingTests._execute` (function/method, line 14): Reuse existing fixtures and mocked deletion endpoints for one date. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RetentionCleanupAccountingTests` to use its existing endpoint, state or callback context.

- `RetentionCleanupAccountingTests.test_two_payload_subvolumes_count_as_one_snapshot_date_per_side` (function/method, line 40): Regression assertion: two payload subvolumes count as one snapshot date per side. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RetentionCleanupAccountingTests` to use its existing endpoint, state or callback context.

- `RetentionCleanupAccountingTests.test_cache_failure_preserves_destination_success_and_state_for_retry` (function/method, line 48): Regression assertion: cache failure preserves destination success and state for retry. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RetentionCleanupAccountingTests` to use its existing endpoint, state or callback context.

- `RetentionCleanupAccountingTests.test_destination_failure_does_not_attempt_cache_cleanup` (function/method, line 60): Regression assertion: destination failure does not attempt cache cleanup. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RetentionCleanupAccountingTests` to use its existing endpoint, state or callback context.

- `RetentionCleanupAccountingTests.test_disabled_cache_is_not_counted_or_deleted` (function/method, line 67): Regression assertion: disabled cache is not counted or deleted. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RetentionCleanupAccountingTests` to use its existing endpoint, state or callback context.

- `RetentionCleanupAccountingTests.test_direct_timeshift_send_is_not_counted_as_a_cache_snapshot` (function/method, line 76): Regression assertion: direct timeshift send is not counted as a cache snapshot. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RetentionCleanupAccountingTests` to use its existing endpoint, state or callback context.

- `RetentionCleanupAccountingTests.test_blocked_source_authorization_keeps_both_sides_untouched` (function/method, line 82): Regression assertion: blocked source authorization keeps both sides untouched. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RetentionCleanupAccountingTests` to use its existing endpoint, state or callback context.

- `RetentionCleanupAccountingTests.test_prune_returns_side_counts_when_cache_failure_prevents_state_removal` (function/method, line 102): Regression assertion: prune returns side counts when cache failure prevents state removal. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RetentionCleanupAccountingTests` to use its existing endpoint, state or callback context.

- `RetentionCleanupAccountingTests.test_dry_run_uses_candidates_and_never_claims_real_deletion` (function/method, line 122): Regression assertion: dry run uses candidates and never claims real deletion. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RetentionCleanupAccountingTests` to use its existing endpoint, state or callback context.

- `RetentionCleanupAccountingTests.test_missing_result_labels_both_sides_unknown_instead_of_zero` (function/method, line 140): Regression assertion: missing result labels both sides unknown instead of zero. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RetentionCleanupAccountingTests` to use its existing endpoint, state or callback context.

- `RetentionCleanupAccountingTests.test_not_requested_still_has_both_side_summaries` (function/method, line 145): Regression assertion: not requested still has both side summaries. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RetentionCleanupAccountingTests` to use its existing endpoint, state or callback context.

- `RetentionCleanupAccountingTests.test_original_timeshift_cleanup_is_labeled_separately_from_cache` (function/method, line 151): Regression assertion: original timeshift cleanup is labeled separately from cache. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RetentionCleanupAccountingTests` to use its existing endpoint, state or callback context.

- `RetentionCleanupAccountingTests.test_source_app_success_is_counted_before_later_destination_failure` (function/method, line 157): Regression assertion: source app success is counted before later destination failure. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `RetentionCleanupAccountingTests` to use its existing endpoint, state or callback context.

## `tests/test_runtime_safety.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `PreflightParserTests` (class, line 18): Groups PreflightParser regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `PreflightParserTests.test_shared_parser_handles_ok_failure_and_detail` (function/method, line 19): Regression assertion: shared parser handles ok failure and detail. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `PreflightParserTests` to use its existing endpoint, state or callback context.

- `PreflightParserTests.test_source_path_checks_executes_parser_after_lock_stage` (function/method, line 32): Regression assertion: source path checks executes parser after lock stage. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `PreflightParserTests` to use its existing endpoint, state or callback context.

- `StaticRuntimeSymbolTests` (class, line 56): Groups StaticRuntimeSymbol regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `StaticRuntimeSymbolTests.test_no_package_function_references_an_undefined_module_global` (function/method, line 57): Regression assertion: no package function references an undefined module global. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `StaticRuntimeSymbolTests` to use its existing endpoint, state or callback context.

- `StaticRuntimeSymbolTests.test_no_package_function_references_an_undefined_module_global.walk` (function/method, line 77): Test support: walk; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `StaticRuntimeSymbolTests.test_no_package_function_references_an_undefined_module_global` to use its existing endpoint, state or callback context.

- `LocalPathSafetyTests` (class, line 89): Groups LocalPathSafety regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `LocalPathSafetyTests.test_source_normalization_preserves_disabled_empty_path` (function/method, line 90): Regression assertion: source normalization preserves disabled empty path. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `LocalPathSafetyTests` to use its existing endpoint, state or callback context.

- `LocalPathSafetyTests.test_local_containment_resolves_symlinks` (function/method, line 95): Regression assertion: local containment resolves symlinks. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `LocalPathSafetyTests` to use its existing endpoint, state or callback context.

- `LocalPathSafetyTests.test_unmatched_btrfs_list_path_is_not_guessed_below_root` (function/method, line 106): Regression assertion: unmatched btrfs list path is not guessed below root. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `LocalPathSafetyTests` to use its existing endpoint, state or callback context.

- `SharedTreeSafetyTests` (class, line 111): Groups SharedTreeSafety regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `SharedTreeSafetyTests.setUp` (function/method, line 112): Test support: setUp; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SharedTreeSafetyTests` to use its existing endpoint, state or callback context.

- `SharedTreeSafetyTests.test_dry_run_refuses_nonempty_ordinary_root` (function/method, line 115): Regression assertion: dry run refuses nonempty ordinary root. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SharedTreeSafetyTests` to use its existing endpoint, state or callback context.

- `SharedTreeSafetyTests.test_destination_cleanup_refuses_unexpected_nested_subvolume` (function/method, line 130): Regression assertion: destination cleanup refuses unexpected nested subvolume. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SharedTreeSafetyTests` to use its existing endpoint, state or callback context.

## `tests/test_shared_workflows.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `snapshot` (function/method, line 22): Test support: snapshot; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `SharedWorkflowTests` (class, line 34): Groups SharedWorkflow regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `SharedWorkflowTests.source_snapshots` (function/method, line 35): Test support: source snapshots; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SharedWorkflowTests` to use its existing endpoint, state or callback context.

- `SharedWorkflowTests.test_sync_planner_is_pure_and_orders_oldest_to_newest` (function/method, line 38): Regression assertion: sync planner is pure and orders oldest to newest. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SharedWorkflowTests` to use its existing endpoint, state or callback context.

- `SharedWorkflowTests.test_planner_and_executor_compose_in_the_same_order` (function/method, line 62): Regression assertion: planner and executor compose in the same order. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SharedWorkflowTests` to use its existing endpoint, state or callback context.

- `SharedWorkflowTests.test_planner_and_executor_compose_in_the_same_order.handle` (function/method, line 66): Test support: handle; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SharedWorkflowTests.test_planner_and_executor_compose_in_the_same_order` to use its existing endpoint, state or callback context.

- `SharedWorkflowTests.test_prune_plan_preserves_destination_cache_state_order` (function/method, line 75): Regression assertion: prune plan preserves destination cache state order. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SharedWorkflowTests` to use its existing endpoint, state or callback context.

- `SharedWorkflowTests.test_recovery_plan_uses_cache_destination_state_order` (function/method, line 82): Regression assertion: recovery plan uses cache destination state order. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SharedWorkflowTests` to use its existing endpoint, state or callback context.

- `SharedWorkflowTests.test_all_cleanup_workflows_use_one_tree_delete_implementation` (function/method, line 89): Regression assertion: all cleanup workflows use one tree delete implementation. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SharedWorkflowTests` to use its existing endpoint, state or callback context.

- `SharedWorkflowTests.test_cache_operation_uses_one_btrfs_facade_and_exact_target` (function/method, line 94): Regression assertion: cache operation uses one btrfs facade and exact target. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SharedWorkflowTests` to use its existing endpoint, state or callback context.

- `SharedWorkflowTests.test_cache_operation_uses_one_btrfs_facade_and_exact_target.run_shell` (function/method, line 117): Test support: run shell; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SharedWorkflowTests.test_cache_operation_uses_one_btrfs_facade_and_exact_target` to use its existing endpoint, state or callback context.

- `SharedWorkflowTests.test_tree_discovery_uses_one_bulk_child_listing` (function/method, line 135): Regression assertion: tree discovery uses one bulk child listing. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SharedWorkflowTests` to use its existing endpoint, state or callback context.

- `SharedWorkflowTests.test_operation_modules_have_single_authoritative_definitions` (function/method, line 148): Regression assertion: operation modules have single authoritative definitions. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SharedWorkflowTests` to use its existing endpoint, state or callback context.

## `tests/test_snapshot_info_json.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `inventory_with_info` (function/method, line 18): Test support: inventory with info; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `InfoJsonFrameTests` (class, line 27): Groups InfoJsonFrame regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `InfoJsonFrameTests.test_parser_preserves_content_with_final_newline` (function/method, line 28): Regression assertion: parser preserves content with final newline. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `InfoJsonFrameTests` to use its existing endpoint, state or callback context.

- `InfoJsonFrameTests.test_local_reader_loads_only_timeshift_date_directories` (function/method, line 39): Regression assertion: local reader loads only timeshift date directories. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `InfoJsonFrameTests` to use its existing endpoint, state or callback context.

- `InfoJsonFrameTests.test_parser_preserves_content_without_final_newline` (function/method, line 52): Regression assertion: parser preserves content without final newline. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `InfoJsonFrameTests` to use its existing endpoint, state or callback context.

- `DestinationInfoJsonTests` (class, line 64): Groups DestinationInfoJson regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `DestinationInfoJsonTests.make_config` (function/method, line 65): Test support: make config; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationInfoJsonTests` to use its existing endpoint, state or callback context.

- `DestinationInfoJsonTests.test_single_subvolume_snapshot_writes_shared_info_json` (function/method, line 71): Regression assertion: single subvolume snapshot writes shared info json. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationInfoJsonTests` to use its existing endpoint, state or callback context.

- `DestinationInfoJsonTests.test_home_only_snapshot_writes_shared_info_json` (function/method, line 85): Regression assertion: home only snapshot writes shared info json. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationInfoJsonTests` to use its existing endpoint, state or callback context.

- `DestinationInfoJsonTests.test_paired_snapshot_is_complete_only_after_both_subvolumes_exist` (function/method, line 93): Regression assertion: paired snapshot is complete only after both subvolumes exist. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationInfoJsonTests` to use its existing endpoint, state or callback context.

- `DestinationInfoJsonTests.test_existing_file_is_updated_and_then_idempotent` (function/method, line 118): Regression assertion: existing file is updated and then idempotent. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationInfoJsonTests` to use its existing endpoint, state or callback context.

- `DestinationInfoJsonTests.test_missing_source_metadata_is_a_hard_error` (function/method, line 128): Regression assertion: missing source metadata is a hard error. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationInfoJsonTests` to use its existing endpoint, state or callback context.

- `DestinationInfoJsonTests.test_missing_metadata_error_names_remote_user_uid_and_fstab_fix` (function/method, line 138): Regression assertion: missing metadata error names remote user uid and fstab fix. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationInfoJsonTests` to use its existing endpoint, state or callback context.

- `DestinationInfoJsonTests.test_symlink_destination_is_refused` (function/method, line 155): Regression assertion: symlink destination is refused. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationInfoJsonTests` to use its existing endpoint, state or callback context.

- `DestinationInfoJsonTests.test_prune_preserves_info_json_when_unknown_content_remains` (function/method, line 168): Regression assertion: prune preserves info json when unknown content remains. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationInfoJsonTests` to use its existing endpoint, state or callback context.

- `DestinationInfoJsonTests.test_prune_deletes_date_subvolume_after_children_and_info_json_disappears_with_it` (function/method, line 183): Regression assertion: prune deletes date subvolume after children and info json disappears with it. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationInfoJsonTests` to use its existing endpoint, state or callback context.

- `DestinationInfoJsonTests.test_prune_refuses_ordinary_date_folder` (function/method, line 205): Regression assertion: prune refuses ordinary date folder. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `DestinationInfoJsonTests` to use its existing endpoint, state or callback context.

## `tests/test_snapshot_listing.py`

**Role:** Regression tests. Non-root inventory tests with physical local fixtures and simulated Btrfs/SSH.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `_record` (function/method, line 29): Create a discovered physical date with native Timeshift metadata. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `SnapshotListingTests` (class, line 35): Verify truthful reports and transport/privilege boundaries across every profile. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `SnapshotListingTests._section` (function/method, line 38): Reuse the shared config fixture and isolate only external discovery/probes. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotListingTests` to use its existing endpoint, state or callback context.

- `SnapshotListingTests.test_named_tags_do_not_invent_ondemand_or_boot` (function/method, line 47): Regression assertion: named tags do not invent ondemand or boot. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotListingTests` to use its existing endpoint, state or callback context.

- `SnapshotListingTests.test_compact_tags_and_unknown_metadata` (function/method, line 51): Regression assertion: compact tags and unknown metadata. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotListingTests` to use its existing endpoint, state or callback context.

- `SnapshotListingTests.test_remote_comments_cannot_inject_terminal_controls` (function/method, line 59): Regression assertion: remote comments cannot inject terminal controls. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotListingTests` to use its existing endpoint, state or callback context.

- `SnapshotListingTests.test_pair_counts_once_and_readonly_is_visible` (function/method, line 66): Regression assertion: pair counts once and readonly is visible. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotListingTests` to use its existing endpoint, state or callback context.

- `SnapshotListingTests.test_incomplete_and_unverified_dates_stay_visible` (function/method, line 80): Regression assertion: incomplete and unverified dates stay visible. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotListingTests` to use its existing endpoint, state or callback context.

- `SnapshotListingTests.test_permission_denied_is_visible_without_fallback` (function/method, line 90): Regression assertion: permission denied is visible without fallback. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotListingTests` to use its existing endpoint, state or callback context.

- `SnapshotListingTests.test_symlink_date_and_payload_not_probed` (function/method, line 96): Regression assertion: symlink date and payload not probed. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotListingTests` to use its existing endpoint, state or callback context.

- `SnapshotListingTests.test_cache_own_metadata_precedes_live_source_fallback` (function/method, line 108): Regression assertion: cache own metadata precedes live source fallback. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotListingTests` to use its existing endpoint, state or callback context.

- `SnapshotListingTests.test_disabled_cache_reports_source_filesystem` (function/method, line 119): Regression assertion: disabled cache reports source filesystem. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotListingTests` to use its existing endpoint, state or callback context.

- `SnapshotListingTests.test_empty_repository_is_distinct_from_unavailable` (function/method, line 127): Regression assertion: empty repository is distinct from unavailable. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotListingTests` to use its existing endpoint, state or callback context.

- `SnapshotListingTests.test_wrong_filesystem_is_reported_even_for_empty_repository` (function/method, line 135): Regression assertion: wrong filesystem is reported even for empty repository. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotListingTests` to use its existing endpoint, state or callback context.

- `SnapshotListingTests.test_real_batch_execution_quotes_paths_and_preserves_failures` (function/method, line 141): Regression assertion: real batch execution quotes paths and preserves failures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotListingTests` to use its existing endpoint, state or callback context.

- `SnapshotListingTests.test_all_eight_profiles_choose_actual_hosts_in_auto` (function/method, line 153): Regression assertion: all eight profiles choose actual hosts in auto. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotListingTests` to use its existing endpoint, state or callback context.

- `SnapshotListingTests.test_explicit_restore_local_ignores_sync_ssh_source` (function/method, line 173): Regression assertion: explicit restore local ignores sync ssh source. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotListingTests` to use its existing endpoint, state or callback context.

- `SnapshotListingTests.test_source_failure_does_not_hide_destination` (function/method, line 181): Regression assertion: source failure does not hide destination. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotListingTests` to use its existing endpoint, state or callback context.

- `SnapshotListingTests.test_source_failure_does_not_hide_destination.scan` (function/method, line 182): Simulate inaccessible source and a readable backup date. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotListingTests.test_source_failure_does_not_hide_destination` to use its existing endpoint, state or callback context.

- `SnapshotListingTests.test_cli_returns_failure_after_printing_all_sections_without_run_logging` (function/method, line 198): Regression assertion: cli returns failure after printing all sections without run logging. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotListingTests` to use its existing endpoint, state or callback context.

- `SnapshotListingTests.test_df_parses_localized_environment_and_spaced_mount` (function/method, line 207): Regression assertion: df parses localized environment and spaced mount. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotListingTests` to use its existing endpoint, state or callback context.

- `SnapshotListingTests.test_actual_local_scan_and_df_need_no_privilege` (function/method, line 220): Regression assertion: actual local scan and df need no privilege. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotListingTests` to use its existing endpoint, state or callback context.

- `SnapshotListingTests.test_batch_probes_reuse_btrfs_argv_and_do_not_inject_sudo` (function/method, line 232): Regression assertion: batch probes reuse btrfs argv and do not inject sudo. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotListingTests` to use its existing endpoint, state or callback context.

- `SnapshotListingTests.test_truncated_or_duplicate_batch_response_fails` (function/method, line 247): Regression assertion: truncated or duplicate batch response fails. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotListingTests` to use its existing endpoint, state or callback context.

- `SnapshotListingTests.test_large_repository_uses_bounded_batches_without_losing_rows` (function/method, line 254): Regression assertion: large repository uses bounded batches without losing rows. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotListingTests` to use its existing endpoint, state or callback context.

- `SnapshotListingTests.test_large_repository_uses_bounded_batches_without_losing_rows.respond` (function/method, line 257): Return one flag frame per request in each bounded transport batch. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotListingTests.test_large_repository_uses_bounded_batches_without_losing_rows` to use its existing endpoint, state or callback context.

- `SnapshotPairComparisonTests` (class, line 270): Expose cache leftovers and UUID mismatches without changing storage or default exit policy. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `SnapshotPairComparisonTests._rows` (function/method, line 273): Build both configured payload identities; differing local UUIDs share a valid send identity. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotPairComparisonTests` to use its existing endpoint, state or callback context.

- `SnapshotPairComparisonTests._compare` (function/method, line 282): Keep endpoint discovery separate from the comparison's captured physical observations. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotPairComparisonTests` to use its existing endpoint, state or callback context.

- `SnapshotPairComparisonTests.test_user_36_cache_17_target_sample_reports_all_19_july_leftovers` (function/method, line 288): Regression assertion: user 36 cache 17 target sample reports all 19 july leftovers. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotPairComparisonTests` to use its existing endpoint, state or callback context.

- `SnapshotPairComparisonTests.test_equal_counts_with_different_dates_are_not_parity` (function/method, line 305): Regression assertion: equal counts with different dates are not parity. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotPairComparisonTests` to use its existing endpoint, state or callback context.

- `SnapshotPairComparisonTests.test_changed_flags_do_not_invalidate_an_immutable_pair` (function/method, line 311): Regression assertion: changed flags do not invalidate an immutable pair. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotPairComparisonTests` to use its existing endpoint, state or callback context.

- `SnapshotPairComparisonTests.test_same_names_with_uuid_mismatch_missing_sibling_or_writable_payload_are_unproven` (function/method, line 318): Regression assertion: same names with uuid mismatch missing sibling or writable payload are unproven. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotPairComparisonTests` to use its existing endpoint, state or callback context.

- `SnapshotPairComparisonTests.test_received_sender_uses_original_stream_identity` (function/method, line 332): Regression assertion: received sender uses original stream identity. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotPairComparisonTests` to use its existing endpoint, state or callback context.

- `SnapshotPairComparisonTests.test_outside_window_is_distinguished_without_a_deletion_claim` (function/method, line 339): Regression assertion: outside window is distinguished without a deletion claim. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotPairComparisonTests` to use its existing endpoint, state or callback context.

- `SnapshotPairComparisonTests.test_incomplete_discovery_never_confirms_parity_or_absence` (function/method, line 348): Regression assertion: incomplete discovery never confirms parity or absence. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotPairComparisonTests` to use its existing endpoint, state or callback context.

- `SnapshotPairComparisonTests.test_disabled_cache_is_explicit_and_empty_enabled_roots_match` (function/method, line 355): Regression assertion: disabled cache is explicit and empty enabled roots match. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotPairComparisonTests` to use its existing endpoint, state or callback context.

- `SnapshotPairComparisonTests.test_opt_in_cli_exit_check_and_default_warning_have_no_run_logging` (function/method, line 363): Regression assertion: opt in cli exit check and default warning have no run logging. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotPairComparisonTests` to use its existing endpoint, state or callback context.

- `SnapshotPairComparisonTests.test_df_unknown_type_preserves_space_when_native_identity_confirms_btrfs` (function/method, line 374): Regression assertion: df unknown type preserves space when native identity confirms btrfs. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotPairComparisonTests` to use its existing endpoint, state or callback context.

- `SnapshotPairComparisonTests.test_df_unknown_type_without_identity_uses_existing_btrfs_reader` (function/method, line 385): Regression assertion: df unknown type without identity uses existing btrfs reader. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotPairComparisonTests` to use its existing endpoint, state or callback context.

- `SnapshotPairComparisonTests.test_partial_native_index_marks_comparison_incomplete` (function/method, line 396): Regression assertion: partial native index marks comparison incomplete. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SnapshotPairComparisonTests` to use its existing endpoint, state or callback context.

## `tests/test_source_inventory.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `FakeSource` (class, line 14): Groups FakeSource regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `FakeSource.__init__` (function/method, line 15): Test support: init; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `FakeSource` to use its existing endpoint, state or callback context.

- `FakeSource.run` (function/method, line 21): Test support: run; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `FakeSource` to use its existing endpoint, state or callback context.

- `index` (function/method, line 26): Test support: index; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `CombinedInventoryTests` (class, line 33): Groups CombinedInventory regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `CombinedInventoryTests.test_build_source_inventory_uses_one_source_command_and_parses_all_sections` (function/method, line 34): Regression assertion: build source inventory uses one source command and parses all sections. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CombinedInventoryTests` to use its existing endpoint, state or callback context.

- `CombinedInventoryTests.test_index_finds_received_copy_by_effective_send_uuid` (function/method, line 116): Regression assertion: index finds received copy by effective send uuid. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CombinedInventoryTests` to use its existing endpoint, state or callback context.

- `CombinedInventoryTests.test_unreadable_snapshot_root_is_applied_to_each_missing_info_json` (function/method, line 130): Regression assertion: unreadable snapshot root is applied to each missing info json. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CombinedInventoryTests` to use its existing endpoint, state or callback context.

- `CombinedInventoryTests.test_required_path_changes_ignore_unrelated_churn` (function/method, line 159): Regression assertion: required path changes ignore unrelated churn. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CombinedInventoryTests` to use its existing endpoint, state or callback context.

- `CombinedInventoryTests.test_required_path_changes_detect_disappearance_and_uuid_replacement` (function/method, line 191): Regression assertion: required path changes detect disappearance and uuid replacement. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CombinedInventoryTests` to use its existing endpoint, state or callback context.

- `PreflightBatchTests` (class, line 218): Groups PreflightBatch regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `PreflightBatchTests.test_cache_check_runs_only_after_snapshot_ok_inside_one_shell` (function/method, line 219): Regression assertion: cache check runs only after snapshot ok inside one shell. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `PreflightBatchTests` to use its existing endpoint, state or callback context.

- `PreflightBatchTests.test_cache_check_is_skipped_when_snapshot_fails` (function/method, line 229): Regression assertion: cache check is skipped when snapshot fails. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `PreflightBatchTests` to use its existing endpoint, state or callback context.

- `CacheCreationBatchTests` (class, line 239): Groups CacheCreationBatch regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `CacheCreationBatchTests.test_create_and_show_metadata_are_parsed_from_one_source_command` (function/method, line 240): Regression assertion: create and show metadata are parsed from one source command. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CacheCreationBatchTests` to use its existing endpoint, state or callback context.

- `SyncContinuationTests` (class, line 276): Groups SyncContinuation regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `SyncContinuationTests.test_failed_send_rebuilds_inventory_recovers_version_and_continues` (function/method, line 277): Regression assertion: failed send rebuilds inventory recovers version and continues. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SyncContinuationTests` to use its existing endpoint, state or callback context.

- `SyncContinuationTests.test_failed_send_rebuilds_inventory_recovers_version_and_continues.SyncSource` (class, line 307): Groups SyncSource regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `SyncContinuationTests.test_failed_send_rebuilds_inventory_recovers_version_and_continues.SyncSource.command` (function/method, line 311): Test support: command; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SyncContinuationTests.test_failed_send_rebuilds_inventory_recovers_version_and_continues.SyncSource` to use its existing endpoint, state or callback context.

- `SyncContinuationTests.test_failed_send_rebuilds_inventory_recovers_version_and_continues.SyncSource.environment` (function/method, line 314): Test support: environment; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SyncContinuationTests.test_failed_send_rebuilds_inventory_recovers_version_and_continues.SyncSource` to use its existing endpoint, state or callback context.

- `SyncContinuationTests.test_failed_send_rebuilds_inventory_recovers_version_and_continues.SyncSource.run` (function/method, line 317): Test support: run; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SyncContinuationTests.test_failed_send_rebuilds_inventory_recovers_version_and_continues.SyncSource` to use its existing endpoint, state or callback context.

## `tests/test_ssh_auth_regressions.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `SSHAuthenticationRegressionTests` (class, line 13): Groups SSHAuthenticationRegression regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `SSHAuthenticationRegressionTests.tearDown` (function/method, line 14): Test support: tearDown; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SSHAuthenticationRegressionTests` to use its existing endpoint, state or callback context.

- `SSHAuthenticationRegressionTests._write_config` (function/method, line 17): Test support: write config; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SSHAuthenticationRegressionTests` to use its existing endpoint, state or callback context.

- `SSHAuthenticationRegressionTests.test_password_only_behavior_still_uses_sshpass_environment` (function/method, line 39): Regression assertion: password only behavior still uses sshpass environment. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SSHAuthenticationRegressionTests` to use its existing endpoint, state or callback context.

- `SSHAuthenticationRegressionTests.test_direct_identity_passphrase_uses_prompt_aware_askpass` (function/method, line 44): Regression assertion: direct identity passphrase uses prompt aware askpass. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SSHAuthenticationRegressionTests` to use its existing endpoint, state or callback context.

- `SSHAuthenticationRegressionTests.test_file_backed_identity_passphrase_allows_one_final_newline` (function/method, line 58): Regression assertion: file backed identity passphrase allows one final newline. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SSHAuthenticationRegressionTests` to use its existing endpoint, state or callback context.

- `SSHAuthenticationRegressionTests.test_key_and_account_secrets_can_be_distinct` (function/method, line 71): Regression assertion: key and account secrets can be distinct. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SSHAuthenticationRegressionTests` to use its existing endpoint, state or callback context.

- `SSHAuthenticationRegressionTests.test_askpass_dispatches_key_and_account_prompts_and_refuses_unknown_prompt` (function/method, line 85): Regression assertion: askpass dispatches key and account prompts and refuses unknown prompt. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SSHAuthenticationRegressionTests` to use its existing endpoint, state or callback context.

- `SSHAuthenticationRegressionTests.test_batch_mode_yes_is_rejected_with_password_or_passphrase` (function/method, line 127): Regression assertion: batch mode yes is rejected with password or passphrase. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SSHAuthenticationRegressionTests` to use its existing endpoint, state or callback context.

- `SSHAuthenticationRegressionTests.test_identity_passphrase_requires_identity_file` (function/method, line 138): Regression assertion: identity passphrase requires identity file. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SSHAuthenticationRegressionTests` to use its existing endpoint, state or callback context.

- `SSHAuthenticationRegressionTests.test_identity_passphrase_file_must_exist` (function/method, line 144): Regression assertion: identity passphrase file must exist. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SSHAuthenticationRegressionTests` to use its existing endpoint, state or callback context.

- `SSHAuthenticationRegressionTests.test_direct_and_file_secret_are_mutually_exclusive` (function/method, line 154): Regression assertion: direct and file secret are mutually exclusive. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SSHAuthenticationRegressionTests` to use its existing endpoint, state or callback context.

- `SSHAuthenticationRegressionTests.test_empty_secrets_fail_closed` (function/method, line 167): Regression assertion: empty secrets fail closed. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SSHAuthenticationRegressionTests` to use its existing endpoint, state or callback context.

- `SSHAuthenticationRegressionTests.test_runner_stream_environment_uses_same_authentication_builder` (function/method, line 180): Regression assertion: runner stream environment uses same authentication builder. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SSHAuthenticationRegressionTests` to use its existing endpoint, state or callback context.

## `tests/test_ssh_identity_passphrase.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `SSHIdentityPassphraseTests` (class, line 15): Groups SSHIdentityPassphrase regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `SSHIdentityPassphraseTests.test_password_only_keeps_established_sshpass_path` (function/method, line 16): Regression assertion: password only keeps established sshpass path. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SSHIdentityPassphraseTests` to use its existing endpoint, state or callback context.

- `SSHIdentityPassphraseTests.test_identity_passphrase_uses_prompt_aware_askpass_without_sshpass` (function/method, line 21): Regression assertion: identity passphrase uses prompt aware askpass without sshpass. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SSHIdentityPassphraseTests` to use its existing endpoint, state or callback context.

- `SSHIdentityPassphraseTests.test_distinct_key_and_account_secrets_are_dispatched_by_prompt` (function/method, line 40): Regression assertion: distinct key and account secrets are dispatched by prompt. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SSHIdentityPassphraseTests` to use its existing endpoint, state or callback context.

- `SSHIdentityPassphraseTests.test_identity_passphrase_file_is_read_without_final_newline` (function/method, line 86): Regression assertion: identity passphrase file is read without final newline. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SSHIdentityPassphraseTests` to use its existing endpoint, state or callback context.

- `SSHIdentityPassphraseTests.test_empty_identity_passphrase_file_is_refused_at_use` (function/method, line 99): Regression assertion: empty identity passphrase file is refused at use. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SSHIdentityPassphraseTests` to use its existing endpoint, state or callback context.

- `SSHIdentityPassphraseTests.test_ssh_runner_and_streaming_runner_share_prompt_dispatch` (function/method, line 111): Regression assertion: ssh runner and streaming runner share prompt dispatch. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SSHIdentityPassphraseTests` to use its existing endpoint, state or callback context.

- `SSHIdentityPassphraseConfigTests` (class, line 141): Groups SSHIdentityPassphraseConfig regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `SSHIdentityPassphraseConfigTests._write_config` (function/method, line 142): Test support: write config; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SSHIdentityPassphraseConfigTests` to use its existing endpoint, state or callback context.

- `SSHIdentityPassphraseConfigTests.test_loader_accepts_direct_identity_passphrase` (function/method, line 169): Regression assertion: loader accepts direct identity passphrase. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SSHIdentityPassphraseConfigTests` to use its existing endpoint, state or callback context.

- `SSHIdentityPassphraseConfigTests.test_loader_accepts_identity_passphrase_file` (function/method, line 182): Regression assertion: loader accepts identity passphrase file. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SSHIdentityPassphraseConfigTests` to use its existing endpoint, state or callback context.

- `SSHIdentityPassphraseConfigTests.test_loader_rejects_both_identity_passphrase_sources` (function/method, line 197): Regression assertion: loader rejects both identity passphrase sources. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SSHIdentityPassphraseConfigTests` to use its existing endpoint, state or callback context.

- `SSHIdentityPassphraseConfigTests.test_loader_requires_identity_file` (function/method, line 212): Regression assertion: loader requires identity file. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SSHIdentityPassphraseConfigTests` to use its existing endpoint, state or callback context.

- `SSHIdentityPassphraseConfigTests.test_loader_rejects_batch_mode_with_identity_passphrase` (function/method, line 218): Regression assertion: loader rejects batch mode with identity passphrase. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SSHIdentityPassphraseConfigTests` to use its existing endpoint, state or callback context.

## `tests/test_state_path_portability.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `CurrentStatePathTests` (class, line 24): Groups CurrentStatePath regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `CurrentStatePathTests._snapshot` (function/method, line 25): Test support: snapshot; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CurrentStatePathTests` to use its existing endpoint, state or callback context.

- `CurrentStatePathTests.test_cache_paths_are_written_in_current_relative_schema` (function/method, line 44): Regression assertion: cache paths are written in current relative schema. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CurrentStatePathTests` to use its existing endpoint, state or callback context.

- `CurrentStatePathTests.test_received_send_source_records_received_uuid_not_local_uuid` (function/method, line 83): Regression assertion: received send source records received uuid not local uuid. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CurrentStatePathTests` to use its existing endpoint, state or callback context.

- `CurrentStatePathTests.test_direct_timeshift_path_uses_explicit_current_kind` (function/method, line 123): Regression assertion: direct timeshift path uses explicit current kind. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CurrentStatePathTests` to use its existing endpoint, state or callback context.

- `CurrentStatePathTests.test_loader_accepts_only_current_state_version` (function/method, line 148): Regression assertion: loader accepts only current state version. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CurrentStatePathTests` to use its existing endpoint, state or callback context.

- `CurrentStatePathTests.test_loader_rejects_invalid_state_shapes` (function/method, line 157): Regression assertion: loader rejects invalid state shapes. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CurrentStatePathTests` to use its existing endpoint, state or callback context.

- `CurrentStatePathTests.test_relative_state_rebases_under_current_cache_root` (function/method, line 167): Regression assertion: relative state rebases under current cache root. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CurrentStatePathTests` to use its existing endpoint, state or callback context.

- `CurrentStatePathTests.test_missing_send_path_kind_is_rejected` (function/method, line 181): Regression assertion: missing send path kind is rejected. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CurrentStatePathTests` to use its existing endpoint, state or callback context.

- `CurrentStatePathTests.test_writer_rejects_paths_outside_current_roots` (function/method, line 192): Regression assertion: writer rejects paths outside current roots. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CurrentStatePathTests` to use its existing endpoint, state or callback context.

- `CurrentStatePathTests.test_prune_resolves_current_relative_cache_path` (function/method, line 210): Regression assertion: prune resolves current relative cache path. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CurrentStatePathTests` to use its existing endpoint, state or callback context.

- `CurrentStatePathTests.test_parent_selection_rebases_current_relative_cache_path` (function/method, line 224): Regression assertion: parent selection rebases current relative cache path. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CurrentStatePathTests` to use its existing endpoint, state or callback context.

- `CurrentStatePathTests.test_save_preserves_current_schema_version` (function/method, line 240): Regression assertion: save preserves current schema version. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CurrentStatePathTests` to use its existing endpoint, state or callback context.

- `CurrentStatePathTests.test_relative_path_must_match_record_identity` (function/method, line 247): Regression assertion: relative path must match record identity. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `CurrentStatePathTests` to use its existing endpoint, state or callback context.

## `tests/test_sync_cleanup_summary.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `SyncCleanupSummaryTests` (class, line 18): Groups SyncCleanupSummary regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `SyncCleanupSummaryTests.test_cleanup_summary_is_present_when_prune_not_requested` (function/method, line 19): Regression assertion: cleanup summary is present when prune not requested. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SyncCleanupSummaryTests` to use its existing endpoint, state or callback context.

- `SyncCleanupSummaryTests.test_cleanup_summary_reports_successful_zero_cleanup` (function/method, line 26): Regression assertion: cleanup summary reports successful zero cleanup. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SyncCleanupSummaryTests` to use its existing endpoint, state or callback context.

- `SyncCleanupSummaryTests.test_cleanup_summary_reports_dry_run_zero_deletions` (function/method, line 37): Regression assertion: cleanup summary reports dry run zero deletions. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SyncCleanupSummaryTests` to use its existing endpoint, state or callback context.

- `SyncCleanupSummaryTests._sample_sync` (function/method, line 49): Test support: sample sync; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SyncCleanupSummaryTests` to use its existing endpoint, state or callback context.

- `SyncCleanupSummaryTests.test_final_terminal_log_order_is_transfers_sync_cleanup` (function/method, line 70): Regression assertion: final terminal log order is transfers sync cleanup. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SyncCleanupSummaryTests` to use its existing endpoint, state or callback context.

- `SyncCleanupSummaryTests.test_mail_success_text_replaces_intermediate_success_output_and_starts_with_name` (function/method, line 97): Regression assertion: mail success text replaces intermediate success output and starts with name. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SyncCleanupSummaryTests` to use its existing endpoint, state or callback context.

- `SyncCleanupSummaryTests.test_sync_summary_includes_total_backup_time` (function/method, line 128): Regression assertion: sync summary includes total backup time. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SyncCleanupSummaryTests` to use its existing endpoint, state or callback context.

- `SyncCleanupSummaryTests.test_duration_supports_days` (function/method, line 132): Regression assertion: duration supports days. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SyncCleanupSummaryTests` to use its existing endpoint, state or callback context.

- `SyncCleanupSummaryTests.test_transfer_section_explains_what_is_listed` (function/method, line 135): Regression assertion: transfer section explains what is listed. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SyncCleanupSummaryTests` to use its existing endpoint, state or callback context.

- `SyncCleanupSummaryTests.test_failed_sync_summary_format_is_not_used_for_completed_sync` (function/method, line 141): Regression assertion: failed sync summary format is not used for completed sync. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SyncCleanupSummaryTests` to use its existing endpoint, state or callback context.

## `tests/test_topology_safety.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `TopologySafetyTests` (class, line 24): Groups TopologySafety regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `TopologySafetyTests.test_sync_command_refuses_pull_restore_profile_before_work` (function/method, line 26): Regression assertion: sync command refuses pull restore profile before work. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `TopologySafetyTests` to use its existing endpoint, state or callback context.

- `TopologySafetyTests.test_pull_restore_profile_is_refused_for_sync` (function/method, line 32): Regression assertion: pull restore profile is refused for sync. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `TopologySafetyTests` to use its existing endpoint, state or callback context.

- `TopologySafetyTests.test_remote_roundtrip_profile_is_valid_for_sync_and_push_restore` (function/method, line 37): Regression assertion: remote roundtrip profile is valid for sync and push restore. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `TopologySafetyTests` to use its existing endpoint, state or callback context.

- `TopologySafetyTests.test_no_overlap_reason_reports_both_newest_physical_dates` (function/method, line 48): Regression assertion: no overlap reason reports both newest physical dates. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `TopologySafetyTests` to use its existing endpoint, state or callback context.

- `TopologySafetyTests.test_restore_pull_and_push_endpoint_descriptions_are_directional` (function/method, line 82): Regression assertion: restore pull and push endpoint descriptions are directional. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `TopologySafetyTests` to use its existing endpoint, state or callback context.

## `tests/test_transfer_accounting.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `TransferAccountingTests` (class, line 10): Groups TransferAccounting regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `TransferAccountingTests.test_parse_mbuffer_final_summary` (function/method, line 11): Regression assertion: parse mbuffer final summary. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `TransferAccountingTests` to use its existing endpoint, state or callback context.

- `TransferAccountingTests.test_parse_mbuffer_progress_total_fallback` (function/method, line 15): Regression assertion: parse mbuffer progress total fallback. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `TransferAccountingTests` to use its existing endpoint, state or callback context.

- `TransferAccountingTests.test_parse_mbuffer_multi_sender_summary` (function/method, line 20): Regression assertion: parse mbuffer multi sender summary. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `TransferAccountingTests` to use its existing endpoint, state or callback context.

- `TransferAccountingTests.test_middle_process_runs_without_controlling_terminal_for_capture` (function/method, line 24): Regression assertion: middle process runs without controlling terminal for capture. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `TransferAccountingTests` to use its existing endpoint, state or callback context.

- `TransferAccountingTests.test_successful_pipeline_returns_mbuffer_byte_total` (function/method, line 41): Regression assertion: successful pipeline returns mbuffer byte total. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `TransferAccountingTests` to use its existing endpoint, state or callback context.

- `TransferAccountingTests._summary` (function/method, line 56): Test support: summary; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `TransferAccountingTests` to use its existing endpoint, state or callback context.

- `TransferAccountingTests.test_sync_summary_sums_all_successful_transfer_bytes` (function/method, line 82): Regression assertion: sync summary sums all successful transfer bytes. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `TransferAccountingTests` to use its existing endpoint, state or callback context.

- `TransferAccountingTests.test_sync_summary_uses_tb_when_large` (function/method, line 87): Regression assertion: sync summary uses tb when large. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `TransferAccountingTests` to use its existing endpoint, state or callback context.

- `TransferAccountingTests.test_sync_summary_reports_unavailable_when_any_actual_size_is_unknown` (function/method, line 90): Regression assertion: sync summary reports unavailable when any actual size is unknown. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `TransferAccountingTests` to use its existing endpoint, state or callback context.

## `tests/test_transfer_size_preflight.py`

**Role:** Regression tests. Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

**Why:** Keeps test fixtures and assertions close to the behavior they verify so regressions can be reproduced without production data.

- `TransferSizeParsingTests` (class, line 26): Groups TransferSizeParsing regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `TransferSizeParsingTests.test_size_parser_uses_binary_suffixes` (function/method, line 27): Regression assertion: size parser uses binary suffixes. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `TransferSizeParsingTests` to use its existing endpoint, state or callback context.

- `TransferSizeParsingTests.test_btrfs_usage_prefers_minimum_free_estimate` (function/method, line 33): Regression assertion: btrfs usage prefers minimum free estimate. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `TransferSizeParsingTests` to use its existing endpoint, state or callback context.

- `TransferSizeParsingTests.test_estimate_summary_parser_reads_ascii_marker` (function/method, line 37): Regression assertion: estimate summary parser reads ascii marker. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `TransferSizeParsingTests` to use its existing endpoint, state or callback context.

- `TransferSizeParsingTests.test_estimate_summary_parser_requires_marker` (function/method, line 43): Regression assertion: estimate summary parser requires marker. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `TransferSizeParsingTests` to use its existing endpoint, state or callback context.

- `ExactTransferMeasurementTests` (class, line 48): Groups ExactTransferMeasurement regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `ExactTransferMeasurementTests._ops` (function/method, line 49): Test support: ops; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ExactTransferMeasurementTests` to use its existing endpoint, state or callback context.

- `ExactTransferMeasurementTests.test_exact_measurement_counts_on_source_endpoint_with_real_send_options` (function/method, line 55): Regression assertion: exact measurement counts on source endpoint with real send options. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ExactTransferMeasurementTests` to use its existing endpoint, state or callback context.

- `ExactTransferMeasurementTests.test_exact_measurement_does_not_hide_failed_btrfs_send_behind_wc` (function/method, line 77): Regression assertion: exact measurement does not hide failed btrfs send behind wc. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `ExactTransferMeasurementTests` to use its existing endpoint, state or callback context.

- `EstimatedTransferMeasurementTests` (class, line 88): Groups EstimatedTransferMeasurement regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `EstimatedTransferMeasurementTests._ops` (function/method, line 89): Test support: ops; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `EstimatedTransferMeasurementTests` to use its existing endpoint, state or callback context.

- `EstimatedTransferMeasurementTests.test_incremental_estimate_uses_parent_specific_no_data_send` (function/method, line 95): Regression assertion: incremental estimate uses parent specific no data send. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `EstimatedTransferMeasurementTests` to use its existing endpoint, state or callback context.

- `EstimatedTransferMeasurementTests.test_estimate_does_not_use_subvolume_exclusive_bytes` (function/method, line 124): Regression assertion: estimate does not use subvolume exclusive bytes. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `EstimatedTransferMeasurementTests` to use its existing endpoint, state or callback context.

- `EstimatedTransferMeasurementTests.test_estimate_does_not_hide_failed_send_behind_dump` (function/method, line 135): Regression assertion: estimate does not hide failed send behind dump. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `EstimatedTransferMeasurementTests` to use its existing endpoint, state or callback context.

- `EstimatedTransferMeasurementTests.test_estimate_reduces_non_utf8_stream_before_python_capture` (function/method, line 150): Regression assertion: estimate reduces non utf8 stream before python capture. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `EstimatedTransferMeasurementTests` to use its existing endpoint, state or callback context.

- `EstimatedTransferMeasurementTests.test_estimate_detects_failed_dump_stage` (function/method, line 176): Regression assertion: estimate detects failed dump stage. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `EstimatedTransferMeasurementTests` to use its existing endpoint, state or callback context.

- `EstimatedTransferMeasurementTests.test_destination_free_space_uses_btrfs_estimated_lower_bound` (function/method, line 190): Regression assertion: destination free space uses btrfs estimated lower bound. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `EstimatedTransferMeasurementTests` to use its existing endpoint, state or callback context.

- `TransferSizeConfigTests` (class, line 200): Groups TransferSizeConfig regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `TransferSizeConfigTests._base_config` (function/method, line 201): Test support: base config; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `TransferSizeConfigTests` to use its existing endpoint, state or callback context.

- `TransferSizeConfigTests.test_requested_transfer_size_options_load` (function/method, line 217): Regression assertion: requested transfer size options load. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `TransferSizeConfigTests` to use its existing endpoint, state or callback context.

- `TransferSizeConfigTests.test_transfer_size_defaults_are_disabled_and_estimate` (function/method, line 226): Regression assertion: transfer size defaults are disabled and estimate. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `TransferSizeConfigTests` to use its existing endpoint, state or callback context.

- `TransferSizeConfigTests.test_invalid_mode_is_rejected` (function/method, line 245): Regression assertion: invalid mode is rejected. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `TransferSizeConfigTests` to use its existing endpoint, state or callback context.

- `TransferSizeConfigTests.test_invalid_margin_is_rejected` (function/method, line 252): Regression assertion: invalid margin is rejected. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `TransferSizeConfigTests` to use its existing endpoint, state or callback context.

- `SyncCapacityGateTests` (class, line 260): Groups SyncCapacityGate regression cases and their isolated fixtures. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed.

- `SyncCapacityGateTests._config` (function/method, line 261): Test support: config; prepares, simulates or formats the isolated data used by these regression cases. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SyncCapacityGateTests` to use its existing endpoint, state or callback context.

- `SyncCapacityGateTests.test_capacity_gate_allows_stream_plus_margin_that_fits` (function/method, line 272): Regression assertion: capacity gate allows stream plus margin that fits. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SyncCapacityGateTests` to use its existing endpoint, state or callback context.

- `SyncCapacityGateTests.test_capacity_gate_refuses_before_receive_when_stream_plus_margin_does_not_fit` (function/method, line 293): Regression assertion: capacity gate refuses before receive when stream plus margin does not fit. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SyncCapacityGateTests` to use its existing endpoint, state or callback context.

- `SyncCapacityGateTests.test_estimate_capacity_gate_refuses_when_changed_extents_plus_margin_do_not_fit` (function/method, line 315): Regression assertion: estimate capacity gate refuses when changed extents plus margin do not fit. **Why:** Preserves regression coverage for the stated behavior; fixtures simulate commands or use temporary data so production snapshots are not needed. Scoped within `SyncCapacityGateTests` to use its existing endpoint, state or callback context.

## `timeshift_btrfs_sync/__init__.py`

**Role:** Current source/build entry. Timeshift Btrfs sync package.

**Why:** Exposes the release version through a minimal package entry point.

No function or class definitions. The module exposes metadata or invokes the existing CLI entry point.

## `timeshift_btrfs_sync/__main__.py`

**Role:** Current source/build entry. Run the CLI with: python -m timeshift_btrfs_sync.

**Why:** Makes python -m timeshift_btrfs_sync invoke the same CLI as the installed ts-btrfs command.

No function or class definitions. The module exposes metadata or invokes the existing CLI entry point.

## `timeshift_btrfs_sync/btrfs_ops.py`

**Role:** Current source/build entry. Reusable Btrfs operations independent of workflow order.

**Why:** Centralizes Btrfs command syntax, exact-path metadata and numeric containment so local and SSH workflows apply the same UUID and deletion checks.

- `_ListedSubvolume` (class, line 24): One numeric containment record from ``btrfs subvolume list -a -p``. **Why:** Centralizes Btrfs command syntax, exact-path metadata and numeric containment so local and SSH workflows apply the same UUID and deletion checks.

- `_parse_listed_subvolumes` (function/method, line 32): Parse numeric ID, containing-parent ID, and raw path fields. **Why:** Centralizes Btrfs command syntax, exact-path metadata and numeric containment so local and SSH workflows apply the same UUID and deletion checks.

- `_descendant_list_paths` (function/method, line 56): Return only numeric descendants of ``root_id`` from one full list. **Why:** Centralizes Btrfs command syntax, exact-path metadata and numeric containment so local and SSH workflows apply the same UUID and deletion checks.

- `clean_uuid` (function/method, line 73): Strip whitespace and convert empty or dash UUID fields to None. **Why:** Centralizes Btrfs command syntax, exact-path metadata and numeric containment so local and SSH workflows apply the same UUID and deletion checks.

- `parse_subvolume_show` (function/method, line 78): Parse UUID and read-only fields from ``btrfs subvolume show``. **Why:** Centralizes Btrfs command syntax, exact-path metadata and numeric containment so local and SSH workflows apply the same UUID and deletion checks.

- `BtrfsOps` (class, line 104): Btrfs command facade for one local or source endpoint. **Why:** Centralizes Btrfs command syntax, exact-path metadata and numeric containment so local and SSH workflows apply the same UUID and deletion checks.

- `BtrfsOps.prefix` (property, line 112): Combine the configured sudo prefix with the Btrfs executable. **Why:** Centralizes Btrfs command syntax, exact-path metadata and numeric containment so local and SSH workflows apply the same UUID and deletion checks. Scoped within `BtrfsOps` to use its existing endpoint, state or callback context.

- `BtrfsOps.argv` (function/method, line 115): Append operation arguments to the common Btrfs command prefix. **Why:** Centralizes Btrfs command syntax, exact-path metadata and numeric containment so local and SSH workflows apply the same UUID and deletion checks. Scoped within `BtrfsOps` to use its existing endpoint, state or callback context.

- `BtrfsOps.run` (function/method, line 118): Execute Btrfs argv through the selected endpoint and propagate logging/check controls. **Why:** Centralizes Btrfs command syntax, exact-path metadata and numeric containment so local and SSH workflows apply the same UUID and deletion checks. Scoped within `BtrfsOps` to use its existing endpoint, state or callback context.

- `BtrfsOps.meta` (function/method, line 133): Return exact-path subvolume metadata or ``None`` for an optional miss. **Why:** Centralizes Btrfs command syntax, exact-path metadata and numeric containment so local and SSH workflows apply the same UUID and deletion checks. Scoped within `BtrfsOps` to use its existing endpoint, state or callback context.

- `BtrfsOps.list_children` (function/method, line 152): Return all descendants selected from one Btrfs containment graph. **Why:** Centralizes Btrfs command syntax, exact-path metadata and numeric containment so local and SSH workflows apply the same UUID and deletion checks. Scoped within `BtrfsOps` to use its existing endpoint, state or callback context.

- `BtrfsOps.create` (function/method, line 171): Create a Btrfs subvolume at the exact requested path. **Why:** Centralizes Btrfs command syntax, exact-path metadata and numeric containment so local and SSH workflows apply the same UUID and deletion checks. Scoped within `BtrfsOps` to use its existing endpoint, state or callback context.

- `BtrfsOps.snapshot` (function/method, line 174): Create one exact writable or read-only Btrfs snapshot. **Why:** Centralizes Btrfs command syntax, exact-path metadata and numeric containment so local and SSH workflows apply the same UUID and deletion checks. Scoped within `BtrfsOps` to use its existing endpoint, state or callback context.

- `BtrfsOps.delete` (function/method, line 190): Delete one exact Btrfs subvolume through the common command wrapper. **Why:** Centralizes Btrfs command syntax, exact-path metadata and numeric containment so local and SSH workflows apply the same UUID and deletion checks. Scoped within `BtrfsOps` to use its existing endpoint, state or callback context.

- `BtrfsOps.send_argv` (function/method, line 205): Return source-endpoint argv for one full or incremental Btrfs send. **Why:** Centralizes Btrfs command syntax, exact-path metadata and numeric containment so local and SSH workflows apply the same UUID and deletion checks. Scoped within `BtrfsOps` to use its existing endpoint, state or callback context.

- `BtrfsOps.send_command` (function/method, line 228): Return local process argv that executes one send on this endpoint. **Why:** Centralizes Btrfs command syntax, exact-path metadata and numeric containment so local and SSH workflows apply the same UUID and deletion checks. Scoped within `BtrfsOps` to use its existing endpoint, state or callback context.

- `BtrfsOps.receive_command` (function/method, line 249): Build endpoint process argv for Btrfs receive, including optional verbosity. **Why:** Centralizes Btrfs command syntax, exact-path metadata and numeric containment so local and SSH workflows apply the same UUID and deletion checks. Scoped within `BtrfsOps` to use its existing endpoint, state or callback context.

- `BtrfsOps.set_readonly` (function/method, line 256): Set the Btrfs subvolume read-only property explicitly. **Why:** Centralizes Btrfs command syntax, exact-path metadata and numeric containment so local and SSH workflows apply the same UUID and deletion checks. Scoped within `BtrfsOps` to use its existing endpoint, state or callback context.

- `BtrfsOps.batch_delete` (function/method, line 261): Delete exact paths in one endpoint command and validate confirmations. **Why:** Centralizes Btrfs command syntax, exact-path metadata and numeric containment so local and SSH workflows apply the same UUID and deletion checks. Scoped within `BtrfsOps` to use its existing endpoint, state or callback context.

## `timeshift_btrfs_sync/cache_ops.py`

**Role:** Current source/build entry. Single source send-cache operation used by sync and recovery.

**Why:** Keeps cache ownership, read-only status and Parent UUID proof together so writable Timeshift originals can be sent without being changed or creating nested cache snapshots.

- `_safe_name` (function/method, line 14): Reject empty names, dot components and slashes before joining cache path components. **Why:** Keeps cache ownership, read-only status and Parent UUID proof together so writable Timeshift originals can be sent without being changed or creating nested cache snapshots.

- `cache_parent_path` (function/method, line 20): Join a validated snapshot name below the configured cache root. **Why:** Keeps cache ownership, read-only status and Parent UUID proof together so writable Timeshift originals can be sent without being changed or creating nested cache snapshots.

- `cache_child_path` (function/method, line 24): Join a validated subvolume name below its cache date. **Why:** Keeps cache ownership, read-only status and Parent UUID proof together so writable Timeshift originals can be sent without being changed or creating nested cache snapshots.

- `validate_cache_snapshot` (function/method, line 28): Prove an exact cache child is a safe read-only snapshot of ``original``. **Why:** Keeps cache ownership, read-only status and Parent UUID proof together so writable Timeshift originals can be sent without being changed or creating nested cache snapshots.

- `CacheManager` (class, line 61): Ensure exact reusable send snapshots without nested cache creation. **Why:** Keeps cache ownership, read-only status and Parent UUID proof together so writable Timeshift originals can be sent without being changed or creating nested cache snapshots.

- `CacheManager.__init__` (function/method, line 64): Store the shared Btrfs endpoint, cache root and cache-creation policy. **Why:** Keeps cache ownership, read-only status and Parent UUID proof together so writable Timeshift originals can be sent without being changed or creating nested cache snapshots. Scoped within `CacheManager` to use its existing endpoint, state or callback context.

- `CacheManager._ensure_subvolume` (function/method, line 69): Reuse indexed or exact-probed cache containers, create absent Btrfs containers, and reject existing ordinary paths. **Why:** Keeps cache ownership, read-only status and Parent UUID proof together so writable Timeshift originals can be sent without being changed or creating nested cache snapshots. Scoped within `CacheManager` to use its existing endpoint, state or callback context.

- `CacheManager._probe_existing_from_parent` (function/method, line 96): Find one exact cache child from an authoritative parent-scoped list. **Why:** Keeps cache ownership, read-only status and Parent UUID proof together so writable Timeshift originals can be sent without being changed or creating nested cache snapshots. Scoped within `CacheManager` to use its existing endpoint, state or callback context.

- `CacheManager._probe_create_verify` (function/method, line 192): Probe, create if absent, and verify exact cache path in one command. **Why:** Keeps cache ownership, read-only status and Parent UUID proof together so writable Timeshift originals can be sent without being changed or creating nested cache snapshots. Scoped within `CacheManager` to use its existing endpoint, state or callback context.

- `CacheManager._probe_create_verify.meta` (function/method, line 272): Parse a framed probe result into exact cache metadata, or return None when the probe failed. **Why:** Keeps cache ownership, read-only status and Parent UUID proof together so writable Timeshift originals can be sent without being changed or creating nested cache snapshots. Scoped within `CacheManager._probe_create_verify` to use its existing endpoint, state or callback context.

- `CacheManager.ensure_send_snapshot` (function/method, line 305): Return original read-only source or create/reuse one exact cache child. **Why:** Keeps cache ownership, read-only status and Parent UUID proof together so writable Timeshift originals can be sent without being changed or creating nested cache snapshots. Scoped within `CacheManager` to use its existing endpoint, state or callback context.

## `timeshift_btrfs_sync/cli.py`

**Role:** Current source/build entry. Command-line interface for timeshift-btrfs-sync.

**Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `add_version_arg` (function/method, line 39): Expose the installed package version from the top level and every subcommand. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `new_subparser` (function/method, line 50): Create one self-contained command parser with version and troubleshooting help. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `add_config_arg` (function/method, line 73): Add the required TOML --config/-c option consistently to config-based commands. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `add_run_mode_args` (function/method, line 87): Add mutually exclusive --dry-run and --run options with command-specific help. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `add_yes_delete_arg` (function/method, line 93): Add the separate retention deletion authorization flag. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `_load_config_state` (function/method, line 97): Load state and resolve all root-relative paths against this config. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `_failure_exit_code` (function/method, line 103): Return a stable CLI exit code for failure notifications. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `_stderr_tail_for_exception` (function/method, line 119): Return the best available recent stderr text for failure notifications. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `_send_notifications` (function/method, line 129): Send optional MQTT/email status without changing the command exit code. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `_mail_attachment_paths` (function/method, line 169): Return current run log paths for optional email attachment. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `_safe_destroy_log_dir` (function/method, line 179): Return a log directory that will survive a destructive cleanup. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `_with_logging` (function/method, line 220): Run a command with optional logging, notifications, and final summary. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `_with_logging._summary_text` (function/method, line 241): Call the terminal finalizer safely and report formatting failures without hiding the original outcome. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations. Scoped within `_with_logging` to use its existing endpoint, state or callback context.

- `_with_logging._mail_summary_text` (function/method, line 250): Call the mail finalizer safely, falling back to the normal summary. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations. Scoped within `_with_logging` to use its existing endpoint, state or callback context.

- `_with_logging._stage` (function/method, line 259): Stage nonempty final summaries in the log and success-mail streams. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations. Scoped within `_with_logging` to use its existing endpoint, state or callback context.

- `_with_logging._emit_terminal` (function/method, line 263): Emit the final terminal summary after notification handling. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations. Scoped within `_with_logging` to use its existing endpoint, state or callback context.

- `_resolve_dry_run` (function/method, line 324): Prefer explicit --dry-run or --run and otherwise use config.default_dry_run. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `cmd_init_config` (function/method, line 332): Write the selected packaged config profile; refuse overwriting an existing file without --force. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `cmd_test_source` (function/method, line 347): Load config and run source connectivity, Timeshift listing and Btrfs version checks with logging. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `cmd_test_source._run` (function/method, line 350): Test SSH when selected, then run source Timeshift listing and Btrfs version through configured privilege. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations. Scoped within `cmd_test_source` to use its existing endpoint, state or callback context.

- `_refresh_state_metadata_from_timeshift` (function/method, line 368): Refresh mutable state metadata and return the same current Timeshift index. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `cmd_list_snapshots` (function/method, line 377): Report repositories and pair differences using configured storage readers without state writes. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `cmd_list_source` (function/method, line 391): List snapshots on the source machine. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `cmd_list_source._run` (function/method, line 401): Discover and print source snapshots with the requested optional Btrfs verification. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations. Scoped within `cmd_list_source` to use its existing endpoint, state or callback context.

- `_format_cleanup_summary` (function/method, line 414): Return overall retention and separate destination/cache cleanup summaries. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `_format_failed_sync_summary` (function/method, line 484): Return a final sync block when sync failed before a normal summary existed. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `cmd_sync` (function/method, line 501): Reject invalid sync topology, resolve run mode, coordinate the local lock and run shared sync/optional retention with final summaries. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `cmd_sync._final_blocks` (function/method, line 522): Finalize elapsed time and produce transfer, sync and cleanup blocks, including early failures. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations. Scoped within `cmd_sync` to use its existing endpoint, state or callback context.

- `cmd_sync._finalize` (function/method, line 548): Join final terminal blocks in transfer-list, sync-summary, cleanup-summary order. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations. Scoped within `cmd_sync` to use its existing endpoint, state or callback context.

- `cmd_sync._mail_finalize` (function/method, line 552): Place the configured job name and sync/cleanup summaries before the transfer list in mail. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations. Scoped within `cmd_sync` to use its existing endpoint, state or callback context.

- `cmd_sync._run_dry` (function/method, line 566): Run sync and optional retention previews using in-memory state without acquiring a mutation lock. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations. Scoped within `cmd_sync` to use its existing endpoint, state or callback context.

- `cmd_sync._run_locked` (function/method, line 582): Run real sync and requested retention against state while the caller holds the local lock. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations. Scoped within `cmd_sync` to use its existing endpoint, state or callback context.

- `cmd_prune` (function/method, line 613): Refresh current source metadata and apply shared retention under the real-run lock or in preview. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `cmd_prune._run_dry` (function/method, line 617): Refresh state metadata in memory and preview retention without saving or deleting. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations. Scoped within `cmd_prune` to use its existing endpoint, state or callback context.

- `cmd_prune._run_locked` (function/method, line 630): Prepare helper paths, refresh state metadata and execute authorized retention under the local lock. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations. Scoped within `cmd_prune` to use its existing endpoint, state or callback context.

- `cmd_restore` (function/method, line 652): Restore one snapshot or the complete post-common backup chain into Timeshift. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `cmd_restore._run` (function/method, line 658): Pass selection, direction and explicit safety choices to the shared restore_backups workflow. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations. Scoped within `cmd_restore` to use its existing endpoint, state or callback context.

- `cmd_create_manual` (function/method, line 688): Verify source paths, identity and parent viability before requesting an on-demand Timeshift snapshot. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `cmd_create_manual._run` (function/method, line 691): Check source connectivity/paths and identity, then call the existing manual-snapshot creator. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations. Scoped within `cmd_create_manual` to use its existing endpoint, state or callback context.

- `cmd_clear_state` (function/method, line 717): Guardedly remove the configured state_file with normal run logging. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `cmd_clear_state._run` (function/method, line 723): Preview state removal, or hold the existing lock while confirmed state-file removal runs. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations. Scoped within `cmd_clear_state` to use its existing endpoint, state or callback context.

- `cmd_delete_lock` (function/method, line 745): Guardedly remove the configured lock_file if it is stale, with logging. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `cmd_delete_lock._run` (function/method, line 751): Call guarded stale-lock removal with the selected preview and danger confirmation. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations. Scoped within `cmd_delete_lock` to use its existing endpoint, state or callback context.

- `cmd_destroy_leftovers` (function/method, line 762): Destroy configured leftovers with normal run logging enabled. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `cmd_destroy_leftovers._run` (function/method, line 776): Call the shared retirement workflow for only the selected source-cache/destination roots. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations. Scoped within `cmd_destroy_leftovers` to use its existing endpoint, state or callback context.

- `cmd_show_state` (function/method, line 788): Print validated state as JSON or a compact snapshot/tag/subvolume table. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `cmd_show_state._run` (function/method, line 791): Load validated state and print JSON, a compact table or an empty-state message. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations. Scoped within `cmd_show_state` to use its existing endpoint, state or callback context.

- `build_parser` (function/method, line 857): Create the argparse parser and complete command-specific flag help. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

- `main` (function/method, line 1329): Parse and dispatch CLI arguments; translate configuration, lock, runtime and interruption errors to documented exit codes. **Why:** Connects user flags to existing workflow functions, logging and explicit confirmation gates before real operations.

## `timeshift_btrfs_sync/commands.py`

**Role:** Current source/build entry. Shared subprocess helpers.

**Why:** Owns subprocess execution, stream routing, captured diagnostics and successful byte accounting so workflows can distinguish source, buffer and receiver failures.

- `CommandError` (class, line 22): Raised when an external command exits with a non-zero status. **Why:** Owns subprocess execution, stream routing, captured diagnostics and successful byte accounting so workflows can distinguish source, buffer and receiver failures.

- `CommandError.__init__` (function/method, line 25): Retain argv, return code, captured output and individual pipeline-stage diagnostics in one exception. **Why:** Owns subprocess execution, stream routing, captured diagnostics and successful byte accounting so workflows can distinguish source, buffer and receiver failures. Scoped within `CommandError` to use its existing endpoint, state or callback context.

- `Completed` (class, line 51): Captured exit status and text streams for one command. **Why:** Owns subprocess execution, stream routing, captured diagnostics and successful byte accounting so workflows can distinguish source, buffer and receiver failures.

- `PipelineResult` (class, line 60): Successful streaming-pipeline statistics needed by higher-level summaries. **Why:** Owns subprocess execution, stream routing, captured diagnostics and successful byte accounting so workflows can distinguish source, buffer and receiver failures.

- `parse_mbuffer_transferred_bytes` (function/method, line 66): Return the successful byte total reported by mbuffer, when available. **Why:** Owns subprocess execution, stream routing, captured diagnostics and successful byte accounting so workflows can distinguish source, buffer and receiver failures.

- `parse_mbuffer_transferred_bytes.convert` (function/method, line 90): Convert a recognized mbuffer numeric size and unit to bytes; return None for invalid input. **Why:** Owns subprocess execution, stream routing, captured diagnostics and successful byte accounting so workflows can distinguish source, buffer and receiver failures. Scoped within `parse_mbuffer_transferred_bytes` to use its existing endpoint, state or callback context.

- `sudo_prefix` (function/method, line 118): Split a configured sudo prefix into argv parts. **Why:** Owns subprocess execution, stream routing, captured diagnostics and successful byte accounting so workflows can distinguish source, buffer and receiver failures.

- `quote_join` (function/method, line 126): Quote argv parts into one safe remote-shell command string. **Why:** Owns subprocess execution, stream routing, captured diagnostics and successful byte accounting so workflows can distinguish source, buffer and receiver failures.

- `remote_double_quote` (function/method, line 132): Return a shell-safe double-quoted argument for a remote shell command. **Why:** Owns subprocess execution, stream routing, captured diagnostics and successful byte accounting so workflows can distinguish source, buffer and receiver failures.

- `_merged_env` (function/method, line 155): Merge optional child-process environment variables. **Why:** Owns subprocess execution, stream routing, captured diagnostics and successful byte accounting so workflows can distinguish source, buffer and receiver failures.

- `run_local` (function/method, line 165): Run a local command and capture stdout/stderr. **Why:** Owns subprocess execution, stream routing, captured diagnostics and successful byte accounting so workflows can distinguish source, buffer and receiver failures.

- `_start_pipeline_readers` (function/method, line 222): Start tee readers from compact stream routing specs. **Why:** Owns subprocess execution, stream routing, captured diagnostics and successful byte accounting so workflows can distinguish source, buffer and receiver failures.

- `_failed_stderr` (function/method, line 241): Return captured pipeline stderr for streams that belong in failures. **Why:** Owns subprocess execution, stream routing, captured diagnostics and successful byte accounting so workflows can distinguish source, buffer and receiver failures.

- `_log_failed_streams` (function/method, line 247): Copy captured failed pipeline streams to .err. **Why:** Owns subprocess execution, stream routing, captured diagnostics and successful byte accounting so workflows can distinguish source, buffer and receiver failures.

- `stream_pipeline` (function/method, line 259): Stream left command into optional middle command, then right command. **Why:** Owns subprocess execution, stream routing, captured diagnostics and successful byte accounting so workflows can distinguish source, buffer and receiver failures.

## `timeshift_btrfs_sync/config.py`

**Role:** Current source/build entry. TOML configuration loading and validation.

**Why:** Validates the TOML schema before commands interpret paths, credentials or cleanup settings; rejects unknown or incompatible configuration.

- `_reject_unknown_keys` (function/method, line 49): Reject configuration entries that are not part of the current schema. **Why:** Validates the TOML schema before commands interpret paths, credentials or cleanup settings; rejects unknown or incompatible configuration.

- `ManualSnapshotConfig` (class, line 57): Optional source-side Timeshift on-demand snapshot creation and cleanup. **Why:** Validates the TOML schema before commands interpret paths, credentials or cleanup settings; rejects unknown or incompatible configuration.

- `SourceConfig` (class, line 93): Timeshift source/restore-target paths that always share one endpoint. **Why:** Validates the TOML schema before commands interpret paths, credentials or cleanup settings; rejects unknown or incompatible configuration.

- `DestinationConfig` (class, line 144): Backup repository and normal local receive settings. **Why:** Validates the TOML schema before commands interpret paths, credentials or cleanup settings; rejects unknown or incompatible configuration.

- `StreamConfig` (class, line 161): Optional pipeline display/buffering settings. **Why:** Validates the TOML schema before commands interpret paths, credentials or cleanup settings; rejects unknown or incompatible configuration.

- `StreamConfig.command` (function/method, line 189): Return mbuffer command argv or None when disabled. **Why:** Validates the TOML schema before commands interpret paths, credentials or cleanup settings; rejects unknown or incompatible configuration. Scoped within `StreamConfig` to use its existing endpoint, state or callback context.

- `RetentionConfig` (class, line 203): Backup retention counts by Timeshift tag. **Why:** Validates the TOML schema before commands interpret paths, credentials or cleanup settings; rejects unknown or incompatible configuration.

- `RetentionConfig.counts_by_tag` (function/method, line 222): Return retention counts keyed by Timeshift tag letters. **Why:** Validates the TOML schema before commands interpret paths, credentials or cleanup settings; rejects unknown or incompatible configuration. Scoped within `RetentionConfig` to use its existing endpoint, state or callback context.

- `RestoreConfig` (class, line 228): Restore-only transport direction. **Why:** Validates the TOML schema before commands interpret paths, credentials or cleanup settings; rejects unknown or incompatible configuration.

- `RestoreConfig.backup_uses_ssh` (property, line 238): Return True when restore reads the backup repository over SSH. **Why:** Validates the TOML schema before commands interpret paths, credentials or cleanup settings; rejects unknown or incompatible configuration. Scoped within `RestoreConfig` to use its existing endpoint, state or callback context.

- `RestoreConfig.timeshift_uses_ssh` (property, line 244): Return True when snapshot_root and cache_root are on the SSH Timeshift host. **Why:** Validates the TOML schema before commands interpret paths, credentials or cleanup settings; rejects unknown or incompatible configuration. Scoped within `RestoreConfig` to use its existing endpoint, state or callback context.

- `AppConfig` (class, line 251): Complete validated app configuration. **Why:** Validates the TOML schema before commands interpret paths, credentials or cleanup settings; rejects unknown or incompatible configuration.

- `ConfigError` (class, line 270): Raised when the TOML config is invalid. **Why:** Validates the TOML schema before commands interpret paths, credentials or cleanup settings; rejects unknown or incompatible configuration.

- `_table` (function/method, line 273): Read a config section or an empty default and reject values that are not TOML tables. **Why:** Validates the TOML schema before commands interpret paths, credentials or cleanup settings; rejects unknown or incompatible configuration.

- `_optional_str` (function/method, line 279): Return a nonempty string option or None for an absent/blank/non-string optional value. **Why:** Validates the TOML schema before commands interpret paths, credentials or cleanup settings; rejects unknown or incompatible configuration.

- `_positive_int` (function/method, line 282): Accept a positive integer or default and reject nonpositive/invalid values. **Why:** Validates the TOML schema before commands interpret paths, credentials or cleanup settings; rejects unknown or incompatible configuration.

- `_stripped` (function/method, line 289): Read an option/default as stripped text for normalized config handling. **Why:** Validates the TOML schema before commands interpret paths, credentials or cleanup settings; rejects unknown or incompatible configuration.

- `_bool` (function/method, line 292): Validate a section boolean through the shared typed boolean helper. **Why:** Validates the TOML schema before commands interpret paths, credentials or cleanup settings; rejects unknown or incompatible configuration.

- `_int` (function/method, line 295): Validate a section count through the shared nonnegative integer helper. **Why:** Validates the TOML schema before commands interpret paths, credentials or cleanup settings; rejects unknown or incompatible configuration.

- `_as_str` (function/method, line 298): Require a nonempty string and include the field name in validation errors. **Why:** Validates the TOML schema before commands interpret paths, credentials or cleanup settings; rejects unknown or incompatible configuration.

- `_as_path` (function/method, line 303): Validate nonempty path text and expand the local user-home shortcut. **Why:** Validates the TOML schema before commands interpret paths, credentials or cleanup settings; rejects unknown or incompatible configuration.

- `_as_bool` (function/method, line 306): Use the default for None and otherwise require an actual boolean. **Why:** Validates the TOML schema before commands interpret paths, credentials or cleanup settings; rejects unknown or incompatible configuration.

- `_as_int` (function/method, line 313): Use the default for None and otherwise require a nonnegative integer. **Why:** Validates the TOML schema before commands interpret paths, credentials or cleanup settings; rejects unknown or incompatible configuration.

- `_string_list` (function/method, line 320): Require a list of nonempty strings, or return an empty list when absent. **Why:** Validates the TOML schema before commands interpret paths, credentials or cleanup settings; rejects unknown or incompatible configuration.

- `load_config` (function/method, line 328): Read and validate the current TOML configuration. **Why:** Validates the TOML schema before commands interpret paths, credentials or cleanup settings; rejects unknown or incompatible configuration.

## `timeshift_btrfs_sync/destroy.py`

**Role:** Current source/build entry. Destructive setup retirement using the shared Btrfs tree engine.

**Why:** Retires selected app-owned roots through the shared tree engine while protecting broad paths and requiring explicit confirmations.

- `DestroyResult` (class, line 26): Named wrapper around the shared tree-deletion result. **Why:** Retires selected app-owned roots through the shared tree engine while protecting broad paths and requiring explicit confirmations.

- `_safe_cleanup_path` (function/method, line 33): Require an absolute sufficiently specific path and reject configured broad system roots. **Why:** Retires selected app-owned roots through the shared tree engine while protecting broad paths and requiring explicit confirmations.

- `_confirm_or_raise` (function/method, line 46): Require the exact typed phrase; abort cleanup when it differs. **Why:** Retires selected app-owned roots through the shared tree engine while protecting broad paths and requiring explicit confirmations.

- `_mode_text` (function/method, line 51): Return the exact confirmation phrase for source, destination or combined deletion. **Why:** Retires selected app-owned roots through the shared tree engine while protecting broad paths and requiring explicit confirmations.

- `_load_payload_state` (function/method, line 57): Load optional validated state for payload reporting; return None if it cannot be loaded. **Why:** Retires selected app-owned roots through the shared tree engine while protecting broad paths and requiring explicit confirmations.

- `_result_by_label` (function/method, line 64): Find an existing deletion target result by its endpoint label. **Why:** Retires selected app-owned roots through the shared tree engine while protecting broad paths and requiring explicit confirmations.

- `_print_payload_match` (function/method, line 68): Compare app-cache/direct-send and destination payload counts for combined cleanup reporting. **Why:** Retires selected app-owned roots through the shared tree engine while protecting broad paths and requiring explicit confirmations.

- `_print_result` (function/method, line 87): Print planned or verified cleanup results, remaining paths and errors; real completion requires root-absence proof. **Why:** Retires selected app-owned roots through the shared tree engine while protecting broad paths and requiring explicit confirmations.

- `destroy_leftovers` (function/method, line 118): Plan and execute selected source/destination tree retirement. **Why:** Retires selected app-owned roots through the shared tree engine while protecting broad paths and requiring explicit confirmations.

- `destroy_leftovers.handle` (function/method, line 172): Dispatch each planned destroy action to its shared Btrfs tree operation and collect the named result. **Why:** Retires selected app-owned roots through the shared tree engine while protecting broad paths and requiring explicit confirmations. Scoped within `destroy_leftovers` to use its existing endpoint, state or callback context.

## `timeshift_btrfs_sync/endpoint.py`

**Role:** Current source/build entry. Unified command endpoints for local, Timeshift, and backup operations.

**Why:** Keeps transport selection independent of backup policy so callers reuse identical command operations locally and over SSH.

- `CommandEndpoint` (class, line 19): Execute commands on one local or transported endpoint. **Why:** Keeps transport selection independent of backup policy so callers reuse identical command operations locally and over SSH.

- `CommandEndpoint.for_source` (function/method, line 30): Wrap an existing local/SSH SourceRunner and label the endpoint by its location. **Why:** Keeps transport selection independent of backup policy so callers reuse identical command operations locally and over SSH. Scoped within `CommandEndpoint` to use its existing endpoint, state or callback context.

- `CommandEndpoint.local` (function/method, line 34): Create a direct local command endpoint with a caller-selected label. **Why:** Keeps transport selection independent of backup policy so callers reuse identical command operations locally and over SSH. Scoped within `CommandEndpoint` to use its existing endpoint, state or callback context.

- `CommandEndpoint.location` (property, line 38): Expose the wrapped runner location or local for a direct endpoint. **Why:** Keeps transport selection independent of backup policy so callers reuse identical command operations locally and over SSH. Scoped within `CommandEndpoint` to use its existing endpoint, state or callback context.

- `CommandEndpoint.shell_command` (function/method, line 41): Return a safely quoted shell command for this endpoint. **Why:** Keeps transport selection independent of backup policy so callers reuse identical command operations locally and over SSH. Scoped within `CommandEndpoint` to use its existing endpoint, state or callback context.

- `CommandEndpoint.command` (function/method, line 46): Return process argv for a command executed on this endpoint. **Why:** Keeps transport selection independent of backup policy so callers reuse identical command operations locally and over SSH. Scoped within `CommandEndpoint` to use its existing endpoint, state or callback context.

- `CommandEndpoint.run_argv` (function/method, line 54): Execute one argv command through the endpoint transport. **Why:** Keeps transport selection independent of backup policy so callers reuse identical command operations locally and over SSH. Scoped within `CommandEndpoint` to use its existing endpoint, state or callback context.

- `CommandEndpoint.run_shell` (function/method, line 82): Execute one shell script through the endpoint transport. **Why:** Keeps transport selection independent of backup policy so callers reuse identical command operations locally and over SSH. Scoped within `CommandEndpoint` to use its existing endpoint, state or callback context.

## `timeshift_btrfs_sync/executor.py`

**Role:** Current source/build entry. Generic ordered workflow action executor.

**Why:** Runs ordered pure plans through registered handlers and keeps preview mode from invoking mutation handlers.

- `WorkflowExecutor` (class, line 14): Execute or preview a plan using one handler per action kind. **Why:** Runs ordered pure plans through registered handlers and keeps preview mode from invoking mutation handlers.

- `WorkflowExecutor.execute` (function/method, line 22): Preview ordered actions without calling handlers, or run each registered handler and collect results. **Why:** Runs ordered pure plans through registered handlers and keeps preview mode from invoking mutation handlers. Scoped within `WorkflowExecutor` to use its existing endpoint, state or callback context.

## `timeshift_btrfs_sync/inventory.py`

**Role:** Current source/build entry. Per-run Btrfs subvolume indexes for fewer SSH calls.

**Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory.

- `BtrfsIndex` (class, line 29): In-memory index of Btrfs subvolumes below one root path. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory.

- `BtrfsIndex.add` (function/method, line 40): Add or replace one indexed subvolume. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory. Scoped within `BtrfsIndex` to use its existing endpoint, state or callback context.

- `BtrfsIndex.discard` (function/method, line 53): Remove one path and any known UUID lookup entries for it. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory. Scoped within `BtrfsIndex` to use its existing endpoint, state or callback context.

- `BtrfsIndex.contains` (function/method, line 65): Return True when ``path`` is an indexed subvolume. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory. Scoped within `BtrfsIndex` to use its existing endpoint, state or callback context.

- `BtrfsIndex.meta` (function/method, line 70): Return metadata for ``path`` if it was indexed. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory. Scoped within `BtrfsIndex` to use its existing endpoint, state or callback context.

- `BtrfsIndex.find_send_uuid` (function/method, line 75): Return a subvolume whose Btrfs send-stream identity equals ``uuid``. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory. Scoped within `BtrfsIndex` to use its existing endpoint, state or callback context.

- `BtrfsIndex.remove_tree` (function/method, line 91): Remove a deleted path and all indexed descendants. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory. Scoped within `BtrfsIndex` to use its existing endpoint, state or callback context.

- `SourceInventory` (class, line 101): One coherent source-side Timeshift/Btrfs inventory. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory.

- `SourceInventory.snapshot_names` (property, line 121): Return Timeshift timestamp names in sorted order. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory. Scoped within `SourceInventory` to use its existing endpoint, state or callback context.

- `SourceInventory.meta` (function/method, line 127): Return source metadata from cache first, then snapshot-root index. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory. Scoped within `SourceInventory` to use its existing endpoint, state or callback context.

- `_clean_uuid` (function/method, line 138): Normalize Btrfs UUID fields from list/show output. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory.

- `parse_subvolume_list` (function/method, line 147): Parse ``btrfs subvolume list -u -q -R`` output for one root. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory.

- `parse_subvolume_paths` (function/method, line 178): Return root-scoped absolute paths from ``btrfs subvolume list`` output. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory.

- `_mark_readonly_from_list` (function/method, line 192): Mark indexed paths read-only using one ``btrfs subvolume list -r`` result. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory.

- `build_local_btrfs_index` (function/method, line 208): Build a local Btrfs index with bulk list commands. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory.

- `_remote_bulk_index_script` (function/method, line 256): Return a POSIX shell script that bulk-lists source Btrfs metadata. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory.

- `build_source_btrfs_index` (function/method, line 302): Build a source Btrfs index in SSH or local mode. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory.

- `build_remote_btrfs_index` (function/method, line 334): Build a remote source index using one SSH command. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory.

- `_parse_remote_btrfs_index_result` (function/method, line 366): Parse one remote bulk-index section into a :class:`BtrfsIndex`. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory.

- `_parse_remote_btrfs_index_result.flush_list` (function/method, line 398): Parse accumulated Btrfs list records into the index and clear the framing buffer. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory. Scoped within `_parse_remote_btrfs_index_result` to use its existing endpoint, state or callback context.

- `_parse_remote_btrfs_index_result.flush_readonly` (function/method, line 406): Apply the accumulated read-only list to indexed metadata and clear the framing buffer. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory. Scoped within `_parse_remote_btrfs_index_result` to use its existing endpoint, state or callback context.

- `_remote_source_inventory_script` (function/method, line 466): Return one remote script for Timeshift, info.json, and both Btrfs roots. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory.

- `_extract_snapshot_info_json_frames` (function/method, line 548): Remove and parse the ``cat`` payloads from combined SSH output. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory.

- `_extract_snapshot_info_json_frames.replace` (function/method, line 565): Capture exact successful metadata frames or per-date errors while removing frames from the remaining output. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory. Scoped within `_extract_snapshot_info_json_frames` to use its existing endpoint, state or callback context.

- `_split_remote_source_inventory_output` (function/method, line 582): Split combined output into identity, Timeshift, info.json, and Btrfs sections. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory.

- `_current_process_identity` (function/method, line 655): Return the effective local account name and UID used to read metadata. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory.

- `_read_local_snapshot_info_json` (function/method, line 666): Read all local Timeshift control files without spawning commands. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory.

- `_record_missing_info_json_errors` (function/method, line 693): Record listed Timeshift dates that had no readable control file. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory.

- `build_source_inventory` (function/method, line 707): Build one coherent Timeshift/snapshot/cache source inventory. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory.

- `describe_source_inventory_changes` (function/method, line 830): Return concise human-readable differences between two inventories. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory.

- `describe_source_inventory_changes.compare_index` (function/method, line 843): Compare old/new paths and UUID identities and append labeled inventory differences. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory. Scoped within `describe_source_inventory_changes` to use its existing endpoint, state or callback context.

- `refresh_path` (function/method, line 882): Refresh one exact path through the shared Btrfs operation layer. **Why:** Builds coherent Timeshift, info.json and Btrfs views in bulk so UUID checks and source-change recovery use a consistent per-run inventory.

## `timeshift_btrfs_sync/listing.py`

**Role:** Current source/build entry. Read-only inventory using the configured restricted Btrfs/Timeshift privileges.

**Why:** Reports ordered Timeshift/cache/target observations with the existing restricted Btrfs/Timeshift sudo readers; ordinary JSON/df readers remain unprivileged, fallback origins are labeled and unknown/incomplete results never fabricate transfer or restore safety.

- `SnapshotListingRow` (class, line 26): One physical date, retaining incomplete or inaccessible payloads visibly. **Why:** Reports ordered Timeshift/cache/target observations with the existing restricted Btrfs/Timeshift sudo readers; ordinary JSON/df readers remain unprivileged, fallback origins are labeled and unknown/incomplete results never fabricate transfer or restore safety.

- `SnapshotPairComparison` (class, line 41): Report observed cache/receiver differences without authorizing deletion. **Why:** Reports ordered Timeshift/cache/target observations with the existing restricted Btrfs/Timeshift sudo readers; ordinary JSON/df readers remain unprivileged, fallback origins are labeled and unknown/incomplete results never fabricate transfer or restore safety.

- `SnapshotPairComparison.parity_confirmed` (function/method, line 57): Require enabled, complete inventories and matching UUIDs for every observed date. **Why:** Reports ordered Timeshift/cache/target observations with the existing restricted Btrfs/Timeshift sudo readers; ordinary JSON/df readers remain unprivileged, fallback origins are labeled and unknown/incomplete results never fabricate transfer or restore safety. Scoped within `SnapshotPairComparison` to use its existing endpoint, state or callback context.

- `SnapshotListingSection` (class, line 65): Independent endpoint outcome so one failed side cannot hide the other. **Why:** Reports ordered Timeshift/cache/target observations with the existing restricted Btrfs/Timeshift sudo readers; ordinary JSON/df readers remain unprivileged, fallback origins are labeled and unknown/incomplete results never fabricate transfer or restore safety.

- `_terminal_text` (function/method, line 80): Remove terminal controls and collapse lines in untrusted remote metadata. **Why:** Reports ordered Timeshift/cache/target observations with the existing restricted Btrfs/Timeshift sudo readers; ordinary JSON/df readers remain unprivileged, fallback origins are labeled and unknown/incomplete results never fabricate transfer or restore safety.

- `_snapshot_description` (function/method, line 86): Decode Timeshift's named retention tags without misreading 'hourly' as O/H. **Why:** Reports ordered Timeshift/cache/target observations with the existing restricted Btrfs/Timeshift sudo readers; ordinary JSON/df readers remain unprivileged, fallback origins are labeled and unknown/incomplete results never fabricate transfer or restore safety.

- `_filesystem_space` (function/method, line 120): Read GNU df's available filesystem space without mounting or using sudo. **Why:** Reports ordered Timeshift/cache/target observations with the existing restricted Btrfs/Timeshift sudo readers; ordinary JSON/df readers remain unprivileged, fallback origins are labeled and unknown/incomplete results never fabricate transfer or restore safety.

- `_scan_unprivileged` (function/method, line 138): Reuse ordinary physical discovery, optionally skipping JSON already supplied by Timeshift. **Why:** Reports ordered Timeshift/cache/target observations with the existing restricted Btrfs/Timeshift sudo readers; ordinary JSON/df readers remain unprivileged, fallback origins are labeled and unknown/incomplete results never fabricate transfer or restore safety.

- `_run_batched_commands` (function/method, line 144): Batch captured reads with bounded shell arguments and per-command failure framing. **Why:** Reports ordered Timeshift/cache/target observations with the existing restricted Btrfs/Timeshift sudo readers; ordinary JSON/df readers remain unprivileged, fallback origins are labeled and unknown/incomplete results never fabricate transfer or restore safety.

- `_probe_payloads` (function/method, line 188): Read exact subvolume flags through the same configured Btrfs privilege prefix. **Why:** Reports ordered Timeshift/cache/target observations with the existing restricted Btrfs/Timeshift sudo readers; ordinary JSON/df readers remain unprivileged, fallback origins are labeled and unknown/incomplete results never fabricate transfer or restore safety.

- `_filesystem_identity` (function/method, line 195): Parse filesystem UUID and all device paths from Btrfs filesystem show output. **Why:** Reports ordered Timeshift/cache/target observations with the existing restricted Btrfs/Timeshift sudo readers; ordinary JSON/df readers remain unprivileged, fallback origins are labeled and unknown/incomplete results never fabricate transfer or restore safety.

- `_add_listing_index` (function/method, line 203): Reuse scoped Btrfs parsers and preserve unknown flags when readonly listing fails. **Why:** Reports ordered Timeshift/cache/target observations with the existing restricted Btrfs/Timeshift sudo readers; ordinary JSON/df readers remain unprivileged, fallback origins are labeled and unknown/incomplete results never fabricate transfer or restore safety.

- `_discover_repository` (function/method, line 216): Discover protected dates and nested payloads using only sudo-authorized Btrfs reads. **Why:** Reports ordered Timeshift/cache/target observations with the existing restricted Btrfs/Timeshift sudo readers; ordinary JSON/df readers remain unprivileged, fallback origins are labeled and unknown/incomplete results never fabricate transfer or restore safety.

- `_read_listing_metadata` (function/method, line 256): Read regular info.json as the login user, excluding dates already supplied by Timeshift; never sudo a file reader. **Why:** Reports ordered Timeshift/cache/target observations with the existing restricted Btrfs/Timeshift sudo readers; ordinary JSON/df readers remain unprivileged, fallback origins are labeled and unknown/incomplete results never fabricate transfer or restore safety.

- `_space_with_btrfs_fallback` (function/method, line 276): Keep ordinary df space; use native Btrfs evidence for denied reads or unknown types. **Why:** Reports ordered Timeshift/cache/target observations with the existing restricted Btrfs/Timeshift sudo readers; ordinary JSON/df readers remain unprivileged, fallback origins are labeled and unknown/incomplete results never fabricate transfer or restore safety.

- `_collect_section` (function/method, line 302): Combine Btrfs-authorized discovery with ordinary JSON reads without requiring sudo ls/cat. **Why:** Reports ordered Timeshift/cache/target observations with the existing restricted Btrfs/Timeshift sudo readers; ordinary JSON/df readers remain unprivileged, fallback origins are labeled and unknown/incomplete results never fabricate transfer or restore safety.

- `_set_listing_metadata` (function/method, line 438): Apply a labeled live metadata observation, retaining other diagnostics. **Why:** Reports ordered Timeshift/cache/target observations with the existing restricted Btrfs/Timeshift sudo readers; ordinary JSON/df readers remain unprivileged, fallback origins are labeled and unknown/incomplete results never fabricate transfer or restore safety.

- `_matching_listing_payloads` (function/method, line 445): Require all configured live RO payloads to share send/received UUIDs before borrowing metadata. **Why:** Reports ordered Timeshift/cache/target observations with the existing restricted Btrfs/Timeshift sudo readers; ordinary JSON/df readers remain unprivileged, fallback origins are labeled and unknown/incomplete results never fabricate transfer or restore safety.

- `compare_snapshot_listings` (function/method, line 458): Compare every observed date and reuse full readonly send/Received UUID proof. **Why:** Reports ordered Timeshift/cache/target observations with the existing restricted Btrfs/Timeshift sudo readers; ordinary JSON/df readers remain unprivileged, fallback origins are labeled and unknown/incomplete results never fabricate transfer or restore safety.

- `_format_pair_comparison` (function/method, line 479): Make unequal repositories and unproven pairs visible, without claiming cleanup eligibility. **Why:** Reports ordered Timeshift/cache/target observations with the existing restricted Btrfs/Timeshift sudo readers; ordinary JSON/df readers remain unprivileged, fallback origins are labeled and unknown/incomplete results never fabricate transfer or restore safety.

- `collect_snapshot_listings` (function/method, line 524): Report Timeshift, cache and backup in order using their actual configured local/SSH hosts. **Why:** Reports ordered Timeshift/cache/target observations with the existing restricted Btrfs/Timeshift sudo readers; ordinary JSON/df readers remain unprivileged, fallback origins are labeled and unknown/incomplete results never fabricate transfer or restore safety.

- `format_snapshot_listings` (function/method, line 612): Render Timeshift-style name/tag/description tables and independent df summaries. **Why:** Reports ordered Timeshift/cache/target observations with the existing restricted Btrfs/Timeshift sudo readers; ordinary JSON/df readers remain unprivileged, fallback origins are labeled and unknown/incomplete results never fabricate transfer or restore safety.

## `timeshift_btrfs_sync/lock.py`

**Role:** Current source/build entry. Local advisory file locking for coordinated operations.

**Why:** Coordinates operations on the configured local lock with nonblocking flock so concurrent local workflows cannot proceed together.

- `FileLock` (class, line 10): flock() based non-blocking exclusive lock on the local machine. **Why:** Coordinates operations on the configured local lock with nonblocking flock so concurrent local workflows cannot proceed together.

- `FileLock.__init__` (function/method, line 13): Store the local lock path and initialize its unopened handle. **Why:** Coordinates operations on the configured local lock with nonblocking flock so concurrent local workflows cannot proceed together. Scoped within `FileLock` to use its existing endpoint, state or callback context.

- `FileLock.__enter__` (function/method, line 17): Require the parent directory, open the lock file and acquire nonblocking exclusive flock before marking it locked. **Why:** Coordinates operations on the configured local lock with nonblocking flock so concurrent local workflows cannot proceed together. Scoped within `FileLock` to use its existing endpoint, state or callback context.

- `FileLock.__exit__` (function/method, line 29): Release the advisory lock and close its handle when leaving the context. **Why:** Coordinates operations on the configured local lock with nonblocking flock so concurrent local workflows cannot proceed together. Scoped within `FileLock` to use its existing endpoint, state or callback context.

## `timeshift_btrfs_sync/log.py`

**Role:** Current source/build entry. Split run logging for timeshift-btrfs-sync.

**Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result.

- `RunLogger` (class, line 32): Owns the split log files for one run. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result.

- `RunLogger.__post_init__` (function/method, line 38): Create the log directory and open the run log files. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result. Scoped within `RunLogger` to use its existing endpoint, state or callback context.

- `RunLogger.close` (function/method, line 72): Close all log files, leaving any queued final summary last in .log. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result. Scoped within `RunLogger` to use its existing endpoint, state or callback context.

- `RunLogger.attachment_paths` (function/method, line 84): Return run log files in the order useful for mail attachments. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result. Scoped within `RunLogger` to use its existing endpoint, state or callback context.

- `RunLogger._write` (function/method, line 94): Write text safely from possible stream-reader threads. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result. Scoped within `RunLogger` to use its existing endpoint, state or callback context.

- `RunLogger._remember_stderr` (function/method, line 101): Keep a small tail of stderr for failure notifications. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result. Scoped within `RunLogger` to use its existing endpoint, state or callback context.

- `RunLogger.last_stderr_tail` (function/method, line 109): Return the newest stderr text remembered for MQTT/error reports. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result. Scoped within `RunLogger` to use its existing endpoint, state or callback context.

- `RunLogger._line` (function/method, line 115): Write exactly one logical line. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result. Scoped within `RunLogger` to use its existing endpoint, state or callback context.

- `RunLogger.info` (function/method, line 122): Write a normal status line to .log. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result. Scoped within `RunLogger` to use its existing endpoint, state or callback context.

- `RunLogger.mbuffer` (function/method, line 127): Write one line to the .mbuffer transfer-progress log. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result. Scoped within `RunLogger` to use its existing endpoint, state or callback context.

- `RunLogger.btrfs_out` (function/method, line 132): Write one line to the .btrfs Btrfs verbose-output log. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result. Scoped within `RunLogger` to use its existing endpoint, state or callback context.

- `RunLogger.success` (function/method, line 137): Write one line to the .succes human-readable summary log. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result. Scoped within `RunLogger` to use its existing endpoint, state or callback context.

- `RunLogger.success_text` (function/method, line 142): Write a preformatted block to the .succes summary log. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result. Scoped within `RunLogger` to use its existing endpoint, state or callback context.

- `RunLogger.set_success_text` (function/method, line 149): Replace .succes with the final mail-friendly run summary. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result. Scoped within `RunLogger` to use its existing endpoint, state or callback context.

- `RunLogger.log_text` (function/method, line 165): Write a preformatted block to the normal .log file. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result. Scoped within `RunLogger` to use its existing endpoint, state or callback context.

- `RunLogger.queue_final_log_summary` (function/method, line 172): Queue the final sync/cleanup summary so it is last in .log. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result. Scoped within `RunLogger` to use its existing endpoint, state or callback context.

- `RunLogger.err` (function/method, line 179): Write an error/stderr line to .err and remember its tail. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result. Scoped within `RunLogger` to use its existing endpoint, state or callback context.

- `RunLogger.command` (function/method, line 186): Record a command that is about to run. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result. Scoped within `RunLogger` to use its existing endpoint, state or callback context.

- `RunLogger.completed` (function/method, line 209): Record the output from a normal captured command. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result. Scoped within `RunLogger` to use its existing endpoint, state or callback context.

- `RunLogger.pipeline_commands` (function/method, line 240): Record send/buffer/receive commands to the appropriate logs. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result. Scoped within `RunLogger` to use its existing endpoint, state or callback context.

- `RunLogger.pipeline_summary` (function/method, line 251): Record final pipeline status. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result. Scoped within `RunLogger` to use its existing endpoint, state or callback context.

- `RunLogger.stream_text` (function/method, line 259): Write live pipeline text to terminal and/or split log files. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result. Scoped within `RunLogger` to use its existing endpoint, state or callback context.

- `emit_success_summary` (function/method, line 287): Write a readable summary to the real terminal and .succes only. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result.

- `stage_final_run_summary` (function/method, line 303): Stage final terminal/log text and optional mail-body text before notification. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result.

- `emit_final_terminal_summary` (function/method, line 324): Print the staged final summary after notifications have completed. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result.

- `TeeTextIO` (class, line 333): Terminal stream wrapper that also writes normal app output to run logs. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result.

- `TeeTextIO.__init__` (function/method, line 346): Store the original stream and logger while preserving encoding/error attributes. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result. Scoped within `TeeTextIO` to use its existing endpoint, state or callback context.

- `TeeTextIO.write` (function/method, line 353): Mirror text to the terminal and the selected normal/error log stream. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result. Scoped within `TeeTextIO` to use its existing endpoint, state or callback context.

- `TeeTextIO.flush` (function/method, line 366): Flush the underlying terminal stream. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result. Scoped within `TeeTextIO` to use its existing endpoint, state or callback context.

- `TeeTextIO.isatty` (function/method, line 369): Forward terminal detection to the underlying stream. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result. Scoped within `TeeTextIO` to use its existing endpoint, state or callback context.

- `TeeTextIO.fileno` (function/method, line 372): Expose the original stream file descriptor for compatible consumers. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result. Scoped within `TeeTextIO` to use its existing endpoint, state or callback context.

- `TeeTextIO.writable` (function/method, line 375): Advertise that the tee wrapper accepts text writes. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result. Scoped within `TeeTextIO` to use its existing endpoint, state or callback context.

- `TeeTextIO.__getattr__` (function/method, line 378): Delegate other stream attributes to the original stream. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result. Scoped within `TeeTextIO` to use its existing endpoint, state or callback context.

- `terminal_stdout` (function/method, line 386): Return the real terminal stdout, bypassing the run-log tee wrapper. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result.

- `terminal_stderr` (function/method, line 392): Return the real terminal stderr, bypassing the run-log tee wrapper. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result.

- `get_logger` (function/method, line 400): Return the active logger, if file logging is enabled. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result.

- `active_logger` (function/method, line 407): Temporarily install a run logger and tee app output to files. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result.

- `create_run_logger` (function/method, line 443): Create a logger when log_dir is configured; otherwise return None. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result.

- `tee_pipe_to_log` (function/method, line 465): Start a thread that reads bytes from a process pipe and logs them live. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result.

- `tee_pipe_to_log._reader` (function/method, line 484): Read pipe chunks in a background thread, capture/log them and optionally mirror them without blocking the streaming pipeline. **Why:** Routes normal output, errors, Btrfs/mbuffer streams and final summaries to separate files without changing the workflow result. Scoped within `tee_pipe_to_log` to use its existing endpoint, state or callback context.

## `timeshift_btrfs_sync/mail.py`

**Role:** Current source/build entry. Optional email notifications for timeshift-btrfs-sync.

**Why:** Formats and sends optional status mail with bounded attachments while preserving the underlying backup outcome.

- `MailConfig` (class, line 20): SMTP settings for optional email notifications. **Why:** Formats and sends optional status mail with bounded attachments while preserving the underlying backup outcome.

- `MailConfig.resolved_password` (function/method, line 52): Return password from config value or password_file. **Why:** Formats and sends optional status mail with bounded attachments while preserving the underlying backup outcome. Scoped within `MailConfig` to use its existing endpoint, state or callback context.

- `_subject` (function/method, line 61): Create a short readable subject line. **Why:** Formats and sends optional status mail with bounded attachments while preserving the underlying backup outcome.

- `_body` (function/method, line 72): Create a fallback plain-text email body from the status payload. **Why:** Formats and sends optional status mail with bounded attachments while preserving the underlying backup outcome.

- `_success_body_from_paths` (function/method, line 101): Return the text content of the non-empty .succes file, if present. **Why:** Formats and sends optional status mail with bounded attachments while preserving the underlying backup outcome.

- `_filter_attachments` (function/method, line 118): Return existing attachment paths and human-readable skipped reasons. **Why:** Formats and sends optional status mail with bounded attachments while preserving the underlying backup outcome.

- `_attach_file` (function/method, line 148): Attach one file to an EmailMessage. **Why:** Formats and sends optional status mail with bounded attachments while preserving the underlying backup outcome.

- `send_status` (function/method, line 159): Send one optional SMTP status email. **Why:** Formats and sends optional status mail with bounded attachments while preserving the underlying backup outcome.

## `timeshift_btrfs_sync/maintenance.py`

**Role:** Current source/build entry. Guarded maintenance commands for state and lock files.

**Why:** Restricts state/lock cleanup to exact configured files, verifies their shape and requires confirmations before removal.

- `_confirm_or_raise` (function/method, line 21): Require an exact typed confirmation before destructive maintenance. **Why:** Restricts state/lock cleanup to exact configured files, verifies their shape and requires confirmations before removal.

- `_safe_configured_file` (function/method, line 29): Return a normalized configured file path or raise for unsafe targets. **Why:** Restricts state/lock cleanup to exact configured files, verifies their shape and requires confirmations before removal.

- `_looks_like_state_file` (function/method, line 44): Return True when an existing file appears to be ts-btrfs state. **Why:** Restricts state/lock cleanup to exact configured files, verifies their shape and requires confirmations before removal.

- `_looks_like_lock_file` (function/method, line 63): Return True when an existing file looks like this app's simple lock file. **Why:** Restricts state/lock cleanup to exact configured files, verifies their shape and requires confirmations before removal.

- `_print_header` (function/method, line 77): Print the common maintenance command warning block. **Why:** Restricts state/lock cleanup to exact configured files, verifies their shape and requires confirmations before removal.

- `_require_real_confirmation` (function/method, line 90): Require real-mode flags and typed confirmations. **Why:** Restricts state/lock cleanup to exact configured files, verifies their shape and requires confirmations before removal.

- `clear_state_file` (function/method, line 110): Remove the configured state.json file after explicit confirmation. **Why:** Restricts state/lock cleanup to exact configured files, verifies their shape and requires confirmations before removal.

- `delete_lock_file` (function/method, line 160): Delete the configured lock file when no running process holds it. **Why:** Restricts state/lock cleanup to exact configured files, verifies their shape and requires confirmations before removal.

## `timeshift_btrfs_sync/models.py`

**Role:** Current source/build entry. Shared dataclasses for snapshots and subvolumes.

**Why:** Provides shared snapshot identities and tag formatting so inventory, state, planning and workflows interpret the same data.

- `SubvolumeMeta` (class, line 9): Metadata for one Btrfs subvolume inside one Timeshift snapshot. **Why:** Provides shared snapshot identities and tag formatting so inventory, state, planning and workflows interpret the same data.

- `send_stream_uuid` (function/method, line 21): Return the UUID identity carried when ``meta`` is sent by Btrfs. **Why:** Provides shared snapshot identities and tag formatting so inventory, state, planning and workflows interpret the same data.

- `SnapshotMeta` (class, line 35): Metadata for one Timeshift snapshot. **Why:** Provides shared snapshot identities and tag formatting so inventory, state, planning and workflows interpret the same data.

- `SnapshotMeta.sort_key` (function/method, line 45): Timeshift timestamp names sort oldest-to-newest lexically. **Why:** Provides shared snapshot identities and tag formatting so inventory, state, planning and workflows interpret the same data. Scoped within `SnapshotMeta` to use its existing endpoint, state or callback context.

- `tags_text` (function/method, line 51): Return compact human text for Timeshift tags. **Why:** Provides shared snapshot identities and tag formatting so inventory, state, planning and workflows interpret the same data.

## `timeshift_btrfs_sync/mqtt.py`

**Role:** Current source/build entry. Optional MQTT notifications for timeshift-btrfs-sync.

**Why:** Publishes optional JSON status through a lazily imported MQTT dependency so installations without MQTT remain usable.

- `MQTTConfig` (class, line 19): MQTT broker and publish settings. **Why:** Publishes optional JSON status through a lazily imported MQTT dependency so installations without MQTT remain usable.

- `MQTTConfig.resolved_password` (function/method, line 41): Return password from config value or password_file. **Why:** Publishes optional JSON status through a lazily imported MQTT dependency so installations without MQTT remain usable. Scoped within `MQTTConfig` to use its existing endpoint, state or callback context.

- `publish_status` (function/method, line 51): Publish one JSON MQTT status message. **Why:** Publishes optional JSON status through a lazily imported MQTT dependency so installations without MQTT remain usable.

## `timeshift_btrfs_sync/notify.py`

**Role:** Current source/build entry. Shared notification payload helpers.

**Why:** Builds a consistent status payload for both mail and MQTT so outcome reporting cannot drift between channels.

- `utc_timestamp` (function/method, line 10): Return a compact ISO-8601 UTC timestamp for notifications. **Why:** Builds a consistent status payload for both mail and MQTT so outcome reporting cannot drift between channels.

- `build_notification_payload` (function/method, line 16): Build the shared status payload used by MQTT and email. **Why:** Builds a consistent status payload for both mail and MQTT so outcome reporting cannot drift between channels.

## `timeshift_btrfs_sync/paths.py`

**Role:** Current source/build entry. Canonical path normalization and containment rules.

**Why:** Centralizes POSIX normalization, symlink-aware local containment and mount-aware Btrfs path mapping to keep ownership guards consistent.

- `normalize_source_path` (function/method, line 13): Normalize POSIX path text while preserving an intentionally empty value. **Why:** Centralizes POSIX normalization, symlink-aware local containment and mount-aware Btrfs path mapping to keep ownership guards consistent.

- `is_same_or_under` (function/method, line 23): Return true when ``path`` equals ``root`` or is below it. **Why:** Centralizes POSIX normalization, symlink-aware local containment and mount-aware Btrfs path mapping to keep ownership guards consistent.

- `is_local_same_or_under` (function/method, line 35): Return true when one local path resolves to ``root`` or below it. **Why:** Centralizes POSIX normalization, symlink-aware local containment and mount-aware Btrfs path mapping to keep ownership guards consistent.

- `is_under` (function/method, line 55): Return true only when ``path`` is strictly below ``root``. **Why:** Centralizes POSIX normalization, symlink-aware local containment and mount-aware Btrfs path mapping to keep ownership guards consistent.

- `listed_path_to_absolute` (function/method, line 67): Resolve one Btrfs-list path below a mounted root. **Why:** Centralizes POSIX normalization, symlink-aware local containment and mount-aware Btrfs path mapping to keep ownership guards consistent.

- `sort_deepest_first` (function/method, line 115): Deduplicate and order paths for child-before-parent deletion. **Why:** Centralizes POSIX normalization, symlink-aware local containment and mount-aware Btrfs path mapping to keep ownership guards consistent.

## `timeshift_btrfs_sync/payload_stats.py`

**Role:** Current source/build entry. Normalized source/destination payload statistics for Btrfs snapshot trees.

**Why:** Compares source-cache/direct-send and destination payload inventories so destructive cleanup reports explain what the selected trees contain.

- `PayloadTreeStats` (class, line 30): Normalized payload/container counts for one source or destination tree. **Why:** Compares source-cache/direct-send and destination payload inventories so destructive cleanup reports explain what the selected trees contain.

- `PayloadTreeStats.total_payload` (property, line 47): Return the number of real cached/received payload subvolumes. **Why:** Compares source-cache/direct-send and destination payload inventories so destructive cleanup reports explain what the selected trees contain. Scoped within `PayloadTreeStats` to use its existing endpoint, state or callback context.

- `PayloadTreeStats.total_cache_payload` (property, line 53): Return how many source payloads came from app-owned source cache. **Why:** Compares source-cache/direct-send and destination payload inventories so destructive cleanup reports explain what the selected trees contain. Scoped within `PayloadTreeStats` to use its existing endpoint, state or callback context.

- `PayloadTreeStats.total_direct_payload` (property, line 59): Return how many source payloads came from protected Timeshift originals. **Why:** Compares source-cache/direct-send and destination payload inventories so destructive cleanup reports explain what the selected trees contain. Scoped within `PayloadTreeStats` to use its existing endpoint, state or callback context.

- `normalize_path` (function/method, line 65): Normalize paths so source/destination comparisons ignore trailing slashes. **Why:** Compares source-cache/direct-send and destination payload inventories so destructive cleanup reports explain what the selected trees contain.

- `_relative_parts` (function/method, line 71): Return path parts relative to root, or None if path is outside root. **Why:** Compares source-cache/direct-send and destination payload inventories so destructive cleanup reports explain what the selected trees contain.

- `_recount_payload` (function/method, line 85): Rebuild per-subvolume counters from the normalized payload set. **Why:** Compares source-cache/direct-send and destination payload inventories so destructive cleanup reports explain what the selected trees contain.

- `_add_payload` (function/method, line 93): Add a payload entry when relative parts end in a configured subvolume name. **Why:** Compares source-cache/direct-send and destination payload inventories so destructive cleanup reports explain what the selected trees contain.

- `source_send_cache_stats` (function/method, line 106): Classify source send-cache subvolumes into payload and helper counts. **Why:** Compares source-cache/direct-send and destination payload inventories so destructive cleanup reports explain what the selected trees contain.

- `destination_payload_stats` (function/method, line 129): Classify destination target subvolumes into received payload counts. **Why:** Compares source-cache/direct-send and destination payload inventories so destructive cleanup reports explain what the selected trees contain.

- `direct_send_payload_stats` (function/method, line 152): Return payload entries streamed directly from protected Timeshift originals. **Why:** Compares source-cache/direct-send and destination payload inventories so destructive cleanup reports explain what the selected trees contain.

- `merge_source_payload_stats` (function/method, line 184): Merge app-cache and protected direct-send payload into one source view. **Why:** Compares source-cache/direct-send and destination payload inventories so destructive cleanup reports explain what the selected trees contain.

- `PayloadMatchStats` (class, line 207): Comparison between source send payload and destination received payload. **Why:** Compares source-cache/direct-send and destination payload inventories so destructive cleanup reports explain what the selected trees contain.

- `PayloadMatchStats.source_only` (property, line 214): Return source payload entries not present on the destination. **Why:** Compares source-cache/direct-send and destination payload inventories so destructive cleanup reports explain what the selected trees contain. Scoped within `PayloadMatchStats` to use its existing endpoint, state or callback context.

- `PayloadMatchStats.destination_only` (property, line 220): Return destination payload entries not present on the source side. **Why:** Compares source-cache/direct-send and destination payload inventories so destructive cleanup reports explain what the selected trees contain. Scoped within `PayloadMatchStats` to use its existing endpoint, state or callback context.

- `PayloadMatchStats.ok` (property, line 226): Return True when source send payload and destination payload match. **Why:** Compares source-cache/direct-send and destination payload inventories so destructive cleanup reports explain what the selected trees contain. Scoped within `PayloadMatchStats` to use its existing endpoint, state or callback context.

- `compare_payloads` (function/method, line 232): Return normalized source/destination payload comparison stats. **Why:** Compares source-cache/direct-send and destination payload inventories so destructive cleanup reports explain what the selected trees contain.

- `_format_count_line` (function/method, line 238): Return an aligned summary line. **Why:** Compares source-cache/direct-send and destination payload inventories so destructive cleanup reports explain what the selected trees contain.

- `render_payload_match` (function/method, line 244): Render the source/destination payload comparison block. **Why:** Compares source-cache/direct-send and destination payload inventories so destructive cleanup reports explain what the selected trees contain.

## `timeshift_btrfs_sync/planning.py`

**Role:** Current source/build entry. Pure workflow planning from a combined backup inventory.

**Why:** Describes workflow intent without executing commands, preserving chronological transfer and safe source/destination/cache/state action order.

- `ActionKind` (class, line 17): Enumerate supported workflow operations so plans and handler dispatch agree on action identity. **Why:** Describes workflow intent without executing commands, preserving chronological transfer and safe source/destination/cache/state action order.

- `WorkflowAction` (class, line 29): Represent one immutable action with its kind, snapshot/subvolume identity and operation payload. **Why:** Describes workflow intent without executing commands, preserving chronological transfer and safe source/destination/cache/state action order.

- `WorkflowPlan` (class, line 37): Collect the named ordered action queue used by real execution or preview. **Why:** Describes workflow intent without executing commands, preserving chronological transfer and safe source/destination/cache/state action order.

- `WorkflowPlan.add` (function/method, line 41): Append one typed action with snapshot/subvolume identity and payload and return that action. **Why:** Describes workflow intent without executing commands, preserving chronological transfer and safe source/destination/cache/state action order. Scoped within `WorkflowPlan` to use its existing endpoint, state or callback context.

- `plan_sync_queue` (function/method, line 53): Plan the oldest-to-newest sync queue without executing operations. **Why:** Describes workflow intent without executing commands, preserving chronological transfer and safe source/destination/cache/state action order.

- `plan_snapshot_recovery` (function/method, line 80): Plan one whole-date recovery in cache, destination, then state order. **Why:** Describes workflow intent without executing commands, preserving chronological transfer and safe source/destination/cache/state action order.

- `plan_prune_snapshot` (function/method, line 90): Plan one retention deletion in source/destination/cache/state order. **Why:** Describes workflow intent without executing commands, preserving chronological transfer and safe source/destination/cache/state action order.

- `plan_destroy_targets` (function/method, line 118): Plan named endpoint/root destruction in the caller-provided order. **Why:** Describes workflow intent without executing commands, preserving chronological transfer and safe source/destination/cache/state action order.

## `timeshift_btrfs_sync/preflight.py`

**Role:** Current source/build entry. Sync path preflight checks.

**Why:** Checks protected Timeshift paths, managed Btrfs roots and helper/lock paths before mutation while keeping strict sync previews from creating them.

- `PathPreflightError` (class, line 44): Raised before any destructive/creating sync work when required paths fail. **Why:** Checks protected Timeshift paths, managed Btrfs roots and helper/lock paths before mutation while keeping strict sync previews from creating them.

- `PathCheck` (class, line 49): One configured path availability result. **Why:** Checks protected Timeshift paths, managed Btrfs roots and helper/lock paths before mutation while keeping strict sync previews from creating them.

- `_shell_words` (function/method, line 60): Return a shell-safe string for configured command-prefix words. **Why:** Checks protected Timeshift paths, managed Btrfs roots and helper/lock paths before mutation while keeping strict sync previews from creating them.

- `_parse_path_check_output` (function/method, line 66): Parse source-path preflight sentinel lines into structured checks. **Why:** Checks protected Timeshift paths, managed Btrfs roots and helper/lock paths before mutation while keeping strict sync previews from creating them.

- `_source_snapshot_root_script` (function/method, line 99): Build a source script that validates Timeshift-owned source.snapshot_root. **Why:** Checks protected Timeshift paths, managed Btrfs roots and helper/lock paths before mutation while keeping strict sync previews from creating them.

- `_cache_root_check_script` (function/method, line 167): Build a source script that validates or creates source.cache_root. **Why:** Checks protected Timeshift paths, managed Btrfs roots and helper/lock paths before mutation while keeping strict sync previews from creating them.

- `_combined_source_path_check_script` (function/method, line 243): Run both source-root preflight checks inside one source command. **Why:** Checks protected Timeshift paths, managed Btrfs roots and helper/lock paths before mutation while keeping strict sync previews from creating them.

- `_source_path_checks` (function/method, line 275): Check/create both source roots with at most one SSH command. **Why:** Checks protected Timeshift paths, managed Btrfs roots and helper/lock paths before mutation while keeping strict sync previews from creating them.

- `_parent_of_path` (function/method, line 354): Return the immediate parent path used for exact-path creation checks. **Why:** Checks protected Timeshift paths, managed Btrfs roots and helper/lock paths before mutation while keeping strict sync previews from creating them.

- `_local_btrfs_result` (function/method, line 361): Run one local destination sudo+btrfs command for preflight checks. **Why:** Checks protected Timeshift paths, managed Btrfs roots and helper/lock paths before mutation while keeping strict sync previews from creating them.

- `_compact_process_error` (function/method, line 373): Return compact stderr/stdout text from a failed subprocess. **Why:** Checks protected Timeshift paths, managed Btrfs roots and helper/lock paths before mutation while keeping strict sync previews from creating them.

- `_compact_os_error` (function/method, line 380): Return compact text for local filesystem creation errors. **Why:** Checks protected Timeshift paths, managed Btrfs roots and helper/lock paths before mutation while keeping strict sync previews from creating them.

- `_print_check_block` (function/method, line 386): Print one human-readable preflight result block. **Why:** Checks protected Timeshift paths, managed Btrfs roots and helper/lock paths before mutation while keeping strict sync previews from creating them.

- `_raise_for_failed_checks` (function/method, line 401): Raise a hard preflight error when any check failed. **Why:** Checks protected Timeshift paths, managed Btrfs roots and helper/lock paths before mutation while keeping strict sync previews from creating them.

- `ensure_local_helper_dir` (function/method, line 411): Ensure one local helper directory exists. **Why:** Checks protected Timeshift paths, managed Btrfs roots and helper/lock paths before mutation while keeping strict sync previews from creating them.

- `prepare_lock_path` (function/method, line 565): Create/verify the lock directory before other sync/prune directories. **Why:** Checks protected Timeshift paths, managed Btrfs roots and helper/lock paths before mutation while keeping strict sync previews from creating them.

- `prepare_destination_helper_paths` (function/method, line 597): Create/verify local destination helper folders used by sync/prune. **Why:** Checks protected Timeshift paths, managed Btrfs roots and helper/lock paths before mutation while keeping strict sync previews from creating them.

- `_local_target_path_check` (function/method, line 644): Check/create destination.target_root locally. **Why:** Checks protected Timeshift paths, managed Btrfs roots and helper/lock paths before mutation while keeping strict sync previews from creating them.

- `check_required_sync_paths` (function/method, line 786): Verify/create required configured roots before manual snapshot creation or send. **Why:** Checks protected Timeshift paths, managed Btrfs roots and helper/lock paths before mutation while keeping strict sync previews from creating them.

## `timeshift_btrfs_sync/reconciliation.py`

**Role:** Current source/build entry. Reconcile proven pairs and retire authorized one-sided cache/destination leftovers.

**Why:** Repairs complete missing UUID-proven repository pairs before source cache and destination-only cleanup with a newest-confirmed upper limit and no lower date bound; dedicated managed roots, live identities, counterpart absence, confirmed state upper limit, protected dates, dry-run and explicit deletion consent keep ambiguous or active data intact.

- `ReconciliationContext` (class, line 26): One validated inventory generation shared by recovery and bounded cleanup. **Why:** Repairs complete missing UUID-proven repository pairs before source cache and destination-only cleanup with a newest-confirmed upper limit and no lower date bound; dedicated managed roots, live identities, counterpart absence, confirmed state upper limit, protected dates, dry-run and explicit deletion consent keep ambiguous or active data intact.

- `RedundantCacheResult` (class, line 37): Keep one-sided repository cleanup outcomes separate from paired/state deletion. **Why:** Repairs complete missing UUID-proven repository pairs before source cache and destination-only cleanup with a newest-confirmed upper limit and no lower date bound; dedicated managed roots, live identities, counterpart absence, confirmed state upper limit, protected dates, dry-run and explicit deletion consent keep ambiguous or active data intact.

- `refresh_repository_indexes` (function/method, line 47): Reuse scoped discovery so date-container children cannot be missing from reconciliation indexes. **Why:** Repairs complete missing UUID-proven repository pairs before source cache and destination-only cleanup with a newest-confirmed upper limit and no lower date bound; dedicated managed roots, live identities, counterpart absence, confirmed state upper limit, protected dates, dry-run and explicit deletion consent keep ambiguous or active data intact.

- `prepare_reconciliation` (function/method, line 72): Load complete scoped Btrfs views and recover missing pairs before retention decisions. **Why:** Repairs complete missing UUID-proven repository pairs before source cache and destination-only cleanup with a newest-confirmed upper limit and no lower date bound; dedicated managed roots, live identities, counterpart absence, confirmed state upper limit, protected dates, dry-run and explicit deletion consent keep ambiguous or active data intact.

- `_destination_date_absent` (function/method, line 95): Prove date absence with ordinary traversal; denied access is never interpreted as absence. **Why:** Repairs complete missing UUID-proven repository pairs before source cache and destination-only cleanup with a newest-confirmed upper limit and no lower date bound; dedicated managed roots, live identities, counterpart absence, confirmed state upper limit, protected dates, dry-run and explicit deletion consent keep ambiguous or active data intact.

- `_protected_cache_dates` (function/method, line 107): Protect tracked dates, explicit exclusions and parents of incomplete transfers. **Why:** Repairs complete missing UUID-proven repository pairs before source cache and destination-only cleanup with a newest-confirmed upper limit and no lower date bound; dedicated managed roots, live identities, counterpart absence, confirmed state upper limit, protected dates, dry-run and explicit deletion consent keep ambiguous or active data intact.

- `_confirmed_window` (function/method, line 128): Bound cleanup by state dates that still have complete immutable UUID-confirmed pairs. **Why:** Repairs complete missing UUID-proven repository pairs before source cache and destination-only cleanup with a newest-confirmed upper limit and no lower date bound; dedicated managed roots, live identities, counterpart absence, confirmed state upper limit, protected dates, dry-run and explicit deletion consent keep ambiguous or active data intact.

- `_verified_managed_cache_root` (function/method, line 148): Anchor a dedicated native cache to canonical state paths and complete received UUID pairs. **Why:** Repairs complete missing UUID-proven repository pairs before source cache and destination-only cleanup with a newest-confirmed upper limit and no lower date bound; dedicated managed roots, live identities, counterpart absence, confirmed state upper limit, protected dates, dry-run and explicit deletion consent keep ambiguous or active data intact.

- `_native_identity_matches` (function/method, line 199): Require stable UUID, native ID, readonly state and lineage for either repository side. **Why:** Repairs complete missing UUID-proven repository pairs before source cache and destination-only cleanup with a newest-confirmed upper limit and no lower date bound; dedicated managed roots, live identities, counterpart absence, confirmed state upper limit, protected dates, dry-run and explicit deletion consent keep ambiguous or active data intact.

- `_safe_native_cache_date` (function/method, line 207): Accept a dated RO snapshot or native container of RO snapshots, including partial legacy caches. **Why:** Repairs complete missing UUID-proven repository pairs before source cache and destination-only cleanup with a newest-confirmed upper limit and no lower date bound; dedicated managed roots, live identities, counterpart absence, confirmed state upper limit, protected dates, dry-run and explicit deletion consent keep ambiguous or active data intact.

- `_safe_cache_date` (function/method, line 232): Recheck exact cache UUIDs, native snapshot layout and ordinary entries before deletion. **Why:** Repairs complete missing UUID-proven repository pairs before source cache and destination-only cleanup with a newest-confirmed upper limit and no lower date bound; dedicated managed roots, live identities, counterpart absence, confirmed state upper limit, protected dates, dry-run and explicit deletion consent keep ambiguous or active data intact.

- `cleanup_redundant_cache` (function/method, line 280): After successful sync, delete proven stale native cache dates no newer than the latest pair. **Why:** Repairs complete missing UUID-proven repository pairs before source cache and destination-only cleanup with a newest-confirmed upper limit and no lower date bound; dedicated managed roots, live identities, counterpart absence, confirmed state upper limit, protected dates, dry-run and explicit deletion consent keep ambiguous or active data intact.

- `_verified_destination_root` (function/method, line 358): Anchor destination containment and fresh receiver identities to the verified cache/state job. **Why:** Repairs complete missing UUID-proven repository pairs before source cache and destination-only cleanup with a newest-confirmed upper limit and no lower date bound; dedicated managed roots, live identities, counterpart absence, confirmed state upper limit, protected dates, dry-run and explicit deletion consent keep ambiguous or active data intact.

- `_safe_native_destination_date` (function/method, line 398): Require unchanged native date trees containing only readonly snapshot payloads. **Why:** Repairs complete missing UUID-proven repository pairs before source cache and destination-only cleanup with a newest-confirmed upper limit and no lower date bound; dedicated managed roots, live identities, counterpart absence, confirmed state upper limit, protected dates, dry-run and explicit deletion consent keep ambiguous or active data intact.

- `_refresh_absent_cache_date` (function/method, line 422): Re-prove complete cache inventory and stable root before accepting native date absence. **Why:** Repairs complete missing UUID-proven repository pairs before source cache and destination-only cleanup with a newest-confirmed upper limit and no lower date bound; dedicated managed roots, live identities, counterpart absence, confirmed state upper limit, protected dates, dry-run and explicit deletion consent keep ambiguous or active data intact.

- `cleanup_redundant_destination` (function/method, line 440): After successful sync, remove untracked destination-only RO dates no newer than the newest proven pair. **Why:** Repairs complete missing UUID-proven repository pairs before source cache and destination-only cleanup with a newest-confirmed upper limit and no lower date bound; dedicated managed roots, live identities, counterpart absence, confirmed state upper limit, protected dates, dry-run and explicit deletion consent keep ambiguous or active data intact.

## `timeshift_btrfs_sync/restore.py`

**Role:** Current source/build entry. Restore backed-up snapshots into Timeshift's native Btrfs layout.

**Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `RestoreError` (class, line 50): Raised when backups cannot be imported safely into Timeshift. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `TimeshiftOsIdentity` (class, line 55): Timeshift ``info.json`` provenance metadata for one snapshot. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `BackupSnapshot` (class, line 64): One validated local or SSH backup snapshot available for restore. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `BackupDirectoryRecord` (class, line 75): Ordinary filesystem facts for one backup timestamp directory. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `BackupRepository` (class, line 86): Access one local or SSH backup repository through one transport layer. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `BackupRepository.from_config` (function/method, line 95): Create the backup endpoint selected by restore.mode. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots. Scoped within `BackupRepository` to use its existing endpoint, state or callback context.

- `BackupRepository.root` (property, line 109): Resolve the configured backup root as POSIX path text on its selected endpoint. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots. Scoped within `BackupRepository` to use its existing endpoint, state or callback context.

- `BackupRepository.snapshots_root` (property, line 113): Locate the physical snapshots child below the backup root. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots. Scoped within `BackupRepository` to use its existing endpoint, state or callback context.

- `BackupRepository.environment` (property, line 117): Return the backup runner child-process authentication environment. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots. Scoped within `BackupRepository` to use its existing endpoint, state or callback context.

- `BackupRepository.location_label` (property, line 121): Label whether restore reads a local or remote SSH backup. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots. Scoped within `BackupRepository` to use its existing endpoint, state or callback context.

- `BackupRepository.load_state` (function/method, line 124): Read and validate state.json from the same endpoint as the backup. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots. Scoped within `BackupRepository` to use its existing endpoint, state or callback context.

- `BackupRepository.scan_directories` (function/method, line 146): Read direct date entries and all info.json files with backup privilege. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots. Scoped within `BackupRepository` to use its existing endpoint, state or callback context.

- `BackupRepository.btrfs_index` (function/method, line 156): Build one local or SSH Btrfs index for the complete backup tree. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots. Scoped within `BackupRepository` to use its existing endpoint, state or callback context.

- `_scan_snapshot_directories` (function/method, line 174): Scan physical Timeshift-style date directories and their control files. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `_read_privileged_file` (function/method, line 286): Read one regular non-symlink file through individually privileged commands. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `_effective_send_uuid` (function/method, line 357): Return the UUID identity carried by a Btrfs send stream. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `_info_os_identity` (function/method, line 371): Return Timeshift provenance identity while ignoring mutable fields. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `_parse_info_json` (function/method, line 393): Parse one Timeshift control file and extract its provenance identity. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `_same_os_identity` (function/method, line 405): Return whether two Timeshift control files have matching provenance. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `_consistent_backup_identity` (function/method, line 416): Require one non-conflicting provenance identity across the backup set. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `_timeshift_info_identities` (function/method, line 443): Parse provenance identities from the coherent source info.json inventory. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `_timeshift_info_diagnostic` (function/method, line 456): Return a concise reason when source ``info.json`` provenance is unavailable. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `_compare_repository_os_identity` (function/method, line 482): Compare backup provenance with currently readable Timeshift control files. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `RestorePlan` (class, line 515): A side-effect-free single or chain restore plan. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `RestorePlan.seed_name` (property, line 530): Return the first chain date that must be full-seeded, or None for an empty plan. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots. Scoped within `RestorePlan` to use its existing endpoint, state or callback context.

- `_source_path_exists` (function/method, line 534): Check one Timeshift-side path through the configured source privilege. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `_privileged_argv` (function/method, line 554): Prefix Timeshift-side utility arguments with the configured source privilege command. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `_write_source_info_json` (function/method, line 558): Write exact captured metadata through the configured source privilege prefix. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `_validate_backup_snapshot` (function/method, line 599): Validate one backup date, payload set, metadata file, and Btrfs identity. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `_discover_backups` (function/method, line 677): Return selected or all valid backups ordered by Timeshift timestamp. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `_timeshift_snapshots` (function/method, line 702): Read one coherent Timeshift repository/cache/info inventory. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `_exact_timeshift_payload_meta` (function/method, line 780): Return exact live metadata for one Timeshift payload. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `_state_payload_proof` (function/method, line 803): Check the two UUID links recorded for one completed transfer. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `_live_payload_proof` (function/method, line 833): Prove one payload directly from current Btrfs metadata. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `_find_latest_common_parent` (function/method, line 895): Find the newest safely confirmed timestamp present in both repositories. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `_build_restore_plan` (function/method, line 1074): Build a single or complete-chain restore plan without changing either side. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `_remove_restore_directory` (function/method, line 1208): Remove one exact app-created ordinary restore directory and its payloads. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `_cleanup_restore_attempt` (function/method, line 1262): Roll back only directories created by the current restore attempt. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `_create_pre_restore_snapshot` (function/method, line 1322): Create and verify one safety snapshot on the Timeshift restore target. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `_print_restored_snapshot_retention_warning` (function/method, line 1419): Explain that restored Timeshift tags remain subject to normal retention. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `_print_restore_plan` (function/method, line 1436): Print endpoint ownership, selected dates, common-parent/provenance proofs and restore/retention warnings before execution. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `_is_missing_incremental_parent_error` (function/method, line 1505): Return whether Btrfs failed because a parent/clone UUID was unavailable. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `_remove_partial_received_payload` (function/method, line 1525): Delete only a failed receive's exact partial Btrfs child before retry. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `_run_restore_stream` (function/method, line 1551): Run one topology-independent backup-send to Timeshift-receive stream. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `_receive_restore_payload` (function/method, line 1582): Receive and verify one hidden-chain payload for every restore topology. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

- `restore_backups` (function/method, line 1675): Restore one snapshot or a complete backup chain into Timeshift. **Why:** Validates physical backup dates, metadata, provenance and payload UUIDs before constructing a hidden read-only receive chain and exposing writable Timeshift snapshots.

## `timeshift_btrfs_sync/retention.py`

**Role:** Current source/build entry. Paired destination and app-created source Timeshift retention/pruning logic.

**Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds.

- `PrunePlan` (class, line 33): Dry-run friendly prune plan. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds.

- `PrunePlan.add_keep` (function/method, line 40): Mark a snapshot as kept and remember the human reason. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds. Scoped within `PrunePlan` to use its existing endpoint, state or callback context.

- `PrunePlan.add_delete` (function/method, line 47): Mark a snapshot as deletable only when it is not already protected. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds. Scoped within `PrunePlan` to use its existing endpoint, state or callback context.

- `PruneResult` (class, line 56): Retention outcome used by the final sync cleanup summary. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds.

- `PruneResult.cleaned_snapshots` (property, line 85): Return snapshot-level cleanup successes, not subvolume delete count. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds. Scoped within `PruneResult` to use its existing endpoint, state or callback context.

- `PruneResult.retry_destination_state_items` (property, line 91): Return paired/state candidates that could not complete cleanup. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds. Scoped within `PruneResult` to use its existing endpoint, state or callback context.

- `PruneResult.blocked_source_candidates` (property, line 97): Return current source app-snapshot candidates not authorized now. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds. Scoped within `PruneResult` to use its existing endpoint, state or callback context.

- `format_prune_cleanup_summaries` (function/method, line 103): Report retention outcomes separately for destination and app-owned cache. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds.

- `format_prune_cleanup_summaries.block` (function/method, line 115): Render one cleanup side without inferring success from paired state. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds. Scoped within `format_prune_cleanup_summaries` to use its existing endpoint, state or callback context.

- `_is_app_created_ondemand` (function/method, line 185): Return true when a state entry is a tag O snapshot with the app marker. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds.

- `_is_current_source_app_created_ondemand` (function/method, line 196): Re-prove app ownership from the current Timeshift listing before deletion. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds.

- `_delete_reason_for_snapshot` (function/method, line 206): Explain why a snapshot is outside the active retention rules. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds.

- `_delete_reasons` (function/method, line 242): Return delete reasons without the internal prefix. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds.

- `_source_cache_delete_paths` (function/method, line 251): Return app-owned source send-cache paths for a prune decision. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds.

- `_protected_timeshift_send_paths` (function/method, line 297): Return direct Timeshift send paths that prune must never delete. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds.

- `_destination_delete_paths` (function/method, line 327): Return tracked destination subvolume paths for a prune decision. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds.

- `source_snapshot_state` (function/method, line 338): Return temporary state-like data from source Timeshift snapshots. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds.

- `initial_sync_keep_names` (function/method, line 363): Return retention-selected source names for a fresh or incremental backup. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds.

- `_cleanup_source_cache_for_pruned_snapshot` (function/method, line 374): Delete one pruned snapshot's app-owned cache through the shared tree engine. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds.

- `_load_source_timeshift_index` (function/method, line 423): Read one current Timeshift list for destructive source-retention checks. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds.

- `_delete_source_timeshift_snapshot_for_prune` (function/method, line 438): Delete one old app-created source O snapshot through Timeshift only. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds.

- `_destination_snapshot_is_proven_complete` (function/method, line 490): Prove that state and the live destination contain every configured payload. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds.

- `_source_app_retention_delete_names` (function/method, line 507): Return current app-created source O snapshots outside the same retention rules. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds.

- `_authorized_source_timeshift_delete_names` (function/method, line 526): Authorize source deletion from direct backup proof or a backed retained window. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds.

- `build_prune_plan` (function/method, line 569): Build retention plan from state without deleting anything. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds.

- `_delete_destination_snapshot_for_prune` (function/method, line 656): Delete one destination date through the shared tree engine. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds.

- `_delete_prune_item` (function/method, line 682): Execute one prune item and remove state only after every required side is gone. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds.

- `_delete_prune_item.delete_source_timeshift_action` (function/method, line 732): Delete only freshly authorized app-created Timeshift snapshots before removing their proven backups. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds. Scoped within `_delete_prune_item` to use its existing endpoint, state or callback context.

- `_delete_prune_item.delete_destination` (function/method, line 749): Delete the exact managed backup date using the shared Btrfs-only tree workflow. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds. Scoped within `_delete_prune_item` to use its existing endpoint, state or callback context.

- `_delete_prune_item.delete_cache_action` (function/method, line 762): Delete the matching app-owned cache date after destination removal succeeds. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds. Scoped within `_delete_prune_item` to use its existing endpoint, state or callback context.

- `_delete_prune_item.remove_state` (function/method, line 783): Remove the state record only after preceding required deletion actions complete. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds. Scoped within `_delete_prune_item` to use its existing endpoint, state or callback context.

- `print_prune_plan` (function/method, line 802): Write an easy-to-read retention summary to terminal and .succes. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds.

- `_confirmed_prune_parent` (function/method, line 856): Prove a complete live send/receive anchor before pruning its siblings. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds.

- `prune` (function/method, line 898): Apply paired retention; CLI callers enable inventory reconciliation and bounded extra cache cleanup. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds.

- `_apply_redundant_cache_cleanup` (function/method, line 1095): Merge cache-only counters without falsely increasing paired destination/state deletions. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds.

- `_apply_redundant_destination_cleanup` (function/method, line 1110): Merge receiver-only counts without changing paired retention/state deletion totals. **Why:** Separates user on-demand snapshots from app-created ones, proves backup coverage before source deletion and removes state only after required cleanup succeeds.

## `timeshift_btrfs_sync/source.py`

**Role:** Current source/build entry. Command runner for local or SSH Timeshift and backup endpoints.

**Why:** Selects a local or SSH transport for the intended endpoint without duplicating Timeshift or Btrfs operations.

- `SourceRunner` (class, line 12): Run commands through one local or SSH endpoint. **Why:** Selects a local or SSH transport for the intended endpoint without duplicating Timeshift or Btrfs operations.

- `SourceRunner.from_mode` (function/method, line 24): Create a local or SSH command runner from one validated mode. **Why:** Selects a local or SSH transport for the intended endpoint without duplicating Timeshift or Btrfs operations. Scoped within `SourceRunner` to use its existing endpoint, state or callback context.

- `SourceRunner.from_config` (function/method, line 36): Create the configured Timeshift source runner. **Why:** Selects a local or SSH transport for the intended endpoint without duplicating Timeshift or Btrfs operations. Scoped within `SourceRunner` to use its existing endpoint, state or callback context.

- `SourceRunner.uses_ssh` (property, line 42): Return True when source commands are executed through SSH. **Why:** Selects a local or SSH transport for the intended endpoint without duplicating Timeshift or Btrfs operations. Scoped within `SourceRunner` to use its existing endpoint, state or callback context.

- `SourceRunner.location` (property, line 48): Return the metadata location label used by Btrfs helpers. **Why:** Selects a local or SSH transport for the intended endpoint without duplicating Timeshift or Btrfs operations. Scoped within `SourceRunner` to use its existing endpoint, state or callback context.

- `SourceRunner.command` (function/method, line 53): Return argv that runs one source-side shell command. **Why:** Selects a local or SSH transport for the intended endpoint without duplicating Timeshift or Btrfs operations. Scoped within `SourceRunner` to use its existing endpoint, state or callback context.

- `SourceRunner.run` (function/method, line 60): Run one source-side command and capture stdout/stderr. **Why:** Selects a local or SSH transport for the intended endpoint without duplicating Timeshift or Btrfs operations. Scoped within `SourceRunner` to use its existing endpoint, state or callback context.

- `SourceRunner.environment` (function/method, line 87): Return environment needed for streaming source commands. **Why:** Selects a local or SSH transport for the intended endpoint without duplicating Timeshift or Btrfs operations. Scoped within `SourceRunner` to use its existing endpoint, state or callback context.

- `SourceRunner.test` (function/method, line 94): Verify that the source command endpoint is usable. **Why:** Selects a local or SSH transport for the intended endpoint without duplicating Timeshift or Btrfs operations. Scoped within `SourceRunner` to use its existing endpoint, state or callback context.

## `timeshift_btrfs_sync/ssh.py`

**Role:** Current source/build entry. SSH command construction.

**Why:** Constructs SSH transport and private prompt helpers, validates control sockets and refuses unknown prompts rather than approving host-key questions.

- `_is_relative_to` (function/method, line 46): Return True when path is root or below root without broad string matching. **Why:** Constructs SSH transport and private prompt helpers, validates control sockets and refuses unknown prompts rather than approving host-key questions.

- `_cleanup_askpass_helper` (function/method, line 56): Remove the process-private askpass helper directory at normal exit. **Why:** Constructs SSH transport and private prompt helpers, validates control sockets and refuses unknown prompts rather than approving host-key questions.

- `_ensure_askpass_helper` (function/method, line 67): Create and return one private prompt-dispatch helper for this process. **Why:** Constructs SSH transport and private prompt helpers, validates control sockets and refuses unknown prompts rather than approving host-key questions.

- `validate_control_path_safety` (function/method, line 102): Create and validate a private SSH ControlPath socket directory. **Why:** Constructs SSH transport and private prompt helpers, validates control sockets and refuses unknown prompts rather than approving host-key questions.

- `SSHConfig` (class, line 172): Connection and SSH transport settings. **Why:** Constructs SSH transport and private prompt helpers, validates control sockets and refuses unknown prompts rather than approving host-key questions.

- `SSHConfig.target` (property, line 191): Return host or user@host. **Why:** Constructs SSH transport and private prompt helpers, validates control sockets and refuses unknown prompts rather than approving host-key questions. Scoped within `SSHConfig` to use its existing endpoint, state or callback context.

- `SSHConfig.uses_password_auth` (property, line 197): Return True when a remote SSH account password is configured. **Why:** Constructs SSH transport and private prompt helpers, validates control sockets and refuses unknown prompts rather than approving host-key questions. Scoped within `SSHConfig` to use its existing endpoint, state or callback context.

- `SSHConfig.uses_identity_passphrase` (property, line 203): Return True when the configured private key needs an app-supplied passphrase. **Why:** Constructs SSH transport and private prompt helpers, validates control sockets and refuses unknown prompts rather than approving host-key questions. Scoped within `SSHConfig` to use its existing endpoint, state or callback context.

- `SSHConfig.uses_askpass` (property, line 209): Return True when prompt-aware OpenSSH askpass dispatch is required. **Why:** Constructs SSH transport and private prompt helpers, validates control sockets and refuses unknown prompts rather than approving host-key questions. Scoped within `SSHConfig` to use its existing endpoint, state or callback context.

- `SSHConfig._read_secret` (function/method, line 215): Read one configured secret and reject an empty direct value or file. **Why:** Constructs SSH transport and private prompt helpers, validates control sockets and refuses unknown prompts rather than approving host-key questions. Scoped within `SSHConfig` to use its existing endpoint, state or callback context.

- `SSHConfig._read_password` (function/method, line 228): Read the remote SSH account password from TOML or password_file. **Why:** Constructs SSH transport and private prompt helpers, validates control sockets and refuses unknown prompts rather than approving host-key questions. Scoped within `SSHConfig` to use its existing endpoint, state or callback context.

- `SSHConfig._read_identity_passphrase` (function/method, line 233): Read the private-key passphrase from TOML or identity_passphrase_file. **Why:** Constructs SSH transport and private prompt helpers, validates control sockets and refuses unknown prompts rather than approving host-key questions. Scoped within `SSHConfig` to use its existing endpoint, state or callback context.

- `SSHConfig.environment` (function/method, line 242): Return authentication environment for sshpass or OpenSSH askpass. **Why:** Constructs SSH transport and private prompt helpers, validates control sockets and refuses unknown prompts rather than approving host-key questions. Scoped within `SSHConfig` to use its existing endpoint, state or callback context.

- `SSHConfig.base_command` (function/method, line 267): Build base SSH argv; remote command is appended later. **Why:** Constructs SSH transport and private prompt helpers, validates control sockets and refuses unknown prompts rather than approving host-key questions. Scoped within `SSHConfig` to use its existing endpoint, state or callback context.

- `SSHRunner` (class, line 295): Run remote commands through SSH. **Why:** Constructs SSH transport and private prompt helpers, validates control sockets and refuses unknown prompts rather than approving host-key questions.

- `SSHRunner.__init__` (function/method, line 298): Store the SSH connection configuration for command and environment construction. **Why:** Constructs SSH transport and private prompt helpers, validates control sockets and refuses unknown prompts rather than approving host-key questions. Scoped within `SSHRunner` to use its existing endpoint, state or callback context.

- `SSHRunner.command` (function/method, line 301): Return argv for one SSH remote command. **Why:** Constructs SSH transport and private prompt helpers, validates control sockets and refuses unknown prompts rather than approving host-key questions. Scoped within `SSHRunner` to use its existing endpoint, state or callback context.

- `SSHRunner.run` (function/method, line 306): Run a remote command and capture stdout/stderr. **Why:** Constructs SSH transport and private prompt helpers, validates control sockets and refuses unknown prompts rather than approving host-key questions. Scoped within `SSHRunner` to use its existing endpoint, state or callback context.

- `SSHRunner.environment` (function/method, line 332): Return SSH environment for streaming pipeline calls. **Why:** Constructs SSH transport and private prompt helpers, validates control sockets and refuses unknown prompts rather than approving host-key questions. Scoped within `SSHRunner` to use its existing endpoint, state or callback context.

- `SSHRunner.test` (function/method, line 337): Verify SSH works and stdout is not polluted by banners. **Why:** Constructs SSH transport and private prompt helpers, validates control sockets and refuses unknown prompts rather than approving host-key questions. Scoped within `SSHRunner` to use its existing endpoint, state or callback context.

## `timeshift_btrfs_sync/state.py`

**Role:** Current source/build entry. Persistent local state for completed transfers.

**Why:** Validates and atomically records completed transfers with relocatable root-relative paths and explicit send-path ownership for later UUID proof.

- `empty_state` (function/method, line 28): Return a new empty state document. **Why:** Validates and atomically records completed transfers with relocatable root-relative paths and explicit send-path ownership for later UUID proof.

- `_safe_relative_path` (function/method, line 34): Return a normalized destination-relative path or raise ValueError. **Why:** Validates and atomically records completed transfers with relocatable root-relative paths and explicit send-path ownership for later UUID proof.

- `_safe_source_relative_path` (function/method, line 46): Return a normalized safe POSIX path relative to a configured source root. **Why:** Validates and atomically records completed transfers with relocatable root-relative paths and explicit send-path ownership for later UUID proof.

- `_normalize_source_root` (function/method, line 65): Return one normalized absolute-style POSIX source root. **Why:** Validates and atomically records completed transfers with relocatable root-relative paths and explicit send-path ownership for later UUID proof.

- `_source_path_relative_to_root` (function/method, line 72): Return ``path`` relative to ``root`` when it is currently below that root. **Why:** Validates and atomically records completed transfers with relocatable root-relative paths and explicit send-path ownership for later UUID proof.

- `_expected_snapshot_relative_path` (function/method, line 90): Return the canonical ``<snapshot>/<subvolume>`` source-relative path. **Why:** Validates and atomically records completed transfers with relocatable root-relative paths and explicit send-path ownership for later UUID proof.

- `source_path_to_relative` (function/method, line 98): Convert a current source path to canonical configured-root-relative state form. **Why:** Validates and atomically records completed transfers with relocatable root-relative paths and explicit send-path ownership for later UUID proof.

- `resolve_source_path` (function/method, line 124): Resolve a current root-relative state path under its configured source root. **Why:** Validates and atomically records completed transfers with relocatable root-relative paths and explicit send-path ownership for later UUID proof.

- `destination_path_to_relative` (function/method, line 143): Convert a current destination path to target-root-relative state form. **Why:** Validates and atomically records completed transfers with relocatable root-relative paths and explicit send-path ownership for later UUID proof.

- `resolve_destination_path` (function/method, line 155): Resolve a current target-root-relative state destination path. **Why:** Validates and atomically records completed transfers with relocatable root-relative paths and explicit send-path ownership for later UUID proof.

- `send_path_kind_for_state_subvolume` (function/method, line 160): Return the explicitly stored current send-path ownership kind. **Why:** Validates and atomically records completed transfers with relocatable root-relative paths and explicit send-path ownership for later UUID proof.

- `_source_root_for_kind` (function/method, line 168): Return the configured source root used by one stored send-path kind. **Why:** Validates and atomically records completed transfers with relocatable root-relative paths and explicit send-path ownership for later UUID proof.

- `resolve_state_send_path` (function/method, line 180): Resolve stored ``send_path`` under its current configured source root. **Why:** Validates and atomically records completed transfers with relocatable root-relative paths and explicit send-path ownership for later UUID proof.

- `_reject_unknown_state_keys` (function/method, line 213): Reject state fields outside the current schema before workflows trust persisted identities. **Why:** Validates and atomically records completed transfers with relocatable root-relative paths and explicit send-path ownership for later UUID proof.

- `validate_state_document` (function/method, line 219): Validate the complete current state schema before any workflow uses it. **Why:** Validates and atomically records completed transfers with relocatable root-relative paths and explicit send-path ownership for later UUID proof.

- `load_state` (function/method, line 297): Load and validate the current state document, or return an empty one when absent. **Why:** Validates and atomically records completed transfers with relocatable root-relative paths and explicit send-path ownership for later UUID proof.

- `save_state` (function/method, line 309): Validate and atomically write the current state document. **Why:** Validates and atomically records completed transfers with relocatable root-relative paths and explicit send-path ownership for later UUID proof.

- `refresh_snapshot_metadata_from_source` (function/method, line 328): Refresh mutable Timeshift metadata for already-known snapshots. **Why:** Validates and atomically records completed transfers with relocatable root-relative paths and explicit send-path ownership for later UUID proof.

- `snapshot_is_synced` (function/method, line 355): Return True when a snapshot is recorded as fully synced. **Why:** Validates and atomically records completed transfers with relocatable root-relative paths and explicit send-path ownership for later UUID proof.

- `_kind_for_absolute_source_path` (function/method, line 367): Classify a current absolute source path by configured ownership root. **Why:** Validates and atomically records completed transfers with relocatable root-relative paths and explicit send-path ownership for later UUID proof.

- `mark_subvolume_synced` (function/method, line 384): Record one successful send/receive using only root-relative state paths. **Why:** Validates and atomically records completed transfers with relocatable root-relative paths and explicit send-path ownership for later UUID proof.

- `state_send_path_is_app_cache` (function/method, line 499): Return True when the stored send path belongs to the app cache. **Why:** Validates and atomically records completed transfers with relocatable root-relative paths and explicit send-path ownership for later UUID proof.

- `state_send_path_is_protected_timeshift_original` (function/method, line 504): Return True when the stored send path belongs to Timeshift. **Why:** Validates and atomically records completed transfers with relocatable root-relative paths and explicit send-path ownership for later UUID proof.

- `remove_snapshot_from_state` (function/method, line 509): Remove a pruned snapshot from state. **Why:** Validates and atomically records completed transfers with relocatable root-relative paths and explicit send-path ownership for later UUID proof.

- `refresh_state_metadata_and_report` (function/method, line 515): Refresh only Timeshift tags/comment/created/path, report, and save. **Why:** Validates and atomically records completed transfers with relocatable root-relative paths and explicit send-path ownership for later UUID proof.

- `latest_synced_before` (function/method, line 539): Return newest older synced parent candidate. **Why:** Validates and atomically records completed transfers with relocatable root-relative paths and explicit send-path ownership for later UUID proof.

## `timeshift_btrfs_sync/sync.py`

**Role:** Current source/build entry. Main destination-pull sync workflow.

**Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `SyncError` (class, line 56): Raised for sync safety errors. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_local_meta` (function/method, line 60): Read optional exact local Btrfs metadata through the destination command endpoint. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_source_meta` (function/method, line 66): Return source metadata, preferring bulk indexes over one-off probes. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_human_blank` (function/method, line 90): Print one blank line to separate human-readable status blocks. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_human_rule` (function/method, line 96): Print a visual separator with blank lines around it. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_transfer_size_preflight` (function/method, line 104): Measure one planned send and refuse it when Btrfs free space is too small. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_record_sync_event` (function/method, line 192): Add one planned or completed transfer to the run summary. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `SyncRunSummary` (class, line 226): Completed sync statistics retained until the final end-of-run report. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `format_duration` (function/method, line 236): Format a monotonic elapsed duration as human-readable wall time. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `format_transferred_snapshots` (function/method, line 248): Return the transfer list that must be third-from-last in sync output. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `format_transferred_bytes_total` (function/method, line 278): Format an actual successful-transfer total as MB, GB, or TB. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_summary_transferred_bytes` (function/method, line 294): Return known bytes, known transfer count, and unknown transfer count. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `format_sync_summary` (function/method, line 303): Return the compact sync summary that is second-from-last in sync output. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `prepare_destination` (function/method, line 338): Create/validate destination helper folders before writes. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `list_source_snapshots` (function/method, line 358): Discover source Timeshift snapshots. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `source_snapshot_index` (function/method, line 381): Index discovered Timeshift snapshots by timestamp name for shared workflow lookups. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_snapshots_from_source_inventory` (function/method, line 385): Build Timeshift snapshot objects from one coherent source inventory. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_required_pipeline_source_changes` (function/method, line 403): Return identity changes to source paths required by current work. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_terminal_destination_receive_failure_reason` (function/method, line 450): Return a clear destination-side reason that must not be source-retried. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_revalidate_missing_required_pipeline_paths` (function/method, line 469): Exact-probe required source paths omitted by the refreshed bulk index. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `confirm_source_identity_before_manual_snapshot` (function/method, line 537): Print and enforce the shared manual-snapshot source identity guard. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_is_app_manual_snapshot` (function/method, line 589): Return True for source Timeshift O snapshots created by this app. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_pending_app_manual_snapshots` (function/method, line 605): Return app-created on-demand snapshots that still need syncing. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_maybe_create_manual_snapshot` (function/method, line 630): Optionally create a source Timeshift tag O snapshot before sync. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_snapshots_in_sync_order` (function/method, line 719): Return source snapshots oldest-to-newest for Btrfs send. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_select_initial_sync_snapshots` (function/method, line 725): Select retained snapshots for any sync, plus completed metadata refreshes. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `print_snapshot_table` (function/method, line 762): Print source snapshots in table form. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_dest_subvolume_path` (function/method, line 773): Return the final local path for one received subvolume. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_target_snapshot_dir` (function/method, line 783): Return the managed destination date subvolume passed to `btrfs receive`. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_destination_info_json_path` (function/method, line 793): Return the destination Timeshift control-file path for one snapshot. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_ensure_destination_snapshot_subvolume` (function/method, line 799): Create or validate one managed destination date subvolume. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_validate_destination_snapshot_layout` (function/method, line 849): Refuse ordinary/symlinked date entries after exact Btrfs verification. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_atomic_write_snapshot_info_json` (function/method, line 910): Atomically write one captured Timeshift ``info.json`` file. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_require_snapshot_info_json` (function/method, line 943): Return captured control-file content or raise a precise sync error. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_sync_snapshot_info_json` (function/method, line 977): Create or refresh destination ``info.json`` for one complete snapshot. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_destination_has_existing_snapshots` (function/method, line 1017): Return true only when a date directory contains a configured payload subvolume. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_snapshot_destination_paths_exist` (function/method, line 1038): Return True only when every expected destination subvolume path exists. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_preview_send_path` (function/method, line 1043): Return the send path that would be used, without creating cache snapshots. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_send_path_kind_text` (function/method, line 1057): Return human text explaining who owns the selected send path. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_ensure_source_send_path` (function/method, line 1067): Resolve one real send path through the shared cache operation. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_cleanup_incomplete_destination_receive` (function/method, line 1094): Delete one exact incomplete destination Btrfs child before retrying. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_cleanup_source_cache_snapshot_version` (function/method, line 1124): Delete one app-owned cache date through the shared tree engine. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_cleanup_destination_snapshot_version` (function/method, line 1155): Delete one destination date through the shared tree engine. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_refresh_snapshot_source_subvolumes_live` (function/method, line 1184): Return configured source subvolumes, preferring the bulk index. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_snapshot_destination_has_any_path` (function/method, line 1213): Return True when the destination date folder or configured children exist. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_snapshot_state_is_complete_with_destination` (function/method, line 1222): Return True only when state and destination contain every configured subvolume. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_recover_snapshot_version` (function/method, line 1229): Remove stale current-version traces from cache, destination, and state. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_recover_snapshot_version.handle` (function/method, line 1262): Dispatch cache, destination and state recovery actions in the planned whole-date order. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery. Scoped within `_recover_snapshot_version` to use its existing endpoint, state or callback context.

- `_prepare_snapshot_for_transfer_or_recover` (function/method, line 1284): Return True when a snapshot can be transferred, False when skipped. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_recover_stale_state_snapshots_missing_from_source` (function/method, line 1358): Clean incomplete state entries whose Timeshift source name is gone. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_read_local_destination_parent_metadata` (function/method, line 1390): Read metadata for the destination snapshot that would be the receiver parent. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_match_source_path_to_destination_received_uuid` (function/method, line 1412): Check whether a source send-stream UUID matches destination identity. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_select_verified_parent_send_path` (function/method, line 1474): Select a safe source parent path for incremental send without recreating it. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_select_verified_parent_send_path.add_candidate` (function/method, line 1503): Add distinct candidate send paths with metadata and an origin label before exact parent UUID validation. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery. Scoped within `_select_verified_parent_send_path` to use its existing endpoint, state or callback context.

- `_state_uuid_values_for_path` (function/method, line 1581): Return a saved UUID hint for a candidate; never authorize receiver identity. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_find_confirmed_sync_floor` (function/method, line 1598): Return the newest complete state date with a proven immutable shared parent. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_destination_snapshot_names` (function/method, line 1701): Return destination snapshot folder names sorted oldest-to-newest. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_expected_original_source_path` (function/method, line 1710): Return the Timeshift-owned original source path for one snapshot/subvolume. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_source_cache_meta_by_uuid` (function/method, line 1716): Return indexed read-only source-cache metadata for one send UUID. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_match_existing_destination_to_source` (function/method, line 1735): Match one existing destination subvolume to an exact source/cache UUID. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_recover_state_from_existing_destination` (function/method, line 1815): Merge missing complete UUID-proven dates into empty or populated state without inventing parents. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_filesystem_parent_candidates` (function/method, line 1940): Find local destination parent candidates by matching snapshot names. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_select_parent` (function/method, line 1964): Choose the newest valid incremental parent. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_verify_sync_viability_before_manual_snapshot` (function/method, line 2116): Prove sync can start before asking Timeshift to create a snapshot. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `_verify_sync_viability_before_manual_snapshot.verify_parent_for` (function/method, line 2173): Verify a pending or future manual snapshot can use a safe incremental parent; abort source creation on failure. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery. Scoped within `_verify_sync_viability_before_manual_snapshot` to use its existing endpoint, state or callback context.

- `sync_once` (function/method, line 2244): Run one sync pass. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery.

- `sync_once.load_source_inventory` (function/method, line 2286): Build and report one coherent source inventory generation. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery. Scoped within `sync_once` to use its existing endpoint, state or callback context.

- `sync_once.build_snapshot_queue` (function/method, line 2445): Build one pure oldest-to-newest sync plan, then return its snapshot queue. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery. Scoped within `sync_once` to use its existing endpoint, state or callback context.

- `sync_once.recover_from_source_inventory_change` (function/method, line 2488): Recover one failed snapshot version and rebuild all source lists. **Why:** Orchestrates oldest-to-newest backup, run-start full-seed authorization, UUID-proven incremental parents, metadata completion and bounded relevant-source recovery. Scoped within `sync_once` to use its existing endpoint, state or callback context.

## `timeshift_btrfs_sync/timeshift.py`

**Role:** Current source/build entry. Timeshift command wrappers and parser for `timeshift --list`.

**Why:** Wraps Timeshift listing, creation and verified deletion so original source snapshots remain under Timeshift ownership.

- `timeshift_cmd` (function/method, line 18): Build a source-side shell command that invokes sudo+timeshift. **Why:** Wraps Timeshift listing, creation and verified deletion so original source snapshots remain under Timeshift ownership.

- `normalize_tags` (function/method, line 24): Return unique Timeshift tag letters found in text. **Why:** Wraps Timeshift listing, creation and verified deletion so original source snapshots remain under Timeshift ownership.

- `parse_timeshift_list` (function/method, line 34): Parse Timeshift snapshot names and tag/comment text. **Why:** Wraps Timeshift listing, creation and verified deletion so original source snapshots remain under Timeshift ownership.

- `list_source_snapshots` (function/method, line 67): Discover source snapshots through SSH or local source commands. **Why:** Wraps Timeshift listing, creation and verified deletion so original source snapshots remain under Timeshift ownership.

- `create_remote_manual_snapshot_cmd` (function/method, line 108): Build the Timeshift manual/on-demand snapshot create command. **Why:** Wraps Timeshift listing, creation and verified deletion so original source snapshots remain under Timeshift ownership.

- `create_source_manual_snapshot` (function/method, line 127): Create a source Timeshift on-demand snapshot through SSH or locally. **Why:** Wraps Timeshift listing, creation and verified deletion so original source snapshots remain under Timeshift ownership.

- `delete_remote_manual_snapshot_cmd` (function/method, line 133): Build one Timeshift delete command with an in-command verification list. **Why:** Wraps Timeshift listing, creation and verified deletion so original source snapshots remain under Timeshift ownership.

- `delete_source_manual_snapshot` (function/method, line 157): Delete one app-created source snapshot through Timeshift and verify it is gone. **Why:** Wraps Timeshift listing, creation and verified deletion so original source snapshots remain under Timeshift ownership.

## `timeshift_btrfs_sync/topology.py`

**Role:** Current source/build entry. Command topology descriptions and safety checks.

**Why:** Makes endpoint ownership explicit and refuses pull-restore configurations for sync because sync always writes its destination locally.

- `TopologyError` (class, line 21): Raised when a command/config combination would use unintended hosts. **Why:** Makes endpoint ownership explicit and refuses pull-restore configurations for sync because sync always writes its destination locally.

- `TopologyDescription` (class, line 26): Human-readable endpoint ownership for one command. **Why:** Makes endpoint ownership explicit and refuses pull-restore configurations for sync because sync always writes its destination locally.

- `_ssh_target` (function/method, line 34): Format the configured user/host for topology diagnostics or report an unconfigured SSH endpoint. **Why:** Makes endpoint ownership explicit and refuses pull-restore configurations for sync because sync always writes its destination locally.

- `describe_sync_topology` (function/method, line 42): Return the endpoints actually used by ``sync``. **Why:** Makes endpoint ownership explicit and refuses pull-restore configurations for sync because sync always writes its destination locally.

- `describe_restore_topology` (function/method, line 57): Return the endpoints actually used by ``restore``. **Why:** Makes endpoint ownership explicit and refuses pull-restore configurations for sync because sync always writes its destination locally.

- `reject_pull_restore_profile_for_sync` (function/method, line 79): Refuse ``sync`` with a profile whose restore backup lives over SSH. **Why:** Makes endpoint ownership explicit and refuses pull-restore configurations for sync because sync always writes its destination locally.

## `timeshift_btrfs_sync/transfer_size.py`

**Role:** Current source/build entry. Btrfs send-stream size measurement and destination-capacity checks.

**Why:** Measures or estimates the exact planned send and compares conservative Btrfs free space plus margin before receive; estimates remain distinct from actual transferred bytes.

- `TransferSizeError` (class, line 28): Raised when send-size measurement or destination-space probing fails. **Why:** Measures or estimates the exact planned send and compares conservative Btrfs free space plus margin before receive; estimates remain distinct from actual transferred bytes.

- `TransferSizeMeasurement` (class, line 33): One measured or estimated Btrfs send-stream size. **Why:** Measures or estimates the exact planned send and compares conservative Btrfs free space plus margin before receive; estimates remain distinct from actual transferred bytes.

- `parse_size_bytes` (function/method, line 41): Parse a binary K/M/G/T/P/E size string into bytes. **Why:** Measures or estimates the exact planned send and compares conservative Btrfs free space plus margin before receive; estimates remain distinct from actual transferred bytes.

- `format_bytes` (function/method, line 66): Format bytes as a compact IEC value plus the exact byte count. **Why:** Measures or estimates the exact planned send and compares conservative Btrfs free space plus margin before receive; estimates remain distinct from actual transferred bytes.

- `parse_btrfs_usage_free_bytes` (function/method, line 81): Return the conservative ``Free (estimated)`` value from raw Btrfs usage. **Why:** Measures or estimates the exact planned send and compares conservative Btrfs free space plus margin before receive; estimates remain distinct from actual transferred bytes.

- `parse_estimate_changed_bytes` (function/method, line 96): Parse the source-side ASCII estimate summary into bytes. **Why:** Measures or estimates the exact planned send and compares conservative Btrfs free space plus margin before receive; estimates remain distinct from actual transferred bytes.

- `exact_send_stream_size` (function/method, line 115): Generate and count the real send stream entirely on the source endpoint. **Why:** Measures or estimates the exact planned send and compares conservative Btrfs free space plus margin before receive; estimates remain distinct from actual transferred bytes.

- `estimated_send_stream_size` (function/method, line 185): Return a fast parent-specific changed-data estimate without file payload. **Why:** Measures or estimates the exact planned send and compares conservative Btrfs free space plus margin before receive; estimates remain distinct from actual transferred bytes.

- `destination_free_bytes` (function/method, line 305): Return conservative Btrfs estimated free bytes for the destination filesystem. **Why:** Measures or estimates the exact planned send and compares conservative Btrfs free space plus margin before receive; estimates remain distinct from actual transferred bytes.

## `timeshift_btrfs_sync/tree_ops.py`

**Role:** Current source/build entry. Single Btrfs tree discovery, deletion, and post-verification engine.

**Why:** Uses one deepest-first Btrfs deletion engine with protected-root checks, exact confirmations and final absence proof; ordinary non-empty roots are refused.

- `TreeDeleteResult` (class, line 16): Record planned, confirmed and remaining paths plus errors and final root-absence proof for one cleanup. **Why:** Uses one deepest-first Btrfs deletion engine with protected-root checks, exact confirmations and final absence proof; ordinary non-empty roots are refused.

- `TreeDeleteResult.success` (property, line 27): Report success only when there are no errors and the configured root is independently verified absent. **Why:** Uses one deepest-first Btrfs deletion engine with protected-root checks, exact confirmations and final absence proof; ordinary non-empty roots are refused. Scoped within `TreeDeleteResult` to use its existing endpoint, state or callback context.

- `NativeCacheDeletionProof` (class, line 32): Exact native identities below a repository root anchored to state/cache/receiver pairs. **Why:** Uses one deepest-first Btrfs deletion engine with protected-root checks, exact confirmations and final absence proof; ordinary non-empty roots are refused.

- `_native_cache_view` (function/method, line 42): Check the surviving repository identity and read live IDs without ordinary directory access. **Why:** Uses one deepest-first Btrfs deletion engine with protected-root checks, exact confirmations and final absence proof; ordinary non-empty roots are refused.

- `_path_exists` (function/method, line 80): Probe endpoint path existence and distinguish absent paths from command errors. **Why:** Uses one deepest-first Btrfs deletion engine with protected-root checks, exact confirmations and final absence proof; ordinary non-empty roots are refused.

- `discover_subvolume_tree` (function/method, line 91): Discover a complete nested Btrfs tree in one endpoint list command. **Why:** Uses one deepest-first Btrfs deletion engine with protected-root checks, exact confirmations and final absence proof; ordinary non-empty roots are refused.

- `list_direct_entries` (function/method, line 117): List exact direct children with shell built-ins on either endpoint. **Why:** Uses one deepest-first Btrfs deletion engine with protected-root checks, exact confirmations and final absence proof; ordinary non-empty roots are refused.

- `_validate_confirmations` (function/method, line 133): Compare planned and confirmed exact paths and record missing or unexpected deletion confirmations. **Why:** Uses one deepest-first Btrfs deletion engine with protected-root checks, exact confirmations and final absence proof; ordinary non-empty roots are refused.

- `_verify_absent` (function/method, line 150): Independently prove the configured root is gone and inventory any surviving subvolumes. **Why:** Uses one deepest-first Btrfs deletion engine with protected-root checks, exact confirmations and final absence proof; ordinary non-empty roots are refused.

- `delete_subvolume_tree` (function/method, line 167): Delete one managed tree deepest-first and prove the root is absent. **Why:** Uses one deepest-first Btrfs deletion engine with protected-root checks, exact confirmations and final absence proof; ordinary non-empty roots are refused.

## `tools/pyinstaller_entry.py`

**Role:** Current source/build entry. Small PyInstaller entry point for building the ts-btrfs executable.

**Why:** Invokes the real CLI through a normal script so PyInstaller can package the same command behavior.

No function or class definitions. The module exposes metadata or invokes the existing CLI entry point.

## Application commands

### `init-config` → `cli.cmd_init_config`

Write one packaged complete TOML profile. This command does not need --config.
The generated file contains every supported configuration key with comments.

Profiles (backup direction and restore direction are independent):
  sync: SSH Timeshift source -> local backup; local restore default
  restore-pull: SSH backup -> local Timeshift restore
  remote-roundtrip: SSH Timeshift -> local backup -> SSH Timeshift restore
  local-backup: local Timeshift -> local backup
  remote-pull: SSH Timeshift -> local backup
  local-restore: local backup -> local Timeshift restore
  remote-push-restore: local backup -> SSH Timeshift restore
  remote-pull-restore: SSH backup -> local Timeshift restore

Examples:
  ts-btrfs init-config --profile local-backup --path ./local-backup.toml
  ts-btrfs init-config --profile remote-push-restore --path ./restore.toml
  ts-btrfs init-config --profile sync --path ./config.toml --force

An existing file is preserved unless --force is supplied. Edit all host/path settings before use.

### `list-snapshots` → `cli.cmd_list_snapshots`

Print Timeshift snapshots, cache_root snapshots, then target_root snapshots, with space on each side.
Use configured source/destination sudo prefixes only for Btrfs/Timeshift reads.
Timeshift --list supplies source tags/descriptions; omitted dates use ordinary JSON reads.
Btrfs lists discover protected paths and nested payloads without requiring sudo ls/cat.
Always compare cache/destination dates and full readonly send/Received UUID pairs.
No sudo shell/file-reader/df, app locks/state/log writes, notifications, transfers,
snapshot creation or cleanup are performed. Timeshift --list can mount its normal repository.
Permission/tool failures remain visible and exit 1 after reporting the other side.
Pair differences are warnings by default; --check-pairs also makes them exit 1.

Auto uses restore rules if restore.mode is ssh or ssh-target, otherwise backup rules.
Backup: source.mode chooses the Timeshift/cache host; destination is always local.
Restore: restore.mode chooses both hosts exactly as the restore command does.
Source/destination headings always identify Timeshift/cache and backup repositories,
even when data would flow from backup to Timeshift during restore.

Examples:
  ts-btrfs list-snapshots --config ./config.toml
  ts-btrfs list-snapshots --config ./restore.toml --workflow restore --include-timeshift

Rows are physical dates plus Timeshift-listed dates not confirmed below snapshot_root.
Metadata origins are labeled; missing originals may use an existing target copy only
when all configured live readonly payload UUIDs match. No state metadata is invented.
Free space prefers ordinary df; native Btrfs reads resolve denied reads/unknown types.
Cache/target own info.json is read without sudo; unresolved metadata remains unknown.

### `test-source` → `cli.cmd_test_source`

Test the configured source command endpoint without sending or deleting snapshots.
SSH mode first verifies the SSH connection; local mode skips SSH. The command then
runs Timeshift --list and Btrfs --version through the configured source sudo/commands.

Example:
  ts-btrfs test-source --config ./config.toml

If it fails, the failing SSH/Timeshift/Btrfs command is the item to repair. This command does not test destination capacity or perform a backup.

### `list-source` → `cli.cmd_list_source`

List Timeshift snapshots found on the configured source.
Fast mode is the default: Timeshift metadata is parsed and expected payload paths are constructed.
Add --verify-btrfs when you need slower per-payload Btrfs verification.

Examples:
  ts-btrfs list-source --config ./config.toml
  ts-btrfs list-source --config ./config.toml --verify-btrfs

Use --verify-btrfs when diagnosing a wrong snapshot_root, missing @/@home payload, or unexpected Btrfs layout. Omit it for normal quick inventory.

### `sync` → `cli.cmd_sync`

Back up Timeshift snapshot payloads from the configured source into the local destination.target_root.
source.mode selects local versus SSH source. Normal sync never writes a remote backup destination.
Without --run or --dry-run, config.default_dry_run selects preview versus real execution.

Flag relationships:
  --dry-run and --run are mutually exclusive. If neither is used, default_dry_run from FILE decides.
  --snapshot DATE restricts discovery/transfer to that Timeshift timestamp and skips automatic manual-snapshot creation for other dates.
  --resend bypasses only the state.json 'already synced' skip; it does not bypass UUID lineage, existing-path, topology, or receive safety checks.
  --prune enables retention after sync even when prune_after_sync=false. prune_after_sync=true enables it without --prune.
  --yes-delete authorizes deletion only when pruning is actually requested and the command is in real-run mode.

Examples:
  ts-btrfs sync --config ./config.toml --dry-run
  ts-btrfs sync --config ./config.toml --run --limit 1
  ts-btrfs sync --config ./config.toml --snapshot 2026-08-14_16-33-59 --run
  ts-btrfs sync --config ./config.toml --run --prune --yes-delete

Troubleshooting:
  If a pull-restore profile is refused, normal remote-source backup needs source.mode=ssh and a local destination; do not use restore.mode=ssh for the same sync profile.
  If transfer-size preflight refuses space, adjust destination capacity or the [stream] transfer-size settings in FILE; --resend does not override capacity safety.

### `prune` → `cli.cmd_prune`

Reconcile complete missing repository pairs, then apply retention without transferring snapshots.
App-created tag O snapshots can also be retired from Timeshift only when they still match
manual_snapshot.marker and their required backup payloads are proven complete.
source.delete_redundant_snapshots (default true) previews proven stale readonly cache dates.
destination.delete_redundant_snapshots (default true) previews destination-only readonly dates
no newer than the latest confirmed state pair, including older leftovers; cache absence and UUID ownership are required.
Real redundant cache/destination deletion runs only after successful sync; standalone prune does not delete extras.

Flag relationships:
  --dry-run and --run are mutually exclusive. If neither is supplied, config.default_dry_run decides.
  A real run may calculate a delete plan, but no retention delete is allowed without --yes-delete.
  --yes-delete does not bypass protected snapshots, keep_latest/common-parent rules, backup proof, or Timeshift marker checks.

Examples:
  ts-btrfs prune --config ./config.toml --dry-run
  ts-btrfs prune --config ./config.toml --run --yes-delete

If the command says 'Refusing to delete without --yes-delete', review the printed plan and rerun with both --run and --yes-delete only if the plan is correct.

### `restore` → `cli.cmd_restore`

Restore backup payloads into source.snapshot_root in Timeshift's native layout.
[restore].mode selects transport: local = local backup -> local Timeshift; ssh = SSH backup -> local Timeshift;
ssh-target = local backup -> SSH Timeshift. source.mode does not select restore direction.
Exactly one of --snapshot DATE or --all is required.

Flag relationships and safety:
  --snapshot DATE performs one full restore and is mutually exclusive with --all.
  --all restores the proven chain newer than the newest safely confirmed shared timestamp.
  --allow-no-common-parent is valid only with --all and is needed only when --all cannot prove a common timestamp; real execution adds stronger typed confirmations.
  --allow-os-identity-mismatch is needed only when identity cannot be proven; real execution requires an additional exact typed acknowledgement.
  --create-pre-restore-snapshot creates one tag O safety snapshot on the Timeshift restore target, never on the backup repository.
  --run requires --i-understand-this-modifies-timeshift; the command still asks for the documented typed retention-risk confirmation before receive.
  --dry-run and --run are mutually exclusive; if neither is supplied, config.default_dry_run decides.

Examples:
  ts-btrfs restore --config ./config.toml --snapshot 2026-08-14_16-33-59 --dry-run
  ts-btrfs restore --config ./config.toml --all --dry-run
  ts-btrfs restore --config ./config.toml --all --run --i-understand-this-modifies-timeshift
  ts-btrfs restore --config ./config.toml --all --allow-no-common-parent --allow-os-identity-mismatch --run --i-understand-this-modifies-timeshift

When a guard refuses a real restore, read the refusal literally: add a danger override only after independently verifying the condition named by that refusal.

### `create-manual` → `cli.cmd_create_manual`

Ask the configured source Timeshift endpoint to create one on-demand snapshot (tag O).
Before creation the command validates source/destination paths and, when backups already exist,
requires UUID-confirmed source/destination continuity so a stray manual snapshot is not created on the wrong source.

Example:
  ts-btrfs create-manual --config ./config.toml --comment 'before kernel upgrade'

This command is always real; it has no --dry-run/--run pair. The supplied comment is passed to Timeshift. Automatic app-created snapshot recognition during retention additionally depends on your configured manual_snapshot.marker.

### `destroy-leftovers` → `cli.cmd_destroy_leftovers`

Permanently destroy selected app-owned Btrfs trees. This ignores state.json and retention rules.
source.snapshot_root is never a target. Dry-run is the default for this maintenance command.

Selection (exactly one is required):
  --delete-source       source.cache_root only
  --delete-destination  destination.target_root only
  --delete-both         both of the above; still never source.snapshot_root

Real deletion requires ALL of: a delete selection, --run, --i-understand-this-destroys-data, and the command's typed confirmations.
--dry-run is optional because preview is already the default when --run is absent. Ordinary non-empty roots are refused; the app does not fall back to recursive ordinary-file removal.

Examples:
  ts-btrfs destroy-leftovers --config ./config.toml --delete-destination --dry-run
  ts-btrfs destroy-leftovers --config ./config.toml --delete-both --run --i-understand-this-destroys-data

### `clear-state` → `cli.cmd_clear_state`

Remove only the configured state_file; snapshots are not deleted. Dry-run is the default.
A real run acquires the existing app lock so state cannot be cleared while sync/prune is active.
After clearing, later sync can recover only entries it can prove again from exact live Btrfs UUID relationships.

Real removal requires BOTH --run and --i-understand-this-clears-state, followed by guarded typed confirmations.
--dry-run is optional because preview is already the default when --run is absent. The command does not create missing destination/helper folders merely to clear state.

Examples:
  ts-btrfs clear-state --config ./config.toml --dry-run
  ts-btrfs clear-state --config ./config.toml --run --i-understand-this-clears-state

### `delete-lock` → `cli.cmd_delete_lock`

Remove only the configured lock_file when it is stale. Dry-run is the default.
This command is not a way to stop or bypass a running ts-btrfs process; if the lock is held, stop the process normally instead.

Real removal requires BOTH --run and --i-understand-this-deletes-lock, followed by guarded typed confirmations.
--dry-run is optional because preview is already the default when --run is absent.

Examples:
  ts-btrfs delete-lock --config ./config.toml --dry-run
  ts-btrfs delete-lock --config ./config.toml --run --i-understand-this-deletes-lock

### `show-state` → `cli.cmd_show_state`

Read the configured local state.json that records completed payloads, source/send UUID identity,
destination Received UUID relationships, and incremental-parent metadata. This command does not modify state.

Examples:
  ts-btrfs show-state --config ./config.toml
  ts-btrfs show-state --config ./config.toml --json

Use --json when you need the complete stored structure for diagnosis or automation. The default table is a compact human-readable summary.

## Standalone shell helper

`delete-btrfs-tree.sh` is preserved as an independent tool. Its safety policy is broader than managed application cleanup: it removes ordinary leftovers after subvolume deletion. The Python runtime never calls it.

- `usage`: print flags, modes and destination-preservation rules so a user can preview before opting into deletion.
- `die`: report a fatal error and stop before subsequent cleanup phases.
- `require_command`: verify each external dependency before examining a destination.
- `discover_outermost_subvolumes`: use NUL-separated inode-256 candidates and prune traversal at outer subvolumes, for native recursive Btrfs deletion and final verification.
- `discover_all_subvolumes_deepest_first`: discover child-before-parent candidates for older Btrfs tools without recursive deletion support.
- Argument parsing: `--help` and `--version` exit without mutation; `--dry-run` is default; `--yes-delete` enables permanent removal; exactly one destination is required.
- `realpath`: resolve the existing destination before refusing `/` and validating its filesystem.
- `findmnt`: require writable Btrfs and reject nested mounts so ordinary cleanup cannot cross a mount boundary.
- `btrfs subvolume show`: prove every inode candidate is an actual subvolume before deletion.
- `btrfs --dry-run subvolume delete --recursive`: show native recursive deletion when supported; older tools print the planned deepest-first order.
- `btrfs subvolume delete [--recursive] --commit-after`: remove validated candidates; a failure stops ordinary cleanup.
- `find`: rediscover remaining subvolumes before ordinary-file removal, and check the destination is empty afterward.
- `rm -rf --`: used only by this original independent helper to remove ordinary leftovers after all subvolumes are gone; this is absent from managed Python tree deletion.

## Systemd, sudoers and Home Assistant commands

- `systemd/ts-btrfs-sync.service` invokes `ts-btrfs sync --config … --run --prune --yes-delete` to run backup and authorized retention; its configured path must be adapted before enabling.
- `systemd/ts-btrfs-sync.timer` schedules the service hourly, randomizes by up to ten minutes and catches missed runs with Persistent=true.
- `sudoers/source-minimal.example` permits only configured Btrfs/Timeshift source commands; ordinary info.json reading uses normal user permissions.
- The supplied Home Assistant queue uses time/MQTT triggers, switch.turn_on for power, connectivity waits, mqtt.publish for job start, MQTT result waits, status parsing, Pushover notifications and script calls. Each configured machine has its own status handling and continuation after timeout/failure. These are external integration examples; none is invoked by the CLI.

## Preserved artifacts

- `dist/ts-btrfs`: original executable, independently verified to report 0.1.84. Kept unchanged; rebuild to obtain an executable for the source release.
- The older nested project and its duplicate docs/tests/helpers were removed. Root documents describe current usage; REMOVED_NESTED_SOURCES.md lists every former path.

Coverage: 573 current source/build symbols; 639 root test symbols.

## Python environment installation

- `python3 -m venv .venv`: creates an isolated Python environment for the project.
- `. .venv/bin/activate`: selects that environment for the current shell.
- `python -m pip install -r requirements.txt`: reads the root requirements file; its `-e .[mqtt,pyinstaller]` entry installs the existing project/CLI, MQTT support and executable builder with their dependencies from pyproject.toml. Run from the project root.
- `python -m pip check`: verifies declared Python dependency compatibility in the environment.
- `python -m pip install -e '.[mqtt]'`: installs optional MQTT publishing support from the existing project extra.
- `deactivate`: restores the shell environment after venv activation.

- `python -c "import paho.mqtt.client; import PyInstaller"`: verifies the full environment contains both required feature modules before building.
- `python3 scripts/build_pyinstaller.py --mode onefile --with-mqtt`: packages the existing CLI with all config templates and the lazy MQTT import into a one-file executable.
