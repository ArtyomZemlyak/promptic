# Tasks: File-First Prompt Hierarchy

**Input**: Design documents from `/specs/003-file-first-prompts/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/file_first_renderer.yaml, quickstart.md

**Tests**: Contract, integration, and unit coverage are mandatory per the `promptic Constitution`. Each story lists its required tests, which must fail before implementation begins.

**Organization**: Tasks are grouped by user story so every slice can be implemented, tested, and demonstrated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Task can run in parallel (different files, no blocking dependencies)
- **[Story]**: User story label (US1, US2, US3). Setup/Foundational/Polish phases omit the label.
- Include exact file paths in every description.

## Constitution Alignment Checklist

- [X] Document how Entities → Use Cases → Interface adapters are updated; keep dependencies pointing inward.
  - **Status**: ✅ COMPLETE - Architecture documentation created in `docs_site/context-engineering/file-first-architecture.md` explaining:
    - Entities: `PromptHierarchyBlueprint`, `InstructionReference`, `MemoryChannel`, `RenderMetrics` (domain models in `src/promptic/blueprints/models.py`)
    - Use Cases: `FileFirstRenderer.render()` orchestrates rendering workflow (application layer)
    - Interface Adapters: `FileSummaryService`, `ReferenceFormatter`, `ReferenceTreeBuilder`, `RenderMetricsBuilder` (adapt domain to rendering needs)
    - Dependencies: All point inward (renderer depends on `ContextMaterializer` interface, not concrete implementations)
    - SOLID principles documented for each adapter class
    - Dependency flow diagram and integration points explained

- [ ] Capture SOLID responsibilities for each new helper (`FileSummaryService`, `ReferenceFormatter`, etc.) and add `# AICODE-NOTE` where deviations occur.
  - **Status**: ⚠️ PARTIALLY COMPLETE - Only one `# AICODE-NOTE` found (in `FileFirstRenderer` class docstring). Helper classes lack explicit SOLID responsibility documentation.
  - **Action needed**: Add `# AICODE-NOTE` comments to each helper class documenting their SOLID responsibilities:
    - `FileSummaryService`: Single Responsibility (SRP) - summarizes instructions only; Open/Closed (OCP) - extensible via overrides
    - `ReferenceFormatter`: SRP - formats paths/hints only; Dependency Inversion (DIP) - depends on base_url abstraction
    - `ReferenceTreeBuilder`: SRP - builds reference trees; Interface Segregation (ISP) - minimal public interface
    - `RenderMetricsBuilder`: SRP - calculates metrics only

- [X] Plan docs updates in `docs_site/`, quickstart, and inline docstrings; resolve any `# AICODE-ASK`.
  - **Status**: ✅ COMPLETE - Documentation updated in:
    - `docs_site/context-engineering/blueprint-guide.md` (File-First Render Mode Metadata section)
    - `docs_site/context-engineering/quickstart-validation.md` (File-First Quickstart Check section)
    - `docs_site/context-engineering/execution-recipes.md` (file-first CLI usage)
  - No `# AICODE-ASK` comments found in codebase (all resolved).

- [ ] Preserve readability: helper functions ≤40 LOC, descriptive naming, no dead code.
  - **Status**: ❌ NOT COMPLETE - `FileFirstRenderer.render()` method has 55 LOC (exceeds 40 LOC limit by 15 lines).
  - **Action needed**: Refactor `render()` method to extract logic into smaller helper methods:
    - Extract metadata/overrides preparation (lines 297-299)
    - Extract service initialization (lines 301-312)
    - Extract hierarchy building (lines 323-329)
    - Extract markdown rendering call (lines 330-335)
  - Descriptive naming: ✅ Good (all functions have clear names)
  - Dead code: ✅ None detected

- [ ] Schedule pytest (unit, integration, contract) plus `pre-commit run --all-files` before requesting review.
  - **Status**: ❌ NOT COMPLETE - Tasks T031 and T032 are still unchecked:
    - T031: Run targeted pytest focus (`pytest tests -k file_first`) plus full suite
    - T032: Run `pre-commit run --all-files` and fix any issues
  - **Action needed**: Complete T031 and T032 before marking this checklist item as done.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare shared scaffolding for renderer code and tests.

- [X] T001 Create file-first renderer module scaffold in `src/promptic/pipeline/format_renderers/file_first.py` with placeholder strategy class and exports.
- [X] T002 [P] Add dedicated test module skeleton in `tests/unit/pipeline/test_file_first_renderer.py` with fixtures for sample blueprints.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure required before any user story work.

