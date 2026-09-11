from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase, mock

from timeshift_btrfs_sync.config import (
    AppConfig,
    DestinationConfig,
    ManualSnapshotConfig,
    RestoreConfig,
    RetentionConfig,
    SourceConfig,
    StreamConfig,
)
from timeshift_btrfs_sync.inventory import BtrfsIndex
from timeshift_btrfs_sync.mail import MailConfig
from timeshift_btrfs_sync.models import SnapshotMeta, SubvolumeMeta
from timeshift_btrfs_sync.mqtt import MQTTConfig
from timeshift_btrfs_sync.planning import ActionKind, plan_prune_snapshot
from timeshift_btrfs_sync import retention, timeshift
from timeshift_btrfs_sync.state import STATE_VERSION


def _config(*, retention_count: int = 10, cleanup_enabled: bool = True) -> AppConfig:
    return AppConfig(
        name="retention-test",
        ssh=None,
        source=SourceConfig(
            snapshot_root="/timeshift/snapshots",
            mode="local",
            subvolumes=["@", "@home"],
            cache_root="/timeshift/cache",
            cleanup_superseded_cache=True,
        ),
        destination=DestinationConfig(target_root=Path("/backup")),
        stream=StreamConfig(),
        retention=RetentionConfig(
            hourly=0,
            daily=0,
            weekly=0,
            monthly=0,
            boot=0,
            ondemand=10,
            cleanup_ondemand=False,
            keep_latest=True,
            keep_latest_common_parent=False,
        ),
        mqtt=MQTTConfig(),
        mail=MailConfig(),
        manual_snapshot=ManualSnapshotConfig(
            enabled=True,
            cleanup_enabled=cleanup_enabled,
            comment="ts-btrfs-sync automatic on-demand snapshot",
            marker="ts-btrfs-sync",
            retention_count=retention_count,
        ),
        restore=RestoreConfig(),
        state_file=Path("/backup/.ts-btrfs-sync/state.json"),
        lock_file=Path("/backup/.ts-btrfs-sync/lock"),
        log_dir=None,
    )


def _name(day: int) -> str:
    return f"2026-09-{day:02d}_01-00-00"


def _source_snapshot(day: int, *, app: bool = True, tags: list[str] | None = None) -> SnapshotMeta:
    name = _name(day)
    return SnapshotMeta(
        name=name,
        path=f"/timeshift/snapshots/{name}",
        tags=list(tags if tags is not None else ["O"]),
        comment=("ts-btrfs-sync automatic on-demand snapshot" if app else "my manual snapshot"),
        created=name,
    )


def _synced_state_entry(name: str, *, app: bool = True) -> dict:
    return {
        "name": name,
        "tags": ["O"],
        "comment": "ts-btrfs-sync automatic on-demand snapshot" if app else "my manual snapshot",
        "created": name,
        "path": f"snapshots/{name}",
        "subvolumes": {
            "@": {
                "status": "ok",
                "destination_path": f"snapshots/{name}/@",
                "send_path_kind": "source-cache",
                "send_path": f"{name}/@",
            },
            "@home": {
                "status": "ok",
                "destination_path": f"snapshots/{name}/@home",
                "send_path_kind": "source-cache",
                "send_path": f"{name}/@home",
            },
        },
    }


def _state(names: list[str]) -> dict:
    return {
        "version": STATE_VERSION,
        "snapshots": {name: _synced_state_entry(name) for name in names},
    }


def _destination_index(names: list[str]) -> BtrfsIndex:
    index = BtrfsIndex(root="/backup/snapshots", location="local")
    for name in names:
        for subvolume in ("@", "@home"):
            index.add(SubvolumeMeta(name=subvolume, path=f"/backup/snapshots/{name}/{subvolume}"))
    return index


