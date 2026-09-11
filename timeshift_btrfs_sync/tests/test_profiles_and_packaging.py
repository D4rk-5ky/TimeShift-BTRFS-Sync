from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest

from timeshift_btrfs_sync import __version__
from timeshift_btrfs_sync import config as config_module
from timeshift_btrfs_sync.config import load_config


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "timeshift_btrfs_sync" / "data"
PROFILE_FILES = {
    "sync": "config.example.toml",
    "restore-pull": "config.restore-pull.example.toml",
    "remote-roundtrip": "config.remote-roundtrip.example.toml",
}


class ConfigProfileTests(unittest.TestCase):
    def test_all_three_packaged_profiles_exist_and_load(self) -> None:
        expected_modes = {
            "sync": ("ssh", "local"),
            "restore-pull": ("local", "ssh"),
            "remote-roundtrip": ("ssh", "ssh-target"),
        }
        for profile, filename in PROFILE_FILES.items():
            with self.subTest(profile=profile):
                path = DATA_DIR / filename
                self.assertTrue(path.is_file(), path)
                loaded = load_config(path)
                self.assertEqual(
                    (loaded.source.mode, loaded.restore.mode),
                    expected_modes[profile],
                )

    def test_every_profile_mentions_every_current_config_option(self) -> None:
        groups = [
            config_module.TOP_LEVEL_KEYS,
            config_module.SOURCE_KEYS,
            config_module.DESTINATION_KEYS,
            config_module.STREAM_KEYS,
            config_module.RETENTION_KEYS,
            config_module.MANUAL_SNAPSHOT_KEYS,
            config_module.RESTORE_KEYS,
            config_module.SSH_KEYS,
            config_module.MQTT_KEYS,
            config_module.MAIL_KEYS,
        ]
        expected = set().union(*groups)
        for filename in PROFILE_FILES.values():
            text = (DATA_DIR / filename).read_text(encoding="utf-8")
            with self.subTest(filename=filename):
                missing = sorted(key for key in expected if key not in text)
                self.assertEqual(missing, [], f"missing documented config keys: {missing}")

    def test_init_config_generates_every_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            for profile, filename in PROFILE_FILES.items():
                output = tmpdir / f"{profile}.toml"
                proc = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "timeshift_btrfs_sync",
                        "init-config",
                        "--profile",
                        profile,
                        "--path",
                        str(output),
                    ],
                    cwd=PROJECT_ROOT,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                with self.subTest(profile=profile):
                    self.assertEqual(proc.returncode, 0, proc.stderr)
                    self.assertEqual(
                        output.read_text(encoding="utf-8"),
                        (DATA_DIR / filename).read_text(encoding="utf-8"),
                    )
                    load_config(output)

    def test_init_config_help_describes_every_profile(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "timeshift_btrfs_sync", "init-config", "--help"],
            cwd=PROJECT_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for profile in PROFILE_FILES:
            with self.subTest(profile=profile):
                self.assertIn(profile, proc.stdout)

    def test_pyproject_package_data_lists_every_profile(self) -> None:
        with (PROJECT_ROOT / "pyproject.toml").open("rb") as handle:
            project = tomllib.load(handle)
        package_data = project["tool"]["setuptools"]["package-data"]["timeshift_btrfs_sync"]
        self.assertEqual(
            set(package_data),
            {f"data/{filename}" for filename in PROFILE_FILES.values()},
        )

    def test_pyinstaller_bundles_the_complete_data_directory(self) -> None:
        script_path = PROJECT_ROOT / "scripts" / "build_pyinstaller.py"
        spec = importlib.util.spec_from_file_location("build_pyinstaller", script_path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        args = module.build_args(
            mode="onefile",
            name="ts-btrfs",
            clean=True,
            with_mqtt=False,
            extra=[],
        )
        add_data_index = args.index("--add-data") + 1
        add_data = args[add_data_index]
        source, destination = add_data.rsplit(":", 1)
        self.assertEqual(Path(source), DATA_DIR)
        self.assertEqual(destination, "timeshift_btrfs_sync/data")
        for filename in PROFILE_FILES.values():
            self.assertTrue((Path(source) / filename).is_file())

    def test_profile_headers_match_package_version(self) -> None:
        for filename in PROFILE_FILES.values():
            first_line = (DATA_DIR / filename).read_text(encoding="utf-8").splitlines()[0]
            with self.subTest(filename=filename):
                self.assertIn(f"v{__version__}", first_line)


if __name__ == "__main__":
    unittest.main()
