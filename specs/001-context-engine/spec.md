# Feature Specification: Context Engineering Library

**Feature Branch**: `001-context-engine`  
**Created**: 2025-11-17  
**Status**: Draft  
**Input**: User description: "Я хочу сделать библиотеку на python, которая будет позволять работать с промптами, контекстом и памятью в унифицированном режиме. Идея в том, что контекст = промпт + инструкции + данные + память и тд, и получается, если мы делаем библиотеку для промптов, то это все нужно учитывать вместе. Тут еще есть поле для размышлений, как и что лучше отделять, так как данные и память могут абсолютно любыми способами получаться, и лучше это не захардкоживать. А вот инструкции и промпт точно можно, плюс места под данные и память (так называемый context engineering). И самая главная идея - все части контекста могут быть иерархическими и выполняться агентом иерархически. К примеру, у нас есть пайплайн работы агента в 5 шагов, но 3 шаг состоит из списка действий для N элементов из данных - и чтобы не передавать список действий в промпте каждый раз, то можно сделать к примеру файл 3_step_instruction - и вот к этому файлу будет обращаться агент при каждой обработке элемента в 3 шаге. То есть, мы не захардкодиваем все шаги и инструкции в коде, а предлагаем агенту инструкции как что делать, но итоговый пайплайн действий выбирает он сам."
> This specification MUST satisfy the `promptic Constitution`: clean architecture layering, SOLID responsibilities, mandatory tests, documentation updates, and readability.

**Scope Clarification**: This feature delivers a pure Python library meant to be imported directly into host projects. No CLI utilities, HTTP/REST services, or persistent servers are included in this release; all interactions happen through the SDK.

## Clarifications

### Session 2025-11-17

- Q: Which entrypoints are in scope (library vs CLI vs HTTP)? → A: Importable Python library only; no CLI or HTTP surfaces.

### Session 2025-11-18

- Q: Should `ContextMaterializer` be treated as a new use case or folded into existing preview/executor services? → A: Keep it as a dedicated registry-style module documented in the spec so layering remains explicit.
- Q: Should T020/T021 rely on ContextMaterializer from day one or pull T034 earlier? → A: Keep T034 in US2, but inject the existing ContextMaterializer interface into T020/T021 immediately and add tests proving preview/executor flows never touch adapters directly.

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

**Why this priority**: This unlocks the core value proposition—representing the entire conversational context (prompt + instructions + data + memory) as one managed artifact.

**Independent Test**: Starting from an empty workspace, a designer can author a blueprint with five pipeline steps (including nested instructions for step 3) and preview the composed context for a sample data item.

**Architecture Impact**: Introduces `ContextBlueprint` entity (domain) and `BlueprintBuilder` use case with adapters for file I/O. Enforces SRP by keeping blueprint assembly separate from rendering; dependency inversion ensures builders depend on interfaces for instruction/data retrieval. `ContextPreviewer` and any early executor helpers must call data/memory slots exclusively via the `ContextMaterializer` abstraction so adapter registries stay encapsulated even before T034 wires additional flows.

**Quality Signals**: Unit tests for blueprint validation rules, integration test that assembles a sample 5-step pipeline, docs_site guide “Context blueprint authoring”, `# AICODE-NOTE` capturing blueprint schema rationale.

**Acceptance Scenarios**:

1. **Given** a designer provides prompt text, global instructions, and step definitions referencing child instruction files, **When** they save the blueprint, **Then** the library stores a structured representation that preserves hierarchy and references.
2. **Given** the blueprint exists, **When** the designer requests a preview for sample data, **Then** the library renders a merged context showing where each instruction/data/memory element will appear.

---

### User Story 2 - Plug Data & Memory Sources (Priority: P2)

Platform integrators connect arbitrary data streams and memory providers (files, APIs, vector stores, etc.) to the blueprint without hardcoding implementations.

**Why this priority**: Context is incomplete without live data/memory; pluggable connectors keep the library agnostic to storage choices.

**Independent Test**: With the same blueprint, swap in two different data providers (CSV vs. API) and a mock memory store to prove the pipeline still executes without code changes.

**Architecture Impact**: Defines `DataSourceAdapter` and `MemoryProvider` interfaces plus adapter registry. Introduces a dedicated `ContextMaterializer` module in the use-case layer that orchestrates registry lookups for preview/execution flows so `ContextPreviewer` and `PipelineExecutor` stay focused on composition and traversal. Uses DIP so use cases depend on abstractions; open/closed principle ensures new adapters register without modifying core logic.

**Quality Signals**: Contract tests for adapter interface compliance, integration test that feeds mock data/memory to render contexts, docs_site section “Registering connectors”, `# AICODE-NOTE` describing adapter lifecycle.

**Acceptance Scenarios**:

1. **Given** an adapter implementing the required interface, **When** it is registered under a slot name, **Then** the blueprint can request data for that slot during rendering without knowing transport details.
2. **Given** a memory provider fails, **When** the pipeline executes, **Then** the library emits a structured error describing the missing dependency instead of crashing.

---

### User Story 3 - Execute Reusable Instruction Pipelines (Priority: P3)

Automation engineers orchestrate agent workflows where each pipeline step can trigger nested instruction assets (e.g., per-element sub-tasks) and the agent decides how to traverse them.

**Why this priority**: Demonstrates the hierarchical execution model that differentiates the library from plain prompt templates.

**Independent Test**: Configure a 5-step pipeline where step 3 loops through N items, pulls `3_step_instruction` for each, and the agent execution trace shows instructions resolved per item.

**Architecture Impact**: Adds `PipelineExecutor` use case and `InstructionResolver` adapter. Liskov substitution ensures custom executors can extend behavior, while Interface Segregation keeps instruction lookups separate from execution control.

