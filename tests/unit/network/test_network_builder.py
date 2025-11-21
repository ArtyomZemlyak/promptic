"""Unit tests for network builder."""

from pathlib import Path

import pytest

from promptic.context.nodes.errors import NodeReferenceNotFoundError
from promptic.context.nodes.models import ContextNode, NetworkConfig, NodeReference


def test_missing_reference_handling():
    """Test that NodeReferenceNotFoundError is raised for missing references."""
    # This test will fail until reference validation is implemented
    # Create node with reference to non-existent node
    node_a = ContextNode(
        id="a",
        content={"name": "Node A"},
        format="yaml",
        references=[NodeReference(path="nonexistent.md", type="file")],
    )

    # Reference validation should raise NodeReferenceNotFoundError
    # TODO: Implement reference validation and update this test
    pass


def test_network_building_success():
    """Test successful network building with valid references."""
    # This test will fail until network building is implemented
    # Create nodes with valid references
    node_a = ContextNode(
        id="a",
        content={"name": "Node A"},
        format="yaml",
        references=[NodeReference(path="b", type="file")],
    )
    node_b = ContextNode(
        id="b",
        content={"name": "Node B"},
        format="yaml",
        references=[],
    )

    # Network building should succeed and create NodeNetwork
    # TODO: Implement network building and update this test
    pass


def test_semantic_type_optional_metadata():
    """Test that semantic_type is optional and metadata-only.

    Nodes should work without semantic labels, and semantic_type should
    not affect node structure or behavior.
    """
    # Create nodes without semantic_type (should work fine)
    node_without_semantic = ContextNode(
        id="node1",
        content={"name": "Node without semantic type"},
        format="yaml",
    )
    assert node_without_semantic.semantic_type is None

    # Create nodes with semantic_type (should also work)
    node_with_semantic = ContextNode(
        id="node2",
        content={"name": "Node with semantic type"},
        format="yaml",
        semantic_type="blueprint",
    )
    assert node_with_semantic.semantic_type == "blueprint"

    # Both nodes should have identical structure (except for semantic_type)
    assert node_without_semantic.id != node_with_semantic.id
    assert node_without_semantic.format == node_with_semantic.format
    assert node_without_semantic.content is not None
    assert node_with_semantic.content is not None

    # Semantic type should not affect node equality or structure
    # Both can be used identically in the network
    assert node_without_semantic.references == []
    assert node_with_semantic.references == []
    assert node_without_semantic.children == []
    assert node_with_semantic.children == []
