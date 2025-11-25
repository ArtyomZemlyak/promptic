"""Abstract base class for reference resolution strategies.

# AICODE-NOTE: This module defines the Strategy pattern interface for reference resolution.
# Each concrete strategy handles one type of reference pattern:
# - MarkdownLinkStrategy: [text](path) references
# - Jinja2RefStrategy: {# ref: path #} references
# - StructuredRefStrategy: {"$ref": "path"} references

The strategy pattern allows adding new reference types without modifying existing code
(Open/Closed Principle) and each strategy has a single responsibility (SRP).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional


class ReferenceStrategy(ABC):
    """Abstract base class for reference resolution strategies.

    Each strategy handles one type of reference pattern. Strategies are composable
    and can be combined in a ReferenceInliner to process all reference types.

    Contract requirements (see contracts/reference_strategy.py):
    1. IDEMPOTENCY: process_string(process_string(content)) == process_string(content)
    2. GRACEFUL DEGRADATION: Missing references return original content unchanged
    3. EXTERNAL LINKS: URLs (http://, https://, mailto:) are never processed
    4. TYPE SAFETY: String input returns string, dict input returns dict
    5. NO SIDE EFFECTS: Processing does not modify input content
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name for debugging and logging.

        Must be:
        - Non-empty string
        - Unique among all strategies
        - Lowercase with underscores (e.g., "markdown_link")
        """
        pass

    @abstractmethod
    def can_process(self, content: Any) -> bool:
        """Check if this strategy can process the given content.

        Args:
            content: Content to check (string or dict)

        Returns:
            True if this strategy should process the content (contains relevant patterns)
        """
        pass

    @abstractmethod
    def process_string(
        self,
        content: str,
        node_lookup: Callable[[str], Optional[Any]],
        content_renderer: Callable[[Any, str], str],
        target_format: str,
    ) -> str:
        """Process string content and replace references.

        Args:
            content: String content with potential references
            node_lookup: Function(path) -> ContextNode or None
            content_renderer: Function(node, format) -> rendered string
            target_format: Target output format (yaml, json, markdown)

        Returns:
            Content with references replaced by resolved content
        """
        pass

    @abstractmethod
    def process_structure(
        self,
        content: dict[str, Any],
        node_lookup: Callable[[str], Optional[Any]],
        content_renderer: Callable[[Any, str], Any],
        target_format: str,
    ) -> dict[str, Any]:
        """Process structured content (dict) and replace references.

        Args:
            content: Dict content with potential $ref entries
            node_lookup: Function(path) -> ContextNode or None
            content_renderer: Function(node, format) -> rendered content
            target_format: Target output format

        Returns:
            Content with $ref entries replaced by resolved content
        """
        pass
