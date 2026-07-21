from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import call, patch

from timeshift_btrfs_sync import restore
from timeshift_btrfs_sync.commands import Completed
from timeshift_btrfs_sync.inventory import BtrfsIndex, SourceInventory
from timeshift_btrfs_sync.models import SnapshotMeta, SubvolumeMeta


S1 = "2026-07-15_04-00-02"
S2 = "2026-07-15_05-00-02"
S3 = "2026-07-15_06-00-02"


def info(_name: str) -> str:
    return (
        '{"sys-uuid":"source-root-uuid","sys-distro":"Ubuntu",'
        '"app-version":"24.06.6","file_count":"123",'
        '"tags":"ondemand","comments":"","live":"false","type":"btrfs"}\n'
    )


class FakeSource:
    def __init__(self, remote: bool, listed: list[str]):
        self.uses_ssh = remote
        self.location = "remote" if remote else "local"
        self.listed = listed
        self.calls: list[str] = []

    def command(self, shell_command: str) -> list[str]:
        return ["ssh", "source", shell_command] if self.uses_ssh else ["sh", "-c", shell_command]

    def run(self, shell_command: str, **_kwargs) -> Completed:
        self.calls.append(shell_command)
        if "timeshift" in shell_command and "--list" in shell_command:
            return Completed(0, "\n".join(f"{name} O restored" for name in self.listed) + "\n", "")
        if "cat" in shell_command and "info.json" in shell_command:
            for name in (S1, S2, S3):
                if name in shell_command:
                    return Completed(0, info(name), "")
        return Completed(0, "", "")

    def environment(self):
        return {"SSHPASS": "secret"} if self.uses_ssh else None


