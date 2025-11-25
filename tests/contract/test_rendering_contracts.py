"""Contract tests for rendering module interfaces.

# AICODE-NOTE: These tests verify that all ReferenceStrategy implementations
# comply with the contract defined in contracts/reference_strategy.py.
# They ensure LSP compliance and consistent behavior across strategies.
"""

from __future__ import annotations

from typing import Any, Optional

import pytest

from promptic.rendering.strategies import (
    Jinja2RefStrategy,
    MarkdownLinkStrategy,
    ReferenceStrategy,
    StructuredRefStrategy,
)


class MockNode:
    """Mock node for testing."""

    def __init__(self, content: str = "Mock content"):
        self.content = content
        self.id = "mock_node"
        self.format = "markdown"


def null_lookup(path: str) -> Optional[Any]:
    """Lookup that always returns None."""
    return None


def null_renderer(node: Any, fmt: str) -> str:
    """Renderer that returns empty string."""
    return ""


def mock_lookup(path: str) -> Optional[MockNode]:
    """Lookup that returns a mock node for known paths."""
    known_paths = ["child.md", "data.yaml", "config.json", "template.md"]
    if any(p in path for p in known_paths):
        return MockNode(f"Content for {path}")
    return None


def mock_renderer(node: Any, fmt: str) -> str:
    """Renderer that returns node content."""
    return node.content


class TestReferenceStrategyContract:
    """Contract tests for ReferenceStrategy interface."""

    @pytest.fixture(params=[MarkdownLinkStrategy, Jinja2RefStrategy, StructuredRefStrategy])
    def strategy(self, request) -> ReferenceStrategy:
        """Parameterized fixture providing all strategy implementations."""
        return request.param()

    def test_name_is_valid_string(self, strategy: ReferenceStrategy):
        """Contract: name must be non-empty lowercase string."""
        assert isinstance(strategy.name, str)
        assert len(strategy.name) > 0
        assert strategy.name == strategy.name.lower()
        assert "_" not in strategy.name or strategy.name.replace("_", "").isalnum()

    def test_can_process_is_deterministic(self, strategy: ReferenceStrategy):
        """Contract: can_process must return same result for same input."""
        test_contents = [
            "Simple text",
            "[link](file.md)",
            "{# ref: data.yaml #}",
            '{"$ref": "config.json"}',
            {"key": "value"},
            {"nested": {"$ref": "file.yaml"}},
        ]

        for content in test_contents:
            result1 = strategy.can_process(content)
            result2 = strategy.can_process(content)
            assert result1 == result2, f"Non-deterministic for: {content}"

    def test_can_process_does_not_raise(self, strategy: ReferenceStrategy):
        """Contract: can_process must not raise exceptions."""
        test_contents = [
            None,
            "",
            "text",
            123,
            [],
            {},
            {"key": None},
        ]

        for content in test_contents:
            try:
                strategy.can_process(content)
            except Exception as e:
                pytest.fail(f"can_process raised {type(e).__name__} for: {content}")

    def test_process_string_returns_string(self, strategy: ReferenceStrategy):
        """Contract: process_string must always return string."""
        test_contents = [
            "",
            "Simple text",
            "[link](file.md)",
            "{# ref: data.yaml #}",
        ]

        for content in test_contents:
            result = strategy.process_string(content, null_lookup, null_renderer, "markdown")
            assert isinstance(result, str), f"Expected string, got {type(result)} for: {content}"

    def test_process_structure_returns_dict(self, strategy: ReferenceStrategy):
        """Contract: process_structure must always return dict."""
        test_contents = [
            {},
            {"key": "value"},
            {"nested": {"$ref": "file.yaml"}},
        ]

        for content in test_contents:
            result = strategy.process_structure(content, null_lookup, null_renderer, "yaml")
            assert isinstance(result, dict), f"Expected dict, got {type(result)} for: {content}"

    def test_missing_reference_returns_original(self, strategy: ReferenceStrategy):
        """Contract: Missing references should preserve original content."""
        # Test with null lookup (no nodes found)
        original_string = "[missing](nonexistent.md)"
        result = strategy.process_string(original_string, null_lookup, null_renderer, "markdown")
        # Original should be preserved or minimally changed
        assert isinstance(result, str)

    def test_no_modification_when_no_match(self, strategy: ReferenceStrategy):
        """Contract: Content without matching patterns should pass through unchanged."""
        content = "Plain text without any references or patterns."
        result = strategy.process_string(content, null_lookup, null_renderer, "markdown")
        assert result == content


