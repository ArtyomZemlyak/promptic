import logging
import sys
from pathlib import Path

# Ensure we can import promptic from src
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from promptic.blueprints.models import InstructionNode
from promptic.context.template_context import InstructionRenderContext
from promptic.pipeline.template_renderer import TemplateRenderer


def main():
    logging.basicConfig(level=logging.INFO)

    # 1. Load instruction content
    base_dir = Path(__file__).parent
    instruction_path = base_dir / "instruction.yaml"
    if not instruction_path.exists():
        print(f"Error: {instruction_path} not found.")
        return

    with open(instruction_path, "r") as f:
        content = f.read()

    print(f"--- Original Content ---\n{content}\n")

    # 2. Prepare data
    data = {
        "service_name": "user-service",
        "config": {"timeout": 30},
        "permissions": {"read": "public", "write": "admin"},
    }

    # 3. Create context
    context = InstructionRenderContext(data=data)

    # 4. Configure Node with Pattern
    # The pattern expects placeholders like $(variable.name)
    # Starts with letter/underscore to avoid matching $(...) in comments
    node = InstructionNode(
        instruction_id="yaml_example",
        source_uri=str(instruction_path),
        format="yaml",
        checksum="0" * 32,
        pattern=r"\$\((?P<placeholder>[a-zA-Z_][a-zA-Z0-9_.]+)\)",
    )

    # 5. Render
    renderer = TemplateRenderer()
    try:
        rendered = renderer.render(node, content, context)
        print("--- Rendered Output ---")
        print(rendered)
    except Exception as e:
        print(f"Error rendering template: {e}")


if __name__ == "__main__":
    main()
