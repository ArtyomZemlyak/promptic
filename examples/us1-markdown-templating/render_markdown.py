import logging
import sys
from pathlib import Path

# Ensure we can import promptic from src
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from promptic.context.template_context import InstructionRenderContext
from promptic.pipeline.format_renderers.markdown import MarkdownFormatRenderer


def main():
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # 1. Load instruction content
    base_dir = Path(__file__).parent
    instruction_path = base_dir / "instruction.md"
    if not instruction_path.exists():
        print(f"Error: {instruction_path} not found.")
        return

    with open(instruction_path, "r") as f:
        content = f.read()

    print(f"--- Original Content ---\n{content}\n")

    # 2. Prepare data
    data = {"user": {"name": "Alice", "role": "Admin"}, "task": "Review system logs"}
    print(f"--- Data ---\n{data}\n")

    # 3. Create context
    # Note: In a real pipeline, this is built automatically from blueprint/data slots
    context = InstructionRenderContext(data=data)

    # 4. Render
    renderer = MarkdownFormatRenderer()
    try:
        rendered = renderer.render(content, context)
        print("--- Rendered Output ---")
        print(rendered)
    except Exception as e:
        print(f"Error rendering template: {e}")


if __name__ == "__main__":
    main()
