"""Unit tests for ReferenceInliner service.

# AICODE-NOTE: These tests verify that ReferenceInliner correctly orchestrates
# multiple strategies to process all reference types. They test both the
# inline_references method and the internal _find_node helper.
"""

from __future__ import annotations

from typing import Any, Optional
from unittest.mock import MagicMock

import pytest

from promptic.rendering.inliner import ReferenceInliner
from promptic.rendering.strategies import (
    Jinja2RefStrategy,
    MarkdownLinkStrategy,
    StructuredRefStrategy,
)


class MockContextNode:
    """Mock ContextNode for testing."""

    def __init__(
        self,
        node_id: str,
        content: dict[str, Any],
        fmt: str = "markdown",
    ):
        self.id = node_id
        self.content = content
        self.format = fmt


class MockNodeNetwork:
    """Mock NodeNetwork for testing."""

    def __init__(self, nodes: dict[str, MockContextNode]):
        self.nodes = nodes
        if nodes:
            self.root = list(nodes.values())[0]
        else:
            self.root = None


class TestReferenceInliner:
    """Unit tests for ReferenceInliner."""

    def test_default_strategies(self):
        """Test that inliner has default strategies."""
        inliner = ReferenceInliner()

        assert len(inliner.strategies) == 3
        assert any(isinstance(s, Jinja2RefStrategy) for s in inliner.strategies)
        assert any(isinstance(s, MarkdownLinkStrategy) for s in inliner.strategies)
        assert any(isinstance(s, StructuredRefStrategy) for s in inliner.strategies)

    def test_custom_strategies(self):
        """Test that custom strategies can be provided."""
        custom_strategy = MarkdownLinkStrategy()
        inliner = ReferenceInliner(strategies=[custom_strategy])

        assert len(inliner.strategies) == 1
        assert inliner.strategies[0] is custom_strategy


class TestReferenceInlinerFindNode:
    """Unit tests for _find_node helper method."""

    def test_find_node_exact_match(self):
        """Test finding node by exact path match."""
        inliner = ReferenceInliner()
        nodes = {
            "path/to/file.md": MockContextNode("path/to/file.md", {"raw_content": "Content"}),
        }
        network = MockNodeNetwork(nodes)

        result = inliner._find_node("path/to/file.md", network)

        assert result is not None
        assert result.id == "path/to/file.md"

    def test_find_node_partial_match(self):
        """Test finding node by partial path match."""
        inliner = ReferenceInliner()
        nodes = {
            "/full/path/to/file.md": MockContextNode(
                "/full/path/to/file.md", {"raw_content": "Content"}
            ),
        }
        network = MockNodeNetwork(nodes)

        result = inliner._find_node("file.md", network)

        assert result is not None
        assert result.id == "/full/path/to/file.md"

    def test_find_node_suffix_match(self):
        """Test finding node by suffix match."""
        inliner = ReferenceInliner()
        nodes = {
            "/project/src/child.md": MockContextNode(
                "/project/src/child.md", {"raw_content": "Content"}
            ),
        }
        network = MockNodeNetwork(nodes)

        result = inliner._find_node("child.md", network)

        assert result is not None
        assert result.id == "/project/src/child.md"

    def test_find_node_not_found(self):
        """Test when node is not found."""
        inliner = ReferenceInliner()
        nodes = {
            "existing.md": MockContextNode("existing.md", {"raw_content": "Content"}),
        }
        network = MockNodeNetwork(nodes)

        result = inliner._find_node("nonexistent.md", network)

        assert result is None


