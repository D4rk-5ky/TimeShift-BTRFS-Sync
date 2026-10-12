# Release verification — TimeShift-BTRFS-Sync 0.1.91

Created on 2026-10-12, incrementing 0.1.90 by 0.0.1.

## Changes

- requirements.txt now uses -e .[mqtt,pyinstaller], installing the existing project, paho-mqtt and PyInstaller through the declared extras, with their resolved dependencies. The setuptools build backend remains declared in pyproject.toml. No duplicate dependency list was introduced.
- INSTALL.md and README.md describe the full venv workflow, both-module import verification and one-file executable building with --with-mqtt. Smaller installs are documented alternatives; MQTT notifications still require config enablement.
- Updated VERSIONING.md, COMMENTED_CODE_MAP.md, the current config/CLI audit summary, all version metadata/config headers and the existing version expectation. Runtime Python modules except version metadata are byte-identical to 0.1.90. Backup, restore, retention and safety behavior are unchanged.

## Verification

- Pip's own requirements parser accepts the editable project entry and selects exactly the mqtt and pyinstaller extras.
- Existing metadata declares paho-mqtt>=1.6, pyinstaller>=6.0 and setuptools>=68 as the build backend. Static imports across the application/build entry points identify only paho and PyInstaller as external Python dependencies; both are covered.
- Verified executable argument construction includes --onefile, the complete config data directory and --hidden-import paho.mqtt.client when --with-mqtt is selected.
- Python 3.12 and 3.14 each ran 295 tests: 291 passed and four existing historical remote-lock cases skipped.
- All 67 Python files compiled outside the release tree. Global and all 11 CLI commands passed 24 help/version checks; source reports 0.1.91. All eight config profiles load and generate exactly their packaged templates. Helper help/version checks and shell syntax validation passed.
- Canonical document layout, nested version-history preservation and existing Git ignore checks passed. The full ZIP's CRC, safe unique paths, hashes, permissions and cache/temp exclusions were verified against the tree, 0.1.90 and the uploaded original. All 94 prior files are retained. Only the earlier authorized 52 nested-source removals and previously excluded empty runtime marker are absent relative to the upload.

## Limits

This release did not download/install the MQTT/PyInstaller dependency set or construct an executable. The prior core-only offline venv test does not establish a full dependency installation for this release. Live MQTT delivery, Btrfs/Timeshift/SSH operations and integration deployment remain untested. Python 3.11 was not exercised.

The preserved original dist/ts-btrfs still reports 0.1.84; run the current Python source/installed command or build a new executable for current behavior. The original upload and previous releases are unchanged. Extract this complete project into a fresh directory to avoid carrying obsolete files from an older checkout.
