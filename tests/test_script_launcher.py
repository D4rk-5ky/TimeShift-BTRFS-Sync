"""Exercise the direct Python launcher without installation, a venv or site packages."""
import argparse
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from timeshift_btrfs_sync import __version__
from timeshift_btrfs_sync.cli import build_parser
from timeshift_btrfs_sync.config import CONFIG_PROFILES
from timeshift_btrfs_sync.state import empty_state

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "timeshift_btrfs_sync.py"


class ScriptLauncherTests(unittest.TestCase):
    """Protect shared CLI behavior, relative paths and complete-project import resolution."""

    def run_script(self, *args, cwd=None, expected=0):
        """Run a real script process with site packages and user Python path disabled."""
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        environment.pop("PYTHONPATH", None)
        environment.pop("PYTHONHOME", None)
        result = subprocess.run([sys.executable, "-S", "-B", str(LAUNCHER), *args],
            cwd=cwd or ROOT, env=environment, text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def test_global_and_every_command_help_version_share_the_cli(self):
        """All 26 help/version routes work with no installed Python dependencies."""
        parser = build_parser()
        commands = next(action.choices for action in parser._actions if isinstance(action, argparse._SubParsersAction))
        for prefix in [[], *[[name] for name in commands]]:
            for flag in ["--help", "--version"]:
                with self.subTest(prefix=prefix, flag=flag):
                    result = self.run_script(*prefix, flag)
                    self.assertIn(__version__, result.stdout)

    def test_default_and_all_profiles_are_generated_from_another_directory(self):
        """The script finds bundled resources and leaves relative output paths in the caller's cwd."""
        with tempfile.TemporaryDirectory() as tmp:
            for profile in [None, *CONFIG_PROFILES]:
                filename = (profile or "default") + ".toml"
                args = ["init-config", "--path", filename]
                if profile: args += ["--profile", profile]
                with self.subTest(profile=profile):
                    self.run_script(*args, cwd=tmp)
                    expected = ROOT / "timeshift_btrfs_sync/data" / CONFIG_PROFILES[profile or "sync"][0]
                    self.assertEqual((Path(tmp) / filename).read_bytes(), expected.read_bytes())

    def test_relative_config_and_state_paths_keep_caller_directory(self):
        """Reading state and safe maintenance must not silently chdir to the launcher's directory."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config.toml").write_text('state_file="state.json"\nlock_file="lock"\n[source]\nmode="local"\nsnapshot_root="/unused-source"\n[destination]\ntarget_root="/unused-backup"\n')
            state = root / "state.json"; state.write_text(json.dumps(empty_state()))
            original = state.read_bytes()
            result = self.run_script("show-state", "--config", "config.toml", "--json", cwd=tmp)
            self.assertEqual(json.loads(result.stdout), empty_state())
            result = self.run_script("clear-state", "--config", "config.toml", "--dry-run", cwd=tmp, expected=1)
            self.assertIn("must be absolute", result.stderr)
            config = root / "config.toml"
            config.write_text(config.read_text().replace('state_file="state.json"', 'state_file='+json.dumps(str(state))))
            result = self.run_script("clear-state", "--config", "config.toml", "--dry-run", cwd=tmp)
            self.assertIn("would remove", result.stdout)
            self.assertEqual(state.read_bytes(), original)
            self.assertFalse((root / "lock").exists())

    def test_existing_config_is_preserved_without_force(self):
        """The launcher cannot weaken init-config's existing overwrite refusal."""
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "config.toml"; output.write_text("# keep my configuration\n")
            result = self.run_script("init-config", "--path", "config.toml", cwd=tmp, expected=2)
            self.assertIn("Refusing to overwrite existing file", result.stderr)
            self.assertEqual(output.read_text(), "# keep my configuration\n")

    def test_argument_and_configuration_refusals_keep_exit_codes(self):
        """Normal parser/config errors still exit 2 through the shared main function."""
        self.run_script(expected=2)
        self.run_script("sync", "--config", "unused.toml", "--dry-run", "--run", expected=2)
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "bad.toml").write_text('[source]\nmode="invalid"\n')
            result = self.run_script("show-state", "--config", "bad.toml", cwd=tmp, expected=2)
            self.assertIn("Config error:", result.stderr)

    def test_exact_return_code_from_shared_main_is_forwarded(self):
        """No new dispatcher or error translation can hide the existing CLI's result."""
        with patch("timeshift_btrfs_sync.cli.main", return_value=23) as main, self.assertRaises(SystemExit) as raised:
            runpy.run_path(str(LAUNCHER), run_name="__main__")
        self.assertEqual(raised.exception.code, 23)
        main.assert_called_once_with()

    def test_importing_launcher_does_not_dispatch_commands(self):
        """Treat the file like a normal Python script with a guarded main entry point."""
        with patch("timeshift_btrfs_sync.cli.main") as main:
            runpy.run_path(str(LAUNCHER), run_name="launcher_import_probe")
        main.assert_not_called()

    def test_package_import_wins_over_same_named_script(self):
        """The adjacent package remains importable despite the matching launcher filename."""
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        environment.pop("PYTHONPATH", None)
        result = subprocess.run([sys.executable, "-S", "-B", "-c", "import timeshift_btrfs_sync; print(timeshift_btrfs_sync.__file__)"],
            cwd=ROOT, env=environment, text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(result.stdout.strip()), ROOT / "timeshift_btrfs_sync/__init__.py")

    def test_missing_adjacent_package_gives_clear_instructions(self):
        """Copying the launcher alone reports the full-project requirement instead of recursive imports."""
        with tempfile.TemporaryDirectory() as tmp:
            copied = Path(tmp) / LAUNCHER.name; copied.write_bytes(LAUNCHER.read_bytes())
            result = subprocess.run([sys.executable, "-S", "-B", str(copied), "--version"],
                cwd=tmp, text=True, capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Extract the full project ZIP", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_python_version_guard_runs_before_cli_import(self):
        """Unsupported interpreters receive the required version before tomllib/import failures."""
        with patch.object(sys, "version_info", (3, 10, 0)), patch("timeshift_btrfs_sync.cli.main") as main, self.assertRaises(SystemExit) as raised:
            runpy.run_path(str(LAUNCHER), run_name="__main__")
        self.assertIn("Python 3.11", str(raised.exception))
        main.assert_not_called()

    def test_executable_shebang_launch(self):
        """The source script also runs directly when the archive executable bit is preserved."""
        self.assertTrue(os.access(LAUNCHER, os.X_OK))
        result = subprocess.run([str(LAUNCHER), "--version"], cwd=ROOT,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"), text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(__version__, result.stdout)
