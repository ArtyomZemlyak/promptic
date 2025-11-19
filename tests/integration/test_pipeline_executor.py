from __future__ import annotations

from pathlib import Path
from typing import Any

from promptic.adapters import AdapterRegistry, BaseDataAdapter
from promptic.adapters.registry import AdapterFactory
from promptic.blueprints import DataSlot
from promptic.sdk import adapters as sdk_adapters
from promptic.sdk import pipeline as sdk_pipeline
from promptic.sdk.api import build_materializer
from promptic.settings.base import ContextEngineSettings


class StaticListAdapter(BaseDataAdapter):
    def __init__(self, items: list[dict[str, Any]] | None = None) -> None:
        super().__init__(None)
        self._items = items or [{"title": "A"}, {"title": "B"}]

    def fetch(self, slot: DataSlot) -> list[dict[str, Any]]:
        return list(self._items)


def _write_blueprint(tmp_path: Path) -> ContextEngineSettings:
    blueprint_root = tmp_path / "blueprints"
    instruction_root = tmp_path / "instructions"
    blueprint_root.mkdir()
    instruction_root.mkdir()

    (instruction_root / "collect.md").write_text("Collect step", encoding="utf-8")
    (instruction_root / "detail.md").write_text("Detail step", encoding="utf-8")

    blueprint_root.joinpath("pipeline.yaml").write_text(
        """
name: Integration Executor
prompt_template: Integration test
steps:
  - step_id: collect
    title: Collect Items
    kind: loop
    loop_slot: records
    instruction_refs:
      - instruction_id: collect
    children:
      - step_id: describe
        title: Describe Item
        kind: sequence
        instruction_refs:
          - instruction_id: detail
data_slots:
  - name: records
    adapter_key: integration_records
    schema:
      type: array
memory_slots:
  - name: history
    provider_key: integration_memory
""",
        encoding="utf-8",
    )

    return ContextEngineSettings(
        blueprint_root=blueprint_root,
        instruction_root=instruction_root,
        log_root=tmp_path / "logs",
    )


def test_pipeline_executor_walks_loop_steps(tmp_path: Path) -> None:
    settings = _write_blueprint(tmp_path)
    registry = AdapterRegistry()

    def _make_adapter(_: Any = None) -> BaseDataAdapter:
        return StaticListAdapter([{"title": "First"}, {"title": "Second"}])

    adapter_factory: AdapterFactory[BaseDataAdapter] = _make_adapter
    sdk_adapters.register_data_adapter(
        key="integration_records",
        adapter=adapter_factory,
        registry=registry,
    )
    sdk_adapters.register_static_memory_provider(key="integration_memory", registry=registry)

    materializer = build_materializer(settings=settings, registry=registry)
    response = sdk_pipeline.run_pipeline(
        blueprint_id="pipeline",
        settings=settings,
        materializer=materializer,
    )

    assert len(response.events) >= 4
    instruction_events = [e for e in response.events if e.event_type == "instruction_loaded"]
    assert instruction_events, "Executor should emit instruction events."
    sizes = [e for e in response.events if e.event_type == "size_warning"]
    assert sizes == [], "No size warnings expected for short instructions."
