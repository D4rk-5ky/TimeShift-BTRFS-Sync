# Installation

Current source release: **0.2.0**. Install from the project root. The included original `dist/ts-btrfs` reports **0.1.84** and has not been rebuilt; use `python3 -m timeshift_btrfs_sync` or rebuild the executable from this source before treating it as the current release. The active package is timeshift_btrfs_sync/; project documentation and helpers live at the project root.

Normal sync runs on the backup/destination machine. The Timeshift source is reached over SSH or selected locally. Restore may also run on the Timeshift machine and pull a backup repository over SSH when `[restore] mode = "ssh"` is selected. The selected endpoints need the commands and minimal permissions described in the README. `cat` and `id` are not run through sudo during normal discovery. The configured source account must have normal traversal/list/read permission for `<source.snapshot_root>/<date>/info.json`. When metadata access fails, the app reports the effective source account name and UID. Prefer a stable source Btrfs mount created by a privileged administrator in `/etc/fstab`, then grant that account narrow Unix mode or POSIX ACL access as documented in README.md.


The executable or Python install does **not** include system tools such as `btrfs`, `timeshift`, `ssh`, `sudo`, `wc`, `mbuffer`, or `sshpass`. Those must be installed on the relevant machines.

## System packages

On a Debian/Ubuntu style destination machine, install the tools you plan to use:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip openssh-client btrfs-progs
```

Optional tools:

```bash
sudo apt install mbuffer
sudo apt install sshpass
```

Transfer-size preflight is disabled by default. When enabled with the default `transfer_size_mode = "estimate"`, the source endpoint must support `btrfs send --no-data`, `btrfs receive --dump`, and a POSIX-compatible `awk`; estimate reduction runs there under `LC_ALL=C` and returns only an ASCII byte count. When explicitly enabled with `transfer_size_mode = "exact"`, exact measurement uses the standard `wc` utility on the source endpoint; it is normally provided by GNU coreutils. Use `mbuffer` only if `[stream].use_mbuffer = true`. `sshpass` is required only for remote-account password authentication when no identity passphrase is configured. Encrypted private keys use the app-generated OpenSSH askpass helper and do not require a separate askpass package. Key-based SSH remains recommended.

## Encrypted private-key passphrases

Create an owner-only passphrase file on the machine running `ts-btrfs`:

```bash
sudo install -d -m 700 /root/.config/ts-btrfs
sudo install -m 600 /dev/null /root/.config/ts-btrfs/identity.passphrase
sudo nano /root/.config/ts-btrfs/identity.passphrase
```

Then configure:

```toml
[ssh]
identity_file = "/root/.ssh/timeshift-btrfs-sync"
identity_passphrase_file = "/root/.config/ts-btrfs/identity.passphrase"
```

The identity passphrase unlocks the local private key. It is separate from `password`/`password_file`, which authenticate the remote account. Both families may be present when both prompts are genuinely required. Remove `BatchMode=yes` whenever either family is configured.

## Install from source in a virtual environment

From the extracted project root, using Python 3.11 or newer:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
ts-btrfs --version
```

Run the install command from the directory containing `requirements.txt` and `pyproject.toml`. The requirements file uses `-e .[mqtt,pyinstaller]` to install this project, its `ts-btrfs` command, **paho-mqtt** for MQTT and **PyInstaller** for executable builds. Pip resolves their transitive dependencies and the build backend declared in `pyproject.toml`; there is no second dependency list to maintain. `python -m pip` uses the activated venv. Do not use sudo for these pip commands.

Check that both modules are available and build an executable with MQTT included:

```bash
python -c "import paho.mqtt.client; import PyInstaller; print('MQTT and PyInstaller imports passed')"
python3 scripts/build_pyinstaller.py --mode onefile --with-mqtt
```

`--with-mqtt` is required to include the lazily imported MQTT module in the executable. The application config still controls whether notifications are enabled. Pip installs Python packages; external tools such as Btrfs, Timeshift and SSH must be installed separately using the system-package instructions above.

To activate the same environment in another terminal or a later session, run `. .venv/bin/activate` from the project root. Run `deactivate` to leave it. You can also invoke `.venv/bin/ts-btrfs --version` without activating the environment. An editable installation refers to this source directory, so keep it in place or reinstall after moving it.

