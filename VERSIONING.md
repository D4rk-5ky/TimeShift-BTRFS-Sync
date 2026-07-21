## 0.1.49

- Fixed shared Btrfs tree discovery after the 0.1.47 refactor. The previous one-root `btrfs subvolume list -o` plan could contain only direct date/container subvolumes and omit nested `@`/`@home` payloads, causing parent deletion to fail with `Directory not empty`.
- Changed the authoritative `BtrfsOps.list_children()` operation to read the exact root subvolume ID and request one filesystem-wide `btrfs subvolume list -a -p <root>` containment graph. Numeric parent IDs retain only actual descendants before the central mount-aware path mapper resolves them.
- Kept normal source/cache/destination inventory root-scoped. The full filesystem graph is used only by recursive managed-tree deletion and post-failure remaining-tree verification.
- Preserved one endpoint command for tree discovery and one endpoint command for deepest-first batch deletion; SSH mode does not open one connection per date or payload subvolume.
- Preserved deletion safety: protected roots, ordinary non-empty root refusal, exact confirmation validation, unexpected-content checks, remaining-tree inventory, and final root-absence proof are unchanged.
- Added realistic regression coverage for local cache trees, destination trees, `<FS_TREE>`/remounted path prefixes, complete child-before-parent ordering, single-batch deletion, and local/SSH tree command construction and numeric-ID filtering.
- Kept all config keys, CLI flags, state schema version 2, retention rules, oldest-to-newest sync behavior, cache reuse, UUID matching, and destructive confirmations unchanged.

## 0.1.48

- Fixed the real-run preflight crash after lock acquisition by restoring the shared `_parse_path_check_output()` sentinel parser removed during the 0.1.47 refactor. Local-source and SSH-source preflight now use the same defined parser for snapshot/cache root results.
- Added a package-wide static runtime-symbol regression test so any function that references an undefined module global fails the test suite before release.
- Corrected sync planning so every retention-selected source subvolume remains in the oldest-to-newest queue. Existing state/destination entries are again evaluated by the established live UUID, recovery, and `info.json` refresh checks instead of being prematurely filtered by the pure planner.
- Restored prune action order to destination date tree, source cache tree, then state entry, matching the pre-refactor safety behavior.
- Restored symlink-aware local containment checks for survivor log placement during `destroy-leftovers`; lexical POSIX containment remains reserved for source/SSH paths.
- Tightened the shared tree-deletion engine so dry-run and real-run both refuse ordinary non-empty configured roots, and destination date cleanup rejects unexpected nested Btrfs subvolumes in addition to unexpected ordinary entries.
- Restored conservative Btrfs list-path mapping: unmatched absolute or relative paths are no longer guessed below a configured root, while valid remount-prefix suffix matching remains supported.
- Restored empty optional source-path normalization to the empty string instead of `.` so disabled paths cannot accidentally participate in containment checks.
- Corrected `destroy-leftovers` dry-run reporting so a blocking safety error is printed and counted as incomplete rather than as a complete plan.
- Removed unused refactor methods and stale imports without reintroducing duplicate Btrfs, inventory, cache, or deletion implementations.
- Kept all configuration keys, CLI commands, state schema version 2, retention rules, oldest-to-newest transfer order, UUID safety, cache reuse, recovery, and Btrfs-only deletion behavior unchanged.
- Added focused regression coverage for the preflight parser, undefined globals, planner queue preservation, prune ordering, symlink-aware local containment, conservative Btrfs path mapping, empty-path normalization, ordinary-root dry-run refusal, unexpected nested destination subvolumes, and destroy dry-run failure reporting.

## 0.1.47

- Performed a behavior-preserving architectural refactor around seven shared layers: command endpoints, Btrfs operations, coherent inventory, combined snapshot records, pure workflow planning, generic ordered execution, and shared cache/tree safety operations.
- Replaced separate local/SSH Btrfs command implementations with `CommandEndpoint` plus `BtrfsOps`; workflow code now changes the endpoint, not the Btrfs business rules.
- Made `inventory.py` the only source/cache/destination inventory implementation. `remote_index.py` remains as a compatibility re-export and contains no second scanner.
- Added `SnapshotRecord` and `BackupInventory` so source Timeshift metadata, source cache, destination metadata, and `state.json` are joined once per date and consumed by planners.
- Added side-effect-free sync, recovery, prune, and destroy action plans plus `WorkflowExecutor` for ordered execution or preview. Existing retention selection and oldest-to-newest transfer ordering are unchanged.
- Consolidated exact cache creation/reuse into `CacheManager`, including read-only and Parent UUID validation, stale-index exact probing, concurrent creation reuse, and prevention of nested `<date>/@/@` creation.
- Consolidated deepest-first source-cache/destination deletion, protected-root enforcement, exact confirmation validation, unknown-content refusal, remaining-subvolume inventory, and final root-absence verification into `delete_subvolume_tree()`. Sync recovery, prune, and destroy now use that one implementation.
- Converted the original `btrfs.py` into a compatibility export surface only; it no longer contains another command/cache/deletion implementation.
- Removed dead and duplicated helpers after redirecting all runtime consumers to the shared layers. Compared with uploaded 0.1.46, runtime package size decreased from 11,645 to 10,583 lines and function definitions decreased from 408 to 398.
- Kept config keys, CLI behavior, state schema version 2, retention behavior, full/incremental safety rules, source-change continuation, `info.json` behavior, notification behavior, and Btrfs-only cleanup rules unchanged.
- Added architecture integration tests proving the single authoritative definitions, coherent record joining, pure oldest-to-newest plans, plan/executor ordering, shared cleanup identity, exact cache targeting, and reduced source/function counts.
- Updated README.md, COMMENTED_CODE_MAP.md, CONFIG_AND_CLI_AUDIT.md, VERSIONING.md, package version metadata, and the packaged config example.

## 0.1.46

- Fixed source send-cache reuse after remounting or moving the configured source paths. Bulk Btrfs list-path resolution now recognizes the longest configured-root suffix anywhere inside filesystem-relative paths, including on-disk prefixes such as `@/` that are absent from the mount path.
- Changed cache child preparation so the exact `<source.cache_root>/<snapshot>/<subvolume>` target is probed before snapshot creation inside the same source command/SSH session. A valid existing read-only cache snapshot is reused even when the earlier bulk cache index missed it.
- Prevented Btrfs from interpreting an existing cache child such as `<date>/@` as a destination directory and attempting the nested path `<date>/@/@`, which previously produced a misleading `Read-only file system` error because the existing cache snapshot was read-only.
- Refused exact cache targets that exist as ordinary paths, writable subvolumes, or read-only snapshots with a mismatching Parent UUID instead of overwriting or nesting below them.
- Added a post-create-failure exact metadata probe in the same source command so a concurrently created safe cache snapshot can be reused without another SSH request.
- Preserved fresh-destination behavior: retention selects the source snapshots to seed, the queue remains oldest-to-newest, existing safe cache snapshots are reused, and only missing cache children are created.
- Added regression coverage for stale bulk-index cache reuse, no nested `@/@` target, ordinary-target refusal, concurrent creation reuse, and remounted Btrfs list paths with extra on-disk prefixes.
- Updated README.md, INSTALL.md, COMMENTED_CODE_MAP.md, CONFIG_AND_CLI_AUDIT.md, VERSIONING.md, package version metadata, and the packaged config example.

## 0.1.45

- Tightened `destroy-leftovers` so a real target can be complete only after every planned Btrfs subvolume path has an exact unique deletion confirmation and the configured root is independently verified absent.
- Added exact source deletion-confirmation parsing. Duplicate, malformed, and unexpected confirmation lines are errors, and every unconfirmed planned path is listed.
- Added final local destination and source-cache root existence checks after deletion, including verification after removing an empty ordinary configured root with exact-path `rmdir`.
- When a configured root remains, rebuild its Btrfs inventory and print every remaining root/child subvolume. A surviving root is incomplete even when all deletion commands returned success.
- Mark zero confirmed deletions, fewer confirmations than planned, final existence-check failures, surviving roots, and remaining child subvolumes as incomplete.
- Changed the terminal result so `result: complete` is printed only after `verified configured root absent: yes`.
- Changed the final destroy summary to use verified `DestroyResult.success`, preventing an empty error list from counting an unverified target as complete.
- Applied the same post-deletion completion checks to both source-cache and local destination cleanup.
- Added regression tests for zero/partial source confirmations, failed final checks, surviving source/destination roots, remaining-subvolume reporting, and verified successful cleanup.
- Updated README.md, COMMENTED_CODE_MAP.md, CONFIG_AND_CLI_AUDIT.md, VERSIONING.md, package version metadata, and the packaged config example.

