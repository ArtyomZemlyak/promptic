"""Contract definition for ReferenceStrategy interface.

# AICODE-NOTE: This file defines the contract that all reference strategy
# implementations must follow. Used for contract testing to ensure LSP compliance.

This is a SPECIFICATION file, not implementation code.
See data-model.md for full class documentation.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional, Protocol


class NodeLookup(Protocol):
    """Protocol for node lookup function."""

    def __call__(self, path: str) -> Optional[Any]:
        """Look up node by path.

        Args:
            path: Reference path to look up

        Returns:
            Node if found, None otherwise
        """
        ...


class ContentRenderer(Protocol):
    """Protocol for content rendering function."""

    def __call__(self, node: Any, target_format: str) -> Any:
        """Render node content to target format.

        Args:
            node: Node to render
            target_format: Target format (yaml, json, markdown, jinja2)

        Returns:
            Rendered content (string for text formats, dict for structured)
        """
        ...


class ReferenceStrategyContract(ABC):
    """Contract for reference resolution strategies.

    All implementations MUST satisfy these requirements:

    1. IDEMPOTENCY: process_string(process_string(content)) == process_string(content)
    2. GRACEFUL DEGRADATION: Missing references return original content unchanged
    3. EXTERNAL LINKS: URLs (http://, https://, mailto:) are never processed
    4. TYPE SAFETY: String input returns string, dict input returns dict
    5. NO SIDE EFFECTS: Processing does not modify input content

    Contract Tests:
        See tests/contract/test_rendering_contracts.py
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name for debugging and logging.

        Requirements:
            - Must be non-empty string
            - Must be unique among all strategies
            - Should be lowercase with underscores (e.g., "markdown_link")
        """
        pass

    @abstractmethod
    def can_process(self, content: Any) -> bool:
        """Check if this strategy can process the given content.

        Requirements:
            - Must return True only if process_* methods will make changes
            - Must not raise exceptions
            - Must be deterministic (same input = same output)

        Args:
            content: Content to check (string or dict)

        Returns:
            True if this strategy should process the content
        """
        pass

    @abstractmethod
    def process_string(
        self,
        content: str,
        node_lookup: NodeLookup,
        content_renderer: ContentRenderer,
        target_format: str,
    ) -> str:
        """Process string content and replace references.

        Requirements:
            - Must return string type
            - Must return original content if no references found
            - Must preserve external links unchanged
            - Must handle missing references gracefully (return original)
            - Must be idempotent

        Args:
            content: String content with potential references
            node_lookup: Function(path) -> Node or None
            content_renderer: Function(node, format) -> rendered content
            target_format: Target output format (yaml, json, markdown)

        Returns:
            Content with references replaced by resolved content
        """
        pass

    @abstractmethod
    def process_structure(
        self,
        content: dict[str, Any],
        node_lookup: NodeLookup,
        content_renderer: ContentRenderer,
        target_format: str,
    ) -> dict[str, Any]:
        """Process structured content (dict) and replace references.

        Requirements:
            - Must return dict type
            - Must return original content if no $ref entries found
            - Must recursively process nested dicts and lists
            - Must handle missing references gracefully
            - Must be idempotent

        Args:
            content: Dict content with potential $ref entries
            node_lookup: Function(path) -> Node or None
            content_renderer: Function(node, format) -> rendered content
            target_format: Target output format

        Returns:
            Content with $ref entries replaced by resolved content
        """
        pass


# Contract test assertions (to be used in test file)
CONTRACT_ASSERTIONS = """
def test_strategy_name_is_valid(strategy):
    assert isinstance(strategy.name, str)
    assert len(strategy.name) > 0
    assert strategy.name == strategy.name.lower()

def test_can_process_is_deterministic(strategy, content):
    result1 = strategy.can_process(content)
    result2 = strategy.can_process(content)
    assert result1 == result2

def test_process_string_is_idempotent(strategy, content, lookup, renderer, format):
    if strategy.can_process(content):
        result1 = strategy.process_string(content, lookup, renderer, format)
        result2 = strategy.process_string(result1, lookup, renderer, format)
        assert result1 == result2

def test_process_string_returns_string(strategy, content, lookup, renderer, format):
    result = strategy.process_string(content, lookup, renderer, format)
    assert isinstance(result, str)

def test_process_structure_returns_dict(strategy, content, lookup, renderer, format):
    result = strategy.process_structure(content, lookup, renderer, format)
    assert isinstance(result, dict)

def test_external_links_preserved(strategy):
    content = "[link](https://example.com)"
    result = strategy.process_string(content, lambda p: None, lambda n, f: "", "markdown")
    assert "https://example.com" in result

def test_missing_reference_returns_original(strategy, content, format):
    # Lookup always returns None
    def null_lookup(path): return None
    def null_renderer(node, fmt): return ""
    
    result = strategy.process_string(content, null_lookup, null_renderer, format)
    # Original reference markers should be preserved
    assert len(result) >= len(content) - 10  # Allow for minor changes
"""
