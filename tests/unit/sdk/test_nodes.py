"""Unit tests for SDK nodes functions."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from promptic.context.nodes.models import ContextNode
from promptic.sdk.nodes import load_node, render_node


def test_load_node_yaml():
    """Test loading a YAML node."""
    with TemporaryDirectory() as tmpdir:
        yaml_file = Path(tmpdir) / "test.yaml"
        yaml_file.write_text("name: Test\nvalue: 42\n")

        node = load_node(yaml_file)

        assert isinstance(node, ContextNode)
        assert node.format == "yaml"
        assert node.id == str(yaml_file)
        assert node.content["name"] == "Test"
        assert node.content["value"] == 42


def test_load_node_markdown():
    """Test loading a Markdown node."""
    with TemporaryDirectory() as tmpdir:
        md_file = Path(tmpdir) / "test.md"
        md_file.write_text("# Heading\n\nThis is content.\n")

        node = load_node(md_file)

        assert isinstance(node, ContextNode)
        assert node.format == "markdown"
        assert node.id == str(md_file)
        assert isinstance(node.content, dict)


def test_load_node_json():
    """Test loading a JSON node."""
    with TemporaryDirectory() as tmpdir:
        json_file = Path(tmpdir) / "test.json"
        json_file.write_text('{"key": "value", "number": 123}\n')

        node = load_node(json_file)

        assert isinstance(node, ContextNode)
        assert node.format == "json"
        assert node.id == str(json_file)
        assert node.content["key"] == "value"
        assert node.content["number"] == 123


def test_load_node_jinja2():
    """Test loading a Jinja2 node."""
    with TemporaryDirectory() as tmpdir:
        jinja_file = Path(tmpdir) / "test.jinja"
        jinja_file.write_text("Hello {{ name }}!\n")

        node = load_node(jinja_file)

        assert isinstance(node, ContextNode)
        assert node.format == "jinja2"
        assert node.id == str(jinja_file)
        assert isinstance(node.content, dict)


def test_render_node_to_yaml():
    """Test rendering a node to YAML format."""
    node = ContextNode(
        id="test",
        content={"name": "Test", "value": 42},
        format="yaml",
    )

    rendered = render_node(node, "yaml")

    assert isinstance(rendered, str)
    assert "name: Test" in rendered
    assert "value: 42" in rendered


def test_render_node_to_markdown():
    """Test rendering a node to Markdown format."""
    node = ContextNode(
        id="test",
        content={"paragraphs": ["First paragraph", "Second paragraph"]},
        format="markdown",
    )

    rendered = render_node(node, "markdown")

    assert isinstance(rendered, str)
    assert "First paragraph" in rendered
    assert "Second paragraph" in rendered


def test_render_node_to_json():
    """Test rendering a node to JSON format."""
    node = ContextNode(
        id="test",
        content={"key": "value", "number": 123},
        format="json",
    )

    rendered = render_node(node, "json")

    assert isinstance(rendered, str)
    assert '"key": "value"' in rendered
    assert '"number": 123' in rendered


def test_render_node_to_jinja2():
    """Test rendering a node to Jinja2 format."""
    node = ContextNode(
        id="test",
        content={"raw_content": "Hello {{ name }}!"},
        format="jinja2",
    )

    rendered = render_node(node, "jinja2")

    assert isinstance(rendered, str)
    assert "Hello {{ name }}!" in rendered


def test_network_rendering_to_yaml():
    """Test network rendering to YAML format."""
    # This test will fail until network rendering is implemented
    from promptic.context.nodes.models import NodeNetwork

    # Create a simple network
    root_node = ContextNode(
        id="root",
        content={"name": "Root"},
        format="yaml",
    )
    network = NodeNetwork(root=root_node, nodes={"root": root_node})

    # Render network to YAML
    from promptic.sdk.nodes import render_node_network

    rendered = render_node_network(network, target_format="yaml")

    assert isinstance(rendered, str)
    assert len(rendered) > 0
    # TODO: Implement network rendering and update this test
    pass


def test_network_rendering_to_markdown():
    """Test network rendering to Markdown format."""
    # This test will fail until network rendering is implemented
    from promptic.context.nodes.models import NodeNetwork

    # Create a simple network
    root_node = ContextNode(
        id="root",
        content={"name": "Root"},
        format="yaml",
    )
    network = NodeNetwork(root=root_node, nodes={"root": root_node})

    # Render network to Markdown
    from promptic.sdk.nodes import render_node_network

    rendered = render_node_network(network, target_format="markdown")

    assert isinstance(rendered, str)
    assert len(rendered) > 0
    # TODO: Implement network rendering and update this test
    pass


def test_network_rendering_to_json():
    """Test network rendering to JSON format."""
    # This test will fail until network rendering is implemented
    from promptic.context.nodes.models import NodeNetwork

    # Create a simple network
    root_node = ContextNode(
        id="root",
        content={"name": "Root"},
        format="yaml",
    )
    network = NodeNetwork(root=root_node, nodes={"root": root_node})

    # Render network to JSON
    from promptic.sdk.nodes import render_node_network

    rendered = render_node_network(network, target_format="json")

    assert isinstance(rendered, str)
    assert len(rendered) > 0
    # TODO: Implement network rendering and update this test
    pass


def test_network_rendering_to_file_first():
    """Test network rendering to file-first format."""
    # This test will fail until network rendering is implemented
    from promptic.context.nodes.models import NodeNetwork

    # Create a simple network
    root_node = ContextNode(
        id="root",
        content={"name": "Root"},
        format="yaml",
    )
    network = NodeNetwork(root=root_node, nodes={"root": root_node})

    # Render network to file-first format
    from promptic.sdk.nodes import render_node_network

    rendered = render_node_network(network, target_format="yaml", render_mode="file_first")

    assert isinstance(rendered, str)
    assert len(rendered) > 0
    # TODO: Implement network rendering and update this test
    pass
