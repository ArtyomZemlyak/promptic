# Jinja2 Templating (Advanced)

This example demonstrates how to use Jinja2 syntax in instruction files for conditional logic, loops, and complex data usage at a low level.

**Note**: In the main workflow, templating happens automatically when rendering blueprints. This example shows the underlying mechanism for advanced users who need direct control over instruction rendering.

## Features

- **Variable Interpolation**: `{{ data.variable }}`
- **Conditionals**: `{% if condition %} ... {% endif %}`
- **Loops**: `{% for item in list %} ... {% endfor %}`
- **Filters**: `{{ value | filter }}`

## Files

- `instruction.jinja`: Sample instruction file with Jinja2 syntax
- `render_jinja2.py`: Python script demonstrating how to render the instruction

## Usage

Run the example script:

```bash
python render_jinja2.py
```

## Context Namespacing

Variables are namespaced just like in Markdown templating:

- `data.*`
- `memory.*`
- `step.*`
- `blueprint.*`

## Main Workflow

In the main workflow, you typically use blueprints which handle templating automatically:

```python
from promptic.sdk.blueprints import load_blueprint, preview_blueprint

blueprint = load_blueprint("my_blueprint.yaml")
result = preview_blueprint("my_blueprint.yaml", render_mode="file_first")
```

See `examples/get_started/` and `examples/tutorials/` for the main workflow examples.
