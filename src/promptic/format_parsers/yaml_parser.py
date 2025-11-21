"""YAML format parser implementation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from promptic.context.nodes.errors import (
    FormatParseError,
    JSONConversionError,
    ReferenceSyntaxError,
)
from promptic.context.nodes.models import NodeReference
from promptic.format_parsers.base import FormatParser


class YAMLParser(FormatParser):
    """Parser for YAML format files.

    # AICODE-NOTE: This parser recognizes YAML $ref: syntax for references.
    References are converted to canonical NodeReference format during JSON conversion.
    YAML content is parsed and converted to JSON as the canonical internal representation.
    """

    def detect(self, content: str, path: Path) -> bool:
        """Detect if content is YAML format based on file extension.

        This method uses file extension as the primary detection signal. YAML files
        typically have .yaml or .yml extensions. Content analysis is not performed
        as YAML syntax can be ambiguous without extension context.

        Side Effects:
            - No state mutation (pure function)
            - No I/O operations

        Args:
            content: File content as string (not used for detection)
            path: File path with extension

        Returns:
            True if file extension is .yaml or .yml (case-insensitive)

        Example:
            >>> parser = YAMLParser()
            >>> parser.detect("", Path("config.yaml"))
            True
            >>> parser.detect("", Path("config.yml"))
            True
            >>> parser.detect("", Path("config.json"))
            False
        """
        return path.suffix.lower() in {".yaml", ".yml"}

    def parse(self, content: str, path: Path) -> dict[str, Any]:
        """Parse YAML content into structured dictionary.

        Uses yaml.safe_load() for safe YAML parsing. Handles edge cases:
        - Empty/null content returns empty dict
        - Non-dict content (scalars, lists) wrapped in dict with "content" key
        - Preserves YAML structure including nested dicts and lists

        Side Effects:
            - No state mutation (pure function)
            - Uses yaml library for parsing

        Args:
            content: YAML content as string
            path: File path (used for error messages)

        Returns:
            Structured dictionary representation of YAML content. Always returns
            a dict (empty dict for null/empty content, wrapped dict for scalars/lists).

        Raises:
            FormatParseError: If YAML parsing fails (syntax errors, invalid YAML).
                Error message includes file path and original exception details.

        Example:
            >>> parser = YAMLParser()
            >>> parsed = parser.parse("name: test\\nvalue: 42", Path("test.yaml"))
            >>> assert parsed["name"] == "test"
            >>> assert parsed["value"] == 42
        """
        try:
            parsed = yaml.safe_load(content)
            if parsed is None:
                return {}
            if not isinstance(parsed, dict):
                # Wrap non-dict content in a dict
                return {"content": parsed}
            return parsed
        except yaml.YAMLError as e:
            raise FormatParseError(f"Failed to parse YAML from {path}: {e}") from e

    def to_json(self, parsed: dict[str, Any]) -> dict[str, Any]:
        """Convert parsed YAML to canonical JSON representation.

        YAML content is already JSON-compatible (dict, list, str, int, float, bool, None),
        so conversion is straightforward - the parsed dict is returned as-is. This preserves
        the original structure while normalizing to the canonical JSON format used internally.

        # AICODE-NOTE: YAML $ref: syntax is preserved as-is in the JSON structure
        and will be extracted by extract_references(). The conversion strategy ensures
        format-agnostic processing while maintaining reference information.

        Side Effects:
            - No state mutation (pure function)
            - Validates JSON compatibility (raises error if incompatible types found)

        Args:
            parsed: Parsed YAML content from parse() method

        Returns:
            JSON-compatible dictionary. Same structure as input (YAML is JSON-compatible).

        Raises:
            JSONConversionError: If conversion fails (should not occur for valid YAML,
                but included for interface compliance). This would indicate a bug in
                the parser or non-JSON-compatible YAML types.

        Example:
            >>> parser = YAMLParser()
            >>> parsed = {"name": "test", "value": 42}
            >>> json_content = parser.to_json(parsed)
            >>> assert json_content == parsed
        """
        try:
            # YAML is already JSON-compatible, return as-is
            return parsed
        except Exception as e:
            raise JSONConversionError(f"Failed to convert YAML to JSON: {e}") from e

    def extract_references(self, parsed: dict[str, Any]) -> list[NodeReference]:
        """Extract references from YAML $ref: syntax.

        Recognizes YAML reference syntax in two forms:
        1. Dictionary key: `$ref: path/to/file.yaml` (as dict key)
        2. String value: `"$ref: path/to/file.yaml"` (as string value with regex)

        The method recursively traverses the YAML structure to find all references,
        converting them to canonical NodeReference objects with type="file".

        Side Effects:
            - No state mutation (pure function)
            - Recursively traverses parsed structure

        Args:
            parsed: Parsed YAML content from parse() method

        Returns:
            List of NodeReference objects extracted from YAML content. Each reference
            has type="file" and path set to the referenced file path. Labels are None
            (YAML $ref: syntax doesn't support labels).

        Example:
            >>> parser = YAMLParser()
            >>> parsed = {
            ...     "steps": [{"$ref": "instructions/analyze.md"}],
            ...     "data": "$ref: data/sources.json"
            ... }
            >>> refs = parser.extract_references(parsed)
            >>> assert len(refs) == 2
            >>> assert refs[0].path == "instructions/analyze.md"
        """
        references = []
        ref_pattern = re.compile(r"\$ref:\s*(.+)", re.IGNORECASE)

        def extract_from_value(value: Any) -> None:
            """Recursively extract references from YAML structure."""
            if isinstance(value, dict):
                for key, val in value.items():
                    if isinstance(key, str) and key.lower() == "$ref":
                        if isinstance(val, str):
                            references.append(
                                NodeReference(path=val.strip(), type="file", label=None)
                            )
                    else:
                        extract_from_value(val)
            elif isinstance(value, list):
                for item in value:
                    extract_from_value(item)
            elif isinstance(value, str):
                # Check for $ref: syntax in string values
                matches = ref_pattern.findall(value)
                for match in matches:
                    references.append(NodeReference(path=match.strip(), type="file", label=None))

        extract_from_value(parsed)
        return references
