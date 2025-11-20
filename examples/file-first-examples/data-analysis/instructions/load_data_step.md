# Load and Validate Data

Load datasets from configured sources and perform initial validation.

## Loading Process

1. **Identify data sources**: Determine which datasets to load
2. **Select appropriate loader**: Use CSV, JSON, or Parquet loader based on format
3. **Handle errors gracefully**: Catch and report loading failures
4. **Log metadata**: Record dataset size, shape, and basic statistics

## Validation Checklist

- [ ] Data loaded successfully
- [ ] Expected columns/fields present
- [ ] Data types are correct
- [ ] No obvious corruption detected
- [ ] File size matches expectations

## Error Handling

- Report missing files clearly
- Handle encoding issues
- Detect and report malformed data
- Provide actionable error messages
