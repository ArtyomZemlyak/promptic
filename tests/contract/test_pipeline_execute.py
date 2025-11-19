from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from promptic.blueprints import ContextBlueprint, FallbackEvent, InstructionNode, InstructionNodeRef
from promptic.context import OperationResult
from promptic.sdk import pipeline as sdk_pipeline
from promptic.sdk.api import ExecutionResponse
from promptic.settings.base import ContextEngineSettings


class StubMaterializer:
    def __init__(self, *, fallback_events: Sequence[FallbackEvent] | None = None) -> None:
        self.calls: list[tuple[str, Any]] = []
        self._fallback_events = list(fallback_events or [])

    def resolve_instruction_refs(
        self, refs: Sequence[InstructionNodeRef]
    ) -> OperationResult[Sequence[tuple[InstructionNode, str]]]:
        self.calls.append(("instructions", [ref.instruction_id for ref in refs]))
        resolved = []
        for ref in refs:
            node = InstructionNode(
                instruction_id=ref.instruction_id,
                source_uri=f"memory://{ref.instruction_id}",
                format="md",
                checksum="c" * 32,
                locale="en-US",
                version="1",
            )
            resolved.append((node, f"Instruction {ref.instruction_id}"))
        return OperationResult.success(tuple(resolved))

    def resolve_data(
        self,
        blueprint: ContextBlueprint,
        slot_name: str,
        *,
        overrides: Mapping[str, Any] | None = None,
    ) -> OperationResult[Any]:
        self.calls.append(("data", slot_name))
        value = overrides.get(slot_name) if overrides else [{"title": slot_name}]
        return OperationResult.success(value)

    def resolve_memory(
        self,
        blueprint: ContextBlueprint,
        slot_name: str,
        *,
        overrides: Mapping[str, Any] | None = None,
    ) -> OperationResult[Any]:
        self.calls.append(("memory", slot_name))
        value = overrides.get(slot_name) if overrides else ["mem"]
        return OperationResult.success(value)

    def reset_caches(self) -> None:  # pragma: no cover - compatibility hook
        return

    def prefetch_instructions(self, blueprint: ContextBlueprint) -> OperationResult[int]:
        self.calls.append(("prefetch", blueprint.id))
        return OperationResult.success(0)

    def resolve_data_slots(
        self,
        blueprint: ContextBlueprint,
        *,
        overrides: Mapping[str, Any] | None = None,
    ) -> OperationResult[dict[str, Any]]:
        payload: dict[str, Any] = {}
        warnings: list[str] = []
        for slot in blueprint.data_slots:
            result = self.resolve_data(blueprint, slot.name, overrides=overrides)
            warnings.extend(result.warnings)
            if not result.ok:
                return result
            payload[slot.name] = result.unwrap()
        return OperationResult.success(payload, warnings=warnings)

    def resolve_memory_slots(
        self,
        blueprint: ContextBlueprint,
        *,
        overrides: Mapping[str, Any] | None = None,
    ) -> OperationResult[dict[str, Any]]:
        payload: dict[str, Any] = {}
        warnings: list[str] = []
        for slot in blueprint.memory_slots:
            result = self.resolve_memory(blueprint, slot.name, overrides=overrides)
            warnings.extend(result.warnings)
            if not result.ok:
                return result
            payload[slot.name] = result.unwrap()
        return OperationResult.success(payload, warnings=warnings)

    def consume_fallback_events(self) -> list[FallbackEvent]:
        events = list(self._fallback_events)
        self._fallback_events.clear()
        return events


def _write_blueprint_assets(tmp_path: Path) -> ContextEngineSettings:
    blueprint_root = tmp_path / "blueprints"
    instruction_root = tmp_path / "instructions"
    blueprint_root.mkdir()
    instruction_root.mkdir()

    (instruction_root / "intro.md").write_text("Intro", encoding="utf-8")
    (instruction_root / "summary.md").write_text("Summary", encoding="utf-8")

    blueprint_root.joinpath("demo.yaml").write_text(
        """
name: Demo Executor
prompt_template: |
  Title: {{ data.records[0].title }}
global_instructions:
  - instruction_id: intro
steps:
  - step_id: summarize
    title: Summarize
    kind: sequence
    instruction_refs:
      - instruction_id: summary
data_slots:
  - name: records
    adapter_key: demo_adapter
    schema:
      type: array
memory_slots:
  - name: history
    provider_key: demo_memory
""",
        encoding="utf-8",
    )

    return ContextEngineSettings(
        blueprint_root=blueprint_root,
        instruction_root=instruction_root,
        log_root=tmp_path / "logs",
    )


def test_pipeline_run_uses_materializer_interfaces(tmp_path: Path) -> None:
    settings = _write_blueprint_assets(tmp_path)
    materializer = StubMaterializer()

    response = sdk_pipeline.run_pipeline(
        blueprint_id="demo",
        settings=settings,
        materializer=materializer,  # type: ignore[arg-type]
        data_inputs={"records": [{"title": "Contract Test"}]},
        memory_inputs={"history": ["contract"]},
    )

    assert isinstance(response, ExecutionResponse)
    assert response.events, "Expected execution events to be recorded."
    instruction_calls = [call for call in materializer.calls if call[0] == "instructions"]
    assert instruction_calls
    assert ("data", "records") in materializer.calls
    assert ("memory", "history") in materializer.calls


def test_pipeline_response_includes_fallback_events(tmp_path: Path) -> None:
    settings = _write_blueprint_assets(tmp_path)
    fallback_event = FallbackEvent(
        instruction_id="summary",
        mode="warn",
        message="warn fallback applied",
        placeholder_used="[summary missing]",
        log_key="summary",
    )
    materializer = StubMaterializer(fallback_events=[fallback_event])

    response = sdk_pipeline.run_pipeline(
        blueprint_id="demo",
        settings=settings,
        materializer=materializer,  # type: ignore[arg-type]
    )

    assert response.fallback_events == [fallback_event]
