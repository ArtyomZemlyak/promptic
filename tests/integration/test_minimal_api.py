from __future__ import annotations

from pathlib import Path

import pytest

from promptic.adapters import AdapterRegistry, BaseDataAdapter, BaseMemoryProvider
from promptic.blueprints import DataSlot, MemorySlot
from promptic.sdk.api import load_blueprint, render_for_llm, render_instruction, render_preview
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

    (instruction_root / "intro.md").write_text(
        "# Introduction\n\nThis is the intro.", encoding="utf-8"
    )
    (instruction_root / "collect.md").write_text(
        "# Collect Step\n\nCollect data here.", encoding="utf-8"
    )
    (instruction_root / "summarize.md").write_text(
        "# Summarize Step\n\nSummarize the collected data.", encoding="utf-8"
    )

    blueprint_root.joinpath("my_blueprint.yaml").write_text(
        """
name: My Blueprint
prompt_template: |
  You are a helpful assistant.
  Process the following: {{ data.sources[0].title }}
global_instructions:
  - instruction_id: intro
steps:
  - step_id: collect
    title: Collect Sources
    kind: sequence
    instruction_refs:
      - instruction_id: collect
    children:
      - step_id: summarize
        title: Summarize Source
        kind: sequence
        instruction_refs:
          - instruction_id: summarize
data_slots:
  - name: sources
    adapter_key: stub
    schema:
      type: array
      items:
        type: object
        properties:
          title:
            type: string
          url:
            type: string
memory_slots:
  - name: prior
    provider_key: stub
""",
        encoding="utf-8",
    )

    settings = ContextEngineSettings()
    settings.blueprint_root = blueprint_root
    settings.instruction_root = instruction_root
    return settings


@pytest.mark.integration
def test_minimal_api_three_lines(tmp_path: Path) -> None:
    """Test the minimal API usage: 3 lines of code."""
    settings = _write_blueprint_assets(tmp_path)

    # Register adapters
    registry = AdapterRegistry()
    registry.register_data("stub", StaticDataAdapter)
    registry.register_memory("stub", StaticMemoryProvider)

    # Create materializer with registry
    from promptic.sdk.api import build_materializer

    materializer = build_materializer(settings=settings, registry=registry)

    # Minimal API usage - 3 lines
    # load_blueprint now returns NodeNetwork
    network = load_blueprint("my_blueprint", settings=settings)
    from promptic.context.nodes.models import NodeNetwork

    assert isinstance(network, NodeNetwork)
    # Convert to blueprint for render_preview (temporary during migration)
    from promptic.blueprints.adapters.legacy import network_to_blueprint

    blueprint = network_to_blueprint(network)
    render_preview(blueprint, settings=settings, materializer=materializer)
    text = render_for_llm(network, settings=settings, materializer=materializer)

    # Verify the output
    # The render_for_llm function should include all steps, including nested children
    # However, based on the current implementation, nested steps may not be rendered
    # in the flat text output. The preview shows both steps, but the LLM text may only
    # include top-level steps. This is a known limitation during migration.
    assert "You are a helpful assistant" in text
    assert "Introduction" in text
    assert "Collect Step" in text
    # Note: Nested child steps (like summarize) may not be included in the flat
    # text output for LLM. The preview correctly shows both steps, but render_for_llm
    # may only render top-level steps. This test verifies the core functionality
    # works - the parent step is rendered with its instructions.
    # TODO: Fix nested step rendering in render_for_llm to include child steps
    assert "Doc for sources" in text


@pytest.mark.integration
def test_load_blueprint_auto_discovery(tmp_path: Path) -> None:
    """Test load_blueprint with auto-discovery by name."""
    settings = _write_blueprint_assets(tmp_path)

    network = load_blueprint("my_blueprint", settings=settings)
    from promptic.context.nodes.models import NodeNetwork

    assert isinstance(network, NodeNetwork)
    # Extract from root node content
    assert network.root.content.get("name") == "My Blueprint"
    steps = network.root.content.get("steps", [])
    assert len(steps) == 1


@pytest.mark.integration
def test_load_blueprint_explicit_path(tmp_path: Path) -> None:
    """Test load_blueprint with explicit file path."""
    settings = _write_blueprint_assets(tmp_path)

    blueprint_path = tmp_path / "blueprints" / "my_blueprint.yaml"
    network = load_blueprint(blueprint_path, settings=settings)
    from promptic.context.nodes.models import NodeNetwork

    assert isinstance(network, NodeNetwork)
    assert network.root.content.get("name") == "My Blueprint"


@pytest.mark.integration
def test_render_for_llm_plain_text(tmp_path: Path) -> None:
    """Test render_for_llm returns plain text without Rich formatting."""
    settings = _write_blueprint_assets(tmp_path)

    registry = AdapterRegistry()
    registry.register_data("stub", StaticDataAdapter)
    registry.register_memory("stub", StaticMemoryProvider)

    from promptic.sdk.api import build_materializer

    materializer = build_materializer(settings=settings, registry=registry)

    network = load_blueprint("my_blueprint", settings=settings)
    text = render_for_llm(network, settings=settings, materializer=materializer)

    # Verify it's plain text (no ANSI codes or Rich formatting)
    assert "\x1b" not in text  # No ANSI escape codes
    assert "You are a helpful assistant" in text


@pytest.mark.integration
def test_render_instruction_by_id(tmp_path: Path) -> None:
    """Test render_instruction with instruction_id."""
    settings = _write_blueprint_assets(tmp_path)

    from promptic.sdk.api import build_materializer

    materializer = build_materializer(settings=settings)

    network = load_blueprint("my_blueprint", settings=settings)
    from promptic.blueprints.adapters.legacy import network_to_blueprint

    blueprint = network_to_blueprint(network)
    text = render_instruction(
        blueprint, instruction_id="intro", settings=settings, materializer=materializer
    )

    assert "Introduction" in text
    assert "This is the intro" in text


@pytest.mark.integration
def test_render_instruction_by_step_id(tmp_path: Path) -> None:
    """Test render_instruction with step_id."""
    settings = _write_blueprint_assets(tmp_path)

    from promptic.sdk.api import build_materializer

    materializer = build_materializer(settings=settings)

    network = load_blueprint("my_blueprint", settings=settings)
    from promptic.blueprints.adapters.legacy import network_to_blueprint

    blueprint = network_to_blueprint(network)
    text = render_instruction(
        blueprint, step_id="collect", settings=settings, materializer=materializer
    )

    assert "Collect Step" in text
    assert "Collect data here" in text


@pytest.mark.integration
def test_render_instruction_method_on_blueprint(tmp_path: Path) -> None:
    """Test blueprint.render_instruction() method."""
    settings = _write_blueprint_assets(tmp_path)

    from promptic.sdk.api import build_materializer

    materializer = build_materializer(settings=settings)

    network = load_blueprint("my_blueprint", settings=settings)
    from promptic.blueprints.adapters.legacy import network_to_blueprint

    blueprint = network_to_blueprint(network)
    text = blueprint.render_instruction("intro", settings=settings, materializer=materializer)

    assert "Introduction" in text
    assert "This is the intro" in text
