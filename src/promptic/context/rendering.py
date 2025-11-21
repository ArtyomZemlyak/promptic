from __future__ import annotations

import io
import json
import re
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from jinja2 import DebugUndefined, Environment, StrictUndefined, TemplateError
from rich.box import DOUBLE_EDGE, ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from promptic.blueprints.adapters.legacy import network_to_blueprint
from promptic.blueprints.models import BlueprintStep, ContextBlueprint
from promptic.context.nodes.models import NodeNetwork

_PLACEHOLDER_PATTERN = re.compile(r"(\{\{[^{}]+\}\})")


@dataclass
class RenderResult:
    text: str
    warnings: list[str] = field(default_factory=list)


def render_context_preview(
    *,
    blueprint: ContextBlueprint | NodeNetwork,
    template_context: Mapping[str, Any],
    global_instructions: Sequence[str],
    step_instructions: Mapping[str, Sequence[str]],
    data_preview: Mapping[str, Any],
    memory_preview: Mapping[str, Any],
    print_to_console: bool = True,
) -> RenderResult:
    """Render a human-friendly preview leveraging rich formatting.

    Args:
        blueprint: ContextBlueprint or NodeNetwork (converted during migration)
        template_context: Template variables for rendering
        global_instructions: Global instruction texts
        step_instructions: Step instruction texts by step_id
        data_preview: Data preview values
        memory_preview: Memory preview values
        print_to_console: If True (default), output formatted preview to console.
                          If False, only return plain text without console output.
    """
    # Convert NodeNetwork to ContextBlueprint for compatibility during migration
    if not isinstance(blueprint, ContextBlueprint):
        blueprint = network_to_blueprint(blueprint)

    prompt_text, prompt_warnings = _render_prompt(blueprint, template_context)
    # AICODE-NOTE: If print_to_console=True, output directly to console to preserve Rich formatting
    # If False, use StringIO buffer to suppress console output
    # Always record to buffer for text export (plain text without formatting)
    if print_to_console:
        console = Console(record=True, width=100)
    else:
        output_buffer = io.StringIO()
        console = Console(file=output_buffer, record=True, width=100)

    # Blueprint header with enhanced styling
    console.print()
    console.print(
        Panel(
            Text(f"{blueprint.name}", style="bold bright_cyan"),
            title=f"[bold bright_blue]Blueprint[/bold bright_blue] · [dim]{blueprint.id}[/dim]",
            border_style="bright_blue",
            box=DOUBLE_EDGE,
            padding=(1, 2),
        )
    )

    # Prompt section with enhanced styling
    console.print()
    console.print(
        Panel(
            _highlight_placeholders(prompt_text),
            title="[bold bright_yellow]📝 Prompt[/bold bright_yellow]",
            border_style="bright_yellow",
            box=ROUNDED,
            padding=(1, 2),
        )
    )

    # Global Instructions with enhanced styling
    if global_instructions:
        console.print()
        console.print(
            Panel(
                Text("\n".join(global_instructions), style="default"),
                title="[bold bright_magenta]🌐 Global Instructions[/bold bright_magenta]",
                border_style="bright_magenta",
                box=ROUNDED,
                padding=(1, 2),
            )
        )

    # Steps table with enhanced styling
    console.print()
    table = Table(
        title="[bold bright_green]📋 Steps[/bold bright_green]",
        show_lines=True,
        border_style="bright_green",
        box=ROUNDED,
        header_style="bold bright_green",
        row_styles=["default", "dim"],
    )
    table.add_column("Step", style="cyan", no_wrap=False)
    table.add_column("Kind", style="yellow", justify="center", width=12)
    table.add_column("Instructions", style="default", no_wrap=False)
    for step in _iter_steps(blueprint.steps):
        instructions = (
            "\n".join(step_instructions.get(step.step_id, []))
            or "[dim italic]no instructions[/dim italic]"
        )
        # Style step kind based on type
        kind_style = _get_step_kind_style(step.kind)
        table.add_row(
            f"[bold cyan]{step.step_id}[/bold cyan]: {step.title}",
            f"[{kind_style}]{step.kind}[/{kind_style}]",
            instructions,
        )
    console.print(table)

    # Sample Data with enhanced styling
    console.print()
    console.print(
        Panel(
            Syntax(
                json.dumps(data_preview, indent=2, sort_keys=True),
                "json",
                theme="monokai",
                line_numbers=False,
            ),
            title="[bold bright_blue]💾 Sample Data[/bold bright_blue]",
            border_style="bright_blue",
            box=ROUNDED,
            padding=(1, 2),
        )
    )

    # Sample Memory with enhanced styling
    console.print()
    console.print(
        Panel(
            Syntax(
                json.dumps(memory_preview, indent=2, sort_keys=True),
                "json",
                theme="monokai",
                line_numbers=False,
            ),
            title="[bold bright_cyan]🧠 Sample Memory[/bold bright_cyan]",
            border_style="bright_cyan",
            box=ROUNDED,
            padding=(1, 2),
        )
    )
    console.print()

    warnings = list(prompt_warnings)
    # AICODE-NOTE: export_text() returns plain text without ANSI codes
    # If print_to_console=True, formatted output is already printed to console above
    # Always return plain text for programmatic use (e.g., logging, testing)
    return RenderResult(text=console.export_text(clear=False), warnings=warnings)


