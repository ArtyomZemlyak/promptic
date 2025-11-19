from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from promptic.blueprints import (
    BlueprintStep,
    ContextBlueprint,
    DataSlot,
    FallbackEvent,
    InstructionNode,
    InstructionNodeRef,
    MemorySlot,
)
from promptic.context import OperationResult
from promptic.pipeline.executor import ExecutionArtifact, PipelineExecutor
from promptic.pipeline.hooks import PipelineHooks
from promptic.pipeline.loggers import PipelineLogger
from promptic.pipeline.policies import PolicyEngine
from promptic.settings.base import ContextEngineSettings


@dataclass
class StubBuilder:
    blueprint: ContextBlueprint

    def load(self, blueprint_id: str) -> OperationResult[ContextBlueprint]:
        return OperationResult.success(self.blueprint)


class StubMaterializer:
    def __init__(self) -> None:
        self.instructions: list[str] = []
        self._fallback_events: list[FallbackEvent] = []
        self.fallback_targets: dict[str, str] = {}

    def resolve_instruction_refs(
        self, refs: Sequence[InstructionNodeRef]
    ) -> OperationResult[Sequence[tuple[InstructionNode, str]]]:
        payload = []
        for ref in refs:
            self.instructions.append(ref.instruction_id)
            payload.append(
                (
                    InstructionNode(
                        instruction_id=ref.instruction_id,
                        source_uri=f"memory://{ref.instruction_id}",
                        format="md",
                        checksum="d" * 32,
                        locale="en-US",
                        version="1",
                    ),
                    self._maybe_placeholder(ref.instruction_id),
                )
            )
        return OperationResult.success(tuple(payload))

    def _maybe_placeholder(self, instruction_id: str) -> str:
        placeholder = self.fallback_targets.get(instruction_id)
        if placeholder is None:
            return f"Instruction {instruction_id}"
        self._fallback_events.append(
            FallbackEvent(
                instruction_id=instruction_id,
                mode="warn",
                message="warn fallback applied",
                placeholder_used=placeholder,
                log_key=instruction_id,
            )
        )
        return placeholder

    def resolve_data(
        self,
        blueprint: ContextBlueprint,
        slot_name: str,
        *,
        overrides: Mapping[str, Any] | None = None,
    ) -> OperationResult[Any]:
        return OperationResult.success(
            overrides.get(slot_name) if overrides else [{"title": "Item"}]
        )

    def resolve_memory(
        self,
        blueprint: ContextBlueprint,
        slot_name: str,
        *,
        overrides: Mapping[str, Any] | None = None,
    ) -> OperationResult[Any]:
        return OperationResult.success(overrides.get(slot_name) if overrides else ["memo"])

    def prefetch_instructions(self, blueprint: ContextBlueprint) -> OperationResult[int]:
        return OperationResult.success(0)

    def resolve_data_slots(
        self,
        blueprint: ContextBlueprint,
        *,
        overrides: Mapping[str, Any] | None = None,
    ) -> OperationResult[dict[str, Any]]:
        payload: dict[str, Any] = {}
        for slot in blueprint.data_slots:
            result = self.resolve_data(blueprint, slot.name, overrides=overrides)
            if not result.ok:
                return result
            payload[slot.name] = result.unwrap()
        return OperationResult.success(payload)

    def resolve_memory_slots(
        self,
        blueprint: ContextBlueprint,
        *,
        overrides: Mapping[str, Any] | None = None,
    ) -> OperationResult[dict[str, Any]]:
        payload: dict[str, Any] = {}
        for slot in blueprint.memory_slots:
            result = self.resolve_memory(blueprint, slot.name, overrides=overrides)
            if not result.ok:
                return result
            payload[slot.name] = result.unwrap()
        return OperationResult.success(payload)

    def consume_fallback_events(self) -> list[FallbackEvent]:
        events = list(self._fallback_events)
        self._fallback_events.clear()
        return events


def _make_blueprint() -> ContextBlueprint:
    return ContextBlueprint(
        name="Exec",
        prompt_template="Exec",
        steps=[
            BlueprintStep(
                step_id="loop",
                title="Loop",
                kind="loop",
                loop_slot="records",
                instruction_refs=[InstructionNodeRef(instruction_id="loop_inst")],
                children=[
                    BlueprintStep(
                        step_id="detail",
                        title="Detail",
                        kind="sequence",
                        instruction_refs=[InstructionNodeRef(instruction_id="detail_inst")],
                    )
                ],
            )
        ],
        data_slots=[DataSlot(name="records", adapter_key="static", schema_definition={})],
        memory_slots=[MemorySlot(name="history", provider_key="static")],
    )


def test_executor_logs_events(tmp_path: Path) -> None:
    blueprint = _make_blueprint()
    builder = StubBuilder(blueprint)
    materializer = StubMaterializer()
    settings = ContextEngineSettings(log_root=tmp_path / "logs")
    logger = PipelineLogger()
    policies = PolicyEngine(settings=settings)
    executor = PipelineExecutor(
        builder=builder,  # type: ignore[arg-type]
        materializer=materializer,  # type: ignore[arg-type]
        logger=logger,
        policies=policies,
        hooks=PipelineHooks(),
    )

    result = executor.run(
        blueprint_id="exec",
        data_inputs={"records": [{"title": "One"}, {"title": "Two"}]},
        memory_inputs={"history": ["memo"]},
    )

    assert result.ok
    artifact = result.unwrap()
    assert isinstance(artifact, ExecutionArtifact)
    assert len(artifact.events) >= 4
    assert materializer.instructions == ["loop_inst", "detail_inst", "detail_inst"]


def test_executor_emits_size_warning_when_step_exceeds_budget(tmp_path: Path) -> None:
    blueprint = _make_blueprint()
    builder = StubBuilder(blueprint)
    materializer = StubMaterializer()
    base_settings = ContextEngineSettings(log_root=tmp_path / "logs")
    settings = base_settings.model_copy(
        update={
            "size_budget": base_settings.size_budget.model_copy(
                update={"per_step_budget_chars": 10}
            )
        }
    )
    logger = PipelineLogger()
    policies = PolicyEngine(settings=settings)
    executor = PipelineExecutor(
        builder=builder,  # type: ignore[arg-type]
        materializer=materializer,  # type: ignore[arg-type]
        logger=logger,
        policies=policies,
    )

    result = executor.run(blueprint_id="exec")
    assert result.ok
    warnings = [event for event in result.unwrap().events if event.event_type == "size_warning"]
    assert warnings, "Expected size warnings when per-step budget is exceeded."


def test_executor_captures_instruction_fallbacks(tmp_path: Path) -> None:
    blueprint = _make_blueprint()
    builder = StubBuilder(blueprint)
    materializer = StubMaterializer()
    materializer.fallback_targets["detail_inst"] = "[detail missing]"
    settings = ContextEngineSettings(log_root=tmp_path / "logs")
    logger = PipelineLogger()
    policies = PolicyEngine(settings=settings)
    executor = PipelineExecutor(
        builder=builder,  # type: ignore[arg-type]
        materializer=materializer,  # type: ignore[arg-type]
        logger=logger,
        policies=policies,
    )

    result = executor.run(blueprint_id="exec")

    assert result.ok
    artifact = result.unwrap()
    fallback_events = [e for e in artifact.events if e.event_type == "instruction_fallback"]
    assert fallback_events, "Expected fallback log entries when placeholder text is used."
    assert artifact.fallback_events, "ExecutionArtifact should expose fallback events."
