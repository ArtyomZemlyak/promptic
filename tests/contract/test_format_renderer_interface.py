import pytest

from promptic.blueprints.models import InstructionNode
from promptic.context.template_context import InstructionRenderContext
from promptic.pipeline.format_renderers.base import FormatRenderer
from promptic.pipeline.template_renderer import TemplateRenderer


def test_markdown_renderer_implements_interface():
    from promptic.pipeline.format_renderers.markdown import MarkdownFormatRenderer

    assert issubclass(MarkdownFormatRenderer, FormatRenderer)

    renderer = MarkdownFormatRenderer()
    assert isinstance(renderer, FormatRenderer)
    assert hasattr(renderer, "render")
    assert hasattr(renderer, "supports_format")


def test_template_renderer_routes_formats_correctly():
    renderer = TemplateRenderer()
    context = InstructionRenderContext(data={"value": "demo"})

    markdown_node = InstructionNode(
        instruction_id="md-contract",
        source_uri="file://md.md",
        format="md",
        checksum="0" * 32,
    )
    jinja_node = InstructionNode(
        instruction_id="jinja-contract",
        source_uri="file://jinja.jinja",
        format="jinja",
        checksum="0" * 32,
    )
    txt_node = InstructionNode(
        instruction_id="txt-contract",
        source_uri="file://plain.txt",
        format="txt",
        checksum="0" * 32,
    )

    md_result = renderer.render(markdown_node, "Value: {data.value}", context)
    assert md_result == "Value: demo"

    jinja_result = renderer.render(jinja_node, "Value: {{ data.value }}", context)
    assert "Value: demo" in jinja_result

    txt_result = renderer.render(txt_node, "Value: {data.value}", context)
    assert txt_result == "Value: {data.value}"
