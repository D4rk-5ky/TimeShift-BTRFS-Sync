# Installation

Normal sync runs on the backup/destination machine. The Timeshift source is reached over SSH or selected locally. Restore may also run on the Timeshift machine and pull a backup repository over SSH when `[restore] mode = "ssh"` is selected. The selected endpoints need the commands and minimal permissions described in the README. `cat` and `id` are not run through sudo during normal discovery. The configured source account must have normal traversal/list/read permission for `<source.snapshot_root>/<date>/info.json`. When metadata access fails, the app reports the effective source account name and UID. Prefer a stable source Btrfs mount created by a privileged administrator in `/etc/fstab`, then grant that account narrow Unix mode or POSIX ACL access as documented in README.md.


The executable or Python install does **not** include system tools such as `btrfs`, `timeshift`, `ssh`, `sudo`, `mbuffer`, or `sshpass`. Those must be installed on the relevant machines.

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

Use `mbuffer` only if `[stream].use_mbuffer = true`. Use `sshpass` only if `[ssh].password` or `[ssh].password_file` is configured. Key-based SSH is recommended.

## Install from source in a virtual environment

From the project folder:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e .
ts-btrfs --version
```

With MQTT notification support:

```bash
python3 -m pip install -e '.[mqtt]'
```

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

Both profiles document every supported setting. The `[ssh]` section includes key files, port, password/password_file through `sshpass`, compression, cipher, ControlMaster, host-key verification, connection timeouts, keepalives, jump hosts, and extra OpenSSH arguments.

Recommended first checks:

```bash
ts-btrfs test-source --config ./config.toml
ts-btrfs list-source --config ./config.toml
ts-btrfs sync --config ./config.toml --dry-run
ts-btrfs sync --config ./config.toml --run --limit 1
ts-btrfs restore --config ./config.toml --snapshot 2026-07-15_05-00-02 --dry-run
ts-btrfs restore --config ./config.toml --all --dry-run
```


## Restore permissions

`restore` writes directly into the Timeshift repository. Timeshift expects an ordinary `<snapshot_root>/<date>` directory containing writable Btrfs payload subvolumes and a regular `info.json`, so restore needs both Btrfs privilege and ordinary directory/file privilege on the source endpoint.

The same permissions are used for both restore selections:

```bash
# One full snapshot.
ts-btrfs restore --config ./config.toml --snapshot 2026-07-15_05-00-02 --dry-run

# Latest UUID- and info.json-confirmed common parent, then every newer backup.
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
mkdir
tee
chmod
mv
rm
rmdir
```

For SSH restore, those permissions must be configured for the remote SSH account on the source host. Running only the destination-side process as root does not provide remote permission. The command does not need passwordless `sh` or `bash`, and granting a general shell is not recommended.

`--all` uses `state.json`, live Btrfs UUID metadata, and stable `info.json` identity (`sys-uuid` plus Btrfs `type`) to identify the latest common source/backup snapshot. Snapshot-specific fields such as H/D/W/M tags, comments, creation time, file count, app version, and live status are ignored. If no common parent can be proven, a real full-chain restore additionally requires `--allow-no-common-parent`, the phrase `RESTORE ALL WITHOUT COMMON PARENT`, and the configured job name. If no current `info.json` identity matches the backup, real restore also requires `--allow-os-identity-mismatch` and `I UNDERSTAND THIS BACKUP MAY BELONG TO ANOTHER OS`.

Optionally add `--create-pre-restore-snapshot`. After all restore confirmations and before any receive, the app creates one Timeshift on-demand safety snapshot on the Timeshift target, verifies the new timestamp and every configured Btrfs payload, and leaves it in place even if restore later fails. Local restore creates it locally; SSH-target restore creates it on that SSH Timeshift host; SSH-backup pull restore creates it locally and never runs Timeshift creation on the remote backup host. This flag is independent of `[manual_snapshot]`, which applies to `sync`.

Every real restore also explains that the exact original `info.json` preserves H/D/W/M tags, so normal retention can later prune a restored snapshot or an existing tagged snapshot older than the restored snapshot. Before any receive begins, local and SSH modes both require this exact sentence:

```text
I UNDERSTAND TIMESHIFT MAY DELETE RESTORED SNAPSHOTS OR OLDER THAN RESTORED SNAPSHOTS
```

Review or pause Timeshift scheduling and retention until the intended rollback is complete.

When the exact recorded read-only source send parent still exists with the expected UUID, the first newer backup is received incrementally and later backups continue incrementally. If that exact parent is unavailable, restore prints the reason and uses one full hidden seed followed by incrementals. The final Timeshift payloads are writable Btrfs CoW snapshots of the hidden read-only chain, so they retain shared extents after the hidden chain is deleted.

### Pull restore from an SSH backup host

Use a separate restore config with `[restore] mode = "ssh"`, `[ssh]` pointing to the backup host, and `[destination].target_root` plus `state_file` set to their paths on that host. `lock_file`, `source.snapshot_root`, and `source.cache_root` must be local paths on the machine running the restore. `source.mode` remains sync-only. Preview with:

```bash
ts-btrfs restore --config ./config-restore-pull.toml \
  --all \
  --dry-run