class ManualSnapshotRetentionTests(TestCase):
    def test_app_created_source_retention_keeps_newest_ten(self) -> None:
        config = _config(retention_count=10)
        source_index = {snap.name: snap for snap in (_source_snapshot(day) for day in range(1, 13))}
        self.assertEqual(
            retention._source_app_retention_delete_names(config, source_index),
            {_name(1), _name(2)},
        )

    def test_destination_app_retention_keeps_the_same_newest_ten(self) -> None:
        config = _config(retention_count=10)
        state = _state([_name(day) for day in range(1, 13)])
        plan = retention.build_prune_plan(config, state)
        self.assertEqual(plan.delete, {_name(1), _name(2)})
        self.assertEqual({_name(day) for day in range(3, 13)}, plan.keep)

    def test_marker_without_o_tag_is_not_a_source_delete_candidate(self) -> None:
        config = _config(retention_count=1)
        source_index = {
            _name(1): _source_snapshot(1, app=True, tags=["D"]),
            _name(2): _source_snapshot(2, app=True, tags=["O"]),
        }
        self.assertNotIn(_name(1), retention._source_app_retention_delete_names(config, source_index))

    def test_cleanup_disabled_never_creates_source_delete_candidates(self) -> None:
        config = _config(retention_count=1, cleanup_enabled=False)
        source_index = {snap.name: snap for snap in (_source_snapshot(day) for day in range(1, 4))}
        self.assertEqual(retention._source_app_retention_delete_names(config, source_index), set())

    def test_normal_user_created_ondemand_is_never_source_app_candidate(self) -> None:
        config = _config(retention_count=1)
        source_index = {
            _name(1): _source_snapshot(1, app=False),
            _name(2): _source_snapshot(2, app=True),
        }
        self.assertNotIn(_name(1), retention._source_app_retention_delete_names(config, source_index))

    def test_tracked_source_delete_requires_complete_live_backup(self) -> None:
        config = _config(retention_count=10)
        source_index = {snap.name: snap for snap in (_source_snapshot(day) for day in range(1, 13))}
        state = _state([_name(1), _name(2), *[_name(day) for day in range(3, 13)]])
        destination = _destination_index([_name(1), *[_name(day) for day in range(3, 13)]])
        candidates = {_name(1), _name(2)}
        allowed, _window = retention._authorized_source_timeshift_delete_names(
            config, state, source_index, destination, candidates
        )
        self.assertIn(_name(1), allowed)
        self.assertNotIn(_name(2), allowed)

    def test_legacy_01373_source_only_backlog_is_allowed_after_retained_window_is_proven(self) -> None:
        config = _config(retention_count=10)
        source_index = {snap.name: snap for snap in (_source_snapshot(day) for day in range(1, 13))}
        retained_names = [_name(day) for day in range(3, 13)]
        state = _state(retained_names)
        destination = _destination_index(retained_names)
        candidates = retention._source_app_retention_delete_names(config, source_index)
        allowed, window_proven = retention._authorized_source_timeshift_delete_names(
            config, state, source_index, destination, candidates
        )
        self.assertTrue(window_proven)
        self.assertEqual(allowed, {_name(1), _name(2)})

    def test_legacy_backlog_is_blocked_when_one_retained_backup_is_not_proven(self) -> None:
        config = _config(retention_count=10)
        source_index = {snap.name: snap for snap in (_source_snapshot(day) for day in range(1, 13))}
        retained_names = [_name(day) for day in range(3, 13)]
        state = _state(retained_names)
        destination = _destination_index(retained_names[:-1])
        candidates = retention._source_app_retention_delete_names(config, source_index)
        allowed, window_proven = retention._authorized_source_timeshift_delete_names(
            config, state, source_index, destination, candidates
        )
        self.assertFalse(window_proven)
        self.assertEqual(allowed, set())

    def test_source_timeshift_delete_revalidates_current_o_tag_and_marker(self) -> None:
        config = _config()
        name = _name(1)
        state = _state([name])
        source_index = {name: _source_snapshot(1, app=False)}
        with mock.patch.object(timeshift, "delete_source_manual_snapshot") as delete:
            ok = retention._delete_source_timeshift_snapshot_for_prune(
                config, state, SimpleNamespace(), source_index, name
            )
        self.assertFalse(ok)
        delete.assert_not_called()

    def test_timeshift_delete_command_uses_timeshift_not_raw_btrfs_or_rm(self) -> None:
        name = _name(1)
        command = timeshift.delete_remote_manual_snapshot_cmd("sudo -n", "timeshift", name)
        self.assertIn("timeshift --delete --snapshot", command)
        self.assertIn("--scripted --yes", command)
        self.assertIn("timeshift --list", command)
        self.assertNotIn("btrfs subvolume delete", command)
        self.assertNotIn("rm -", command)

    def test_timeshift_delete_verifies_snapshot_is_absent_after_delete(self) -> None:
        name = _name(1)
        fake_source = SimpleNamespace(
            run=lambda *_args, **_kwargs: SimpleNamespace(
                stdout=f"deleted\n{timeshift.DELETE_VERIFY_MARKER}\n{_name(2)} O ts-btrfs-sync automatic on-demand snapshot\n"
            )
        )
        timeshift.delete_source_manual_snapshot(
            fake_source,
            snapshot_root="/timeshift/snapshots",
            sudo="sudo -n",
            timeshift_command="timeshift",
            snapshot_name=name,
        )

    def test_timeshift_delete_fails_if_snapshot_is_still_listed(self) -> None:
        name = _name(1)
        fake_source = SimpleNamespace(
            run=lambda *_args, **_kwargs: SimpleNamespace(
                stdout=f"deleted\n{timeshift.DELETE_VERIFY_MARKER}\n{name} O ts-btrfs-sync automatic on-demand snapshot\n"
            )
        )
        with self.assertRaisesRegex(RuntimeError, "still listed"):
            timeshift.delete_source_manual_snapshot(
                fake_source,
                snapshot_root="/timeshift/snapshots",
                sudo="sudo -n",
                timeshift_command="timeshift",
                snapshot_name=name,
            )

    def test_failed_source_timeshift_delete_leaves_destination_untouched_for_retry(self) -> None:
        config = _config(retention_count=10)
        config.source.cleanup_superseded_cache = False
        name = _name(1)
        state = _state([name])
        source_index = {name: _source_snapshot(1)}
        plan = retention.PrunePlan(delete={name})
        with (
            mock.patch.object(retention, "_delete_source_timeshift_snapshot_for_prune", return_value=False) as source_delete,
            mock.patch.object(retention, "_delete_destination_snapshot_for_prune", return_value=True) as destination_delete,
        ):
            ok = retention._delete_prune_item(
                config,
                state,
                plan,
                SimpleNamespace(),
                source_index,
                {name},
                name,
            )
        self.assertFalse(ok)
        source_delete.assert_called_once()
        destination_delete.assert_not_called()
        self.assertIn(name, state["snapshots"])

    def test_successful_source_delete_allows_destination_cleanup(self) -> None:
        config = _config(retention_count=10)
        config.source.cleanup_superseded_cache = False
        name = _name(1)
        state = _state([name])
        source_index = {name: _source_snapshot(1)}
        plan = retention.PrunePlan(delete={name})
        calls: list[str] = []

        def source_ok(*_args, **_kwargs):
            calls.append("source")
            source_index.pop(name, None)
            return True

        def destination_ok(*_args, **_kwargs):
            calls.append("destination")
            return True

        with (
            mock.patch.object(retention, "_delete_source_timeshift_snapshot_for_prune", side_effect=source_ok),
            mock.patch.object(retention, "_delete_destination_snapshot_for_prune", side_effect=destination_ok),
        ):
            ok = retention._delete_prune_item(
                config,
                state,
                plan,
                SimpleNamespace(),
                source_index,
                {name},
                name,
            )
        self.assertTrue(ok)
        self.assertEqual(calls, ["source", "destination"])
        self.assertNotIn(name, state["snapshots"])

    def test_prune_action_order_preserves_backup_until_source_delete_is_confirmed(self) -> None:
        plan = plan_prune_snapshot(
            _name(1),
            delete_destination=True,
            delete_cache=True,
            delete_source_timeshift=True,
        )
        self.assertEqual(
            [action.kind for action in plan.actions],
            [
                ActionKind.DELETE_SOURCE_TIMESHIFT,
                ActionKind.DELETE_DESTINATION_TREE,
                ActionKind.DELETE_CACHE_TREE,
                ActionKind.REMOVE_STATE,
            ],
        )


if __name__ == "__main__":
    import unittest
    unittest.main()
