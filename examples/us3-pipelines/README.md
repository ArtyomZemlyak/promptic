# User Story 3: Execute Reusable Instruction Pipelines

This example demonstrates hierarchical pipeline execution with per-item instruction fetching.

## Overview

This example shows:
- Creating a 5-step pipeline
- Step 3 loops over N items
- Fetches instruction for each item
- Execution log shows correct instruction IDs per item

## Files

- `hierarchical_blueprint.yaml` - Blueprint with hierarchical steps
- `run_pipeline.py` - Runnable script demonstrating pipeline execution

## Running the Example

```bash
python examples/us3-pipelines/run_pipeline.py
```

## Expected Output

The script will:
1. Execute the 5-step pipeline
2. Show step 3 looping over items
3. Display execution log with instruction IDs per item
