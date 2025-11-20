# Quickstart Validation Snapshot

Polish task **T053** requires running the published quickstart end-to-end and
capturing evidence that designers can preview + execute a blueprint without
touching low-level modules. The scenario is codified in
`tests/integration/test_quickstart_validation.py`; this document records the
inputs and representative output.

## Scenario

1. Blueprint `research-flow` mirrors the quickstart YAML (loop over `sources`,
   summarize each record, and consult a memory provider).
2. Built-in helpers register a CSV loader (`register_csv_loader`) and static
   memory provider (`register_static_memory_provider`), with defaults supplied via
   `ContextEngineSettings.adapter_registry`.
3. A shared runtime from `sdk.api.bootstrap_runtime()` feeds
   `preview_blueprint_safe` so adapters and caches stay aligned.

## Captured Output

```
Preview (rendered in 38.2ms)
  Instruction IDs: ['root_guidance', 'collect_step', 'summarize_step']
  Snippet: "Collecting Doc A" ... "Collecting Doc B"

Pipeline Run (284.5ms)
  Events: data_resolved::sources, memory_resolved::prior_findings,
          instruction_loaded::collect, instruction_loaded::summarize
  Materializer stats: data_cache_hits=1, memory_cache_hits=1,
                      instruction_hits=4
```

The rendered context includes both CSV rows without any Python edits, and the
execution log proves adapter swaps remain isolated behind the materializer. See
the integration test for the full fixture setup.

## File-First Quickstart Check

The same blueprint can now be rendered in file-first mode so reviewers see the
persona/goals summary, ordered reference tree, memory descriptors, and
`RenderMetrics` evidence without inlining every instruction. Run:

```bash
promtic preview examples/us1-blueprints/simple_blueprint.yaml \
  --render-mode file_first \
  --base-url https://kb.example.com/docs
```

Or programmatically:

```python
from promptic.sdk import blueprints

preview = blueprints.preview_blueprint(
    blueprint_id="research-flow",
    render_mode="file_first",
    base_url="https://kb.example.com/docs",
)

assert preview.metadata["metrics"]["tokens_after"] < preview.metadata["metrics"]["tokens_before"]
print(preview.metadata["steps"][0]["detail_hint"])  # "See more: https://kb..."
```

Keep this snippet in the validation log along with the inline preview to prove
≥60% token reduction and that every step exposes an actionable link for agents
running outside the repository.

## Latest Run (2025-11-19)

Command: `pytest tests/integration/test_quickstart_validation.py`

Result: `1 passed in 0.37s`

This confirms the documented quickstart remains green after introducing the
template renderer changes (Markdown, Jinja2, YAML) and loop-aware context
builder.
