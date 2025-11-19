# User Story 2: Jinja2 Templating

This example demonstrates how to use Jinja2 syntax in instruction files for conditional logic, loops, and complex data usage.

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
