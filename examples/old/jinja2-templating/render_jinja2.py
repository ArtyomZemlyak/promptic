import logging
import sys
from pathlib import Path

# Ensure we can import promptic from src
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from promptic.context.template_context import InstructionRenderContext
from promptic.pipeline.format_renderers.jinja2 import Jinja2FormatRenderer


def main():
    logging.basicConfig(level=logging.INFO)

    # 1. Load instruction content
    base_dir = Path(__file__).parent
    instruction_path = base_dir / "instruction.jinja"
    if not instruction_path.exists():
        print(f"Error: {instruction_path} not found.")
        return

    with open(instruction_path, "r") as f:
        content = f.read()

    print(f"--- Original Content ---\n{content}\n")

    # 2. Prepare data
    data = {
        "project": "Q3 Report",
        "is_urgent": True,
        "tasks": [
            {"title": "Collect metrics", "assignee": "Alice", "notes": "Check DB logs"},
            {"title": "Draft summary", "assignee": "Bob"},
        ],
    }

    # 3. Create context
    context = InstructionRenderContext(data=data)

    # 4. Render
    renderer = Jinja2FormatRenderer()
    try:
        rendered = renderer.render(content, context)
        print("--- Rendered Output ---")
        print(rendered)
    except Exception as e:
        print(f"Error rendering template: {e}")


if __name__ == "__main__":
    main()
