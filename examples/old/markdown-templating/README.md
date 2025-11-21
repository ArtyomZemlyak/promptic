# Markdown Templating (Advanced)

This example demonstrates how to use Python string format syntax (`{}`) within Markdown instruction files to insert dynamic data at a low level.

**Note**: In the main workflow, templating happens automatically when rendering blueprints. This example shows the underlying mechanism for advanced users who need direct control over instruction rendering.

## Features

- **Simple Placeholders**: `{data.variable}`
- **Nested Access**: `{data.user.profile.name}` (supports dot notation for dicts)
- **Escaping**: Use `{{` and `}}` for literal braces
- **Formatting**: Preserves indentation and whitespace

## Files

- `instruction.md`: Sample instruction file with placeholders
- `render_markdown.py`: Python script demonstrating how to render the instruction with data

## Usage

Run the example script:

```bash
python render_markdown.py
```

## Context Namespacing

Variables are namespaced under `data`, `memory`, `step`, or `blueprint` in the context:

- `{data.my_var}`: Access data slot value
- `{memory.my_mem}`: Access memory slot value
- `{step.title}`: Access current step title

## Main Workflow

In the main workflow, you typically use blueprints which handle templating automatically:

```python
from promptic.sdk.blueprints import load_blueprint, preview_blueprint

blueprint = load_blueprint("my_blueprint.yaml")
result = preview_blueprint("my_blueprint.yaml", render_mode="file_first")
```

See `examples/get_started/` and `examples/tutorials/` for the main workflow examples.
