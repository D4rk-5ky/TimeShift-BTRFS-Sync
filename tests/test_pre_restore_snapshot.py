from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from timeshift_btrfs_sync import restore
from timeshift_btrfs_sync.commands import Completed, CommandError
from timeshift_btrfs_sync.models import SubvolumeMeta


EXISTING = "2026-07-15_05-00-02"
CREATED = "2026-07-19_08-30-00"
RESTORE_DATE = "2026-07-15_06-00-02"
INFO = '{"sys-uuid":"root-uuid","type":"btrfs"}\n'


class FakeTargetSource:
    def __init__(self, *, remote: bool, create_error: bool = False):
        self.uses_ssh = remote
        self.location = "remote" if remote else "local"
        self.create_error = create_error
        self.created = False
        self.calls: list[str] = []

    def command(self, shell_command: str) -> list[str]:
        return ["ssh", "timeshift-target", shell_command] if self.uses_ssh else ["sh", "-c", shell_command]

    def run(self, shell_command: str, **_kwargs) -> Completed:
        self.calls.append(shell_command)
        if "--create" in shell_command:
            if self.create_error:
                raise CommandError(self.command(shell_command), 1, "", "create failed")
            self.created = True
            return Completed(0, "", "")
        if "--list" in shell_command:
            lines = [f"{EXISTING} O existing"]
            if self.created:
                lines.append(f"{CREATED} O {restore.PRE_RESTORE_SNAPSHOT_COMMENT}")
            return Completed(0, "\n".join(lines) + "\n", "")
        return Completed(0, "", "")

    def environment(self):
        return {"SSHPASS": "target-secret"} if self.uses_ssh else None


class FakeOps:
    def __init__(self):
        self.paths: list[str] = []

    def meta(self, path, *, name=None, required=True):
        self.paths.append(str(path))
        return SubvolumeMeta(name or Path(path).name, str(path), uuid=f"uuid-{name}", readonly=False)


