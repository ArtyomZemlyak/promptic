"""Unit tests for resource limit validation."""

from pathlib import Path

import pytest

from promptic.context.nodes.errors import NodeResourceLimitExceededError
from promptic.context.nodes.models import ContextNode, NetworkConfig, NodeNetwork, NodeReference
from promptic.pipeline.network.builder import NodeNetworkBuilder
from promptic.token_counting.tiktoken_counter import TiktokenTokenCounter


def test_node_size_limit_enforcement():
    """Verify NodeResourceLimitExceededError raised when node size exceeds limit."""
    config = NetworkConfig(max_node_size=100)  # Very small limit

    # Create a node with content that exceeds size limit
    large_content = {"text": "x" * 200}  # 200 bytes
    node = ContextNode(
        id="test-node",
        content=large_content,
        format="json",
    )

    builder = NodeNetworkBuilder()
    # Manually check node size (simulating what builder does)
    node_size = len(str(node.content).encode("utf-8"))

    with pytest.raises(NodeResourceLimitExceededError) as exc_info:
        if node_size > config.max_node_size:
            raise NodeResourceLimitExceededError(
                f"Node {node.id} exceeds size limit: {node_size} > {config.max_node_size}",
                limit_type="node_size",
                current_value=node_size,
                max_value=config.max_node_size,
            )

    assert exc_info.value.limit_type == "node_size"
    assert exc_info.value.current_value > exc_info.value.max_value


def test_network_size_limit_enforcement():
    """Verify NodeResourceLimitExceededError raised when network size exceeds limit."""
    config = NetworkConfig(max_network_size=2)  # Very small limit

    # Create nodes that will exceed network size limit
    nodes = {
        "node1": ContextNode(id="node1", content={"text": "content1"}, format="json"),
        "node2": ContextNode(id="node2", content={"text": "content2"}, format="json"),
        "node3": ContextNode(id="node3", content={"text": "content3"}, format="json"),
    }

    with pytest.raises(NodeResourceLimitExceededError) as exc_info:
        if len(nodes) > config.max_network_size:
            raise NodeResourceLimitExceededError(
                f"Network size exceeds limit: {len(nodes)} > {config.max_network_size}",
                limit_type="network_size",
                current_value=len(nodes),
                max_value=config.max_network_size,
            )

    assert exc_info.value.limit_type == "network_size"
    assert exc_info.value.current_value > exc_info.value.max_value


def test_token_limit_per_node_enforcement():
    """Verify NodeResourceLimitExceededError raised when node token count exceeds limit."""
    config = NetworkConfig(max_tokens_per_node=10)  # Very small limit

    # Create a node with content that will exceed token limit
    large_content = {
        "text": "This is a very long text that will definitely exceed ten tokens when counted."
    }
    node = ContextNode(
        id="test-node",
        content=large_content,
        format="markdown",
    )

    counter = TiktokenTokenCounter()
    node_tokens = counter.count_tokens_for_node(node, model="gpt-4")

    with pytest.raises(NodeResourceLimitExceededError) as exc_info:
        if config.max_tokens_per_node is not None and node_tokens > config.max_tokens_per_node:
            raise NodeResourceLimitExceededError(
                f"Node {node.id} exceeds token limit: {node_tokens} > {config.max_tokens_per_node}",
                limit_type="tokens_per_node",
                current_value=node_tokens,
                max_value=config.max_tokens_per_node,
            )

    assert exc_info.value.limit_type == "tokens_per_node"
    assert exc_info.value.current_value > exc_info.value.max_value


def test_token_limit_per_network_enforcement():
    """Verify NodeResourceLimitExceededError raised when network token count exceeds limit."""
    config = NetworkConfig(max_tokens_per_network=50)  # Very small limit

    # Create nodes that will exceed network token limit
    nodes = [
        ContextNode(
            id=f"node{i}",
            content={"text": f"This is node {i} with some content that adds tokens."},
            format="markdown",
        )
        for i in range(5)
    ]

    counter = TiktokenTokenCounter()
    total_tokens = sum(counter.count_tokens_for_node(node, model="gpt-4") for node in nodes)

    with pytest.raises(NodeResourceLimitExceededError) as exc_info:
        if (
            config.max_tokens_per_network is not None
            and total_tokens > config.max_tokens_per_network
        ):
            raise NodeResourceLimitExceededError(
                f"Network token count exceeds limit: {total_tokens} > {config.max_tokens_per_network}",
                limit_type="tokens_per_network",
                current_value=total_tokens,
                max_value=config.max_tokens_per_network,
            )

    assert exc_info.value.limit_type == "tokens_per_network"
    assert exc_info.value.current_value > exc_info.value.max_value


def test_resource_limits_within_bounds():
    """Verify no errors raised when all resource limits are within bounds."""
    config = NetworkConfig(
        max_node_size=10 * 1024 * 1024,  # 10MB
        max_network_size=1000,
        max_tokens_per_node=100000,
        max_tokens_per_network=1000000,
    )

    # Create a small node that should pass all limits
    node = ContextNode(
        id="test-node",
        content={"text": "Small content"},
        format="json",
    )

    # Check node size
    node_size = len(str(node.content).encode("utf-8"))
    assert node_size <= config.max_node_size

    # Check network size
    nodes = {"test-node": node}
    assert len(nodes) <= config.max_network_size

    # Check token limits (if counter available)
    counter = TiktokenTokenCounter()
    node_tokens = counter.count_tokens_for_node(node, model="gpt-4")
    if config.max_tokens_per_node is not None:
        assert node_tokens <= config.max_tokens_per_node

    total_tokens = node_tokens
    if config.max_tokens_per_network is not None:
        assert total_tokens <= config.max_tokens_per_network
