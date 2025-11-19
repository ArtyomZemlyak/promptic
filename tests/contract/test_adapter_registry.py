from __future__ import annotations

from pathlib import Path
from typing import Any

from promptic.adapters import AdapterRegistry, BaseDataAdapter, BaseMemoryProvider
from promptic.blueprints import BlueprintStep, ContextBlueprint, DataSlot, MemorySlot
from promptic.sdk import adapters as sdk_adapters
from promptic.sdk.api import build_materializer
from promptic.settings.base import AdapterRegistrySettings, ContextEngineSettings


class UppercaseDataAdapter(BaseDataAdapter):
    def fetch(self, slot: DataSlot) -> list[dict[str, str]]:
        return [{"slot": slot.name.upper()}]


class EchoMemoryProvider(BaseMemoryProvider):
    def load(self, slot: MemorySlot) -> list[str]:
        return [slot.name, slot.name]


def _build_blueprint() -> ContextBlueprint:
    return ContextBlueprint(
        name="Adapters",
        prompt_template="Demo",
        steps=[BlueprintStep(step_id="root", title="Root", kind="sequence")],
        data_slots=[DataSlot(name="sources", adapter_key="uppercase")],
        memory_slots=[MemorySlot(name="history", provider_key="echo")],
    )


def test_sdk_registers_and_lists_adapters(tmp_path: Path) -> None:
    registry = AdapterRegistry()
    sdk_adapters.register_data_adapter(
        key="uppercase", adapter=UppercaseDataAdapter, registry=registry
    )
    sdk_adapters.register_memory_provider(
        key="echo", provider=EchoMemoryProvider, registry=registry
    )

    assert "uppercase" in sdk_adapters.list_data_adapters(registry=registry)
    assert "echo" in sdk_adapters.list_memory_providers(registry=registry)

    blueprint = _build_blueprint()
    settings = ContextEngineSettings(
        blueprint_root=tmp_path / "blueprints",
        instruction_root=tmp_path / "instructions",
        log_root=tmp_path / "logs",
        adapter_registry=AdapterRegistrySettings(),
    )
    materializer = build_materializer(settings=settings, registry=registry)

    data_result = materializer.resolve_data(blueprint, "sources")
    memory_result = materializer.resolve_memory(blueprint, "history")

    assert data_result.ok
    assert data_result.unwrap()[0]["slot"] == "SOURCES"
    assert memory_result.ok
    assert memory_result.unwrap() == ["history", "history"]
