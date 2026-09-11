from __future__ import annotations

import ast
import unittest
from pathlib import Path

from timeshift_btrfs_sync import config as config_module


class ConfigAttributeSurfaceTests(unittest.TestCase):
    def test_runtime_config_section_attributes_exist(self) -> None:
        """Catch stale config attributes left behind by refactors."""

        sections = {
            "source": config_module.SourceConfig,
            "destination": config_module.DestinationConfig,
            "stream": config_module.StreamConfig,
            "retention": config_module.RetentionConfig,
            "manual_snapshot": config_module.ManualSnapshotConfig,
            "mqtt": config_module.MQTTConfig,
            "mail": config_module.MailConfig,
            "ssh": config_module.SSHConfig,
        }
        allowed = {
            name: set(cls.__dataclass_fields__)
            | {attribute for attribute in dir(cls) if not attribute.startswith("_")}
            for name, cls in sections.items()
        }
        invalid: list[str] = []
        checked = 0
        package = Path(__file__).parents[1] / "timeshift_btrfs_sync"
        for path in sorted(package.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Attribute):
                    continue
                section_access = node.value
                if not (
                    isinstance(section_access, ast.Attribute)
                    and isinstance(section_access.value, ast.Name)
                    and section_access.value.id == "config"
                    and section_access.attr in sections
                ):
                    continue
                checked += 1
                if node.attr not in allowed[section_access.attr]:
                    invalid.append(
                        f"{path.name}:{node.lineno}: config.{section_access.attr}.{node.attr}"
                    )
        self.assertGreater(checked, 0)
        self.assertEqual(invalid, [])


if __name__ == "__main__":
    unittest.main()
