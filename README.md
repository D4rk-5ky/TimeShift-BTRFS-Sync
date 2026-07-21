# timeshift-btrfs-sync

`timeshift-btrfs-sync` backs up Timeshift Btrfs snapshots and can restore either one backup or a complete UUID-validated backup chain into the configured Timeshift repository. It can pull from or restore to another machine over SSH, or operate locally on the same machine. All restore directions use the same Btrfs, metadata, validation, and safety logic; only the selected backup and Timeshift endpoints change.

> ⚠️ AI-assisted / vibe-coded experimental software. Use at your own risk.

## Disclaimer

This project is AI-assisted / vibe-coded software created as a hobby project. It has not been professionally audited and may contain bugs, unsafe behavior, data-loss issues, security problems, or incorrect assumptions.

You are responsible for reviewing the code, testing it in a safe environment, making backups, and understanding what it does before using it on real data. The author is not responsible for damage, data loss, broken systems, security issues, or other problems caused by using this software.

## Data Loss Warning

This application can perform destructive operations, including deleting Btrfs subvolumes, snapshots, and backup data. Always test with dry-runs first, check the generated plans, and keep a separate working backup.

## License

MIT License. See [`LICENSE`](LICENSE).

## What it does

`source.mode` is used only by normal sync/source commands: `ssh` reads Timeshift snapshots through SSH and `local` reads them on the current machine. Restore direction is selected separately by `[restore] mode`: `local`, `ssh`, or `ssh-target`.

`timeshift-btrfs-sync` is a destination-pull backup tool for Timeshift Btrfs snapshots. It runs on the backup/destination machine, connects to the source over SSH by default, or uses local source mode on the same machine, and transfers Timeshift snapshots with `btrfs send` / `btrfs receive`.

It supports full and incremental backup sends, Timeshift snapshot discovery, copying each snapshot date’s shared Timeshift `info.json`, writable source snapshots through a read-only send cache, restoring one backup or a full post-common backup chain to Timeshift’s native layout, safe destination pruning, optional automatic Timeshift on-demand snapshots, split logs, MQTT notifications, and email notifications with optional log attachments.

Two complete commented config profiles are packaged: `config.example.toml` for normal sync/local restore and `config.restore-pull.example.toml` for SSH-backup-to-local-Timeshift restore. Generate either one with `ts-btrfs init-config --profile ...`.

## Packaged project layout

The release zip keeps package data as real directories. The complete profiles live only at:

```text
timeshift_btrfs_sync/data/config.example.toml
timeshift_btrfs_sync/data/config.restore-pull.example.toml
```

There should not be root-level config templates in the release zip. The `data` path must be a directory, not a file, because `init-config` reads the selected profile as package data.

## Shared workflow architecture

The app uses one shared implementation for each Btrfs, inventory, cache, planning, execution, and deletion responsibility. Sync, prune, recovery, and `destroy-leftovers` compose those operations in the order required by each workflow:

1. `endpoint.py` selects local, local-source, or SSH command transport.
2. `btrfs_ops.py` owns exact Btrfs probe, list, create, read-only snapshot, delete, send, and receive commands.
3. `inventory.py` builds the coherent Timeshift, `info.json`, snapshot-root, cache-root, and destination indexes.
4. `planning.py` creates ordered, side-effect-free workflow actions; sync selection remains oldest-to-newest.
5. `executor.py` executes or previews those actions through workflow-specific handlers.
6. `cache_ops.py` provides the exact cache ensure/reuse operation.
7. `tree_ops.py` provides verified deepest-first Btrfs tree discovery and deletion.

This structure does not weaken the UUID rules. Plans locate work; Btrfs UUID, Parent UUID, Received UUID, read-only, protected-root, and post-deletion checks still prove whether each action is safe. Dry-run and real workflows consume the same ordered plan model, while real execution performs the required live verification before changing data.

The pure sync planner intentionally keeps every retention-selected source subvolume in the oldest-to-newest queue, including entries already represented in state. The real workflow then performs the authoritative destination existence, UUID, recovery, and `info.json` checks. This prevents a shallow planning decision from bypassing live validation or metadata refresh.

Source preflight emits one tab-delimited sentinel protocol for both local and SSH source modes and parses it through one shared result parser. The parser is tested directly because it runs immediately after the destination lock is acquired and before source/cache creation or transfer work begins.

## Safety model

The safe defaults are intentionally conservative:

- `default_dry_run = true` previews changes unless `--run` is passed. In strict dry-run mode the app does not prepare the destination, create lock/state directories, run `btrfs receive`, or delete/prune snapshots.
- Destination pruning only deletes when `--run --yes-delete` is used.
- Incremental parents are verified with Btrfs UUID metadata before use.
- Automatic source-side manual snapshot creation requires source identity and sync-parent viability checks before Timeshift is changed.
- Restore refuses to overwrite an existing Timeshift date, validates state/Btrfs UUID lineage, reports `info.json` provenance separately, starts incrementally when the exact read-only send parent still exists, otherwise uses a justified full seed, exposes writable CoW snapshots in Timeshift’s native layout, and commits only after every payload and metadata check succeeds.
- Normal/user-created Timeshift on-demand snapshots are not pruned unless explicitly enabled.
- The app does not manage destination Btrfs compression; mount the receiving Btrfs filesystem/subvolume with compression enabled if you want compressed destination storage.

For normal backup, prune, cache cleanup, and Timeshift manual-snapshot operations, the source machine needs passwordless sudo only for Btrfs and Timeshift:

```sudoers
ts-btrfs-sync-user ALL=(root) NOPASSWD: /usr/bin/btrfs *
ts-btrfs-sync-user ALL=(root) NOPASSWD: /usr/bin/timeshift *
```

This is enough because Timeshift listing/creation, Btrfs send, Btrfs metadata checks, read-only cache creation, and source send-cache cleanup use those two commands. Per-snapshot Timeshift `info.json` files are read with ordinary non-sudo `cat`; the SSH/source user therefore needs normal path traversal and file read permission.

The `restore` command additionally creates and renames an ordinary Timeshift date directory and writes its regular `info.json`. With the restricted sudoers rules above, run a **local restore as root**, or grant narrow source-side passwordless sudo for `/usr/bin/mkdir`, `/usr/bin/tee`, `/usr/bin/chmod`, `/usr/bin/mv`, `/usr/bin/rm`, and `/usr/bin/rmdir`. For SSH restore, those permissions must exist on the remote source account; running the destination-side app as local root does not grant remote filesystem permission. `base64` and `cat` remain unprivileged. Do not grant a passwordless shell such as `sh` or `bash` merely for restore.

## Remote `info.json` permissions and persistent source mount

The app runs on the backup/destination machine, but `info.json` is read on the source machine by the unprivileged account configured as `[ssh].user`. This is the account the destination uses for the SSH connection. It is not necessarily the local user or `root` account running `ts-btrfs` on the destination.

The combined inventory records the effective source account name and UID without opening another SSH connection. If a required `info.json` cannot be read, the terminal and normal log error include a line like:

```text
remote SSH source account used by this destination: btrbk-source (uid 1001)
```

That exact account must be able to:

- traverse every parent directory leading to `source.snapshot_root` (`x`/search permission);
- list `source.snapshot_root` (`r-x`), because the combined inventory enumerates the timestamp directories in one shell loop;
- traverse each timestamp directory;
- read `<source.snapshot_root>/<date>/info.json`.

A file can be mode `0644` and still be unreadable when one parent such as `/media/<desktop-user>` is mode `0750`. Root may read it locally while the unprivileged SSH account receives `Permission denied`. Diagnose the first blocked component on the source host with:

```bash
sudo -u btrbk-source -- namei -l \
  /path/to/timeshift-btrfs/snapshots/<date>/info.json
```

For a reliable unattended backup source, a privileged administrator should mount the Btrfs filesystem at a stable system path through `/etc/fstab` instead of relying on a private desktop mount below `/media/<user>`. Example for the Btrfs top-level tree:

```bash
sudo install -d -m 0755 /mnt/OS-Root
sudo blkid
sudoedit /etc/fstab
```

Example `/etc/fstab` entry:

```fstab
UUID=<BTRFS-FILESYSTEM-UUID> /mnt/OS-Root btrfs defaults,subvolid=5 0 0
```

Mount it and grant the configured SSH account only the access it needs:

```bash
sudo mount /mnt/OS-Root

# Search-only permission through private parent directories.
sudo setfacl -m u:btrbk-source:--x /mnt/OS-Root
sudo setfacl -m u:btrbk-source:--x /mnt/OS-Root/timeshift-btrfs

# The inventory must be able to list the snapshot dates.
sudo setfacl -m u:btrbk-source:r-x \
  /mnt/OS-Root/timeshift-btrfs/snapshots

# Confirm the exact file is readable as the SSH account.
sudo -u btrbk-source -- cat \
  /mnt/OS-Root/timeshift-btrfs/snapshots/<date>/info.json
```

Replace `btrbk-source` with the name printed by the application and use its printed UID when checking ownership or ACL results. The mount does not have to be owned by the backup account; it only has to be accessible to that account by name/UID through normal mode bits or a narrow ACL. Btrfs normally keeps Unix ownership in filesystem metadata, so do not rely on FAT/NTFS-style `uid=` or `gid=` mount options to remap ownership. After changing the mount path, update `source.snapshot_root` and `source.cache_root` in the config.

## Source sudoers and source cleanup

`destroy-leftovers --delete-source` keeps the source sudoers model narrow. On the source host it uses passwordless `sudo btrfs` only for Btrfs metadata and subvolume deletion. It does not require passwordless `find`, `test`, `rm`, `mkdir`, or `cat`.

Source cache payloads and timestamp containers are Btrfs subvolumes. Cleanup deletes child cache subvolumes first and then deletes the timestamp parent with `btrfs subvolume delete`. The app does not use ordinary-directory cleanup as a fallback. If a configured cache path is an ordinary non-empty directory, cleanup stops and requires manual inspection.


