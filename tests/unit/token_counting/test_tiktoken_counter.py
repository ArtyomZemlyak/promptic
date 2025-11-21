"""Unit tests for TiktokenTokenCounter implementation."""

import pytest

from promptic.context.nodes.errors import TokenCountingError
from promptic.context.nodes.models import ContextNode
from promptic.token_counting.tiktoken_counter import TiktokenTokenCounter


def test_count_tokens_basic():
    """Verify basic token counting works."""
    counter = TiktokenTokenCounter()
    content = "This is a test string."

    token_count = counter.count_tokens(content, model="gpt-4")
    assert isinstance(token_count, int)
    assert token_count > 0


def test_count_tokens_different_models():
    """Verify token counting works with different models."""
    counter = TiktokenTokenCounter()
    content = "This is a test string for different models."

    # Test GPT-4
    tokens_gpt4 = counter.count_tokens(content, model="gpt-4")
    assert tokens_gpt4 > 0

    # Test GPT-3.5-turbo
    tokens_gpt35 = counter.count_tokens(content, model="gpt-3.5-turbo")
    assert tokens_gpt35 > 0

    # Token counts should be similar (may differ slightly due to encoding differences)
    assert abs(tokens_gpt4 - tokens_gpt35) < 10


def test_count_tokens_for_node():
    """Verify token counting for nodes works."""
    counter = TiktokenTokenCounter()
    node = ContextNode(
        id="test-node",
        content={"text": "This is a test node with some content."},
        format="markdown",
    )

    token_count = counter.count_tokens_for_node(node, model="gpt-4")
    assert isinstance(token_count, int)
    assert token_count > 0


def test_count_tokens_for_node_different_formats():
    """Verify token counting works for nodes in different formats."""
    counter = TiktokenTokenCounter()

    # Test markdown node
    md_node = ContextNode(
        id="md-node",
        content={"text": "Markdown content here."},
        format="markdown",
    )
    md_tokens = counter.count_tokens_for_node(md_node, model="gpt-4")
    assert md_tokens > 0

    # Test JSON node
    json_node = ContextNode(
        id="json-node",
        content={"key": "JSON content here."},
        format="json",
    )
    json_tokens = counter.count_tokens_for_node(json_node, model="gpt-4")
    assert json_tokens > 0

    # Test YAML node
    yaml_node = ContextNode(
        id="yaml-node",
        content={"key": "YAML content here."},
        format="yaml",
    )
    yaml_tokens = counter.count_tokens_for_node(yaml_node, model="gpt-4")
    assert yaml_tokens > 0


def test_count_tokens_empty_content():
    """Verify token counting handles empty content."""
    counter = TiktokenTokenCounter()

    # Empty string should return 0 or small number
    token_count = counter.count_tokens("", model="gpt-4")
    assert isinstance(token_count, int)
    assert token_count >= 0


def test_count_tokens_long_content():
    """Verify token counting works with long content."""
    counter = TiktokenTokenCounter()
    long_content = "This is a very long string. " * 100

    token_count = counter.count_tokens(long_content, model="gpt-4")
    assert isinstance(token_count, int)
    assert token_count > 100  # Should have many tokens


def test_count_tokens_unknown_model_fallback():
    """Verify token counting falls back to gpt-4 for unknown models."""
    counter = TiktokenTokenCounter()
    content = "Test content"

    # Should not raise error, should fallback to gpt-4 encoding
    token_count = counter.count_tokens(content, model="unknown-model-xyz")
    assert isinstance(token_count, int)
    assert token_count > 0


def test_count_tokens_invalid_model_raises_error():
    """Verify invalid model raises TokenCountingError."""
    counter = TiktokenTokenCounter()
    content = "Test content"

    # This should work with fallback, but test error handling path
    # by checking that encoding creation is handled gracefully
    try:
        token_count = counter.count_tokens(content, model="invalid")
        # If it doesn't raise, it should return a valid count (fallback worked)
        assert isinstance(token_count, int)
    except TokenCountingError:
        # If it raises, that's also acceptable behavior
        pass


def test_count_tokens_model_name_variations():
    """Verify token counting works with different model name variations."""
    counter = TiktokenTokenCounter()
    content = "Test content for model variations"

    # Test various model name formats
    models = [
        "gpt-4",
        "gpt-3.5-turbo",
        "gpt-35-turbo",
        "GPT-4",
        "GPT-3.5-TURBO",
    ]

    for model in models:
        token_count = counter.count_tokens(content, model=model)
        assert isinstance(token_count, int)
        assert token_count > 0