```

The remote backup account needs ordinary traversal/read access to the backup date directories, `info.json`, and `state.json`; `base64`; and narrow passwordless sudo for Btrfs list/show/send. It does not need write access to a remote lock file or `flock`. The local machine needs the restore-target permissions described above and write access to the configured local `lock_file`.

Do not use the same path interpretation blindly for scheduled sync. In the pull profile, `[restore] mode = "ssh"` makes `destination.target_root` and `state_file` remote only for restore; `lock_file` remains local and normal sync/prune semantics remain unchanged.

## PyInstaller builds

PyInstaller can create a Linux executable for the machine/distro where the build is run. Build on the same OS family and CPU architecture where you expect to run the executable.

PyInstaller bundles the Python app. It does **not** bundle external system commands. The destination still needs commands like `btrfs`, `ssh`, `sudo`, optional `mbuffer`, and optional `sshpass` installed. The source still needs `timeshift` and `btrfs`.

### Install PyInstaller build dependency

From the project folder:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e '.[pyinstaller]'
```

If MQTT support should work inside the executable, install both extras before building:

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
python3 -m PyInstaller --clean --name ts-btrfs --console --paths . tools/pyinstaller_entry.py
```

One-file executable:

```bash
python3 -m PyInstaller --clean --onefile --name ts-btrfs --console --paths . tools/pyinstaller_entry.py
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

### Cleanup build artifacts

PyInstaller creates `build/`, `dist/`, and a `.spec` file. These are build artifacts, not backup data. Inspect and remove them manually before a clean rebuild; the application itself never recursively deletes backup or source-cache trees through ordinary filesystem commands.

## Moving configured roots

State schema version 3 stores source snapshot paths relative to `source.snapshot_root`, app-created send paths relative to `source.cache_root`, and destination paths relative to `destination.target_root`. After moving or remounting one of these roots, update the matching config value. The app resolves the saved suffix under the new root and still requires the same Btrfs UUID before it accepts an incremental parent. State files must already use the current relative schema.

When a writable Timeshift snapshot needs a read-only send-cache copy, the app first checks the root-scoped cache inventory. Btrfs list paths may include an on-disk prefix, may be relative as `<date>/@`, or may be bare `@` when the date parent itself is probed. If the bulk index missed the child, one authoritative parent-scoped UUID/read-only listing is performed before creation. A valid existing cache snapshot is reused after read-only and Parent UUID checks; an unavailable safety listing aborts instead of guessing. The exact target is therefore never blindly passed to `btrfs subvolume snapshot -r`, so an existing `<date>/@` cannot become a nested `<date>/@/@`.