## Destination layout

The destination `target_root` is the backup job folder. The app creates and owns:

```text
<target_root>/snapshots/                         Btrfs snapshots-root subvolume
<target_root>/snapshots/<date>/                   Btrfs date subvolume
<target_root>/snapshots/<date>/info.json         shared Timeshift control file
<target_root>/snapshots/<date>/@                 received root subvolume, when configured
<target_root>/snapshots/<date>/@home             received home subvolume, when configured
<target_root>/.ts-btrfs-sync/                    state.json, lock file, logs
```

Timeshift uses one `info.json` for the whole snapshot date. It sits beside `@` and optional `@home`; there is not a second combined metadata file to create. The app captures that one file once and writes it once after every subvolume configured for the date has completed. This works with `subvolumes = ["@", "@home"]`, `subvolumes = ["@"]`, or `subvolumes = ["@home"]`.

The destination `target_root`, its managed `snapshots/` child, and every `snapshots/<date>` container must be Btrfs subvolumes. If `target_root` is missing and `destination.create_target_root = true`, the app creates it with `btrfs subvolume create`. Missing `snapshots/` is also created with `btrfs subvolume create`, but unlike state, lock, and optional log helpers it never falls back to `mkdir`. Each date container is created and exact-probed as a Btrfs subvolume before `btrfs receive`. Existing ordinary date folders, files, or symlinks directly below `snapshots/` are refused as an unsupported layout and must be inspected and moved or removed manually. A bulk destination index miss is not enough to classify a date as ordinary: the app first runs an exact `btrfs subvolume show` probe and accepts/adds a real subvolume to the current index.

`state.json` records successfully received snapshots and the metadata needed for incremental sends. Do not manually delete `state.json` while a job is running. Use the guarded `clear-state` command when you intentionally want to remove the configured state file after a failed transfer or before a controlled state-recovery run. Do not delete only `snapshots/` while keeping the corresponding state file.

State schema version 3 stores every managed path relative to the configured root that owns it:

```json
{
  "source_path": "2026-07-15_05-00-02/@",
  "send_path": "2026-07-15_05-00-02/@",
  "send_path_kind": "source-cache",
  "parent_source_path": "2026-07-15_04-00-02/@",
  "parent_source_path_kind": "source-cache",
  "destination_path": "snapshots/2026-07-15_05-00-02/@"
}
```

`source_path` is always relative to `source.snapshot_root`. `send_path` is resolved under `source.cache_root` when `send_path_kind = "source-cache"`, or under `source.snapshot_root` when `send_path_kind = "timeshift-original-readonly"`. `parent_source_path` follows the same rule through `parent_source_path_kind`. `destination_path` remains relative to `destination.target_root`.

This lets you move or remount `source.snapshot_root`, `source.cache_root`, or the whole destination target, then update those roots in the config. State paths resolve below the new locations. Btrfs UUID identity is still required before a moved send-cache or Timeshift path can be used as an incremental parent. `state.json` must use schema version 3 and root-relative managed paths; unsupported versions, absolute stored paths, missing ownership kinds, and mismatching snapshot/subvolume suffixes are rejected.

During `sync` and before standalone `prune`, mutable Timeshift metadata for already-synced snapshots is refreshed from the latest `timeshift --list`. This updates snapshot-level `tags`, `comment`, `created`, and `path` in `state.json` without re-sending data and without changing Btrfs UUID, parent-chain, send-path, destination-path, or status fields. This lets retention follow Timeshift when it later promotes or changes flags such as `O`, `H`, `D`, `W`, or `M`. The metadata refresh uses the fast Timeshift list path and does not run `btrfs subvolume show` for every already-synced snapshot.

If `state.json` is missing or empty while destination snapshots already exist, `sync` tries a conservative state recovery before creating a manual snapshot or sending data. It scans destination snapshots and compares each destination subvolume's `Received UUID` with the UUID of the matching source Timeshift subvolume or an existing read-only source-cache subvolume. Only exact UUID matches are adopted into in-memory state and, during a real run, written back to `state.json`. Names alone are never trusted. If an existing destination subvolume cannot be adopted, the app refuses to delete it as an incomplete receive because it may be a valid backup from a missing state file.

A full reset means deleting both the received snapshot subvolumes and `.ts-btrfs-sync/`. Use `destroy-leftovers` for a complete app-owned reset. It deletes nested Btrfs subvolumes deepest-first and does not recursively remove ordinary non-empty backup trees.

## Restore layout and workflow

The backup layout and Timeshift's native source layout are intentionally different:

```text
Backup destination:
<target_root>/snapshots/<date>/              Btrfs date-container subvolume
├── info.json                                regular file
├── @                                        read-only received Btrfs subvolume
└── @home                                    read-only received Btrfs subvolume, when configured

Timeshift repository after restore:
<source.snapshot_root>/<date>/               ordinary directory
├── info.json                                exact original Timeshift file
├── @                                        writable Btrfs subvolume
└── @home                                    writable Btrfs subvolume, when configured
```

The command has two restore selections:

- `restore --snapshot <date>` restores one selected backup.
- `restore --all` finds the newest proven common snapshot and restores every newer backup oldest-to-newest.

### Optional pre-restore safety snapshot

Add `--create-pre-restore-snapshot` to create one Timeshift on-demand/tag O snapshot of the system **being restored** before any hidden receive directory or Btrfs stream is started:

```bash
ts-btrfs restore --config ./config.toml \
  --all \
  --create-pre-restore-snapshot \
  --dry-run
```

In a real run the snapshot is created only after the restore plan, OS identity, target-path checks, and typed confirmations have succeeded. The app then re-reads `timeshift --list`, identifies exactly one newly created timestamp, and exact-checks every configured payload such as `@` and `@home` with Btrfs metadata. Failure aborts before transfer.

The safety snapshot always runs through the configured Timeshift `source` endpoint:

- local backup → local Timeshift: created locally;
- local backup → SSH Timeshift: created on the remote Timeshift machine;
- SSH backup → local Timeshift with `[restore] mode = "ssh"`: created locally.

It is never created on `destination.target_root` or on the SSH backup host. The fixed comment is `TimeShift-BTRFS-Sync pre-restore safety snapshot`. It is intentionally left in Timeshift if the later restore fails, providing a rollback point for the pre-restore system state. The `[manual_snapshot]` section controls automatic snapshots before `sync`; it does not control this restore-only flag.

### Pull a remote SSH backup into local Timeshift

Restore can reverse the normal network direction without a second restore implementation. In pull mode the backup repository is remote and the Timeshift repository is local:

```text
SSH backup host: destination.target_root/snapshots/<date>/@
        btrfs send over SSH
                 ↓
Local machine: source.snapshot_root/<date>/@
        local btrfs receive
```

Generate the complete restore-only profile instead of building it from a shortened snippet:

```bash
ts-btrfs init-config \
  --profile restore-pull \
  --path ./config-restore-pull.toml
```

The generated file includes every supported top-level, restore, SSH, source, destination, stream, retention, manual-snapshot, MQTT, and mail setting with comments. Its `[ssh]` section includes both key authentication and optional `sshpass` password/password-file authentication, plus port, cipher, compression, ControlMaster, strict host-key checking, timeouts, keepalives, and jump-host examples.

The generated pull profile sets `[restore] mode = "ssh"`, so `destination.target_root` and `state_file` are interpreted on the SSH backup host. `lock_file`, `source.snapshot_root`, and `source.cache_root` remain local to the machine running the restore; neither Timeshift path nor the restore lock is probed on the backup host. `source.mode` is not used to choose restore direction. Use a separate restore config so later normal `sync`, `prune`, and `destroy-leftovers` runs do not accidentally interpret remote restore paths as local backup paths.

Dry-run and real examples:

```bash
ts-btrfs restore --config ./config-restore-pull.toml \
  --all \
  --create-pre-restore-snapshot \
  --dry-run

ts-btrfs restore --config ./config-restore-pull.toml \
  --all \
  --create-pre-restore-snapshot \
  --run \
  --i-understand-this-modifies-timeshift
```

If a local Timeshift repository is accidentally selected as the backup, the app now explains that Timeshift date folders are correctly ordinary directories and points to this transport setting instead of presenting the layout as corrupt.

The remote SSH account needs ordinary traversal/read permission for the backup timestamp directories, `info.json`, and `state.json`; access to `base64`; and narrow passwordless sudo permission for the configured Btrfs command used by `subvolume list/show` and `send`. It does not need remote lock-file write permission or `flock`. The local side needs the normal restore permissions for `btrfs receive`, Timeshift, ordinary date directories, `info.json`, and the configured local `lock_file`. The local restore lock is held until all streams and verification complete.

### `info.json` provenance and same-OS warnings

Restore parses Timeshift metadata before changing the source repository. It uses:

- `sys-uuid` as the root-filesystem identity recorded when that snapshot was created.
- `type`, which must identify Btrfs snapshots.
- `sys-distro` as diagnostic context only, because an in-place distribution upgrade can change that text without creating a different root filesystem.

The comparison intentionally ignores snapshot-specific fields that legitimately change between snapshots, including H/D/W/M/O/B tags, comments, creation time, file counts, Timeshift app version, live status, and Btrfs statistics.

The original `info.json` is restored unchanged. Its `sys-uuid` is therefore snapshot provenance, not guaranteed live-repository identity after an OS clone, filesystem recreation, or imported restore. The app uses that provenance as a separate cross-OS warning when no stronger common-parent proof exists. It never lets a differing `sys-uuid` invalidate an exact common parent already proven through `state.json` and live Btrfs UUIDs.