class RestoreSnapshotTests(unittest.TestCase):
    def make_config(self, target_root: Path, *, remote: bool):
        return SimpleNamespace(
            name="restore-test",
            state_file=target_root / ".ts-btrfs-sync" / "state.json",
            ssh=SimpleNamespace() if remote else None,
            source=SimpleNamespace(
                mode="ssh" if remote else "local",
                snapshot_root="/source/timeshift-btrfs/snapshots",
                cache_root="/source/timeshift-btrfs/.ts-btrfs-sync/send-cache",
                subvolumes=["@", "@home"],
                sudo="sudo -n",
                btrfs_command="btrfs",
                timeshift_command="timeshift",
            ),
            destination=SimpleNamespace(
                target_root=target_root,
                sudo="sudo -n",
                btrfs_command="btrfs",
            ),
            stream=SimpleNamespace(
                btrfs_verbose=False,
                command=lambda: None,
            ),
            restore=SimpleNamespace(
                mode="ssh-target" if remote else "local",
                backup_uses_ssh=False,
                timeshift_uses_ssh=remote,
            ),
        )

    def backup(self, root: Path, name: str) -> restore.BackupSnapshot:
        date = root / "snapshots" / name
        return restore.BackupSnapshot(
            name,
            date,
            info(name),
            {
                "@": SubvolumeMeta("@", str(date / "@"), uuid=f"backup-{name}-root", received_uuid=f"send-{name}-root", readonly=True),
                "@home": SubvolumeMeta("@home", str(date / "@home"), uuid=f"backup-{name}-home", received_uuid=f"send-{name}-home", readonly=True),
            },
            restore.TimeshiftOsIdentity("source-root-uuid", "btrfs", "Ubuntu"),
        )

    def single_plan(self, root: Path) -> restore.RestorePlan:
        backup = self.backup(root, S2)
        return restore.RestorePlan(
            backups={S2: backup},
            chain_names=[S2],
            restore_names=[S2],
            common_parent=None,
            common_reason="single",
            no_common_parent=False,
        )

    def chain_plan(self, root: Path, *, common: bool) -> restore.RestorePlan:
        backups = {name: self.backup(root, name) for name in (S1, S2, S3)}
        return restore.RestorePlan(
            backups=backups,
            chain_names=[S1, S2, S3],
            restore_names=[S2, S3] if common else [S1, S2, S3],
            common_parent=S1 if common else None,
            common_reason="UUIDs match" if common else "none match",
            no_common_parent=not common,
        )

    def meta_side_effect(self, _ops, path, *, name=None, required=True):
        text = str(path)
        payload = name or Path(text).name
        for snapshot in (S1, S2, S3):
            if "restore-chain-" in text and f"/{snapshot}/{payload}" in text:
                return SubvolumeMeta(
                    payload,
                    text,
                    uuid=f"hidden-{snapshot}-{payload}",
                    received_uuid=f"send-{snapshot}-{'root' if payload == '@' else 'home'}",
                    readonly=True,
                )
            if f"/.ts-btrfs-sync-restore-{snapshot}/{payload}" in text:
                return SubvolumeMeta(payload, text, parent_uuid=f"hidden-{snapshot}-{payload}", readonly=False)
            if text.endswith(f"/{snapshot}/{payload}") and _ops.endpoint.label != "backup destination":
                return SubvolumeMeta(payload, text, parent_uuid=f"hidden-{snapshot}-{payload}", readonly=False)
        return None

    def run_execution(self, *, remote: bool, plan: restore.RestorePlan, inputs: list[str]):
        source = FakeSource(remote, plan.restore_names)
        pipeline_calls = []

        def capture_pipeline(left, right, **kwargs):
            pipeline_calls.append((left, right, kwargs))

        config = self.make_config(next(iter(plan.backups.values())).path.parents[1], remote=remote)
        repository = restore.BackupRepository.from_config(config)
        with (
            patch.object(restore.BackupRepository, "from_config", return_value=repository),
            patch.object(restore.SourceRunner, "from_mode", return_value=source),
            patch.object(restore, "_build_restore_plan", return_value=(plan, {}, "")),
            patch.object(restore, "_source_path_exists", return_value=(False, "")),
            patch.object(restore.BtrfsOps, "meta", autospec=True, side_effect=self.meta_side_effect),
            patch.object(restore.BtrfsOps, "snapshot", return_value=Completed(0, "", "")) as snapshot_call,
            patch.object(restore, "stream_pipeline", side_effect=capture_pipeline),
            patch.object(restore, "_write_source_info_json"),
            patch.object(restore, "_cleanup_restore_attempt", return_value=[]),
            patch("builtins.input", side_effect=inputs),
        ):
            restore.restore_backups(
                config,
                snapshot_name=None if len(plan.backups) > 1 else plan.restore_names[0],
                restore_all=len(plan.backups) > 1,
                dry_run=False,
                danger_confirmed=True,
                allow_no_common_parent=plan.no_common_parent,
                allow_os_identity_mismatch=False,
            )
        return source, pipeline_calls, snapshot_call

    def test_single_local_restore_uses_full_receive_then_writable_cow_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = self.single_plan(Path(directory) / "target")
            source, pipelines, snapshots = self.run_execution(
                remote=False,
                plan=plan,
                inputs=[restore.RESTORE_RETENTION_CONFIRMATION, "RESTORE SNAPSHOT", S2],
            )
        self.assertEqual(len(pipelines), 2)
        self.assertTrue(all("-p" not in pipeline[0] for pipeline in pipelines))
        self.assertTrue(all(pipeline[1][:2] == ["sh", "-c"] for pipeline in pipelines))
        self.assertEqual(snapshots.call_count, 2)
        self.assertTrue(all(call_.kwargs["readonly"] is False for call_ in snapshots.call_args_list))
        self.assertIsNone(pipelines[0][2]["right_env"])

    def test_single_remote_restore_uses_same_flow_over_ssh(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = self.single_plan(Path(directory) / "target")
            _source, pipelines, snapshots = self.run_execution(
                remote=True,
                plan=plan,
                inputs=[restore.RESTORE_RETENTION_CONFIRMATION, "RESTORE SNAPSHOT", S2],
            )
        self.assertEqual(len(pipelines), 2)
        self.assertTrue(all(pipeline[1][0] == "ssh" for pipeline in pipelines))
        self.assertTrue(all(pipeline[2]["right_env"] == {"SSHPASS": "secret"} for pipeline in pipelines))
        self.assertEqual(snapshots.call_count, 2)

    def test_restore_cli_requires_exactly_one_selection_and_exposes_no_common_override(self):
        from timeshift_btrfs_sync.cli import build_parser

        parser = build_parser()
        parsed = parser.parse_args([
            "restore", "--config", "config.toml", "--all",
            "--allow-no-common-parent", "--allow-os-identity-mismatch", "--dry-run"
        ])
        self.assertTrue(parsed.restore_all)
        self.assertTrue(parsed.allow_no_common_parent)
        self.assertTrue(parsed.allow_os_identity_mismatch)
        with self.assertRaises(SystemExit):
            parser.parse_args(["restore", "--config", "config.toml", "--dry-run"])
        with self.assertRaises(SystemExit):
            parser.parse_args([
                "restore", "--config", "config.toml", "--all", "--snapshot", S1, "--dry-run"
            ])

    def test_common_parent_chain_full_seeds_common_then_sends_incrementals(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = self.chain_plan(Path(directory) / "target", common=True)
            _source, pipelines, snapshots = self.run_execution(
                remote=False,
                plan=plan,
                inputs=[restore.RESTORE_RETENTION_CONFIRMATION, "RESTORE SNAPSHOT CHAIN", S1],
            )
        self.assertEqual(len(pipelines), 6)
        self.assertTrue(all("-p" not in pipeline[0] for pipeline in pipelines[:2]))
        self.assertTrue(all("-p" in pipeline[0] for pipeline in pipelines[2:]))
        for index, (snapshot, parent) in enumerate(((S2, S1), (S3, S2)), start=1):
            for offset, payload in enumerate(("@", "@home")):
                command = pipelines[index * 2 + offset][0]
                parent_index = command.index("-p") + 1
                self.assertTrue(command[parent_index].endswith(f"/snapshots/{parent}/{payload}"))
                self.assertTrue(command[-1].endswith(f"/snapshots/{snapshot}/{payload}"))
        self.assertEqual(snapshots.call_count, 4)  # S2/S3 only; common parent is hidden seed.

    def test_no_common_parent_full_restores_oldest_then_incrementals(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = self.chain_plan(Path(directory) / "target", common=False)
            _source, pipelines, snapshots = self.run_execution(
                remote=True,
                plan=plan,
                inputs=[restore.RESTORE_RETENTION_CONFIRMATION, "RESTORE ALL WITHOUT COMMON PARENT", "restore-test"],
            )
        self.assertEqual(len(pipelines), 6)
        self.assertTrue(all("-p" not in pipeline[0] for pipeline in pipelines[:2]))
        self.assertTrue(all("-p" in pipeline[0] for pipeline in pipelines[2:]))
        self.assertEqual(snapshots.call_count, 6)

    def test_no_common_parent_real_restore_requires_explicit_override(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "target"
            plan = self.chain_plan(root, common=False)
            config = self.make_config(root, remote=False)
            source = FakeSource(False, [])
            with (
                patch.object(restore.SourceRunner, "from_mode", return_value=source),
                patch.object(restore, "_build_restore_plan", return_value=(plan, {}, "")),
            ):
                with self.assertRaisesRegex(restore.RestoreError, "could import another OS"):
                    restore.restore_backups(
                        config,
                        snapshot_name=None,
                        restore_all=True,
                        dry_run=False,
                        danger_confirmed=True,
                        allow_no_common_parent=False,
                        allow_os_identity_mismatch=False,
                    )

    def test_all_with_one_backup_still_warns_when_no_common_parent_exists(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "target"
            backup = self.backup(root, S1)
            plan = restore.RestorePlan(
                backups={S1: backup},
                chain_names=[S1],
                restore_names=[S1],
                common_parent=None,
                common_reason="no state identity",
                no_common_parent=True,
            )
            output = io.StringIO()
            with patch("sys.stdout", output):
                restore._print_restore_plan(self.make_config(root, remote=False), FakeSource(False, []), plan, dry_run=True)
        self.assertIn("selection:      all snapshots", output.getvalue())
        self.assertIn("common parent:  NONE", output.getvalue())
        self.assertIn("different OS", output.getvalue())

    def test_restore_retention_confirmation_sentence_is_exact(self):
        self.assertEqual(
            restore.RESTORE_RETENTION_CONFIRMATION,
            "I UNDERSTAND TIMESHIFT MAY DELETE RESTORED SNAPSHOTS OR OLDER THAN RESTORED SNAPSHOTS",
        )

    def test_restore_plan_warns_that_timeshift_retention_can_delete_restored_snapshots(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "target"
            plan = self.single_plan(root)
            output = io.StringIO()
            with patch("sys.stdout", output):
                restore._print_restore_plan(
                    self.make_config(root, remote=False),
                    FakeSource(False, []),
                    plan,
                    dry_run=True,
                )
        warning = output.getvalue()
        self.assertIn("RESTORED SNAPSHOT RETENTION WARNING", warning)
        self.assertIn("original info.json is restored unchanged", warning)
        self.assertIn("H/D/W/M", warning)
        self.assertIn("may later delete", warning)
        self.assertIn("older than", warning)
        self.assertIn("older existing rollback point", warning)
        self.assertIn(restore.RESTORE_RETENTION_CONFIRMATION, warning)

    def test_real_restore_rejects_missing_retention_risk_sentence_before_streaming(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "target"
            plan = self.single_plan(root)
            config = self.make_config(root, remote=True)
            source = FakeSource(True, [])
            with (
                patch.object(restore.SourceRunner, "from_mode", return_value=source),
                patch.object(restore, "_build_restore_plan", return_value=(plan, {}, "")),
                patch.object(restore, "_source_path_exists", return_value=(False, "")),
                patch.object(restore, "stream_pipeline") as pipeline,
                patch("builtins.input", return_value="I DID NOT READ THE WARNING"),
            ):
                with self.assertRaisesRegex(restore.RestoreError, "retention confirmation did not match"):
                    restore.restore_backups(
                        config,
                        snapshot_name=S2,
                        restore_all=False,
                        dry_run=False,
                        danger_confirmed=True,
                        allow_no_common_parent=False,
                        allow_os_identity_mismatch=False,
                    )
        pipeline.assert_not_called()

    def test_dry_run_warns_without_common_parent_and_does_not_stream(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "target"
            plan = self.chain_plan(root, common=False)
            config = self.make_config(root, remote=False)
            source = FakeSource(False, [])
            output = io.StringIO()
            with (
                patch.object(restore.SourceRunner, "from_mode", return_value=source),
                patch.object(restore, "_build_restore_plan", return_value=(plan, {}, "")),
                patch.object(restore, "_source_path_exists", return_value=(False, "")),
                patch.object(restore, "stream_pipeline") as pipeline,
                patch("sys.stdout", output),
            ):
                restore.restore_backups(
                    config,
                    snapshot_name=None,
                    restore_all=True,
                    dry_run=True,
                    danger_confirmed=False,
                    allow_no_common_parent=False,
                    allow_os_identity_mismatch=False,
                )
        pipeline.assert_not_called()
        self.assertIn("DANGER", output.getvalue())
        self.assertIn("full receive of the oldest backup", output.getvalue())
        self.assertIn("incremental", output.getvalue())

    def test_build_all_plan_restores_only_snapshots_after_newest_common_parent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "target"
            backups = {name: self.backup(root, name) for name in (S1, S2, S3)}
            source = {
                S2: SnapshotMeta(
                    S2, f"/snapshots/{S2}",
                    subvolumes={
                        "@": SubvolumeMeta("@", f"/snapshots/{S2}/@", uuid=f"original-{S2}-root"),
                        "@home": SubvolumeMeta("@home", f"/snapshots/{S2}/@home", uuid=f"original-{S2}-home"),
                    },
                )
            }
            state = {
                "snapshots": {
                    S2: {
                        "subvolumes": {
                            "@": {"status": "ok", "original_source_uuid": f"original-{S2}-root", "send_source_uuid": f"send-{S2}-root"},
                            "@home": {"status": "ok", "original_source_uuid": f"original-{S2}-home", "send_source_uuid": f"send-{S2}-home"},
                        }
                    }
                }
            }
            config = self.make_config(root, remote=False)
            repository = SimpleNamespace(load_state=lambda: state)
            with (
                patch.object(restore, "_discover_backups", return_value=backups),
                patch.object(restore, "_timeshift_snapshots", return_value=(
                    source,
                    SourceInventory(
                        "timeshift list",
                        BtrfsIndex("/source/timeshift-btrfs/snapshots", "local"),
                        None,
                        {S2: info(S2)},
                    ),
                )),
            ):
                plan, _source, _output = restore._build_restore_plan(
                    config, repository, FakeSource(False, []), snapshot_name=None, restore_all=True
                )
        self.assertEqual(plan.common_parent, S2)
        self.assertEqual(plan.chain_names, [S2, S3])
        self.assertEqual(plan.restore_names, [S3])
        self.assertFalse(plan.no_common_parent)

    def test_build_all_plan_starts_incrementally_when_exact_source_cache_parent_exists(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "target"
            backups = {name: self.backup(root, name) for name in (S1, S2, S3)}
            source = {
                S1: SnapshotMeta(
                    S1, f"/snapshots/{S1}",
                    subvolumes={
                        "@": SubvolumeMeta("@", f"/snapshots/{S1}/@", uuid=f"original-{S1}-root"),
                        "@home": SubvolumeMeta("@home", f"/snapshots/{S1}/@home", uuid=f"original-{S1}-home"),
                    },
                )
            }
            config = self.make_config(root, remote=False)
            cache_index = BtrfsIndex(config.source.cache_root, "local")
            state_payloads = {}
            for payload, suffix in (("@", "root"), ("@home", "home")):
                cache_path = f"{config.source.cache_root}/{S1}/{payload}"
                cache_index.add(SubvolumeMeta(payload, cache_path, uuid=f"send-{S1}-{suffix}", readonly=True))
                state_payloads[payload] = {
                    "status": "ok",
                    "original_source_uuid": f"original-{S1}-{suffix}",
                    "send_source_uuid": f"send-{S1}-{suffix}",
                    "send_path": f"{S1}/{payload}",
                    "send_path_kind": "source-cache",
                }
            state = {"snapshots": {S1: {"subvolumes": state_payloads}}}
            inventory = SourceInventory(
                "timeshift list",
                BtrfsIndex(config.source.snapshot_root, "local"),
                cache_index,
                {S1: info(S1)},
            )
            repository = SimpleNamespace(load_state=lambda: state)
            source_ops = restore.BtrfsOps(restore.CommandEndpoint.local("source"), "sudo -n", "btrfs")
            with (
                patch.object(restore, "_discover_backups", return_value=backups),
                patch.object(restore, "_timeshift_snapshots", return_value=(source, inventory)),
            ):
                plan, _source, _output = restore._build_restore_plan(
                    config,
                    repository,
                    FakeSource(False, []),
                    timeshift_ops=source_ops,
                    snapshot_name=None,
                    restore_all=True,
                )
        self.assertEqual(plan.common_parent, S1)
        self.assertEqual(plan.initial_send_parent, S1)
        self.assertEqual(plan.chain_names, [S2, S3])
        self.assertEqual(plan.restore_names, [S2, S3])
        self.assertEqual(set(plan.receive_parent_paths or {}), {"@", "@home"})

    def test_build_all_plan_with_newest_common_parent_has_nothing_to_restore(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "target"
            backups = {name: self.backup(root, name) for name in (S1, S2)}
            source = {
                S2: SnapshotMeta(
                    S2, f"/snapshots/{S2}",
                    subvolumes={
                        "@": SubvolumeMeta("@", f"/snapshots/{S2}/@", uuid=f"original-{S2}-root"),
                        "@home": SubvolumeMeta("@home", f"/snapshots/{S2}/@home", uuid=f"original-{S2}-home"),
                    },
                )
            }
            state = {
                "snapshots": {
                    S2: {
                        "subvolumes": {
                            "@": {"status": "ok", "original_source_uuid": f"original-{S2}-root", "send_source_uuid": f"send-{S2}-root"},
                            "@home": {"status": "ok", "original_source_uuid": f"original-{S2}-home", "send_source_uuid": f"send-{S2}-home"},
                        }
                    }
                }
            }
            config = self.make_config(root, remote=False)
            repository = SimpleNamespace(load_state=lambda: state)
            with (
                patch.object(restore, "_discover_backups", return_value=backups),
                patch.object(restore, "_timeshift_snapshots", return_value=(
                    source,
                    SourceInventory(
                        "timeshift list",
                        BtrfsIndex("/source/timeshift-btrfs/snapshots", "local"),
                        None,
                        {S2: info(S2)},
                    ),
                )),
            ):
                plan, _source, _output = restore._build_restore_plan(
                    config, repository, FakeSource(False, []), snapshot_name=None, restore_all=True
                )
        self.assertEqual(plan.common_parent, S2)
        self.assertEqual(plan.chain_names, [])
        self.assertEqual(plan.restore_names, [])

    def test_latest_common_parent_requires_source_and_backup_uuid_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "target"
            backups = {name: self.backup(root, name) for name in (S1, S2)}
            source = {
                name: SnapshotMeta(
                    name,
                    f"/snapshots/{name}",
                    subvolumes={
                        "@": SubvolumeMeta("@", f"/snapshots/{name}/@", uuid=f"original-{name}-root"),
                        "@home": SubvolumeMeta("@home", f"/snapshots/{name}/@home", uuid=f"original-{name}-home"),
                    },
                )
                for name in (S1, S2)
            }
            state = {
                "snapshots": {
                    name: {
                        "subvolumes": {
                            "@": {
                                "status": "ok",
                                "original_source_uuid": f"original-{name}-root",
                                "send_source_uuid": f"send-{name}-root",
                            },
                            "@home": {
                                "status": "ok",
                                "original_source_uuid": f"original-{name}-home",
                                "send_source_uuid": f"send-{name}-home",
                            },
                        }
                    }
                    for name in (S1, S2)
                }
            }
            config = self.make_config(root, remote=False)
            common, reason = restore._find_latest_common_parent(
                config,
                backups,
                source,
                {S1: backups[S1].os_identity, S2: backups[S2].os_identity},
                state,
            )
            self.assertEqual(common, S2)
            self.assertIn("all configured", reason)

            backups[S2].payloads["@home"].received_uuid = "wrong-os-send-uuid"
            common, _reason = restore._find_latest_common_parent(
                config,
                backups,
                source,
                {S1: backups[S1].os_identity, S2: backups[S2].os_identity},
                state,
            )
            self.assertEqual(common, S1)

    def test_existing_restore_target_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "target"
            plan = self.single_plan(root)
            config = self.make_config(root, remote=False)
            source = FakeSource(False, [])
            with (
                patch.object(restore.SourceRunner, "from_mode", return_value=source),
                patch.object(restore, "_build_restore_plan", return_value=(plan, {}, "")),
                patch.object(restore, "_source_path_exists", side_effect=[(False, ""), (True, "")]),
            ):
                with self.assertRaisesRegex(restore.RestoreError, "Refusing to overwrite existing final Timeshift date"):
                    restore.restore_backups(
                        config,
                        snapshot_name=S2,
                        restore_all=False,
                        dry_run=True,
                        danger_confirmed=False,
                        allow_no_common_parent=False,
                        allow_os_identity_mismatch=False,
                    )

    def test_real_timeshift_info_json_without_date_is_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            date = target / "snapshots" / S2
            (date / "@").mkdir(parents=True)
            (date / "@home").mkdir()
            content = info(S2)
            (date / "info.json").write_text(content, encoding="utf-8")
            config = self.make_config(target, remote=False)

            def meta(_ops, path, **_kwargs):
                text = str(path)
                if text.endswith(S2):
                    return SubvolumeMeta(S2, text, uuid="date")
                return SubvolumeMeta(Path(text).name, text, uuid="payload", readonly=True)

            repository = restore.BackupRepository.from_config(config)
            with (
                patch.object(restore, "build_source_btrfs_index", return_value=BtrfsIndex(str(target / "snapshots"), "local")),
                patch.object(restore.BtrfsOps, "meta", autospec=True, side_effect=meta),
            ):
                backup = restore._discover_backups(config, repository, selected_name=S2)[S2]
            self.assertEqual(backup.name, S2)
            self.assertEqual(backup.info_content, content)

    def test_restore_all_discovers_multiple_real_timeshift_info_files_without_date(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            for name in (S1, S2):
                date = target / "snapshots" / name
                (date / "@").mkdir(parents=True)
                (date / "@home").mkdir()
                (date / "info.json").write_text(info(name), encoding="utf-8")
            config = self.make_config(target, remote=False)

            def meta(_ops, path, **_kwargs):
                text = str(path)
                name = Path(text).name
                if name in (S1, S2):
                    return SubvolumeMeta(name, text, uuid=f"date-{name}")
                return SubvolumeMeta(name, text, uuid=f"payload-{name}", readonly=True)

            repository = restore.BackupRepository.from_config(config)
            with (
                patch.object(restore, "build_source_btrfs_index", return_value=BtrfsIndex(str(target / "snapshots"), "local")),
                patch.object(restore.BtrfsOps, "meta", autospec=True, side_effect=meta),
            ):
                backups = restore._discover_backups(config, repository)
            self.assertEqual(list(backups), [S1, S2])
            self.assertTrue(all('"date"' not in item.info_content for item in backups.values()))


    def test_common_parent_reuses_exact_readonly_source_send_parent_in_local_and_ssh_modes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "target"
            backups = {name: self.backup(root, name) for name in (S1, S2, S3)}
            for remote in (False, True):
                with self.subTest(remote=remote):
                    plan = restore.RestorePlan(
                        backups=backups,
                        chain_names=[S2, S3],
                        restore_names=[S2, S3],
                        common_parent=S1,
                        common_reason="UUID and info.json identity match",
                        no_common_parent=False,
                        initial_send_parent=S1,
                        receive_parent_paths={
                            "@": f"/source/timeshift-btrfs/.ts-btrfs-sync/send-cache/{S1}/@",
                            "@home": f"/source/timeshift-btrfs/.ts-btrfs-sync/send-cache/{S1}/@home",
                        },
                        receive_parent_reason="exact recorded send parents remain read-only",
                        backup_identity=restore.TimeshiftOsIdentity("source-root-uuid", "btrfs", "Ubuntu"),
                        os_identity_match=True,
                        os_identity_reason="matched",
                    )
                    _source, pipelines, snapshots = self.run_execution(
                        remote=remote,
                        plan=plan,
                        inputs=[restore.RESTORE_RETENTION_CONFIRMATION, "RESTORE SNAPSHOT CHAIN", S1],
                    )
                    self.assertEqual(len(pipelines), 4)
                    self.assertTrue(all("-p" in pipeline[0] for pipeline in pipelines))
                    for offset, payload in enumerate(("@", "@home")):
                        command = pipelines[offset][0]
                        parent_index = command.index("-p") + 1
                        self.assertTrue(command[parent_index].endswith(f"/snapshots/{S1}/{payload}"))
                        self.assertTrue(command[-1].endswith(f"/snapshots/{S2}/{payload}"))
                    self.assertEqual(snapshots.call_count, 4)

    def test_ssh_target_inventory_keeps_snapshot_and_cache_on_same_remote_runner(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "target"
            config = self.make_config(root, remote=True)
            runner = FakeSource(True, [])
            inventory = SourceInventory(
                "",
                BtrfsIndex(config.source.snapshot_root, "remote"),
                BtrfsIndex(config.source.cache_root, "remote"),
            )
            with (
                patch.object(restore, "build_source_inventory", return_value=inventory) as build_inventory,
                patch.object(restore, "list_source_snapshots", return_value=[]),
            ):
                snapshots, built = restore._timeshift_snapshots(config, runner)

            self.assertEqual(snapshots, {})
            self.assertIs(built, inventory)
            build_inventory.assert_called_once_with(
                runner,
                snapshot_root=config.source.snapshot_root,
                cache_root=config.source.cache_root,
                sudo=config.source.sudo,
                btrfs_command=config.source.btrfs_command,
                timeshift_command=config.source.timeshift_command,
                required=True,
            )

    def test_reusable_receive_parent_requires_recorded_uuid_and_readonly_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "target"
            config = self.make_config(root, remote=False)
            cache_index = BtrfsIndex(config.source.cache_root, "local")
            state_payloads = {}
            for payload, suffix in (("@", "root"), ("@home", "home")):
                path = f"{config.source.cache_root}/{S1}/{payload}"
                cache_index.add(SubvolumeMeta(payload, path, uuid=f"send-{S1}-{suffix}", readonly=True))
                state_payloads[payload] = {
                    "send_path": f"{S1}/{payload}",
                    "send_path_kind": "source-cache",
                    "send_source_uuid": f"send-{S1}-{suffix}",
                }
            inventory = SourceInventory(
                "",
                BtrfsIndex(config.source.snapshot_root, "local"),
                cache_index,
            )
            state = {"snapshots": {S1: {"subvolumes": state_payloads}}}
            source_ops = restore.BtrfsOps(restore.CommandEndpoint.local("source"), "sudo -n", "btrfs")
            paths, reason = restore._find_reusable_receive_parent(
                config, source_ops, inventory, state, S1
            )
            self.assertEqual(set(paths or {}), {"@", "@home"})
            self.assertIn("exact recorded", reason)

            cache_index.by_path[f"{config.source.cache_root}/{S1}/@"].readonly = False
            paths, reason = restore._find_reusable_receive_parent(
                config, source_ops, inventory, state, S1
            )
            self.assertIsNone(paths)
            self.assertIn("not read-only", reason)

    def test_info_json_os_identity_ignores_snapshot_specific_fields(self):
        left, left_identity = restore._parse_info_json(
            '{"sys-uuid":"same-root","type":"btrfs","sys-distro":"Ubuntu 24.04",'
            '"tags":"H","comments":"one","created":"1","file_count":"10",'
            '"app-version":"24.06.6","live":"false"}',
            label="left",
        )
        right, right_identity = restore._parse_info_json(
            '{"sys-uuid":"same-root","type":"btrfs","sys-distro":"Ubuntu 26.04",'
            '"tags":"M","comments":"two","created":"2","file_count":"99",'
            '"app-version":"25.12.4","live":"true"}',
            label="right",
        )
        self.assertNotEqual(left["tags"], right["tags"])
        self.assertTrue(restore._same_os_identity(left_identity, right_identity))

    def test_real_restore_requires_explicit_override_when_info_json_os_identity_is_not_proven(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "target"
            plan = self.single_plan(root)
            plan.os_identity_match = False
            plan.os_identity_reason = "backup sys-uuid differs"
            config = self.make_config(root, remote=False)
            source = FakeSource(False, [])
            with (
                patch.object(restore.SourceRunner, "from_mode", return_value=source),
                patch.object(restore, "_build_restore_plan", return_value=(plan, {}, "")),
            ):
                with self.assertRaisesRegex(restore.RestoreError, "--allow-os-identity-mismatch"):
                    restore.restore_backups(
                        config,
                        snapshot_name=S2,
                        restore_all=False,
                        dry_run=False,
                        danger_confirmed=True,
                        allow_no_common_parent=False,
                        allow_os_identity_mismatch=False,
                    )

    def test_os_identity_override_requires_exact_sentence_before_streaming(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "target"
            plan = self.single_plan(root)
            plan.os_identity_match = False
            plan.os_identity_reason = "backup sys-uuid differs"
            plan.backup_identity = restore.TimeshiftOsIdentity("other-root", "btrfs", "Ubuntu")
            config = self.make_config(root, remote=True)
            source = FakeSource(True, [S2])
            with (
                patch.object(restore.SourceRunner, "from_mode", return_value=source),
                patch.object(restore, "_build_restore_plan", return_value=(plan, {}, "")),
                patch.object(restore, "_source_path_exists", return_value=(False, "")),
                patch.object(restore, "stream_pipeline") as pipeline,
                patch("builtins.input", side_effect=[
                    restore.RESTORE_RETENTION_CONFIRMATION,
                    "WRONG OS SENTENCE",
                ]),
            ):
                with self.assertRaisesRegex(restore.RestoreError, "OS-identity risk confirmation did not match"):
                    restore.restore_backups(
                        config,
                        snapshot_name=S2,
                        restore_all=False,
                        dry_run=False,
                        danger_confirmed=True,
                        allow_no_common_parent=False,
                        allow_os_identity_mismatch=True,
                    )
            pipeline.assert_not_called()

    def test_effective_send_uuid_prefers_received_uuid_for_received_backups(self):
        received = SubvolumeMeta("@", "/backup/@", uuid="local-uuid", received_uuid="stream-uuid", readonly=True)
        native = SubvolumeMeta("@", "/native/@", uuid="native-uuid", readonly=True)
        self.assertEqual(restore._effective_send_uuid(received), "stream-uuid")
        self.assertEqual(restore._effective_send_uuid(native), "native-uuid")

    def test_btrfs_snapshot_operation_builds_writable_and_readonly_commands(self):
        ops = restore.BtrfsOps(restore.CommandEndpoint.local("test"), "", "btrfs")
        with patch.object(restore.BtrfsOps, "run", autospec=True, return_value=Completed(0, "", "")) as run:
            ops.snapshot("/source", "/target", readonly=False)
            ops.snapshot("/source", "/target-ro", readonly=True)
        self.assertEqual(
            run.call_args_list[0],
            call(ops, ["subvolume", "snapshot", "/source", "/target"], check=True),
        )
        self.assertEqual(
            run.call_args_list[1],
            call(ops, ["subvolume", "snapshot", "-r", "/source", "/target-ro"], check=True),
        )


if __name__ == "__main__":
    unittest.main()
