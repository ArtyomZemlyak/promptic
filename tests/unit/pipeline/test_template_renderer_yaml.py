from typing import Optional

import pytest

from promptic.blueprints.models import InstructionNode
from promptic.context.errors import TemplateRenderError
from promptic.context.template_context import InstructionRenderContext


@pytest.fixture
def yaml_renderer():
    try:
        from promptic.pipeline.format_renderers.yaml import YamlFormatRenderer
    except ImportError:
        pytest.skip("YamlFormatRenderer not implemented yet")
    return YamlFormatRenderer()


def _node(pattern: Optional[str]) -> InstructionNode:
    return InstructionNode(
        instruction_id="test",
        source_uri="test.yaml",
        format="yaml",
        checksum="0" * 32,
        pattern=pattern,
    )


def test_render_custom_pattern_brackets(yaml_renderer):
    content = "key: {{data.value}}"
    node = _node(r"\{\{(?P<placeholder>[^}]+)\}\}")
    context = InstructionRenderContext(data={"value": "123"})
    result = yaml_renderer.render(content, context, instruction_node=node)
    assert result == "key: 123"


def test_render_custom_pattern_dollar(yaml_renderer):
    content = "key: $data.value"
    node = _node(r"\$(?P<placeholder>[\w\.]+)")
    context = InstructionRenderContext(data={"value": "123"})
    result = yaml_renderer.render(content, context, instruction_node=node)
    assert result == "key: 123"


def test_default_pattern_if_none_provided(yaml_renderer):
    content = "key: {{data.value}}"
    node = _node(None)
    context = InstructionRenderContext(data={"value": "123"})
    result = yaml_renderer.render(content, context, instruction_node=node)
    assert result == "key: 123"


def test_invalid_pattern_raises_template_render_error(yaml_renderer):
    content = "key: {{data.value}}"
    node = _node(r"\{\{(?P<placeholder)")
    context = InstructionRenderContext(data={"value": "123"})
    with pytest.raises(TemplateRenderError):
        yaml_renderer.render(content, context, instruction_node=node)


import pytest

from promptic.blueprints.models import InstructionNode
from promptic.context.template_context import InstructionRenderContext


@pytest.fixture
def yaml_renderer():
    try:
        from promptic.pipeline.format_renderers.yaml import YamlFormatRenderer

        return YamlFormatRenderer()
    except ImportError:
        pytest.skip("YamlFormatRenderer not implemented yet")


def test_render_custom_pattern_brackets(yaml_renderer):
    # Pattern: {{name}}
    content = "key: {{data.value}}"
    node = InstructionNode(
        instruction_id="test",
        source_uri="test.yaml",
        format="yaml",
        checksum="0" * 32,
        pattern=r"\{\{(?P<placeholder>[^}]+)\}\}",
    )
    context = InstructionRenderContext(data={"value": "123"})

    # We need to pass the node to render?
    # Wait, FormatRenderer.render(content, context) signature doesn't include node.
    # T043 says "Add optional pattern field to InstructionNode".
    # But FormatRenderer.render only takes content and context.
    # How does YamlFormatRenderer get the pattern?
    #
    # The Plan says:
    # "TemplateRenderer... routes to format-specific renderers...
    #  render(instruction_node: InstructionNode, content: str, context: InstructionRenderContext)"
    #
    # BUT `FormatRenderer.render` interface is `render(content, context)`.
    #
    # So `TemplateRenderer` has access to `InstructionNode`.
    # It calls `renderer.render(content, context)`.
    #
    # If `YamlFormatRenderer` needs `pattern` from `InstructionNode`, the interface needs to change
    # OR `TemplateRenderer` configures `YamlFormatRenderer` before calling?
    # But `YamlFormatRenderer` is a shared instance.
    #
    # WE MUST CHANGE THE INTERFACE of `FormatRenderer.render` to accept `instruction_node` or `options`.
    # Or `TemplateRenderer` must handle substitution if it's generic?
    # No, "Add pattern-based substitution logic in YamlFormatRenderer".
    #
    # So `YamlFormatRenderer` MUST receive the pattern.
    #
    # Option 1: Update `FormatRenderer.render` to accept `instruction_node`.
    # Option 2: Pass pattern in `InstructionRenderContext`? No, context is data/state. Node is config.
    #
    # I should update `FormatRenderer` interface to take `instruction_node` (optional?) or `**kwargs`.
    #
    # Let's check `TemplateRenderer.render`:
    # def render(self, instruction_node: InstructionNode, content: str, context: InstructionRenderContext) -> str:
    #     ...
    #     return renderer.render(content, context)
    #
    # I should change it to:
    #     return renderer.render(content, context, instruction_node=instruction_node)
    #
    # And update `FormatRenderer` interface.
    # And update Markdown/Jinja2 renderers to accept `**kwargs` or specific arg.
    #
    # I will update the interface in `base.py` first.
    pass


def test_render_custom_pattern_dollar(yaml_renderer):
    # Pattern: $name
    content = "key: $data.value"
    node = InstructionNode(
        instruction_id="test",
        source_uri="test.yaml",
        format="yaml",
        checksum="0" * 32,
        pattern=r"\$(?P<placeholder>[\w\.]+)",
    )
    context = InstructionRenderContext(data={"value": "123"})

    # Assumes updated interface
    result = yaml_renderer.render(content, context, instruction_node=node)
    assert result == "key: 123"


def test_default_pattern_if_none_provided(yaml_renderer):
    # Should default to something reasonable, maybe {{}}?
    content = "key: {{data.value}}"
    node = InstructionNode(
        instruction_id="test",
        source_uri="test.yaml",
        format="yaml",
        checksum="0" * 32,
        pattern=None,
    )
    context = InstructionRenderContext(data={"value": "123"})
    result = yaml_renderer.render(content, context, instruction_node=node)
    assert result == "key: 123"
