# Execution Recipes

The Context Engineering SDK focuses on previewing blueprints and exposing the
structured metadata that downstream agents need to run safely. Execution is the
responsibility of host applications, which compose their own loops around the
`ContextMaterializer`. This guide shows how to build that preview-oriented flow,
prime caches, and inspect diagnostic signals that agents can act upon.

## Sample Preview-Oriented Workflow

```python
from promptic.adapters import AdapterRegistry
from promptic.sdk import adapters as sdk_adapters, blueprints as sdk_blueprints
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
preview = sdk_blueprints.preview_blueprint(
    blueprint_id="research-flow",
    settings=settings,
    materializer=materializer,
    sample_data={"research_sources": [{"title": "Doc A"}]},
)

print(preview.rendered_context)
print("Warnings:", preview.warnings)
print("Instruction IDs:", preview.instruction_ids)
```

The preview response surfaces every instruction that participated in the render
alongside fallback diagnostics, making it easy to construct a compact prompt
for an LLM while keeping the heavy lifting (data/memory resolution) inside the
materializer.

## Loop & Branch Strategies

- **Loops**: Assign `loop_slot` to a `DataSlot` that returns a list/iterable. When the
  previewer renders a loop, it resolves the slot once, iterates over the cached records,
  and produces instruction text for each iteration. Custom executors can reuse this
  structure by traversing `ContextBlueprint.steps` in the same order.
- **Branches**: Define child steps with `kind="branch"` and populate `conditions`.
  Your orchestration layer can evaluate those predicates before deciding which
  branch to render or execute.

## Logging & Policy Enforcement

`PolicyEngine` evaluates per-step budgets using `ContextEngineSettings.size_budget`.
When a preview exceeds `per_step_budget_chars`, the engine emits warnings that
ship with the `PreviewResponse`. Downstream orchestrators can treat those warnings
as signals to truncate responses or request additional human review. If you build
custom executors, you can still wire `PipelineLogger` to emit structured events
and reuse the same policy checks.

Every `instruction_loaded` event now includes a `reference_path` payload derived
from the filesystem store. This mirrors the file-first metadata so downstream
agents (or log processors) can open the same `instructions/*.md` files that were
referenced in the compact prompt. When combined with the new CLI/SDK flag
`--render-mode file_first`, operators can hand LLMs the persona/goals summary
while still relying on executor logs to trace which files were accessed during a
full pipeline run.

## Instruction Fallback Telemetry

`InstructionFallbackPolicy` lets previews keep running even if a remote store goes dark. Declare the fallback in the blueprint (e.g., `warn` with a placeholder) and register providers with the modes they support. When the provider raises an error, `ContextMaterializer.apply_instruction_fallback()` records an `instruction_fallback` event and returns either the placeholder (`warn`) or an empty string (`noop`). SDK responses (`preview.fallback_events`) expose the structured diagnostics:

```python
for event in result.fallback_events:
    print(f"[{event.mode}] {event.instruction_id} → {event.placeholder_used}")
```

Because fallback handling stays inside the materializer + executor layers, blueprint authors do not edit code when swapping providers; they simply pick the policy that matches their tolerance for degraded instructions.
Pipeline event streams also emit `instruction_fallback` entries, which means the JSONL logs under `logs/` can be parsed for degraded instructions without correlating additional metadata.

## Integration with Agents

Because every slot lookup flows through the `ContextMaterializer`, swapping adapters
remains identical to the preview story—register a new adapter under the same key and
provide fresh defaults. Host applications can build their own execution loops around
the materializer hooks to forward per-step payloads, inject retries, or capture
metrics alongside the JSONL logs emitted by `ContextPreviewer`.

## Runtime Bootstrap & Benchmarks

Use `promptic.sdk.api.bootstrap_runtime()` when running recipes from scripts or
notebooks. It wires settings, registry, and a shared `ContextMaterializer`
instance so repeated previews reuse warm caches. Pair that with
`materializer.snapshot_stats()` to capture cache hit/miss ratios before and after
your run—`tests/integration/test_performance.py` demonstrates how we keep preview
latency under 500 ms even with multiple instruction blocks. For release readiness,
the docs_site quickstart now mirrors this flow and records a
`quickstart-validation` snapshot so every adapter swap is proven end-to-end.

To analyze file-first output alongside execution logs, run:

```bash
promtic preview blueprints/research-flow.yaml --render-mode file_first --base-url https://kb.example.com
pytest tests/integration/test_instruction_templating.py -k file_first
```

The first command prints the persona/goals/steps summary plus `RenderMetrics`,
while the second ensures integration coverage for absolute links, depth-limit
warnings, and the “Memory & Logging” block. Combine those artifacts when handing
the workflow to hosted agents or human reviewers.
