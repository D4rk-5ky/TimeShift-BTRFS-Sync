# Release verification — TimeShift-BTRFS-Sync 0.2.9

Prepared 2026-11-14 from source 0.2.8. Increment by exactly 0.0.1; preserve every previous ledger entry and patch-99 rollover rule. Compare against source 0.2.8 and the supplied TimeShift-BTRFS-Sync-main.zip (source 0.2.2).

## Direct script usage

Extract the full project and keep root timeshift_btrfs_sync.py beside the complete timeshift_btrfs_sync/ directory. With Python 3.11 or newer:

```bash
python3 timeshift_btrfs_sync.py --version
python3 timeshift_btrfs_sync.py --help
python3 timeshift_btrfs_sync.py init-config --profile local-backup --path ./config.toml
# Edit the generated file before contacting actual hosts or using real mounts.
python3 timeshift_btrfs_sync.py sync --config ./config.toml --dry-run
```

No venv, pip installation or PyInstaller build is needed for core source use. The executable/shebang form `./timeshift_btrfs_sync.py --help` works when the extracted executable permission is present; otherwise use Python explicitly or chmod +x the script. An absolute script path works from another directory. The launcher leaves the working directory unchanged, so relative paths retain normal CLI interpretation. Existing maintenance commands still require absolute metadata paths. Shared help retains the ts-btrfs command name; substitute the script prefix in examples.

This is a source launcher, not a self-contained flattened file. Copying the launcher alone gives a clear full-project extraction message. Optional MQTT still requires paho-mqtt available to the interpreter in use. External Btrfs/Timeshift/SSH/sudo and configured optional tools remain required; mailx additionally needs its installed client/MTA. The launcher neither installs dependencies nor configures services. PyInstaller is only needed to build a binary.

## What changed

- Add root timeshift_btrfs_sync.py with Python3 shebang and 0755 executable mode. Its main guard checks Python>=3.11 and adjacent package __init__.py/cli.py, then imports the existing cli.main and forwards its return code through SystemExit. No duplicate parser/dispatcher or application functions are added. Importing the script without __main__ does not dispatch the CLI.
- Preserve standard Python import resolution so the adjacent package wins over the same-named script, with no sys.path override or chdir. Preserve every existing command, flag, config resource, exit code, validation, lock and destructive-action confirmation by calling the same main function.
- Document direct script use first in README/INSTALL, with safe config generation/dry-run examples, executable permission, complete-project requirement, relative paths and optional dependency behavior. Add launcher command/guard explanations to the code map/config audit. Align all eight template headers and source/test/helper metadata to 0.2.9; parsed option values are unchanged. Synchronize full uppercase/lowercase maps/ledgers and preserve both disclaimers and all original/prior files.

## Runtime and safety scope

All **34 existing runtime modules other than the package version label are byte-identical to 0.2.8**, including CLI/parser/dispatch, config parsing, mail/SMTP/mailx, MQTT/HA monitoring, actual byte measurement, sync/planning/retention/reconciliation, restore, native Btrfs/delete guards, transport, locking and state/schema. Existing module and build entry points, requirements and the manufacturer card are unchanged. All eight parsed configurations are identical to 0.2.8; only their release-header comments change. The standalone shell helper changes only its release label.

No real backup, restore, deletion, service/dependency installation, remote endpoint or notification delivery is performed by release preparation. Launcher tests use ordinary temporary files, actual harmless subprocess CLI calls, mocked exit/unsupported-version conditions and disabled third-party site packages. Existing consent/absolute-path/overwrite refusals remain active through the new route.

## Verification performed