**Quality Signals**: Scenario test simulating the 5-step pipeline with mock agent, logging to verify hierarchical execution order; docs_site recipe “Nested instruction pipelines”; `# AICODE-NOTE` capturing executor design decisions.

**Acceptance Scenarios**:

1. **Given** a pipeline with nested instruction references, **When** the executor runs against sample data, **Then** it fetches the correct instruction asset for each loop iteration and records which assets were used.
2. **Given** pipeline steps include optional branches, **When** the agent chooses a subset of steps, **Then** the executor still resolves required instructions and marks skipped steps as pending for auditability.

---

[Add more user stories as needed, each with an assigned priority]

### Edge Cases

- Missing instruction asset: executor must fail fast with a descriptive error and suggest which file path is expected.
- Circular instruction references: blueprint validator rejects graphs with cycles and highlights offending nodes.
- Extremely large data payloads: adapters stream or chunk data so context rendering can enforce size budgets per step.
- Memory provider unavailable mid-run: executor retries once, then records the failure summary for the agent to decide fallback.
- Readability safeguards: Preview helpers highlight steps exceeding recommended text length so designers can refactor.

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: The library MUST let users define a context blueprint composed of prompt text, instruction blocks, data slots, and memory slots in a single schema.
- **FR-002**: The blueprint engine MUST support hierarchical step structures, including nested instructions and repeating steps for item collections.
- **FR-003**: The system MUST expose pluggable interfaces for data sources and memory providers so integrators can register custom adapters without modifying core modules, and preview/execution use cases must interact with those adapters only through the `ContextMaterializer` abstraction starting in US1.
- **FR-004**: The executor MUST resolve instruction references at runtime (e.g., loading `3_step_instruction`) and provide transparent caching to avoid redundant file reads within a run.
- **FR-005**: The library MUST render a preview of the fully assembled context for any blueprint + sample data combination, highlighting unresolved placeholders.
- **FR-006**: Validation MUST detect circular references, missing assets, or slot mismatches before execution and return actionable error messages.
- **FR-007**: The system MUST log every instruction/data/memory asset accessed per run so agents can audit which guidance influenced each output.
- **FR-008**: Configuration MUST allow per-step context size limits and warn when rendered text exceeds those limits.

### Key Entities *(include if feature involves data)*

- **ContextBlueprint**: Domain object describing prompt, global instructions, steps, and references to data/memory slots with hierarchy metadata.
- **InstructionNode**: Represents an instruction asset (file, string, template) plus metadata (version, locale, caching policy) and parent/child relations.
- **DataSlot**: Named contract describing the shape and validation rules for inbound data a blueprint consumes.
- **MemorySlot**: Descriptor for recalling prior conversation or long-term facts, referencing a provider capability (e.g., vector search, key-value recall).
- **DataSourceAdapter / MemoryProvider**: Interfaces plus concrete adapters responsible for fetching data/memory values when requested.
- **PipelineExecutor**: Application service that walks the blueprint, orchestrates step execution, and produces resolved context packages for agents.
- **ContextMaterializer**: Dedicated registry-style service that resolves data and memory slot requests by coordinating adapter lookups/caching; shared by `ContextPreviewer` and `PipelineExecutor` so those use cases remain focused on blueprint traversal rather than adapter management.

### Architecture & Quality Constraints *(from Constitution)*

- **AQ-001**: Keep `ContextBlueprint`, `InstructionNode`, and slots in the domain layer; use cases (`BlueprintBuilder`, `PipelineExecutor`) depend only on interfaces (`InstructionStore`, `DataSourceAdapter`), while adapters handle filesystem/API concerns.
- **AQ-002**: Apply SRP by separating blueprint authoring, validation, rendering, and execution into distinct classes; document any intentional coupling via `# AICODE-NOTE`.
- **AQ-003**: Provide unit tests for schema validation, adapter contracts, and execution traversal; integration tests covering a multi-step pipeline; contract tests for adapter registration/resolution; all run via `pytest` in CI.
- **AQ-004**: Update docs_site with blueprint schema reference, adapter integration guide, and execution walkthrough; ensure spec, plan, and inline docstrings stay synchronized; resolve any `# AICODE-ASK` prompts before merge.
- **AQ-005**: Enforce readability by limiting public functions to <100 logical lines, using descriptive names (e.g., `render_context_preview`), and deleting dead experimental code after each milestone.
- **AICODE-NOTE**: We satisfy AQ-005 through coding guidelines and reviews rather than bespoke tooling. Black (line length 100) and isort remain the only automated formatters for this feature.

### Assumptions

- Instruction assets are stored as Markdown/plain-text files by default; other formats can register as adapters later.
- Agents trigger pipeline execution via an external orchestrator; this feature focuses on producing contexts, not running the agent itself.
- Data payload sizes are expected to fit within current LLM token constraints; enforcement happens via configurable limits rather than dynamic truncation.

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: Designers can create a 5-step hierarchical blueprint (with nested instructions) entirely through the library API in under 10 minutes without editing Python code.
- **SC-002**: Integrators can swap data/memory adapters and rerun the sample pipeline with <5 minutes of configuration, proving hardcoded dependencies are eliminated.
- **SC-003**: Execution logs capture 100% of instruction/data/memory accesses for every run, enabling auditors to trace agent decisions.
- **SC-004**: Preview rendering flags >95% of validation issues (missing assets, cycles, oversize contexts) before runtime execution.
- **SC-005**: All related pytest suites (unit, integration, contract) pass locally and in CI with evidence linked in the PR.
- **SC-006**: Relevant docs_site pages, specs, and inline comments are updated and reviewed alongside the code change.