def _render_prompt(
    blueprint: ContextBlueprint | NodeNetwork, context: Mapping[str, Any]
) -> tuple[str, list[str]]:
    # Convert NodeNetwork to ContextBlueprint for compatibility during migration
    if not isinstance(blueprint, ContextBlueprint):
        blueprint = network_to_blueprint(blueprint)
    env = Environment(autoescape=False, undefined=StrictUndefined)
    warnings: list[str] = []
    try:
        prompt = env.from_string(blueprint.prompt_template).render(**context)
        return prompt, warnings
    except TemplateError as exc:
        warnings.append(str(exc))
        fallback_env = Environment(autoescape=False, undefined=DebugUndefined)
        prompt = fallback_env.from_string(blueprint.prompt_template).render(**context)
        return prompt, warnings


def _highlight_placeholders(text: str) -> Text:
    """Highlight template placeholders with enhanced styling."""
    rich_text = Text()
    start = 0
    for match in _PLACEHOLDER_PATTERN.finditer(text):
        rich_text.append(text[start : match.start()])
        # Enhanced placeholder styling with background
        rich_text.append(match.group(1), style="bold bright_red on dark_red")
        start = match.end()
    rich_text.append(text[start:])
    return rich_text


def _get_step_kind_style(kind: str) -> str:
    """Return appropriate style for step kind."""
    kind_lower = kind.lower()
    if kind_lower == "loop":
        return "bold bright_yellow"
    elif kind_lower == "sequence":
        return "bold bright_blue"
    elif kind_lower == "parallel":
        return "bold bright_green"
    elif kind_lower == "conditional":
        return "bold bright_magenta"
    else:
        return "bold white"


def _iter_steps(steps: Sequence[BlueprintStep]) -> Sequence[BlueprintStep]:
    ordered: list[BlueprintStep] = []

    def _walk(step_list: Sequence[BlueprintStep]) -> None:
        for step in step_list:
            ordered.append(step)
            if step.children:
                _walk(step.children)

    _walk(steps)
    return ordered


def render_context_for_llm(
    *,
    blueprint: ContextBlueprint | NodeNetwork,
    template_context: Mapping[str, Any],
    global_instructions: Sequence[str],
    step_instructions: Mapping[str, Sequence[str]],
) -> RenderResult:
    """Render plain text context ready for LLM input (no Rich formatting).

    # AICODE-NOTE: This function produces clean, plain text output suitable
    #              for direct LLM consumption, without any formatting artifacts.
    """
    # Convert NodeNetwork to ContextBlueprint for compatibility during migration
    if not isinstance(blueprint, ContextBlueprint):
        blueprint = network_to_blueprint(blueprint)

    parts: list[str] = []

    # Render prompt template
    prompt_text, prompt_warnings = _render_prompt(blueprint, template_context)
    parts.append(prompt_text)

    # Add global instructions
    if global_instructions:
        parts.append("\n\n## Global Instructions\n")
        parts.append("\n\n".join(global_instructions))

    # Add step instructions
    if step_instructions:
        parts.append("\n\n## Steps\n")
        for step in _iter_steps(blueprint.steps):
            step_insts = step_instructions.get(step.step_id, [])
            if step_insts:
                parts.append(f"\n### {step.step_id}: {step.title}\n")
                parts.append("\n\n".join(step_insts))

    text = "".join(parts).strip()
    return RenderResult(text=text, warnings=list(prompt_warnings))


__all__ = ["RenderResult", "render_context_preview", "render_context_for_llm"]
