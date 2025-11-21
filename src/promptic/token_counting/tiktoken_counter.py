"""Tiktoken-based token counter implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, cast

import tiktoken

from promptic.context.nodes.errors import TokenCountingError
from promptic.token_counting.base import TokenCounter

if TYPE_CHECKING:
    from promptic.context.nodes.models import ContextNode


class TiktokenTokenCounter(TokenCounter):
    """Tiktoken-based token counter with configurable model specification.

    # AICODE-NOTE: Token counting strategy - counting on final rendered content:
    Token counting is performed on the final rendered content (after all format
    conversions) to accurately reflect LLM context usage. This ensures that the
    token count matches what will actually be sent to the LLM, accounting for
    any format-specific rendering transformations. The counter uses tiktoken
    library which provides accurate, model-specific token counting for OpenAI
    models (GPT-4, GPT-3.5-turbo, etc.). Model specification is configurable per
    counting operation to support different LLM models and use cases.
    """

    def __init__(self) -> None:
        """Initialize tiktoken token counter."""
        self._encodings: dict[str, tiktoken.Encoding] = {}

    def _get_encoding(self, model: str) -> tiktoken.Encoding:
        """Get or create encoding for model.

        Args:
            model: Model name (e.g., "gpt-4", "gpt-3.5-turbo")

        Returns:
            Tiktoken encoding for model

        Raises:
            TokenCountingError: If encoding cannot be created for model
        """
        if model not in self._encodings:
            try:
                # Map model names to tiktoken encoding names
                encoding_name = self._map_model_to_encoding(model)
                self._encodings[model] = tiktoken.encoding_for_model(encoding_name)
            except Exception as e:
                raise TokenCountingError(
                    f"Failed to create encoding for model '{model}': {e}"
                ) from e

        return self._encodings[model]

    def _map_model_to_encoding(self, model: str) -> str:
        """Map model name to tiktoken encoding name.

        Args:
            model: Model name (e.g., "gpt-4", "gpt-3.5-turbo")

        Returns:
            Tiktoken encoding name

        Raises:
            TokenCountingError: If model is not supported
        """
        # Map common model names to tiktoken encoding names
        model_lower = model.lower()
        if "gpt-4" in model_lower or "gpt4" in model_lower:
            return "gpt-4"
        elif "gpt-3.5" in model_lower or "gpt-35" in model_lower or "gpt3.5" in model_lower:
            return "gpt-3.5-turbo"
        elif "gpt-3" in model_lower or "gpt3" in model_lower:
            return "gpt-3.5-turbo"  # GPT-3 uses same encoding as GPT-3.5
        else:
            # Try to use model name directly (tiktoken may support it)
            try:
                tiktoken.encoding_for_model(model)
                return model
            except Exception:
                # Fallback to gpt-4 encoding for unknown models
                return "gpt-4"

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
        try:
            encoding = self._get_encoding(model)
            tokens = encoding.encode(content)
            return len(tokens)
        except TokenCountingError:
            raise
        except Exception as e:
            raise TokenCountingError(f"Failed to count tokens: {e}") from e

    def count_tokens_for_node(self, node: "ContextNode", model: str) -> int:
        """Count tokens for a node's rendered content.

        # AICODE-NOTE: Token counting on final rendered content:
        This method renders the node to a string format (using the node's
        original format) and then counts tokens on the rendered content. This
        ensures accurate token counting that reflects what will actually be
        sent to the LLM, accounting for any format-specific rendering
        transformations.

        Args:
            node: ContextNode to count tokens for
            model: Model name (e.g., "gpt-4", "gpt-3.5-turbo")

        Returns:
            Number of tokens in node's rendered content

        Raises:
            TokenCountingError: If token counting fails
        """
        try:
            # Render node to string format for token counting
            from promptic.sdk.nodes import render_node

            # Convert format to supported format for render_node
            # jinja2 is similar to markdown, so convert it to markdown for rendering
            target_format: Literal["yaml", "markdown", "json"]
            if node.format == "jinja2":
                target_format = "markdown"
            elif node.format == "yaml":
                target_format = "yaml"
            elif node.format == "markdown":
                target_format = "markdown"
            elif node.format == "json":
                target_format = "json"
            else:
                # Fallback to markdown for unknown formats
                target_format = "markdown"
            rendered_content = render_node(node, target_format)
            return self.count_tokens(rendered_content, model)
        except TokenCountingError:
            raise
        except Exception as e:
            raise TokenCountingError(f"Failed to count tokens for node: {e}") from e
