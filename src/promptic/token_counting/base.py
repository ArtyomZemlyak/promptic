"""Base interface for token counting."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from promptic.context.nodes.models import ContextNode


class TokenCounter(ABC):
    """Interface for token counting with model-specific implementations.

    # AICODE-NOTE: This interface enables pluggable token counting strategies
    with model-specific implementations. Token counting is performed on final
    rendered content to accurately reflect LLM context usage. The interface
    supports different models (GPT-4, GPT-3.5-turbo, etc.) through configurable
    model specification.
    """

    @abstractmethod
    def count_tokens(self, content: str, model: str) -> int:
        """Count tokens in content for a specific model.

        Args:
            content: Content string to count tokens for
            model: Model name (e.g., "gpt-4", "gpt-3.5-turbo")

        Returns:
            Number of tokens in content

        Raises:
            TokenCountingError: If token counting fails
        """
        pass

    @abstractmethod
    def count_tokens_for_node(self, node: "ContextNode", model: str) -> int:
        """Count tokens for a node's rendered content.

        Args:
            node: ContextNode to count tokens for
            model: Model name (e.g., "gpt-4", "gpt-3.5-turbo")

        Returns:
            Number of tokens in node's rendered content

        Raises:
            TokenCountingError: If token counting fails
        """
        pass