## 0.1.44

- Upgraded persistent state to schema version 2 and made source-side paths relocatable.
- `source_path` is now stored as `<snapshot>/<subvolume>` relative to `source.snapshot_root`.
- `send_path` is now stored as `<snapshot>/<subvolume>` relative to the root selected by `send_path_kind`: app-owned cache paths resolve below `source.cache_root`, while direct read-only Timeshift paths resolve below `source.snapshot_root`.
- `parent_source_path` is now root-relative and records `parent_source_path_kind` so incremental parent paths remain unambiguous after source-root relocation.
- Kept `destination_path` relative to `destination.target_root` as before.
- Added in-memory migration for older absolute source/cache/parent/destination state paths. Migration requires the exact state snapshot/subvolume suffix, refuses path escapes or mismatched identities, and writes the relative format on the next state save.
- Updated parent selection, sync-floor confirmation, prune cache cleanup, protected Timeshift reporting, state recovery, show-state, and destroy-leftovers reporting to resolve state paths through the current configured roots before UUID checks or deletion decisions.
- Preserved the UUID safety model: moving/remounting a root does not bypass `Received UUID`/source UUID validation, and recreated cache snapshots with new UUIDs remain invalid as old incremental parents.
- Added regression coverage for cache/direct path storage, old-state migration after all roots move, parent resolution, prune resolution, and rejection of mismatched relative paths.
- Updated README.md, INSTALL.md, COMMENTED_CODE_MAP.md, CONFIG_AND_CLI_AUDIT.md, VERSIONING.md, package version metadata, and the packaged config example.

## 0.1.43

- Made the managed destination snapshot-date layout strictly Btrfs-only. Every newly created `<destination.target_root>/snapshots/<date>` container is now a Btrfs subvolume containing the received `@` and optional `@home` child subvolumes plus the regular Timeshift `info.json` control file.
- Changed destination prune and failed-transfer recovery to delete child payload subvolumes first and then delete the date-container subvolume. Deleting the date subvolume removes its regular `info.json` automatically, so no ordinary recursive cleanup is used for managed snapshot versions.
- Removed legacy ordinary destination date-folder support. Startup validation now refuses any direct `snapshots/` entry that is not a Btrfs subvolume, and prune/recovery refuse ordinary or unexpectedly populated date paths for manual inspection rather than migrating or deleting them.
- Removed both recursive ordinary-directory fallback branches from `destroy-leftovers`. A Btrfs source cache or destination tree is recursively discovered and deleted deepest-first only with `btrfs subvolume delete`; an ordinary non-empty configured root is refused and reported for manual inspection.
- Removed ordinary stale-directory cleanup from normal source-cache deletion. Cache payload children and timestamp parents are now deleted only as Btrfs subvolumes, while `source.snapshot_root` remains protected.
- Kept only narrow ordinary-file operations required for app metadata and control files, such as atomic temporary-file replacement and guarded state/lock handling. Backup and cache trees are never recursively deleted through ordinary filesystem commands.
- Added regression coverage for date-subvolume creation/reuse, refusal of legacy ordinary date folders and ordinary non-empty destroy roots, child-first Btrfs-only remote cleanup, and absence of `rm -rf` from packaged runtime Python.
- Updated README.md, INSTALL.md, COMMENTED_CODE_MAP.md, CONFIG_AND_CLI_AUDIT.md, VERSIONING.md, package version metadata, and the packaged config example.

## 0.1.42

- Added effective source account identity capture to the existing combined source inventory. SSH mode records the non-sudo remote account name and UID in the same SSH request used for Timeshift, `info.json`, snapshot-root, and cache-root discovery, so permission diagnostics add no SSH round trip.
- Improved remote metadata discovery so inability to traverse or list `source.snapshot_root` is recorded explicitly and applied to every Timeshift-listed date whose `info.json` could not be captured.
- Expanded the hard `info.json` error to print the remote SSH source account used by the destination, including its UID, and explain that this account—not local destination root—must traverse every source mount-path parent and read the control file.
- Added current README/install/config guidance for a stable privileged `/etc/fstab` Btrfs mount, narrow ownership/mode or POSIX ACL access by the printed account name/UID, and the difference between Btrfs filesystem permissions and FAT/NTFS-style `uid=`/`gid=` mount remapping.
- Added regression coverage for identity parsing, root traversal failure propagation, and the complete user/UID/fstab permission error.
- Updated README.md, INSTALL.md, COMMENTED_CODE_MAP.md, CONFIG_AND_CLI_AUDIT.md, VERSIONING.md, package version metadata, and the packaged config example.

## 0.1.41

- Added preservation of Timeshift's one shared per-snapshot-date `info.json` beside received `@` and optional `@home` subvolumes at `<destination.target_root>/snapshots/<date>/info.json`.
- Kept SSH round trips minimal: the existing combined source inventory command now reads all readable `<source.snapshot_root>/<date>/info.json` files with ordinary non-sudo `cat` in the same SSH request that runs `timeshift --list` and scans snapshot/cache Btrfs metadata. Local source mode reads the same files directly.
- Added framed parsing that preserves the exact text content, including whether the source file has a final newline, and records missing/unreadable metadata per Timeshift date.
- Made metadata completion strict: sync cannot report success for a processed snapshot date unless its source control file was captured and the destination file can be created/refreshed; paired `@`/`@home`, root-only, and home-only configurations all write the shared file once after their configured subvolume set is complete.
- Added atomic destination creation/update using a same-directory temporary file, `fsync`, and `os.replace`; symlinked destination `info.json` paths are refused.
- Added backfill/refresh for already-complete destination dates whose source snapshot remains available, without re-sending Btrfs data.
- Updated source-change reporting to include added, removed, or changed `info.json` content. Snapshot recovery removes the copied control file with the failed whole-date version, and prune removes it only after tracked destination Btrfs subvolumes are confirmed gone and no unknown sibling content remains.
- Added regression coverage for one-command SSH capture, exact framing, paired and single-subvolume completion, atomic update/idempotence, missing metadata failure, symlink refusal, and prune cleanup.
- Updated README.md, INSTALL.md, COMMENTED_CODE_MAP.md, CONFIG_AND_CLI_AUDIT.md, VERSIONING.md, package version metadata, the packaged config example, and the minimal source sudoers comments.

## 0.1.40

- Replaced separate sync-time source discovery calls with one coherent source inventory. In SSH mode a single SSH command now captures `timeshift --list`, bulk UUID/read-only metadata for `source.snapshot_root`, and bulk UUID/read-only metadata for `source.cache_root`; `destination.target_root` is indexed locally once.
- Batched source snapshot-root and cache-root preflight into one source command while preserving the rule that cache creation/checking runs only after the Timeshift-owned snapshot root emits an explicit successful safety result.
- Removed normal per-parent source-cache `subvolume show` probes. UUID/read-only parent matching now uses the coherent bulk cache inventory, while source mutations update the index and failed operations rebuild the complete inventory.
- Reduced normal cache-creation round trips: an absent cache path in the coherent index is created directly, a newly created cache parent is inserted into the index, and read-only snapshot creation plus metadata verification run in one source command. Concurrent target creation still receives a targeted exceptional refresh before reuse.
- Added bounded source-change recovery with `source.source_change_retry_count` (default `5`, `0` disables). If a required original/cache/parent path disappears or changes UUID during cache preparation or `btrfs send`, the app reports the before/after inventory difference, cleans the incomplete whole snapshot date from app-owned cache/destination/state, corrects in-run transfer accounting, rebuilds all source lists and the oldest-to-newest queue, and continues.
- Kept unrelated source churn from masking real network, mbuffer, receive, permission, or destination failures: automatic continuation occurs only when the exact paths required by the failed operation changed identity.
- Added regression tests for one-command inventory parsing, conditional one-command source preflight, one-command cache snapshot creation/verification, relevant-versus-unrelated source changes, and continuation after a source snapshot disappears during a failed send.
- Updated README.md, COMMENTED_CODE_MAP.md, CONFIG_AND_CLI_AUDIT.md, VERSIONING.md, package version metadata, and the packaged config example.

## 0.1.39

- Removed any silent acceptance of the obsolete `source.allow_incremental_without_parent_match` setting. A config containing that key now fails validation and tells the user to delete it.
- Enforced the only two safe transfer outcomes from run-start state: a destination that was empty when the run began may start with a full send, while a destination that was already populated requires at least one complete UUID-confirmed source/destination snapshot match for incremental send.
- Moved the existing-chain identity check ahead of stale/partial destination recovery. Recovery cleanup can no longer make an existing destination temporarily empty and thereby permit a full send; full-seed authorization remains fixed for the entire run.
- Improved sync and manual-snapshot safety errors so they explicitly report when source and destination do not match in any usable UUID-confirmed snapshot and explain that a full send into the existing destination is refused.
- Updated README.md, COMMENTED_CODE_MAP.md, CONFIG_AND_CLI_AUDIT.md, VERSIONING.md, package version metadata, and the packaged config example.

