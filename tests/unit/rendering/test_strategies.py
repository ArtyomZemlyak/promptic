"""Unit tests for reference resolution strategies.

# AICODE-NOTE: These tests verify the behavior of individual strategy
# implementations in isolation. They test the regex patterns, edge cases,
# and format-specific behavior.
"""

from __future__ import annotations

from typing import Any, Optional

import pytest

from promptic.rendering.strategies import (
    Jinja2RefStrategy,
    MarkdownLinkStrategy,
    StructuredRefStrategy,
)


class MockNode:
    """Mock node for testing."""

    def __init__(self, content: str = "Mock content", fmt: str = "markdown"):
        self.content = {"raw_content": content}
        self.id = "mock_node"
        self.format = fmt


def create_lookup(nodes: dict[str, MockNode]):
    """Create a lookup function from a dict of path -> node mappings."""

    def lookup(path: str) -> Optional[MockNode]:
        for key, node in nodes.items():
            if path == key or path in key or key.endswith(path):
                return node
        return None

    return lookup


def simple_renderer(node: Any, fmt: str) -> str:
    """Simple renderer that returns raw_content or the node itself."""
    if hasattr(node, "content") and "raw_content" in node.content:
        return node.content["raw_content"]
    return str(node)


class TestMarkdownLinkStrategy:
    """Unit tests for MarkdownLinkStrategy."""

    @pytest.fixture
    def strategy(self) -> MarkdownLinkStrategy:
        return MarkdownLinkStrategy()

    def test_name(self, strategy: MarkdownLinkStrategy):
        """Test strategy name."""
        assert strategy.name == "markdown_link"

    def test_can_process_with_link(self, strategy: MarkdownLinkStrategy):
        """Test detection of markdown links."""
        assert strategy.can_process("[text](file.md)")
        assert strategy.can_process("Some text [link](path/to/file.md) more text")
        assert strategy.can_process("[Link Label](./relative/path.md)")

    def test_can_process_without_link(self, strategy: MarkdownLinkStrategy):
        """Test non-matching content."""
        assert not strategy.can_process("Plain text")
        assert not strategy.can_process("{# ref: file.md #}")
        assert not strategy.can_process('{"$ref": "file.yaml"}')
        assert not strategy.can_process("")

    def test_can_process_non_string(self, strategy: MarkdownLinkStrategy):
        """Test with non-string content."""
        assert not strategy.can_process({"key": "value"})
        assert not strategy.can_process([1, 2, 3])
        assert not strategy.can_process(None)

    def test_replace_single_link(self, strategy: MarkdownLinkStrategy):
        """Test replacing a single markdown link."""
        content = "[Include](child.md)"
        nodes = {"child.md": MockNode("Child Content")}
        lookup = create_lookup(nodes)

        result = strategy.process_string(content, lookup, simple_renderer, "markdown")

        assert result == "Child Content"

    def test_replace_multiple_links(self, strategy: MarkdownLinkStrategy):
        """Test replacing multiple markdown links."""
        content = "Start [First](a.md) middle [Second](b.md) end"
        nodes = {
            "a.md": MockNode("A"),
            "b.md": MockNode("B"),
        }
        lookup = create_lookup(nodes)

        result = strategy.process_string(content, lookup, simple_renderer, "markdown")

        assert result == "Start A middle B end"

    def test_preserve_external_http(self, strategy: MarkdownLinkStrategy):
        """Test that http:// links are preserved."""
        content = "[Google](https://google.com)"
        result = strategy.process_string(content, lambda p: None, simple_renderer, "markdown")
        assert result == content

    def test_preserve_external_https(self, strategy: MarkdownLinkStrategy):
        """Test that https:// links are preserved."""
        content = "[Secure](https://secure.example.com)"
        result = strategy.process_string(content, lambda p: None, simple_renderer, "markdown")
        assert result == content

    def test_preserve_mailto(self, strategy: MarkdownLinkStrategy):
        """Test that mailto: links are preserved."""
        content = "[Email](mailto:test@example.com)"
        result = strategy.process_string(content, lambda p: None, simple_renderer, "markdown")
        assert result == content

    def test_preserve_anchor(self, strategy: MarkdownLinkStrategy):
        """Test that anchor links (#) are preserved."""
        content = "[Section](#section-1)"
        result = strategy.process_string(content, lambda p: None, simple_renderer, "markdown")
        assert result == content

    def test_missing_reference_preserved(self, strategy: MarkdownLinkStrategy):
        """Test that missing references keep original link."""
        content = "[Missing](nonexistent.md)"
        result = strategy.process_string(content, lambda p: None, simple_renderer, "markdown")
        assert result == content

    def test_mixed_local_and_external(self, strategy: MarkdownLinkStrategy):
        """Test content with both local and external links."""
        content = "[Local](local.md) and [External](https://example.com)"
        nodes = {"local.md": MockNode("Local Content")}
        lookup = create_lookup(nodes)

        result = strategy.process_string(content, lookup, simple_renderer, "markdown")

        assert "Local Content" in result
        assert "[External](https://example.com)" in result

    def test_process_structure_returns_unchanged(self, strategy: MarkdownLinkStrategy):
        """Test that process_structure returns dict unchanged."""
        content = {"key": "[link](file.md)"}
        result = strategy.process_structure(content, lambda p: None, simple_renderer, "markdown")
        assert result == content


