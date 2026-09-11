from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import io
from pathlib import Path
import subprocess
import sys
import unittest

from timeshift_btrfs_sync import __version__
from timeshift_btrfs_sync.cli import build_parser


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _subparsers(parser: argparse.ArgumentParser) -> dict[str, argparse.ArgumentParser]:
    for action in parser._actions:
        choices = getattr(action, "choices", None)
        if isinstance(choices, dict) and choices:
            return choices
    return {}


class CliHelpContractTests(unittest.TestCase):
    def test_top_level_help_is_self_contained_and_shows_version(self) -> None:
        text = build_parser().format_help()
        self.assertIn(f"TimeShift-BTRFS-Sync {__version__}", text)
        self.assertIn(f"Version: {__version__}", text)
        self.assertIn("--version", text)
        self.assertIn("Run-mode rules:", text)
        self.assertIn("Deletion / danger rules:", text)
        self.assertIn("Exit codes:", text)
        self.assertIn("ts-btrfs COMMAND --help", text)
        self.assertNotIn("Config options are documented in README", text)

    def test_every_public_option_has_meaningful_help_and_is_rendered(self) -> None:
        parser = build_parser()
        parsers = {"<top-level>": parser, **_subparsers(parser)}
        failures: list[str] = []
        for name, current in parsers.items():
            rendered = current.format_help()
            for action in current._actions:
                option_strings = list(getattr(action, "option_strings", []))
                if not option_strings:
                    continue
                help_text = action.help
                if help_text in (None, argparse.SUPPRESS) or len(str(help_text).strip()) < 12:
                    failures.append(f"{name}: weak/missing help for {option_strings}: {help_text!r}")
                for option in option_strings:
                    if option not in rendered:
                        failures.append(f"{name}: {option} missing from rendered --help")
        self.assertEqual(failures, [], "\n".join(failures))

    def test_every_subcommand_help_shows_version_relationships_or_examples(self) -> None:
        parser = build_parser()
        failures: list[str] = []
        for name, current in _subparsers(parser).items():
            rendered = current.format_help()
            if f"TimeShift-BTRFS-Sync {__version__}" not in rendered:
                failures.append(f"{name}: version missing")
            if "--version" not in rendered:
                failures.append(f"{name}: --version missing")
            if "Example" not in rendered:
                failures.append(f"{name}: no command example in help")
        self.assertEqual(failures, [], "\n".join(failures))

    def test_version_works_top_level_and_after_every_subcommand(self) -> None:
        parser = build_parser()
        commands = sorted(_subparsers(parser))
        invocations = [["--version"], *[[command, "--version"] for command in commands]]
        for argv in invocations:
            proc = subprocess.run(
                [sys.executable, "-m", "timeshift_btrfs_sync", *argv],
                cwd=PROJECT_ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            with self.subTest(argv=argv):
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIn(__version__, proc.stdout)

    def test_help_action_exits_successfully_before_required_command_flags(self) -> None:
        # Required groups such as restore --snapshot/--all and destroy-leftovers
        # selections must not prevent users from asking for help.
        for command in _subparsers(build_parser()):
            proc = subprocess.run(
                [sys.executable, "-m", "timeshift_btrfs_sync", command, "--help"],
                cwd=PROJECT_ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            with self.subTest(command=command):
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIn("--help", proc.stdout)


if __name__ == "__main__":
    unittest.main()