Every backup selected by `--all` must contain one consistent `sys-uuid` and snapshot type. A mixed backup set is refused. The backup provenance is compared with the readable `info.json` files in the current Timeshift repository. When no exact UUID common parent exists and no metadata match can be proven, dry-run prints a cross-OS warning and a real restore requires:

```text
--allow-os-identity-mismatch
```

followed by this exact typed sentence:

```text
I UNDERSTAND THIS BACKUP MAY BELONG TO ANOTHER OS
```

### Common-parent safety

A timestamp name alone is never considered common. For every configured payload such as `@` and `@home`, the newest common date must satisfy both authoritative checks:

1. The current Timeshift payload UUID equals `original_source_uuid` in `state.json`.
2. The backup payload `Received UUID` equals `send_source_uuid` in the same state entry.

The source and backup `info.json` provenance is still shown in the plan. A difference is diagnostic only once both UUID links above prove the same state record. This prevents Timeshift tag/retention changes or restored historical metadata from invalidating stronger Btrfs lineage proof.

If the common parent is already the newest backup, there is nothing to restore.

If no common parent can be proven, `--all` prints a prominent warning. A real full-chain restore is refused unless `--allow-no-common-parent` is supplied, followed by the stronger no-common-parent confirmations. The `info.json` OS-identity check remains separate; either or both overrides may be required depending on the plan.

### First transfer: incremental when the exact receive parent still exists

A common Timeshift snapshot proves source identity, but it is not automatically the Btrfs receive parent. Backups are commonly sent from a read-only cache snapshot, so the incremental stream parent UUID can differ from the writable Timeshift snapshot UUID.

For every payload of the common date, restore resolves the exact recorded `send_path` from `state.json` and verifies that it:

- still exists on the source filesystem;
- has the recorded `send_source_uuid`;
- remains read-only.

When every payload passes, the first newer backup is sent incrementally with the common backup as the sender parent. Btrfs receive uses the existing exact read-only source/cache parent, so no full seed transfer is needed. Later backups continue incrementally from the previously received hidden snapshot.

When any exact receive parent is missing, writable, or has the wrong UUID, restore cannot safely use it. The terminal prints the precise reason and falls back to a full hidden receive of the common backup, followed by incrementals. Restore never guesses a parent from matching names and never changes an existing Timeshift snapshot to manufacture a parent.

Without any common parent, the oldest backup is full-received and every later backup is incremental.

### Restored-tag retention warning

Restore writes the original `info.json` unchanged. Original Hourly, Daily, Weekly, and Monthly tags therefore remain active after import. Timeshift may later delete a restored snapshot during scheduled retention cleanup when it falls outside configured keep counts. Importing a tagged restored snapshot can also push an older existing tagged snapshot outside the same keep count.

Every real restore requires this exact acknowledgement before receive begins:

```text
I UNDERSTAND TIMESHIFT MAY DELETE RESTORED SNAPSHOTS OR OLDER THAN RESTORED SNAPSHOTS
```

Review or pause Timeshift scheduling and retention until the intended rollback is complete. This confirmation applies to local and SSH restore.

### Hidden receive chain and writable Timeshift snapshots

Restore receives backup payloads into a hidden read-only chain below `source.snapshot_root`. After all required full/incremental receives succeed, each visible Timeshift payload is created as a writable Btrfs snapshot of the corresponding hidden received payload. The visible snapshots retain shared extents through Btrfs copy-on-write.

The original `info.json` is written into an ordinary staging date directory. That directory is renamed to the final Timeshift timestamp only after every payload and metadata check succeeds. `timeshift --list` must report every restored date before the command reports success. The hidden receive chain is then deleted; visible CoW snapshots remain valid.

Every backup date is validated before use. Its date container must be a Btrfs subvolume, all configured payloads must exist and be read-only, and `info.json` must be readable UTF-8 containing a JSON object. The timestamp directory name is the snapshot identity; restore preserves `info.json` byte-for-byte and does not require a non-standard `date` property. Unknown entries and existing final Timeshift dates are refused.

If a transfer fails before commit, cleanup removes only exact Btrfs subvolumes and staging files created by the current attempt. It never recursively deletes an ordinary Timeshift tree. Once a visible date is committed, a later verification or hidden-chain cleanup error leaves that potentially usable snapshot in place for manual inspection.

Single-snapshot dry-run:

```bash
ts-btrfs restore --config ./config.toml \
  --snapshot 2026-07-15_05-00-02 \
  --dry-run
```

Restore every backup newer than the latest proven common parent:

```bash
ts-btrfs restore --config ./config.toml \
  --all \
  --dry-run
```

Real common-parent chain restore:

```bash
ts-btrfs restore --config ./config.toml \
  --all \
  --run \
  --i-understand-this-modifies-timeshift
```

Dangerous restore when no common parent and/or no matching `info.json` OS identity can be proven:

```bash
ts-btrfs restore --config ./config.toml \
  --all \
  --allow-no-common-parent \
  --allow-os-identity-mismatch \
  --run \
  --i-understand-this-modifies-timeshift
```

## How sync works

Normal sync flow:

```text
1. In real-run mode, run lock path preflight before checking other sync paths. This prepares the lock-file parent first so the app can acquire the lock early. If the lock path chain includes destination.target_root, that component is created by the strict Btrfs subvolume rule.
2. Acquire the lock file.
3. Run sync path preflight for source.snapshot_root, source.cache_root, and destination.target_root. The Timeshift-owned snapshot_root must already exist and may be an ordinary directory on Btrfs. Missing source.cache_root and destination.target_root are created only by their own rules.
4. Prepare destination helpers. `destination.snapshots` must be a Btrfs subvolume and has no mkdir fallback; state_file.parent, lock_file.parent, and log_dir may be ordinary directories or Btrfs subvolumes.
5. Build one coherent source inventory. In SSH mode one SSH command runs Timeshift listing, reads every readable `<snapshot_root>/<date>/info.json` with ordinary `cat`, and performs bulk Btrfs metadata scans for both source.snapshot_root and source.cache_root. In local mode the same information is collected locally.
6. Build one local bulk Btrfs index rooted at `destination.target_root/snapshots`, so mounted-subvolume list paths such as `snapshots/<date>` map to the correct absolute destination paths. Exact-probe any direct date missed by the bulk list before deciding it is ordinary.
7. Compare Timeshift names, snapshot-root UUIDs, cache UUIDs, destination Received UUIDs, and state.json to find the newest safe common parent.
8. Skip snapshots already received or older than the confirmed sync floor.
9. Use full send only when the destination was empty at the start of the sync run.
10. Use incremental send when a UUID-confirmed parent is available.
11. Error out if the destination already has snapshots but no matching parent can be proven.
12. Create `<target_root>/snapshots/<snapshot>` as a Btrfs date subvolume.
13. Receive each configured child into `<target_root>/snapshots/<snapshot>/<subvolume>`.
14. Save state after each successful receive, but treat all configured subvolumes for one Timeshift date as one complete version.
15. After the configured `@`, `@home`, or single selected subvolume set is complete, atomically create or refresh `<target_root>/snapshots/<snapshot>/info.json` inside the date subvolume.
16. If a required source/cache/parent path disappears or changes UUID during preparation or transfer, rebuild the complete combined source inventory, delete the incomplete child subvolumes and then the date subvolume, rebuild the queue, and continue within `source.source_change_retry_count`.
```

Normal `sync` always bulk-loads source Btrfs metadata; it does not open one SSH connection per snapshot or subvolume. `source.verify_subvolumes_at_discovery` controls whether missing bulk-index entries are omitted immediately or represented as expected paths for later recovery handling. `list-source` remains a lightweight Timeshift-only command unless `--verify-btrfs` is requested.

## Sync path preflight

Before automatic on-demand snapshot creation and before any send/receive work, `sync` verifies that the required configured roots are actually reachable:

```text
source.snapshot_root
source.cache_root, when configured; missing cache roots are created as Btrfs subvolumes in real-run mode when create_readonly_cache = true
destination.target_root
```

The snapshot-root and cache-root source preflight checks are executed inside one source command, and the cache check runs only after the snapshot-root script emits its explicit safe marker. They use the configured source Btrfs command. In SSH mode those source commands are executed through the configured SSH/sshpass source endpoint; in local mode they run locally. `source.snapshot_root` is Timeshift-owned: it must already exist, it may be an ordinary directory on a Btrfs filesystem, and the app never creates, prunes, deletes, destroys, or cleans it. Snapshot-root verification first tries `btrfs subvolume list -o <snapshot_root>` and then falls back to `btrfs filesystem df <snapshot_root>` so ordinary Timeshift directories can be accepted even when a Btrfs version does not accept the ordinary directory for subvolume listing. This prevents the app from hiding a missing Timeshift mount, wrong OS root, or wrong snapshot path by creating an empty replacement directory, and it prevents source cleanup from ever touching Timeshift-owned snapshots. `source.cache_root` is app-owned send-cache storage, must be outside `source.snapshot_root`, and is created as a Btrfs subvolume when it is missing and `create_readonly_cache = true`; an existing ordinary directory is refused. If `destination.target_root` is missing and `destination.create_target_root = true`, the app verifies that its parent already exists and is Btrfs-accessible, then creates the exact target root with `btrfs subvolume create <target_root>` and verifies it with `btrfs subvolume show`. If `destination.target_root` already exists, it must also pass `btrfs subvolume show`; an ordinary directory inside Btrfs is refused. This keeps the app-owned backup root explicit and prevents a later receive/prune run from continuing after a misleading preflight. Dry-run mode describes cache/target creation attempts without creating them, but missing `source.snapshot_root` is still an error.

If `source.snapshot_root` is missing, not a directory, or not Btrfs-accessible through the configured source endpoint, the app fails before creating a fresh Timeshift on-demand snapshot, before creating source cache storage, and before trying to send data. In SSH mode, `snapshot_root` must be the path as seen on the remote source machine, and the source Timeshift filesystem must already be mounted there. The same early failure happens if the cache root exists as an ordinary directory instead of a Btrfs subvolume, the cache-root parent is not accessible, or the destination target-root parent cannot be used for Btrfs subvolume creation. This is intended to prevent avoidable leftover on-demand snapshots after a restored VM, changed mount point, wrong Timeshift snapshot path, wrong send-cache path, or broken destination.

