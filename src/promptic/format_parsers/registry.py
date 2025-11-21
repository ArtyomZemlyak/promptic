"""Format parser registry for managing format parsers."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from promptic.context.nodes.errors import FormatDetectionError
from promptic.format_parsers.base import FormatParser

if TYPE_CHECKING:
    from promptic.format_parsers.jinja2_parser import Jinja2Parser
    from promptic.format_parsers.json_parser import JSONParser
    from promptic.format_parsers.markdown_parser import MarkdownParser
    from promptic.format_parsers.yaml_parser import YAMLParser


class FormatParserRegistry:
    """Registry for managing format parsers.

    # AICODE-NOTE: This registry intentionally couples format detection and
    parser selection. This is acceptable because format detection is a core
    responsibility of the registry, and the coupling enables efficient parser
    lookup. The registry maintains a mapping of file extensions to format names
    and format names to parser instances.
    """

    def __init__(self) -> None:
        """Initialize registry with default parsers."""
        self._parsers: dict[str, FormatParser] = {}
        self._extensions: dict[str, str] = {}

    def register(self, format_name: str, parser: FormatParser, extensions: list[str]) -> None:
        """Register a parser for a format.

        Args:
            format_name: Name of the format (e.g., "yaml", "markdown")
            parser: Parser instance implementing FormatParser interface
            extensions: List of file extensions for this format (e.g., [".yaml", ".yml"])
        """
        self._parsers[format_name] = parser
        for ext in extensions:
            self._extensions[ext.lower()] = format_name

    def detect_format(self, content: str, path: Path) -> str:
        """Detect format from content and path.

        # AICODE-NOTE: Format detection strategy:
        1. First, try file extension-based detection (primary signal)
        2. If extension doesn't match, try content-based detection (fallback)
        3. Raise FormatDetectionError if no format can be detected

        Args:
            content: File content as string
            path: File path for extension-based detection

        Returns:
            Format name (e.g., "yaml", "markdown")

        Raises:
            FormatDetectionError: If format cannot be detected
        """
        # Try extension-based detection first
        ext = path.suffix.lower()
        if ext in self._extensions:
            format_name = self._extensions[ext]
            # Verify parser can detect this content
            parser = self._parsers[format_name]
            if parser.detect(content, path):
                return format_name

        # Fallback to content-based detection
        for format_name, parser in self._parsers.items():
            if parser.detect(content, path):
                return format_name

        raise FormatDetectionError(f"Could not detect format for {path}")

    def get_parser(self, format_name: str) -> FormatParser:
        """Get parser for a format.

        Args:
            format_name: Name of the format

        Returns:
            FormatParser instance

        Raises:
            KeyError: If format is not registered
        """
        if format_name not in self._parsers:
            raise KeyError(f"Format '{format_name}' is not registered")
        return self._parsers[format_name]


# Global registry instance with default parsers
_default_registry: FormatParserRegistry | None = None


def get_default_registry() -> FormatParserRegistry:
    """Get the default format parser registry with all parsers registered.

    # AICODE-NOTE: Default parsers are registered on first access to enable
    lazy initialization and avoid circular import issues.
    """
    global _default_registry
    if _default_registry is None:
        _default_registry = FormatParserRegistry()

        # Register default parsers
        from promptic.format_parsers.jinja2_parser import Jinja2Parser
        from promptic.format_parsers.json_parser import JSONParser
        from promptic.format_parsers.markdown_parser import MarkdownParser
        from promptic.format_parsers.yaml_parser import YAMLParser

        _default_registry.register("yaml", YAMLParser(), [".yaml", ".yml"])
        _default_registry.register("markdown", MarkdownParser(), [".md", ".markdown"])
        _default_registry.register("jinja2", Jinja2Parser(), [".jinja", ".jinja2"])
        _default_registry.register("json", JSONParser(), [".json"])

    return _default_registry
