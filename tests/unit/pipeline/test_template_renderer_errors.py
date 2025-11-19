from typing import Optional

import pytest

from promptic.blueprints.models import InstructionFallbackPolicy, InstructionNode
from promptic.context.errors import TemplateRenderError
from promptic.context.template_context import InstructionRenderContext
from promptic.pipeline.template_renderer import TemplateRenderer


def _make_instruction_node(
    *,
    fallback_policy: InstructionFallbackPolicy,
    placeholder_template: Optional[str] = None,
) -> InstructionNode:
    payload = {
        "instruction_id": f"jinja-{fallback_policy.value}",
        "source_uri": "file:///jinja/instruction",
        "format": "jinja",
        "checksum": "0" * 32,
        "fallback_policy": fallback_policy,
    }
    if placeholder_template:
        payload["placeholder_template"] = placeholder_template
    return InstructionNode(**payload)


def test_error_policy_raises_template_render_error():
    renderer = TemplateRenderer()
    node = _make_instruction_node(fallback_policy=InstructionFallbackPolicy.ERROR)
    context = InstructionRenderContext(data={})
    content = "{% if data.value %}"

    with pytest.raises(TemplateRenderError):
        renderer.render(node, content, context)


def test_warn_policy_returns_placeholder_with_warning_message(caplog):
    renderer = TemplateRenderer()
    node = _make_instruction_node(
        fallback_policy=InstructionFallbackPolicy.WARN,
        placeholder_template="[placeholder for {instruction_id}]",
    )
    context = InstructionRenderContext(data={})
    content = "{% if data.value %}"

    with caplog.at_level("WARNING"):
        rendered = renderer.render(node, content, context)

    assert rendered == "[placeholder for jinja-warn]"
    assert any("Template rendering failed" in message for message in caplog.messages)


def test_noop_policy_returns_empty_string():
    renderer = TemplateRenderer()
    node = _make_instruction_node(fallback_policy=InstructionFallbackPolicy.NOOP)
    context = InstructionRenderContext(data={})
    content = "{% if data.value %}"

    rendered = renderer.render(node, content, context)

    assert rendered == ""
