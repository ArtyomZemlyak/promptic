# User Story 2: Plug Data & Memory Sources

This example demonstrates how to register and swap data/memory adapters without code changes.

## Overview

This example shows:
- Registering CSV and HTTP data adapters
- Registering a mock memory provider
- Swapping adapters without modifying blueprint code
- Verifying adapter swap works correctly

## Files

- `blueprint.yaml` - Blueprint definition using adapters
- `data/sample.csv` - Sample data file
- `swap_adapters.py` - Runnable script demonstrating adapter registration and swapping

## Running the Example

```bash
python examples/us2-adapters/swap_adapters.py
```

## Expected Output

The script will:
1. Register CSV adapter and render blueprint
2. Register HTTP adapter and render blueprint again
3. Verify both work without blueprint code changes
