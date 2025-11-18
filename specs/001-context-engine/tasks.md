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

- [X] T001 Create `pyproject.toml` and configure poetry/pip settings for Python 3.11 with `pydantic`, `pydantic-settings`, `rich`, `jinja2`, `orjson`, `pytest`, `pytest-asyncio`, `hypothesis` in project root.
- [X] T002 Initialize package skeleton `src/promptic/__init__.py` and subpackages (`blueprints`, `instructions`, `pipeline`, `adapters`, `context`, `settings`, `sdk`).
- [X] T003 Configure formatting and linting (`black`, `isort`, `mypy`) plus `pre-commit` hooks in `.pre-commit-config.yaml`.
- [X] T004 [P] Add `ContextEngineSettings` using `pydantic-settings` in `src/promptic/settings/base.py` with filesystem roots, adapter registry config, and size budgets.
- [X] T005 [P] Scaffold SDK façade module `src/promptic/sdk/api.py` with placeholder functions for blueprint and pipeline workflows.
- [X] T006 Add base test layout (`tests/unit`, `tests/integration`, `tests/contract`) and configure `pytest.ini` with markers (`unit`, `integration`, `contract`).
- [X] T007 Create docs directory `docs_site/context-engineering/` with initial stubs (`blueprint-guide.md`, `adapter-guide.md`, `execution-recipes.md`).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core domain models, adapters infrastructure, and logging needed before any story-specific work.

- [X] T008 Define domain models from data-model.md in `src/promptic/blueprints/models.py` (ContextBlueprint, BlueprintStep, InstructionNode, DataSlot, MemorySlot, AdapterRegistration, ExecutionLogEntry) with Pydantic validation.
- [X] T009 Implement instruction storage interfaces (`InstructionStore`, `InstructionResolver`) and filesystem-backed implementation in `src/promptic/instructions/store.py`.
- [X] T010 Implement adapter registry infrastructure (`BaseAdapter`, `BaseMemoryProvider`, registration API) in `src/promptic/adapters/registry.py` with plugin loading hooks.
- [X] T010a Implement dedicated `ContextMaterializer` use case in `src/promptic/pipeline/context_materializer.py` to broker adapter registry lookups, caching, and structured errors for preview/execution flows.
- [X] T011 Build event logging utility emitting JSONL entries in `src/promptic/context/logging.py`.
- [X] T012 Implement blueprint serializer/deserializer (YAML + JSON Schema export) in `src/promptic/blueprints/serialization.py`.
- [X] T013 [P] Create validation services (`BlueprintValidator`) handling cycles, asset existence, and size budgets in `src/promptic/pipeline/validation.py`.
- [X] T014 [P] Add shared error types and result objects in `src/promptic/context/errors.py`.
- [X] T015 [P] Write foundational unit tests for models/registry/logging in `tests/unit/blueprints/test_models.py`, `tests/unit/adapters/test_registry.py`, `tests/unit/context/test_logging.py`.
- [X] T015a [P] Add unit tests for `ContextMaterializer` cache/error paths in `tests/unit/pipeline/test_context_materializer.py`.
- [X] T016 Document foundational architecture in `docs_site/context-engineering/blueprint-guide.md` and `adapter-guide.md` sections describing domain layering, registries, and the `ContextMaterializer` role.

**Checkpoint**: Domain + infrastructure ready; user stories can proceed in parallel.

---

## Phase 3: User Story 1 - Blueprint Hierarchical Contexts (Priority: P1) 🎯 MVP

**Goal**: Designers can author hierarchical blueprints (prompt + instruction blocks + slots) and preview merged contexts without touching Python.

**Independent Test**: Using the Python SDK + YAML/Markdown assets only, author a 5-step blueprint with nested instructions and preview it with sample data; preview output shows every referenced instruction and warns on missing assets.

### Tests for User Story 1 (MANDATORY) ⚠️

- [ ] T017 [P] [US1] Contract test verifying the SDK blueprint preview API (`promptic.sdk.blueprints.preview_blueprint`) in `tests/contract/test_blueprint_preview_sdk.py`.
- [ ] T018 [P] [US1] Integration test running the preview workflow end-to-end with sample assets via SDK helpers in `tests/integration/test_blueprint_preview_sdk.py`.
- [ ] T019 [US1] [P] Unit tests for blueprint builder + serializer edge cases in `tests/unit/blueprints/test_builder.py`.

### Implementation for User Story 1

