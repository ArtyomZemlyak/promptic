"""Unit tests for JSON parser."""

from pathlib import Path

import pytest

from promptic.context.nodes.errors import FormatParseError
from promptic.format_parsers.json_parser import JSONParser


def test_json_parser_format_detection_json_extension():
    """Test JSON parser detects .json extension."""
    parser = JSONParser()
    content = '{"key": "value"}'
    path = Path("test.json")

    assert parser.detect(content, path) is True


def test_json_parser_format_detection_non_json_extension():
    """Test JSON parser rejects non-JSON extensions."""
    parser = JSONParser()
    content = '{"key": "value"}'
    path = Path("test.yaml")

    assert parser.detect(content, path) is False


def test_json_parser_parsing_and_validation():
    """Test JSON parser parses and validates JSON correctly."""
    parser = JSONParser()
    content = '{"key": "value", "nested": {"item": "test"}, "list": [1, 2, 3]}'
    path = Path("test.json")

    parsed = parser.parse(content, path)
    assert isinstance(parsed, dict)
    assert parsed["key"] == "value"
    assert parsed["nested"]["item"] == "test"
    assert parsed["list"] == [1, 2, 3]

    json_content = parser.to_json(parsed)
    assert isinstance(json_content, dict)
    assert json_content["key"] == "value"


def test_json_parser_invalid_json_raises_error():
    """Test JSON parser raises FormatParseError for invalid JSON."""
    parser = JSONParser()
    content = '{"key": "value"'
    path = Path("test.json")

    with pytest.raises(FormatParseError):
        parser.parse(content, path)
