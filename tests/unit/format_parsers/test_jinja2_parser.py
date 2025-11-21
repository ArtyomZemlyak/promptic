"""Unit tests for Jinja2 parser."""

from pathlib import Path

import pytest

from promptic.context.nodes.errors import FormatParseError
from promptic.format_parsers.jinja2_parser import Jinja2Parser


def test_jinja2_parser_format_detection_jinja_extension():
    """Test Jinja2 parser detects .jinja extension."""
    parser = Jinja2Parser()
    content = "{{ variable }}"
    path = Path("test.jinja")

    assert parser.detect(content, path) is True


def test_jinja2_parser_format_detection_jinja2_extension():
    """Test Jinja2 parser detects .jinja2 extension."""
    parser = Jinja2Parser()
    content = "{{ variable }}"
    path = Path("test.jinja2")

    assert parser.detect(content, path) is True


def test_jinja2_parser_format_detection_non_jinja2_extension():
    """Test Jinja2 parser rejects non-Jinja2 extensions."""
    parser = Jinja2Parser()
    content = "{{ variable }}"
    path = Path("test.md")

    assert parser.detect(content, path) is False


def test_jinja2_parser_parsing_and_json_conversion():
    """Test Jinja2 parser parses template syntax and preserves in JSON."""
    parser = Jinja2Parser()
    content = """Hello {{ name }}!

{% if condition %}
Condition is true
{% endif %}
"""
    path = Path("test.jinja")

    parsed = parser.parse(content, path)
    assert isinstance(parsed, dict)

    json_content = parser.to_json(parsed)
    assert isinstance(json_content, dict)
    # Template syntax should be preserved - check for raw_content which contains the template
    assert "raw_content" in json_content
