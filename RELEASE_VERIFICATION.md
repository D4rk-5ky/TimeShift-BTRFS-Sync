# Release verification — TimeShift-BTRFS-Sync 0.2.8

Prepared 2026-11-14 from source 0.2.7. Increment by exactly 0.0.1; preserve every earlier version entry and the patch-99 rollover rule. Compare against source 0.2.7 and the supplied TimeShift-BTRFS-Sync-main.zip (source 0.2.2).

## Findings and corrections

Inspected the actual delivered 0.2.7 ZIP and confirmed that its packaged `timeshift_btrfs_sync/data/config.example.toml` already contains `[mail] use_mailx_util = false` and `to_addr = ""`. Its bytes match the 0.2.7 source resource. All eight resources already represent every current supported setting. No missing mailx option is invented or silently enabled. Generated files come from the version of the command invoked; an older installed `ts-btrfs` retains its own templates.

The audit did find misleading profile comments and restore-only defaults. Correct those in this release:

- Disable backup-time `manual_snapshot.enabled` in local-restore, remote-push-restore and remote-pull-restore, matching the existing restore-pull profile. Restore ignores this setting; its explicit opt-in safety-snapshot flag remains unchanged. Backup/roundtrip profiles retain enabled automatic snapshots.
- Change remote-pull-restore's placeholder SSH user from ts-btrfs-sync-user to ts-btrfs-restore-user because this profile's SSH host holds the backup repository. Preserve its actual host/direction/path modes. All names/hosts/accounts still require adaptation to a real deployment.
- Add prominent primary-command, running-host, backup/restore direction, SSH-role, setting-coverage and mailx-location headers to every file. Correct the inverted comment claiming enabled=false may create a snapshot; distinguish creation settings from prune settings, local log/lock prerequisites, unused local SSH examples and the protected Timeshift versus app-created O cleanup exception. Describe the latest common parent as live UUID-proven.
- Preserve every other parsed template value, including dry-run defaults, retention/cleanup flags, notification topics/options, disabled mail/MQTT/live enablement and transfer-size-check defaults. Do not enable credentials, mailx or real runs as part of completeness checks.
- Add CONFIG_PROFILE_AUDIT.md containing every supported key, active/optional counts, all eight profile/file choices and the effective host/path matrix. Expand current README selection to all eight linked resources, explain default config.example generation and source/installed version checks, and update INSTALL/config audit/code maps/ledgers. Preserve both disclaimers verbatim and all original/prior files.

## Configuration coverage and workflow checks

Every profile covers **108 supported scalar/list settings** across the top level and ten tables, with section-qualified active or parseable commented assignments. Coverage is checked against the real loader registries and independently against their dataclass fields; a prose keyword mention cannot satisfy the test. All active files load through the real config parser. **179 commented assignment examples across the profiles** are separately parsed and loaded with coherent temporary credentials where required. Mutually exclusive secrets/options remain alternatives; the audit does not uncomment them together.

| Profile | Source mode | Restore mode | Intended primary use | Automatic backup-time snapshot |
|---|---|---|---|---|
| sync / config.example.toml | ssh | local | SSH Timeshift → local backup; local restore default | enabled |
| remote-roundtrip | ssh | ssh-target | SSH Timeshift → local backup → same SSH Timeshift | enabled |
| restore-pull | local | ssh | SSH backup → local Timeshift | disabled |
| local-backup | local | local | Local Timeshift → local backup | enabled |
| remote-pull | ssh | local | SSH Timeshift → local backup | enabled |
| local-restore | local | local | Local backup → local Timeshift | disabled |
| remote-push-restore | ssh | ssh-target | Local backup → SSH Timeshift | disabled |
| remote-pull-restore | local | ssh | SSH backup → local Timeshift | disabled |

The actual SourceRunner and BackupRepository endpoint factories agree with these modes without running endpoint commands. Both pull-restore profiles still refuse sync under the existing guard. Local workflows ignore documented optional SSH settings; SSH roles name the proper backup/Timeshift host. Backup state remains under its repository, remote only during pull restore. Locks/logs remain local to the running command; restore requires a pre-existing local lock parent. Supplied roots are absolute, cache stays outside Timeshift snapshots and local backup roots do not overlap protected Timeshift/cache roots.

## Runtime/safety scope

All **34 runtime modules other than the package version label are byte-identical to 0.2.7**, including config parsing, CLI/dispatch/help implementation, mail/SMTP/mailx, MQTT/HA monitoring, sync/planning/retention/reconciliation, native Btrfs/deletion safeguards, restore, transport, locks and state/schema. Requirements and the manufacturer card are unchanged. The shell helper changes only its version label. Existing completion payloads/topics, notifications and deletion consent/proof checks are intact. Only four declared parsed template values differ: the three restore-only manual flags and one placeholder SSH user. All other changes are documentation, headers, tests and release metadata.

