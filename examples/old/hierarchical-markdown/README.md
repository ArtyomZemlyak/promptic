# Hierarchical Markdown (Advanced)

This example demonstrates how designers can express hierarchy and conditional
sections directly inside Markdown instructions at a low level. The file `instruction.md`
contains heading-based structure plus conditional markers of the form
`<!-- if:data.flag --> ... <!-- endif -->`.

**Note**: In the main workflow, conditional rendering happens automatically when rendering blueprints. This example shows the underlying mechanism for advanced users who need direct control over instruction rendering.

## Running the example

```bash
python examples/hierarchical-markdown/render_hierarchical.py
```

The script renders the instruction twice:

1. When `show_details=True`, the detailed section is included.
2. When `show_details=False`, the conditional section is removed.

The output illustrates how the parser preserves hierarchy while enabling
context-driven sections without modifying the blueprint.

## Main Workflow

In the main workflow, you typically use blueprints which handle conditional rendering automatically:

```python
from promptic.sdk.blueprints import load_blueprint, preview_blueprint

blueprint = load_blueprint("my_blueprint.yaml")
result = preview_blueprint("my_blueprint.yaml", render_mode="file_first")
```

See `examples/get_started/` and `examples/tutorials/` for the main workflow examples.
