# User Story 1: Markdown Templating

This example demonstrates how to use Python string format syntax (`{}`) within Markdown instruction files to insert dynamic data.

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
