# Data Model – File-First Prompt Hierarchy

## Overview
The feature extends existing blueprint rendering by introducing explicit entities that describe hierarchical prompts, instruction references, and memory channels. These entities remain framework-agnostic, allowing CLI, SDK, or hosted agents to consume the same structures.

## Entities

### PromptHierarchyBlueprint
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `blueprint_id` | str | Stable identifier from blueprint registry | Required |
| `persona` | str | Short persona description included in root prompt | ≤ 2 sentences |
| `objectives` | list[str] | Ordered goals that contextualize the workflow | 1–5 entries |
| `steps` | list[`InstructionReference`] | Ordered step metadata referencing files | Must match blueprint-defined steps |
| `memory_channels` | list[`MemoryChannel`] | Memory/log destinations surfaced to agents | Optional |
| `metrics` | `RenderMetrics` | Token counts and reference statistics | Auto-calculated |

Relationships: Aggregates `InstructionReference`, `MemoryChannel`, and `RenderMetrics`.

### InstructionReference
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | str | Deterministic slug derived from instruction file path (e.g., `instructions_think_md`) | Unique within blueprint |
| `title` | str | Human-friendly step name | Derived from blueprint |
| `summary` | str | ≤120-token synopsis of the instruction file | Auto-truncated & overrideable |
| `reference_path` | str | Relative path or absolute URL (when base URL provided) | Must resolve to readable file |
| `detail_hint` | str | Text telling agents how to open/use the reference | Required |
| `token_estimate` | int | Approx tokens for referenced instruction | Non-negative |
| `children` | list[`InstructionReference`] | Nested references (tree structure) | Depth ≤ configured max (default 3) |

Relationships: Forms a tree under `PromptHierarchyBlueprint.steps`.

### MemoryChannel
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `location` | str | Directory or file path where agents should write | Must exist or be creatable |
| `expected_format` | str | Human description of format semantics | Required |
| `format_descriptor_path` | str \| None | Path to user-supplied format description file | Optional; fallback to default template |
| `retention_policy` | str | Guidance on how long to keep notes | Optional but recommended |
| `usage_examples` | list[str] | Examples of valid entries | Optional |

Relationships: Listed under `PromptHierarchyBlueprint.memory_channels`.

### RenderMetrics
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `tokens_before` | int | Token count of legacy inline render | ≥0 |
| `tokens_after` | int | Token count of file-first render | ≥0 |
| `reference_count` | int | Number of step references emitted | ≥ number of steps |
| `missing_paths` | list[str] | Missing files detected during validation | Empty list required for successful render |

## Validation Rules
- `InstructionReference.children` must not create cycles; renderer enforces depth limit and warns when additional nesting is truncated.
- Every `reference_path` must pass existence validation before render output is returned; missing paths block execution.
- Memory channels without a custom `format_descriptor_path` automatically reference the default hierarchical `.md` template and must mention it in the generated prompt copy.
- Token reduction is measured using `RenderMetrics` and must demonstrate ≥60% reduction vs. inline mode for representative blueprints (§SC-001).

## State & Lifecycle Considerations
- Prompt blueprints evolve via versioned files; the `blueprint_id` combined with git SHA serves as the immutable state reference for renders.
- Memory channels can be added/removed without code changes as long as descriptors are present; runtime validation highlights mismatches.
- Render metrics are recalculated each time a blueprint is rendered, enabling regression detection in tests.
