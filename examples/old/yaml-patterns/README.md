# YAML Custom Patterns (Advanced)

This example demonstrates how to use custom regex patterns for data insertion in YAML (or other text) files at a low level.

**Note**: In the main workflow, templating happens automatically when rendering blueprints. This example shows the underlying mechanism for advanced users who need custom placeholder patterns.

## Features

- **Custom Patterns**: Define your own placeholder syntax using Regex.
- **Flexible**: Support legacy formats or specialized syntax (e.g., `$(var)`, `<%= var %>`).

## Files

- `instruction.yaml`: Sample YAML file using `$(...)` placeholders.
- `render_yaml.py`: Python script demonstrating how to configure the `pattern` and render.

## Usage

Run the example script:

```bash
python render_yaml.py
```

## Pattern Configuration

The `InstructionNode` takes a `pattern` argument which must be a valid regex string containing a named group `(?P<placeholder>...)`.

Example patterns:
- `\$\((?P<placeholder>[\w\.]+)\)` matches `$(variable)`
- `\{\{(?P<placeholder>[^}]+)\}\}` matches `{{variable}}` (default)
- `<%=\s*(?P<placeholder>[\w\.]+)\s*%>` matches `<%= variable %>`

## Main Workflow

In the main workflow, you typically use blueprints which handle templating automatically:

```python
from promptic.sdk.blueprints import load_blueprint, preview_blueprint

blueprint = load_blueprint("my_blueprint.yaml")
result = preview_blueprint("my_blueprint.yaml", render_mode="file_first")
```

See `examples/get_started/` and `examples/tutorials/` for the main workflow examples.
