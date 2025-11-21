# User Story 2: Plug Data & Memory Sources

This example demonstrates how to register and swap data/memory adapters without code changes.

## Overview

This example shows:
- Registering CSV and HTTP data adapters
- Registering a mock memory provider
- Swapping adapters without modifying blueprint code
- Verifying adapter swap works correctly with both inline and file-first rendering modes

## Files

- `blueprint.yaml` - Blueprint definition using adapters
- `data/sample.csv` - Sample data file
- `swap_adapters.py` - Runnable script demonstrating adapter registration and swapping

## Running the Example

```bash
python examples/tutorials/us2-adapters/swap_adapters.py
```

## Expected Output

The script will:
1. Register CSV adapter and static memory provider
2. Load blueprint and render preview (formatted output) - inline mode
3. File-first rendering with CSV adapter (compact prompts with references)
4. Render plain text context for LLM with CSV adapter
5. Demonstrate adapter swap concept (blueprint unchanged)
6. Show that adapters can be swapped without modifying blueprint code

## Key Features

- **Adapter Registration**: Register CSV and memory adapters
- **Dual Rendering Modes**: Shows how adapters work with both inline and file-first modes
- **Adapter Swapping**: Demonstrates transparent adapter swapping without blueprint changes
