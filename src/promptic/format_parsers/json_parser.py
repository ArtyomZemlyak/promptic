"""JSON format parser implementation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from promptic.context.nodes.errors import FormatParseError, JSONConversionError
from promptic.context.nodes.models import NodeReference
from promptic.format_parsers.base import FormatParser


class JSONParser(FormatParser):
    """Parser for JSON format files.

    # AICODE-NOTE: JSON content is already in JSON format, so parsing and
    conversion are straightforward. Structured reference objects are recognized
    and converted to canonical NodeReference format.
    """

    def detect(self, content: str, path: Path) -> bool:
        """Detect if content is JSON format based on file extension."""
        return path.suffix.lower() == ".json"

    def parse(self, content: str, path: Path) -> dict[str, Any]:
        """Parse JSON content into structured dictionary."""
        try:
            parsed = json.loads(content)
            if parsed is None:
                return {}
            if not isinstance(parsed, dict):
                # Wrap non-dict content in a dict
                return {"content": parsed}
            return parsed
        except json.JSONDecodeError as e:
            raise FormatParseError(f"Failed to parse JSON from {path}: {e}") from e

    def to_json(self, parsed: dict[str, Any]) -> dict[str, Any]:
        """Convert parsed JSON to canonical JSON representation.

        # AICODE-NOTE: JSON content is already in JSON format, so conversion
        is a no-op. Structured reference objects are preserved as-is.
        """
        try:
            # JSON is already in JSON format, return as-is
            return parsed
        except Exception as e:
            raise JSONConversionError(f"Failed to convert JSON: {e}") from e

    def extract_references(self, parsed: dict[str, Any]) -> list[NodeReference]:
        """Extract references from structured reference objects.

        Recognizes objects with type="reference" or {"$ref": "path"} syntax.
        """
        references = []

        def extract_from_value(value: Any) -> None:
            """Recursively extract references from JSON structure."""
            if isinstance(value, dict):
                # Check for structured reference object
                if value.get("type") == "reference" and "path" in value:
                    ref_type = value.get("ref_type", "file")
                    label = value.get("label")
                    references.append(NodeReference(path=value["path"], type=ref_type, label=label))
                # Check for $ref syntax
                elif "$ref" in value:
                    ref_path = value["$ref"]
                    if isinstance(ref_path, str):
                        references.append(NodeReference(path=ref_path, type="file", label=None))
                else:
                    for val in value.values():
                        extract_from_value(val)
            elif isinstance(value, list):
                for item in value:
                    extract_from_value(item)

        extract_from_value(parsed)
        return references
