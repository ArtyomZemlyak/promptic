"""Unit tests for YAML parser."""

from pathlib import Path

import pytest

from promptic.context.nodes.errors import FormatParseError
from promptic.format_parsers.yaml_parser import YAMLParser


def test_yaml_parser_format_detection_yaml_extension():
    """Test YAML parser detects .yaml extension."""
    parser = YAMLParser()
    content = "key: value"
    path = Path("test.yaml")

    assert parser.detect(content, path) is True


def test_yaml_parser_format_detection_yml_extension():
    """Test YAML parser detects .yml extension."""
    parser = YAMLParser()
    content = "key: value"
    path = Path("test.yml")

    assert parser.detect(content, path) is True


def test_yaml_parser_format_detection_non_yaml_extension():
    """Test YAML parser rejects non-YAML extensions."""
    parser = YAMLParser()
    content = "key: value"
    path = Path("test.md")

    assert parser.detect(content, path) is False


def test_yaml_parser_parsing_and_json_conversion():
    """Test YAML parser parses content and converts to JSON correctly."""
    parser = YAMLParser()
    content = """
key: value
nested:
  item: test
list:
  - one
  - two
"""
    path = Path("test.yaml")

    parsed = parser.parse(content, path)
    assert isinstance(parsed, dict)
    assert parsed["key"] == "value"
    assert parsed["nested"]["item"] == "test"
    assert parsed["list"] == ["one", "two"]

    json_content = parser.to_json(parsed)
    assert isinstance(json_content, dict)
    assert json_content["key"] == "value"
    assert json_content["nested"]["item"] == "test"
    assert json_content["list"] == ["one", "two"]


def test_yaml_parser_invalid_yaml_raises_error():
    """Test YAML parser raises FormatParseError for invalid YAML."""
    parser = YAMLParser()
    content = "invalid: yaml: content: ["
    path = Path("test.yaml")

    with pytest.raises(FormatParseError):
        parser.parse(content, path)
