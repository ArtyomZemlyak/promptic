# Complete End-to-End Example

This example demonstrates the full context engineering library workflow covering all functionality.

## Overview

This comprehensive example shows:
- Blueprint authoring with hierarchical steps
- Adapter registration and configuration
- Preview generation (formatted terminal output)
- Render for LLM (plain text ready for LLM input)
- Instruction rendering
- Fallback handling

**Note**: This library focuses on context construction only. Pipeline execution is handled by external agent frameworks.

## Files

- `research_flow.yaml` - Complete blueprint definition
- `instructions/` - All instruction files
- `data/` - Sample data files
- `end_to_end.py` - Complete runnable demonstration

## Running the Example

```bash
python examples/complete/end_to_end.py
```

## Expected Output

The script will demonstrate:
1. Blueprint loading and validation
2. Adapter registration
3. Preview generation (Rich-formatted output)
4. Render for LLM (plain text for LLM consumption)
5. Instruction rendering (specific instruction by ID)
6. Fallback event handling