For a smaller source-only environment, the alternative `python -m pip install -e .` installs the core application. `python -m pip install -e '.[mqtt]'` installs the core with MQTT only; `python -m pip install -e '.[pyinstaller]'` installs the core with the executable builder only. These alternatives are not required after installing the full `requirements.txt`.

Email notifications use Python standard library modules, so they do not need an extra Python package.

## Create a config

Generate the normal sync/local-restore profile and edit it:

```bash
ts-btrfs init-config --profile sync --path ./config.toml
nano config.toml
```

For pulling a remote SSH backup into local Timeshift, generate the dedicated complete profile instead:

```bash
ts-btrfs init-config --profile restore-pull --path ./config-restore-pull.toml
nano config-restore-pull.toml
```

For an SSH Timeshift source backed up locally and push-restored back to the same SSH host, generate:

```bash
ts-btrfs init-config --profile remote-roundtrip --path ./config-remote-roundtrip.toml
nano config-remote-roundtrip.toml
```

The five explicitly named workflow profiles can also be generated directly:

```bash
ts-btrfs init-config --profile local-backup --path ./example-config-local-backup.toml
ts-btrfs init-config --profile remote-pull --path ./example-config-remote-pull.toml
ts-btrfs init-config --profile local-restore --path ./example-config-local-restore.toml
ts-btrfs init-config --profile remote-push-restore --path ./example-config-remote-push-restore.toml
ts-btrfs init-config --profile remote-pull-restore --path ./example-config-remote-pull-restore.toml
```

`local-backup` and `remote-pull` back up local and SSH Timeshift sources respectively. `local-restore` restores a local backup locally; `remote-push-restore` sends a local backup to SSH Timeshift; `remote-pull-restore` retrieves an SSH backup into local Timeshift. All eight profiles contain every supported setting. Adapt their paths, accounts and permissions before running them.

The pull-restore profile is restore-only. The app refuses `sync` with `[restore] mode = "ssh"` because sync always writes `destination.target_root` locally while pull restore reads that path on the SSH host.

All profiles document every supported setting. The `[ssh]` section includes key files, `identity_passphrase`/`identity_passphrase_file`, separate remote-account `password`/`password_file`, port, compression, cipher, ControlMaster, host-key verification, connection timeouts, keepalives, jump hosts, and extra OpenSSH arguments.

Recommended first checks:

```bash
ts-btrfs test-source --config ./config.toml
ts-btrfs list-source --config ./config.toml
ts-btrfs sync --config ./config.toml --dry-run
ts-btrfs sync --config ./config.toml --run --limit 1
ts-btrfs restore --config ./config.toml --snapshot 2026-07-15_05-00-02 --dry-run
ts-btrfs restore --config ./config.toml --all --dry-run
```


## Service-account snapshot and space inventory

After installing this source into the venv, run as your normal account:

```bash
. .venv/bin/activate
ts-btrfs list-snapshots --config ./config.toml
# Inspect the endpoints selected by restore:
ts-btrfs list-snapshots --config ./restore.toml --workflow restore
ts-btrfs list-snapshots --help
```

The output always orders **Timeshift snapshots**, **cache_root snapshots**, then **target_root snapshots**, with independent device/space reports. `--include-timeshift` remains accepted but is no longer necessary. Without installation, run `python3 -m timeshift_btrfs_sync list-snapshots --config ./config.toml` from the new project root. The preserved original executable is older and does not contain this command; install current source or rebuild using the requirements/venv instructions below.

`--workflow auto` uses restore hosts for `restore.mode = "ssh"` or `"ssh-target"`, otherwise backup hosts. Explicit `backup` follows source.mode and a local target; explicit `restore` follows both restore hosts. All eight supplied config profiles support this listing without new config keys.

Install configured Btrfs tools, Timeshift on the original-snapshot host, and GNU coreutils on each inspected host. The local/SSH service account may keep passwordless sudo limited to Btrfs and Timeshift, as in `sudoers/source-minimal.example`. Set the relevant source/destination `sudo = "sudo -n"`; these prefixes are honored only for Btrfs/Timeshift read commands. No sudo shell, cat, ls, base64, df or Python rule is required or used. The Btrfs inventory can enumerate protected payload paths even if ordinary directory scanning fails, and Timeshift --list supplies source tags/descriptions when direct JSON reads are denied. Timeshift listing can mount its normal repository and produce its own normal logs. The app creates no snapshots and does not write app locks/state/logs, transfer, prune or restore during listing.