- [X] T003 Implement `PromptHierarchyBlueprint`, `InstructionReference`, `MemoryChannel`, and `RenderMetrics` models in `src/promptic/blueprints/models.py`.
- [X] T004 [P] Extend `src/promptic/blueprints/serialization.py` to emit deterministic step IDs, token estimates, and honor summary overrides defined in blueprint metadata (depends on T003).
- [X] T005 [P] Add unit tests for summary override serialization in `tests/unit/blueprints/test_serialization.py`.
- [X] T006 [P] Enhance `src/promptic/instructions/store.py` to expose memory descriptor scanning hooks used by later stories.
- [X] T007 Register the `file_first` strategy in `src/promptic/pipeline/template_renderer.py`, wiring dependency-injected helpers (depends on T003–T006).
- [X] T008 [P] Implement `ReferenceTreeBuilder` with cycle detection and depth limiting in `src/promptic/pipeline/format_renderers/file_first.py`.
- [X] T009 [P] Add unit tests for `ReferenceTreeBuilder` in `tests/unit/pipeline/test_file_first_renderer.py`.

**Checkpoint**: Foundation ready—user stories can now start independently.

---

## Phase 3: User Story 1 – Render compact root instruction (Priority: P1) 🎯 MVP

**Goal**: Produce a concise persona/goals block plus ordered steps referencing `instructions/*.md` files with summaries while emitting render metrics.  
**Independent Test**: CLI/SDK render of `examples/us1-blueprints/simple_blueprint.yaml` outputs summary-only content, reports ≥60% token reduction via `RenderMetrics`, and fails fast on missing files.

### Tests for User Story 1 (write first, ensure they fail)

- [X] T010 [P] [US1] Add unit tests covering summary generation, RenderMetrics calculations, and missing-file errors in `tests/unit/pipeline/test_file_first_renderer.py`.
- [X] T011 [P] [US1] Add integration test in `tests/integration/test_blueprint_preview_sdk.py` validating persona/goals, reference bullets, and ≥60% token reduction with metrics asserted.

### Implementation for User Story 1

- [X] T012 [US1] Implement `FileSummaryService` to cap summaries at 120 tokens inside `src/promptic/pipeline/format_renderers/file_first.py`.
- [X] T013 [US1] Build persona/goals + ordered steps block in `src/promptic/pipeline/template_renderer.py`, consuming new models (depends on T012).
- [X] T014 [US1] Implement `RenderMetrics` builder to capture before/after token counts and reference totals in `src/promptic/pipeline/format_renderers/file_first.py`.
- [X] T015 [US1] Enforce deterministic missing-file validation and descriptive errors in `src/promptic/instructions/store.py`.

**Checkpoint**: File-first mode renders compact root instructions, emits metrics, and passes US1 tests.

---

## Phase 4: User Story 2 – Guide agents to fetch deep context on demand (Priority: P2)

**Goal**: Ensure every step provides explicit instructions (including absolute links via `base_url`) so agents know how to retrieve detailed context while respecting nested reference trees.  
**Independent Test**: Rendering `examples/complete/research_flow.yaml` shows inline “see instructions/…“ hints with absolute URLs when `base_url` is set, emits tree metadata, and satisfies contract schema.

### Tests for User Story 2 (write first)

- [X] T016 [P] [US2] Extend contract coverage in `tests/contract/test_template_context_contract.py` to assert metadata schema (`steps`, `memory_channels`, `metrics`, `reference_tree`) and base URL behavior.
- [X] T017 [P] [US2] Add integration test in `tests/integration/test_instruction_templating.py` verifying inline hints, absolute links, and depth-limit warnings when nested references exceed the cap.

### Implementation for User Story 2

- [X] T018 [US2] Enhance `ReferenceFormatter` to inject detail hints and `base_url`-aware links in `src/promptic/pipeline/format_renderers/file_first.py`.
- [X] T019 [US2] Integrate `ReferenceTreeBuilder` into rendering flows, surfacing cycle warnings and depth-limit truncation in `src/promptic/pipeline/format_renderers/file_first.py`.
- [X] T020 [US2] Propagate reference metadata through `src/promptic/pipeline/executor.py` logging so agents can trace step access.
- [X] T021 [US2] Add `--render-mode file_first` / `--base-url` options to CLI preview (`src/promptic/pipeline/previewer.py`) and expose `base_url` kwarg via `src/promptic/sdk/blueprints.py`.

**Checkpoint**: Agents receive actionable reference hints (relative or absolute), nested trees are enforced, and contract tests confirm schema stability.

---

## Phase 5: User Story 3 – Declare memory and metadata instructions centrally (Priority: P3)

