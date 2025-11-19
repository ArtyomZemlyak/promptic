from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from promptic.context.template_context import InstructionRenderContext

# Avoid circular import if possible, but we might need InstructionNode for type hinting
# if we put it in interface.
# Or use Any for now or TYPE_CHECKING.


class FormatRenderer(ABC):
    """Interface for format-specific renderer implementations."""

    @abstractmethod
    def render(self, content: str, context: InstructionRenderContext, **kwargs: Any) -> str:
        """
        Renders content with template context using format-specific syntax.

        Args:
            content: Raw content string
            context: Data/Memory/Step context
            kwargs: Additional context (e.g. instruction_node)
        """
        ...

    @abstractmethod
    def supports_format(self, format: str) -> bool:
        """Returns True if this renderer supports the given format."""
        ...