class TestJinja2RefStrategy:
    """Unit tests for Jinja2RefStrategy."""

    @pytest.fixture
    def strategy(self) -> Jinja2RefStrategy:
        return Jinja2RefStrategy()

    def test_name(self, strategy: Jinja2RefStrategy):
        """Test strategy name."""
        assert strategy.name == "jinja2_ref"

    def test_can_process_with_ref(self, strategy: Jinja2RefStrategy):
        """Test detection of Jinja2 ref comments."""
        assert strategy.can_process("{# ref: file.md #}")
        assert strategy.can_process("{#ref:file.md#}")
        assert strategy.can_process("{# ref: path/to/file.yaml #}")
        assert strategy.can_process("Text {# ref: data.yaml #} more text")

    def test_can_process_case_insensitive(self, strategy: Jinja2RefStrategy):
        """Test that ref detection is case insensitive."""
        assert strategy.can_process("{# REF: file.md #}")
        assert strategy.can_process("{# Ref: file.md #}")
        assert strategy.can_process("{# rEf: file.md #}")

    def test_can_process_without_ref(self, strategy: Jinja2RefStrategy):
        """Test non-matching content."""
        assert not strategy.can_process("Plain text")
        assert not strategy.can_process("[link](file.md)")
        assert not strategy.can_process("{# comment #}")  # Regular Jinja2 comment
        assert not strategy.can_process("")

    def test_can_process_non_string(self, strategy: Jinja2RefStrategy):
        """Test with non-string content."""
        assert not strategy.can_process({"key": "value"})
        assert not strategy.can_process([1, 2, 3])
        assert not strategy.can_process(None)

    def test_replace_single_ref(self, strategy: Jinja2RefStrategy):
        """Test replacing a single Jinja2 ref."""
        content = "{# ref: data.yaml #}"
        nodes = {"data.yaml": MockNode("YAML Content")}
        lookup = create_lookup(nodes)

        result = strategy.process_string(content, lookup, simple_renderer, "markdown")

        assert result == "YAML Content"

    def test_replace_with_whitespace_variations(self, strategy: Jinja2RefStrategy):
        """Test ref with different whitespace."""
        test_cases = [
            "{#ref:data.yaml#}",
            "{# ref:data.yaml #}",
            "{#  ref:  data.yaml  #}",
            "{# ref: data.yaml #}",
        ]
        nodes = {"data.yaml": MockNode("Content")}
        lookup = create_lookup(nodes)

        for content in test_cases:
            result = strategy.process_string(content, lookup, simple_renderer, "markdown")
            assert result == "Content", f"Failed for: {content}"

    def test_replace_in_context(self, strategy: Jinja2RefStrategy):
        """Test ref replacement within surrounding content."""
        content = "Before {# ref: data.yaml #} After"
        nodes = {"data.yaml": MockNode("MIDDLE")}
        lookup = create_lookup(nodes)

        result = strategy.process_string(content, lookup, simple_renderer, "markdown")

        assert result == "Before MIDDLE After"

    def test_missing_reference_preserved(self, strategy: Jinja2RefStrategy):
        """Test that missing references keep original ref comment."""
        content = "{# ref: nonexistent.yaml #}"
        result = strategy.process_string(content, lambda p: None, simple_renderer, "markdown")
        assert result == content

    def test_process_structure_returns_unchanged(self, strategy: Jinja2RefStrategy):
        """Test that process_structure returns dict unchanged."""
        content = {"key": "{# ref: file.yaml #}"}
        result = strategy.process_structure(content, lambda p: None, simple_renderer, "yaml")
        assert result == content


