# User Story 1: Blueprint Hierarchical Contexts

This example demonstrates how to author hierarchical blueprints and preview merged contexts without editing Python code.

## Overview

This example shows:
- Creating a 5-step blueprint with nested instructions
- Previewing the composed context with sample data
- Using the SDK to build and preview blueprints

## Files

- `simple_blueprint.yaml` - A sample blueprint definition
- `instructions/` - Instruction files referenced by the blueprint
- `run_preview.py` - Runnable script demonstrating blueprint authoring and preview

## Running the Example

```bash
python examples/us1-blueprints/run_preview.py
```

## Expected Output

The script will:
1. Load the blueprint from YAML
2. Preview the merged context (formatted terminal output with Rich)
3. Render plain text context ready for LLM input
4. Show all referenced instructions
5. Warn on any missing assets or fallback events