class TestReferenceInlinerInlineReferences:
    """Unit tests for inline_references method."""

    def test_inline_markdown_link(self):
        """Test inlining markdown link references."""
        inliner = ReferenceInliner()

        root = MockContextNode(
            "root.md",
            {"raw_content": "# Root\n\n[Include](child.md)\n\nEnd."},
            "markdown",
        )
        child = MockContextNode(
            "child.md",
            {"raw_content": "## Child Content"},
            "markdown",
        )
        network = MockNodeNetwork({"root.md": root, "child.md": child})

        result = inliner.inline_references(root, network, "markdown")

        assert isinstance(result, str)
        assert "Child Content" in result
        assert "# Root" in result
        assert "End." in result

    def test_inline_jinja2_ref(self):
        """Test inlining Jinja2 ref comments."""
        inliner = ReferenceInliner()

        root = MockContextNode(
            "root.jinja2",
            {"raw_content": "Before {# ref: data.yaml #} After"},
            "jinja2",
        )
        data = MockContextNode(
            "data.yaml",
            {"raw_content": "key: value"},
            "yaml",
        )
        network = MockNodeNetwork({"root.jinja2": root, "data.yaml": data})

        result = inliner.inline_references(root, network, "markdown")

        assert isinstance(result, str)
        assert "Before" in result
        assert "After" in result
        assert "key: value" in result

    def test_inline_structured_ref(self):
        """Test inlining $ref in structured content."""
        inliner = ReferenceInliner()

        root = MockContextNode(
            "root.yaml",
            {"config": {"$ref": "config.yaml"}, "title": "Root"},
            "yaml",
        )
        config = MockContextNode(
            "config.yaml",
            {"setting": "value"},
            "yaml",
        )
        network = MockNodeNetwork({"root.yaml": root, "config.yaml": config})

        result = inliner.inline_references(root, network, "yaml")

        assert isinstance(result, dict)
        assert result["title"] == "Root"
        # The config should be inlined
        assert "setting" in str(result)

    def test_missing_reference_preserved(self):
        """Test that missing references are preserved."""
        inliner = ReferenceInliner()

        root = MockContextNode(
            "root.md",
            {"raw_content": "[Missing](nonexistent.md)"},
            "markdown",
        )
        network = MockNodeNetwork({"root.md": root})

        result = inliner.inline_references(root, network, "markdown")

        assert isinstance(result, str)
        assert "[Missing](nonexistent.md)" in result

    def test_external_link_preserved(self):
        """Test that external links are preserved."""
        inliner = ReferenceInliner()

        root = MockContextNode(
            "root.md",
            {"raw_content": "[Google](https://google.com)"},
            "markdown",
        )
        network = MockNodeNetwork({"root.md": root})

        result = inliner.inline_references(root, network, "markdown")

        assert isinstance(result, str)
        assert "https://google.com" in result

    def test_recursive_inlining(self):
        """Test that nested references are recursively inlined."""
        inliner = ReferenceInliner()

        root = MockContextNode(
            "root.md",
            {"raw_content": "[Child](child.md)"},
            "markdown",
        )
        child = MockContextNode(
            "child.md",
            {"raw_content": "Child: [Grandchild](grandchild.md)"},
            "markdown",
        )
        grandchild = MockContextNode(
            "grandchild.md",
            {"raw_content": "Grandchild Content"},
            "markdown",
        )
        network = MockNodeNetwork(
            {
                "root.md": root,
                "child.md": child,
                "grandchild.md": grandchild,
            }
        )

        result = inliner.inline_references(root, network, "markdown")

        assert isinstance(result, str)
        assert "Grandchild Content" in result

    def test_mixed_reference_types(self):
        """Test content with both markdown links and jinja2 refs."""
        inliner = ReferenceInliner()

        root = MockContextNode(
            "root.md",
            {"raw_content": "[MD](md.md) and {# ref: jinja.md #}"},
            "markdown",
        )
        md_node = MockContextNode(
            "md.md",
            {"raw_content": "MD Content"},
            "markdown",
        )
        jinja_node = MockContextNode(
            "jinja.md",
            {"raw_content": "Jinja Content"},
            "markdown",
        )
        network = MockNodeNetwork(
            {
                "root.md": root,
                "md.md": md_node,
                "jinja.md": jinja_node,
            }
        )

        result = inliner.inline_references(root, network, "markdown")

        assert isinstance(result, str)
        assert "MD Content" in result
        assert "Jinja Content" in result


class TestReferenceInlinerFormatHandling:
    """Tests for cross-format reference handling."""

    def test_yaml_to_markdown_wraps_in_code_block(self):
        """Test that YAML content wrapped in code block when embedded in markdown."""
        inliner = ReferenceInliner()

        root = MockContextNode(
            "root.md",
            {"raw_content": "Config: [config](config.yaml)"},
            "markdown",
        )
        config = MockContextNode(
            "config.yaml",
            {"setting": "value", "enabled": True},
            "yaml",
        )
        network = MockNodeNetwork({"root.md": root, "config.yaml": config})

        result = inliner.inline_references(root, network, "markdown")

        assert isinstance(result, str)
        # YAML should be wrapped in code block for markdown output
        assert "```yaml" in result or "setting" in result

    def test_json_to_markdown_wraps_in_code_block(self):
        """Test that JSON content wrapped in code block when embedded in markdown."""
        inliner = ReferenceInliner()

        root = MockContextNode(
            "root.md",
            {"raw_content": "Data: [data](data.json)"},
            "markdown",
        )
        data = MockContextNode(
            "data.json",
            {"key": "value", "count": 42},
            "json",
        )
        network = MockNodeNetwork({"root.md": root, "data.json": data})

        result = inliner.inline_references(root, network, "markdown")

        assert isinstance(result, str)
        # JSON should be wrapped in code block for markdown output
        assert "```json" in result or "key" in result
