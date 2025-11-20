# Hierarchical Markdown Example (US4)

This example demonstrates how designers can express hierarchy and conditional
sections directly inside Markdown instructions. The file `instruction.md`
contains heading-based structure plus conditional markers of the form
`<!-- if:data.flag --> ... <!-- endif -->`.

## Running the example

```bash
python examples/hierarchical-markdown/render_hierarchical.py
```

The script renders the instruction twice:

1. When `show_details=True`, the detailed section is included.
2. When `show_details=False`, the conditional section is removed.

The output illustrates how the parser preserves hierarchy while enabling
context-driven sections without modifying the blueprint.