- Python 3.14.4: **618 tests run; 614 passed, four existing skips**, in 43.547 seconds. The inherited skips concern the historical remote-lock API absent from current restore. Add 11 launcher regressions to the 607-test 0.2.8 suite.
- The new launcher passes **all 26 global/subcommand help/version routes with `-S` site packages disabled**, environment Python path removed and no installation/venv activation. The module entry point separately passes its existing 26 routes, totaling 52 primary module/script help/version checks. Direct executable/shebang version invocation also passes.
- Default and all eight named config profiles are generated from a separate working directory through the actual script, byte-identical to packaged current resources. Caller-relative config and state reads are correct; existing unsafe relative maintenance targets still refuse, absolute-target dry-run succeeds and original file bytes remain unchanged. Existing init-config overwrite refusal and CLI/config exit 2 are preserved.
- Shared-main return code forwarding, no dispatch on import, adjacent package-versus-script resolution, clear missing-package diagnostics, simulated Python<3.11 pre-import guard and executable permission/shebang execution all pass. No launcher test runs Btrfs, Timeshift, SSH or actual mail/broker delivery.
- All existing 13 profile contract tests pass: all 108 supported settings in each of eight complete templates, 179 separately loaded optional assignments, runtime field/registry coverage, named workflow/SSH/path roles and default/all-profile generation identity. Earlier mail/card/live-monitor/storage/restore/cleanup/pipe/mbuffer/cancellation safety tests remain passing.
- All **82 Python files compile** to scratch outside the release. Parser refusals, all eight CLI-generated profiles, config overwrite/force, isolated show-state/dry-run state/lock maintenance, shell syntax/help/version and builder help/version checks pass.
- Both full code maps cover **1,547 qualified symbols at correct source lines**: 633 runtime/build and 914 test classes/functions/methods/nested callbacks. The launcher defines no functions, but has its own detailed command/main-guard section. Upper/lowercase mirrors, complete original/prior history, supplied disclaimers and README/INSTALL local links pass checks. All four HA YAML files and both systemd units parse offline.
- ZIP verification checks safe unique paths, CRC, SHA-256/tree/manifest equality, original/prior comparisons, explicit Unix modes and fresh extraction. Restore recorded file permissions in the verification extraction (Python ZipFile itself does not restore Unix modes), then re-run extracted-source CLI/hygiene/profile tests and the complete new launcher test module. Thus direct execution, site-package-free CLI calls and generation are tested from the actual ZIP contents too.
- The full ZIP contains **116 files**, preserving all **114 prior files** and all **104 supplied original files**. Original comparison: 75 unchanged, 29 modified, 12 added, zero removed. Two additions relative to 0.2.8 are root timeshift_btrfs_sync.py and tests/test_script_launcher.py. No Python bytecode, __pycache__, build/test caches, scratch scripts or temporary files are included. Preserve all specified original modes and three original executables, and add executable mode for the launcher; unspecified original ZIP modes use 0644 files/0755 directories.

## Limits and preserved original executable

Only Python 3.14.4 was available for actual execution. Python 3.11–3.13 and actual older-interpreter execution remain untested; the minimum-version branch is simulated. Direct no-site-package startup/profile/metadata operations are tested, while real Btrfs/Timeshift backup/send/receive/retention/restore, restored boot, SSH/sudo permissions, SMTP/Postfix inbox delivery, live HA/MQTT and deployed systemd behavior remain untested. Existing installed GNU Mailutils tests only use an isolated fake MTA. Actual mounts, external tools and optional interpreter dependencies must match the user's selected environment.

The original dist/ts-btrfs/ts-btrfs remains preserved byte-for-byte but cannot start because its supplied _internal runtime, including libpython3.14.so.1.0, is missing. Its originally documented 0.1.84 version cannot be verified. The new source launcher provides direct access to current Python code and does not repair that old binary. PyInstaller is unavailable here, so binary builds and complete dependency installation remain untested.

## Manifest and checksum

RELEASE_MANIFEST.json contains original and 0.2.8-prior hashes/sizes/modes, supplied archive SHA-256, current records and explicit changed/unchanged/added/removed lists. Exclude its own hash to avoid self-reference; the archive checksum covers the complete ZIP. Null original modes indicate no supplied Unix permissions. Run `sha256sum -c TimeShift-BTRFS-Sync-0.2.9.zip.sha256` beside the ZIP/sidecar. Earlier source releases and artifacts remain unchanged.
