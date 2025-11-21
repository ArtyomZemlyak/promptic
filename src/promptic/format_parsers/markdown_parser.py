"""Markdown format parser implementation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from promptic.context.nodes.errors import FormatParseError, JSONConversionError
from promptic.context.nodes.models import NodeReference
from promptic.format_parsers.base import FormatParser


class MarkdownParser(FormatParser):
    """Parser for Markdown format files.

    # AICODE-NOTE: This parser recognizes Markdown link syntax [label](path)
    for references. Markdown structure is preserved in JSON format with content
    stored as text and metadata extracted from headings and structure.
    """

    def detect(self, content: str, path: Path) -> bool:
        """Detect if content is Markdown format based on file extension."""
        return path.suffix.lower() in {".md", ".markdown"}

    def parse(self, content: str, path: Path) -> dict[str, Any]:
        """Parse Markdown content - store as raw string only.

        # AICODE-NOTE: Markdown files are treated as plain text strings.
        No structure extraction is performed - the content is stored as-is.
        """
        try:
            # Markdown is just a string - no structure parsing
            return {
                "raw_content": content,
            }
        except Exception as e:
            raise FormatParseError(f"Failed to parse Markdown from {path}: {e}") from e

    def to_json(self, parsed: dict[str, Any]) -> dict[str, Any]:
        """Convert parsed Markdown to canonical JSON representation.

        # AICODE-NOTE: Markdown is stored as raw_content string only.
        Link syntax is preserved in raw_content and will be extracted by extract_references().
        """
        try:
            return parsed
        except Exception as e:
            raise JSONConversionError(f"Failed to convert Markdown to JSON: {e}") from e

    def extract_references(self, parsed: dict[str, Any]) -> list[NodeReference]:
        """Extract references from Markdown link syntax [label](path).

        Recognizes Markdown link syntax: [label](path/to/file.md)
        """
        references = []
        link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

        # Extract from raw_content if available
        raw_content = parsed.get("raw_content", "")
        matches = link_pattern.findall(raw_content)

        for label, path in matches:
            # Only include file references (not URLs)
            if not path.startswith(("http://", "https://", "mailto:")):
                references.append(NodeReference(path=path, type="file", label=label))

        return references
