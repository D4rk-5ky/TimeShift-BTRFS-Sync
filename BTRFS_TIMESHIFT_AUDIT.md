# Btrfs / Timeshift audit — source 0.1.87

Audited 2026-10-12. The uploaded source was 0.1.84; the previous maintenance source was 0.1.85. Findings and fixes below concern the active first-level package. The older nested 0.1.75 project copy was removed as requested; its former paths are listed in REMOVED_NESTED_SOURCES.md. The original 0.1.84 executable remains a preserved artifact. Use the current Python source or rebuild an executable to obtain these fixes.

## What upstream behavior requires

A Btrfs snapshot shares extents through copy-on-write, and deleting one snapshot does not invalidate another completed snapshot. Incremental send changes the wire transfer relative to a shared parent; receive reconstructs a complete snapshot. Send inputs must be read-only, and the receiver must have the corresponding unchanged parent. Retention therefore does not need to preserve every intermediate received hourly once a complete newer snapshot is received. It does need to retain at least one usable source/receiver pair for a future incremental. [Btrfs send/receive overview](https://btrfs.readthedocs.io/en/stable/Send-receive.html), [send requirements](https://btrfs.readthedocs.io/en/latest/btrfs-send.html).

Native subvolumes send their local UUID; an already received subvolume sends its original Received UUID. The kernel makes the same choice for clone/parent identity. Receiver matching also involves transaction identity; UUID/read-only inventory is the app's preflight proof, while Btrfs itself still validates the stream. A previously modified and re-frozen native subvolume is not guaranteed equivalent merely because its UUID is unchanged. The app never deliberately modifies its immutable parent payloads. [Kernel send implementation](https://github.com/torvalds/linux/blob/master/fs/btrfs/send.c), [subvolume read-only/received identity](https://btrfs.readthedocs.io/en/latest/Subvolumes.html).

Timeshift creates Btrfs snapshots of `@` and, when configured, `@home` using writable snapshots. Its timestamp directories are ordinary directories; its payloads are Btrfs subvolumes. The app's separate read-only cache is therefore necessary for normal writable Timeshift sources. [Timeshift creation code](https://github.com/linuxmint/timeshift/blob/master/src/Core/Main.vala).

O/B/H/D/W/M correspond to on-demand/boot/hourly/daily/weekly/monthly metadata tags. Timeshift changes tags and comments in `info.json`; changing those labels does not create a different payload UUID. Timeshift's own retention removes expired tags and deletes untagged snapshots. The app consequently refreshes metadata independently of incremental payload identity. [Timeshift snapshot metadata](https://github.com/linuxmint/timeshift/blob/master/src/Core/Snapshot.vala), [Timeshift repository retention](https://github.com/linuxmint/timeshift/blob/master/src/Core/SnapshotRepo.vala).

## Confirmed defects and corrections

| Area | Defect before this release | Current correction |
|---|---|---|
| Parent ordering | An older state-recorded parent took priority over a newer matching filesystem date absent from state. | Sort the union of candidate dates newest-first before proof. |
| Missing receiver parent | Missing/unreadable destination metadata raised out of the search, preventing an older daily from being considered. | Reject that candidate and continue to older candidates. |
| Stale state authority | Sync-floor matching accepted source UUIDs from saved state even when the live destination Received UUID differed or was absent. | Live Received UUID is authoritative; state is only a candidate-location hint. |
| Read-only proof | Unknown source read-only status was accepted, and parent destination read-only status was not required. | Require confirmed read-only parents on both ends; apply the same rule to cache lookup/state adoption. |
| Cache-floor recovery | Floor proof used the saved path/original but did not perform the parent selector's indexed cache UUID search. | Reuse the verified-parent selector, allowing exact cache lookup after an original disappears or a saved location goes stale. |
| Transfer selection | Fresh seeds used retention selection, but existing backups queued every source date, including unneeded hourlies. | Use the existing shared retention selector for both. Completed copies remain queued for changed metadata refresh. Explicit `--snapshot` still selects one date directly. |
| Retention anchor | `keep_latest_common_parent` kept the newest state name without proving it was still shared. An older sole matching daily could be deleted. | Before retention deletion, prove and protect the newest complete live read-only matching pair. Stop cleanup when no pair is proven. |
| Native restore layout | Home-only/custom backup payloads could reach a function that promises Timeshift system snapshots. | Refuse those layouts before restore commands; require `@`, optionally `@home`. |

Eight focused old-behavior cases were run against 0.1.85: five assertions failed and one missing-parent case errored. Two controls passed: changed tags already preserved a valid parent, and a saved newer hourly cache already worked after its original disappeared. Both controls remain covered. Additional tests exercise daily fallback, full-seed restrictions, retained queues and cleanup protection/refusal.

## The missing-hourly / surviving-daily case

1. Find the newest complete matching date independently of its current tags. If the original hourly is gone but its exact read-only cache remains, that hourly can still be used.
2. If the hourly has no matching cache, or its destination is missing/unusable, continue backward. A matching daily is a valid starting parent.
3. Transfer the retained newer source snapshots oldest-to-newest. Each completed snapshot can become the next incremental parent. Do not retransmit historical dates at/below the confirmed floor merely because destination retention removed them.
4. When pruning is requested and real deletion is authorized, remove tracked backup dates outside the union of retention/protection rules, including extra hourlies. Delete their eligible cache copies through the existing guarded tree engine. Protect the actual common parent.
5. Let Timeshift retire ordinary source H/D/W/M/B snapshots. The app only retires verified app-created O snapshots with its configured marker and complete backup proof. Normal/user-created O backup retention remains independently disabled by default.

Retention counts are not exact total snapshot counts: multi-tag snapshots survive if any tag keeps them; protected dates, newest safeguards, the proven common parent, and disabled on-demand cleanup can retain additional copies. Unknown/untracked destination trees are not automatically deleted just because their names look like dates. Failed/incomplete items retain the existing guarded recovery/retry behavior.

If a pre-existing nonempty backup has no usable shared pair, the safety policy still refuses an automatic full-send fallback. Repair the exact cache/state or use a separate empty target. First-send interruption without a complete shared pair can therefore require explicit repair/new-target handling. This preserves the user's requested safety policy.

## Failure continuation

The code restarts an incomplete snapshot date rather than resuming an interrupted byte stream. A completed snapshot is recorded immediately; an incomplete date/cache is retired only through the existing recovery guards. Confirmed changes to a required source/current/parent/sibling path trigger a bounded combined-inventory rebuild and restart at the normal chronological position. Unrelated tag/list churn cannot turn a network or buffer error into a source-change retry. Definite destination storage failures abort immediately. A later run can handle the remaining incomplete receive once the underlying failure is repaired and a complete anchor is proven.

Dry-run parent paths remain provisional previews. They do not authorize a real transfer: the real path-selection and pre-existing destination-floor checks require live identity proof. External Timeshift activity is not locked by the app's local lock; Btrfs errors and exact-path recovery remain necessary when it changes during a transfer.

## Restore assessment

The existing restore architecture is appropriate for the supported native layout. It full-receives a hidden seed, receives later snapshots incrementally from exact hidden parents, and retries an explicitly missing receiver parent/clone once with a full stream. It then creates writable CoW payloads under ordinary staging date directories, restores original `info.json`, verifies payloads/metadata, moves the dates into `source.snapshot_root`, and checks that `timeshift --list` accepts them. This imports snapshots for Timeshift; it does not restore the running OS itself.

Preserving `info.json` is intentional. Timeshift reads root/home paths using its configured repository mounts and queries current subvolume IDs when loading the repository, rather than requiring copied original IDs to remain valid. The original tags remain subject to Timeshift retention after import. [Timeshift metadata loading](https://github.com/linuxmint/timeshift/blob/master/src/Core/Snapshot.vala), [repository loading](https://github.com/linuxmint/timeshift/blob/master/src/Core/SnapshotRepo.vala), [current ID refresh](https://github.com/linuxmint/timeshift/blob/master/src/Core/Main.vala).

One snapshot root/filesystem containing `@` and optional `@home` is supported. Timeshift can support root/home on separate devices, but this app's single-root restore configuration does not implement that placement; do not use it for that topology. Existing date collisions, OS-identity checks, all danger flags and typed retention warnings remain intact. The metadata identity fallback identifies the same OS/date; it is not a cryptographic payload comparison, and the receive path still starts with an exact full seed.

## Examples and verification limits

All five requested explicit example names are under `timeshift_btrfs_sync/data/` and exposed through `init-config --profile`. Existing profile names are retained. Each example contains every available option and explains which host owns the Timeshift path, backup path, lock and logs. See README.md for commands/flags and RELEASE_VERIFICATION.md for test results and archive checks.

Tests use isolated fixtures/mocks. This environment has not exercised real Btrfs send/receive, Timeshift import/list/delete behavior, source churn during a real stream, split filesystems, or SSH transfer/privilege setup. Those need a non-production Btrfs/Timeshift test. No production snapshot operation was performed. The original executable remains 0.1.84 because PyInstaller is unavailable here.
