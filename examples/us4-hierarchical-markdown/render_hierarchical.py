from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from promptic.context.template_context import InstructionRenderContext, StepContext
from promptic.pipeline.template_renderer import TemplateRenderer


def _load_instruction() -> str:
    instruction_path = pathlib.Path(__file__).with_name("instruction.md")
    return instruction_path.read_text(encoding="utf-8")


def render_example(show_details: bool) -> str:
    renderer = TemplateRenderer()
    content = _load_instruction()
    context = InstructionRenderContext(
        data={
            "show_details": show_details,
            "risks": "schedule drift",
            "next_steps": "expand pilot",
        },
        memory={"owner": "ops-team"},
        step=StepContext(step_id="summary", title="Summary", kind="sequence"),
    )
    # TemplateRenderer requires an InstructionNode, but for demo purposes we can
    # simulate a minimal node using the Markdown format.
    from promptic.blueprints.models import InstructionNode

    node = InstructionNode(
        instruction_id="us4-example",
        source_uri="file://instruction.md",
        format="md",
        checksum="0" * 32,
    )
    return renderer.render(node, content, context)


if __name__ == "__main__":
    print("=== Rendering with details ===")
    print(render_example(show_details=True))
    print("\n=== Rendering without details ===")
    print(render_example(show_details=False))
