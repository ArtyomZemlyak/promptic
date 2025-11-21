# User Story 1: Blueprint Hierarchical Contexts

This example demonstrates how to author hierarchical blueprints and preview merged contexts without editing Python code.

## Overview

This example shows:
- Creating a 5-step blueprint with nested instructions
- Previewing the composed context with sample data (inline mode)
- File-first rendering (compact prompts with file references)
- Using the SDK to build and preview blueprints

## Files

- `simple_blueprint.yaml` - A sample blueprint definition
- `instructions/` - Instruction files referenced by the blueprint
- `run_preview.py` - Runnable script demonstrating blueprint authoring and preview

## Running the Example

```bash
python examples/get_started/us1-blueprints/run_preview.py
```

## Expected Output

The script will:
1. Load the blueprint from YAML
2. Preview the merged context (formatted terminal output with Rich) - inline mode
3. File-first rendering showing compact prompts with file references
4. Render plain text context ready for LLM input
5. Show all referenced instructions
6. Warn on any missing assets or fallback events

## Key Features

- **Minimal API**: Just a few lines of code to load and render blueprints
- **Dual Rendering Modes**: Demonstrates both inline and file-first rendering
- **File References**: Shows how file-first mode creates compact prompts with references
