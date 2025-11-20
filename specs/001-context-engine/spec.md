# Feature Specification: Context Engineering Library

**Feature Branch**: `001-context-engine`  
**Created**: 2025-11-17  
**Status**: Draft  
**Input**: User description: "Я хочу сделать библиотеку на python, которая будет позволять работать с промптами, контекстом и памятью в унифицированном режиме. Идея в том, что контекст = промпт + инструкции + данные + память и тд, и получается, если мы делаем библиотеку для промптов, то это все нужно учитывать вместе. Тут еще есть поле для размышлений, как и что лучше отделять, так как данные и память могут абсолютно любыми способами получаться, и лучше это не захардкоживать. А вот инструкции и промпт точно можно, плюс места под данные и память (так называемый context engineering). И самая главная идея - все части контекста могут быть иерархическими и выполняться агентом иерархически. К примеру, у нас есть пайплайн работы агента в 5 шагов, но 3 шаг состоит из списка действий для N элементов из данных - и чтобы не передавать список действий в промпте каждый раз, то можно сделать к примеру файл 3_step_instruction - и вот к этому файлу будет обращаться агент при каждой обработке элемента в 3 шаге. То есть, мы не захардкодиваем все шаги и инструкции в коде, а предлагаем агенту инструкции как что делать, но итоговый пайплайн действий выбирает он сам."
> This specification MUST satisfy the `promptic Constitution`: clean architecture layering, SOLID responsibilities, mandatory tests, documentation updates, and readability.

**Scope Clarification**: This feature delivers a pure Python library for context engineering—constructing LLM-ready contexts from hierarchical blueprints. The library focuses solely on context construction (loading blueprints, rendering text for LLM input); execution is handled by external agent frameworks. No CLI utilities, HTTP/REST services, or persistent servers are included; all interactions happen through the SDK. The library is designed to be compatible with any agent framework accessible via Python, with minimal API surface (3 lines of Python code for basic usage).

## Clarifications

### Session 2025-11-17

- Q: Which entrypoints are in scope (library vs CLI vs HTTP)? → A: Importable Python library only; no CLI or HTTP surfaces.

### Session 2025-11-18

- Q: Should `ContextMaterializer` be treated as a new use case or folded into existing preview/executor services? → A: Keep it as a dedicated registry-style module documented in the spec so layering remains explicit.
- Q: Should T020/T021 rely on ContextMaterializer from day one or pull T034 earlier? → A: Keep T034 in US2, but inject the existing ContextMaterializer interface into T020/T021 immediately and add tests proving preview/executor flows never touch adapters directly.

### Session 2025-01-27

- Q: Where should examples folder be located and how should it be structured? → A: Repository root `examples/` with subdirectories by user story (us1-blueprints/, us2-adapters/) plus `complete/` for end-to-end scenarios covering all functionality.
- Q: Should the spec define explicit performance targets (latency, throughput, scale limits)? → A: No explicit performance targets; optimize based on profiling during development. Size budgets (per-step context limits) remain the primary constraint mechanism.
- Q: What error response format should the SDK use (exceptions vs structured errors vs hybrid)? → A: Hybrid approach: raise domain-specific exceptions (e.g., `BlueprintValidationError`, `AdapterNotFoundError`) for fatal errors; return structured error dicts in response objects for warnings/non-fatal issues (e.g., fallback events, validation warnings).
- Q: What instruction asset format support is required (plain-text only vs templates vs multiple formats)? → A: Support multiple formats natively (Markdown, JSON, YAML, plain-text) with format auto-detection. JSON is the canonical/main format internally; all other formats convert to JSON during ingestion/processing.
- Q: What logging format and schema should be used for execution logs? → A: Structured JSONL format with defined schema: each entry includes `timestamp`, `level`, `event_type` (e.g., "instruction_accessed", "adapter_resolved", "fallback_applied"), `blueprint_id`, `step_id` (if applicable), `asset_id`, and `metadata` (dict) for structured querying and audit trails.

### Session 2025-01-28

