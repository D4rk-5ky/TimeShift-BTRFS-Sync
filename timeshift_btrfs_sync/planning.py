"""Pure workflow planning from a combined backup inventory.

Planners describe intent but perform no commands.  The same ordered action
model powers real execution and dry-run output, preventing the two modes from
drifting apart.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Mapping, Any

from .snapshot_records import BackupInventory


class ActionKind(str, Enum):
    ENSURE_CACHE = "ensure-cache"
    SYNC_SUBVOLUME = "sync-subvolume"
    COPY_INFO_JSON = "copy-info-json"
    DELETE_CACHE_TREE = "delete-cache-tree"
    DELETE_DESTINATION_TREE = "delete-destination-tree"
    REMOVE_STATE = "remove-state"
    DESTROY_TREE = "destroy-tree"


@dataclass(frozen=True, slots=True)
class WorkflowAction:
    kind: ActionKind
    snapshot: str | None = None
    subvolume: str | None = None
    payload: Mapping[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class WorkflowPlan:
    name: str
    actions: list[WorkflowAction] = field(default_factory=list)

    def add(
        self,
        kind: ActionKind,
        *,
        snapshot: str | None = None,
        subvolume: str | None = None,
        **payload: Any,
    ) -> WorkflowAction:
        action = WorkflowAction(kind, snapshot, subvolume, payload)
        self.actions.append(action)
        return action

def plan_sync_queue(
    inventory: BackupInventory,
    selected_snapshot_names: Iterable[str],
    subvolume_names: Iterable[str],
) -> WorkflowPlan:
    """Plan the oldest-to-newest sync queue without executing operations."""

    plan = WorkflowPlan("sync")
    for snapshot_name in sorted(set(selected_snapshot_names)):
        record = inventory.get(snapshot_name)
        if not record or not record.source:
            continue
        for subvolume_name in subvolume_names:
            source_meta = record.source_meta(subvolume_name)
            if not source_meta:
                continue
            # The planner deliberately retains already-recorded items. Only the
            # execution workflow has enough live information to validate UUIDs,
            # destination paths, partial dates, sync-floor rules, and info.json
            # refreshes safely. A shallow state/path check here would bypass those
            # established checks before the snapshot reaches the sync loop.
            plan.add(ActionKind.ENSURE_CACHE, snapshot=snapshot_name, subvolume=subvolume_name)
            plan.add(ActionKind.SYNC_SUBVOLUME, snapshot=snapshot_name, subvolume=subvolume_name)
        plan.add(ActionKind.COPY_INFO_JSON, snapshot=snapshot_name)
    return plan


def plan_snapshot_recovery(snapshot_name: str) -> WorkflowPlan:
    """Plan one whole-date recovery in cache, destination, then state order."""

    plan = WorkflowPlan("recovery")
    plan.add(ActionKind.DELETE_CACHE_TREE, snapshot=snapshot_name)
    plan.add(ActionKind.DELETE_DESTINATION_TREE, snapshot=snapshot_name)
    plan.add(ActionKind.REMOVE_STATE, snapshot=snapshot_name)
    return plan


def plan_prune_snapshot(snapshot_name: str, *, delete_cache: bool, delete_destination: bool) -> WorkflowPlan:
    plan = WorkflowPlan("prune")
    # Preserve the historical prune order: remove the received destination
    # version first, then retire its source send-cache, and remove state only
    # after both sides are confirmed gone.
    if delete_destination:
        plan.add(ActionKind.DELETE_DESTINATION_TREE, snapshot=snapshot_name)
    if delete_cache:
        plan.add(ActionKind.DELETE_CACHE_TREE, snapshot=snapshot_name)
    plan.add(ActionKind.REMOVE_STATE, snapshot=snapshot_name)
    return plan


def plan_destroy_targets(targets: Iterable[tuple[str, str]]) -> WorkflowPlan:
    """Plan named endpoint/root destruction in the caller-provided order."""

    plan = WorkflowPlan("destroy-leftovers")
    for label, path in targets:
        plan.add(ActionKind.DESTROY_TREE, label=label, path=path)
    return plan
