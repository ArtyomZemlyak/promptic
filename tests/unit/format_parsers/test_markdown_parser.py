"""Unit tests for Markdown parser."""

from pathlib import Path

import pytest

from promptic.context.nodes.errors import FormatParseError
from promptic.format_parsers.markdown_parser import MarkdownParser


def test_markdown_parser_format_detection_md_extension():
    """Test Markdown parser detects .md extension."""
    parser = MarkdownParser()
    content = "# Heading"
    path = Path("test.md")

    assert parser.detect(content, path) is True


def test_markdown_parser_format_detection_markdown_extension():
    """Test Markdown parser detects .markdown extension."""
    parser = MarkdownParser()
    content = "# Heading"
    path = Path("test.markdown")

    assert parser.detect(content, path) is True


def test_markdown_parser_format_detection_non_markdown_extension():
    """Test Markdown parser rejects non-Markdown extensions."""
    parser = MarkdownParser()
    content = "# Heading"
    path = Path("test.yaml")

    assert parser.detect(content, path) is False


def test_markdown_parser_parsing_and_json_conversion():
    """Test Markdown parser parses content and preserves structure in JSON."""
    parser = MarkdownParser()
    content = """# Main Heading

This is a paragraph.

## Subheading

- Item 1
- Item 2
"""
    path = Path("test.md")

    parsed = parser.parse(content, path)
    assert isinstance(parsed, dict)

    json_content = parser.to_json(parsed)
    assert isinstance(json_content, dict)
    # Structure should be preserved - check for raw_content which contains the markdown
    assert "raw_content" in json_content
