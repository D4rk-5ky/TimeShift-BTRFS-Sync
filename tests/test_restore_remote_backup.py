from __future__ import annotations

import base64
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from timeshift_btrfs_sync import restore
from timeshift_btrfs_sync.commands import Completed
from timeshift_btrfs_sync.config import load_config
from timeshift_btrfs_sync.endpoint import CommandEndpoint
from timeshift_btrfs_sync.models import SubvolumeMeta
from timeshift_btrfs_sync.source import SourceRunner


SNAPSHOT = "2026-07-15_05-00-02"
INFO = '{"sys-uuid":"root-uuid","sys-distro":"Ubuntu","type":"btrfs","tags":"D"}\n'


class FakeRunner:
    def __init__(self, *, ssh: bool, listed: list[str] | None = None):
        self.uses_ssh = ssh
        self.location = "remote" if ssh else "local"
        self.listed = listed or []
        self.calls: list[str] = []

    def command(self, shell_command: str) -> list[str]:
        return ["ssh", "backup", shell_command] if self.uses_ssh else ["sh", "-c", shell_command]

    def run(self, shell_command: str, **_kwargs) -> Completed:
        self.calls.append(shell_command)
        if "timeshift" in shell_command and "--list" in shell_command:
            return Completed(0, "\n".join(f"{name} D restored" for name in self.listed) + "\n", "")
        if "cat" in shell_command and "info.json" in shell_command:
            return Completed(0, INFO, "")
        return Completed(0, "", "")

    def environment(self):
        return {"SSHPASS": "backup-secret"} if self.uses_ssh else None


class FakeEndpoint:
    def __init__(self, output: str):
        self.output = output
        self.scripts: list[str] = []

    def run_shell(self, script: str, **_kwargs) -> Completed:
        self.scripts.append(script)
        return Completed(0, self.output, "")


