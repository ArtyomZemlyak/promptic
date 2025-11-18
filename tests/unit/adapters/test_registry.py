from __future__ import annotations

from typing import Any

import pytest

from promptic.adapters import AdapterRegistry, BaseDataAdapter, BaseMemoryProvider
from promptic.blueprints import DataSlot, MemorySlot
from promptic.context import AdapterNotRegisteredError


class DummyDataAdapter(BaseDataAdapter):
    def fetch(self, slot: DataSlot) -> Any:
        return {"slot": slot.name, "adapter": "dummy"}


class DummyMemoryProvider(BaseMemoryProvider):
    def load(self, slot: MemorySlot) -> Any:
        return ["memory", slot.name]


def test_register_and_create_adapters() -> None:
    registry = AdapterRegistry()
    registry.register_data("dummy", DummyDataAdapter)
    registry.register_memory("mem", DummyMemoryProvider)

    data_adapter = registry.create_data_adapter("dummy")
    memory_adapter = registry.create_memory_provider("mem")

    assert data_adapter.fetch(DataSlot(name="sources", adapter_key="dummy"))["slot"] == "sources"
    assert memory_adapter.load(MemorySlot(name="prior", provider_key="mem"))[0] == "memory"


def test_missing_adapter_raises() -> None:
    registry = AdapterRegistry()
    with pytest.raises(AdapterNotRegisteredError):
        registry.create_memory_provider("missing")


def test_entry_point_loading(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = AdapterRegistry()

    class StubEntryPoint:
        def __init__(self, name: str, payload: object) -> None:
            self.name = name
            self._payload = payload

        def load(self) -> object:
            return self._payload

    monkeypatch.setattr(
        "promptic.adapters.registry._iter_entry_points",
        lambda group: [StubEntryPoint("ep_data", DummyDataAdapter)],
    )

    registry.load_entry_points("promptic.adapters")
    assert "ep_data" in registry.available_data_keys()