`create-manual` also runs the same preflight before asking Timeshift to create a standalone on-demand snapshot.

## Incremental parent guard

Incremental parent verification is mandatory. If the destination is empty when the sync run starts, the app can start with a normal full sync. If matching snapshots exist, the app uses an incremental send after proving the source parent matches the destination parent. If the destination already contains snapshots but no matching parent can be proven across any usable snapshot, the app refuses to send and tells the user to use an empty/separate backup directory for a new full sync or repair the existing backup state/cache.

There is no setting that permits an unmatched incremental chain. If the destination contains snapshots, sync requires at least one source UUID to match a destination Received UUID. Only a destination that is empty when the run begins may start with a full send.

Incremental Btrfs send uses:

```bash
btrfs send -p <parent> <current>
```

The parent must represent the same Btrfs snapshot on both source and destination. Before using a destination snapshot as an incremental parent, the app compares:

```text
source parent UUID == destination parent Received UUID
```

This protects the backup from mixing snapshots from another OS, another source host, or a reset backup chain. Parent paths from previous runs are always checked before use. The app first checks whether the indexed source send-cache already contains a read-only snapshot whose UUID exactly matches the destination parent's `Received UUID`. This lets a local run reuse read-only cache snapshots that were created earlier by an SSH pull. If no indexed cache UUID match exists, the app resolves the saved root-relative `send_path` against the current configured source root, then tries any indexed cache path for the UUIDs recorded in state, and finally the original Timeshift source snapshot. It never creates a replacement cache snapshot while choosing an existing parent, because a recreated cache snapshot gets a new UUID and cannot match the destination parent.

## Source read-only send cache

`btrfs send` requires read-only source snapshots. If Timeshift snapshots are writable, the app can create read-only source send-cache snapshots under `source.cache_root`.

If a Timeshift snapshot child is already read-only, the app sends directly from that original Timeshift path instead of creating a duplicate source-cache snapshot. The state records the `source_path` and `send_path` as `<date>/<subvolume>` plus `send_path_kind = "timeshift-original-readonly"`; the kind resolves both paths under the current `source.snapshot_root`, and prune treats that path as protected Timeshift-owned data. The app may read and send from `source.snapshot_root`, but it must not delete, prune, destroy, clean, rename, move, or change original Timeshift snapshots; cleanup of `source.snapshot_root` remains Timeshift's job only. Source-side delete functions have an explicit protected-root guard for this.

The top-level `cache_root` does not have to be created manually, but it must not be the Timeshift snapshots directory and must not be inside `source.snapshot_root`. If `cache_root` is missing, real preflight creates it as a Btrfs subvolume before snapshot discovery/send work. The parent directory of `cache_root` must already exist and be Btrfs-accessible. Per-snapshot cache parents and read-only send snapshots are also created with Btrfs commands:

```bash
sudo -n btrfs subvolume create <cache_root>
sudo -n btrfs subvolume create <cache_root>/<snapshot-name>
sudo -n btrfs subvolume snapshot -r <original> <cache_root>/<snapshot>/<subvolume>
```

The app checks cache paths with root-scoped Btrfs subvolume listings under `source.cache_root` and, for deletion, under each timestamp cache parent. Btrfs may report a descendant with an on-disk prefix such as `@root/.../send-cache/<date>/@`, relative to the cache root as `<date>/@`, or relative to one date parent as bare `@`. The root-scoped mapper accepts all three only for commands that were actually restricted with `btrfs subvolume list -o <root>`. Unscoped list output still rejects unmatched paths. This lets existing cache children remain indexed after remounts and mounted-subvolume path changes without guessing unrelated paths below the cache root.

Before creating `<cache_root>/<snapshot>/<subvolume>`, the app first checks the per-run cache index. If the exact child was missed, it performs one authoritative parent-scoped UUID and read-only listing below `<cache_root>/<snapshot>` and reuses the exact child only when it is read-only and its Parent UUID matches the original Timeshift subvolume when both UUIDs are available. If that parent-scoped safety check cannot be completed, creation is refused. Only a target proven absent is passed to `btrfs subvolume snapshot -r`. This is important because Btrfs treats an existing destination as a directory and appends the source basename; passing an existing `<date>/@` as the destination would otherwise attempt `<date>/@/@`.

A missing exact child is expected when the cache snapshot has not been created yet, for example `send-cache/<snapshot>/@home`. Existing ordinary paths, writable cache subvolumes, and cache snapshots whose Parent UUID belongs to a different Timeshift original are refused instead of overwritten or nested. If another process creates the exact read-only child during the final create attempt, the app repeats the authoritative parent-scoped check and reuses it instead of entering recovery and deleting a valid cache snapshot. Required failures and real send/receive failures still print and log full stderr.

Every read-only cache snapshot created by `sync` is kept until retention runs. Its state `send_path` is stored as `<date>/<subvolume>` relative to the current `source.cache_root`, not as an absolute mount path. This preserves more possible source/destination UUID common ground when short-lived snapshots, such as hourly snapshots, disappear later. For each pruned snapshot, `prune` attempts both destination deletion and matching source send-cache deletion in one coordinated item. It removes the `state.json` entry only after destination subvolumes and source send-cache are both confirmed gone or already absent. If either side is unavailable, it still attempts the available side and keeps state so the next prune can retry.

Prune only deletes send paths that are explicitly app-owned source-cache paths below `source.cache_root`. On the destination, prune requires `snapshots/<date>` to be a Btrfs subvolume, deletes its configured received child subvolumes first, and then deletes the date subvolume. The final Btrfs deletion removes the regular `info.json` automatically. Before deleting a timestamp cache parent such as `send-cache/<snapshot>`, prune re-reads live Btrfs children under that parent and deletes remaining child subvolumes deepest-first. No ordinary-directory cleanup fallback is used. Unexpected content, an ordinary date folder, or an ordinary non-empty configured root causes a manual-inspection error. Source delete candidates at or below `source.snapshot_root` are always refused.

## Source/destination Btrfs index optimization

At the beginning of a sync run, the app builds one coherent source inventory and one local destination index. The source inventory contains the Timeshift list, the contents of every readable per-date `<source.snapshot_root>/<date>/info.json`, and short-lived Btrfs indexes for `source.snapshot_root` and `source.cache_root`. In SSH mode one source shell/SSH request runs Timeshift, loops over the date folders, reads each control file with ordinary non-sudo `cat`, and performs both Btrfs root scans—not one connection per root, snapshot, metadata file, or subvolume. `destination.target_root` is indexed locally in bulk. Later Timeshift discovery, parent checks, sync-floor checks, and send-path checks can use dictionary lookups instead of repeatedly starting new source-side `btrfs subvolume list/show` probes. Destructive source send-cache parent cleanup still does a final live child-subvolume listing under the timestamp parent before deleting it, because the index is a performance cache and must not be the final emptiness authority for deletion.

The index is deliberately per-run only. Successful cache preparation performs an exact target probe, optional snapshot creation, and metadata verification in one source command, then inserts or refreshes the result in the cache index. Successful receive refreshes the new destination path, and prune removes deleted source-cache paths from the index. The exact target probe is a safety fallback when a bulk list could not map a remounted filesystem-relative path; it does not add a separate SSH request. Normal discovery and parent comparison still use the bulk inventory without per-parent SSH metadata reads. Safety-critical incremental matching still requires the same identity rule:

```text
source parent UUID == destination parent Received UUID
```

This reduces the overhead from many small SSH calls, especially when the SSH identity file is password-protected with high key-derivation iterations. The actual `btrfs send`/`receive` stream still uses one SSH pipeline per snapshot/subvolume that must be transferred.

On a fresh/full sync into a destination that was empty at run start, the app first applies the active retention rules to the source Timeshift list and sends only the snapshots that would be kept. For example, if retention keeps the newest 6 hourly, 5 daily, 2 weekly, and 6 monthly snapshots, the first seed starts at the oldest snapshot in that kept set and then sends the kept snapshots in date order. Existing safe read-only cache children for those selected dates are reused; only missing cache children are created. Deleting only the destination therefore does not require rebuilding every surviving source-cache snapshot. Existing non-empty destinations still use the normal UUID-confirmed parent/floor safety logic.

## Optional automatic on-demand snapshots

When `manual_snapshot.enabled = true`, `sync` can create a source Timeshift on-demand snapshot before normal syncing.

The app first runs `timeshift --list`. If the destination already contains snapshots, it checks the configured source against existing `state.json` history by Btrfs UUID, then proves sync can actually continue before creating the new source snapshot. That pre-manual check verifies a UUID-confirmed sync floor and a usable incremental parent for the next pending transfer, or a usable parent for the future manual snapshot when no current snapshot needs transfer. If that cannot be proven, the app fails before creating another Timeshift snapshot. If the destination was empty when the run started, the run may create a first snapshot and seed the backup with a full send; later snapshots then become incremental.

The create command intentionally omits `--tags O` because Timeshift creates on-demand/tag `O` snapshots by default, and some Timeshift versions reject explicit `--tags O`.

After creating the snapshot, the app re-reads `timeshift --list`. The new snapshot is not sent directly or prioritized. It is sent only when the normal oldest-to-newest snapshot loop reaches its timestamp, using the same full/incremental parent logic as every other snapshot.

Interrupted-run behavior: if a previous run created an app on-demand snapshot and then failed before that snapshot was fully synced, the next normal `sync` detects the existing app-created pending snapshot by tag `O` plus `manual_snapshot.marker`. It keeps that older pending snapshot in the normal oldest-to-newest order, but it still creates a fresh on-demand snapshot for the current run because the older pending snapshot may no longer represent the current system state. Both the older pending snapshot and the new snapshot are sent only when the normal oldest-to-newest loop reaches their timestamps.