class PreRestoreSnapshotTests(unittest.TestCase):
    def make_config(self, *, source_mode: str):
        return SimpleNamespace(
            name="restore-test",
            source=SimpleNamespace(
                mode=source_mode,
                snapshot_root="/timeshift-btrfs/snapshots",
                subvolumes=["@", "@home"],
                sudo="sudo -n",
                btrfs_command="btrfs",
                timeshift_command="timeshift",
            ),
        )

    def test_shared_helper_creates_and_verifies_snapshot_on_local_and_ssh_targets(self):
        for remote in (False, True):
            with self.subTest(remote=remote):
                source = FakeTargetSource(remote=remote)
                ops = FakeOps()
                created = restore._create_pre_restore_snapshot(
                    self.make_config(source_mode="ssh" if remote else "local"),
                    source,
                    ops,
                    existing_names={EXISTING},
                    restore_names=[RESTORE_DATE],
                )
                self.assertEqual(created, CREATED)
                self.assertTrue(any("timeshift --create" in command for command in source.calls))
                self.assertTrue(any("timeshift --list" in command for command in source.calls))
                self.assertEqual(
                    ops.paths,
                    [
                        f"/timeshift-btrfs/snapshots/{CREATED}/@",
                        f"/timeshift-btrfs/snapshots/{CREATED}/@home",
                    ],
                )

    def test_failed_safety_snapshot_aborts_before_any_restore_stream(self):
        source = FakeTargetSource(remote=False, create_error=True)
        with self.assertRaisesRegex(restore.RestoreError, "No backup stream has started"):
            restore._create_pre_restore_snapshot(
                self.make_config(source_mode="local"),
                source,
                FakeOps(),
                existing_names={EXISTING},
                restore_names=[RESTORE_DATE],
            )

    def test_pull_restore_uses_local_timeshift_target_not_remote_backup_for_safety_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "backup"
            backup_path = target / "snapshots" / RESTORE_DATE
            backup = restore.BackupSnapshot(
                RESTORE_DATE,
                str(backup_path),
                INFO,
                {
                    "@": SubvolumeMeta("@", str(backup_path / "@"), uuid="backup-root", received_uuid="send-root", readonly=True),
                    "@home": SubvolumeMeta("@home", str(backup_path / "@home"), uuid="backup-home", received_uuid="send-home", readonly=True),
                },
                restore.TimeshiftOsIdentity("root-uuid", "btrfs", "Ubuntu"),
            )
            plan = restore.RestorePlan(
                backups={RESTORE_DATE: backup},
                chain_names=[RESTORE_DATE],
                restore_names=[RESTORE_DATE],
                common_parent=None,
                common_reason="single",
                no_common_parent=False,
                backup_identity=backup.os_identity,
                os_identity_match=True,
                os_identity_reason="matched",
            )
            config = SimpleNamespace(
                name="pull-restore",
                ssh=SimpleNamespace(),
                state_file=Path("/remote/backup/.ts-btrfs-sync/state.json"),
                source=SimpleNamespace(
                    mode="local",
                    snapshot_root="/local/timeshift-btrfs/snapshots",
                    cache_root="/local/timeshift-btrfs/.ts-btrfs-sync/send-cache",
                    subvolumes=["@", "@home"],
                    sudo="sudo -n",
                    btrfs_command="btrfs",
                    timeshift_command="timeshift",
                ),
                destination=SimpleNamespace(target_root=Path("/remote/backup"), sudo="sudo -n", btrfs_command="btrfs"),
                stream=SimpleNamespace(btrfs_verbose=False, command=lambda: None),
                restore=SimpleNamespace(mode="ssh", backup_uses_ssh=True, timeshift_uses_ssh=False),
            )
            local_target = FakeTargetSource(remote=False)
            remote_backup = FakeTargetSource(remote=True)
            repository = restore.BackupRepository(
                config,
                remote_backup,
                restore.CommandEndpoint.for_source(remote_backup),
                restore.BtrfsOps(restore.CommandEndpoint.for_source(remote_backup), "sudo -n", "btrfs"),
            )
            events: list[tuple[str, object]] = []

            def safety(*args, **kwargs):
                events.append(("safety", args[1]))
                return CREATED

            def stop_stream(*_args, **_kwargs):
                events.append(("stream", None))
                raise RuntimeError("stop after first stream")

            with (
                patch.object(restore.BackupRepository, "from_config", return_value=repository),
                patch.object(restore.SourceRunner, "from_mode", return_value=local_target),
                patch.object(restore, "_build_restore_plan", return_value=(plan, {}, "")),
                patch.object(restore, "_source_path_exists", return_value=(False, "")),
                patch.object(restore, "_create_pre_restore_snapshot", side_effect=safety),
                patch.object(restore, "stream_pipeline", side_effect=stop_stream),
                patch.object(restore, "_cleanup_restore_attempt", return_value=[]),
                patch("builtins.input", side_effect=[
                    restore.RESTORE_RETENTION_CONFIRMATION,
                    "RESTORE SNAPSHOT",
                    RESTORE_DATE,
                ]),
            ):
                with self.assertRaisesRegex(RuntimeError, "stop after first stream"):
                    restore.restore_backups(
                        config,
                        snapshot_name=RESTORE_DATE,
                        restore_all=False,
                        dry_run=False,
                        danger_confirmed=True,
                        allow_no_common_parent=False,
                        create_pre_restore_snapshot=True,
                    )

            self.assertEqual(events[0], ("safety", local_target))
            self.assertEqual(events[1][0], "stream")
            self.assertFalse(any("timeshift --create" in command for command in remote_backup.calls))

    def test_dry_run_reports_safety_snapshot_without_creating_it(self):
        backup_root = Path("/backup")
        backup_path = backup_root / "snapshots" / RESTORE_DATE
        backup = restore.BackupSnapshot(
            RESTORE_DATE,
            str(backup_path),
            INFO,
            {
                "@": SubvolumeMeta("@", str(backup_path / "@"), uuid="backup-root", readonly=True),
                "@home": SubvolumeMeta("@home", str(backup_path / "@home"), uuid="backup-home", readonly=True),
            },
            restore.TimeshiftOsIdentity("root-uuid", "btrfs", "Ubuntu"),
        )
        plan = restore.RestorePlan(
            backups={RESTORE_DATE: backup},
            chain_names=[RESTORE_DATE],
            restore_names=[RESTORE_DATE],
            common_parent=None,
            common_reason="single",
            no_common_parent=False,
            backup_identity=backup.os_identity,
            os_identity_match=True,
            os_identity_reason="matched",
        )
        config = SimpleNamespace(
            name="dry-run",
            ssh=None,
            state_file=Path("/backup/.ts-btrfs-sync/state.json"),
            source=SimpleNamespace(
                mode="local",
                snapshot_root="/timeshift-btrfs/snapshots",
                cache_root="/timeshift-btrfs/.ts-btrfs-sync/send-cache",
                subvolumes=["@", "@home"],
                sudo="sudo -n",
                btrfs_command="btrfs",
                timeshift_command="timeshift",
            ),
            destination=SimpleNamespace(target_root=backup_root, sudo="sudo -n", btrfs_command="btrfs"),
            stream=SimpleNamespace(btrfs_verbose=False, command=lambda: None),
            restore=SimpleNamespace(
                mode="local",
                backup_uses_ssh=False,
                timeshift_uses_ssh=False,
            ),
        )
        source = FakeTargetSource(remote=False)
        with (
            patch.object(restore.SourceRunner, "from_mode", return_value=source),
            patch.object(restore, "_build_restore_plan", return_value=(plan, {}, "")),
            patch.object(restore, "_source_path_exists", return_value=(False, "")),
            patch.object(restore, "_create_pre_restore_snapshot") as create,
        ):
            restore.restore_backups(
                config,
                snapshot_name=RESTORE_DATE,
                restore_all=False,
                dry_run=True,
                danger_confirmed=False,
                allow_no_common_parent=False,
                create_pre_restore_snapshot=True,
            )
        create.assert_not_called()
        self.assertFalse(any("timeshift --create" in command for command in source.calls))

    def test_restore_cli_exposes_pre_restore_snapshot_flag(self):
        from timeshift_btrfs_sync.cli import build_parser

        args = build_parser().parse_args([
            "restore",
            "--config", "restore.toml",
            "--all",
            "--create-pre-restore-snapshot",
            "--dry-run",
        ])
        self.assertTrue(args.create_pre_restore_snapshot)


if __name__ == "__main__":
    unittest.main()