- Q: What minimal API should be provided for loading blueprint.yaml? → A: All three variants must be supported: (A) `load_blueprint("my_blueprint")` - auto-discovery by name, (B) `load_blueprint("path/to/blueprint.yaml")` - explicit file path, (C) `load_blueprint("my_blueprint", settings=...)` - with optional settings. All dependencies (instructions, adapters) are resolved automatically under the hood.
- Q: How should preview rendering and LLM text generation be separated? → A: Two separate functions: `render_preview(blueprint)` returns formatted output for terminal display (Rich formatting), `render_for_llm(blueprint)` returns plain text string ready for LLM input.
- Q: How should rendering of specific instructions work? → A: All variants must be supported: (A) `render_instruction(blueprint, instruction_id, step_id=None)` - render single instruction by ID, optionally in step context, (B) `render_instruction(blueprint, step_id)` - render all instructions for a step, (C) `blueprint.render_instruction(instruction_id)` - method on blueprint object.
- Q: What should be done with User Story 3 (Execute Reusable Instruction Pipelines) and related code? → A: Completely remove US3 from specification, remove `run_pipeline`/`PipelineExecutor` functionality. Library focuses solely on context construction (loading blueprints, rendering) - execution is handled by external agent frameworks.
- Q: What should the minimal usage example look like in documentation? → A: One blueprint.yaml file + 3 lines of Python code: `blueprint = load_blueprint("my_blueprint")`, `render_preview(blueprint)`, `text = render_for_llm(blueprint)`. All complexity hidden under the hood.

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.

  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Blueprint Hierarchical Contexts (Priority: P1)

Prompt/system designers define multi-level context blueprints that combine prompts, reusable instruction blocks, data placeholders, and memory slots without editing Python code.

**Why this priority**: This unlocks the core value proposition—representing the entire conversational context (prompt + instructions + data + memory) as one managed artifact that can be rendered for LLM input.

**Independent Test**: Starting from an empty workspace, a designer can author a blueprint with five hierarchical steps (including nested instructions for step 3) and render the composed context for a sample data item using minimal Python code: `blueprint = load_blueprint("my_blueprint")`, `text = render_for_llm(blueprint)`.

**Architecture Impact**: Introduces `ContextBlueprint` entity (domain) and `BlueprintBuilder` use case with adapters for file I/O. Enforces SRP by keeping blueprint assembly separate from rendering; dependency inversion ensures builders depend on interfaces for instruction/data retrieval. `ContextPreviewer` and rendering functions must call data/memory slots exclusively via the `ContextMaterializer` abstraction so adapter registries stay encapsulated.

**Quality Signals**: Unit tests for blueprint validation rules, integration test that assembles and renders a sample 5-step blueprint, docs_site guide "Context blueprint authoring", `# AICODE-NOTE` capturing blueprint schema rationale.

**Acceptance Scenarios**:

1. **Given** a designer provides prompt text, global instructions, and step definitions referencing child instruction files, **When** they save the blueprint, **Then** the library stores a structured representation that preserves hierarchy and references.
2. **Given** the blueprint exists, **When** the designer requests a preview for sample data, **Then** the library renders a merged context showing where each instruction/data/memory element will appear.

---

### User Story 2 - Plug Data & Memory Sources (Priority: P2)

Platform integrators connect arbitrary data streams and memory providers (files, APIs, vector stores, etc.) to the blueprint without hardcoding implementations.

**Why this priority**: Context is incomplete without live data/memory; pluggable connectors keep the library agnostic to storage choices.

**Independent Test**: With the same blueprint, swap in two different data providers (CSV vs. API) and a mock memory store to prove contexts can be rendered without code changes.

**Architecture Impact**: Defines `DataSourceAdapter` and `MemoryProvider` interfaces plus adapter registry. Introduces a dedicated `ContextMaterializer` module in the use-case layer that orchestrates registry lookups for rendering flows so `ContextPreviewer` and rendering functions stay focused on composition and traversal. Uses DIP so use cases depend on abstractions; open/closed principle ensures new adapters register without modifying core logic. Instruction providers must declare supported `InstructionFallbackPolicy` modes (`error`, `warn`, `noop`) so rendering can degrade predictably without editing core modules.

**Quality Signals**: Contract tests for adapter interface compliance, integration test that feeds mock data/memory to render contexts, docs_site section "Registering connectors", `# AICODE-NOTE` describing adapter lifecycle.

**Acceptance Scenarios**:

1. **Given** an adapter implementing the required interface, **When** it is registered under a slot name, **Then** the blueprint can request data for that slot during rendering without knowing transport details.
2. **Given** a memory provider fails, **When** the context is rendered, **Then** the library emits a structured error describing the missing dependency instead of crashing.