Automatic creation is skipped when `--snapshot <name>` is used, because that command targets one existing snapshot.

## Run summaries

Every `sync` ends with a terminal-friendly `SYNC SUMMARY`. It shows how many full syncs and incremental syncs were planned or completed, how many entries were already synced, and which source/destination paths were used. Each transfer is labeled clearly as `FULL SYNC` or `INCREMENTAL`. When `log_dir` is enabled, this readable statistics block is written to `.succes`, not mixed into `.log`.

If a transfer is interrupted while `btrfs receive` has already created the destination path, that path is not marked as complete in `state.json`. For a destination that was already populated when the next run starts, the app first requires at least one complete UUID-confirmed source/destination snapshot anchor. If no such anchor exists, it errors before deleting recovery data or sending anything; use an empty/separate target for a new full backup. After that guard passes, `destination.cleanup_incomplete_receive = true` makes the real sync treat the whole snapshot date as the recovery unit. If either configured source subvolume for that Timeshift date, for example `@` or `@home`, is incomplete, missing from state, or missing on destination, the app first live-checks every configured subvolume under `source.snapshot_root/<date>`. When all source subvolumes still exist, it removes the current failed `snapshots/<date>` destination version, removes the matching app-owned `source.cache_root/<date>` send-cache version, removes the stale state entry, refreshes the in-memory Btrfs indexes, and then transfers the snapshot again in the normal oldest-to-newest position.

If Timeshift or another process changes the source while a snapshot is being prepared or streamed—for example, an hourly snapshot or selected parent is deleted—the failed command is followed by one complete combined source inventory rebuild. The app compares the before/after UUID identities of the exact current, parent, and configured sibling paths. Unrelated Timeshift churn does not hide a network, mbuffer, or destination error. When a required path really disappeared or changed UUID, the terminal and logs show the complete inventory difference, the app removes the incomplete app-owned cache/destination/state version for that date, rebuilds all source lists and the oldest-to-newest queue, and continues. If the vanished snapshot is no longer available it is skipped; if it still exists with a valid new inventory it can be retried. This is bounded per snapshot/subvolume by `source.source_change_retry_count`; `0` disables automatic continuation. The same snapshot-level cleanup is used at the start of a later sync for stale incomplete state entries whose source Timeshift snapshot is no longer listed.

Recovery cleanup never deletes `source.snapshot_root` or anything below it. Source cleanup is limited to app-owned Btrfs subvolumes under `source.cache_root`. Destination cleanup deletes configured received child subvolumes first and then deletes the `snapshots/<date>` Btrfs subvolume; its regular `info.json` disappears as part of that final Btrfs deletion. Ordinary destination date folders are not supported or cleaned automatically. Complete destination snapshots remain valid even after Timeshift later prunes the original source snapshot.

The copied control file is required for every snapshot date processed by sync. If the source `info.json` is absent, unreadable, malformed in transport framing, or cannot be written safely on the destination, the sync run raises an error instead of silently reporting success for a metadata-less snapshot. For source read failures, the error names the effective SSH/source account and UID and explains the required mount-path traversal/read permissions and persistent `/etc/fstab` option. Existing complete destination snapshots are backfilled or refreshed from the current source inventory when their source snapshot is still available. Destination writes use a temporary file plus atomic replacement, and a symlink at the final `info.json` path is refused.

This also applies when the failed snapshot is an app-created on-demand snapshot. The app does not move the on-demand snapshot to the front of the queue. It keeps the already sorted source snapshot list, recovers or skips the failed snapshot only when that snapshot date is reached, and then continues in the existing oldest-to-newest order. If automatic on-demand creation is enabled, a fresh on-demand snapshot for the current run is still created and then added to the same sorted queue.

Every `prune` now prints a `RETENTION SUMMARY`, a `RETENTION DELETE PLAN`, and a `RETENTION DELETE SUMMARY` after real deletion. Delete candidates are labeled as `WOULD DELETE` in dry-run mode or `DELETE` in real mode, and each entry includes the destination subvolumes, source send-cache subvolumes, Timeshift tags, and the reason it falls outside the active retention rules. The final summary reports attempted, completed, retry, and remaining state counts. When `log_dir` is enabled, these readable summaries are written to `.succes` and the normal run log.

## Pruning and retention

Pruning applies destination retention rules. It can be enabled from config with `prune_after_sync = true` or from CLI with `sync --prune`.

Real deletion requires all of these:

```text
1. non-dry-run mode
2. pruning enabled
3. --yes-delete passed
```

Examples:

```bash

## Destroy leftovers when retiring this setup

`destroy-leftovers` is a separate destructive command for the case where you no longer want to use this app/setup and want to remove app-created source send-cache and/or destination backup leftovers. It ignores retention rules and `state.json` because it is not a normal prune operation. It never deletes `source.snapshot_root`, because that belongs to Timeshift and contains the user's own source snapshots.

Source send-cache cleanup deletes nested Btrfs subvolumes deepest-first. Cache entries can be container subvolumes such as `send-cache/<snapshot>` with child payload subvolumes such as `send-cache/<snapshot>/@`. The app walks the Btrfs tree, deletes children before parents, and never falls back to recursive ordinary deletion. The destination is handled the same way: received `@`/`@home` subvolumes are deleted before the date subvolume, which also removes `info.json`. An ordinary non-empty configured source or destination root is refused for manual inspection in both dry-run and real-run modes. Destination snapshot-date cleanup also refuses unexpected nested Btrfs subvolumes or unexpected ordinary content instead of deleting an unknown tree.

A real cleanup target is reported as `complete` only after all planned subvolume paths returned exact deletion confirmations and a separate final existence check confirmed that the configured root is absent. The terminal prints `verified configured root absent: yes` immediately before `result: complete`. Zero confirmations, fewer confirmations than planned, an existence-check failure, a surviving configured root, or any remaining child subvolume marks the target `incomplete`. If the root remains, the app rebuilds its Btrfs index and prints every remaining subvolume for diagnosis. The source and destination targets use the same completion rule.

Dry-run is the default:

```bash

## Logging and notifications

Set top-level `log_dir` to enable split per-run logs. Logging starts immediately after the config is loaded and before command work begins. Normal app stdout is copied to `.log`. Normal command stderr is copied to `.err`. This applies to sync/prune and also to guarded maintenance/destructive commands such as `destroy-leftovers`, `clear-state`, and `delete-lock`. Transfer stderr is handled differently because successful `btrfs send` and `mbuffer` both write normal status/progress to stderr: that transfer text is kept in `.btrfs`/`.mbuffer`, and is copied to `.err` only if the transfer pipeline fails.

For `destroy-leftovers`, logs must survive the cleanup. If the configured `log_dir` is inside a selected delete target, the command warns and uses a survivor log directory outside the target, such as `./logs` or `~/.cache/timeshift-btrfs-sync/logs`. This avoids opening log files inside a tree that is about to be removed. Local containment is resolved through real filesystem paths, so a symlinked log directory that points inside a delete target is also moved to a survivor location.

```text
*.log      normal command/control output
*.err      real command/pipeline error output
*.btrfs    Btrfs send/receive command headers and status/verbose output
*.mbuffer  mbuffer progress and summary
*.succes   readable sync/retention statistics and success mail body
```

Email notifications can attach these log files when `mail.attach_logs = true`. Missing files and 0-byte files are skipped. `mail.max_attachment_bytes` can limit attachment size. When `.succes` exists and has content, its text is used as the plain-text email message body.

MQTT notifications publish simple JSON status to the configured topic. Failure messages include exit code, error text, and latest captured stderr. MQTT uses optional `paho-mqtt`; email uses Python standard library `smtplib` / `email`.

## Transfer output

`mbuffer` is the useful live throughput display. It can show rate, total transferred, elapsed time, and buffer fill. Btrfs verbose output is optional and can be useful for debugging, but it is operation/detail output, not a percentage progress bar.

The app does not estimate a progress bar from Btrfs disk-usage values because those values can be very different from the real send-stream size.

## Destination filesystem compression

The app does not set destination Btrfs compression properties. If you want received backup snapshots to be stored compressed on the receiving end, mount the receiving Btrfs filesystem/subvolume with compression enabled before running the app.

For example, configure the receiving mount outside this app with a Btrfs mount option such as `compress=zstd` or `compress=zstd:<level>` in `/etc/fstab`, then use that mounted path as `destination.target_root`.

`source.send_compressed_data = true` only controls the Btrfs send stream. It can send already-compressed source extents efficiently when supported, but it does not configure destination compression. Destination compression is decided by how the receiving Btrfs filesystem/subvolume is mounted or configured outside the app.

## Installation and executable builds

Install instructions, editable install steps, and PyInstaller executable build commands are kept in [`INSTALL.md`](INSTALL.md).

For a normal source install:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e .
ts-btrfs --version
```

For PyInstaller builds, see the dedicated `INSTALL.md` section for both folder-style and one-file executables.

## Usual test flow

```bash
ts-btrfs test-source --config ./config.toml
ts-btrfs list-source --config ./config.toml
ts-btrfs sync --config ./config.toml --dry-run
ts-btrfs sync --config ./config.toml --run --limit 1
```

When that looks correct, run a full sync:

```bash
ts-btrfs sync --config ./config.toml --run
```

Run with pruning only when you are ready for destination deletes:

```bash
ts-btrfs sync --config ./config.toml --run --prune --yes-delete
```

Inspect a single or complete-chain restore plan without modifying Timeshift:

```bash
ts-btrfs restore --config ./config.toml \
  --snapshot 2026-07-15_05-00-02 \
  --dry-run

