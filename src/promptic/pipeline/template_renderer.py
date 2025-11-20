from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, Optional

from promptic.blueprints.models import InstructionFallbackPolicy, InstructionNode
from promptic.context.errors import TemplateRenderError
from promptic.context.template_context import InstructionRenderContext
from promptic.pipeline.format_renderers.base import FormatRenderer

if TYPE_CHECKING:
    from promptic.blueprints.models import ContextBlueprint
    from promptic.pipeline.context_materializer import ContextMaterializer
    from promptic.pipeline.format_renderers.file_first import (
        FileFirstRenderer,
        FileFirstRenderResult,
    )

# We import implementations lazily or check availability to avoid circularity if necessary.
# But here we want to register them.


logger = logging.getLogger(__name__)


class TemplateRenderer:
    """
    Dispatcher that routes instruction rendering to format-specific renderers.
    """

    def __init__(self) -> None:
        self._renderers: Dict[str, FormatRenderer] = {}
        self._strategies: Dict[str, "FileFirstRenderer"] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Registers default format renderers."""
        # Markdown
        try:
            from promptic.pipeline.format_renderers.markdown import MarkdownFormatRenderer

            self.register_renderer("md", MarkdownFormatRenderer())
        except ImportError:
            pass  # Should allow running without it if not available (e.g. during dev)

        # Jinja2
        try:
            from promptic.pipeline.format_renderers.jinja2 import Jinja2FormatRenderer

            self.register_renderer("jinja", Jinja2FormatRenderer())
        except ImportError:
            pass

        # YAML
        try:
            from promptic.pipeline.format_renderers.yaml import YamlFormatRenderer

            renderer = YamlFormatRenderer()
            self.register_renderer("yaml", renderer)
            self.register_renderer("yml", renderer)
        except ImportError:
            pass

        self._register_file_first_strategy()

    def register_renderer(self, format: str, renderer: FormatRenderer) -> None:
        """Registers a renderer for a specific format."""
        self._renderers[format] = renderer

    def render_file_first(
        self,
        *,
        blueprint: "ContextBlueprint",
        materializer: "ContextMaterializer",
        base_url: str | None = None,
        depth_limit: int = 3,
        summary_overrides: Optional[Dict[str, str]] = None,
    ) -> "FileFirstRenderResult":
        """Render persona/goals markdown plus metadata via the file-first strategy."""

        strategy = self._strategies.get("file_first")
        if not strategy:
            raise TemplateRenderError(
                instruction_id="__file_first__",
                format="file_first",
                error_type="render_error",
                message="File-first renderer is not available in this runtime.",
            )
        return strategy.render(
            blueprint=blueprint,
            materializer=materializer,
            base_url=base_url,
            depth_limit=depth_limit,
            summary_overrides=summary_overrides or {},
        )

    def _register_file_first_strategy(self) -> None:
        try:
            from promptic.pipeline.format_renderers.file_first import FileFirstRenderer
        except ImportError:
            return

        self._strategies["file_first"] = FileFirstRenderer()

    def render(
        self,
        instruction_node: InstructionNode,
        content: str,
        context: InstructionRenderContext,
    ) -> str:
        """
        Renders instruction content using the appropriate format renderer.

        Args:
            instruction_node: The instruction metadata containing format info
            content: The raw instruction content to render
            context: The template context containing data/memory/step info

        Returns:
            Rendered instruction content

        Raises:
            TemplateRenderError: If rendering fails or format is unsupported
        """
        format_key = instruction_node.format
        renderer = self._renderers.get(format_key)

        # Try to find a renderer that explicitly supports this format
        if not renderer:
            # Check all renderers if they claim support (fallback)
            for r in self._renderers.values():
                if r.supports_format(format_key):
                    renderer = r
                    break

        if not renderer:
            # If no renderer found, return content as-is for txt, or raise error?
            # For now, if it's 'txt', maybe we just return it.
            # But spec says "routes to format-specific renderers".
            # If 'txt' format is used, we might want a TxtRenderer or just pass through.
            # Assuming if no renderer registered, we can't render.
            # However, for MVP/Setup, we might not have any renderers registered yet.
            # But we should probably raise an error if we expect to handle it.
            # Or maybe just return content if format is 'txt' and no renderer?
            if format_key == "txt":
                return content

            raise TemplateRenderError(
                instruction_id=instruction_node.instruction_id,
                format=format_key,
                error_type="syntax_error",
                message=f"No renderer registered for format '{format_key}'",
                context={"available_formats": list(self._renderers.keys())},
            )

        try:
            return renderer.render(content, context, instruction_node=instruction_node)
        except TemplateRenderError as error:
            return self._handle_render_error(instruction_node, error)
        except Exception as exc:
            wrapped = TemplateRenderError(
                instruction_id=instruction_node.instruction_id,
                format=format_key,
                error_type="render_error",
                message=f"Unexpected error during rendering: {exc}",
                context={"original_error": str(exc)},
            )
            return self._handle_render_error(instruction_node, wrapped)

    def _handle_render_error(
        self, instruction_node: InstructionNode, error: TemplateRenderError
    ) -> str:
        policy = instruction_node.fallback_policy or InstructionFallbackPolicy.ERROR

        if policy == InstructionFallbackPolicy.ERROR:
            raise error

        placeholder = instruction_node.placeholder_template or _DEFAULT_PLACEHOLDER
        try:
            rendered_placeholder = placeholder.format(
                instruction_id=instruction_node.instruction_id
            )
        except Exception:
            rendered_placeholder = placeholder

        # AICODE-NOTE: Degrading per-instruction fallback policies keeps template rendering
        #              aligned with instruction loading semantics without duplicating logic.
        logger.warning(
            "Template rendering failed for instruction_id=%s policy=%s error=%s",
            instruction_node.instruction_id,
            policy.value,
            error,
        )

        if policy == InstructionFallbackPolicy.NOOP:
            return ""

        return rendered_placeholder


_DEFAULT_PLACEHOLDER = "[instruction {instruction_id} unavailable]"
