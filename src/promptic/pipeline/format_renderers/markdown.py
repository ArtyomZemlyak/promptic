from __future__ import annotations

import logging
from string import Formatter
from typing import Any, Dict

from promptic.context.errors import TemplateRenderError
from promptic.context.template_context import InstructionRenderContext
from promptic.pipeline.format_renderers.base import FormatRenderer
from promptic.pipeline.format_renderers.markdown_hierarchy import MarkdownHierarchyParser

logger = logging.getLogger(__name__)


class MarkdownFormatRenderer(FormatRenderer):
    """
    Renders Markdown content using Python string format syntax ({}) with context variables.
    """

    def __init__(self) -> None:
        self._hierarchy_parser = MarkdownHierarchyParser()

    def render(self, content: str, context: InstructionRenderContext, **kwargs: Any) -> str:
        # AICODE-NOTE: Markdown rendering uses Python's standard string.Formatter parsing
        # but implements custom field resolution to support dot notation for both
        # attributes and dictionary keys (e.g. data.user.name) without requiring keys to
        # be valid Python identifiers or attributes.

        instruction = kwargs.get("instruction_node")
        instruction_id = getattr(instruction, "instruction_id", "<unknown>")

        content = self._apply_conditionals(content, context, instruction_id)
        variables = context.get_template_variables()
        formatter = Formatter()
        output = []

        logger.debug(
            "Rendering Markdown content (length=%d) with context keys: %s",
            len(content),
            list(variables.keys()),
        )

        # Track position for error reporting
        # Note: simple line counting might be approximate if placeholders span lines,
        # but typically they don't.
        current_line = 1

        try:
            # Formatter.parse yields (literal_text, field_name, format_spec, conversion)
            iterable = formatter.parse(content)
        except ValueError as e:
            # Error parsing the format string itself (e.g. single '}')
            raise TemplateRenderError(
                instruction_id=instruction_id,
                format="md",
                error_type="syntax_error",
                message=f"Invalid format syntax: {str(e)}",
                line_number=1,
            ) from e

        for literal_text, field_name, format_spec, conversion in iterable:
            if literal_text:
                output.append(literal_text)
                current_line += literal_text.count("\n")

            if field_name is not None:
                try:
                    value = self._resolve_value(field_name, variables)

                    # Apply conversion
                    obj = value
                    if conversion:
                        obj = formatter.convert_field(obj, conversion)

                    # Apply format spec
                    # format_spec can be None if not specified
                    spec = format_spec or ""
                    formatted = formatter.format_field(obj, spec)
                    output.append(formatted)

                    # Update line count based on formatted output (though strictly
                    # we track source lines, but placeholder is usually on one line.
                    # Actually we should count newlines in the placeholder source?
                    # formatter.parse doesn't give source length of field.
                    # But we know literal_text precedes it.
                    # We assume placeholder is on the current line (or starts there).

                except Exception as e:
                    raise TemplateRenderError(
                        instruction_id=instruction_id,
                        format="md",
                        error_type=(
                            "missing_placeholder"
                            if isinstance(e, (KeyError, AttributeError))
                            else "render_error"
                        ),
                        message=f"Failed to render placeholder '{field_name}': {str(e)}",
                        line_number=current_line,
                        placeholder=field_name,
                    ) from e

        return "".join(output)

    def supports_format(self, format: str) -> bool:
        return format.lower() in ("md", "markdown")

    def _resolve_value(self, field_name: str, variables: Dict[str, Any]) -> Any:
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
                # Reconstruct path for error message
                path = ".".join(parts[: i + 1])
                raise KeyError(f"Key '{part}' not found in '{path}'")

            # Neither dict key nor attribute
            path = ".".join(parts[: i + 1])
            raise AttributeError(f"Attribute '{part}' not found in '{path}'")

        return obj

    def _apply_conditionals(
        self,
        content: str,
        context: InstructionRenderContext,
        instruction_id: str,
    ) -> str:
        metadata = self._hierarchy_parser.parse(content)
        if not metadata.conditionals:
            return content

        variables = context.get_template_variables()
        updated_content = content

        # AICODE-NOTE: Applying conditionals prior to placeholder expansion keeps
        #              hierarchy-driven sections consistent across renderer types.
        for conditional in sorted(
            metadata.conditionals, key=lambda item: item.start_index, reverse=True
        ):
            if not self._evaluate_condition(conditional.condition, variables, instruction_id):
                updated_content = (
                    updated_content[: conditional.start_index]
                    + updated_content[conditional.end_index :]
                )
        return updated_content

    def _evaluate_condition(
        self,
        expression: str,
        variables: Dict[str, Any],
        instruction_id: str,
    ) -> bool:
        try:
            value = self._resolve_value(expression, variables)
        except Exception as exc:
            raise TemplateRenderError(
                instruction_id=instruction_id,
                format="md",
                error_type="missing_placeholder",
                message=f"Conditional expression '{expression}' could not be resolved: {exc}",
                placeholder=expression,
            ) from exc
        return bool(value)
