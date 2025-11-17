# Data Model: Context Engineering Library

All models will be implemented as `pydantic.BaseModel` subclasses (domain layer) to guarantee validation, serialization, and compatibility with `pydantic-settings`.

## ContextBlueprint
| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `id` | `UUID4` | Blueprint identifier exposed to SDK/agents | Auto-generated; immutable |
| `name` | `str` | Human-readable label | 3–80 chars |
| `prompt_template` | `str` | Base system prompt text | Non-empty; supports Jinja2 placeholders |
| `global_instructions` | `list[InstructionNodeRef]` | Instruction assets applied to every step | Each ref must resolve |
| `steps` | `list[BlueprintStep]` | Ordered pipeline definition | ≥1 step |
| `data_slots` | `list[DataSlot]` | Required data inputs | Names unique per blueprint |
| `memory_slots` | `list[MemorySlot]` | Required memory inputs | Names unique per blueprint |
| `metadata` | `dict[str, Any]` | Tags, version, owner | Optional |

Relationships: owns many `BlueprintStep`, references `InstructionNode`, `DataSlot`, `MemorySlot`.

## BlueprintStep
| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `step_id` | `str` | Unique within blueprint | slug regex |
| `title` | `str` | Designer-friendly name | 3–60 chars |
| `kind` | `Literal["sequence","loop","branch"]` | Execution semantics | required |
| `instruction_refs` | `list[InstructionNodeRef]` | Instructions for this step | allow empty for data-only steps |
| `children` | `list[BlueprintStep]` | Nested sub-steps | Depth capped by settings |
| `loop_slot` | `Optional[str]` | Data slot used for iteration | required when `kind="loop"` |
| `conditions` | `Optional[list[Condition]]` | Branch predicates | validated expression |

Relationships: recursive parent/child; may include `loop_slot` referencing `DataSlot`.

## InstructionNode
| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `instruction_id` | `str` | Asset identifier (e.g., file stem) | matches file path |
| `source_uri` | `AnyUrl | FilePath` | Where to load asset | must exist for filesystem |
| `format` | `Literal["md","txt","jinja"]` | Rendering hint | default `md` |
| `checksum` | `str` | Content fingerprint for caching | sha256 hex |
| `locale` | `str` | Language/locale | ISO tag |
| `version` | `str` | Semantic version for auditing | semver |

Instruction nodes live in instruction store; blueprint references only `instruction_id`.

## DataSlot
| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `name` | `str` | Slot identifier | slug |
| `schema` | `JsonSchemaValue` | Expected shape for adapter output | validated by Pydantic |
| `adapter_key` | `str` | Registry key for data source | must map to registered adapter |
| `cardinality` | `Literal["single","list"]` | Determines loop semantics | default `single` |
| `ttl_seconds` | `Optional[int]` | Cache hint | >=0 |

## MemorySlot
| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `name` | `str` | Slot identifier | slug |
| `provider_key` | `str` | Registered memory provider | required |
| `scope` | `Literal["conversation","project","global"]` | Access level | default `conversation` |
| `fallback` | `Optional[str]` | Behavior when missing | `warn`, `noop`, `error` |

## AdapterRegistration
| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `key` | `str` | Registry name (unique) | slug |
| `type` | `Literal["data","memory"]` | Adapter category | required |
| `entry_point` | `str` | Python import path to factory | importable |
| `config_model` | `type[BaseSettings]` | Pydantic settings used for config | subclass of `BaseSettings` |
| `capabilities` | `set[str]` | e.g., `{"async","streaming"}` | optional |

## ExecutionLogEntry
| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `timestamp` | `datetime` | Event time | timezone-aware |
| `step_id` | `str` | Step generating event | must exist |
| `event_type` | `Literal["instruction_loaded","data_resolved","memory_resolved","size_warning","error"]` | Event classification | required |
| `payload` | `dict[str, Any]` | Context (sizes, adapter keys, errors) | kept ≤4 KB |
| `reference_ids` | `list[str]` | Instruction/data/memory IDs touched | optional |

## Relationships Overview
- `ContextBlueprint` aggregates `BlueprintStep`, `DataSlot`, `MemorySlot`.
- `BlueprintStep` tree references `InstructionNode` via `InstructionNodeRef` (id + version).
- `DataSlot` / `MemorySlot` resolve via `AdapterRegistration`.
- `PipelineExecutor` produces `ExecutionLogEntry` records per step, linking back to blueprint + adapters.
