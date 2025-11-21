# Simple Task Example

The simplest example demonstrating a basic workflow with file-first rendering.

## Overview

This minimal example shows:
- Creating a basic blueprint YAML file
- Structuring instruction files
- Rendering blueprints in file-first mode

## Files

- `task_workflow.yaml` - Simple blueprint with 3 steps
- `instructions/` - Instruction files for each step:
  - `understand_task_step.md`
  - `plan_action_step.md`
  - `execute_step.md`

## Usage

### Using SDK

```python
from promptic.sdk.blueprints import load_blueprint, preview_blueprint

# Load blueprint
blueprint = load_blueprint("examples/get_started/simple-task/task_workflow.yaml")

# Render in file-first mode
result = preview_blueprint(
    "examples/get_started/simple-task/task_workflow.yaml",
    render_mode="file_first"
)

print(result.markdown)
```

### Using CLI

```bash
promtic preview examples/get_started/simple-task/task_workflow.yaml --render-mode file_first
```

## Expected Output

The file-first rendering will produce a compact prompt with:
- Persona and goals (from `prompt_template`)
- Step summaries with file references
- References to detailed instruction files

## Next Steps

After understanding this example, check out:
- **Blueprint Basics** (`../us1-blueprints/`) - More detailed blueprint example
- **Tutorials** (`../../tutorials/`) - Complex real-world workflows
