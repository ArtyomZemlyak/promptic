import textwrap

import pytest

from promptic.blueprints.models import InstructionFallbackPolicy, InstructionNode
from promptic.context.template_context import InstructionRenderContext, StepContext
from promptic.pipeline.template_renderer import TemplateRenderer


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
