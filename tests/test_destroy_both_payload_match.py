from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from timeshift_btrfs_sync import destroy
from timeshift_btrfs_sync.config import SourceConfig, load_config
from timeshift_btrfs_sync.tree_ops import TreeDeleteResult


SNAPSHOT = "2026-07-17_14-04-41"


class DestroyBothPayloadMatchTests(unittest.TestCase):
    def _config(self, directory: str, mode: str):
        template = (
            Path(__file__).parents[1]
            / "timeshift_btrfs_sync"
            / "data"
            / "config.example.toml"
        )
        text = template.read_text(encoding="utf-8")
        text = text.replace('\nmode = "ssh"', f'\nmode = "{mode}"', 1)
        path = Path(directory) / f"config-{mode}.toml"
        path.write_text(text, encoding="utf-8")
        config = load_config(path)
        config.source.cache_root = f"/srv/source-{mode}/send-cache"
        config.destination.target_root = Path(f"/srv/destination-{mode}")
        return config

    @staticmethod
    def _successful_tree(root: str, planned: list[str], endpoint: str) -> TreeDeleteResult:
        return TreeDeleteResult(
            root=root,
            endpoint=endpoint,
            existed=True,
            planned=planned,
            confirmed=list(planned),
            verified_root_absent=True,
        )

    def test_delete_both_completes_payload_comparison_for_local_and_ssh_sources(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for mode, expected_source_location in (("local", "local"), ("ssh", "remote")):
                with self.subTest(mode=mode):
                    config = self._config(directory, mode)
                    cache_root = str(config.source.cache_root)
                    destination_root = str(config.destination.target_root)
                    source_plan = [
                        f"{cache_root}/{SNAPSHOT}/@home",
                        f"{cache_root}/{SNAPSHOT}/@",
                        f"{cache_root}/{SNAPSHOT}",
                        cache_root,
                    ]
                    destination_plan = [
                        f"{destination_root}/snapshots/{SNAPSHOT}/@home",
                        f"{destination_root}/snapshots/{SNAPSHOT}/@",
                        f"{destination_root}/snapshots/{SNAPSHOT}",
                        f"{destination_root}/snapshots",
                        destination_root,
                    ]
                    endpoint_locations: list[str] = []

                    def fake_delete(ops, root, **_kwargs):
                        endpoint_locations.append(ops.endpoint.location)
                        if str(root) == cache_root:
                            return self._successful_tree(cache_root, source_plan, expected_source_location)
                        if str(root) == destination_root:
                            return self._successful_tree(destination_root, destination_plan, "local")
                        raise AssertionError(f"unexpected tree root: {root}")

                    output = io.StringIO()
                    with (
                        patch.object(destroy, "delete_subvolume_tree", side_effect=fake_delete),
                        patch.object(destroy, "_load_payload_state", return_value=None),
                        redirect_stdout(output),
                    ):
                        results = destroy.destroy_leftovers(
                            config,
                            delete_source=True,
                            delete_destination=True,
                            dry_run=False,
                            danger_confirmed=True,
                            interactive=False,
                        )

                    rendered = output.getvalue()
                    self.assertEqual(len(results), 2)
                    self.assertEqual(endpoint_locations, [expected_source_location, "local"])
                    self.assertIn("SOURCE / DESTINATION SNAPSHOT MATCH", rendered)
                    self.assertIn("OK - source send payload matches destination received payload", rendered)
                    self.assertIn("complete:   2", rendered)
                    self.assertIn("incomplete: 0", rendered)

    def test_every_destroy_source_config_attribute_exists(self) -> None:
        # Regression guard for cleanup/refactor mistakes such as the removed
        # SourceConfig.tree attribute that remained in destroy payload reporting.
        self.assertIn("subvolumes", SourceConfig.__dataclass_fields__)
        self.assertNotIn("tree", SourceConfig.__dataclass_fields__)
        source = Path("timeshift_btrfs_sync/destroy.py").read_text(encoding="utf-8")
        self.assertNotIn("config.source.tree", source)
        self.assertEqual(source.count("config.source.subvolumes"), 3)


if __name__ == "__main__":
    unittest.main()
