# Nested document comparison — 0.1.89

Compared all seven original files under `timeshift_btrfs_sync/` in the uploaded archive with the current root documents on 2026-10-12. These package-local duplicates were already removed in 0.1.87 and remain absent. The active package contains Python modules and its eight config examples; the root contains the canonical documentation, license and ignore rules.

| Original nested file | Result in the current root |
|---|---|
| `VERSIONING.md` | The entire 879-line original nested ledger is contained verbatim in root `VERSIONING.md`, with later versions and all subsequent changes added. No nested version entry or change description is missing. |
| `LICENSE` | Byte-identical MIT license and copyright notice. |
| `.gitignore` | All original exclusions and original config exceptions are retained. Added exceptions for `pyproject.toml` and the five new `example-config-*.toml` files so Git can stage required project files. |
| `CONFIG_AND_CLI_AUDIT.md` | All nonblank original nested lines were retained in the 0.1.88 root notes. The 0.1.89 root clarifies current versus historical material and identifies the current loader, eight profiles, README and this comparison. Historical findings are preserved; the earlier three-profile summary is explicitly labeled as historical. |
| `INSTALL.md` | Four original passages were extended to describe newer transfer-size dependencies and eight profiles rather than three. Original source installation, permissions, encrypted-key configuration, restore workflow, executable build/run and path portability guidance remains present. Added direct generation commands and executable checks for all eight profiles. |
| `README.md` | Reviewed all 16 changed original lines against 0.1.88. Replacements describe the current eight profiles, send-stream UUID identity, retention selection for incremental backups, pending on-demand snapshots, final summaries/mail, mbuffer accounting, current help/version support, capacity checks and verified retention anchor. The user-supplied disclaimers are retained. Original applicable usage guidance remains; obsolete behavior was updated rather than copied into current usage. |
| `COMMENTED_CODE_MAP.md` | The root map was regenerated from the current project. It explains all 528 current source/build symbols and 476 test symbols, application commands, shell helper and integrations. The old map's module coverage is retained, with newer functions added and current line references. The existing release-hygiene check verifies every current source/build symbol is documented. |

`VERSIONING.md` and `COMMENTED_CODE_MAP.md` are the sole canonical ledger and map. Lowercase `versioning.md` and `commented_code_map.md` remain absent. No project paths differ only by capitalization.

The uploaded original and earlier release archives remain unchanged for reference. Use the complete new release directory or ZIP; merging it into an older checkout does not automatically delete files already present there. When updating an existing checkout, remove the seven listed package-local files and the two lowercase root duplicates there as well.

Backup, restore, retention, deletion and locking implementations were not changed by this documentation/packaging audit. No live filesystem operations were performed; full verification and limitations are in `RELEASE_VERIFICATION.md`.