---

[Add more user stories as needed, each with an assigned priority]

### Edge Cases

- Missing instruction asset: blueprint loader raises `BlueprintValidationError` (fatal) with descriptive message and suggested file path when required assets are missing; optional assets with fallback policy return structured warnings in response objects.
- Instruction provider fallback: when a configured provider cannot return content, the materializer applies the blueprint's fallback policy (`error`, `warn`, `noop`). Policy `error` raises exception; `warn`/`noop` inject placeholders and return structured fallback events in response objects, logging degradation for audit.
- Circular instruction references: blueprint validator raises `BlueprintValidationError` (fatal) rejecting graphs with cycles and highlights offending nodes.
- Extremely large data payloads: adapters stream or chunk data so context rendering can enforce size budgets per step. Exceeding limits raises `ContextSizeExceededError` (fatal) or returns structured warnings depending on configuration.
- Memory provider unavailable: materializer raises `AdapterUnavailableError` (fatal) or returns structured failure summary in response object depending on fallback policy.
- Readability safeguards: Preview helpers return structured warnings (non-fatal) highlighting steps exceeding recommended text length so designers can refactor.

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: The library MUST let users define a context blueprint composed of prompt text, instruction blocks, data slots, and memory slots in a single schema.
- **FR-002**: The blueprint engine MUST support hierarchical step structures, including nested instructions and repeating steps for item collections.
- **FR-003**: The system MUST expose pluggable interfaces for data sources and memory providers so integrators can register custom adapters without modifying core modules, and rendering use cases must interact with those adapters only through the `ContextMaterializer` abstraction starting in US1.
- **FR-004**: The library MUST resolve instruction references at load/render time (e.g., loading `3_step_instruction`), provide transparent caching to avoid redundant file reads, and enforce `InstructionFallbackPolicy` semantics (`error`, `warn`, `noop`) so alternate instruction providers can swap without modifying core modules. Instruction assets in multiple formats (Markdown, JSON, YAML, plain-text) MUST be auto-detected and converted to JSON as the canonical format during ingestion.
- **FR-005**: The library MUST provide a minimal API: `load_blueprint()` supporting three variants - (A) auto-discovery by name `load_blueprint("my_blueprint")`, (B) explicit file path `load_blueprint("path/to/blueprint.yaml")`, (C) with optional settings `load_blueprint("my_blueprint", settings=...)`. All dependencies (instructions, adapters) MUST be resolved automatically under the hood.
- **FR-006**: The library MUST provide separate rendering functions: `render_preview(blueprint)` for formatted terminal output (Rich formatting) and `render_for_llm(blueprint)` for plain text string ready for LLM input.
- **FR-007**: The library MUST support multiple ways to render specific instructions: (A) `render_instruction(blueprint, instruction_id, step_id=None)` - render single instruction by ID, optionally in step context, (B) `render_instruction(blueprint, step_id)` - render all instructions for a step, (C) `blueprint.render_instruction(instruction_id)` - method on blueprint object.
- **FR-008**: The library MUST render a preview of the fully assembled context for any blueprint + sample data combination, highlighting unresolved placeholders.
- **FR-009**: Validation MUST detect circular references, missing assets, or slot mismatches before rendering. Fatal errors (e.g., circular references, missing required assets) raise domain-specific exceptions (e.g., `BlueprintValidationError`); non-fatal warnings (e.g., optional asset fallbacks, size limit warnings) are returned as structured error dicts in response objects.
- **FR-010**: Configuration MUST allow per-step context size limits and warn when rendered text exceeds those limits.

### Key Entities *(include if feature involves data)*

- **ContextBlueprint**: Domain object describing prompt, global instructions, steps, and references to data/memory slots with hierarchy metadata.
- **InstructionNode**: Represents an instruction asset (file, string) in multiple formats (Markdown, JSON, YAML, plain-text) with format auto-detection, plus metadata (version, locale, caching policy) and parent/child relations. All formats convert to JSON internally as the canonical representation.
- **DataSlot**: Named contract describing the shape and validation rules for inbound data a blueprint consumes.
- **MemorySlot**: Descriptor for recalling prior conversation or long-term facts, referencing a provider capability (e.g., vector search, key-value recall).
- **DataSourceAdapter / MemoryProvider**: Interfaces plus concrete adapters responsible for fetching data/memory values when requested.
- **ContextMaterializer**: Dedicated registry-style service that resolves data and memory slot requests by coordinating adapter lookups/caching; shared by `ContextPreviewer` and rendering functions so those use cases remain focused on blueprint traversal rather than adapter management.

