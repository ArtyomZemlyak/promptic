from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, List, Sequence

from promptic.blueprints.models import ExecutionLogEntry
from promptic.context.logging import JsonlEventLogger


@dataclass
class PipelineLogger:
    """Collects execution events and optionally streams them to JSONL."""

    event_logger: JsonlEventLogger | None = None
    events: List[ExecutionLogEntry] = field(default_factory=list)

    def emit(
        self,
        *,
        step_id: str,
        event_type: str,
        payload: dict[str, Any] | None = None,
        reference_ids: Sequence[str] | None = None,
    ) -> ExecutionLogEntry:
        entry = ExecutionLogEntry(
            step_id=step_id,
            event_type=event_type,
            payload=payload or {},
            reference_ids=list(reference_ids or []),
        )
        self.events.append(entry)
        if self.event_logger:
            self.event_logger.log(entry)
        return entry

    def extend(self, entries: Iterable[ExecutionLogEntry]) -> None:
        for entry in entries:
            self.events.append(entry)
            if self.event_logger:
                self.event_logger.log(entry)

    def snapshot(self) -> List[ExecutionLogEntry]:
        return list(self.events)


__all__ = ["PipelineLogger"]
