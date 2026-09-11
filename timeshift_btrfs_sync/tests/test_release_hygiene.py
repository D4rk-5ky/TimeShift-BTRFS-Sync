from __future__ import annotations

import ast
from pathlib import Path
import re
import tomllib
import unittest

from timeshift_btrfs_sync import __version__
from timeshift_btrfs_sync.cli import build_parser


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = PROJECT_ROOT / "timeshift_btrfs_sync"
EXPECTED_COMMANDS = {
    "init-config",
    "test-source",
    "list-source",
    "sync",
    "prune",
    "restore",
    "create-manual",
    "destroy-leftovers",
    "clear-state",
    "delete-lock",
    "show-state",
}


class ReleaseHygieneTests(unittest.TestCase):
    def test_removed_legacy_files_stay_removed(self) -> None:
        self.assertFalse((RUNTIME_DIR / "metadata.py").exists())
        self.assertFalse((PROJECT_ROOT / "delete-btrfs-tree.sh").exists())

    def test_runtime_success_logs_are_ignored_and_not_shipped(self) -> None:
        gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn("*.succes", gitignore)
        for filename in (
            "config.example.toml",
            "config.restore-pull.example.toml",
            "config.remote-roundtrip.example.toml",
        ):
            self.assertIn(f"!timeshift_btrfs_sync/data/{filename}", gitignore)
        shipped = [
            path.relative_to(PROJECT_ROOT).as_posix()
            for path in PROJECT_ROOT.rglob("*.succes")
            if not any(part in {".git", "build", "dist"} for part in path.parts)
        ]
        self.assertEqual(shipped, [])

    def test_version_metadata_is_consistent(self) -> None:
        with (PROJECT_ROOT / "pyproject.toml").open("rb") as handle:
            pyproject = tomllib.load(handle)
        self.assertEqual(pyproject["project"]["version"], __version__)
        self.assertEqual(__version__, "0.1.75")

    def test_readme_documents_every_cli_command(self) -> None:
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        for command in EXPECTED_COMMANDS:
            with self.subTest(command=command):
                self.assertIn(f"### `{command}`", readme)

    def test_parser_command_set_matches_documented_command_set(self) -> None:
        parser = build_parser()
        subparser_choices = None
        for action in parser._actions:
            choices = getattr(action, "choices", None)
            if isinstance(choices, dict) and choices:
                subparser_choices = set(choices)
                break
        self.assertEqual(subparser_choices, EXPECTED_COMMANDS)

    def test_readme_mentions_every_public_parser_option(self) -> None:
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        parser = build_parser()
        parsers = [parser]
        for action in parser._actions:
            choices = getattr(action, "choices", None)
            if isinstance(choices, dict):
                parsers.extend(choices.values())
        missing: list[str] = []
        for current in parsers:
            for action in current._actions:
                for option in getattr(action, "option_strings", []):
                    if option not in readme:
                        missing.append(option)
        self.assertEqual(sorted(set(missing)), [])

    def test_code_map_names_every_runtime_and_build_symbol(self) -> None:
        code_map = (PROJECT_ROOT / "COMMENTED_CODE_MAP.md").read_text(encoding="utf-8")
        source_files = [
            PROJECT_ROOT / "scripts" / "build_pyinstaller.py",
            *sorted(RUNTIME_DIR.glob("*.py")),
        ]
        missing: list[str] = []
        for path in source_files:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    name = node.name
                    if re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])", code_map) is None:
                        missing.append(f"{path.relative_to(PROJECT_ROOT)}:{node.lineno}:{name}")
        self.assertEqual(missing, [], "undocumented symbols:\n" + "\n".join(missing))

    def test_no_python_cache_or_build_cache_is_present_in_source_tree(self) -> None:
        forbidden_names = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "build", "dist"}
        offenders = []
        for path in PROJECT_ROOT.rglob("*"):
            rel = path.relative_to(PROJECT_ROOT)
            if any(part in forbidden_names or part.endswith(".egg-info") for part in rel.parts):
                offenders.append(rel.as_posix())
            elif path.is_file() and path.suffix in {".pyc", ".pyo"}:
                offenders.append(rel.as_posix())
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