## 0.1.38

- Added snapshot-level sync recovery for incomplete or vanished Timeshift snapshot dates. If any configured source subvolume such as `@` or `@home` is missing under `source.snapshot_root/<date>`, the app now removes stale app-owned source-cache paths, the failed destination `snapshots/<date>` version, and the state entry, then skips that vanished date and continues.
- If all configured source subvolumes still exist but the current snapshot date has partial state or partial destination content, sync now clears the failed current cache/destination/state version and retries the whole date so `@` and `@home` are transferred as one consistent version.
- Added start-of-run cleanup for stale incomplete state entries whose Timeshift source snapshot is no longer listed, so a later sync can recover from a failed or missed snapshot left by an earlier run.
- Recovery cleanup updates the per-run source-cache and destination Btrfs metadata indexes, uses only Btrfs subvolume deletes plus empty-directory `rmdir`, and still refuses any source cleanup below `source.snapshot_root`.
- Updated README.md, COMMENTED_CODE_MAP.md, CONFIG_AND_CLI_AUDIT.md, VERSIONING.md, package version metadata, and the packaged config example.

## 0.1.37

- Fixed retention source send-cache parent cleanup so it no longer trusts the run-start cache index as the final emptiness check before deleting `<source.cache_root>/<snapshot>`.
- Before deleting a timestamp cache parent, prune now re-reads live Btrfs child subvolumes below that parent, deletes any remaining app-owned children deepest-first, and only then deletes the parent. This handles cases where tracked `@` and `@home` looked gone but the parent still contained live or stale children.
- Source cache parent deletion may now remove only empty ordinary child directories with non-sudo `rmdir` before retrying `btrfs subvolume delete`, while still never using source-side sudo `rm`, `find`, `chmod`, or `chown` and still protecting `source.snapshot_root`.
- Updated README.md, COMMENTED_CODE_MAP.md, VERSIONING.md, package version metadata, and the packaged config example.

## 0.1.36

- Restored the stderr-control path for expected negative Btrfs probes. Optional `btrfs subvolume show` checks now stay out of terminal `COMMAND STDERR` and `.err` when they are only checking whether a not-yet-created cache path such as `send-cache/<snapshot>/@home` already exists.
- Kept required metadata checks and real command failures noisy: they still print and log stderr and still raise normally.
- Updated README.md, COMMENTED_CODE_MAP.md, CONFIG_AND_CLI_AUDIT.md, VERSIONING.md, package version metadata, and the packaged config example.

## 0.1.35

- Fixed `destroy-leftovers --delete-source` so an existing Btrfs `source.cache_root` is detected with configured sudo+Btrfs metadata before falling back to source-shell `test -e` visibility.
- This prevents the source send-cache root from being reported as already missing when the source user cannot normally traverse the cache path but the configured passwordless Btrfs command can access the app-owned cache subvolume.
- Kept the narrow source sudo model intact: source cleanup still does not require sudo `test`, `rm`, `find`, `chmod`, or `chown`, and `source.snapshot_root` remains protected.
- Updated README.md, COMMENTED_CODE_MAP.md, CONFIG_AND_CLI_AUDIT.md, and the config example comments to describe the current destroy-leftovers source-cache behavior.

## 0.1.34

- Fixed read-only source-cache reuse before creation. When a writable Timeshift subvolume needs a send-cache snapshot, the app now refreshes and validates the exact `<cache_root>/<snapshot>/<subvolume>` path before attempting `btrfs subvolume snapshot -r`.
- Existing cache snapshots are reused only when Btrfs proves they are real read-only subvolumes and, when available, their Parent UUID matches the original Timeshift source subvolume UUID.
- This prevents failed recreate attempts after interrupted runs, state recovery, or switching between SSH and local mode when valid read-only cache snapshots already exist.
- Updated README.md, COMMENTED_CODE_MAP.md, and the config example comments to document current cache reuse behavior.

## 0.1.33

- Enabled normal split run logging for `destroy-leftovers`, `clear-state`, and `delete-lock` so these guarded maintenance/destructive commands produce `.log`, `.err`, `.btrfs`, `.mbuffer`, and `.succes` files when `log_dir` is configured.
- Added a survivor log-directory fallback for `destroy-leftovers`: when the configured `log_dir` is inside a selected delete target, the command uses an outside fallback log directory so the cleanup logs are not deleted with the target.
- Added progress output before each destroy target and during source/destination discovery/deletion so long destination cleanup no longer appears frozen after the source side finishes.
- Destroy cleanup probe/delete commands are now recorded in the active `.log`/`.err` files for easier SSH and destination cleanup debugging.

## 0.1.32

- Improved `destroy-leftovers` cleanup for nested source send-cache subvolumes.
- Source send-cache deletion now recursively discovers child Btrfs subvolumes by walking each subvolume with `btrfs subvolume list -o`, so child payload subvolumes such as `send-cache/<snapshot>/@` are deleted before their parent container subvolume.
- Empty ordinary directory entries left behind by deleted child subvolumes are removed before retrying/deleting the parent subvolume.
- The source-side cleanup still uses only the configured source user plus passwordless `btrfs`; it does not require sudo access to `rm`, `find`, `chmod`, or `chown`.
- `source.snapshot_root` remains globally protected and is never deleted, pruned, destroyed, or cleaned.

## 0.1.31

- Added a bulk source snapshot-root Btrfs index so Timeshift discovery can reuse in-memory metadata instead of running one source-side `btrfs subvolume show` per snapshot/subvolume.
- Changed source cache and snapshot-root indexing to collect UUID/parent/received-UUID data with bulk `btrfs subvolume list -u -q -R -o <root>` and read-only status with bulk `btrfs subvolume list -r -o <root>`.
- In SSH mode, each source root index is built inside one SSH session, reducing repeated SSH calls while keeping the same UUID safety checks.
- Send-path selection, parent verification, sync-floor checks, state recovery, and Timeshift discovery now prefer the bulk source snapshot/cache indexes and fall back to targeted `subvolume show` only when needed.
- Updated README.md and COMMENTED_CODE_MAP.md to describe the current index behavior without adding previous-version explanations there.

## 0.1.30

- Added a pre-manual sync viability check so automatic Timeshift on-demand snapshot creation happens only after the app proves the current source/destination chain can continue.
- Existing destinations now require both a UUID-confirmed sync floor and a usable incremental parent for the next pending transfer, or a usable parent for the future manual snapshot when nothing is pending, before `timeshift --create` is run.
- If parent/state/source-cache validation fails, sync now stops before creating another source snapshot.
- Updated README.md, COMMENTED_CODE_MAP.md, CONFIG_AND_CLI_AUDIT.md, and the config example comments to document the current manual snapshot ordering.

## 0.1.29

- Added guarded `clear-state` command to remove only the configured `state_file`. It defaults to dry-run and real removal requires `--run`, `--i-understand-this-clears-state`, app lock acquisition, and two typed confirmations.
- Added guarded `delete-lock` command to remove only the configured `lock_file` when `flock` proves no running process currently holds it. It defaults to dry-run and real removal requires `--run`, `--i-understand-this-deletes-lock`, and two typed confirmations.
- Added `maintenance.py` so state/lock file removal has explicit path validation and does not delete source snapshots, source cache snapshots, destination snapshots, or Timeshift-owned paths.
- Updated README.md, COMMENTED_CODE_MAP.md, and the config example comments to document the guarded maintenance commands.

## 0.1.28

- Added conservative state recovery when `state.json` is missing or empty but destination snapshots already exist.
- Existing destination subvolumes are adopted into rebuilt state only when their `Received UUID` exactly matches the UUID of the matching source Timeshift subvolume or an existing read-only source-cache subvolume.
- The recovered state lets sync continue from the newest fully adopted matching snapshot instead of forcing a new full chain.
- Added a safety guard so, when state was missing/empty at run start, an existing destination subvolume that cannot be adopted is not deleted as an incomplete receive.

## 0.1.27

- Added source-cache UUID adoption for incremental parent selection.
- Existing read-only cache snapshots below `source.cache_root` can now be used as parent candidates when their UUID exactly matches the destination parent's `Received UUID`.
- This supports switching from SSH pull to local sync on the same source when the earlier SSH pull already created valid read-only cache snapshots.
- Kept the safety rule that missing cache parents are never recreated for parent matching, because recreated Btrfs snapshots get new UUIDs.

## 0.1.26 - source snapshot-root SSH preflight order and ordinary-directory fallback

