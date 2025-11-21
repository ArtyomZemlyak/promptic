"""Integration tests for format parsing."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from promptic.format_parsers.registry import FormatParserRegistry
from promptic.sdk.nodes import load_node


def test_load_nodes_in_all_formats():
    """Test loading nodes in all four formats (YAML, Markdown, Jinja2, JSON)."""
    with TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create test files in all formats
        yaml_file = tmp_path / "blueprint.yaml"
        yaml_file.write_text("name: Test Blueprint\nsteps: []\n")

        markdown_file = tmp_path / "instruction.md"
        markdown_file.write_text("# Instruction\n\nThis is an instruction.\n")

        jinja2_file = tmp_path / "template.jinja"
        jinja2_file.write_text("Hello {{ name }}!\n")

        json_file = tmp_path / "data.json"
        json_file.write_text('{"key": "value", "data": "test"}\n')

        # Load all nodes
        yaml_node = load_node(yaml_file)
        markdown_node = load_node(markdown_file)
        jinja2_node = load_node(jinja2_file)
        json_node = load_node(json_file)

        # Verify all nodes loaded successfully
        assert yaml_node is not None
        assert yaml_node.format == "yaml"
        assert yaml_node.id == str(yaml_file)

        assert markdown_node is not None
        assert markdown_node.format == "markdown"
        assert markdown_node.id == str(markdown_file)

        assert jinja2_node is not None
        assert jinja2_node.format == "jinja2"
        assert jinja2_node.id == str(jinja2_file)

        assert json_node is not None
        assert json_node.format == "json"
        assert json_node.id == str(json_file)

        # Verify all formats convert to JSON
        assert isinstance(yaml_node.content, dict)
        assert isinstance(markdown_node.content, dict)
        assert isinstance(jinja2_node.content, dict)
        assert isinstance(json_node.content, dict)
