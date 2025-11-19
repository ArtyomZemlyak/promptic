# Tasks: Context Engineering Library

**Input**: Design documents from `/specs/001-context-engine/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are MANDATORY under the `promptic Constitution`. Write the listed contract, integration, and unit tests before implementation and ensure they fail first.

**Organization**: Tasks are grouped by user story to enable independent implementation/testing while keeping Clean Architecture layers isolated.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Task can run in parallel (different files, no unmet dependencies)
- **[Story]**: User story tag (US1, US2, US3, …) only for user-story phases
- Include exact file paths in every description

**Scope Reminder**: All tasks operate within the Python SDK surface only—no CLI, HTTP endpoints, or long-lived services. Black (line length 100) remains the only line-length enforcement; readability limits are handled via code review guidance.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize repository plumbing, settings, and scaffolding required by all stories.

- [X] T001 Create `pyproject.toml` and configure poetry/pip settings for Python 3.11 with `pydantic>=2`, `pydantic-settings`, `rich`, `jinja2`, `orjson`, `pytest`, `pytest-asyncio`, `hypothesis` in project root.
- [X] T002 Initialize package skeleton `src/promptic/__init__.py` and subpackages (`blueprints`, `instructions`, `pipeline`, `adapters`, `context`, `settings`, `sdk`).
- [X] T003 Configure formatting and linting (`black`, `isort`, `mypy`) plus `pre-commit` hooks in `.pre-commit-config.yaml`.
- [X] T004 [P] Add `ContextEngineSettings` using `pydantic-settings` in `src/promptic/settings/base.py` with filesystem roots, adapter registry config, and size budgets.
- [X] T005 [P] Scaffold SDK façade module `src/promptic/sdk/api.py` with placeholder functions for blueprint workflows (load_blueprint, render_preview, render_for_llm, render_instruction).
- [X] T006 Add base test layout (`tests/unit`, `tests/integration`, `tests/contract`) and configure `pytest.ini` with markers (`unit`, `integration`, `contract`).
- [X] T007 Create docs directory `docs_site/context-engineering/` with initial stubs (`blueprint-guide.md`, `adapter-guide.md`, `execution-recipes.md`).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core domain models, adapters infrastructure, and logging needed before any story-specific work.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T008 Define domain models from data-model.md in `src/promptic/blueprints/models.py` (ContextBlueprint, BlueprintStep, InstructionNode, InstructionNodeRef, InstructionFallbackPolicy, InstructionFallbackConfig, DataSlot, MemorySlot, AdapterRegistration) with Pydantic validation.
- [X] T009 Implement instruction storage interfaces (`InstructionStore`, `InstructionResolver`) and filesystem-backed implementation with multi-format support (Markdown, JSON, YAML, plain-text) and auto-detection in `src/promptic/instructions/store.py`, converting all formats to JSON as canonical format.
- [X] T010 Implement adapter registry infrastructure (`BaseAdapter`, `BaseMemoryProvider`, registration API) in `src/promptic/adapters/registry.py` with plugin loading hooks.
- [X] T010a Implement dedicated `ContextMaterializer` use case in `src/promptic/pipeline/context_materializer.py` to broker adapter registry lookups, caching, and structured errors for rendering flows.
- [X] T011 Build optional event logging utility for instruction/data/memory lookups during rendering, with structured warnings/fallback events returned in response objects in `src/promptic/context/logging.py`.
- [X] T012 Implement blueprint serializer/deserializer (YAML + JSON Schema export) in `src/promptic/blueprints/serialization.py`.
- [X] T013 [P] Create validation services (`BlueprintValidator`) handling cycles, asset existence, and size budgets in `src/promptic/pipeline/validation.py`.
- [X] T014 [P] Add shared error types (BlueprintValidationError, AdapterNotFoundError, ContextSizeExceededError, AdapterUnavailableError) and structured error result objects in `src/promptic/context/errors.py` implementing hybrid error handling (exceptions for fatal, structured dicts for warnings).
- [X] T015 [P] Write foundational unit tests for models/registry/logging in `tests/unit/blueprints/test_models.py`, `tests/unit/adapters/test_registry.py`, `tests/unit/context/test_logging.py`.
- [X] T015a [P] Add unit tests for `ContextMaterializer` cache/error paths in `tests/unit/pipeline/test_context_materializer.py`.
- [X] T016 Document foundational architecture in `docs_site/context-engineering/blueprint-guide.md` and `adapter-guide.md` sections describing domain layering, registries, and the `ContextMaterializer` role.

**Checkpoint**: Domain + infrastructure ready; user stories can proceed in parallel.

---

## Phase 3: User Story 1 - Blueprint Hierarchical Contexts (Priority: P1) 🎯 MVP

**Goal**: Designers can author hierarchical blueprints (prompt + instruction blocks + slots) and render contexts for LLM input using minimal Python code (3 lines).

**Independent Test**: Using the Python SDK + YAML/Markdown assets only, author a 5-step blueprint with nested instructions and render it with sample data using minimal API: `blueprint = load_blueprint("my_blueprint")`, `render_preview(blueprint)`, `text = render_for_llm(blueprint)`. Preview output shows every referenced instruction and warns on missing assets.

### Tests for User Story 1 (MANDATORY) ⚠️

- [X] T017 [P] [US1] Contract test verifying the SDK blueprint preview API (`promptic.sdk.blueprints.preview_blueprint`) in `tests/contract/test_blueprint_preview_sdk.py`, stubbing adapters behind `ContextMaterializer` to prove previews never access registries directly.
- [X] T018 [P] [US1] Integration test running the preview workflow end-to-end with sample assets via SDK helpers in `tests/integration/test_blueprint_preview_sdk.py`, injecting a fake `ContextMaterializer` and asserting all slot lookups flow through it.
- [X] T019 [US1] [P] Unit tests for blueprint builder + serializer edge cases in `tests/unit/blueprints/test_builder.py`.

### Implementation for User Story 1

- [X] T020 [US1] Implement `BlueprintBuilder` service in `src/promptic/pipeline/builder.py` handling YAML ingestion and schema validation.
- [X] T021 [US1] Implement `ContextPreviewer` in `src/promptic/pipeline/previewer.py` merging prompt + instructions + placeholder data while resolving every data/memory slot exclusively via the injected `ContextMaterializer` interface (no registry access).
- [X] T022 [P] [US1] Expose blueprint builder/previewer via SDK façade functions in `src/promptic/sdk/blueprints.py`, ensuring the façades receive a `ContextMaterializer` dependency they pass through untouched.
- [X] T023 [P] [US1] Add filesystem instruction discovery + caching (LRU) in `src/promptic/instructions/cache.py`.
- [X] T024 [US1] Generate blueprint JSON Schema export helper surfaced via SDK (e.g., `src/promptic/sdk/blueprints.py`).
- [X] T025 [US1] Implement preview formatting with `rich` highlighting unresolved placeholders in `src/promptic/context/rendering.py`.
- [X] T025a [US1] Implement minimal API function `load_blueprint()` in `src/promptic/sdk/api.py` supporting three variants: (A) auto-discovery by name `load_blueprint("my_blueprint")`, (B) explicit file path `load_blueprint("path/to/blueprint.yaml")`, (C) with optional settings `load_blueprint("my_blueprint", settings=...)`. All dependencies (instructions, adapters) must be resolved automatically under the hood.
- [X] T025b [US1] Implement `render_preview(blueprint)` function in `src/promptic/sdk/api.py` returning formatted output for terminal display (Rich formatting).
- [X] T025c [US1] Implement `render_for_llm(blueprint)` function in `src/promptic/sdk/api.py` returning plain text string ready for LLM input.
- [X] T025d [US1] Implement `render_instruction()` function in `src/promptic/sdk/api.py` supporting all variants: (A) `render_instruction(blueprint, instruction_id, step_id=None)`, (B) `render_instruction(blueprint, step_id)`, (C) add `blueprint.render_instruction(instruction_id)` method to ContextBlueprint model in `src/promptic/blueprints/models.py`.
- [X] T025e [US1] Add integration test for minimal API usage in `tests/integration/test_minimal_api.py` verifying 3-line usage works: `blueprint = load_blueprint("my_blueprint")`, `render_preview(blueprint)`, `text = render_for_llm(blueprint)`.
- [X] T026 [US1] Write docs/tutorial for blueprint authoring + SDK usage in `docs_site/context-engineering/blueprint-guide.md`.
- [X] T027 [US1] Add logging instrumentation (`# AICODE-NOTE` for caching strategy) and ensure preview helpers log used instruction IDs.
- [X] T027a [US1] Create examples directory structure `examples/us1-blueprints/` with README.md, sample blueprint YAML, instruction files, and runnable Python script demonstrating minimal API usage (3 lines max) in `examples/us1-blueprints/run_preview.py`.

