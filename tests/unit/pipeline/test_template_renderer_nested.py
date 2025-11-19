import pytest

from promptic.context.template_context import InstructionRenderContext


@pytest.fixture
def markdown_renderer():
    try:
        from promptic.pipeline.format_renderers.markdown import MarkdownFormatRenderer

        return MarkdownFormatRenderer()
    except ImportError:
        pytest.skip("MarkdownFormatRenderer not implemented yet")


def test_nested_access_dot_notation(markdown_renderer):
    content = "User: {data.user.profile.name}"
    data = {"user": {"profile": {"name": "Alice"}}}
    context = InstructionRenderContext(data=data)
    result = markdown_renderer.render(content, context)
    assert result == "User: Alice"


def test_nested_access_deep(markdown_renderer):
    # Test deep nesting (up to 10 levels)
    data = {"level1": {"level2": {"level3": "value"}}}
    content = "Deep: {data.level1.level2.level3}"
    context = InstructionRenderContext(data=data)
    result = markdown_renderer.render(content, context)
    assert result == "Deep: value"


def test_nested_missing_key(markdown_renderer):
    from promptic.context.errors import TemplateRenderError

    data = {"user": {"profile": {}}}
    content = "{data.user.profile.missing}"
    context = InstructionRenderContext(data=data)
    with pytest.raises(TemplateRenderError) as exc:
        markdown_renderer.render(content, context)
    assert "data.user.profile.missing" in str(exc.value) or "missing" in str(exc.value)
