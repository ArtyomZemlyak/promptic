from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

import pytest

from promptic.blueprints import ContextBlueprint, FallbackEvent, InstructionNode, InstructionNodeRef
from promptic.context import OperationResult
from promptic.sdk import blueprints as sdk_blueprints
from promptic.sdk.api import PreviewResponse
from promptic.settings.base import ContextEngineSettings


class StubMaterializer:
    def __init__(
        self,
        instructions: Mapping[str, str],
        *,
        fallback_events: Sequence[FallbackEvent] | None = None,
    ) -> None:
        self._instructions = instructions
        self.calls: list[tuple[str, Any]] = []
        self._fallback_events = list(fallback_events or [])

    def resolve_instruction_refs(
        self, refs: Sequence[InstructionNodeRef]
    ) -> OperationResult[Sequence[tuple[InstructionNode, str]]]:
        self.calls.append(("instructions", [ref.instruction_id for ref in refs]))
        resolved: list[tuple[InstructionNode, str]] = []
        for ref in refs:
            payload = self._instructions[ref.instruction_id]
            node = InstructionNode(
                instruction_id=ref.instruction_id,
                source_uri=f"memory://{ref.instruction_id}",
                format="md",
                checksum="b" * 32,
                locale="en-US",
                version="1",
            )
            resolved.append((node, payload))
        return OperationResult.success(tuple(resolved))

    def resolve_data(
        self,
        blueprint: ContextBlueprint,
        slot_name: str,
        *,
        overrides: Mapping[str, Any] | None = None,
    ) -> OperationResult[Any]:
        self.calls.append(("data", slot_name))
        if overrides and slot_name in overrides:
            return OperationResult.success(overrides[slot_name])
        return OperationResult.success({"slot": slot_name})

    def resolve_memory(
        self,
        blueprint: ContextBlueprint,
        slot_name: str,
        *,
        overrides: Mapping[str, Any] | None = None,
    ) -> OperationResult[Any]:
        self.calls.append(("memory", slot_name))
        if overrides and slot_name in overrides:
            return OperationResult.success(overrides[slot_name])
        return OperationResult.success({"memory": slot_name})

    def reset_caches(self) -> None:  # pragma: no cover - compatibility hook
        pass

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
    (instruction_root / "collect.md").write_text("Collect", encoding="utf-8")

    blueprint_root.joinpath("demo.yaml").write_text(
        """
name: Demo Flow
prompt_template: |
  Hello {{ sample_data.sources[0].title }}
global_instructions:
  - instruction_id: intro
steps:
  - step_id: collect
    title: Collect
    kind: sequence
    instruction_refs:
      - instruction_id: collect
data_slots:
  - name: sources
    adapter_key: stub
    schema:
      type: array
memory_slots:
  - name: prior
    provider_key: stub
""",
        encoding="utf-8",
    )

    return ContextEngineSettings(
        blueprint_root=blueprint_root,
        instruction_root=instruction_root,
        log_root=tmp_path / "logs",
    )


def test_preview_blueprint_uses_injected_materializer(tmp_path: Path) -> None:
    settings = _write_blueprint_assets(tmp_path)
    materializer = StubMaterializer({"intro": "Intro", "collect": "Collect"})

    response = sdk_blueprints.preview_blueprint(
        blueprint_id="demo",
        materializer=materializer,  # type: ignore[arg-type]
        settings=settings,
        sample_data={"sources": [{"title": "Sample Doc"}]},
        sample_memory={"prior": ["Finding A"]},
    )

    assert isinstance(response, PreviewResponse)
    assert "Sample Doc" in response.rendered_context

    instruction_calls = [call for call in materializer.calls if call[0] == "instructions"]
    assert instruction_calls, "Materializer was not asked to resolve instructions."

    data_calls = [call for call in materializer.calls if call[0] == "data"]
    memory_calls = [call for call in materializer.calls if call[0] == "memory"]
    assert ("data", "sources") in data_calls
    assert ("memory", "prior") in memory_calls

    assert "Collect" in response.rendered_context


def test_preview_response_includes_fallback_events(tmp_path: Path) -> None:
    settings = _write_blueprint_assets(tmp_path)
    fallback_event = FallbackEvent(
        instruction_id="collect",
        mode="warn",
        message="warn fallback applied",
        placeholder_used="[collect missing]",
        log_key="collect",
    )
    materializer = StubMaterializer(
        {"intro": "Intro", "collect": "Collect"}, fallback_events=[fallback_event]
    )

    response = sdk_blueprints.preview_blueprint(
        blueprint_id="demo",
        materializer=materializer,  # type: ignore[arg-type]
        settings=settings,
        sample_data={"sources": [{"title": "Sample Doc"}]},
        sample_memory={"prior": ["Finding A"]},
    )

    assert response.fallback_events == [fallback_event]