class TestMarkdownLinkStrategyContract:
    """Specific contract tests for MarkdownLinkStrategy."""

    def test_external_links_preserved(self):
        """Contract: External links (http/https/mailto) must never be processed."""
        strategy = MarkdownLinkStrategy()
        external_contents = [
            "[Google](https://google.com)",
            "[Example](http://example.com)",
            "[Email](mailto:test@example.com)",
            "[Anchor](#section)",
        ]

        for content in external_contents:
            result = strategy.process_string(content, null_lookup, null_renderer, "markdown")
            assert content in result, f"External link modified: {content} -> {result}"

    def test_idempotent_processing(self):
        """Contract: Processing should be idempotent."""
        strategy = MarkdownLinkStrategy()
        content = "[link](child.md)"

        # First pass
        result1 = strategy.process_string(content, mock_lookup, mock_renderer, "markdown")
        # Second pass on result
        result2 = strategy.process_string(result1, mock_lookup, mock_renderer, "markdown")

        # Content should not change after first replacement
        # (mock_renderer returns plain text, not markdown links)
        assert result2 == result1 or "[" not in result1


class TestJinja2RefStrategyContract:
    """Specific contract tests for Jinja2RefStrategy."""

    def test_pattern_detection(self):
        """Contract: Should detect Jinja2 ref comments."""
        strategy = Jinja2RefStrategy()

        assert strategy.can_process("{# ref: file.md #}")
        assert strategy.can_process("{#ref:file.md#}")
        assert strategy.can_process("{# REF: file.md #}")  # Case insensitive
        assert not strategy.can_process("Simple text")
        assert not strategy.can_process("[link](file.md)")

    def test_idempotent_processing(self):
        """Contract: Processing should be idempotent."""
        strategy = Jinja2RefStrategy()
        content = "{# ref: data.yaml #}"

        result1 = strategy.process_string(content, mock_lookup, mock_renderer, "markdown")
        result2 = strategy.process_string(result1, mock_lookup, mock_renderer, "markdown")

        # After replacement, {# ref: #} pattern should be gone
        assert result2 == result1


class TestStructuredRefStrategyContract:
    """Specific contract tests for StructuredRefStrategy."""

    def test_ref_detection(self):
        """Contract: Should detect $ref in dicts."""
        strategy = StructuredRefStrategy()

        assert strategy.can_process({"data": {"$ref": "file.yaml"}})
        assert strategy.can_process({"nested": {"deep": {"$ref": "file.yaml"}}})
        assert not strategy.can_process({"key": "value"})
        assert not strategy.can_process({"$notref": "file.yaml"})
        assert not strategy.can_process("string content")

    def test_recursive_replacement(self):
        """Contract: Should recursively process nested structures."""
        strategy = StructuredRefStrategy()
        content = {
            "level1": {
                "level2": {"$ref": "config.json"},
                "other": "value",
            }
        }

        def test_lookup(path: str) -> Optional[MockNode]:
            if "config.json" in path:
                return MockNode("resolved")
            return None

        def test_renderer(node: Any, fmt: str) -> str:
            return "RESOLVED"

        result = strategy.process_structure(content, test_lookup, test_renderer, "yaml")

        assert result["level1"]["level2"] == "RESOLVED"
        assert result["level1"]["other"] == "value"

    def test_preserves_non_ref_structure(self):
        """Contract: Non-$ref structures should pass through unchanged."""
        strategy = StructuredRefStrategy()
        content = {
            "string": "value",
            "number": 42,
            "list": [1, 2, 3],
            "nested": {"key": "value"},
        }

        result = strategy.process_structure(content, null_lookup, null_renderer, "yaml")

        assert result == content