class RemoteBackupRestoreTests(unittest.TestCase):
    def make_config(self, root: Path):
        return SimpleNamespace(
            name="remote-pull-restore",
            state_file=Path("/remote/backup/.ts-btrfs-sync/state.json"),
            lock_file=root / "restore-lock" / "lock",
            ssh=SimpleNamespace(),
            source=SimpleNamespace(
                mode="local",
                snapshot_root="/local/timeshift-btrfs/snapshots",
                cache_root="/local/timeshift-btrfs/.ts-btrfs-sync/send-cache",
                subvolumes=["@", "@home"],
                sudo="sudo -n",
                btrfs_command="btrfs",
                timeshift_command="timeshift",
            ),
            destination=SimpleNamespace(
                target_root=Path("/remote/backup"),
                sudo="sudo -n",
                btrfs_command="btrfs",
            ),
            stream=SimpleNamespace(btrfs_verbose=False, command=lambda: None),
            restore=SimpleNamespace(mode="ssh", backup_uses_ssh=True, timeshift_uses_ssh=False),
        )

    def plan(self) -> restore.RestorePlan:
        root = "/remote/backup/snapshots/" + SNAPSHOT
        backup = restore.BackupSnapshot(
            SNAPSHOT,
            root,
            INFO,
            {
                "@": SubvolumeMeta("@", root + "/@", uuid="backup-root", received_uuid="send-root", readonly=True),
                "@home": SubvolumeMeta("@home", root + "/@home", uuid="backup-home", received_uuid="send-home", readonly=True),
            },
            restore.TimeshiftOsIdentity("root-uuid", "btrfs", "Ubuntu"),
        )
        return restore.RestorePlan(
            backups={SNAPSHOT: backup},
            chain_names=[SNAPSHOT],
            restore_names=[SNAPSHOT],
            common_parent=None,
            common_reason="single",
            no_common_parent=False,
            backup_identity=backup.os_identity,
            os_identity_match=True,
            os_identity_reason="matched",
        )

    def source_meta(self, _ops, path, *, name=None, required=True):
        text = str(path)
        payload = name or Path(text).name
        second = "2026-07-15_06-00-02"
        if "restore-chain-" in text:
            suffix = "-2" if f"/{second}/" in text else ""
            received_base = "send-root" if payload == "@" else "send-home"
            return SubvolumeMeta(
                payload,
                text,
                uuid="hidden-" + payload + suffix,
                received_uuid=received_base + suffix,
                readonly=True,
            )
        if ".ts-btrfs-sync-restore-" in text or text.endswith(f"/{SNAPSHOT}/{payload}") or text.endswith(f"/{second}/{payload}"):
            suffix = "-2" if second in text else ""
            return SubvolumeMeta(payload, text, parent_uuid="hidden-" + payload + suffix, readonly=False)
        return None

    def test_remote_backup_streams_ssh_send_into_local_receive(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.make_config(Path(directory))
            plan = self.plan()
            backup_runner = FakeRunner(ssh=True)
            repository = restore.BackupRepository(
                config,
                backup_runner,
                CommandEndpoint.for_source(backup_runner),
                restore.BtrfsOps(CommandEndpoint.for_source(backup_runner), "sudo -n", "btrfs"),
            )
            source_runner = FakeRunner(ssh=False, listed=[SNAPSHOT])
            pipelines = []

            def capture(left, right, **kwargs):
                pipelines.append((left, right, kwargs))

            with (
                patch.object(restore.BackupRepository, "from_config", return_value=repository),
                patch.object(restore.SourceRunner, "from_mode", return_value=source_runner),
                patch.object(restore, "_build_restore_plan", return_value=(plan, {}, "")),
                patch.object(restore, "_source_path_exists", return_value=(False, "")),
                patch.object(restore.BtrfsOps, "meta", autospec=True, side_effect=self.source_meta),
                patch.object(restore.BtrfsOps, "snapshot", return_value=Completed(0, "", "")),
                patch.object(restore, "stream_pipeline", side_effect=capture),
                patch.object(restore, "_write_source_info_json"),
                patch.object(restore, "_cleanup_restore_attempt", return_value=[]),
                patch("builtins.input", side_effect=[
                    restore.RESTORE_RETENTION_CONFIRMATION,
                    "RESTORE SNAPSHOT",
                    SNAPSHOT,
                ]),
            ):
                restore.restore_backups(
                    config,
                    snapshot_name=SNAPSHOT,
                    restore_all=False,
                    dry_run=False,
                    danger_confirmed=True,
                    allow_no_common_parent=False,
                )

        self.assertEqual(len(pipelines), 2)
        for left, right, kwargs in pipelines:
            self.assertEqual(left[:2], ["ssh", "backup"])
            self.assertIn("btrfs send", left[-1])
            self.assertEqual(right[:2], ["sh", "-c"])
            self.assertIn("btrfs receive", right[-1])
            self.assertEqual(kwargs["left_env"], {"SSHPASS": "backup-secret"})
            self.assertIsNone(kwargs["right_env"])
            self.assertEqual(kwargs["left_label"], "REMOTE BACKUP SEND")
            self.assertEqual(kwargs["right_label"], "LOCAL TIMESHIFT RECEIVE")


    def test_remote_backup_all_uses_remote_incremental_parent_paths(self):
        second = "2026-07-15_06-00-02"
        with tempfile.TemporaryDirectory() as directory:
            config = self.make_config(Path(directory))
            first = self.plan().backups[SNAPSHOT]
            second_root = "/remote/backup/snapshots/" + second
            second_backup = restore.BackupSnapshot(
                second,
                second_root,
                INFO,
                {
                    "@": SubvolumeMeta("@", second_root + "/@", uuid="backup-root-2", received_uuid="send-root-2", readonly=True),
                    "@home": SubvolumeMeta("@home", second_root + "/@home", uuid="backup-home-2", received_uuid="send-home-2", readonly=True),
                },
                restore.TimeshiftOsIdentity("root-uuid", "btrfs", "Ubuntu"),
            )
            plan = restore.RestorePlan(
                backups={SNAPSHOT: first, second: second_backup},
                chain_names=[SNAPSHOT, second],
                restore_names=[SNAPSHOT, second],
                common_parent=None,
                common_reason="none",
                no_common_parent=True,
                backup_identity=first.os_identity,
                os_identity_match=True,
                os_identity_reason="matched",
            )
            backup_runner = FakeRunner(ssh=True)
            repository = restore.BackupRepository(
                config,
                backup_runner,
                CommandEndpoint.for_source(backup_runner),
                restore.BtrfsOps(CommandEndpoint.for_source(backup_runner), "sudo -n", "btrfs"),
            )
            source_runner = FakeRunner(ssh=False, listed=[SNAPSHOT, second])
            pipelines = []

            def capture(left, right, **kwargs):
                pipelines.append((left, right, kwargs))

            with (
                patch.object(restore.BackupRepository, "from_config", return_value=repository),
                patch.object(restore.SourceRunner, "from_mode", return_value=source_runner),
                patch.object(restore, "_build_restore_plan", return_value=(plan, {}, "")),
                patch.object(restore, "_source_path_exists", return_value=(False, "")),
                patch.object(restore.BtrfsOps, "meta", autospec=True, side_effect=self.source_meta),
                patch.object(restore.BtrfsOps, "snapshot", return_value=Completed(0, "", "")),
                patch.object(restore, "stream_pipeline", side_effect=capture),
                patch.object(restore, "_write_source_info_json"),
                patch.object(restore, "_cleanup_restore_attempt", return_value=[]),
                patch("builtins.input", side_effect=[
                    restore.RESTORE_RETENTION_CONFIRMATION,
                    "RESTORE ALL WITHOUT COMMON PARENT",
                    config.name,
                ]),
            ):
                restore.restore_backups(
                    config,
                    snapshot_name=None,
                    restore_all=True,
                    dry_run=False,
                    danger_confirmed=True,
                    allow_no_common_parent=True,
                )

        self.assertEqual(len(pipelines), 4)
        first_commands = [left[-1] for left, _right, _kwargs in pipelines[:2]]
        second_commands = [left[-1] for left, _right, _kwargs in pipelines[2:]]
        self.assertTrue(all(" -p " not in command for command in first_commands))
        self.assertIn(f"-p /remote/backup/snapshots/{SNAPSHOT}/@", second_commands[0])
        self.assertIn(f"-p /remote/backup/snapshots/{SNAPSHOT}/@home", second_commands[1])
        self.assertTrue(all(left[:2] == ["ssh", "backup"] for left, _right, _kwargs in pipelines))
        self.assertTrue(all(right[:2] == ["sh", "-c"] for _left, right, _kwargs in pipelines))

    def test_remote_backup_mode_ignores_sync_source_mode_and_targets_local_timeshift(self):
        config = self.make_config(Path("/tmp"))
        config.source.mode = "ssh"
        repository = SimpleNamespace(runner=SimpleNamespace(uses_ssh=True))
        target = FakeRunner(ssh=False)
        with (
            patch.object(restore.BackupRepository, "from_config", return_value=repository),
            patch.object(restore.SourceRunner, "from_mode", return_value=target) as from_mode,
            patch.object(restore, "_build_restore_plan", side_effect=restore.RestoreError("stop")),
        ):
            with self.assertRaisesRegex(restore.RestoreError, "stop"):
                restore.restore_backups(
                    config,
                    snapshot_name=SNAPSHOT,
                    restore_all=False,
                    dry_run=True,
                    danger_confirmed=False,
                    allow_no_common_parent=False,
                )
        from_mode.assert_called_once_with("local", config.ssh)

    def test_pull_restore_indexes_snapshot_and_cache_on_local_timeshift_runner(self):
        config = self.make_config(Path("/tmp"))
        timeshift_runner = FakeRunner(ssh=False)
        inventory = restore.SourceInventory(
            "",
            restore.BtrfsIndex(config.source.snapshot_root, "local"),
            restore.BtrfsIndex(config.source.cache_root, "local"),
        )
        with (
            patch.object(restore, "build_source_inventory", return_value=inventory) as build_inventory,
            patch.object(restore, "list_source_snapshots", return_value=[]),
        ):
            snapshots, built = restore._timeshift_snapshots(config, timeshift_runner)

        self.assertEqual(snapshots, {})
        self.assertIs(built, inventory)
        build_inventory.assert_called_once_with(
            timeshift_runner,
            snapshot_root=config.source.snapshot_root,
            cache_root=config.source.cache_root,
            sudo=config.source.sudo,
            btrfs_command=config.source.btrfs_command,
            timeshift_command=config.source.timeshift_command,
            required=True,
        )

    def test_pull_restore_exact_parent_probe_uses_local_timeshift_cache_path(self):
        config = self.make_config(Path("/tmp"))
        cache_path = f"{config.source.cache_root}/{SNAPSHOT}/@"
        state = {
            "snapshots": {
                SNAPSHOT: {
                    "subvolumes": {
                        "@": {
                            "send_path": f"{SNAPSHOT}/@",
                            "send_path_kind": "source-cache",
                            "send_source_uuid": "send-root",
                        },
                        "@home": {
                            "send_path": f"{SNAPSHOT}/@home",
                            "send_path_kind": "source-cache",
                            "send_source_uuid": "send-home",
                        },
                    }
                }
            }
        }
        inventory = restore.SourceInventory(
            "",
            restore.BtrfsIndex(config.source.snapshot_root, "local"),
            restore.BtrfsIndex(config.source.cache_root, "local"),
        )

        class CapturingOps:
            def __init__(self):
                self.paths = []

            def meta(self, path, *, name=None, required=False):
                self.paths.append(str(path))
                uuid = "send-root" if name == "@" else "send-home"
                return SubvolumeMeta(name or Path(path).name, str(path), uuid=uuid, readonly=True)

        ops = CapturingOps()
        paths, reason = restore._find_reusable_receive_parent(
            config, ops, inventory, state, SNAPSHOT
        )

        self.assertEqual(paths["@"], cache_path)
        self.assertEqual(
            ops.paths,
            [
                f"{config.source.cache_root}/{SNAPSHOT}/@",
                f"{config.source.cache_root}/{SNAPSHOT}/@home",
            ],
        )
        self.assertTrue(all(path.startswith(config.source.cache_root) for path in ops.paths))
        self.assertTrue(all(not path.startswith(str(config.destination.target_root)) for path in ops.paths))
        self.assertIn("Timeshift filesystem", reason)

    def test_remote_backup_scan_never_uses_local_timeshift_cache_root(self):
        encoded = base64.b64encode(INFO.encode()).decode()
        output = "\n".join([
            f"TSBTRFS_BACKUP_DATE\t{SNAPSHOT}\tdirectory",
            f"TSBTRFS_BACKUP_ENTRY\t{SNAPSHOT}\t@\tdirectory",
            f"TSBTRFS_BACKUP_ENTRY\t{SNAPSHOT}\t@home\tdirectory",
            f"TSBTRFS_BACKUP_ENTRY\t{SNAPSHOT}\tinfo.json\tfile",
            f"TSBTRFS_BACKUP_INFO\t{SNAPSHOT}\t{encoded}",
        ]) + "\n"
        config = self.make_config(Path("/tmp"))
        runner = FakeRunner(ssh=True)
        endpoint = FakeEndpoint(output)
        repository = restore.BackupRepository(config, runner, endpoint, SimpleNamespace())
        repository.scan_directories()
        self.assertEqual(len(endpoint.scripts), 1)
        self.assertIn("/remote/backup/snapshots", endpoint.scripts[0])
        self.assertNotIn(config.source.snapshot_root, endpoint.scripts[0])
        self.assertNotIn(config.source.cache_root, endpoint.scripts[0])

    def test_remote_backup_scan_reads_entries_and_info_in_one_command(self):
        encoded = base64.b64encode(INFO.encode()).decode()
        output = "\n".join([
            f"TSBTRFS_BACKUP_DATE\t{SNAPSHOT}\tdirectory",
            f"TSBTRFS_BACKUP_ENTRY\t{SNAPSHOT}\t@\tdirectory",
            f"TSBTRFS_BACKUP_ENTRY\t{SNAPSHOT}\t@home\tdirectory",
            f"TSBTRFS_BACKUP_ENTRY\t{SNAPSHOT}\tinfo.json\tfile",
            f"TSBTRFS_BACKUP_INFO\t{SNAPSHOT}\t{encoded}",
        ]) + "\n"
        config = self.make_config(Path("/tmp"))
        runner = FakeRunner(ssh=True)
        endpoint = FakeEndpoint(output)
        repository = restore.BackupRepository(config, runner, endpoint, SimpleNamespace())
        records = repository.scan_directories()
        self.assertEqual(records[SNAPSHOT].entries, {"@": "directory", "@home": "directory", "info.json": "file"})
        self.assertEqual(records[SNAPSHOT].info_content, INFO)
        self.assertEqual(len(endpoint.scripts), 1)
        self.assertIn("/remote/backup/snapshots", endpoint.scripts[0])

    def test_remote_backup_state_is_read_and_validated_on_backup_endpoint(self):
        output = 'TSBTRFS_STATE_BEGIN\n{"version":3,"snapshots":{}}\nTSBTRFS_STATE_END\n'
        config = self.make_config(Path("/tmp"))
        runner = FakeRunner(ssh=True)
        endpoint = FakeEndpoint(output)
        repository = restore.BackupRepository(config, runner, endpoint, SimpleNamespace())
        self.assertEqual(repository.load_state(), {"version": 3, "snapshots": {}})
        self.assertIn("/remote/backup/.ts-btrfs-sync/state.json", endpoint.scripts[0])

    def test_restore_mode_ssh_loads_ssh_even_when_sync_source_mode_is_local(self):
        template = Path("timeshift_btrfs_sync/data/config.restore-pull.example.toml").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "restore.toml"
            path.write_text(template, encoding="utf-8")
            config = load_config(path)
        self.assertEqual(config.source.mode, "local")
        self.assertEqual(config.restore.mode, "ssh")
        self.assertIsNotNone(config.ssh)


    def test_real_pull_restore_uses_local_process_lock(self):
        from timeshift_btrfs_sync import cli

        with tempfile.TemporaryDirectory() as directory:
            config = self.make_config(Path(directory))
            config.lock_file.parent.mkdir(parents=True)
            lock_events: list[tuple[str, Path]] = []

            class FakeLock:
                def __init__(self, path):
                    self.path = Path(path)

                def __enter__(self):
                    lock_events.append(("enter", self.path))
                    return self

                def __exit__(self, exc_type, exc, tb):
                    lock_events.append(("exit", self.path))

            args = SimpleNamespace(
                config="restore.toml",
                snapshot=None,
                restore_all=True,
                allow_no_common_parent=False,
                allow_os_identity_mismatch=False,
                i_understand_this_modifies_timeshift=True,
                create_pre_restore_snapshot=True,
                dry_run=False,
                run=True,
            )
            with (
                patch.object(cli, "load_config", return_value=config) as load,
                patch.object(cli, "FileLock", FakeLock),
                patch.object(cli, "SourceRunner") as runner_type,
                patch.object(cli.CommandEndpoint, "for_source") as endpoint_factory,
                patch.object(cli, "restore_backups") as restore_call,
                patch.object(cli, "_with_logging", side_effect=lambda _config, _name, fn: fn()),
                patch("builtins.print") as output,
            ):
                result = cli.cmd_restore(args)

        self.assertEqual(result, 0)
        self.assertEqual(lock_events, [("enter", config.lock_file), ("exit", config.lock_file)])
        load.assert_called_once_with("restore.toml")
        runner_type.from_mode.assert_not_called()
        endpoint_factory.assert_not_called()
        restore_call.assert_called_once()
        self.assertTrue(restore_call.call_args.kwargs["create_pre_restore_snapshot"])
        output.assert_any_call(f"Acquiring local restore lock: {config.lock_file}")

    def test_pull_restore_does_not_require_remote_lock_directory(self):
        from timeshift_btrfs_sync import cli

        with tempfile.TemporaryDirectory() as directory:
            config = self.make_config(Path(directory))
            config.lock_file.parent.mkdir(parents=True)

            args = SimpleNamespace(
                config="restore.toml",
                snapshot=None,
                restore_all=True,
                allow_no_common_parent=False,
                allow_os_identity_mismatch=False,
                i_understand_this_modifies_timeshift=True,
                create_pre_restore_snapshot=False,
                dry_run=False,
                run=True,
            )
            with (
                patch.object(cli, "load_config", return_value=config),
                patch.object(cli, "FileLock"),
                patch.object(cli, "SourceRunner") as runner_type,
                patch.object(cli.CommandEndpoint, "for_source") as endpoint_factory,
                patch.object(cli, "restore_backups"),
                patch.object(cli, "_with_logging", side_effect=lambda _config, _name, fn: fn()),
            ):
                result = cli.cmd_restore(args)

        self.assertEqual(result, 0)
        runner_type.from_mode.assert_not_called()
        endpoint_factory.assert_not_called()

    def test_restore_refuses_missing_local_lock_directory(self):
        from timeshift_btrfs_sync import cli

        with tempfile.TemporaryDirectory() as directory:
            config = self.make_config(Path(directory))
            args = SimpleNamespace(
                config="restore.toml",
                snapshot=None,
                restore_all=True,
                allow_no_common_parent=False,
                allow_os_identity_mismatch=False,
                i_understand_this_modifies_timeshift=True,
                create_pre_restore_snapshot=False,
                dry_run=False,
                run=True,
            )
            with (
                patch.object(cli, "load_config", return_value=config),
                patch.object(cli, "restore_backups"),
            ):
                with self.assertRaisesRegex(RuntimeError, "configured local lock directory"):
                    cli.cmd_restore(args)

    def test_restore_cli_uses_config_selected_transport(self):
        from timeshift_btrfs_sync.cli import build_parser

        args = build_parser().parse_args([
            "restore", "--config", "restore.toml", "--all", "--dry-run"
        ])
        self.assertEqual(args.config, "restore.toml")


if __name__ == "__main__":
    unittest.main()