- [ ] T020 [US1] Implement `BlueprintBuilder` service in `src/promptic/pipeline/builder.py` handling YAML ingestion and schema validation.
- [ ] T021 [US1] Implement `ContextPreviewer` in `src/promptic/pipeline/previewer.py` merging prompt + instructions + placeholder data.
- [ ] T022 [P] [US1] Expose blueprint builder/previewer via SDK façade functions in `src/promptic/sdk/blueprints.py`.
- [ ] T023 [P] [US1] Add filesystem instruction discovery + caching (LRU) in `src/promptic/instructions/cache.py`.
- [ ] T024 [US1] Generate blueprint JSON Schema export helper surfaced via SDK (e.g., `src/promptic/sdk/blueprints.py`).
- [ ] T025 [US1] Implement preview formatting with `rich` highlighting unresolved placeholders in `src/promptic/context/rendering.py`.
- [ ] T026 [US1] Write docs/tutorial for blueprint authoring + SDK usage in `docs_site/context-engineering/blueprint-guide.md`.
- [ ] T027 [US1] Add logging instrumentation (`# AICODE-NOTE` for caching strategy) and ensure preview helpers log used instruction IDs.

**Checkpoint**: Blueprint authoring + preview experience complete and testable independently.

---

## Phase 4: User Story 2 - Plug Data & Memory Sources (Priority: P2)

**Goal**: Integrators can register arbitrary data/memory adapters and swap them without code changes; pipeline rendering/execution resolves slots via adapters.

**Independent Test**: Register CSV and HTTP data adapters plus a mock memory provider, render blueprint twice (each adapter) and run integration test verifying adapter swap works without touching blueprint code.

### Tests for User Story 2 (MANDATORY) ⚠️

- [ ] T028 [P] [US2] Contract test for adapter registration SDK flows (registry APIs) in `tests/contract/test_adapter_registry.py`.
- [ ] T029 [P] [US2] Integration test that swaps CSV vs HTTP adapters and mock memory provider during preview/execution in `tests/integration/test_adapter_swaps.py`.
- [ ] T030 [US2] Unit tests for adapter base classes + registry errors in `tests/unit/adapters/test_base.py`.

### Implementation for User Story 2

- [ ] T031 [US2] Implement adapter registration SDK utilities in `src/promptic/sdk/adapters.py` exposing register/list helpers.
- [ ] T032 [US2] Build data adapter base classes plus sample adapters (CSV loader, HTTP fetcher) in `src/promptic/adapters/data/`.
- [ ] T033 [US2] Build memory provider base classes plus sample vector/memory adapters in `src/promptic/adapters/memory/`.
- [ ] T034 [US2] Wire `ContextPreviewer` and `PipelineExecutor` to call `ContextMaterializer` for all data/memory slot resolution so only `src/promptic/pipeline/context_materializer.py` talks to the adapter registry.
- [ ] T035 [US2] Implement error handling + retries for adapter failures in `src/promptic/context/errors.py`.
- [ ] T036 [US2] Document adapter lifecycle + configuration (Pydantic settings examples) in `docs_site/context-engineering/adapter-guide.md`.
- [ ] T037 [US2] Update quickstart (`quickstart.md`) with examples showing adapter registration + swapping.

**Checkpoint**: Blueprint rendering/execution honors pluggable adapters with tests proving swap-ability.

---

## Phase 5: User Story 3 - Execute Reusable Instruction Pipelines (Priority: P3)

**Goal**: Execute full pipelines with hierarchical steps, per-item instruction fetching, and detailed execution logs so agents can trace decisions.

**Independent Test**: Run a 5-step pipeline where step 3 loops over N items and fetches `3_step_instruction` each time; execution log shows correct instruction IDs per item, and optional branches are tracked.

### Tests for User Story 3 (MANDATORY) ⚠️

- [ ] T038 [P] [US3] Contract test for the SDK pipeline execution API (`promptic.sdk.pipeline.run_pipeline`) returning `ExecutionAck` and validating payload schema in `tests/contract/test_pipeline_execute.py`.
- [ ] T039 [P] [US3] Integration scenario test running the full 5-step pipeline with mock agent hooks in `tests/integration/test_pipeline_executor.py`.
- [ ] T040 [US3] Unit tests for `PipelineExecutor` traversal + logging events in `tests/unit/pipeline/test_executor.py`.

### Implementation for User Story 3

