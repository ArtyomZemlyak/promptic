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
3. A shared runtime from `sdk.api.bootstrap_runtime()` feeds both
   `preview_blueprint_safe` and `run_pipeline_safe`.

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
