from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Sequence

from jinja2 import Environment, StrictUndefined, TemplateSyntaxError, UndefinedError

from promptic.context.errors import TemplateRenderError
from promptic.context.template_context import InstructionRenderContext
from promptic.pipeline.format_renderers.base import FormatRenderer

logger = logging.getLogger(__name__)


class Jinja2FormatRenderer(FormatRenderer):
    """
    Renders content using Jinja2 templating engine.
    """

    def __init__(self) -> None:
        self._env: Optional[Environment] = None

    @property
    def env(self) -> Environment:
        """Lazy initialization of Jinja2 environment."""
        if self._env is None:
            # AICODE-NOTE: Separate environment for instructions keeps instruction-only
            #              filters/globals from leaking into the broader prompt renderer.
            self._env = Environment(
                autoescape=False,
                undefined=StrictUndefined,
                keep_trailing_newline=True,
            )
            self._register_extensions(self._env)
        return self._env

    def _register_extensions(self, env: Environment) -> None:
        """Register instruction-specific filters and globals."""

        def format_step(step: Any) -> str:
            if step is None:
                return ""
            step_id = getattr(step, "step_id", None) or getattr(step, "id", None)
            title = getattr(step, "title", None) or ""
            if step_id and title:
                return f"[{step_id}] {title}"
            if step_id:
                return f"[{step_id}]"
            return str(step)

        def get_parent_step(step: Any) -> str | None:
            hierarchy = getattr(step, "hierarchy", None)
            if not hierarchy:
                return None
            if isinstance(hierarchy, Sequence):
                try:
                    parent = hierarchy[-1]
                except IndexError:
                    return None
                return str(parent)
            return None

        env.filters["format_step"] = format_step
        env.globals["format_step"] = format_step
        env.globals["get_parent_step"] = get_parent_step

    def render(self, content: str, context: InstructionRenderContext, **kwargs: Any) -> str:
        variables = context.get_template_variables()

        instruction = kwargs.get("instruction_node")
        instruction_id = getattr(instruction, "instruction_id", "<unknown>")

        try:
            template = self.env.from_string(content)
            rendered = template.render(**variables)
            return str(rendered)
        except UndefinedError as e:
            raise TemplateRenderError(
                instruction_id=instruction_id,
                format="jinja",
                error_type="missing_placeholder",
                message=f"Missing variable in template: {e}",
                context={"original_error": str(e)},
            ) from e
        except TemplateSyntaxError as e:
            raise TemplateRenderError(
                instruction_id=instruction_id,
                format="jinja",
                error_type="syntax_error",
                message=f"Jinja2 syntax error: {e.message}",
                line_number=e.lineno,
                context={"filename": e.filename, "lineno": e.lineno},
            ) from e
        except Exception as e:
            raise TemplateRenderError(
                instruction_id=instruction_id,
                format="jinja",
                error_type="render_error",
                message=f"Jinja2 rendering failed: {e}",
                context={"original_error": str(e)},
            ) from e

    def supports_format(self, format: str) -> bool:
        return format.lower() in ("jinja", "jinja2", "j2")
