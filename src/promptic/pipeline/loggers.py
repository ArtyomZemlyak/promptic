from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, List, Literal, Sequence

from promptic.blueprints.models import ExecutionLogEntry
from promptic.context.logging import JsonlEventLogger


@dataclass
class PipelineLogger:
    """Collects execution events and optionally streams them to JSONL."""

    event_logger: JsonlEventLogger | None = None
    events: List[ExecutionLogEntry] = field(default_factory=list)
    blueprint_id: str | None = None

    def emit(
        self,
        *,
        step_id: str,
        event_type: str,
        payload: dict[str, Any] | None = None,
        reference_ids: Sequence[str] | None = None,
        level: str | None = None,
        asset_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionLogEntry:
        # Determine level from event_type if not provided
        resolved_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]
        if level is None:
            if event_type == "error":
                resolved_level = "ERROR"
            elif event_type in ("size_warning", "instruction_fallback"):
                resolved_level = "WARNING"
            else:
                resolved_level = "INFO"
        else:
            resolved_level = level  # type: ignore[assignment]

        # Extract asset_id from reference_ids or payload if not provided
        if asset_id is None:
            if reference_ids:
                asset_id = reference_ids[0]
            elif payload and "instruction_id" in payload:
                asset_id = payload["instruction_id"]
            elif payload and "adapter_key" in payload:
                asset_id = payload["adapter_key"]

        # Merge payload into metadata for structured querying
        merged_metadata = dict(metadata or {})
        if payload:
            merged_metadata.update(payload)

        # Cast event_type to the expected literal type
        event_type_literal: Literal[
            "instruction_accessed",
            "instruction_loaded",
            "instruction_fallback",
            "adapter_resolved",
            "fallback_applied",
            "data_resolved",
            "memory_resolved",
            "size_warning",
            "error",
        ] = event_type  # type: ignore[assignment]

        entry = ExecutionLogEntry(
            level=resolved_level,
            event_type=event_type_literal,
            blueprint_id=self.blueprint_id,
            step_id=step_id,
            asset_id=asset_id,
            metadata=merged_metadata,
            # Legacy fields for backward compatibility
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
