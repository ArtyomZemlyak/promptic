from __future__ import annotations

from pathlib import Path

from promptic.adapters import AdapterRegistry, BaseDataAdapter, BaseMemoryProvider
from promptic.blueprints import DataSlot, MemorySlot
from promptic.sdk import blueprints as sdk_blueprints
from promptic.sdk.api import PreviewResponse, build_materializer
from promptic.settings.base import ContextEngineSettings


class StaticDataAdapter(BaseDataAdapter):
    def fetch(self, slot: DataSlot) -> list[dict[str, str]]:
        return [{"title": f"Doc for {slot.name}", "url": "https://example.com"}]


class StaticMemoryProvider(BaseMemoryProvider):
    def load(self, slot: MemorySlot) -> list[str]:
        return [f"memory::{slot.name}"]


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
  Hello {{ data.sources[0].title }}
metadata:
  file_first:
    persona: Research curator
    objectives:
      - Collect sources
      - Summaries
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


def test_preview_blueprint_renders_context(tmp_path: Path) -> None:
    settings = _write_blueprint_assets(tmp_path)
    registry = AdapterRegistry()
    registry.register_data("stub", StaticDataAdapter)
    registry.register_memory("stub", StaticMemoryProvider)

    materializer = build_materializer(settings=settings, registry=registry)
    response = sdk_blueprints.preview_blueprint(
        blueprint_id="demo",
        settings=settings,
        materializer=materializer,
    )

    assert isinstance(response, PreviewResponse)
    assert "Demo Flow" in response.rendered_context
    assert "Doc for sources" in response.rendered_context
    assert "memory::prior" in response.rendered_context


def test_preview_blueprint_file_first_mode(tmp_path: Path) -> None:
    settings = _write_blueprint_assets(tmp_path)
    # Inflate instruction content to demonstrate token reduction
    instructions_dir = settings.instruction_root
    (instructions_dir / "collect.md").write_text(" ".join(["token"] * 200), encoding="utf-8")
    (instructions_dir / "intro.md").write_text("Intro", encoding="utf-8")
    registry = AdapterRegistry()
    registry.register_data("stub", StaticDataAdapter)
    registry.register_memory("stub", StaticMemoryProvider)

    materializer = build_materializer(settings=settings, registry=registry)
    response = sdk_blueprints.preview_blueprint(
        blueprint_id="demo",
        settings=settings,
        materializer=materializer,
        render_mode="file_first",
        base_url="https://example.com/kb",
    )

    assert response.markdown
    assert response.metadata
    steps = response.metadata["steps"]
    metrics = response.metadata["metrics"]
    assert steps[0]["reference_path"].startswith("https://example.com/kb")
    assert metrics["tokens_before"] > metrics["tokens_after"]
    assert metrics["reference_count"] == len(steps)