For inventory, the Timeshift source table takes tags/descriptions from `timeshift --list`, which already reads Timeshift control files. The app skips redundant source JSON reads for reported dates. Physically discovered dates omitted by Timeshift, failed Timeshift listing, or a known filesystem mismatch still use ordinary source JSON reads. Cache and target tables always prefer their own readable regular `info.json` files, read as the login/SSH user without sudo; these preserve stored tags when source tags differ. No generic privileged file reader or additional permission is needed for readable files. App-created caches normally lack control files, so their fallback uses current same-date source data or, after original expiry, a target copy proven by all configured readonly send/received UUIDs. Missing/invalid/unreadable metadata stays visibly unknown when no supported fallback exists. The command changes no ACLs, ownership, modes or sudoers.

Space prefers unprivileged df; protected paths fall back to configured sudo Btrfs filesystem usage, with statfs/estimated origin labeled. See README.md for exact flag, row/count, failure and metadata semantics. A denied or incomplete required reader returns 1 after still reporting all three tables.

## Restore permissions

`restore` writes directly into the Timeshift repository. Timeshift expects an ordinary `<snapshot_root>/<date>` directory containing writable Btrfs payload subvolumes and a regular `info.json`, so restore needs both Btrfs privilege and ordinary directory/file privilege on the source endpoint.

The same permissions are used for both restore selections:

```bash
# One full snapshot.
ts-btrfs restore --config ./config.toml --snapshot 2026-07-15_05-00-02 --dry-run

# Newest safely confirmed shared timestamp, then every newer backup.
ts-btrfs restore --config ./config.toml --all --dry-run
```

For local restore, the simplest supported invocation is to run the app as root:

```bash
sudo python3 -m timeshift_btrfs_sync restore \
  --config ./config-local.toml \
  --all \
  --run \
  --i-understand-this-modifies-timeshift
```

Running the app as an unprivileged user is possible only when `source.sudo` has narrow passwordless permission for:

```text
btrfs
timeshift
test
ls
base64
mkdir
tee
chmod
mv
rm
rmdir
```

For SSH restore, those permissions must be configured for the remote SSH account on the source host. Running only the destination-side process as root does not provide remote permission. The command does not need passwordless `sh` or `bash`, and granting a general shell is not recommended.

`--all` intersects the timestamp directories physically present below the configured Timeshift and backup roots and tests candidates newest-to-oldest. Every configured payload must be a real Btrfs subvolume on both sides. Exact proof is preferred: a completed state record links current Timeshift UUID to `original_source_uuid` and backup Received UUID to `send_source_uuid`, or retained-cache metadata links current Timeshift UUID → cache Parent UUID and cache send identity → backup Received UUID. Missing or invalid state is ignored with a visible diagnostic rather than trusted. When exact state/cache lineage is unavailable, the same physical timestamp is still safely confirmed when source and backup `info.json` match stable `sys-uuid` and `type`; tags, comments, counters, and other mutable fields are ignored. This fallback is valid because restore full-receives the exact backup copy of the common timestamp into the hidden target-side chain instead of using the visible Timeshift snapshot as the receive parent. If no candidate passes either proof, a real full-chain restore additionally requires `--allow-no-common-parent`, the phrase `RESTORE ALL WITHOUT COMMON PARENT`, and the configured job name. If no current OS identity can be matched and no exact Btrfs proof overrides that warning, real restore also requires `--allow-os-identity-mismatch` and `I UNDERSTAND THIS BACKUP MAY BELONG TO ANOTHER OS`.

Optionally add `--create-pre-restore-snapshot`. After all restore confirmations and before any receive, the app creates one Timeshift on-demand safety snapshot on the Timeshift target, verifies the new timestamp and every configured Btrfs payload, and leaves it in place even if restore later fails. Local restore creates it locally; SSH-target restore creates it on that SSH Timeshift host; SSH-backup pull restore creates it locally and never runs Timeshift creation on the remote backup host. This flag is independent of `[manual_snapshot]`, which applies to `sync`.

Every real restore also explains that the exact original `info.json` preserves H/D/W/M tags, so normal retention can later prune a restored snapshot or an existing tagged snapshot older than the restored snapshot. Before any receive begins, local and SSH modes both require this exact sentence:

```text
I UNDERSTAND TIMESHIFT MAY DELETE RESTORED SNAPSHOTS OR OLDER THAN RESTORED SNAPSHOTS
```

Review or pause Timeshift scheduling and retention until the intended rollback is complete.

When a common parent exists, restore always full-receives that exact backup into a hidden chain on the Timeshift receiving filesystem before sending newer backups incrementally. This prevents a source-side cache snapshot from being mistaken for a receiver-side Btrfs parent or clone source. Before every incremental, the hidden parent must be read-only and its Received UUID must match the exact backup parent send identity. An explicit missing-parent/clone-source receive error retries only that exact payload once as a full stream; unrelated failures remain hard errors. The final Timeshift payloads are writable Btrfs CoW snapshots of the hidden read-only chain, so they retain shared extents after the hidden chain is deleted.

### Pull restore from an SSH backup host

Use a separate restore config with `[restore] mode = "ssh"`, `[ssh]` pointing to the backup host, and `[destination].target_root` plus `state_file` set to their paths on that host. `lock_file`, `source.snapshot_root`, and `source.cache_root` must be local paths on the machine running the restore. `source.mode` remains sync-only. Preview with:

```bash
ts-btrfs restore --config ./config-restore-pull.toml \
  --all \
  --dry-run
```

The remote backup account needs narrow passwordless permission through `destination.sudo` for Btrfs list/show/send and the read-only `test`, `ls`, and `base64` operations used to inspect backup date directories, control files, and `state.json`. The app prefixes those individual commands and does not invoke a privileged shell. It does not need write access to a remote lock file or `flock`. The local machine needs the restore-target permissions described above and write access to the configured local `lock_file`.

Do not use the same path interpretation blindly for scheduled sync. In the pull profile, `[restore] mode = "ssh"` makes `destination.target_root` and `state_file` remote only for restore; `lock_file` remains local and normal sync/prune semantics remain unchanged.

## PyInstaller builds

PyInstaller can create a Linux executable for the machine/distro where the build is run. Build on the same OS family and CPU architecture where you expect to run the executable.

PyInstaller bundles the Python app. It does **not** bundle external system commands. The destination still needs commands like `btrfs`, `ssh`, `sudo`, `wc`, optional `mbuffer`, and optional `sshpass` installed. The source still needs `timeshift` and `btrfs`.

The project build helper also bundles the complete `timeshift_btrfs_sync/data/` directory. This is required so the frozen executable can generate all eight packaged config profiles with `init-config`.

### Prepare the complete executable build environment

From the project folder:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

The requirements file already includes both MQTT and PyInstaller. The equivalent direct installation is:

```bash
python3 -m pip install -e '.[mqtt,pyinstaller]'
```

### Folder-style executable

This creates `dist/ts-btrfs/ts-btrfs` plus supporting files in the same folder.

```bash
python3 scripts/build_pyinstaller.py --mode onedir
./dist/ts-btrfs/ts-btrfs --version
```

Use this when you want easier inspection/debugging and usually faster startup. Copy the whole `dist/ts-btrfs/` folder to the destination machine.

### One-file executable

This creates one executable at `dist/ts-btrfs`.

```bash
python3 scripts/build_pyinstaller.py --mode onefile
./dist/ts-btrfs --version
```

Use this when you want one file that is easy to copy. Startup can be slower because the executable extracts itself to a temporary directory when it starts.

### Build both formats

```bash
python3 scripts/build_pyinstaller.py --mode both
```

With MQTT support included:

```bash
python3 scripts/build_pyinstaller.py --mode both --with-mqtt
```

### Direct PyInstaller commands

The helper script above is recommended, but these are the direct commands it wraps.

Folder-style executable:

```bash
python3 -m PyInstaller --clean --name ts-btrfs --console --paths . --add-data "timeshift_btrfs_sync/data:timeshift_btrfs_sync/data" tools/pyinstaller_entry.py
```

One-file executable:

```bash
python3 -m PyInstaller --clean --onefile --name ts-btrfs --console --paths . --add-data "timeshift_btrfs_sync/data:timeshift_btrfs_sync/data" tools/pyinstaller_entry.py
```

With MQTT support, add:

```bash
--hidden-import paho.mqtt.client
```

### Running the executable

The executable uses the same config file and command flags as the Python module.

Folder-style build:

```bash
./dist/ts-btrfs/ts-btrfs test-source --config ./config.toml
./dist/ts-btrfs/ts-btrfs sync --config ./config.toml --dry-run
```

One-file build:

```bash
./dist/ts-btrfs test-source --config ./config.toml
./dist/ts-btrfs sync --config ./config.toml --dry-run
```

Verify that the frozen executable contains every config profile:

```bash
tmpdir=$(mktemp -d)
./dist/ts-btrfs init-config --profile sync --path "$tmpdir/sync.toml"
./dist/ts-btrfs init-config --profile restore-pull --path "$tmpdir/restore-pull.toml"
./dist/ts-btrfs init-config --profile remote-roundtrip --path "$tmpdir/remote-roundtrip.toml"
./dist/ts-btrfs init-config --profile local-backup --path "$tmpdir/local-backup.toml"
./dist/ts-btrfs init-config --profile remote-pull --path "$tmpdir/remote-pull.toml"
./dist/ts-btrfs init-config --profile local-restore --path "$tmpdir/local-restore.toml"
./dist/ts-btrfs init-config --profile remote-push-restore --path "$tmpdir/remote-push-restore.toml"
./dist/ts-btrfs init-config --profile remote-pull-restore --path "$tmpdir/remote-pull-restore.toml"
ls -l "$tmpdir"/*.toml
rm -f "$tmpdir"/*.toml
rmdir "$tmpdir"
```

### Cleanup build artifacts

PyInstaller creates `build/`, `dist/`, and a `.spec` file. These are build artifacts, not backup data. Inspect and remove them manually before a clean rebuild; the application itself never recursively deletes backup or source-cache trees through ordinary filesystem commands.

## Moving configured roots

State schema version 3 stores source snapshot paths relative to `source.snapshot_root`, app-created send paths relative to `source.cache_root`, and destination paths relative to `destination.target_root`. After moving or remounting one of these roots, update the matching config value. The app resolves the saved suffix under the new root and still requires the same Btrfs UUID before it accepts an incremental parent. State files must already use the current relative schema.

When a writable Timeshift snapshot needs a read-only send-cache copy, the app first checks the root-scoped cache inventory. Btrfs list paths may include an on-disk prefix, may be relative as `<date>/@`, or may be bare `@` when the date parent itself is probed. If the bulk index missed the child, one authoritative parent-scoped UUID/read-only listing is performed before creation. A valid existing cache snapshot is reused after read-only and Parent UUID checks; an unavailable safety listing aborts instead of guessing. The exact target is therefore never blindly passed to `btrfs subvolume snapshot -r`, so an existing `<date>/@` cannot become a nested `<date>/@/@`.

## Tracking packaged example configs in Git

The root `.gitignore` allows `pyproject.toml` and all eight packaged examples. The current package contains no nested `.gitignore`. When copying over an older checkout, an obsolete `timeshift_btrfs_sync/.gitignore` can remain and its `*.toml` rule can override the root exceptions. Use a fresh checkout/release directory or remove that obsolete duplicate as described in NESTED_DOCUMENT_AUDIT.md.

To identify the actual ignore rule in your checkout:

```bash
git check-ignore -v -- timeshift_btrfs_sync/data/example-config-local-backup.toml
```

To stage only the five new packaged examples despite an ignore rule:

```bash
git add -f -- timeshift_btrfs_sync/data/example-config-*.toml
```

After correcting the ignore rule, `git add -A` stages the packaged examples normally. The current `.gitignore` continues to ignore private/runtime configs.

## State reconciliation and bounded cache cleanup

Current `sync` recovers missing complete UUID-proven dates even from populated state before transfer planning. Standalone `prune` and sync cleanup reconcile before retention. The `[source]` option `delete_redundant_snapshots = true` defaults to true; it removes only verified cache-only dates inside the range of complete live state pairs, under a dedicated app-owned per-job cache_root. `cleanup_superseded_cache = false` disables all cache deletion; the new option false disables only this extra cleanup. Neither option disables state repair. No additional dependency or sudo permission is required.

Preview with `python3 -m timeshift_btrfs_sync prune --config ./config.toml --dry-run`; use `--run --yes-delete` for reviewed real cleanup. Dry-run never saves recovered state or deletes snapshots. Cache-only cleanup protects destination presence, tracked dates, explicit exclusions, incomplete-transfer parents, out-of-window dates, symlinks, unexpected entries/nested subvolumes, inaccessible paths and changed/unproven identities. See README.md for exact bounds and counter meanings. Ordinary source Timeshift retention stays Timeshift-managed; native restore behavior is unchanged.

