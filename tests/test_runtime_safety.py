from __future__ import annotations

import builtins
import symtable
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from timeshift_btrfs_sync import paths, preflight, tree_ops
from timeshift_btrfs_sync.btrfs_ops import BtrfsOps
from timeshift_btrfs_sync.commands import Completed
from timeshift_btrfs_sync.endpoint import CommandEndpoint
from timeshift_btrfs_sync.models import SubvolumeMeta


class PreflightParserTests(unittest.TestCase):
    def test_shared_parser_handles_ok_failure_and_detail(self):
        output = (
            "noise before markers\n"
            "TSBTRFS_PATH_OK\tsource.snapshot_root\t/snapshots\tverified\n"
            "TSBTRFS_PATH_FAIL\tsource.cache_root\t/cache\t30\tread-only filesystem\n"
        )
        parsed = preflight._parse_path_check_output(output, location="remote")
        self.assertEqual(len(parsed), 2)
        self.assertTrue(parsed[0].ok)
        self.assertEqual(parsed[0].detail, "verified")
        self.assertFalse(parsed[1].ok)
        self.assertEqual(parsed[1].detail, "btrfs access failed with exit 30: read-only filesystem")

    def test_source_path_checks_executes_parser_after_lock_stage(self):
        config = SimpleNamespace(
            source=SimpleNamespace(
                snapshot_root="/snapshots",
                cache_root="/cache",
                sudo="sudo -n",
                btrfs_command="btrfs",
                create_readonly_cache=True,
            )
        )
        source = SimpleNamespace(
            location="local",
            run=lambda *_args, **_kwargs: Completed(
                0,
                "TSBTRFS_PATH_OK\tsource.snapshot_root\t/snapshots\tverified\n"
                "TSBTRFS_PATH_OK\tsource.cache_root\t/cache\texists as Btrfs subvolume\n",
                "",
            ),
        )
        results = preflight._source_path_checks(config, source, dry_run=False)
        self.assertEqual([item.label for item in results], ["source.snapshot_root", "source.cache_root"])
        self.assertTrue(all(item.ok for item in results))


class StaticRuntimeSymbolTests(unittest.TestCase):
    def test_no_package_function_references_an_undefined_module_global(self):
        builtin_names = set(dir(builtins)) | {
            "__file__", "__name__", "__package__", "__spec__", "__loader__",
            "__cached__", "__doc__", "__annotations__",
        }
        problems: list[str] = []
        for path in sorted(Path("timeshift_btrfs_sync").glob("*.py")):
            table = symtable.symtable(path.read_text(encoding="utf-8"), str(path), "exec")
            module_defs = {
                name
                for name in table.get_identifiers()
                if (
                    table.lookup(name).is_assigned()
                    or table.lookup(name).is_imported()
                    or table.lookup(name).is_parameter()
                    or table.lookup(name).is_namespace()
                )
            }

            def walk(scope) -> None:
                for name in scope.get_identifiers():
                    symbol = scope.lookup(name)
                    if symbol.is_referenced() and symbol.is_global() and name not in module_defs and name not in builtin_names:
                        problems.append(f"{path}:{scope.get_lineno()}:{scope.get_name()} references {name}")
                for child in scope.get_children():
                    walk(child)

            walk(table)
        self.assertEqual(problems, [])


class LocalPathSafetyTests(unittest.TestCase):
    def test_source_normalization_preserves_disabled_empty_path(self):
        self.assertEqual(paths.normalize_source_path("   "), "")
        self.assertFalse(paths.is_same_or_under("", ""))
        self.assertFalse(paths.is_under("", "/cache"))

    def test_local_containment_resolves_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target = base / "target"
            logs = target / "logs"
            logs.mkdir(parents=True)
            alias = base / "logs-alias"
            alias.symlink_to(logs, target_is_directory=True)
            self.assertTrue(paths.is_local_same_or_under(alias, target))
            self.assertFalse(paths.is_same_or_under(alias, target))

    def test_unmatched_btrfs_list_path_is_not_guessed_below_root(self):
        self.assertIsNone(paths.listed_path_to_absolute("/mounted/cache", "@other/unrelated/subvolume"))
        self.assertIsNone(paths.listed_path_to_absolute("/mounted/cache", "/outside/cache/date/@"))


class SharedTreeSafetyTests(unittest.TestCase):
    def setUp(self):
        self.ops = BtrfsOps(CommandEndpoint.local("test"), "", "btrfs")

    def test_dry_run_refuses_nonempty_ordinary_root(self):
        with (
            patch.object(tree_ops, "_path_exists", return_value=(True, "")),
            patch.object(BtrfsOps, "meta", return_value=None),
            patch.object(tree_ops, "list_direct_entries", return_value=(["/cache/file"], "")),
        ):
            result = tree_ops.delete_subvolume_tree(
                self.ops,
                "/cache",
                dry_run=True,
                allow_empty_ordinary_root=True,
            )
        self.assertFalse(result.success)
        self.assertTrue(any("ordinary non-empty" in error for error in result.errors))

    def test_destination_cleanup_refuses_unexpected_nested_subvolume(self):
        root = "/target/snapshots/2026-07-15_05-00-02"
        expected = {f"{root}/@", f"{root}/@home"}
        planned = [f"{root}/@/unexpected", f"{root}/@", f"{root}/@home", root]
        with (
            patch.object(tree_ops, "_path_exists", return_value=(True, "")),
            patch.object(BtrfsOps, "meta", return_value=SubvolumeMeta(Path(root).name, root, uuid="root")),
            patch.object(tree_ops, "discover_subvolume_tree", return_value=(planned, [])),
            patch.object(tree_ops, "list_direct_entries", return_value=([f"{root}/@", f"{root}/@home", f"{root}/info.json"], "")),
            patch.object(BtrfsOps, "batch_delete") as delete,
        ):
            result = tree_ops.delete_subvolume_tree(
                self.ops,
                root,
                expected_subvolume_paths=expected,
                allowed_regular_names={"info.json"},
                refuse_unknown_entries=True,
            )
        self.assertFalse(result.success)
        self.assertTrue(any("unexpected subvolume" in error for error in result.errors))
        delete.assert_not_called()


if __name__ == "__main__":
    unittest.main()