# Or find the latest state/Btrfs UUID-confirmed common parent and preview all newer backups.
ts-btrfs restore --config ./config.toml --all --dry-run
```

## Configuration

Generate the complete normal sync/local-restore profile:

```bash
ts-btrfs init-config --profile sync --path ./config.toml
nano config.toml
```

Generate the complete SSH-backup-to-local-Timeshift pull-restore profile:

```bash
ts-btrfs init-config --profile restore-pull --path ./config-restore-pull.toml
nano config-restore-pull.toml
```

Both packaged profiles contain every current configuration key with comments. The pull-restore profile is preconfigured with `[restore] mode = "ssh"`, `[ssh]` describing the backup host, remote meanings for `destination.target_root` and `state_file`, and a local `lock_file`. `source.mode` remains available only for sync/source commands. Its SSH section documents key authentication, `password`, `password_file`, `sshpass`, port, cipher, compression, ControlMaster, host-key checking, timeouts, keepalives, and jump-host arguments.

The packaged `timeshift_btrfs_sync/data/config.example.toml` file contains all options with safe defaults. Keep `default_dry_run = true` and `retention.cleanup_ondemand = false` unless you intentionally want less conservative behavior. Incremental sends require a proven matching parent; there is no unsafe override to continue when source and destination parent metadata does not match. Manual snapshot creation follows the same safety model: existing destinations require a UUID-confirmed source/destination anchor and a proven next-parent path before Timeshift is asked to create a new source snapshot, while a destination that was empty at run start may start with a full seed.

## Command reference

Top-level help lists every command. Command-specific flags are visible with `ts-btrfs <command> --help` or `python3 -m timeshift_btrfs_sync <command> --help`.

### Global

| Flag | What it does | Why it may be needed |
|---|---|---|
| `--help` | Shows help for the main command or subcommand. | Use it to check the exact supported flags in the installed package. |
| `--version` | Prints the app version. | Useful when confirming which package is installed. |

### `init-config`

Writes one complete commented config profile.

| Flag | What it does | Why it may be needed |
|---|---|---|
| `--path PATH` | Writes the selected profile to `PATH`; default is `./ts-btrfs.toml`. | Lets you create a config in the folder or name you prefer. |
| `--profile sync` | Writes the normal sync/local-restore profile; this is the default. | Use for SSH-source backup, local backup, and restore from a locally mounted backup repository. |
| `--profile restore-pull` | Writes the complete SSH-backup-to-local-Timeshift profile. | Sets `[restore] mode = "ssh"`; includes every supported SSH authentication and transport option with comments. |
| `--force` | Overwrites the target file if it already exists. | Needed when refreshing an existing generated template. Review changes before replacing a real config. |

### `test-source`

Tests the configured source endpoint and the required source sudo commands. In `source.mode = "local"`, SSH is skipped.

| Flag | What it does | Why it may be needed |
|---|---|---|
| `--config`, `-c` | Loads the chosen TOML config. | Needed so the app knows source mode, source command paths, and SSH settings when SSH mode is used. |

### `list-source`

Lists source Timeshift snapshots.

| Flag | What it does | Why it may be needed |
|---|---|---|
| `--config`, `-c` | Loads the chosen TOML config. | Needed for source mode and source snapshot settings. |
| `--verify-btrfs` | Runs slower Btrfs checks for every configured source subvolume during listing. | Useful when validating a new `snapshot_root` or subvolume layout. Omit it for faster normal listing. |

### `sync`

Pulls missing source snapshot subvolumes to the destination.

| Flag | What it does | Why it may be needed |
|---|---|---|
| `--config`, `-c` | Loads the chosen TOML config. | Needed for all source, destination, stream, retention, and notification settings. |
| `--dry-run` | Prints the sync/prune plan without destination preparation, lock creation, receiving, state writing, manual snapshot creation, or deletion. | Safest way to inspect what the app intends to do without touching the destination, except optional log files. |
| `--run` | Performs real send/receive work. | Required for actual backup changes. |
| `--limit LIMIT` | Transfers at most this many subvolumes. | Useful for first live testing, for example `--run --limit 1`. |
| `--snapshot SNAPSHOT` | Syncs only one Timeshift snapshot name. | Useful for targeted testing or retrying one known snapshot. Automatic manual snapshot creation is skipped. |
| `--resend` | Tries to transfer even if `state.json` says it was already synced. | Useful for controlled repair/testing, but should be used carefully to avoid conflicts. |
| `--prune` | Runs destination pruning after sync. | Needed when you want retention cleanup after the backup. Real deletion still needs `--run --yes-delete`. |
| `--yes-delete` | Allows real pruning deletes when pruning is enabled and command is non-dry-run. | Extra safety confirmation for destructive deletion of destination snapshots. |

### `prune`

Applies destination retention without syncing first.

| Flag | What it does | Why it may be needed |
|---|---|---|
| `--config`, `-c` | Loads the chosen TOML config. | Needed for destination and retention settings. |
| `--dry-run` | Shows what would be deleted without creating a lock file, saving state, or deleting anything. | Use before real pruning to verify retention behavior. |
| `--run` | Allows pruning to run for real if `--yes-delete` is also present. | Required for actual deletion. |
| `--yes-delete` | Confirms real deletion. | Prevents accidental destructive retention cleanup. |

### `restore`

Restores either one backup or a complete backup chain to `source.snapshot_root` in Timeshift's native layout. `--all` finds the newest common parent by current Timeshift UUID, backup Received UUID, and the same `state.json` identity record. `info.json` provenance remains a separate cross-OS warning, but it cannot invalidate an exact UUID-proven common parent. When the exact recorded read-only source send parent still exists, the first newer backup is incremental; otherwise restore explains why a full hidden seed is required. Writable Timeshift payloads are CoW snapshots of the hidden received subvolumes.

| Flag | What it does | Why it may be needed |
|---|---|---|
| `--config`, `-c` | Loads source endpoint, backup destination, stream, sudo, state, and lock settings. | Required to locate the backup, current Timeshift repository, and UUID identity history. |
| `--snapshot SNAPSHOT` | Restores exactly one timestamp with a full send. | Use for an isolated snapshot import. Mutually exclusive with `--all`. |
| `--all` | Restores every backup newer than the latest state/Btrfs UUID-confirmed common parent. | Starts incrementally when the exact recorded read-only receive parent still exists; otherwise uses one explained full seed followed by incrementals. Mutually exclusive with `--snapshot`. |
| `--allow-no-common-parent` | Allows `--all` to proceed when no common snapshot can be proven. | Dangerous escape hatch for a full oldest-to-newest restore. It adds stronger typed confirmation. |
| `--allow-os-identity-mismatch` | Allows restore without an exact UUID common parent when current Timeshift `info.json` provenance does not match the backup `sys-uuid` and Btrfs type. | Dangerous escape hatch when the backup may belong to another OS. It requires `I UNDERSTAND THIS BACKUP MAY BELONG TO ANOTHER OS`. An exact UUID-proven common parent does not need this override. |
| `--dry-run` | Validates backup/source/state UUIDs, `info.json` OS identity, and exact receive-parent availability without changing Timeshift. | Always use first; it shows whether the first transfer will be incremental or why a full seed is required. |
| `--run` | Performs the restore. | Required to modify the Timeshift repository. |
| `--create-pre-restore-snapshot` | Creates and verifies one Timeshift on-demand safety snapshot before any receive. | The snapshot is created only on the Timeshift restore target, never on the backup repository, and is retained if restore later fails. |
| `--i-understand-this-modifies-timeshift` | Required with `--run`. | Confirms direct Timeshift changes; the command then also requires `I UNDERSTAND TIMESHIFT MAY DELETE RESTORED SNAPSHOTS OR OLDER THAN RESTORED SNAPSHOTS` before receiving data. |

A local restore normally needs to run as root unless `source.sudo` can run the exact ordinary filesystem commands listed in the restore-permissions section. In SSH mode those permissions are required on the remote source.

### `create-manual`

Creates one source Timeshift on-demand snapshot using the configured source. Timeshift assigns tag `O` by default.

| Flag | What it does | Why it may be needed |
|---|---|---|
| `--config`, `-c` | Loads the chosen TOML config. | Needed for source mode, Timeshift command, and manual snapshot safety settings. |
| `--comment COMMENT` | Passes a custom comment to `timeshift --create --comments`. | Useful to identify why the snapshot was created and to include the configured marker text. |

### `clear-state`

Removes the configured `state_file` after guarded confirmation. This command does not delete source snapshots, source cache snapshots, destination snapshots, or Timeshift-owned paths. It is useful after a failed transfer when you want the next sync to rebuild state from exact Btrfs UUID matches. When `log_dir` is enabled, the command writes the normal split run logs.

Real removal acquires the existing app lock first, so it refuses to run while another sync/prune job is active. It does not create destination/helper folders as a side effect.

| Flag | What it does | Why it may be needed |
|---|---|---|
| `--config`, `-c` | Loads the chosen TOML config. | Required so the app knows the exact configured `state_file`, `lock_file`, and job name. |
| `--dry-run` | Shows the configured state file that would be removed. | Default mode; does not remove anything. |
| `--run` | Allows real state-file removal. | Still requires the long danger flag and typed confirmations. |
| `--i-understand-this-clears-state` | Required with `--run`. | Confirms you understand removing state can break incremental continuity unless state recovery can prove UUID matches. |

### `delete-lock`

Removes the configured `lock_file` only when it is stale and no running `ts-btrfs` process currently holds it. This command is not for stopping a running sync/prune job. Stop the process first; then use `delete-lock` only if the file remains. When `log_dir` is enabled, the command writes the normal split run logs.

| Flag | What it does | Why it may be needed |
|---|---|---|
| `--config`, `-c` | Loads the chosen TOML config. | Required so the app knows the exact configured `lock_file` and job name. |
| `--dry-run` | Shows the configured lock file that would be removed. | Default mode; does not remove anything. |
| `--run` | Allows real stale-lock removal. | Still requires the long danger flag and typed confirmations. |
| `--i-understand-this-deletes-lock` | Required with `--run`. | Confirms you understand deleting a lock must not be used to bypass an active running job. |

### `show-state`

Shows the local state tracking file.

| Flag | What it does | Why it may be needed |
|---|---|---|
| `--config`, `-c` | Loads the chosen TOML config. | Needed to locate `state.json`. |
| `--json` | Prints raw `state.json`. | Useful for debugging parent metadata or automation parsing. |

### `destroy-leftovers`

Destroys configured source/destination leftovers when this app setup is being retired. This is not a prune command and does not use retention or `state.json` safety. Configured Btrfs roots are scanned recursively and their child subvolumes are deleted deepest-first before the root subvolume. There is no recursive ordinary-directory fallback. A configured ordinary non-empty source cache root or destination root is refused and must be inspected manually in both dry-run and real-run modes; an empty ordinary root may be removed with `rmdir`. Unexpected nested destination Btrfs subvolumes are also refused rather than treated as configured payload children. The command never deletes `source.snapshot_root`.

For a real run, every discovered deletion path must be individually confirmed by the deletion command. The command then checks the configured root again. `result: complete` is printed only together with `verified configured root absent: yes`. When the root still exists, `destroy-leftovers` rebuilds the current Btrfs index below it and prints all remaining subvolumes; the summary counts that target as incomplete and the command returns an error.

Tree discovery first reads the exact root subvolume ID, then uses one filesystem-wide `btrfs subvolume list -a -p <configured-root>` command per endpoint. It follows numeric containing-parent IDs from that root before mapping paths back to the current mount. This is required for nested app layouts because date containers are themselves subvolumes and contain payload subvolumes such as `@` and `@home`. The deletion plan therefore contains payload children first, then date containers, then `snapshots`/cache containers, and finally the configured root. Local source, SSH source, and local destination use the same discovery and deepest-first batch-deletion implementation.

| Flag | What it does | Why it may be needed |
|---|---|---|
| `--config`, `-c` | Loads the chosen TOML config. | Required so the app knows the exact configured paths and job name. |
| `--delete-source` | Deletes `source.cache_root` when configured. | Removes app-created source send-cache leftovers only; never deletes `source.snapshot_root`. |
| `--delete-destination` | Deletes `destination.target_root`. | Removes the backup target tree, including received snapshots and `.ts-btrfs-sync`. |
| `--delete-both` | Deletes `source.cache_root` and `destination.target_root`. | Full retirement cleanup for app-created source send-cache plus backup destination; never deletes `source.snapshot_root`. |
| `--dry-run` | Shows the destructive cleanup plan. | Default mode; does not delete anything. |
| `--run` | Allows real deletion. | Still requires the long danger flag and typed confirmations. |
| `--i-understand-this-destroys-data` | Required with `--run`. | Prevents accidental execution of this destructive command. |

When `--delete-both` is used, the command prints `SOURCE / DESTINATION SNAPSHOT MATCH`. This is a reporting aid only; deletion still ignores state.json and only targets the explicitly configured source cache and destination target.

## Config reference

Every option below is present in both packaged profiles. Commented entries are optional but supported. The two files differ only in profile-oriented defaults and path/transport explanations; they expose the same current schema.

### Top-level options

| Option | What it does | Why it may be needed |
|---|---|---|
| `name` | Human-readable job name used in output, notifications, and log filenames. | Helps recognize which backup job sent a mail/MQTT message or produced a log. |
| `default_dry_run` | Makes commands preview by default unless `--run` is passed. Dry-run skips destination preparation, lock creation, receives, state writes, manual snapshot creation, and prune deletion. | Safe default to avoid accidental writes or deletes while checking the plan. |
| `prune_after_sync` | Automatically runs the prune step after successful sync. | Useful for scheduled jobs, but real deletion still requires `--run --yes-delete`. |
| `log_dir` | Directory for split per-run log files; blank/omitted disables file logging. The logger creates only the exact log directory when its parent already exists; destination helper preflight prepares missing log directories during real sync/prune. | Needed for persistent debug logs and email log attachments without letting logging accidentally create destination roots as ordinary directories. |
| `state_file` | Optional custom path for `state.json`; default is under `<target_root>/.ts-btrfs-sync/`. | Use only when you need app metadata outside `target_root`. |
| `lock_file` | Optional custom path for the lock file; default is under `<target_root>/.ts-btrfs-sync/`. In real sync/prune, the lock-file parent is prepared before other path checks and may be either a directory or Btrfs subvolume. | Prevents two jobs from writing the same target at the same time; if the lock path includes `target_root`, that component is created by the strict Btrfs subvolume rule. |

### `[mqtt]`

| Option | What it does | Why it may be needed |
|---|---|---|
| `enabled` | Turns MQTT notifications on or off. | Keep false unless you want MQTT status messages. If false, `paho-mqtt` is not required. |
| `host` | MQTT broker hostname or IP. | Needed when MQTT is enabled so the app knows where to publish. |
| `port` | MQTT broker port, normally `1883`. | Change if your broker uses a non-default port. |
| `topic` | MQTT topic for JSON status messages. | Home Assistant sensors/automations subscribe to this topic. |
| `username` | Optional MQTT username. | Needed for brokers that require authentication. |
| `password` | Optional MQTT password directly in config. | Works, but `password_file` is safer. Use only one of `password` or `password_file`. |
| `password_file` | File containing the MQTT password. | Keeps secrets out of the main config file. |
| `client_id` | Optional fixed MQTT client ID. | Useful when you want a predictable MQTT client name. If omitted, one is generated. |
| `qos` | Publish QoS: `0`, `1`, or `2`. | Higher QoS can improve delivery guarantees but may add broker/client overhead. |
| `retain` | Retains the last status message on the broker. | Useful for Home Assistant to see the latest status after restart, but can show stale status. |
| `timeout` | Connect/publish timeout in seconds. | Avoids notification hangs if the broker is unreachable. |
| `notify_on_success` | Publishes success messages. | Disable if you only want failure alerts. |
| `notify_on_failure` | Publishes failure messages. | Usually keep true so failed backups alert you. |

### `[mail]`

| Option | What it does | Why it may be needed |
|---|---|---|
| `enabled` | Turns email notifications on or off. | Keep false unless you want SMTP status mail. |
| `smtp_host` | SMTP server hostname or IP. | Required when mail is enabled. |
| `smtp_port` | SMTP server port, commonly `587` for STARTTLS or `465` for implicit SSL. | Must match your mail provider/server. |
| `smtp_ssl` | Uses implicit SSL with `smtplib.SMTP_SSL`. | Use for port `465` style SMTP. |
| `starttls` | Upgrades a plain SMTP connection with STARTTLS. | Use for port `587` style SMTP when `smtp_ssl = false`. |
| `timeout` | SMTP connect/send timeout in seconds. | Prevents notification delivery from hanging the backup process too long. |
| `username` | Optional SMTP username. | Needed when the SMTP server requires login. |
| `password` | Optional SMTP password directly in config. | Works, but `password_file` is safer. Use only one of `password` or `password_file`. |
| `password_file` | File containing the SMTP password. | Keeps secrets out of the main config file. |
| `from_addr` | Sender email address. | Required by most SMTP servers and for readable mail. |
| `to_addrs` | Recipient list. | Required when mail is enabled. |
| `subject_prefix` | Prefix added to success/failure subjects. | Helps filter or recognize backup emails. |
| `include_json` | Adds the JSON status payload to the email body. | Useful for debugging or parsing mail content. |
| `attach_logs` | Attaches non-empty `.log`, `.err`, `.btrfs`, `.mbuffer`, and `.succes` files. | Useful for diagnostics without logging into the backup host. Requires `log_dir`. The `.succes` text is also used as the email body when present. |
| `max_attachment_bytes` | Per-file attachment size cap; `0` means no cap. | Prevents huge verbose logs from being mailed. |
| `notify_on_success` | Sends success emails. | Disable if you only want failure mail. |
| `notify_on_failure` | Sends failure emails. | Usually keep true so failed backups alert you. |

### `[ssh]`

Used when `source.mode = "ssh"` for normal sync/source commands, or when `[restore] mode` is `"ssh"` or `"ssh-target"`. In restore mode `"ssh"`, the SSH endpoint is the backup host; in `"ssh-target"`, it is the Timeshift target.

| Option | What it does | Why it may be needed |
|---|---|---|
| `host` | SSH endpoint hostname or IP. | In normal SSH source mode this is the Timeshift host; in restore pull mode it is the backup host. |
| `user` | SSH endpoint user. | Use a dedicated low-privilege account with only the permissions required by the selected direction. |
| `port` | Optional SSH port. | Needed if the source does not use port `22`. |
| `identity_file` | SSH private key path passed with `ssh -i`. | Recommended for unattended scheduled jobs. |
| `compression` | Adds `ssh -C`. | Can help on slow links; often unnecessary on fast LANs or already-compressed streams. |
| `cipher` | Adds `ssh -c <cipher>`. | Lets you choose a fast cipher for your hardware/network. Omit for OpenSSH defaults. |
| `control_master` | Adds OpenSSH `ControlMaster=auto`. | Reuses an existing SSH connection so password-protected keys are unlocked fewer times. Disabled by default because the local control socket must be protected. |
| `control_persist` | Adds OpenSSH `ControlPersist=<value>`. | Keeps the master connection alive between metadata probes and send commands. Default example is `10m`. |
| `control_path` | Adds OpenSSH `ControlPath=<path>`. | Required when `control_master = true`. If the parent directory is missing, the app creates it with owner-only access (`0700`). Existing parents must already be owned by the app user and private. |
| `password` | SSH password passed through `sshpass -e`. | Less safe than key auth; use only if needed. Do not use with `BatchMode=yes`. |
| `password_file` | File containing the SSH password for `sshpass -e`. | Safer than storing the SSH password directly in config. |
| `extra_args` | Extra OpenSSH arguments as a string list. | Commonly used for `BatchMode=yes` with key auth or host-key behavior. |

#### Safe SSH ControlMaster use

`control_master` is optional OpenSSH connection multiplexing. The first SSH command authenticates normally, then OpenSSH keeps a local master connection alive for `control_persist`. Later `ssh` commands reuse a Unix-domain control socket instead of unlocking the private key again. This can still help mutation, cleanup, manual-snapshot, and transfer commands. Normal sync discovery already combines Timeshift plus both source Btrfs indexes into one SSH command, so multiplexing is no longer required merely to avoid per-snapshot metadata authentication.

The security tradeoff is important: anyone who can access the local control socket may be able to reuse the already-authenticated SSH connection without knowing the private key passphrase. In this app that connection reaches the source SSH user, which often has restricted passwordless `sudo btrfs`/`timeshift` permissions, so the socket must be private.

A safe setup when the app runs as root on the destination is to use a private path under `/run`:

```toml
[ssh]
control_master = true
control_persist = "10m"
control_path = "/run/ts-btrfs-ssh/%C"
```

The app validates this at config load time. With `control_master = true`, `control_path` must be absolute. If the ControlPath parent directory is missing, the app creates it with owner-only permissions (`0700`) as the user running `ts-btrfs`; missing intermediate directories it creates are also set to `0700`. Existing directories are not ownership-fixed automatically: they must already be owned by the user running `ts-btrfs`, must not be readable/writable/searchable by group or other users, and must not be inside shared temporary locations such as `/tmp`, `/var/tmp`, or `/dev/shm`.

Leave `control_master = false` for maximum isolation, on shared machines, or anywhere you cannot guarantee the socket directory is private.

### `[restore]`

| Option | What it does | Why it may be needed |
|---|---|---|
| `mode` | Selects restore direction: `local` = local backup → local Timeshift; `ssh` = SSH backup → local Timeshift; `ssh-target` = local backup → SSH Timeshift. | Makes the restore transport explicit and independent from `source.mode`, which remains sync-only. |

Timeshift's native timestamp path remains an ordinary directory. Restore mode changes only which endpoint supplies the backup and which endpoint receives Timeshift payloads; it does not change the native Timeshift layout. `source.snapshot_root` and `source.cache_root` are one inseparable Timeshift-side path pair: modes `local` and `ssh` use both locally, while `ssh-target` uses both on the SSH Timeshift host. The remote backup endpoint never reads or creates `source.cache_root`.

### `[manual_snapshot]`

| Option | What it does | Why it may be needed |
|---|---|---|
| `enabled` | Makes normal `sync` create one source Timeshift on-demand snapshot before syncing. | Useful when you want every sync run to start with a fresh source snapshot. |
| `cleanup_enabled` | Allows destination prune to delete old app-created on-demand snapshots recognized by marker. | Keeps app-created manual snapshots from growing forever. Real deletion still needs prune plus `--yes-delete`. |
| `comment` | Comment passed to `timeshift --create --comments`. | Makes the snapshot recognizable in Timeshift and should include the marker. |
| `marker` | Text used to recognize app-created on-demand snapshots. | Separates app-created on-demand snapshots from your normal manual Timeshift snapshots. |
| `retention_count` | Number of app-created on-demand snapshots to keep by marker. | Gives app-created snapshots independent retention from normal `O` snapshots. |

### `[source]`

| Option | What it does | Why it may be needed |
|---|---|---|
| `mode` | Chooses where Timeshift source/restore-target commands run. Default is `ssh`. | Use `local` for a local Timeshift repository. SSH-backup pull restore requires `local` because `[ssh]` identifies the backup host in that mode. |
| `sudo` | Source sudo prefix, normally `sudo -n`. | Required for Timeshift/Btrfs commands without interactive prompts. |
| `btrfs_command` | Source Btrfs command name/path. | Use an absolute path if the remote sudo PATH is restricted. |
| `timeshift_command` | Source Timeshift command name/path. | Use an absolute path if needed by sudo or your distro. |
| `snapshot_root` | Source Timeshift snapshot root. | Must already exist and may be an ordinary directory on Btrfs; the app builds `<snapshot_root>/<snapshot>/<subvolume>` from this and never creates, prunes, deletes, destroys, or cleans it. In SSH mode this must be the path on the remote source. |
| `subvolumes` | Subvolume names expected inside each Timeshift snapshot, usually `@` and `@home`. | Controls what gets sent for each Timeshift snapshot. |
| `verify_subvolumes_at_discovery` | Verifies every listed snapshot/subvolume during discovery. | Slower but useful when validating a new layout. Keep false for fast normal dry-runs. |
| `verify_incremental_parent_once_per_run` | Verifies parent paths from previous runs, then permits paths successfully sent and received by the current process to be reused without another targeted metadata read. | Reduces repeated SSH probes while preserving UUID confirmation for pre-existing parents. |
| `source_change_retry_count` | Maximum automatic full-inventory rebuild/recovery attempts per snapshot/subvolume after a required source or parent path disappears or changes UUID during preparation or send. `0` disables continuation. | Lets hourly Timeshift pruning be recovered safely without an infinite retry loop or treating unrelated failures as source churn. |
| `cache_root` | Source-side root for read-only send-cache snapshots. | Needed when Timeshift snapshots are writable and cannot be sent directly. Must be outside `source.snapshot_root`; do not point it at the Timeshift snapshots directory. If missing, real preflight creates it as a Btrfs subvolume when `create_readonly_cache = true`; its parent must already exist and be Btrfs-accessible. `destroy-leftovers --delete-source` checks this path with configured sudo+Btrfs before falling back to source-shell visibility. |
| `create_readonly_cache` | Creates read-only cache snapshots for writable source snapshots. | Required for writable Timeshift snapshots because `btrfs send` needs read-only sources. |
| `cleanup_superseded_cache` | Controls app-owned source send-cache cleanup during retention. | Applies to standalone `prune` and prune invoked after `sync`, in local and SSH modes. The cache date is deleted only after the matching destination date is confirmed gone; normal transfer keeps cache snapshots for incremental parents. |
| `send_compressed_data` | Adds `btrfs send --compressed-data`. | Attempts to preserve already-compressed source extents when supported. It does not configure destination compression; mount the receiving Btrfs filesystem/subvolume with compression enabled if you want destination compression. |
| `send_proto` | Adds `btrfs send --proto <N>`. | Needed only when you intentionally want a specific Btrfs send protocol version. |

### `[destination]`

| Option | What it does | Why it may be needed |
|---|---|---|
| `target_root` | Backup repository root. | Normal sync/prune/destroy use it locally. Restore pull mode reads this path on the SSH backup host. If missing during normal sync and creation is enabled, preflight creates it locally as a Btrfs subvolume. |
| `sudo` | Destination sudo prefix, normally `sudo -n`. | Required for local `btrfs receive` and subvolume delete commands. |
| `btrfs_command` | Destination Btrfs command name/path. | Use an absolute path if needed by sudo or your distro. |
| `create_target_root` | Allows preflight to create a missing `target_root` as a Btrfs subvolume and create internal metadata directories. | Convenient for first setup. Disable if you want missing paths to be an error. |
| `cleanup_incomplete_receive` | Removes incomplete destination receives not recorded in state. | Allows safe retry after cancelled transfers only after a non-empty-at-start destination has a complete UUID-confirmed chain anchor. Only Btrfs subvolumes or empty dirs are auto-deleted. |

### `[stream]`

| Option | What it does | Why it may be needed |
|---|---|---|
| `use_mbuffer` | Inserts `mbuffer` between source send and local receive. | Gives useful throughput/total display and smooths network/disk bursts. |
| `mbuffer_command` | mbuffer command name/path. | Use an absolute path or alternative command name if needed. |
| `mbuffer_size` | Memory buffer size passed to `mbuffer -m`. | Larger buffers can smooth bursts; too large wastes RAM. |
| `mbuffer_rate` | Optional rate limit passed to `mbuffer -R`. | Useful if backups should not saturate network or disks. |
| `mbuffer_extra_args` | Extra mbuffer arguments as a string list. | Allows advanced mbuffer tuning without code changes. |
| `btrfs_verbose` | Adds `-v` to `btrfs send` and `btrfs receive`. | Useful for debugging stream operations. Can be noisy and is not a progress bar. |

### `[retention]`

| Option | What it does | Why it may be needed |
|---|---|---|
| `hourly` | Number of newest Timeshift `H` snapshots to keep. | Controls hourly backup history on the destination. |
| `daily` | Number of newest Timeshift `D` snapshots to keep. | Controls daily backup history on the destination. |
| `weekly` | Number of newest Timeshift `W` snapshots to keep. | Controls weekly backup history on the destination. |
| `monthly` | Number of newest Timeshift `M` snapshots to keep. | Controls monthly backup history on the destination. |
| `boot` | Number of newest Timeshift `B` snapshots to keep. | Controls boot snapshot history on the destination. |
| `ondemand` | Number of newest normal/user-created Timeshift `O` snapshots to keep when `cleanup_ondemand = true`. | Ignored unless normal on-demand cleanup is explicitly enabled. |
| `cleanup_ondemand` | Allows pruning normal/user-created Timeshift `O` snapshots. | Default false protects manually created Timeshift snapshots. |
| `keep_latest` | Always keeps the newest synced snapshot. | Extra safety so retention does not remove the newest backup. |
| `keep_latest_common_parent` | Keeps the newest likely common parent for incremental safety. | Reduces risk of pruning the parent needed for future incrementals. |
| `protected_snapshots` | Snapshot names that are never pruned. | Use for important snapshots you want retention to ignore. |