### Architecture & Quality Constraints *(from Constitution)*

- **AQ-001**: Keep `ContextBlueprint`, `InstructionNode`, and slots in the domain layer; use cases (`BlueprintBuilder`, rendering functions) depend only on interfaces (`InstructionStore`, `DataSourceAdapter`), while adapters handle filesystem/API concerns.
- **AQ-002**: Apply SRP by separating blueprint authoring, validation, and rendering into distinct classes; document any intentional coupling via `# AICODE-NOTE`.
- **AQ-003**: Provide unit tests for schema validation, adapter contracts, and rendering logic; integration tests covering multi-step blueprint rendering; contract tests for adapter registration/resolution; all run via `pytest` in CI.
- **AQ-004**: Update docs_site with blueprint schema reference, adapter integration guide, and rendering walkthrough; ensure spec, plan, and inline docstrings stay synchronized; resolve any `# AICODE-ASK` prompts before merge. Provide comprehensive examples in repository root `examples/` directory organized by user story (us1-blueprints/, us2-adapters/) plus `complete/` for end-to-end scenarios, with each example including README, blueprint YAML, sample data files, and runnable Python scripts demonstrating the feature. Examples MUST demonstrate minimal API usage (3 lines of Python code maximum).
- **AQ-005**: Enforce readability by limiting public functions to <100 logical lines, using descriptive names (e.g., `render_context_preview`), and deleting dead experimental code after each milestone.
- **AICODE-NOTE**: We satisfy AQ-005 through coding guidelines and reviews rather than bespoke tooling. Black (line length 100) and isort remain the only automated formatters for this feature.

### Assumptions

- Instruction assets support multiple formats (Markdown, JSON, YAML, plain-text) with format auto-detection. JSON is the canonical format internally; all formats convert to JSON during ingestion/processing. Additional formats can register as adapters later.
- Agents and agent frameworks handle execution externally; this library focuses solely on context construction (loading blueprints, rendering text for LLM input). The library is designed to be compatible with any agent framework accessible via Python.
- Data payload sizes are expected to fit within current LLM token constraints; enforcement happens via configurable limits rather than dynamic truncation.
- Performance optimization will be driven by profiling during development rather than explicit latency/throughput targets; size budgets (per-step context limits) serve as the primary performance constraint mechanism.
- Library usage should be minimal: one blueprint.yaml file + 3 lines of Python code for basic usage. All complexity (instruction loading, adapter resolution, caching) is hidden under the hood.

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: Designers can create a 5-step hierarchical blueprint (with nested instructions) entirely through YAML files without editing Python code.
- **SC-002**: Users can load and render a blueprint with minimal Python code: `blueprint = load_blueprint("my_blueprint")`, `render_preview(blueprint)`, `text = render_for_llm(blueprint)` - all in 3 lines.
- **SC-003**: Integrators can swap data/memory adapters and rerender contexts with <5 minutes of configuration, proving hardcoded dependencies are eliminated.
- **SC-004**: Preview rendering flags >95% of validation issues (missing assets, cycles, oversize contexts) before rendering.
- **SC-005**: All related pytest suites (unit, integration, contract) pass locally and in CI with evidence linked in the PR.
- **SC-006**: Relevant docs_site pages, specs, and inline comments are updated and reviewed alongside the code change.
- **SC-007**: Examples directory at repository root (`examples/`) contains working demonstrations organized by user story (us1-blueprints/, us2-adapters/) plus `complete/` for end-to-end scenarios, with each example including README documentation, blueprint YAML files, sample data, and runnable Python scripts that demonstrate minimal API usage (3 lines maximum for basic usage).
- **SC-008**: Performance instrumentation (`MaterializerStats`, instruction warm-up) and SDK error mapping (`describe_error`, `preview_blueprint_safe`) surface actionable diagnostics for the quickstart scenario, evidenced by `tests/integration/test_performance.py` and `tests/integration/test_quickstart_validation.py`.
- **SC-009**: Swapping instruction providers (filesystem ↔ remote) triggers at least one `warn` fallback path captured in preview/rendering responses, with contract + integration tests proving the swap requires no core module modifications.
