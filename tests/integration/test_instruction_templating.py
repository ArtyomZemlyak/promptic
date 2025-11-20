import textwrap
from pathlib import Path

import pytest

from promptic.blueprints.models import (
    BlueprintStep,
    ContextBlueprint,
    InstructionFallbackPolicy,
    InstructionNode,
    InstructionNodeRef,
)
from promptic.context.template_context import InstructionRenderContext, StepContext
from promptic.pipeline.template_renderer import TemplateRenderer
from promptic.sdk.api import build_materializer
from promptic.settings.base import ContextEngineSettings


def _make_instruction_node(format: str, **overrides):
    payload = {
        "instruction_id": overrides.get("instruction_id", f"{format}-instruction"),
        "source_uri": overrides.get("source_uri", f"file:///{format}/instruction"),
        "format": format,
        "checksum": overrides.get("checksum", "0" * 32),
        "fallback_policy": overrides.get("fallback_policy", InstructionFallbackPolicy.ERROR),
        "placeholder_template": overrides.get("placeholder_template"),
    }
    payload.update(overrides)
    return InstructionNode(**payload)


def test_markdown_instruction_rendering_end_to_end():
    renderer = TemplateRenderer()
    node = _make_instruction_node(format="md", instruction_id="markdown-basic")
    content = "Hello {data.user.name}! Today is {memory.date}."
    context = InstructionRenderContext(
        data={"user": {"name": "Ada"}},
        memory={"date": "Friday"},
        blueprint={"name": "demo"},
    )

    rendered = renderer.render(node, content, context)

    assert rendered == "Hello Ada! Today is Friday."


def test_jinja2_rendering_integration():
    renderer = TemplateRenderer()
    node = _make_instruction_node(
        format="jinja",
        instruction_id="jinja-conditional",
        fallback_policy=InstructionFallbackPolicy.ERROR,
    )
    content = textwrap.dedent(
        """
        Task: {{ data.task }}
        {% if data.urgent %}PRIORITY: HIGH{% endif %}
        Steps:
        {% for step_name in data.steps %}
        - {{ loop.index }}. {{ step_name }}
        {% endfor %}
        Owner: {{ memory.owner }}
        Step Context: {{ step.title }}
        """
    ).strip()
    context = InstructionRenderContext(
        data={"task": "Deploy", "urgent": True, "steps": ["Build", "Test", "Release"]},
        memory={"owner": "ops"},
        step=StepContext(step_id="process", title="Process Items", kind="sequence"),
        blueprint={"name": "demo-blueprint"},
    )

    rendered = renderer.render(node, content, context)

    assert "Task: Deploy" in rendered
    assert "PRIORITY: HIGH" in rendered
    assert "- 1. Build" in rendered
    assert "- 3. Release" in rendered
    assert "Owner: ops" in rendered
    assert "Step Context: Process Items" in rendered


def test_markdown_hierarchy_conditionals():
    renderer = TemplateRenderer()
    node = _make_instruction_node(format="md", instruction_id="markdown-conditional")
    content = textwrap.dedent(
        """
        ## Overview
        Always shown
        <!-- if:data.show_details -->
        ### Details
        Include this section when requested.
        <!-- endif -->
        """
    ).strip()

    show_context = InstructionRenderContext(data={"show_details": True})
    hide_context = InstructionRenderContext(data={"show_details": False})

    rendered_with_details = renderer.render(node, content, show_context)
    rendered_without_details = renderer.render(node, content, hide_context)

    assert "Include this section" in rendered_with_details
    assert "Include this section" not in rendered_without_details


def _setup_file_first_materializer(tmp_path: Path):
    instruction_root = tmp_path / "instructions"
    instruction_root.mkdir()
    settings = ContextEngineSettings(
        blueprint_root=tmp_path / "blueprints",
        instruction_root=instruction_root,
        log_root=tmp_path / "logs",
    )
    settings.ensure_directories()
    return settings, build_materializer(settings=settings)


def _write_instruction(root: Path, name: str, content: str) -> None:
    (root / f"{name}.md").write_text(content, encoding="utf-8")


def test_file_first_absolute_links_and_depth_limit(tmp_path: Path) -> None:
    settings, materializer = _setup_file_first_materializer(tmp_path)
    instruction_root = settings.instruction_root
    _write_instruction(instruction_root, "root", "root")
    _write_instruction(instruction_root, "child", "child")
    _write_instruction(instruction_root, "grand", "grand")
    blueprint = ContextBlueprint(
        name="Depth Flow",
        prompt_template="N/A",
        steps=[
            BlueprintStep(
                step_id="root",
                title="Root",
                kind="sequence",
                instruction_refs=[InstructionNodeRef(instruction_id="root")],
                children=[
                    BlueprintStep(
                        step_id="child",
                        title="Child",
                        kind="sequence",
                        instruction_refs=[InstructionNodeRef(instruction_id="child")],
                        children=[
                            BlueprintStep(
                                step_id="grand",
                                title="Grand",
                                kind="sequence",
                                instruction_refs=[InstructionNodeRef(instruction_id="grand")],
                            )
                        ],
                    )
                ],
            )
        ],
        metadata={"file_first": {"persona": "Agent", "objectives": ["Goal"]}},
    )

    renderer = TemplateRenderer()
    result = renderer.render_file_first(
        blueprint=blueprint,
        materializer=materializer,
        base_url="https://example.com/base",
        depth_limit=1,
        summary_overrides={},
    )

    assert result.metadata.steps[0].detail_hint.startswith("See more: https://example.com/base")
    assert result.warnings and "Depth limit" in result.warnings[0]


def test_file_first_memory_block(tmp_path: Path) -> None:
    settings, materializer = _setup_file_first_materializer(tmp_path)
    instruction_root = settings.instruction_root
    _write_instruction(instruction_root, "step", "step")
    (instruction_root / "memory").mkdir(exist_ok=True)
    (instruction_root / "memory" / "format.md").write_text("Memory guidance", encoding="utf-8")
    blueprint = ContextBlueprint(
        name="Memory Flow",
        prompt_template="N/A",
        steps=[
            BlueprintStep(
                step_id="step",
                title="Step",
                kind="sequence",
                instruction_refs=[InstructionNodeRef(instruction_id="step")],
            )
        ],
        metadata={
            "file_first": {
                "persona": "Recorder",
                "objectives": ["Track notes"],
                "memory_channels": [
                    {
                        "location": "memory/log.md",
                        "expected_format": "Markdown log",
                        "format_descriptor_path": "memory/format.md",
                    }
                ],
            }
        },
    )

    renderer = TemplateRenderer()
    result = renderer.render_file_first(
        blueprint=blueprint,
        materializer=materializer,
        base_url=None,
        depth_limit=3,
        summary_overrides={},
    )

    assert result.metadata.memory_channels
    assert result.metadata.memory_channels[0].location == "memory/log.md"
    assert "Memory & Logging" in result.markdown
