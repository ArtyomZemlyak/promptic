from __future__ import annotations

import logging
import re
from typing import Any

try:
    import regex
except ImportError:
    import re as regex

from promptic.blueprints.adapters.legacy import node_to_instruction
from promptic.blueprints.models import InstructionNode
from promptic.context.errors import TemplateRenderError
from promptic.context.nodes.models import ContextNode
from promptic.context.template_context import InstructionRenderContext
from promptic.pipeline.format_renderers.base import FormatRenderer

logger = logging.getLogger(__name__)


class YamlFormatRenderer(FormatRenderer):
    """
    Renders YAML (or arbitrary text) content using custom regex pattern substitution.
    Defaults to `{{placeholder}}` style if no pattern provided.
    """

    def render(self, content: str, context: InstructionRenderContext, **kwargs: Any) -> str:
        node: InstructionNode | ContextNode | None = kwargs.get("instruction_node")

        # Convert ContextNode to InstructionNode for compatibility during migration
        if isinstance(node, ContextNode):
            node = node_to_instruction(node)

        if not node or not node.pattern:
            # Default pattern: {{ placeholder }}
            pattern = r"\{\{(?P<placeholder>[^}]+)\}\}"
        else:
            pattern = node.pattern

        variables = context.get_template_variables()
        instruction_id = node.instruction_id if node else "<unknown>"

        try:
            # Validate pattern has group 'placeholder'
            regex_pattern = regex.compile(pattern)
            if "placeholder" not in regex_pattern.groupindex:
                raise TemplateRenderError(
                    instruction_id=instruction_id,
                    format="yaml",
                    error_type="syntax_error",
                    message=f"Pattern '{pattern}' must contain a named group 'placeholder' (e.g. '(?P<placeholder>...)').",
                    context={"pattern": pattern},
                )
        except Exception as e:
            if isinstance(e, TemplateRenderError):
                raise
            raise TemplateRenderError(
                instruction_id=instruction_id,
                format="yaml",
                error_type="syntax_error",
                message=f"Invalid regex pattern '{pattern}': {str(e)}",
                context={"pattern": pattern},
            ) from e

        def replace_match(match: Any) -> str:
            placeholder = match.group("placeholder")
            try:
                value = self._resolve_value(placeholder.strip(), variables)
                return str(value)
            except Exception as e:
                raise TemplateRenderError(
                    instruction_id=instruction_id,
                    format="yaml",
                    error_type="missing_placeholder",
                    message=f"Failed to resolve placeholder '{placeholder}': {str(e)}",
                    placeholder=placeholder,
                )

        try:
            result = regex_pattern.sub(replace_match, content)
            return str(result)
        except TemplateRenderError:
            raise
        except Exception as e:
            raise TemplateRenderError(
                instruction_id=instruction_id,
                format="yaml",
                error_type="render_error",
                message=f"YAML rendering failed: {str(e)}",
                context={"pattern": pattern},
            ) from e

    def supports_format(self, format: str) -> bool:
        return format.lower() in ("yaml", "yml")

    def _resolve_value(self, field_name: str, variables: dict[str, Any]) -> Any:
        """
        Resolves a dot-notation field name against the variables dictionary.
        Supports nested access via dot notation for both attributes and dictionary keys.
        """
        if not field_name:
            raise ValueError("Empty placeholder name not allowed")

        parts = field_name.split(".")
        obj = variables

        for i, part in enumerate(parts):
            # Try dict access first
            if isinstance(obj, dict):
                if part in obj:
                    obj = obj[part]
                    continue

            # Try attribute access
            try:
                obj = getattr(obj, part)
                continue
            except AttributeError:
                pass

            # Check if it's a dict but key is missing
            if isinstance(obj, dict):
                path = ".".join(parts[: i + 1])
                raise KeyError(f"Key '{part}' not found in '{path}'")

            path = ".".join(parts[: i + 1])
            raise AttributeError(f"Attribute '{part}' not found in '{path}'")

        return obj