- Changed source snapshot-root preflight to run a second Btrfs-only fallback check with `btrfs filesystem df <snapshot_root>` when `btrfs subvolume list -o <snapshot_root>` does not accept an ordinary Timeshift directory. This keeps ordinary Timeshift-owned snapshot roots valid.
- Clarified in code/config/docs that the source snapshot-root check runs on the selected source endpoint: through SSH/sshpass in SSH mode and locally in local mode.
- Changed source preflight ordering so `source.cache_root` is not created or modified when `source.snapshot_root` fails verification. This avoids creating send-cache storage on the wrong source/mount when the Timeshift-owned snapshot root is missing or misconfigured.
- Kept the global safety invariant that `source.snapshot_root` and everything below it are never created, pruned, deleted, destroyed, or cleaned by the app.

This build is version `0.1.26`.

# Versioning

## 0.1.25 - protect Timeshift snapshot root and improve remote snapshot-root diagnostics

- Added explicit source-delete safety guards so prune, source send-cache cleanup, and destroy-leftovers refuse any source path that is `source.snapshot_root` or below it.
- Updated `source.snapshot_root` comments in code and config example: Timeshift owns this path and the app must never create, prune, delete, destroy, or clean it.
- Changed `source.snapshot_root` preflight to try the configured `sudo btrfs subvolume list -o <snapshot_root>` check first, then use shell visibility checks only for diagnostics. This gives clearer SSH-mode errors when the remote path is wrong, not mounted, or not accessible through sudo btrfs.
- Updated README.md and COMMENTED_CODE_MAP.md to describe the current protected-root safety invariant.

This build is version `0.1.25`.

## 0.1.24 - separate source cache root validation

- Added config/preflight validation that `source.cache_root` must be outside `source.snapshot_root`.
- Clarified the failure case where `source.snapshot_root` is accepted as a normal Timeshift-owned directory, but `source.cache_root` is incorrectly pointed at the same snapshots directory.
- Kept `source.cache_root` as app-owned send-cache storage that is created as a Btrfs subvolume when missing and cache creation is enabled.
- Updated README.md, COMMENTED_CODE_MAP.md, VERSIONING.md, and the example config to describe the current cache-root rule.

This build is version `0.1.24`.

## 0.1.23 - Timeshift-owned snapshot root preflight

- Changed source snapshot-root preflight so `source.snapshot_root` is never created by the app.
- `source.snapshot_root` may be an ordinary directory on a Btrfs filesystem, because Timeshift creates snapshot subvolumes inside that directory.
- Missing, non-directory, or non-Btrfs-accessible `source.snapshot_root` is now a hard preflight error in both dry-run and real-run mode.
- Updated README.md, COMMENTED_CODE_MAP.md, and the example config to describe the current snapshot-root rule without adding old-version notes there.

This build is version `0.1.23`.

## 0.1.22 - early lock path and Btrfs-first helper creation

- Changed real-run ordering so the lock file parent is prepared before source roots, destination helper folders, state paths, logs, or sync/prune work are checked.
- If the lock path chain includes `destination.target_root`, that component is created by the strict target-root rule and must become a Btrfs subvolume.
- Missing lock/helper folders now try `btrfs subvolume create` first, because the app works on Btrfs storage, then fall back to normal `mkdir` when Btrfs creation is not possible.
- Updated README.md and COMMENTED_CODE_MAP.md to describe the current lock-path and helper-folder order without old-version explanations.

This build is version `0.1.22`.

## 0.1.21 - lock/helper folder creation safety

- Added real-run lock path preflight before opening the lock file.
- The lock-file parent is created if missing and may be either an ordinary directory or a Btrfs subvolume.
- Destination helper folders accept existing directories or Btrfs subvolumes.
- `FileLock` no longer creates parent directories itself, preventing accidental normal-directory creation of `destination.target_root`.
- File logging no longer creates missing parent directories before preflight; if the log directory is not ready, the command continues with terminal-only logging.
- Updated README.md and COMMENTED_CODE_MAP.md to describe the current helper-folder behavior.

This build is version `0.1.21`.

## 0.1.20 - require destination target root subvolume

- Fixed destination preflight so an existing `destination.target_root` must pass `btrfs subvolume show`.
- A plain directory inside a Btrfs filesystem is now a hard preflight error instead of being reported as OK by the broader Btrfs-accessibility check.
- Kept missing-target behavior from the previous release: when allowed, the app creates the missing target root with `btrfs subvolume create <target_root>` and verifies it before continuing.
- Updated README, commented code map, and config example comments to describe the current target-root rule.

This build is version `0.1.20`.

## 0.1.19 - release zip directory permissions fix

- Rebuilt the release zip with correct Unix directory permissions so package folders extract as usable directories.
- Ensured `timeshift_btrfs_sync/data/` is a real directory containing `config.example.toml`.
- Kept only one `config.example.toml`, inside the package data folder.
- Updated README and commented code map to describe the current package-data layout without adding old-version details there.

This build is version `0.1.19`.

## 0.1.18 - destination target root subvolume creation

- Changed real-run preflight so a missing `destination.target_root` is created with `btrfs subvolume create <target_root>` instead of Python `mkdir`.
- Preflight now verifies that the destination target-root parent already exists and is Btrfs-accessible before creating the exact configured target root.
- Existing destination target roots are not converted; existing directory-based backup roots keep working as long as they are Btrfs-accessible.
- Updated README, commented code map, and config example comments to describe the current target-root behavior.

This build is version `0.1.18`.

## 0.1.17 - documentation cleanup

- Cleaned `README.md` so it documents the app as it currently works instead of listing release-by-release changes.
- Cleaned `COMMENTED_CODE_MAP.md` so it focuses on current CLI commands, shell command families, functions, and classes, with explanations of what each does and why.
- Kept historical version notes in this `VERSIONING.md` file instead of duplicating them in the README or code map.

This build is version `0.1.17`.

### 0.1.16

- Added `*.toml` to `.gitignore` so local TOML configuration files are ignored by default.
- Kept the example-config exception after the ignore rule so example configuration files can still be tracked.
- Kept release packaging free of `__pycache__`, `.pyc`, and `.pyo` files.

### 0.1.15

- Real-run sync path preflight now attempts to create missing configured roots before Timeshift on-demand creation or send/receive work starts.
- `source.snapshot_root` is created as a normal source-side directory only after its parent is proven Btrfs-accessible.
- `source.cache_root` is created during preflight as a Btrfs subvolume when missing and `source.create_readonly_cache = true`; existing ordinary directories are still refused.
- `destination.target_root` is created locally during preflight when missing and `destination.create_target_root = true`, then verified with Btrfs before sync continues.
- Preflight hard errors now name the exact configured path that could not be verified or created.
- Included the requested `.gitignore` exactly as supplied and kept release packaging free of `__pycache__`, `.pyc`, and `.pyo` files.
- Updated README, commented code map, versioning, and config example comments.

### 0.1.14

- Added lazy source cache-root creation for writable Timeshift snapshots that need a read-only send copy.
- `source.cache_root` is now created as a Btrfs subvolume with `btrfs subvolume create <cache_root>` when it is missing and cache is actually needed.
- Existing `source.cache_root` paths must already be Btrfs subvolumes; ordinary directories are refused so app-owned send-cache cleanup remains safe.
- Preflight now accepts a missing `source.cache_root` only when `create_readonly_cache = true` and the cache-root parent is Btrfs-accessible.
- The same logic works in both `source.mode = "ssh"` and `source.mode = "local"` through `SourceRunner`.
- Updated README, commented code map, and the example config comments for lazy cache-root subvolume creation.

### 0.1.13

- Rebuilt the release archive without Python cache folders or compiled cache files.
- Confirmed no `__pycache__`, `.pyc`, or `.pyo` entries are present in the zip.
- Kept exactly one canonical example config at `timeshift_btrfs_sync/data/config.example.toml`.

### 0.1.12

- Removed the extra top-level `config.example.toml` from the source archive.
- Kept exactly one canonical example config at `timeshift_btrfs_sync/data/config.example.toml`.
- Kept `ts-btrfs init-config` using the packaged data-folder template.
- Removed Python `__pycache__` files from the release archive.

### 0.1.11

- Added a top-level `config.example.toml` copy to the source archive so the complete example config is visible without looking inside package data.
- Kept `timeshift_btrfs_sync/data/config.example.toml` as the packaged template used by `ts-btrfs init-config`.
- Confirmed both config examples include `source.mode = "ssh"` with comments for `ssh` and `local` modes.

### 0.1.10

