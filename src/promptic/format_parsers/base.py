"""Base interface for format parsers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from promptic.context.nodes.models import NodeReference


class FormatParser(ABC):
    """Interface for format-specific parsing.

    # AICODE-NOTE: This interface defines the contract for all format parsers.
    Each parser must implement format detection, parsing, JSON conversion, and
    reference extraction. The interface enables pluggable parser architecture
    where new formats can be added without modifying core code (OCP principle).
    """

    @abstractmethod
    def detect(self, content: str, path: Path) -> bool:
        """Detect if content matches this format.

        Args:
            content: File content as string
            path: File path for extension-based detection

        Returns:
            True if content matches this format, False otherwise
        """
        pass

    @abstractmethod
    def parse(self, content: str, path: Path) -> dict[str, Any]:
        """Extract structured content from format.

        Args:
            content: File content as string
            path: File path for context

        Returns:
            Parsed content as dictionary

        Raises:
            FormatParseError: If parsing fails
        """
        pass

    @abstractmethod
    def to_json(self, parsed: dict[str, Any]) -> dict[str, Any]:
        """Convert parsed content to canonical JSON representation.

        Args:
            parsed: Parsed content from parse() method

        Returns:
            Content in canonical JSON format

        Raises:
            JSONConversionError: If conversion fails
        """
        pass

    @abstractmethod
    def extract_references(self, parsed: dict[str, Any]) -> list["NodeReference"]:
        """Extract references from format-specific syntax.

        Args:
            parsed: Parsed content from parse() method

        Returns:
            List of node references found in content
        """
        pass
