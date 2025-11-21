"""Jinja2 format parser implementation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from promptic.context.nodes.errors import FormatParseError, JSONConversionError
from promptic.context.nodes.models import NodeReference
from promptic.format_parsers.base import FormatParser


class Jinja2Parser(FormatParser):
    """Parser for Jinja2 template format files.

    # AICODE-NOTE: This parser recognizes Jinja2 template syntax and preserves
    it in JSON format. Template variables and comments may contain references
    that are extracted during reference extraction.
    """

    def detect(self, content: str, path: Path) -> bool:
        """Detect if content is Jinja2 format based on file extension."""
        return path.suffix.lower() in {".jinja", ".jinja2"}

    def parse(self, content: str, path: Path) -> dict[str, Any]:
        """Parse Jinja2 template content - store as raw string only.

        # AICODE-NOTE: Jinja2 files are treated as plain text strings.
        No structure extraction is performed - the template content is stored as-is.
        """
        try:
            # Jinja2 is just a string - no structure parsing
            return {
                "raw_content": content,
            }
        except Exception as e:
            raise FormatParseError(f"Failed to parse Jinja2 from {path}: {e}") from e

    def to_json(self, parsed: dict[str, Any]) -> dict[str, Any]:
        """Convert parsed Jinja2 to canonical JSON representation.

        # AICODE-NOTE: Jinja2 is stored as raw_content string only.
        Template syntax is preserved as-is and will be rendered later during template rendering.
        """
        try:
            return parsed
        except Exception as e:
            raise JSONConversionError(f"Failed to convert Jinja2 to JSON: {e}") from e

    def extract_references(self, parsed: dict[str, Any]) -> list[NodeReference]:
        """Extract references from Jinja2 template variables and comments.

        Recognizes references in template variables and comments.
        """
        references = []
        raw_content = parsed.get("raw_content", "")

        # Look for file references in comments {# ref: path/to/file.md #}
        ref_comment_pattern = re.compile(r"\{\#\s*ref:\s*([^\#]+)\s*\#\}", re.IGNORECASE)
        comment_matches = ref_comment_pattern.findall(raw_content)
        for match in comment_matches:
            path = match.strip()
            if path and not path.startswith(("http://", "https://")):
                references.append(NodeReference(path=path, type="file", label=None))

        # Look for references in variables {{ include('path/to/file.md') }}
        include_pattern = re.compile(r"include\(['\"]([^'\"]+)['\"]\)", re.IGNORECASE)
        include_matches = include_pattern.findall(raw_content)
        for match in include_matches:
            path = match.strip()
            if path and not path.startswith(("http://", "https://")):
                references.append(NodeReference(path=path, type="file", label=None))

        return references
