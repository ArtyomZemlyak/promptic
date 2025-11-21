# Process Data Instruction

This instruction demonstrates adapter usage in a blueprint.

## Steps

1. Load data from the configured adapter (CSV, HTTP, etc.)
2. Process each item in the data source
3. Generate insights based on the data
4. Use memory cache if available for prior results

## Adapter Flexibility

This blueprint can work with different adapters without code changes:
- CSV adapter: Loads data from CSV files
- HTTP adapter: Fetches data from APIs
- Other adapters: Can be registered and swapped transparently