## Check cache/destination differences

`list-snapshots` always prints a comparison after its three tables, including every cache-only, destination-only and unproven shared date. It checks all configured readonly payload UUIDs and labels incomplete discovery. O/H/D/W/M/B tag changes do not affect pair identity. Use `--check-pairs` to return exit code 1 unless enabled, complete cache/destination inventories fully match; without it, pair differences are warnings and the existing read-failure exit policy applies. This is read-only and never reads/rebuilds state or deletes snapshots.

```bash
python3 -m timeshift_btrfs_sync list-snapshots --config ./config.toml --check-pairs
python3 -m timeshift_btrfs_sync prune --config ./config.toml --dry-run
# After reviewing the plan:
python3 -m timeshift_btrfs_sync sync --config ./config.toml --run --prune --yes-delete
```

A successful sync without `--prune` or `prune_after_sync = true` does not clean leftover cache dates. Safe redundant cleanup requires both source cache-cleanup switches, existing deletion consent and verified ownership, bounds and receiver absence; protected, active-parent, ambiguous or newer dates remain. The listing comparison describes observed storage, while prune reconciles missing pairs into state before building its plan. Unknown `df` type (`-`) uses native Btrfs identity/usage rather than being mislabeled as a non-Btrfs filesystem. Use the current source release or rebuild the preserved older executable.

## Native stale-cache cleanup after successful sync

The extra cleanup controlled by `[source].delete_redundant_snapshots = true` runs after successful real sync and paired retention, with `--prune` or `prune_after_sync = true`, the existing cache-cleanup master switch and `--yes-delete`. Standalone prune can preview extras but does not delete them in a real standalone run. A verified no-op sync can qualify.

The source Btrfs tool must support `subvolume delete --subvolid` and `--commit-after`. Only configured Btrfs commands use sudo; no privileged shell/file reader or permission/ownership change is needed. Confirm dedicated cache ownership through native root UUID/ID, containment and canonical state/readonly receiver UUID pairs. Then dated readonly snapshots and containers of readonly snapshots no newer than the latest proven pair can be retired, including older or partial cache layouts. Contents inside qualifying Btrfs trees are deleted with them. Tracked/protected/newer dates, incomplete transfers, receiver copies and uncertain/changed/foreign/writable identities stay protected. Ordinary cache directory access is not required after this proof. Final privileged Btrfs ID enumeration confirms absence. See [Btrfs delete options](https://btrfs.readthedocs.io/en/latest/btrfs-subvolume.html); unsupported flags produce a retry error.

## Destination-only cleanup configuration

All eight packaged profiles include `[destination].delete_redundant_snapshots = true`; the same default applies when omitted. This receiver switch is independent of the source cache cleanup switches. Use dedicated cache and destination roots per job. After successful sync and paired retention, cleanup only considers untracked native readonly Timeshift-date trees no newer than the latest complete UUID-confirmed state pair, including older-than-first leftovers, absent from a freshly readable native source-cache inventory. Complete root/state/cache/receiver ownership, canonical paths and immutable identities must be proved; protected, tracked, newer-than-latest, writable and uncertain dates remain. There is no lower date limit.

```bash
python -m timeshift_btrfs_sync prune --config ./config.toml --dry-run
python -m timeshift_btrfs_sync sync --config ./config.toml --run --prune --yes-delete
python -m timeshift_btrfs_sync list-snapshots --config ./config.toml --check-pairs
```

Dry prune previews both extra cleanup sides without deleting or writing state. Standalone real prune skips extra cleanup because no sync succeeded in that invocation. Listing is read-only and reports differences/range labels; it exits 1 with --check-pairs when parity is unconfirmed. Destination cleanup summaries distinguish redundant confirmations from paired/state removal. The shared numeric-ID deletion engine uses the configured Btrfs sudo command only, with --subvolid and --commit-after support required on the destination as well as the source. Unsupported tools or failed proof keep explicit retry/skip results. Live source/SSH access and actual Btrfs mutations must be checked in your environment; equal counts cannot be promised for protected or newer-than-latest dates.
