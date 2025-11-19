# Context Blueprint Authoring

The Context Engineering SDK models conversational workflows as strongly-typed
`ContextBlueprint` objects. Each blueprint combines prompts, reusable
instruction assets, adapter-backed data slots, and optional memory slots. This
guide summarizes the foundational modules added in Phase 1 so designers and SDK
consumers understand how blueprints are represented and validated before we add
story-specific services.

## Domain Model Overview

All schema objects live in `promptic.blueprints.models` and are implemented with
Pydantic 2.x. Key classes:

- `ContextBlueprint`: top-level container with metadata, prompt template,
  ordered `BlueprintStep` tree, `DataSlot` and `MemorySlot` definitions, and
  optional `InstructionNodeRef` references applied globally.
- `BlueprintStep`: hierarchical step supporting `sequence`, `loop`, and
  `branch` semantics. Validators ensure loop steps declare `loop_slot` and
  branch steps own `Condition` predicates.
- `InstructionNode` / `InstructionNodeRef`: metadata for instruction assets
  discovered by the filesystem store.
- `ExecutionLogEntry`: structured event emitted by preview/executor flows.

Models aggressively enforce uniqueness (step IDs, slot names, instruction
references) so downstream services can assume canonical shapes without
additional checks.

## Authoring & Serialization

Blueprints can be created directly in Python or serialized to YAML for version
control. The helpers in `promptic.blueprints.serialization` encapsulate the
round-trip:

```python
from promptic.blueprints import (
    BlueprintStep,
    ContextBlueprint,
    InstructionNodeRef,
    dump_blueprint,
    load_blueprint,
)

blueprint = ContextBlueprint(
    name="Research Flow",
    prompt_template="You are a structured researcher.",
    steps=[
        BlueprintStep(
            step_id="collect",
            title="Collect Sources",
            instruction_refs=[InstructionNodeRef(instruction_id="collect.md")],
        )
    ],
)

dump_blueprint(blueprint, "blueprints/research-flow.yaml")
loaded = load_blueprint("blueprints/research-flow.yaml")
assert loaded.id == blueprint.id
```

`blueprint_json_schema()` exposes a JSON Schema document derived from the
Pydantic models so editor tooling or CI pipelines can validate YAML artifacts.

## Validation & Budget Enforcement

`promptic.pipeline.validation.BlueprintValidator` enforces key guardrails:

- Maximum step depth from `ContextEngineSettings.size_budget.max_step_depth`
- Prompt template size relative to `max_context_chars`
- Presence of all referenced instruction assets (via `InstructionStore.exists`)

The validator returns an `OperationResult`, surfacing warnings when designers
hit depth limits and raising `BlueprintValidationError` when structural issues
are detected. This mirrors the rules described in the project spec, giving us a
single authoritative enforcement point.

## Blueprint Builder Service

Phase 3 introduces `promptic.pipeline.builder.BlueprintBuilder`, a thin service
that locates YAML/JSON artifacts under `ContextEngineSettings.blueprint_root`,
loads them via the serialization helpers, and runs the validator. The builder
returns an `OperationResult` so callers can access warnings (e.g., depth equals
budget) without raising exceptions.

```python
from promptic.pipeline.builder import BlueprintBuilder
from promptic.pipeline.validation import BlueprintValidator
from promptic.settings.base import ContextEngineSettings

settings = ContextEngineSettings(blueprint_root="blueprints", instruction_root="instructions")
validator = BlueprintValidator(settings=settings)
builder = BlueprintBuilder(settings=settings, validator=validator)

result = builder.load("research-flow")
if result.ok:
    blueprint = result.unwrap()
    print("Loaded blueprint:", blueprint.name)
else:
    raise result.error
```

Behind the scenes the builder relies on the new `promptic.instructions.cache.InstructionCache`
wrapper which caches filesystem nodes/content using an LRU map. This keeps repeated
validation or preview runs fast even when blueprints reference dozens of instruction files.

## Previewing Blueprints with the SDK

Designers can now preview any blueprint without writing orchestration code thanks
to `promptic.sdk.blueprints.preview_blueprint`. The façade wires a
`BlueprintBuilder`, `ContextPreviewer`, and `ContextMaterializer`, ensuring
adapter registry access still flows exclusively through the materializer.

```python
from promptic.sdk import blueprints

preview = blueprints.preview_blueprint(
    blueprint_id="research-flow",
    sample_data={"sources": [{"title": "Paper A", "url": "https://example.com"}]},
    sample_memory={"prior_findings": ["vector://finding-123"]},
)

print(preview.rendered_context)
print("Warnings:", preview.warnings)
print("Instruction IDs:", preview.instruction_ids)
```

The previewer resolves every instruction reference via the materializer,
applies sample data/memory overrides, and then hands the assembled payload to
`promptic.context.rendering.render_context_preview`. That renderer uses Rich to
produce a console-friendly snapshot with highlighted placeholders, JSON panels
for resolved data/memory, and a table summarizing each step’s instruction blocks.

## Relationship to the Context Materializer

`ContextMaterializer` remains the sole gateway to adapters and instruction stores.
Preview helpers inject it explicitly (or accept a caller-provided instance), log
the instruction IDs used for auditing, and reuse the same caching strategy that
future executor phases will depend on. This enforces the layering rules outlined
in the specification: builders/previewers never reach into adapter registries or
filesystem specifics directly.

## Troubleshooting & Performance Snapshots

Polish tasks introduced structured diagnostics so blueprint authors can fix issues
without digging through stack traces:

- `promptic.context.errors.describe_error()` converts any `PrompticError` into an
  `ErrorDetail` containing a machine-readable code, human hint, and context payload
  (e.g., missing instruction IDs or adapter keys).
- `promptic.sdk.api.preview_blueprint_safe()` and `run_pipeline_safe()` wrap the
  standard SDK functions, returning an `SdkResult` that embeds `ErrorDetail`,
  run duration, and any warnings instead of raising immediately.

```python
from promptic.sdk import api

result = api.preview_blueprint_safe(blueprint_id="research-flow")
if result.error:
    print(result.error.code, "→", result.error.hint)
else:
    print(f"Rendered in {result.duration_ms:.2f}ms")
```

The `ContextMaterializer` now exposes `prefetch_instructions()` plus
`snapshot_stats()`. Prefetch warms the LRU caches before rendering, while the stats
object reports cache hit ratios and adapter instantiations so you can confirm
performance goals directly from the SDK.