**Checkpoint**: Blueprint authoring + preview experience complete and testable independently.

---

## Phase 4: User Story 2 - Plug Data & Memory Sources (Priority: P2)

**Goal**: Integrators can register arbitrary data/memory adapters and swap them without code changes; context rendering resolves slots via adapters.

**Independent Test**: Register CSV and HTTP data adapters plus a mock memory provider, render blueprint twice (each adapter) and run integration test verifying adapter swap works without touching blueprint code.

### Tests for User Story 2 (MANDATORY) ⚠️

- [X] T028 [P] [US2] Contract test for adapter registration SDK flows (registry APIs) in `tests/contract/test_adapter_registry.py`.
- [X] T029 [P] [US2] Integration test that swaps CSV vs HTTP adapters and mock memory provider during rendering in `tests/integration/test_adapter_swaps.py`, verifying rendering paths interact with adapters only through `ContextMaterializer`.
- [X] T030 [US2] Unit tests for adapter base classes + registry errors in `tests/unit/adapters/test_base.py`.

### Implementation for User Story 2

- [X] T031 [US2] Implement adapter registration SDK utilities in `src/promptic/sdk/adapters.py` exposing register/list helpers.
- [X] T032 [US2] Build data adapter base classes plus sample adapters (CSV loader, HTTP fetcher) in `src/promptic/adapters/data/csv_loader.py` and `src/promptic/adapters/data/http_fetcher.py`.
- [X] T033 [US2] Build memory provider base classes plus sample vector/memory adapters in `src/promptic/adapters/memory/vector_store.py`.
- [X] T034 [US2] Expand `ContextMaterializer` orchestration (caching, retries, structured errors) so rendering functions delegate every slot lookup to it while keeping the adapter registry encapsulated in `src/promptic/pipeline/context_materializer.py`.
- [X] T035 [US2] Implement error handling + retries for adapter failures in `src/promptic/context/errors.py`.
- [X] T036 [US2] Document adapter lifecycle + configuration (Pydantic settings examples) in `docs_site/context-engineering/adapter-guide.md`.
- [X] T037 [US2] Update quickstart (`quickstart.md`) with examples showing adapter registration + swapping.
- [X] T037a [US2] Create examples directory `examples/us2-adapters/` with README.md, blueprint YAML, sample data files, and runnable Python script demonstrating adapter registration and swapping in `examples/us2-adapters/swap_adapters.py`.

