# Example 0: Simple Render

This example demonstrates the simplest way to use promptic - the `render()` function.

## Overview

The `render()` function is the main entry point for promptic. It combines loading and rendering into one convenient function call.

## Files

- `task.md` - Main prompt file with references to other files
- `context.md` - Context information referenced by task.md
- `instructions.md` - Instructions referenced by task.md
- `simple_render.py` - Basic usage of render()
- `with_variables.py` - Using render() with variable substitution

## Usage

```bash
# Basic render
python simple_render.py

# With variables
python with_variables.py
```

## Key Features

1. **One-step rendering**: Load and render in a single function call
2. **Variable substitution**: Pass variables for dynamic content
3. **Format conversion**: Convert between markdown, YAML, JSON, and Jinja2
4. **Render modes**: Choose between full (inline) and file-first (preserve links)

## Why use render()?

- **Simplicity**: One function call instead of two
- **Convenience**: Sensible defaults for common use cases
- **Flexibility**: All the power of node networks with a simpler API
- **Recommended**: This is the recommended way to use promptic for most cases
