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

## Relationship to the Context Materializer

While builders/previewers arrive in later phases, the foundational
`ContextMaterializer` already coordinates blueprint data slots, registered
adapters, and instruction assets. Validated blueprints can be passed to the
materializer to resolve sample data or memory inputs, guaranteeing that future
preview/execution layers share the same caching and error-reporting behavior.
