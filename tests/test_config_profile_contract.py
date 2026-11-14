"""Audit every complete template's real schema, optional examples and named workflow."""
from contextlib import redirect_stdout
from copy import deepcopy
from dataclasses import fields
import io
import json
from pathlib import Path
import re
import tempfile
import tomllib
import unittest
from unittest.mock import patch

from timeshift_btrfs_sync import __version__, config as cfg
from timeshift_btrfs_sync.cli import build_parser, cmd_init_config
from timeshift_btrfs_sync.paths import is_same_or_under
from timeshift_btrfs_sync.restore import BackupRepository
from timeshift_btrfs_sync.source import SourceRunner
from timeshift_btrfs_sync.topology import (
    TopologyError, describe_restore_topology, describe_sync_topology,
    reject_pull_restore_profile_for_sync,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "timeshift_btrfs_sync/data"
CONTRACTS = {
    # source mode, restore mode, backup-time auto snapshot, SSH host role
    "sync": ("ssh", "local", True, "source"),
    "remote-roundtrip": ("ssh", "ssh-target", True, "source"),
    "restore-pull": ("local", "ssh", False, "backup"),
    "local-backup": ("local", "local", True, None),
    "remote-pull": ("ssh", "local", True, "source"),
    "local-restore": ("local", "local", False, None),
    "remote-push-restore": ("ssh", "ssh-target", False, "source"),
    "remote-pull-restore": ("local", "ssh", False, "backup"),
}


def schema():
    """Reuse the loader registries and their runtime dataclasses as independent coverage checks."""
    sections = {
        "source": (cfg.SOURCE_KEYS, cfg.SourceConfig),
        "destination": (cfg.DESTINATION_KEYS, cfg.DestinationConfig),
        "stream": (cfg.STREAM_KEYS, cfg.StreamConfig),
        "retention": (cfg.RETENTION_KEYS, cfg.RetentionConfig),
        "manual_snapshot": (cfg.MANUAL_SNAPSHOT_KEYS, cfg.ManualSnapshotConfig),
        "mqtt": (cfg.MQTT_KEYS, cfg.MQTTConfig),
        "mqtt_monitor": (cfg.MONITOR_KEYS, cfg.MonitorConfig),
        "mail": (cfg.MAIL_KEYS, cfg.MailConfig),
        "ssh": (cfg.SSH_KEYS, cfg.SSHConfig),
        "restore": (cfg.RESTORE_KEYS, cfg.RestoreConfig),
    }
    return {None: (cfg.TOP_LEVEL_KEYS - set(sections), cfg.AppConfig), **sections}


def option_examples(text):
    """Parse actual/commented assignments by table; prose mentions cannot satisfy coverage."""
    registry = schema(); section = None
    found = {section: {} for section in registry}
    for line in text.splitlines():
        if match := re.fullmatch(r"\s*\[([a-z_]+)\]\s*", line):
            section = match[1]
        elif match := re.fullmatch(r"\s*(#\s*)?([a-z_]+)\s*=\s*(.+)", line):
            comment, key, value = match.groups()
            # Exclude prose such as '# local = ...' from assignment examples.
            if key in registry.get(section, (set(),))[0]:
                parsed = tomllib.loads("value = " + value)["value"]
                found[section].setdefault(key, []).append((bool(comment), parsed))
    return found


def config_text(document):
    """Encode the scalar/list/table types used by these templates for isolated loader checks."""
    lines = [key + " = " + json.dumps(value) for key, value in document.items() if not isinstance(value, dict)]
    for section, values in document.items():
        if isinstance(values, dict):
            lines += ["", "[" + section + "]"]
            lines += [key + " = " + json.dumps(value) for key, value in values.items()]
    return "\n".join(lines) + "\n"


class ConfigProfileContractTests(unittest.TestCase):
    """Keep generated and packaged configs complete, consistent and safe to start editing."""

    def profiles(self):
        """Read the actual profile registry instead of maintaining another filename list."""
        for profile, (filename, _) in cfg.CONFIG_PROFILES.items():
            path = DATA / filename
            yield profile, path, tomllib.loads(path.read_text()), cfg.load_config(path)

    def test_registry_matches_runtime_fields(self):
        """An omitted registry key or stale runtime field cannot hide from the template audit."""
        groups = schema()
        for section, (keys, model) in groups.items():
            expected = {field.name for field in fields(model)}
            if section is None: expected -= {name for name in groups if name is not None}
            with self.subTest(section=section): self.assertEqual(keys, expected)

    def test_all_templates_are_registered_and_all_profiles_have_a_contract(self):
        """Adding another template requires an explicit supported workflow and audit expectation."""
        self.assertEqual(set(cfg.CONFIG_PROFILES), set(CONTRACTS))
        self.assertEqual({p.name for p in DATA.glob("*.toml")}, {filename for filename, _ in cfg.CONFIG_PROFILES.values()})

    def test_each_supported_key_has_a_parseable_assignment_in_every_template(self):
        """Check section-specific active/optional settings, including every mail and monitor option."""
        registry = schema(); count = sum(len(keys) for keys, _ in registry.values())
        for profile, path, document, _ in self.profiles():
            examples = option_examples(path.read_text())
            for section, (keys, _) in registry.items():
                with self.subTest(profile=profile, section=section): self.assertEqual(set(examples[section]), keys)
            self.assertIn(f"All {count} supported settings", path.read_text())
            self.assertIs(document['mail']['use_mailx_util'], False)
            self.assertEqual(document['mail']['to_addr'], '')

    def test_optional_examples_load_one_at_a_time_with_coherent_credentials(self):
        """Exercise optional values through the real parser without activating conflicting examples."""
        with tempfile.TemporaryDirectory() as tmp:
            secret = Path(tmp) / "secret"; secret.write_text("fixture-only\n")
            output = Path(tmp) / "example.toml"
            for profile, path, document, _ in self.profiles():
                for section, keys in option_examples(path.read_text()).items():
                    for key, entries in keys.items():
                        for commented, example in entries:
                            if not commented: continue
                            with self.subTest(profile=profile, section=section, key=key, example=example):
                                adjusted = deepcopy(document); value = example
                                if section == "ssh":
                                    adjusted["source"]["mode"] = "ssh"  # Validate optional SSH even for local profiles.
                                    if key in {"password", "password_file", "identity_passphrase", "identity_passphrase_file"}:
                                        adjusted["ssh"]["extra_args"] = ["-o", "NumberOfPasswordPrompts=1"]
                                    if key in {"identity_passphrase", "identity_passphrase_file"}:
                                        adjusted["ssh"]["identity_file"] = str(Path(tmp) / "identity")
                                if key.endswith("password_file") or key == "identity_passphrase_file": value = str(secret)
                                if section is None: adjusted[key] = value
                                else: adjusted[section][key] = value
                                output.write_text(config_text(adjusted))
                                loaded = cfg.load_config(output)
                                selected = getattr(loaded if section is None else getattr(loaded, section), key)
                                if isinstance(selected, Path): selected = str(selected)
                                self.assertEqual(selected, value)

    def test_workflow_modes_and_ssh_host_role_match_profile_names(self):
        """Local backup/restore, SSH pull and SSH push select the intended hosts."""
        for profile, _, _, options in self.profiles():
            source_mode, restore_mode, manual, host = CONTRACTS[profile]
            with self.subTest(profile=profile):
                self.assertEqual(options.source.mode, source_mode)
                self.assertEqual(options.restore.mode, restore_mode)
                self.assertEqual(options.manual_snapshot.enabled, manual)
                if host is None: self.assertIsNone(options.ssh)
                else:
                    self.assertEqual(options.ssh.host, host + "-machine.example.lan")
                    self.assertEqual(options.ssh.user, 'ts-btrfs-restore-user' if host == 'backup' else 'ts-btrfs-sync-user')

    def test_real_endpoint_constructors_agree_with_the_profile_topology(self):
        """Use actual endpoint factories without running SSH, Btrfs or Timeshift commands."""
        with patch.object(SourceRunner, "run", side_effect=AssertionError("audit must not run endpoint commands")):
            for profile, _, _, options in self.profiles():
                with self.subTest(profile=profile):
                    source_mode, restore_mode, _, _ = CONTRACTS[profile]
                    self.assertEqual(SourceRunner.from_config(options).uses_ssh, source_mode == 'ssh')
                    repository = BackupRepository.from_config(options)
                    self.assertEqual(repository.runner.uses_ssh, restore_mode == 'ssh')
                    self.assertEqual(repository.root, str(options.destination.target_root))
                    timeshift = SourceRunner.from_mode('ssh' if options.restore.timeshift_uses_ssh else 'local', options.ssh)
                    self.assertEqual(timeshift.uses_ssh, restore_mode == 'ssh-target')

    def test_pull_restore_profiles_still_refuse_sync(self):
        """A remote-backup restore example cannot silently create the wrong local repository."""
        for profile, _, _, options in self.profiles():
            with self.subTest(profile=profile):
                if CONTRACTS[profile][1] == 'ssh':
                    with self.assertRaises(TopologyError): reject_pull_restore_profile_for_sync(options)
                else: reject_pull_restore_profile_for_sync(options)

    def test_all_path_examples_are_absolute_and_metadata_stays_with_backup(self):
        """Match state to its backup repository while preserving local lock/log examples."""
        for profile, _, _, options in self.profiles():
            with self.subTest(profile=profile):
                for path in [options.source.snapshot_root, options.source.cache_root, options.destination.target_root,
                             options.state_file, options.lock_file, options.log_dir]:
                    self.assertTrue(Path(path).is_absolute())
                self.assertEqual(options.state_file, options.destination.target_root / '.ts-btrfs-sync/state.json')
                self.assertNotEqual(options.lock_file, options.state_file)
                self.assertFalse(is_same_or_under(options.source.cache_root, options.source.snapshot_root))
                if options.source.mode == 'local' and options.restore.mode != 'ssh':
                    for protected in [options.source.snapshot_root, options.source.cache_root]:
                        self.assertFalse(is_same_or_under(str(options.destination.target_root), protected))
                        self.assertFalse(is_same_or_under(protected, str(options.destination.target_root)))

    def test_backup_and_restore_lock_examples_match_the_running_host_role(self):
        """Backup locks follow local backup metadata; restore-only configs use explicit local locks."""
        for profile, _, document, options in self.profiles():
            with self.subTest(profile=profile):
                if CONTRACTS[profile][2]:
                    self.assertEqual(options.lock_file, options.destination.target_root / '.ts-btrfs-sync/lock')
                else:
                    self.assertIn('lock_file', document)
                    self.assertEqual(options.lock_file.name, 'restore.lock')
                    self.assertIn('local lock parent', (DATA / cfg.CONFIG_PROFILES[profile][0]).read_text())

    def test_safety_and_notification_defaults_remain_consistent(self):
        """Completeness does not activate real runs, new alerts or unsafe deletion options."""
        for profile, _, _, options in self.profiles():
            with self.subTest(profile=profile):
                self.assertTrue(options.default_dry_run); self.assertFalse(options.prune_after_sync)
                self.assertTrue(options.retention.keep_latest); self.assertTrue(options.retention.keep_latest_common_parent)
                self.assertFalse(options.retention.cleanup_ondemand)
                self.assertTrue(options.source.cleanup_superseded_cache)
                self.assertTrue(options.source.delete_redundant_snapshots)
                self.assertTrue(options.destination.delete_redundant_snapshots)
                self.assertFalse(options.mail.enabled); self.assertFalse(options.mail.use_mailx_util)
                self.assertFalse(options.mqtt.enabled); self.assertFalse(options.mqtt_monitor.enabled)
                self.assertTrue(options.mqtt_monitor.measure_transfers)
                self.assertFalse(options.stream.transfer_size_check)
                self.assertEqual(options.stream.transfer_size_mode, 'estimate')

    def test_credentials_stay_optional_and_disabled_ssh_examples_are_coherent(self):
        """No template activates secrets or incompatible password/BatchMode/ControlMaster settings."""
        for profile, _, document, _ in self.profiles():
            with self.subTest(profile=profile):
                for section in ['ssh', 'mqtt', 'mail']:
                    for key in ['password', 'password_file', 'identity_passphrase', 'identity_passphrase_file']:
                        self.assertNotIn(key, document[section])
                self.assertEqual(document['ssh']['extra_args'], ['-o', 'BatchMode=yes'])
                self.assertFalse(document['ssh']['control_master'])
                self.assertFalse(document['mail']['smtp_ssl']); self.assertTrue(document['mail']['starttls'])

    def test_headers_and_flag_comments_match_actual_settings(self):
        """Make profiles and mail setting locations visible, with no inverted enabled semantics."""
        for profile, path, _, _ in self.profiles():
            with self.subTest(profile=profile):
                text = path.read_text()
                self.assertIn(f'v{__version__}', text.splitlines()[0])
                self.assertIn(f'# Profile: {profile}.', text)
                self.assertIn('Mailx options use_mailx_util and to_addr are in the [mail] section.', text)
                self.assertNotIn('When enabled = false, `sync` may create', text)
                self.assertIn('When enabled = true, `sync` may create', text)

    def test_default_and_all_generated_profiles_match_current_packaged_resources(self):
        """Both default config.example generation and every named profile receive all current settings."""
        with tempfile.TemporaryDirectory() as tmp:
            for profile in [None, *cfg.CONFIG_PROFILES]:
                output = Path(tmp) / ((profile or 'default')+'.toml')
                command = ['init-config', '--path', str(output)]
                if profile: command += ['--profile', profile]
                args = build_parser().parse_args(command)
                with redirect_stdout(io.StringIO()): self.assertEqual(cmd_init_config(args), 0)
                expected = DATA / cfg.CONFIG_PROFILES[profile or 'sync'][0]
                self.assertEqual(output.read_bytes(), expected.read_bytes())
                self.assertEqual(option_examples(output.read_text()), option_examples(expected.read_text()))
