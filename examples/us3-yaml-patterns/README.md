# User Story 3: YAML Custom Patterns

This example demonstrates how to use custom regex patterns for data insertion in YAML (or other text) files.

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
