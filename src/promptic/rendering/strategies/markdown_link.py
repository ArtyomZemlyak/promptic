"""Strategy for processing markdown link references [text](path).

# AICODE-NOTE: This strategy handles markdown-style links that reference
# other files in the node network. External URLs (http://, https://, mailto:, #)
# are preserved unchanged.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Optional

from promptic.rendering.strategies.base import ReferenceStrategy


class MarkdownLinkStrategy(ReferenceStrategy):
    """Strategy for processing markdown link references [text](path).

    Pattern: \\[([^\\]]+)\\]\\(([^)]+)\\)
    Example: [Instructions](instructions.md) -> content of instructions.md

    External links starting with http://, https://, mailto:, or # are preserved.
    """

    LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "#")

    @property
    def name(self) -> str:
        return "markdown_link"

    def can_process(self, content: Any) -> bool:
        """Check if content contains markdown links."""
        if isinstance(content, str):
            return bool(self.LINK_PATTERN.search(content))
        return False

    def process_string(
        self,
        content: str,
        node_lookup: Callable[[str], Optional[Any]],
        content_renderer: Callable[[Any, str], str],
        target_format: str,
    ) -> str:
        """Process string content and replace markdown links with referenced content."""

        def replace_link(match: re.Match[str]) -> str:
            path = match.group(2)

            # Preserve external links
            if path.startswith(self.EXTERNAL_PREFIXES):
                return match.group(0)

            node = node_lookup(path)
            if node:
                return content_renderer(node, target_format)
            return match.group(0)

        return self.LINK_PATTERN.sub(replace_link, content)

    def process_structure(
        self,
        content: dict[str, Any],
        node_lookup: Callable[[str], Optional[Any]],
        content_renderer: Callable[[Any, str], Any],
        target_format: str,
    ) -> dict[str, Any]:
        """Markdown links don't appear in structured content, return as-is."""
        return content
