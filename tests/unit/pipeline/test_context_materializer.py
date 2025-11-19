from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Sequence

import pytest

from promptic.adapters import AdapterRegistry, BaseDataAdapter, BaseMemoryProvider
from promptic.blueprints import (
    BlueprintStep,
    ContextBlueprint,
    DataSlot,
    InstructionFallbackConfig,
    InstructionNode,
    InstructionNodeRef,
    MemorySlot,
)
from promptic.context import AdapterNotRegisteredError, InstructionNotFoundError
from promptic.instructions.store import InstructionResolver, InstructionStore
from promptic.pipeline import ContextMaterializer
from promptic.settings.base import ContextEngineSettings


class MemoryInstructionStore(InstructionStore):
    def __init__(self, mapping: Dict[str, str]) -> None:
        self._mapping = mapping
        self.load_calls = 0

    def list_ids(self) -> Sequence[str]:
        return tuple(self._mapping.keys())

    def get_node(self, instruction_id: str) -> InstructionNode:
        if instruction_id not in self._mapping:
            raise InstructionNotFoundError(instruction_id)
        self.load_calls += 1
        return InstructionNode(
            instruction_id=instruction_id,
            source_uri=f"memory://{instruction_id}",
            format="md",
            checksum="a" * 32,
            locale="en-US",
            version="1",
        )

    def load_content(self, instruction_id: str) -> str:
        if instruction_id not in self._mapping:
            raise InstructionNotFoundError(instruction_id)
        return self._mapping[instruction_id]


class ConstantDataAdapter(BaseDataAdapter):
    calls = 0

    def fetch(self, slot: DataSlot) -> Dict[str, str]:
        ConstantDataAdapter.calls += 1
        return {"slot": slot.name}


class ConstantMemoryProvider(BaseMemoryProvider):
    def load(self, slot: MemorySlot) -> Dict[str, str]:
        return {"memory": slot.name}


def build_blueprint() -> ContextBlueprint:
    return ContextBlueprint(
        name="Demo",
        prompt_template="Hello",
        steps=[
            BlueprintStep(
                step_id="root",
                title="Root",
                kind="sequence",
                instruction_refs=[InstructionNodeRef(instruction_id="intro")],
            )
        ],
        data_slots=[DataSlot(name="sources", adapter_key="constant")],
        memory_slots=[MemorySlot(name="prior", provider_key="constant")],
    )


def build_materializer() -> tuple[ContextMaterializer, MemoryInstructionStore]:
    store = MemoryInstructionStore({"intro": "Hello world"})
    resolver = InstructionResolver(store)
    registry = AdapterRegistry()
    registry.register_data("constant", ConstantDataAdapter)
    registry.register_memory("constant", ConstantMemoryProvider)
    settings = ContextEngineSettings()
    materializer = ContextMaterializer(
        settings=settings,
        instruction_resolver=resolver,
        adapter_registry=registry,
    )
    return materializer, store


def test_instruction_resolution_is_cached() -> None:
    materializer, store = build_materializer()
    result1 = materializer.resolve_instruction("intro")
    result2 = materializer.resolve_instruction("intro")

    assert result1.ok and result2.ok
    assert result1.unwrap()[1] == "Hello world"
    assert store.load_calls == 1


def test_data_resolution_uses_registry_cache() -> None:
    ConstantDataAdapter.calls = 0
    blueprint = build_blueprint()
    materializer, _ = build_materializer()

    result1 = materializer.resolve_data(blueprint, "sources")
    result2 = materializer.resolve_data(blueprint, "sources")

    assert result1.ok and result2.ok
    assert result1.unwrap()["slot"] == "sources"
    assert ConstantDataAdapter.calls == 1


def test_missing_adapter_returns_failure() -> None:
    blueprint = ContextBlueprint(
        name="Demo",
        prompt_template="Hi",
        steps=[
            BlueprintStep(step_id="root", title="Root", kind="sequence"),
        ],
        data_slots=[DataSlot(name="sources", adapter_key="missing")],
    )
    materializer, _ = build_materializer()
    result = materializer.resolve_data(blueprint, "sources")
    assert not result.ok
    assert isinstance(result.error, AdapterNotRegisteredError)


def test_resolve_data_slots_batches_requests() -> None:
    ConstantDataAdapter.calls = 0
    blueprint = build_blueprint()
    blueprint.data_slots.append(DataSlot(name="sources_copy", adapter_key="constant"))
    materializer, _ = build_materializer()

    result = materializer.resolve_data_slots(blueprint)

    assert result.ok
    values = result.unwrap()
    assert set(values.keys()) == {"sources", "sources_copy"}
    stats = materializer.snapshot_stats()
    assert stats.data_adapter_instances == 1


def test_prefetch_instructions_warms_cache() -> None:
    materializer, store = build_materializer()
    blueprint = build_blueprint()

    warm = materializer.prefetch_instructions(blueprint)

    assert warm.ok
    stats = materializer.snapshot_stats()
    assert store.load_calls == 1
    assert stats.instruction_misses >= 1

    second = materializer.resolve_instruction("intro")
    assert second.ok
    stats_after = materializer.snapshot_stats()
    assert stats_after.instruction_hits >= 1


def test_memory_slots_share_cached_providers() -> None:
    blueprint = build_blueprint()
    blueprint.memory_slots.append(MemorySlot(name="archive", provider_key="constant"))
    materializer, _ = build_materializer()

    first = materializer.resolve_memory_slots(blueprint)
    assert first.ok
    second = materializer.resolve_memory(blueprint, "archive")
    assert second.ok

    stats = materializer.snapshot_stats()
    assert stats.memory_cache_hits >= 1


def test_instruction_fallback_records_events() -> None:
    materializer, _ = build_materializer()
    refs = [
        InstructionNodeRef(
            instruction_id="missing",
            fallback=InstructionFallbackConfig(mode="warn", placeholder="[missing instruction]"),
        )
    ]

    result = materializer.resolve_instruction_refs(refs)

    assert result.ok
    node, content = result.unwrap()[0]
    assert node.instruction_id == "missing"
    assert content == "[missing instruction]"
    events = materializer.consume_fallback_events()
    assert events and events[0].instruction_id == "missing"