No source/destination command, actual snapshot operation, live delivery, package installation or service deployment is performed by the config audit. Optional credential examples use temporary fixture files and coherent settings solely for config loading; they are not production credentials.

## Verification performed

- Python 3.14.4: **607 tests run; 603 passed, four existing skips**, in 30.097 seconds. The skips concern the inherited historical remote-lock API absent from current restore. Add 13 meaningful profile tests to the 594-test 0.2.7 suite.
- New tests cover registry/dataclass parity; template/registry/workflow coverage; every actual/commented section-qualified option; all 179 separately loaded optional assignments; intended source/restore/manual/SSH-role values; actual endpoint constructors; existing pull-restore refusal; absolute/contained state/cache/local lock/log paths; unchanged safety/notification/preflight defaults; inactive secrets and compatible SSH/TLS examples; accurate headers/comments; and default/all-profile CLI generation identity.
- All **eight CLI-generated profiles** match current packaged templates byte-for-byte, including the default sync/config.example resource. All pre-existing parsed values remain unchanged except the four explicit restore-profile corrections. An additional copy of current config.example.toml is delivered next to the ZIP and checked against the packaged resource.
- All **80 Python files compile** to scratch outside the release. Global and all 12 subcommands pass **26 real help/version invocations** reporting 0.2.8. Invalid argument combinations, config overwrite refusal/force, isolated show-state and dry-run state/lock maintenance checks pass. Shell syntax/help/version and builder help/version pass.
- Both code maps cover **1,534 qualified symbols at correct source lines**: 633 runtime/build and 901 test classes/functions/methods/nested callbacks. Upper/lowercase mirrors, complete original/prior ledger history, supplied disclaimers and README/INSTALL local links pass checks. All four HA YAML files and both systemd units parse offline.
- Existing mail, manufacturer/card, live monitor, actual pipe/byte/mbuffer/cancellation, storage/restore/retention/safety and other regression tests pass. Installed GNU mailx is exercised only through the inherited isolated capture-MTA test, without real delivery; native Btrfs/Timeshift/SSH/MQTT boundaries are simulated.
- ZIP checks verify safe unique paths, CRC, SHA-256/tree/manifest equality, original/prior comparisons, file modes, fresh extraction and extracted-source help/version/hygiene. Re-run the complete new profile test module against the fresh ZIP extraction, exercising default and all named generation paths again. The package has **114 files**, retaining all **112 prior files** and all **104 supplied original files**. Original comparison: 75 unchanged, 29 modified, ten added, zero removed. Two additions relative to 0.2.7 are CONFIG_PROFILE_AUDIT.md and tests/test_config_profile_contract.py. No Python bytecode, __pycache__, build/test caches, temporary files or scratch scripts are included. Preserve all specified original modes and the three executables; unspecified ZIP modes use 0644 files/0755 directories.

## Limits and supplied executable

This verifies complete example syntax, supported options, logical workflow/host/path roles and CLI/package behavior. It does not establish that placeholder mounts, filesystems, SSH accounts, sudo permissions, retention choices, mail/MQTT servers or systemd environments match a real deployment. No real Btrfs/Timeshift snapshot/send/receive/cleanup/restore, restored boot, SSH/sudo endpoint, Postfix/SMTP inbox delivery, live HA/MQTT service or service installation was tested. Optional examples are checked individually with prerequisites, not every possible user-edited combination. Adapt host paths/accounts and review the current plan before production use.

Python 3.11–3.13, complete dependency installation and PyInstaller builds remain untested. The original dist/ts-btrfs/ts-btrfs is preserved byte-for-byte but cannot start because its supplied _internal runtime, including libpython3.14.so.1.0, is missing. Its originally documented 0.1.84 version cannot be verified. Use/install current Python source or rebuild; PyInstaller is unavailable here. Extracting new source does not update an older installed executable's generated configs.

## Manifest and checksum

RELEASE_MANIFEST.json includes original and 0.2.7-prior file hashes/sizes/modes, supplied archive SHA-256, current release records and explicit added/removed/modified/unchanged lists. Its own hash is excluded to avoid self-reference; the external ZIP checksum covers the whole archive. Null original modes mean no specified Unix permissions. Run `sha256sum -c TimeShift-BTRFS-Sync-0.2.8.zip.sha256` beside the ZIP/sidecar. Earlier release directories and artifacts remain unchanged.