- Added `source.mode = "local"` so the same sync/prune/destroy workflow can use Timeshift Btrfs snapshots on the machine running `ts-btrfs` without wrapping source commands in SSH.
- Added `source.py` with a shared `SourceRunner` abstraction. Existing SSH pull behavior now uses `SourceRunner(mode="ssh")`; local sync uses `SourceRunner(mode="local")` and runs source-side shell commands locally.
- Generalized Timeshift listing/creation, Btrfs source metadata, source send-cache indexing/cleanup, preflight source checks, pruning, destroy-leftovers, and the `btrfs send` side of the pipeline to use the shared source runner.
- Added `test-source` as the primary source connectivity/sudo check. Existing `test-ssh` remains as a backward-compatible alias and skips SSH checks in local mode.
- Updated README, the commented code map, and the example config to document SSH and local source modes.

### 0.1.9

- Removed source-side `sudo find`, `sudo test`, and `sudo rm` usage from `destroy-leftovers`.
- Source-side destroy cleanup now uses passwordless `sudo btrfs` for Btrfs subvolume deletion/listing only.
- Empty stale ordinary directories left after source subvolume deletion are removed with normal non-sudo `rmdir` as a best-effort cleanup. If permissions prevent that, the app reports the remaining directory instead of requesting broader sudo.
- This preserves the intended least-privilege source sudoers model where the source user only needs passwordless `timeshift` and `btrfs`.

### 0.1.7

- Added a sync path preflight before automatic/manual on-demand creation and before send/receive work.
- The preflight checks `source.snapshot_root`, configured `source.cache_root`, and `destination.target_root` up front, so a missing/mis-mounted path fails before a fresh on-demand Timeshift snapshot is created.
- The source checks are batched into one SSH call and use the configured `sudo btrfs subvolume list -o <path>` access instead of generic sudo filesystem permissions.
- `create-manual` now runs the same path preflight before creating a standalone Timeshift on-demand snapshot.

### 0.1.6

- On-demand retry-order guarantee: if an app-created on-demand snapshot itself failed or was only partially received on the destination, sync deletes only that incomplete destination path and retries it when the existing oldest-to-newest queue reaches that snapshot/subvolume.
- Added explicit output for incomplete destination cleanup showing the retry policy and order policy, so failed on-demand snapshots are visibly not jumped ahead or handled out of order.
- Added code comments around the sorted snapshot/subvolume loop documenting that incomplete destination cleanup is intentionally done inside the normal order loop.

### 0.1.5

- Fresh on-demand creation after interrupted runs: if an older app-created on-demand snapshot is still pending, the next normal `sync` keeps that pending snapshot in the oldest-to-newest queue but still creates a new on-demand snapshot for the current run.
- The pending snapshot notice now explains that older failed-run snapshots remain queued and that a fresh snapshot is still created because the old one may no longer represent the current system state.
- Interrupted/partial destination receives are still deleted and retried when their snapshot/subvolume is reached in the normal send order.

### 0.1.4

- Interrupted-run retry safety: if an earlier sync already created an app on-demand Timeshift snapshot but did not finish syncing it, the next normal `sync` skips creating a duplicate manual snapshot and processes the existing pending app-created snapshot in normal oldest-to-newest order.
- Incomplete destination receives are still cleaned before retry, and the destination per-run index is invalidated for the deleted path so later parent checks do not use stale metadata.
- If `state.json` says a snapshot is fully synced but one of the expected destination paths is missing, sync no longer skips the whole snapshot; it retries the missing path(s).

### 0.1.3

- Added normalized payload match statistics to `destroy-leftovers --delete-both`.
- The summary now compares real source-side send payload against destination received payload by snapshot/subvolume name, so raw Btrfs helper/container subvolume counts no longer look like retention mismatches.
- The comparison understands v0.1.2 direct read-only Timeshift sends: protected Timeshift original send paths from state.json are counted as source-side payload, but are still never deleted by `destroy-leftovers` or prune.

### 0.1.2

- Added explicit read-only Timeshift direct-send support and state labeling.
- If an original Timeshift snapshot child is already read-only, sync sends directly from the original Timeshift path instead of creating an app cache copy.
- State now records `send_path_kind`, `send_path_owned_by_app`, and `send_path_prune_protected` for each subvolume.
- Prune safety was tightened so only app-owned source-cache paths below `source.cache_root` are deleted. Direct Timeshift original send paths are listed as protected and are never removed by prune.

## Changelog

### 0.1.1

- `ssh.control_master = true` now creates a missing `ssh.control_path` parent directory automatically with owner-only permissions (`0700`), including missing intermediate directories when the user running the app is allowed to create it.
- Existing ControlPath parent directories are still validated and refused if they are not owned by the app user, are group/other accessible, or are inside shared temporary storage such as `/tmp`, `/var/tmp`, or `/dev/shm`.
- Updated README and config comments to explain automatic private directory creation and the remaining socket-reuse risk.

### 0.1.0

- Added safety validation and documentation for SSH ControlMaster/ControlPath connection reuse.
- `ssh.control_master = true` requires an explicit absolute `ssh.control_path` whose parent directory is owned by the user running the app, is private (`chmod 0700` style), and is not inside shared temporary storage such as `/tmp`, `/var/tmp`, or `/dev/shm`.
- Documented what OpenSSH multiplexing is, how it speeds up passphrase-protected keys, and why the local control socket must be protected.

### 0.0.99

- Added `remote_index.py`, a per-run Btrfs subvolume index used to cache source send-cache and destination path/UUID lookups.
- Sync now builds a source send-cache index and destination index once per run, then reuses those dictionaries for parent/floor validation where safe.
- Source cache index entries are refreshed after cache snapshot creation; destination index entries are refreshed after each receive; prune removes deleted cache paths from the index.
- Prune source send-cache cleanup now uses the per-run source cache index instead of repeatedly listing cache parents/children.
- `destroy-leftovers` now builds the remote source cache tree in one SSH command and deletes remote source cache subvolumes in one batched SSH command.
- Added optional `[ssh]` `control_master`, `control_persist`, and `control_path` settings for OpenSSH connection reuse, useful with password-protected keys and high KDF iterations.

### 0.0.98

- Changed `destroy-leftovers --delete-source` so it never deletes `source.snapshot_root`, because that path belongs to Timeshift and contains the user's original OS snapshots.
- `--delete-source` now only deletes app-created source send-cache paths under `source.cache_root`; `--delete-both` deletes source send-cache plus destination target.

### 0.0.97

- Fixed destroy-leftovers recursive Btrfs cleanup so nested source send-cache subvolumes are discovered before deleting timestamp parent subvolumes.
- After each subvolume delete, removes stale ordinary directories that can be left behind before deleting parent subvolumes.

### 0.0.96

- Added `destroy-leftovers`, a destructive retirement cleanup command for deleting configured cleanup leftovers and/or destination target root after the app is no longer used. Superseded by 0.0.98: source.snapshot_root is no longer a destroy target.
- Real deletion requires `--run`, `--i-understand-this-destroys-data`, an explicit target flag, and two typed confirmations.

### 0.0.95

- Version-only renumber from 0.9.5 to match the old release-count scheme where 0.9.5 corresponds to release 95.
- No code behavior changed.

### 0.9.5

- Existing-destination sync can now use a saved source send-cache parent even when Timeshift has already pruned the original parent snapshot.
- This lets a delayed backup continue incrementally from the newest UUID-confirmed destination/source-cache parent, then prune normally afterward.

### 0.9.4

- Fresh/full sync now preselects only source snapshots that the active retention rules would keep, then sends that reduced set oldest-to-newest.
- This avoids wasting time and disk wear sending old snapshots that post-sync prune would immediately delete. Existing non-empty destination sync behavior is unchanged.

### 0.9.3

- Moved per-snapshot prune state result into its own unindented `State` section with a blank line before it.
- Output-only readability change; prune/delete logic is unchanged.

### 0.9.2

- Readability-only prune output change: each retention delete item now separates destination deletion from source send-cache deletion with clear section headers.

### 0.9.1

- Version-only bump from 0.8.11.

### 0.8.11

- Reworked prune deletion as one coordinated per-snapshot item: destination subvolumes and source send-cache are both attempted before state is removed.
- Prune now keeps the state entry unless destination and source send-cache are both confirmed gone or already absent, while still attempting the available side when the other side is missing/unavailable.
- Retention delete plans now show both destination subvolume paths and source send-cache paths for each candidate.

### 0.8.10

- Fixed source send-cache prune cleanup for nested `@` and `@home` cache subvolumes. The app now lists the timestamp cache parent before deciding child cache subvolumes are missing.
- Renamed prune output from `SOURCE CACHE RETENTION CLEANUP` to `SOURCE SEND-CACHE RETENTION CLEANUP` to avoid confusion with original Timeshift snapshots.
- Prints a retention delete summary to the normal run log as well as the success summary.

