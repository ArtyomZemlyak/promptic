from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from jinja2 import DebugUndefined, Environment, StrictUndefined, TemplateError
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from promptic.blueprints.models import BlueprintStep, ContextBlueprint

_PLACEHOLDER_PATTERN = re.compile(r"(\{\{[^{}]+\}\})")


@dataclass
class RenderResult:
    text: str
    warnings: list[str] = field(default_factory=list)


def render_context_preview(
    *,
    blueprint: ContextBlueprint,
    template_context: Mapping[str, Any],
    global_instructions: Sequence[str],
    step_instructions: Mapping[str, Sequence[str]],
    data_preview: Mapping[str, Any],
    memory_preview: Mapping[str, Any],
) -> RenderResult:
    """Render a human-friendly preview leveraging rich formatting."""

    prompt_text, prompt_warnings = _render_prompt(blueprint, template_context)
    console = Console(record=True, width=100)
    console.print(
        Panel(
            Text(f"{blueprint.name}", style="bold cyan"),
            title=f"Blueprint · {blueprint.id}",
        )
    )
    console.print(Panel(_highlight_placeholders(prompt_text), title="Prompt"))

    if global_instructions:
        console.print(
            Panel(
                Text("\n".join(global_instructions)),
                title="Global Instructions",
            )
        )

    table = Table(title="Steps", show_lines=True)
    table.add_column("Step")
    table.add_column("Kind")
    table.add_column("Instructions")
    for step in _iter_steps(blueprint.steps):
        instructions = "\n".join(step_instructions.get(step.step_id, [])) or "[no instructions]"
        table.add_row(f"{step.step_id}: {step.title}", step.kind, instructions)
    console.print(table)

    console.print(
        Panel(
            Syntax(json.dumps(data_preview, indent=2, sort_keys=True), "json"),
            title="Sample Data",
        )
    )
    console.print(
        Panel(
            Syntax(json.dumps(memory_preview, indent=2, sort_keys=True), "json"),
            title="Sample Memory",
        )
    )

    warnings = list(prompt_warnings)
    return RenderResult(text=console.export_text(clear=False), warnings=warnings)


def _render_prompt(
    blueprint: ContextBlueprint, context: Mapping[str, Any]
) -> tuple[str, list[str]]:
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
    rich_text = Text()
    start = 0
    for match in _PLACEHOLDER_PATTERN.finditer(text):
        rich_text.append(text[start : match.start()])
        rich_text.append(match.group(1), style="bold red")
        start = match.end()
    rich_text.append(text[start:])
    return rich_text


def _iter_steps(steps: Sequence[BlueprintStep]) -> Sequence[BlueprintStep]:
    ordered: list[BlueprintStep] = []

    def _walk(step_list: Sequence[BlueprintStep]) -> None:
        for step in step_list:
            ordered.append(step)
            if step.children:
                _walk(step.children)

    _walk(steps)
    return ordered


__all__ = ["RenderResult", "render_context_preview"]
