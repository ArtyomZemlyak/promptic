# Quickstart – File-First Prompt Hierarchy

Follow these steps to activate and validate the file-first rendering mode inside the Promptic toolkit.

## Prerequisites
1. Python 3.11 environment with project dependencies installed (`pip install -e .[dev]`).
2. pre-commit hooks installed: `pre-commit install`.
3. Example blueprints cloned locally (repository already contains `examples/us1-blueprints` and `examples/complete`).

## Configure Memory Format (Optional)
1. Create or update `memory/format.md` inside your blueprint directory.
2. Describe the memory structure (e.g., hierarchical folders + `.md` files).  
3. Reference this descriptor in the blueprint metadata so the renderer can surface it.

## Render in File-First Mode
1. Run CLI preview with the new flag:
   ```bash
   promtic preview examples/us1-blueprints/simple_blueprint.yaml --render-mode file_first --base-url https://kb.example.com
   ```
2. Confirm the output:
   - Persona + goals summarized in ≤10 lines.
   - Each step bullet lists a summary plus a `See more: instructions/<step>.md` hint.
   - A “Memory & logging” block points to your configured directories and format descriptor.

## Programmatic Usage
```python
from promptic.sdk.blueprints import BlueprintPreviewer

previewer = BlueprintPreviewer(render_mode="file_first", base_url="https://kb.example.com")
result = previewer.render("examples/us1-blueprints/simple_blueprint.yaml")
print(result.markdown)
print(result.metadata["steps"][0])
```

## Validate Metrics & Tests
1. Ensure render metrics show ≥60% token reduction (`result.metadata["metrics"]`).
2. Run targeted tests:
   ```bash
   pytest tests -k file_first
   ```
3. Run the full suite plus `pre-commit run --all-files` before opening a PR.

## Troubleshooting
- Missing file errors: create the referenced instruction/memory file or fix the path in the blueprint.
- Nested reference depth exceeded: raise the configured depth limit only if agent context budget allows.
- Agents without filesystem access: pass `--base-url` (CLI) or `base_url` (SDK) so links become absolute.