### 0.8.9

- Made retention deletion idempotent: state entries are removed only after destination and source cache cleanup are confirmed gone or already absent.
- Kept state entries when source cache cleanup cannot be verified so a later prune can retry safely.

### 0.8.8

- Fixed retention-based source cache cleanup so it also checks the timestamp cache parent. If `@`/`@home` are already missing but the empty parent still exists, prune now deletes the parent instead of stopping after child skips.
- Source cache cleanup still only deletes app-created cache paths under `source.cache_root`; it does not delete original Timeshift source snapshots.

### 0.8.7

- Fixed first-run multi-subvolume seeding: when the destination was empty at sync start, remaining first-chain subvolumes may still full-send after the first subvolume makes the destination non-empty.
- Preserved the strict mixed-chain guard for normal non-empty destinations.

### 0.8.6

- Fixed retention-based source cache cleanup to pre-check which cache subvolumes still exist before deleting.
- Missing source cache paths are now skipped cleanly instead of producing noisy Btrfs delete/list errors.
- Removed duplicate stderr printing from cache cleanup failures; command stderr is already emitted by the command runner.

### 0.8.5

- Changed source cache cleanup to retention-based cleanup. `sync` now keeps every read-only cache snapshot it creates, and `prune` deletes matching source cache snapshots only for destination snapshots selected by the same retention delete plan.
- This preserves more common Btrfs UUID ground when short-lived snapshots are removed later.

### 0.8.4

- Refreshed `COMMENTED_CODE_MAP.md` to document only current commands, classes, and functions, and to add concise notes explaining safety-driven code paths.

### 0.8.3

- Added light CLI parser helpers for subparser creation, shared `--config`, shared run-mode flags, and shared delete-confirmation flags.
- Preserved command-specific help output and command flag visibility.

### 0.8.2

- Added shared `tags_text()` display helper and removed duplicate `_tags_text()` formatting helpers from sync/prune paths.

### 0.8.1

- Refactored safer config parsing patterns with shared table, optional-string, positive-integer, stripped-string, boolean, and integer helpers.
- Kept password/password_file pair validation explicit for a later, more focused refactor.

### 0.8.0

- Version-only bump from 0.7.10.

### 0.7.10

- Refactored pipeline stream reader setup into one compact stream-routing table.
- Preserved successful btrfs/mbuffer stderr routing to `.btrfs`/`.mbuffer` without polluting `.err`.

### 0.7.9

- Shared state metadata refresh/report/save logic between sync and prune without changing send/receive, retention, or parent UUID behavior.

### 0.7.3

- Consolidated source cache listing helpers around `remote_list_child_subvolumes`, `remote_cache_contains`, and cache child display formatting.
- Removed older overlapping cache list parsing/existence helpers while keeping the same cache parent cleanup behavior.

### 0.7.2

- Consolidated parent/source UUID matching into one shared helper, `match_source_path_to_destination_received_uuid` internally, so parent selection and sync-floor validation use the same Btrfs identity rule.
- Removed older overlapping helper code for parent/source UUID checks while keeping the same strict behavior: source path UUID must match destination received UUID or trusted state UUID history before it can be used.

### 0.6.11

- Reused one parsed Timeshift source snapshot index per sync stage.
- Manual snapshot creation still re-reads `timeshift --list` after creating a new snapshot, but metadata refresh, manual identity checks, sync-floor checks, parent selection, and the sync loop now share the same source index for that stage.

### 0.6.8

- Fixed successful transfer pipeline stderr handling. Successful `btrfs send` status lines such as `At subvol ...` and mbuffer progress no longer make `.err` non-empty.
- Transfer stderr is now buffered and copied to `.err` only if the send/mbuffer/receive pipeline fails.
- Btrfs transfer status is still written to `.btrfs`, and mbuffer progress is still written to `.mbuffer`.

### 0.6.7

- Added a separate `.succes` run log for readable sync and retention statistics.
- Sync summaries and retention delete plans are written to `.succes` and still shown in the terminal, instead of being mixed into the normal `.log` file.
- Email notifications use non-empty `.succes` text as the plain-text message body when present.
- Email log attachments are conditional and include only non-empty `.log`, `.err`, `.btrfs`, `.mbuffer`, and `.succes` files.
- Renamed the Btrfs verbose-output log suffix from `.btrfs-out` to `.btrfs`.

### 0.6.5

- Removed legacy config-option compatibility checks from the runtime config loader.
- Unknown removed config keys are no longer handled by special warning/error branches. The loader now only parses the active configuration needed by current functionality.
- Removed stale documentation text describing those old compatibility warnings.

### 0.6.4

- Destination retention uses only native Timeshift tags: H, D, W, M, B, and O.
- Non-native retention categories are not part of the active config model, examples, embedded `init-config` output, docs, or retention tag map.

### 0.6.3

- Added strict incremental parent source-path selection. For an existing destination parent, the app checks the saved state `send_path` first and requires its current source UUID to match the destination `received_uuid`.
- If the saved `send_path` is missing or does not match, the app tries the original Timeshift source path and only uses it if its UUID matches the destination `received_uuid`.
- Parent selection never creates a replacement cache snapshot. A recreated cache snapshot has a new UUID and cannot be a valid parent for an already received destination snapshot.

### 0.6.2

- Refreshed mutable Timeshift metadata in `state.json` from the latest `timeshift --list` during sync. Existing synced snapshots update `tags`, `comment`, `created`, and top-level target-relative `path` without re-sending data or changing UUID/parent/send identity fields.
- Improved Timeshift tag parsing so separated tag tokens such as `B H D W M` are recognized as tags instead of partly becoming the comment.

### 0.6.1

- Clarified and guarded the automatic manual/on-demand snapshot flow: the app may create a source-side Timeshift snapshot before syncing, but it never sends that snapshot directly or as a special priority target.
- After creating a manual snapshot, sync re-reads `timeshift --list`, reports newly detected snapshot names, and sends them only through the normal oldest-to-newest sync loop.

### 0.6.0

- Version-only bump.

## 0.1.50

- Removed runtime modules, command aliases, helper functions, method branches, parameters, imports, persistent fields, tests, and documentation that are not used by the current workflows.
- Removed support for non-current configuration names and state documents.
- The current configuration loader rejects unknown keys and uses `source.cleanup_cache_during_prune` as the only source-cache prune setting.
- The current state format is schema version 3. It accepts only root-relative managed paths, explicit path ownership kinds, and the UUID fields used by current parent and recovery checks.
- Removed the `test-ssh` command alias; `test-source` is the source endpoint check for both SSH and local modes.
- Removed the compatibility facade modules and the unused alternate Btrfs descendant-list mode.
- Rebuilt README, installation instructions, interface audit, config comments, tests, and code map so they describe only current behavior and implementation reasons.
- Sync, retention, recovery, cache, transfer, notification, logging, and destructive safety behavior remain active through the shared operation layers.

## 0.1.51

- Restored `source.cleanup_superseded_cache` as the current source-cache retention option.
- `sync`, standalone `prune`, and prune-after-sync now load and apply the setting for both local and SSH source modes.
- When enabled, retention removes an app-owned source cache date only after the matching destination date is confirmed deleted; when disabled, the cache is retained.
- Removed the accidental `cleanup_cache_during_prune` rename introduced in 0.1.50.
- Added local and SSH regression coverage for config loading, sync startup, and retention endpoint selection.

## 0.1.52

- Fixed `destroy-leftovers --delete-both` crashing after both source and destination trees were successfully deleted.
- The post-deletion payload comparison now reads the current `source.subvolumes` configuration instead of the removed `SourceConfig.tree` refactor object.
- Added complete local-source and SSH-source `--delete-both` regression tests that execute source/destination payload matching and final summary reporting after both roots are verified absent.

## 0.1.53

