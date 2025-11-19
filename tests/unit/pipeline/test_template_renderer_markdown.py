import pytest

from promptic.context.template_context import InstructionRenderContext
from promptic.pipeline.format_renderers.markdown_hierarchy import MarkdownHierarchyParser

# We'll need to import MarkdownFormatRenderer eventually
# For now we test the logic we expect


@pytest.fixture
def markdown_renderer():
    try:
        from promptic.pipeline.format_renderers.markdown import MarkdownFormatRenderer

        return MarkdownFormatRenderer()
    except ImportError:
        pytest.skip("MarkdownFormatRenderer not implemented yet")


def test_render_simple_placeholder(markdown_renderer):
    content = "Hello {data.name}!"
    context = InstructionRenderContext(data={"name": "World"})
    result = markdown_renderer.render(content, context)
    assert result == "Hello World!"


def test_render_missing_placeholder_raises_error(markdown_renderer):
    from promptic.context.errors import TemplateRenderError

    content = "Hello {data.missing}!"
    context = InstructionRenderContext(data={})
    with pytest.raises(TemplateRenderError) as exc:
        markdown_renderer.render(content, context)
    assert exc.value.context["placeholder"] == "data.missing"


def test_render_escaping(markdown_renderer):
    content = "Use {{braces}} for placeholder {data.name}"
    context = InstructionRenderContext(data={"name": "value"})
    result = markdown_renderer.render(content, context)
    assert result == "Use {braces} for placeholder value"


def test_markdown_hierarchy_parser_extracts_sections():
    parser = MarkdownHierarchyParser()
    content = """## Parent Step
Intro
### Child Step
Child body
"""
    hierarchy = parser.parse(content)

    assert len(hierarchy.sections) == 1
    parent = hierarchy.sections[0]
    assert parent.title == "Parent Step"
    assert len(parent.children) == 1
    assert parent.children[0].title == "Child Step"


def test_markdown_hierarchy_parser_extracts_conditionals():
    parser = MarkdownHierarchyParser()
    content = """Intro
<!-- if:data.show_details -->
Detailed Section
<!-- endif -->
"""
    conditionals = parser.extract_conditionals(content)

    assert len(conditionals) == 1
    conditional = conditionals[0]
    assert conditional.condition == "data.show_details"
    assert "Detailed Section" in conditional.content


def test_markdown_renderer_handles_object_attributes(markdown_renderer):
    class User:
        def __init__(self, name: str) -> None:
            self.name = name

    content = "User: {data.user.name}"
    context = InstructionRenderContext(data={"user": User("Grace")})
    result = markdown_renderer.render(content, context)
    assert result == "User: Grace"
