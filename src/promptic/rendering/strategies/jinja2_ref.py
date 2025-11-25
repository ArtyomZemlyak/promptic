"""Strategy for processing Jinja2-style reference comments.

# AICODE-NOTE: This strategy handles Jinja2 comment-style references
# used for including external files in templates. The pattern uses
# Jinja2 comment syntax to be invisible in rendered templates.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Optional

from promptic.rendering.strategies.base import ReferenceStrategy


class Jinja2RefStrategy(ReferenceStrategy):
    """Strategy for processing Jinja2-style reference comments.

    Pattern: \\{\\#\\s*ref:\\s*([^\\#]+)\\s*\\#\\}
    Example: {# ref: data.yaml #} -> content of data.yaml

    This uses Jinja2 comment syntax so references are invisible when
    templates are rendered without reference processing.
    """

    REF_PATTERN = re.compile(r"\{\#\s*ref:\s*([^\#]+)\s*\#\}", re.IGNORECASE)

    @property
    def name(self) -> str:
        return "jinja2_ref"

    def can_process(self, content: Any) -> bool:
        """Check if content contains Jinja2 ref comments."""
        if isinstance(content, str):
            return bool(self.REF_PATTERN.search(content))
        return False

    def process_string(
        self,
        content: str,
        node_lookup: Callable[[str], Optional[Any]],
        content_renderer: Callable[[Any, str], str],
        target_format: str,
    ) -> str:
        """Process string content and replace Jinja2 ref comments with referenced content."""

        def replace_ref(match: re.Match[str]) -> str:
            path = match.group(1).strip()
            node = node_lookup(path)
            if node:
                return content_renderer(node, target_format)
            return match.group(0)

        return self.REF_PATTERN.sub(replace_ref, content)

    def process_structure(
        self,
        content: dict[str, Any],
        node_lookup: Callable[[str], Optional[Any]],
        content_renderer: Callable[[Any, str], Any],
        target_format: str,
    ) -> dict[str, Any]:
        """Jinja2 refs are string-based, not in structured content, return as-is."""
        return content
