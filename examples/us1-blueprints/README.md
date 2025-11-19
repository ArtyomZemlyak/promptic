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
2. Preview the merged context
3. Show all referenced instructions
4. Warn on any missing assets
