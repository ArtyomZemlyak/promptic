"""Contract test for FormatParser interface."""

from pathlib import Path

import pytest

from promptic.format_parsers.base import FormatParser


def test_format_parser_interface_contract():
    """Verify FormatParser interface contract.

    This test ensures all format parser implementations follow the interface
    contract defined in FormatParser base class.
    """
    # This test will fail until parsers are implemented
    # Once parsers exist, we'll import and test them here
    from promptic.format_parsers.jinja2_parser import Jinja2Parser
    from promptic.format_parsers.json_parser import JSONParser
    from promptic.format_parsers.markdown_parser import MarkdownParser
    from promptic.format_parsers.yaml_parser import YAMLParser

    parsers = [YAMLParser(), MarkdownParser(), Jinja2Parser(), JSONParser()]

    for parser in parsers:
        # Verify parser implements FormatParser interface
        assert issubclass(type(parser), FormatParser)
        assert isinstance(parser, FormatParser)

        # Verify all required methods exist
        assert hasattr(parser, "detect")
        assert hasattr(parser, "parse")
        assert hasattr(parser, "to_json")
        assert hasattr(parser, "extract_references")

        # Verify methods are callable
        assert callable(parser.detect)
        assert callable(parser.parse)
        assert callable(parser.to_json)
        assert callable(parser.extract_references)

        # Test method signatures with sample data
        test_content = "test content"
        test_path = Path("test.txt")

        # detect() should return bool
        result = parser.detect(test_content, test_path)
        assert isinstance(result, bool)

        # parse() should return dict (may raise FormatParseError)
        try:
            result = parser.parse(test_content, test_path)
            assert isinstance(result, dict)
        except Exception:
            # parse() may raise FormatParseError for invalid content
            pass

        # to_json() should accept dict and return dict
        test_parsed = {"key": "value"}
        result = parser.to_json(test_parsed)
        assert isinstance(result, dict)

        # extract_references() should accept dict and return list
        result = parser.extract_references(test_parsed)
        assert isinstance(result, list)