- [ ] T041 [US3] Implement `PipelineExecutor` in `src/promptic/pipeline/executor.py` supporting sequence/loop/branch semantics and structured logging.
- [ ] T042 [US3] Add execution log writers (JSONL + SDK trace helpers) in `src/promptic/pipeline/loggers.py`.
- [ ] T043 [US3] Implement per-step policy enforcement (size budgets, optional branches) in `src/promptic/pipeline/policies.py`.
- [ ] T044 [P] [US3] Provide mock agent integration hooks allowing custom callbacks per step in `src/promptic/pipeline/hooks.py`.
- [ ] T045 [US3] Extend docs with execution recipes + troubleshooting in `docs_site/context-engineering/execution-recipes.md`.
- [ ] T046 [US3] Ensure executor emits `# AICODE-NOTE` detailing design decisions around traversal order and error boundaries.
- [ ] T047 [US3] Update quickstart to include pipeline run + trace SDK usage and sample logs.

**Checkpoint**: Hierarchical execution complete, logs/audits in place, tests prove nested instruction handling.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Repo-wide improvements, hardening, and evidence gathering.

- [ ] T048 [P] Finalize documentation updates (docs_site pages, spec/plan adjustments) and close any outstanding `# AICODE-ASK` items.
- [ ] T049 Harden error messages + exception mapping across blueprint/adapters/pipeline modules (`src/promptic/context/errors.py`).
- [ ] T050 [P] Optimize hot paths (instruction caching, adapter batching) and add benchmarks in `tests/integration/test_performance.py`.
- [ ] T051 Expand SDK ergonomics (helper functions, rich error types) in `src/promptic/sdk/api.py`.
- [ ] T052 [P] Add additional unit tests for uncovered branches reported by coverage in `tests/unit/`.
- [ ] T053 Run `quickstart.md` end-to-end validation and capture output snapshots in `docs_site/context-engineering/`.
- [ ] T054 Execute `pytest -m "unit or integration or contract"` and `pre-commit run --all-files`; attach evidence to PR.

---

## Dependencies & Execution Order

### Phase Dependencies
- Setup must complete before Foundational work.
- Foundational must complete before any user story tasks.
- US1 (P1) unlocks blueprint authoring preview (MVP).
- US2 (P2) depends on Foundational + relevant US1 assets but remains independently testable (adapters can be mocked).
- US3 (P3) depends on US1 data structures and US2 adapter registry (for execution), but once adapters exist, execution logic is independent.
- Polish runs after desired user stories complete.

### User Story Dependencies
- US1 → no prior stories.
- US2 → requires adapter registry + blueprint preview (US1 artifacts) to plug data/memory but does not require executor.
- US3 → requires blueprint definitions (US1) and adapter plumbing (US2) to execute pipelines; logic remains independent.

### Within Each User Story
- Tests written first (contract → integration → unit as applicable).
  - Models/components before public SDK exposure.
- Logging/instrumentation added before docs updates.
- Each story concludes with docs + logging updates so they stay independently demonstrable.

### Parallel Opportunities
- Setup: T004 & T005 can run in parallel after T001–T003.
- Foundational: T013–T015 can proceed concurrently once T008–T012 exist.
  - US1: Test tasks (T017–T019) can run in parallel; SDK façade and caching tasks (T022–T023) parallel after builder (T020).
- US2: Adapter samples (T032–T033) parallelizable after registry enhancements (T010).
- US3: Executor hooks (T044) can build in parallel with policies (T043) after base executor scaffolding (T041).

---

## Parallel Example: User Story 1

```bash
# Run tests together (after scaffolding):
pytest tests/contract/test_blueprint_preview_sdk.py
pytest tests/integration/test_blueprint_preview_sdk.py
pytest tests/unit/blueprints/test_builder.py

# Parallel implementation tracks:
Track A: T020 (builder) → T021 (previewer)
Track B: T022 (SDK façade) + T023 (instruction cache) once builder interfaces fixed
Track C: T024 (schema export) + T025 (rendering) + T026 docs
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Complete Setup + Foundational.
2. Build blueprint authoring + preview (US1) with tests/docs.
3. Validate blueprint flow end-to-end as MVP.

### Incremental Delivery
1. Deliver US1 (blueprints + preview).
2. Add US2 (adapters) showing swap-ability.
3. Add US3 (execution) for full pipelines.
4. Each increment ends with tests/docs so it can ship independently.

### Parallel Team Strategy
1. Team A handles Setup/Foundational.
2. Once ready:
   - Team A → US1
   - Team B → US2 (adapters)
   - Team C → US3 (executor) after adapter interfaces stabilized.
3. Use contract/integration tests as shared gates to keep modules aligned.

---

## Notes
- Respect Constitution checklist (SOLID, docs, readability, tests, pre-commit).
- Every public SDK addition needs doc updates and `# AICODE-NOTE` comments for key trade-offs.
- Keep tasks independent; stop after each story to validate tests + docs before moving forward.