class TestStructuredRefStrategy:
    """Unit tests for StructuredRefStrategy."""

    @pytest.fixture
    def strategy(self) -> StructuredRefStrategy:
        return StructuredRefStrategy()

    def test_name(self, strategy: StructuredRefStrategy):
        """Test strategy name."""
        assert strategy.name == "structured_ref"

    def test_can_process_with_ref(self, strategy: StructuredRefStrategy):
        """Test detection of $ref in dicts."""
        assert strategy.can_process({"data": {"$ref": "file.yaml"}})
        assert strategy.can_process({"nested": {"deep": {"$ref": "file.yaml"}}})
        assert strategy.can_process({"list": [{"$ref": "file.yaml"}]})

    def test_can_process_without_ref(self, strategy: StructuredRefStrategy):
        """Test dicts without $ref."""
        assert not strategy.can_process({"key": "value"})
        assert not strategy.can_process({"nested": {"key": "value"}})
        assert not strategy.can_process({})

    def test_can_process_non_dict(self, strategy: StructuredRefStrategy):
        """Test with non-dict content."""
        assert not strategy.can_process("string")
        assert not strategy.can_process([1, 2, 3])
        assert not strategy.can_process(None)

    def test_replace_single_ref(self, strategy: StructuredRefStrategy):
        """Test replacing a single $ref."""
        content = {"config": {"$ref": "config.yaml"}}
        nodes = {"config.yaml": MockNode("Config Content")}
        lookup = create_lookup(nodes)

        result = strategy.process_structure(content, lookup, simple_renderer, "yaml")

        assert result == {"config": "Config Content"}

    def test_replace_nested_ref(self, strategy: StructuredRefStrategy):
        """Test replacing nested $ref."""
        content = {
            "level1": {
                "level2": {
                    "data": {"$ref": "nested.yaml"},
                }
            }
        }
        nodes = {"nested.yaml": MockNode("Nested Content")}
        lookup = create_lookup(nodes)

        result = strategy.process_structure(content, lookup, simple_renderer, "yaml")

        assert result["level1"]["level2"]["data"] == "Nested Content"

    def test_replace_multiple_refs(self, strategy: StructuredRefStrategy):
        """Test replacing multiple $refs at same level."""
        content = {
            "a": {"$ref": "a.yaml"},
            "b": {"$ref": "b.yaml"},
        }
        nodes = {
            "a.yaml": MockNode("A Content"),
            "b.yaml": MockNode("B Content"),
        }
        lookup = create_lookup(nodes)

        result = strategy.process_structure(content, lookup, simple_renderer, "yaml")

        assert result == {"a": "A Content", "b": "B Content"}

    def test_preserve_non_ref_values(self, strategy: StructuredRefStrategy):
        """Test that non-$ref values are preserved."""
        content = {
            "string": "value",
            "number": 42,
            "boolean": True,
            "null": None,
            "list": [1, 2, 3],
        }

        result = strategy.process_structure(content, lambda p: None, simple_renderer, "yaml")

        assert result == content

    def test_missing_ref_preserved(self, strategy: StructuredRefStrategy):
        """Test that missing $ref keeps original object."""
        content = {"data": {"$ref": "nonexistent.yaml"}}
        result = strategy.process_structure(content, lambda p: None, simple_renderer, "yaml")
        assert result == content

    def test_refs_in_list(self, strategy: StructuredRefStrategy):
        """Test $ref inside list items."""
        content = {
            "items": [
                {"$ref": "a.yaml"},
                {"other": "value"},
                {"$ref": "b.yaml"},
            ]
        }
        nodes = {
            "a.yaml": MockNode("A"),
            "b.yaml": MockNode("B"),
        }
        lookup = create_lookup(nodes)

        result = strategy.process_structure(content, lookup, simple_renderer, "yaml")

        assert result["items"][0] == "A"
        assert result["items"][1] == {"other": "value"}
        assert result["items"][2] == "B"

    def test_process_string_returns_unchanged(self, strategy: StructuredRefStrategy):
        """Test that process_string returns string unchanged."""
        content = '{"$ref": "file.yaml"}'
        result = strategy.process_string(content, lambda p: None, simple_renderer, "yaml")
        assert result == content