- Added the guarded `restore` command for importing one destination backup into the configured source Timeshift repository in Timeshift's native Btrfs layout.
- Restore reads `<destination.target_root>/snapshots/<date>` locally, requires the backup date container and configured payloads to be valid Btrfs subvolumes, requires read-only send payloads, and validates that the saved `info.json` is a JSON object whose `date` matches the selected timestamp.
- Added one shared local/SSH restore implementation. The backup side always performs a local full `btrfs send`; the configured source endpoint performs local or SSH `btrfs receive` using the existing endpoint, stream, sudo, logging, and Btrfs operation layers.
- Restored Timeshift layout uses an ordinary `<source.snapshot_root>/<date>` directory containing writable configured payload subvolumes such as `@` and `@home` plus the exact original regular `info.json` file.
- Added hidden ordinary staging below `source.snapshot_root`, exact UUID/Received UUID validation, writable-property validation, atomic staging-directory rename, refusal to overwrite an existing Timeshift date, and a final `timeshift --list` visibility check.
- Restore always uses full sends and does not depend on an incremental parent or modify backup state/retention data.
- Added failure cleanup that probes and deletes only Btrfs payload paths attempted by the current restore, removes only exact staging metadata files, and removes the staging directory only when empty. No recursive ordinary deletion is used.
- Added restore-specific privilege diagnostics. Normal backup remains limited to source Btrfs/Timeshift privilege; restore additionally requires source-side permission for `mkdir`, `tee`, `chmod`, `mv`, exact `rm`, and `rmdir`. Local root execution is the simplest setup, while SSH restore requires those permissions on the remote source.
- Added `--dry-run`, `--run`, required `--snapshot`, and `--i-understand-this-modifies-timeshift` restore flags plus typed real-run confirmations and shared application locking.
- Added local and SSH restore regression coverage, dry-run/overwrite/metadata validation tests, and partial-receive staging cleanup coverage.

## 0.1.54

- Extended `restore` with mutually exclusive `--snapshot <date>` and `--all` selections. Single restore remains one full import; `--all` restores every backup newer than the newest UUID-confirmed common Timeshift snapshot.
- Added common-parent safety validation for every configured payload. A date is common only when the live Timeshift UUID matches `original_source_uuid` and the backup Received UUID matches `send_source_uuid` in the same current `state.json` entry; matching timestamp names alone are not trusted.
- Added a prominent cross-OS warning when no common parent can be proven. Real no-common restoration is refused unless `--allow-no-common-parent` is supplied and the user types `RESTORE ALL WITHOUT COMMON PARENT` plus the configured job name.
- Added one shared local/SSH restore-chain implementation. It full-receives the common backup as a hidden read-only seed when a common parent exists, or full-receives the oldest backup when none exists, then sends every later backup incrementally oldest-to-newest with the previous backup as `btrfs send -p` parent.
- Added stream-identity validation that uses a backup payload's Received UUID when present, otherwise its normal UUID. This preserves the UUID identity used when a previously received backup is sent again.
- Added writable visible Timeshift snapshots as Btrfs CoW snapshots of the hidden received chain. Their timestamp containers remain ordinary directories with exact saved `info.json` files, while the hidden chain remains read-only until every incremental receive and Timeshift visibility check succeeds.
- Added exact hidden-chain cleanup after successful restore and conservative rollback of only artifacts created by the current attempt. Fully committed Timeshift dates are left in place if a later Timeshift-list or hidden-cleanup check needs manual inspection.
- Added local and SSH regression coverage for common-parent chain restore, no-common full-plus-incremental restore, exact incremental parent paths, current-state identity matching, CLI selection/override rules, stream UUID identity, overwrite refusal, and no-work behavior when the newest backup is already common.

## 0.1.55

- Added a mandatory restored-snapshot retention warning to both single-snapshot and complete-chain restore plans. The terminal explains that exact original `info.json` metadata preserves H/D/W/M tags and that normal Timeshift scheduled retention may later delete an old restored snapshot outside configured keep counts.
- Every real local or SSH restore now requires the exact sentence `I UNDERSTAND TIMESHIFT MAY DELETE RESTORED SNAPSHOTS` before any Btrfs receive starts. This acknowledgement is additional to the existing single-snapshot, common-parent-chain, or no-common-parent confirmations.
- Added regression coverage for warning output, failed acknowledgement blocking all streaming, and successful local/SSH single and chain restores using the shared confirmation path.
- Updated current restore documentation, installation guidance, CLI help, interface audit, config comments, code map, and package version metadata.


## 0.1.56

- Changed the mandatory restore retention acknowledgement to `I UNDERSTAND TIMESHIFT MAY DELETE RESTORED SNAPSHOTS OR OLDER THAN RESTORED SNAPSHOTS`.
- Expanded the terminal warning to explain that restoring tagged H/D/W/M snapshots can cause Timeshift retention to delete either a restored snapshot or an existing tagged snapshot older than the restored snapshot when configured keep counts are exceeded.
- Applied the same shared confirmation to single-snapshot and complete-chain restores in local and SSH modes, with regression coverage for the exact sentence and warning text.
- Updated current restore documentation, CLI help, config comments, interface audit, and package version metadata.

## 0.1.57

- Fixed subsequent sync runs falsely classifying all existing destination date subvolumes as ordinary directories when the destination is mounted from a Btrfs subvolume and bulk list paths begin at `snapshots/...`.
- Destination inventory is now rooted at `<target_root>/snapshots`, matching the managed receive tree and allowing date and payload paths to map correctly across mounted-subvolume prefixes.
- Layout validation treats the bulk index as an optimization: every direct date directory missed by the bulk scan is exact-probed with `btrfs subvolume show` before rejection. Real Btrfs date subvolumes are added to the current index; actual ordinary directories remain a hard error.
- `destination.snapshots` is now strictly Btrfs-only. Missing paths are created and verified as Btrfs subvolumes, and Btrfs creation failure no longer falls back to `mkdir`. State, lock, and optional log helper paths retain their current flexible behavior.
- Full and incremental transfers continue to use the same `_ensure_destination_snapshot_subvolume` path, which creates each date with `btrfs subvolume create` and verifies it before receive.
- Added regression coverage for mounted destination path mapping, snapshots-root inventory selection, exact-probe recovery, ordinary-directory refusal, disabled mkdir fallback, and exact Btrfs create command construction.


## 0.1.58

- Fixed `restore --all` and single-snapshot restore rejecting genuine Timeshift `info.json` files that do not contain a `date` property.
- Removed the non-Timeshift metadata requirement introduced with restore. The timestamp directory name is the snapshot identity; the original `info.json` is now validated only as a readable UTF-8 JSON object and is preserved byte-for-byte.
- Added regression coverage using realistic Timeshift Btrfs control metadata (`sys-uuid`, `sys-distro`, `app-version`, `file_count`, `tags`, `comments`, `live`, and `type`) with no `date` key, including multi-snapshot discovery used by `restore --all`.
- Updated current restore documentation and the code map to describe the directory timestamp as the identity source rather than a control-file date field.

## 0.1.59

- Added stable Timeshift `info.json` OS-identity validation for restore. The backup chain must use one consistent `sys-uuid` and Btrfs `type`, and the identity is compared with current source Timeshift control files before restore.
- Snapshot-specific metadata is intentionally excluded from OS matching: H/D/W/M/O/B tags, comments, creation time, file counts, Timeshift app version, live status, and Btrfs statistics. `sys-distro` is displayed as diagnostic context but is not a hard match so an in-place distribution upgrade does not create a false cross-OS failure.
- Added `--allow-os-identity-mismatch` for an explicitly accepted restore when no current `info.json` identity matches. Real execution additionally requires the exact sentence `I UNDERSTAND THIS BACKUP MAY BELONG TO ANOTHER OS`.
- Strengthened common-parent validation so the source and backup `info.json` identities must match in addition to the existing live source UUID, backup Received UUID, and `state.json` identity checks.
- Optimized common-parent chain restore to start incrementally when every payload's exact recorded source `send_path` still exists, has `send_source_uuid`, and remains read-only. This reuses the source/cache snapshot that Btrfs receive can identify instead of unnecessarily full-receiving the common backup.
- When the exact receive parent is missing, writable, or has the wrong UUID, restore retains the safe full-hidden-seed fallback and prints the precise reason. No existing Timeshift snapshot is modified to manufacture an incremental parent.
- Added local and SSH regression coverage for incremental-first common-parent restore, exact source-cache parent validation, full-seed fallback, stable `info.json` comparison, mixed/mismatched OS identity handling, and the new danger override.
- Updated current CLI help, README, installation guidance, interface audit, code map, tests, and package version metadata.

## 0.1.60

- Added `restore --backup-over-ssh` for pulling a Btrfs backup repository from the configured SSH host and restoring it into a local Timeshift repository.
- In pull-restore mode, `source.mode = "local"` identifies the local Timeshift target, while `destination.target_root`, `state_file`, and `lock_file` are interpreted on the SSH backup host. Ambiguous SSH-backup-to-SSH-Timeshift use with the single SSH profile is refused.
- Added one shared `BackupRepository` abstraction for local and SSH backup inventory, `info.json`, state loading, Btrfs metadata, and send commands. Existing local-backup-to-local and local-backup-to-SSH restore continue through the same restore planner and execution loop.
- Remote backup streams use SSH `btrfs send` on the left side and local `btrfs receive` on the right side, retaining the current single/full-chain, common-parent, exact receive-parent, OS-identity, retention-warning, CoW, and failure-cleanup rules.
- Added a persistent remote `flock` lock that holds the backup host's configured lock file for the complete real restore and coordinates with normal sync/prune processes using the same advisory lock.
- Remote backup inventory reads direct timestamp entries and all readable `info.json` files in one SSH command. The remote account needs ordinary backup metadata read access, write access to the existing lock file, `flock` and `base64`, plus narrow Btrfs list/show/send privilege.
- Updated current CLI help, config comments, README, installation guidance, interface audit, transport documentation, tests, code map, and package metadata.
- Added remote-backup restore and remote-lock regression coverage for configuration loading, remote state/inventory reads, SSH-send-to-local-receive pipelines, lock acquisition/busy/timeout behavior, and local-target enforcement.