**Checkpoint**: Blueprint rendering honors pluggable adapters with tests proving swap-ability.

---

## Phase 5: Instruction Provider Fallbacks (Scope: CHK016)

**Goal**: Define and enforce `InstructionFallbackPolicy` (`error`, `warn`, `noop`) so instruction providers can swap without editing core modules while emitting structured diagnostics, placeholders, and warnings.

**Independent Test**: Swap filesystem and HTTP instruction providers, force an outage, and prove rendering continues per fallback configuration, recording `fallback_events` in response objects without modifying blueprint or core classes.

### Tests for Instruction Fallbacks (MANDATORY) ⚠️

- [X] T055 [P] Add contract coverage for fallback diagnostics by extending `tests/contract/test_blueprint_preview_sdk.py` with scenarios that assert `fallback_events` and "no core edits" guidance in responses.
- [X] T056 [P] Extend `tests/integration/test_adapter_swaps.py` (or add `test_instruction_fallbacks.py`) to simulate warn/noop policies across filesystem + HTTP providers, verifying placeholders and fallback events are returned in response objects.
- [X] T057 Add unit tests for materializer fallback helpers in `tests/unit/pipeline/test_context_materializer.py`, ensuring placeholders, retries, and warnings follow the configured policy.

### Implementation for Instruction Fallbacks

- [X] T058 Update blueprint/data models and materializer orchestration (`src/promptic/blueprints/models.py`, `src/promptic/pipeline/context_materializer.py`) to accept `InstructionFallbackConfig`, wire placeholder rendering, and return fallback events in response objects.
- [X] T059 Emit fallback diagnostics in SDK layers by enhancing `src/promptic/context/logging.py` and `src/promptic/sdk/api.py` so rendering helpers expose `fallback_events` alongside existing outputs.
- [X] T060 Refresh developer guidance by updating `src/promptic/sdk/blueprints.py`, `specs/001-context-engine/quickstart.md`, and `docs_site/context-engineering/adapter-guide.md` with examples showing how to configure fallback policies and interpret warnings.

**Checkpoint**: Fallback semantics documented, enforced via tests, and observable through SDK response objects so CHK016 is satisfied.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Repo-wide improvements, hardening, and evidence gathering.

