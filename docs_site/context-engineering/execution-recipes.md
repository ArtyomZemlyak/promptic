# Execution Recipes

The `PipelineExecutor` walks hierarchical blueprint steps, fetching every instruction,
data slot, and memory provider via the `ContextMaterializer`. This guide demonstrates
how to configure a pipeline run, inspect logs, and react to size/policy warnings.

## Sample Five-Step Pipeline

```python
from promptic.adapters import AdapterRegistry
from promptic.sdk import adapters as sdk_adapters, pipeline
from promptic.sdk.api import build_materializer
from promptic.settings.base import ContextEngineSettings

settings = ContextEngineSettings(
    blueprint_root="blueprints",
    instruction_root="instructions",
    log_root="logs",
)

registry = AdapterRegistry()
sdk_adapters.register_csv_loader("research_sources", registry=registry)
sdk_adapters.register_static_memory_provider("research_memory", registry=registry)
settings.adapter_registry.data_defaults["research_sources"] = {"path": "data/sources.csv"}
settings.adapter_registry.memory_defaults["research_memory"] = {"values": ["vector://findings"]}

materializer = build_materializer(settings=settings, registry=registry)
result = pipeline.run_pipeline(
    blueprint_id="research-flow",
    settings=settings,
    materializer=materializer,
)

print("Run:", result.run_id)
for event in result.events:
    print(event.event_type, event.step_id, event.payload)
print("Warnings:", result.warnings)
```

The executor emits `ExecutionLogEntry` objects for every instruction, data, and memory
access. Loop steps add entries per iteration, while branch/sequence steps log children
in depth-first order. All events stream to `logs/<blueprint>-<run_id>.jsonl`, enabling
tail -f workflows or post-run audits.

## Loop & Branch Strategies

- **Loops**: Assign `loop_slot` to a `DataSlot` that returns a list/iterable. The executor
  resolves the slot once, logs a `data_resolved` event, then iterates over the cached
  items. Use `PipelineHooks.on_loop_item` to inject agent callbacks or to short-circuit
  long-running iterations.
- **Branches**: Define child steps with `kind="branch"` and populate `conditions`.
  Hook decisions can be enforced by overriding `PipelineHooks.before_step` to skip
  execution or to record custom telemetry.

## Logging & Policy Enforcement

`PolicyEngine` evaluates per-step budgets using `ContextEngineSettings.size_budget`.
If an instruction block exceeds `per_step_budget_chars`, the executor emits a
`size_warning` event (and the SDK surfaces the warning in `ExecutionResponse.warnings`).
Customize policies (e.g., token budgets) by extending `PolicyEngine` or injecting
additional emitters into `PipelineLogger`.

## Integration with Agents

Because every slot lookup flows through the `ContextMaterializer`, swapping adapters
remains identical to the preview story—register a new adapter under the same key and
provide fresh defaults. The executor's `PipelineHooks` allow host applications to:

- Forward per-step payloads to downstream agent orchestrators.
- Inject retries or fallback behaviors when adapters fail.
- Capture metrics (timings, token counts) alongside the built-in JSONL logs.

These patterns keep execution aligned with the clean-architecture constraints defined
in the specification while giving teams pragmatic extension points.