## 0.1.61

- Added `init-config --profile sync` and `init-config --profile restore-pull`. The default remains `sync`; `restore-pull` generates a complete SSH-backup-to-local-Timeshift configuration instead of requiring users to expand a shortened documentation snippet.
- Added the packaged `timeshift_btrfs_sync/data/config.restore-pull.example.toml` profile. It uses `source.mode = "local"`, treats `[ssh]` as the remote backup host, and documents the remote meanings of `destination.target_root`, `state_file`, and `lock_file`.
- Kept both generated profiles schema-complete. Every current top-level, SSH, source, destination, stream, retention, manual-snapshot, MQTT, and mail key is present as an active or commented assignment.
- Expanded SSH configuration comments in both profiles for key authentication, optional `sshpass` password/password-file authentication, password-file permissions, port, cipher, compression, ControlMaster, strict host-key checking, known-hosts files, connection timeout, keepalives, jump hosts, and extra OpenSSH arguments.
- Added regression coverage proving both `init-config` profiles exactly match their packaged resources, both resources are included in the package, the pull profile loads with local Timeshift plus remote backup SSH semantics, and no supported configuration key is absent from either profile.
- Updated current README, installation guidance, CLI help, configuration audit, code map, package data, and version metadata.

## 0.1.62

- Added the restore-only `--create-pre-restore-snapshot` flag. When selected, one Timeshift on-demand/tag O safety snapshot is created on the Timeshift restore target after all plan validation and typed confirmations but before any restore staging directory or Btrfs stream.
- Reused the existing shared local/SSH Timeshift creation command. Local restore creates the safety snapshot locally, local-backup-to-SSH restore creates it on the SSH Timeshift target, and SSH-backup-to-local pull restore creates it locally. The backup repository is never asked to create a Timeshift or Btrfs snapshot.
- Added post-create verification through a fresh `timeshift --list` and exact Btrfs metadata checks for every configured payload. Ambiguous creation, a timestamp collision, missing payload, missing UUID, or Timeshift command failure aborts before backup transfer.
- The safety snapshot uses the fixed comment `TimeShift-BTRFS-Sync pre-restore safety snapshot` and is intentionally retained if later restore work fails. The existing `[manual_snapshot]` configuration remains limited to `sync` and `create-manual`.
- Updated the sync and pull-restore config comments, with the pull profile defaulting `manual_snapshot.enabled = false`, plus README, installation guidance, CLI help, configuration audit, tests, code map, and package metadata.


## 0.1.63

- Fixed SSH-backup-to-local restore configurations being silently interpreted as local-backup restore when `--backup-over-ssh` was omitted. The packaged pull profile now sets `[restore] backup_over_ssh = true`, and the CLI uses that validated transport default automatically.
- Preserved Timeshift's native Btrfs layout: `<source.snapshot_root>/<date>` is an ordinary directory containing regular `info.json` plus Btrfs `@`/`@home` payload subvolumes. Only TimeShift-BTRFS-Sync backup date containers below `<destination.target_root>/snapshots` must themselves be Btrfs subvolumes.
- Added a targeted diagnostic when a local Timeshift repository is accidentally scanned as the backup repository, explaining the ordinary date-folder layout and how to select SSH backup transport.
- Kept `--backup-over-ssh` as a one-run override while making the generated pull profile self-contained. Normal sync/prune/destroy path meanings remain unchanged.
- Added regression coverage for config-driven pull restore without the CLI flag, correct remote lock/transport selection, schema-complete restore settings, and misrouted native Timeshift layout detection.
- Updated both generated profiles, README, installation guidance, interface audit, code map, tests, and package metadata.

## 0.1.64

- Replaced the confusing restore-only `backup_over_ssh` boolean and `--backup-over-ssh` flag with one explicit `[restore] mode` setting.
- Added three current restore directions: `local` for local backup to local Timeshift, `ssh` for SSH backup pulled into local Timeshift, and `ssh-target` for local backup restored into an SSH Timeshift target.
- Made restore transport independent from `source.mode`; `source.mode` now describes only normal sync, prune, source-listing, and manual-snapshot command transport.
- Updated real and dry-run terminal output to print the selected restore mode before planning or locking.
- Kept one shared restore planner, Btrfs stream implementation, common-parent logic, OS identity checks, retention warnings, pre-restore safety snapshot, and failure cleanup for all three directions.
- Updated both generated configuration profiles, current README, installation guidance, CLI help, interface audit, tests, code map, and package metadata.


## 0.1.65

- Made restore-side endpoint ownership explicit: `source.snapshot_root` and `source.cache_root` are one Timeshift-side path pair and are always inspected through the same restore-target runner.
- For `[restore] mode = "ssh"`, backup inventory, backup `state.json`, the repository lock, and `btrfs send` run on the SSH backup host, while Timeshift listing, `snapshot_root`, `cache_root`, exact incremental receive-parent probes, receive, staging, and final verification remain local.
- For `[restore] mode = "ssh-target"`, both Timeshift paths and all receive-side operations run on the SSH Timeshift host; the local backup side never supplies or probes `source.cache_root`.
- Renamed restore-internal source inventory/operation variables to Timeshift-specific names and renamed the restore config property to `timeshift_uses_ssh`, removing the ambiguous suggestion that the backup destination controls the cache endpoint.
- Expanded the restore plan output to print the Timeshift endpoint beside both `snapshot_root` and `cache_root`, plus an explicit path-ownership statement before transfer.
- Added regression coverage proving local pull-restore cache indexing, local exact cache-parent probes, remote backup scripts excluding Timeshift paths, and SSH-target snapshot/cache pairing on one remote runner.
- Updated current README, installation guidance, configuration comments, interface audit, code map, tests, and package metadata.

## 0.1.66

- Fixed `[restore] mode = "ssh"` treating the configured `lock_file` as a remote backup-host path and refusing valid pull restores when that path did not exist remotely.
- Restore now always acquires one local `FileLock` on the machine running the command, for `local`, `ssh`, and `ssh-target` modes. `state_file` continues to follow the backup repository endpoint.
- Removed the unused `RemoteFileLock` implementation and its dedicated tests so restore has one lock mechanism instead of parallel local/SSH lock code.
- Updated the generated pull-restore profile so `destination.target_root` and `state_file` are remote, while `lock_file`, `snapshot_root`, `cache_root`, and `log_dir` are local.
- Removed the remote backup requirements for lock-file write access and `flock`; the SSH backup account remains read-only apart from Btrfs send/show/list privilege.
- Added regression coverage proving SSH pull restore never probes or opens the lock through SSH, uses the configured local lock, and refuses a missing local lock directory with a local-path diagnostic.
- Updated current CLI help, README, installation guidance, configuration comments, interface audit, code map, tests, and package metadata.

## 0.1.67

- Fixed local send-cache reuse when root-scoped `btrfs subvolume list -o` output reports existing descendants as `<date>/@`, `<date>/@home`, or bare `@`/`@home` instead of including the configured cache-root mount path.
- Root-scoped inventory parsing now joins unmatched safe relative descendants only for commands that were explicitly restricted to the requested root. Unscoped Btrfs path mapping remains conservative and continues to reject unrelated or absolute outside paths.
- Added one authoritative parent-scoped cache-child probe using UUID and read-only Btrfs listings before any `btrfs subvolume snapshot -r` creation. A valid existing child is reused after read-only and Parent UUID validation; a failed safety listing aborts instead of guessing.
- Added post-create-failure recovery through the same parent-scoped probe so a concurrently created valid cache snapshot is reused rather than treated as a failed cache version.
- Prevented an existing `<cache_root>/<date>/@` or `@home` from being passed to Btrfs as a destination directory, which previously caused attempted nested paths such as `<date>/@/@` and could trigger deletion of a valid reusable cache child during recovery.
- Added regression coverage for cache-root-relative `<date>/@` output, date-parent-relative bare `@` output, exact read-only reuse, no nested snapshot command, and conservative unscoped path rejection.
- Updated current README, installation guidance, generated configuration comments, interface audit, tests, code map, and package metadata.