- [X] T048 [P] Finalize documentation updates (docs_site pages, spec/plan adjustments) and close any outstanding `# AICODE-ASK` items.
- [X] T049 Harden error messages + exception mapping across blueprint/adapters/pipeline modules (`src/promptic/context/errors.py`).
- [X] T050 [P] Optimize hot paths (instruction caching, adapter batching) and add benchmarks in `tests/integration/test_performance.py`.
- [X] T051 Expand SDK ergonomics (helper functions, rich error types) in `src/promptic/sdk/api.py`.
- [X] T052 [P] Add additional unit tests for uncovered branches reported by coverage in `tests/unit/`.
- [X] T053 Run `quickstart.md` end-to-end validation and capture output snapshots in `docs_site/context-engineering/`.
- [X] T054 Execute `pytest -m "unit or integration or contract"` and `pre-commit run --all-files`; attach evidence to PR.
- [X] T054a Create comprehensive end-to-end examples directory `examples/complete/` with README.md, full research flow blueprint, instruction files, data files, and complete runnable script demonstrating all library functionality in `examples/complete/end_to_end.py`.

---

## Dependencies & Execution Order

### Phase Dependencies
- Setup must complete before Foundational work.
- Foundational must complete before any user story tasks.
- US1 (P1) unlocks blueprint authoring and rendering (MVP) with minimal API.
- US2 (P2) depends on Foundational + relevant US1 assets but remains independently testable (adapters can be mocked).
- Instruction Fallbacks can proceed in parallel with US2 once US1 is complete.
- Polish runs after desired user stories complete.

### User Story Dependencies
- US1 → no prior stories. Delivers minimal API: `load_blueprint()`, `render_preview()`, `render_for_llm()`, `render_instruction()`.
- US2 → requires adapter registry + blueprint rendering (US1 artifacts) to plug data/memory but does not require execution.
- Instruction Fallbacks → requires US1 rendering infrastructure and can proceed in parallel with US2.

### Within Each User Story
- Tests written first (contract → integration → unit as applicable).
  - Models/components before public SDK exposure.
- Logging/instrumentation added before docs updates.
- Each story concludes with docs + logging updates so they stay independently demonstrable.

### Parallel Opportunities
- Setup: T004 & T005 can run in parallel after T001–T003.
- Foundational: T013–T015 can proceed concurrently once T008–T012 exist.
  - US1: Test tasks (T017–T019) can run in parallel; SDK façade and caching tasks (T022–T023) parallel after builder (T020); minimal API tasks (T025a–T025d) can run in parallel after T020–T021.
- US2: Adapter samples (T032–T033) parallelizable after registry enhancements (T010).
- Instruction Fallbacks: Test tasks (T055–T057) can run in parallel; implementation tasks (T058–T060) can proceed concurrently.

---

## Parallel Example: User Story 1

```bash
# Run tests together (after scaffolding):
pytest tests/contract/test_blueprint_preview_sdk.py
pytest tests/integration/test_blueprint_preview_sdk.py
pytest tests/unit/blueprints/test_builder.py
pytest tests/integration/test_minimal_api.py

# Parallel implementation tracks:
Track A: T020 (builder) → T021 (previewer)
Track B: T022 (SDK façade) + T023 (instruction cache) once builder interfaces fixed
Track C: T024 (schema export) + T025 (rendering) + T026 docs
Track D: T025a (load_blueprint) + T025b (render_preview) + T025c (render_for_llm) + T025d (render_instruction) once T020–T021 complete
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Complete Setup + Foundational.
2. Build blueprint authoring + preview (US1) with tests/docs.
3. Validate blueprint flow end-to-end as MVP.

### Incremental Delivery
1. Deliver US1 (blueprints + rendering with minimal API) - MVP.
2. Add US2 (adapters) showing swap-ability.
3. Add Instruction Fallbacks for graceful degradation.
4. Each increment ends with tests/docs so it can ship independently.

### Parallel Team Strategy
1. Team A handles Setup/Foundational.
2. Once ready:
   - Team A → US1 (minimal API + rendering)
   - Team B → US2 (adapters) in parallel once US1 rendering is stable
   - Team C → Instruction Fallbacks in parallel with US2
3. Use contract/integration tests as shared gates to keep modules aligned.

---

## Notes
- Respect Constitution checklist (SOLID, docs, readability, tests, pre-commit).
- Every public SDK addition needs doc updates and `# AICODE-NOTE` comments for key trade-offs.
- Keep tasks independent; stop after each story to validate tests + docs before moving forward.
- Examples directory structure: `examples/us1-blueprints/`, `examples/us2-adapters/`, `examples/complete/` each with README, blueprint YAML, sample data, and runnable Python scripts demonstrating minimal API usage (3 lines max for basic usage).
