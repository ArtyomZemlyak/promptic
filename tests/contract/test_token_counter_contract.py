"""Contract test for TokenCounter interface."""

import pytest

from promptic.token_counting.base import TokenCounter


def test_token_counter_interface_contract():
    """Verify TokenCounter interface contract.

    This test ensures all token counter implementations follow the interface
    contract defined in TokenCounter base class.
    """
    from promptic.token_counting.tiktoken_counter import TiktokenTokenCounter

    counter = TiktokenTokenCounter()

    # Verify counter implements TokenCounter interface
    assert issubclass(type(counter), TokenCounter)
    assert isinstance(counter, TokenCounter)

    # Verify all required methods exist
    assert hasattr(counter, "count_tokens")
    assert hasattr(counter, "count_tokens_for_node")

    # Verify methods are callable
    assert callable(counter.count_tokens)
    assert callable(counter.count_tokens_for_node)

    # Test method signatures with sample data
    test_content = "This is a test string for token counting."

    # count_tokens() should return int
    result = counter.count_tokens(test_content, model="gpt-4")
    assert isinstance(result, int)
    assert result > 0

    # count_tokens_for_node() should return int
    from promptic.context.nodes.models import ContextNode

    test_node = ContextNode(
        id="test-node",
        content={"text": test_content},
        format="markdown",
    )
    result = counter.count_tokens_for_node(test_node, model="gpt-4")
    assert isinstance(result, int)
    assert result > 0
