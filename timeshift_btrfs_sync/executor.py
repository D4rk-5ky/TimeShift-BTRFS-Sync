"""Generic ordered workflow action executor."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Any

from .planning import ActionKind, WorkflowAction, WorkflowPlan

ActionHandler = Callable[[WorkflowAction], Any]


@dataclass(slots=True)
class WorkflowExecutor:
    """Execute or preview a plan using one handler per action kind."""

    handlers: dict[ActionKind, ActionHandler]
    dry_run: bool = False
    preview: Callable[[WorkflowAction], None] | None = None
    results: list[tuple[WorkflowAction, Any]] = field(default_factory=list)

    def execute(self, plan: WorkflowPlan) -> list[tuple[WorkflowAction, Any]]:
        self.results.clear()
        for action in plan.actions:
            if self.dry_run:
                if self.preview:
                    self.preview(action)
                self.results.append((action, None))
                continue
            handler = self.handlers.get(action.kind)
            if handler is None:
                raise RuntimeError(f"No workflow handler registered for {action.kind.value}")
            self.results.append((action, handler(action)))
        return list(self.results)
