# Release verification — TimeShift-BTRFS-Sync 0.1.92

Created on 2026-10-12, incrementing 0.1.91 by 0.0.1.

## Changes

- Added separate DESTINATION CLEANUP SUMMARY and SOURCE SEND-CACHE CLEANUP SUMMARY blocks, shared by final sync output and standalone prune. Counts show snapshot-date candidates, attempted dates, confirmed absence and pending/skipped work independently for each side.
- Extended PruneResult and the existing prune action handlers to record each side's outcome. Destination success is preserved in the summary if later cache cleanup fails and state remains for retry. Protected direct Timeshift originals are not counted as cache cleanup. No deletion command, ordering, authorization, state-removal condition, UUID/read-only guard or source-retention policy was changed.
- Labeled app-created Timeshift original cleanup separately in the overall block and explained the overall completed paired/state/source-only count. Ordinary source retention remains managed by Timeshift.
- Updated README with final terminal/log/mail ordering, scope and count semantics. Regenerated the canonical code map: 530 current source/build symbols and 490 test symbols. Updated VERSIONING, current audit, installation/Git guidance and shared version metadata/config headers. The full MQTT/PyInstaller requirements remain unchanged.
- Added 12 regression tests reusing existing retention fixtures, and extended final log/mail order assertions. All prior project files are retained; the new test module brings the release to 95 files.

## Verification

- Python 3.12 and 3.14 each ran 307 tests: 303 passed, four existing historical remote-lock cases skipped.
- Regression coverage includes @/@home counted once, destination/cache partial failures, state retained for retry, disabled cache cleanup, direct protected sends, blocked source authorization, source-app completion, prune aggregation, dry-run, missing-result unknown counts and unrequested cleanup. Log/mail assertions cover both new blocks.
- All 68 Python files compiled outside the release tree. Global and all 11 CLI commands passed 24 help/version checks; source reports 0.1.92. All eight config profiles load and generate their exact templates. Helper help/version and shell syntax checks passed.
- Tested actual git add -A in a temporary repository: all eight example configs, pyproject.toml and requirements.txt were staged. Adding the old package-local .gitignore reproduced exclusion of all five new examples; removing it restored the root exceptions. This reproduces a possible cause, not an inspection of the user's Git index.
- Canonical root documentation, absent nested/lowercase duplicates, no capitalization-only collisions and complete nested version-history preservation passed.
- Full ZIP CRC, safe unique paths, SHA-256 contents, permissions and cache/temp exclusions were verified against the tree, 0.1.91 and the uploaded original. All 94 prior files are retained. The original omissions remain limited to the earlier authorized 52 nested-source removals and previously excluded empty runtime marker.

## Count semantics and limits

These new counters cover retention cleanup, not earlier cache maintenance during transfer preparation. A successful existing cleanup routine proves the required paths absent, whether newly removed or already gone; counts do not measure freed space or guarantee prior existence. Cache counts include only tracked app-owned send-cache dates. Dry-run never claims real deletion. If prune aborts without returning a result, side counts are unknown rather than fabricated.

No live Btrfs/Timeshift/SSH deletion, backup, restore, notification or integration deployment was tested. Full MQTT/PyInstaller installation and executable building were not repeated. Python 3.11 was not exercised. The preserved original dist/ts-btrfs remains 0.1.84; use the current source/installed command or rebuild before expecting new summaries.

The uploaded original and previous archives are unchanged. Extract this release into a fresh directory; copying it over an old checkout leaves obsolete nested files behind. INSTALL.md includes Git ignore diagnosis and staging guidance.
