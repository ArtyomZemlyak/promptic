from __future__ import annotations

from pathlib import Path

import pytest

from promptic.adapters import AdapterRegistry, BaseDataAdapter
from promptic.adapters.data import CSVAdapterSettings, CSVDataAdapter
from promptic.adapters.memory import StaticMemoryProvider, StaticMemorySettings
from promptic.blueprints import DataSlot, MemorySlot
from promptic.context import AdapterRegistrationError


def test_csv_adapter_reads_rows(tmp_path: Path) -> None:
    csv_path = tmp_path / "records.csv"
    csv_path.write_text("title,url\nDoc A,https://a\n", encoding="utf-8")
    adapter = CSVDataAdapter(CSVAdapterSettings(path=csv_path))

    rows = adapter.fetch(DataSlot(name="records", adapter_key="csv"))

    assert rows == [{"title": "Doc A", "url": "https://a"}]


def test_static_memory_provider_returns_configured_values() -> None:
    provider = StaticMemoryProvider(StaticMemorySettings(values=["a", "b"]))
    slot = MemorySlot(name="history", provider_key="memory")

    assert provider.load(slot) == ["a", "b"]


def test_registry_prevents_duplicate_keys() -> None:
    registry = AdapterRegistry()
    registry.register_data("csv", CSVDataAdapter, config_model=CSVAdapterSettings)

    with pytest.raises(AdapterRegistrationError):
        registry.register_data("csv", CSVDataAdapter)