**Goal**: Surface memory/logging instructions (locations, format descriptors, retention guidance) within the root prompt and metadata.  
**Independent Test**: Rendering a blueprint with `memory/format.md` lists the memory block in markdown, includes populated `memory_channels`, and documents fallback behavior.

### Tests for User Story 3 (write first)

- [X] T022 [P] [US3] Add integration test in `tests/integration/test_instruction_templating.py` validating the “Memory & logging” block, descriptor overrides, and default hierarchical fallback.
- [X] T023 [P] [US3] Add unit tests for `MemoryDescriptorCollector` in `tests/unit/instructions/test_store.py`.

### Implementation for User Story 3

- [X] T024 [US3] Implement `MemoryDescriptorCollector` that reads user-defined descriptors or defaults in `src/promptic/instructions/store.py`.
- [X] T025 [US3] Render memory sections and `memory_channels` metadata in `src/promptic/pipeline/format_renderers/file_first.py`.
- [X] T026 [US3] Update `docs_site/context-engineering/blueprint-guide.md` with Memory & logging configuration steps referencing descriptor files.

**Checkpoint**: Memory guidance appears centrally in outputs and metadata, satisfying US3 tests.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T027 [P] Document the full file-first workflow (persona/goals, steps, metrics) in `docs_site/context-engineering/blueprint-guide.md`.
- [X] T028 [P] Update `docs_site/context-engineering/quickstart-validation.md` with CLI/SDK commands, base URL guidance, and RenderMetrics checks.
- [X] T029 [P] Capture CLI/SDK flag usage and reference logging steps in `docs_site/context-engineering/execution-recipes.md`.
- [X] T030 [P] Execute the quickstart scenario in `specs/003-file-first-prompts/quickstart.md` and record outputs/screenshots for docs.
- [ ] T031 Run targeted pytest focus (`pytest tests -k file_first`) plus full suite from repository root (`tests/`).
- [ ] T032 Run `pre-commit run --all-files` at repo root and fix any style/lint issues before final review.

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup (Phase 1) ➜ Foundational (Phase 2) ➜ User Stories (Phases 3–5) ➜ Polish (Phase 6).
- Foundational tasks (T003–T009) block every user story; complete them before starting US1–US3.

### User Story Dependencies

- **US1**: Depends on Foundational phase; delivers MVP and RenderMetrics baseline.
- **US2**: Depends on US1 helpers and tree builder; can proceed once T012–T019 exist.
- **US3**: Depends on memory hooks from Foundational and may share code with US1/US2 but remains independently testable.

### Within Each User Story

- Tests (contract/integration/unit) precede implementation tasks.
- Models/helpers → services → renderer wiring → CLI/SDK exposure.
- Each story concludes with its checkpoint before moving on.

### Parallel Opportunities

- Tasks marked [P] can run concurrently (e.g., T002, T004–T006, test authoring pairs, integration vs. contract tests).
- Different user stories may proceed in parallel after Foundational phase if team size permits.

---

## Parallel Execution Examples

### User Story 1

```bash
# Parallel test authoring
T010 tests/unit/pipeline/test_file_first_renderer.py
T011 tests/integration/test_blueprint_preview_sdk.py

# Parallel helper work after tests exist
T012 src/promptic/pipeline/format_renderers/file_first.py
T015 src/promptic/instructions/store.py
```

### User Story 2

```bash
# Contract vs integration coverage in parallel
T016 tests/contract/test_template_context_contract.py
T017 tests/integration/test_instruction_templating.py

# CLI/SDK updates in parallel with executor logging
T020 src/promptic/pipeline/executor.py
T021 src/promptic/pipeline/previewer.py + src/promptic/sdk/blueprints.py
```

### User Story 3

```bash
# Memory tests first
T022 tests/integration/test_instruction_templating.py
T023 tests/unit/instructions/test_store.py

# Rendering + docs updates in parallel
T024 src/promptic/instructions/store.py
T026 docs_site/context-engineering/blueprint-guide.md
```

---

## Implementation Strategy

### MVP First (US1 Only)
1. Finish Setup + Foundational phases.
2. Complete US1 tests and implementation (T010–T015).
3. Validate via CLI/SDK render; demo compact prompt with RenderMetrics to stakeholders.

### Incremental Delivery
1. Deliver US1 (persona/goals + references + metrics) as MVP.
2. Layer US2 to add actionable hints, tree enforcement, and base URL support.
3. Add US3 to surface memory instructions and descriptors.
4. Finish Polish phase (T027–T032) to finalize docs and quality gates.

### Parallel Team Strategy
1. Team collaborates on Setup/Foundational tasks.
2. Assign US1, US2, US3 to different developers once foundation is stable.
3. Rejoin for Polish tasks to ensure documentation, tests, and tooling are consistent.
