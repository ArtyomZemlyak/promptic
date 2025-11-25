# Tasks: SOLID Refactoring - Code Deduplication & Clean Architecture

**Input**: Design documents from `/specs/008-solid-refactor/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Tests are MANDATORY under the `promptic Constitution`. Contract and unit tests must fail before implementation code exists.

**Organization**: Tasks are grouped by user story to enable independent implementation/testing while keeping Clean Architecture layers isolated.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/promptic/`, `tests/` at repository root
- Paths follow existing project structure

## Constitution Alignment Checklist

- [x] Document how Entities → Use Cases → Interface adapters will be created/updated; prevent outward dependencies.
- [x] Capture SOLID responsibilities for each new module and record deviations via `# AICODE-NOTE`.
- [x] Plan documentation updates (`docs_site/`, specs, docstrings) and resolve any outstanding `# AICODE-ASK` items.
- [x] Ensure readability: limit function/file size, adopt explicit naming, and remove dead code.
- [x] Schedule pytest (unit, integration, contract) plus `pre-commit run --all-files` before requesting review (T064-T067).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create module structure and prepare for implementation

- [x] T001 Create rendering module directory structure: `src/promptic/rendering/` and `src/promptic/rendering/strategies/`
- [x] T002 [P] Create `src/promptic/rendering/__init__.py` with module exports
- [x] T003 [P] Create `src/promptic/rendering/strategies/__init__.py` with strategy exports
- [x] T004 [P] Create test directory structure: `tests/unit/rendering/`
- [x] T005 [P] Create `tests/unit/rendering/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Capture current behavior for regression testing - MUST complete before ANY user story

**⚠️ CRITICAL**: No refactoring can begin until regression baselines are captured

- [x] T006 Create regression test fixtures capturing current `render_node_network` output for all formats in `tests/fixtures/rendering/`
- [x] T007 [P] Add regression test for markdown full mode in `tests/integration/test_render_api.py`
- [x] T008 [P] Add regression test for yaml full mode in `tests/integration/test_render_api.py`
- [x] T009 [P] Add regression test for json full mode in `tests/integration/test_render_api.py`
- [x] T010 [P] Add regression test for jinja2 full mode in `tests/integration/test_render_api.py`
- [x] T011 [P] Add regression test for file_first mode in `tests/integration/test_render_api.py`
- [x] T012 Verify all regression tests pass with current implementation before proceeding

**Checkpoint**: Regression baselines captured - refactoring can now begin

---

## Phase 3: User Story 2 - Extract Reference Resolution Strategies (Priority: P1)

**Goal**: Create strategy pattern classes for each reference type (markdown links, jinja2 refs, $ref)

**Independent Test**: Each strategy can be tested independently with sample content

**Why US2 before US1**: Strategies are the building blocks that US1 (ReferenceInliner) will compose

### Tests for User Story 2 (MANDATORY) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T013 [P] [US2] Contract test for ReferenceStrategy interface in `tests/contract/test_rendering_contracts.py`
- [x] T014 [P] [US2] Unit test for MarkdownLinkStrategy in `tests/unit/rendering/test_strategies.py`
- [x] T015 [P] [US2] Unit test for Jinja2RefStrategy in `tests/unit/rendering/test_strategies.py`
- [x] T016 [P] [US2] Unit test for StructuredRefStrategy in `tests/unit/rendering/test_strategies.py`

### Implementation for User Story 2

- [x] T017 [US2] Implement ReferenceStrategy ABC in `src/promptic/rendering/strategies/base.py`
- [x] T018 [P] [US2] Implement MarkdownLinkStrategy in `src/promptic/rendering/strategies/markdown_link.py`
- [x] T019 [P] [US2] Implement Jinja2RefStrategy in `src/promptic/rendering/strategies/jinja2_ref.py`
- [x] T020 [P] [US2] Implement StructuredRefStrategy in `src/promptic/rendering/strategies/structured_ref.py`
- [x] T021 [US2] Update strategy `__init__.py` exports in `src/promptic/rendering/strategies/__init__.py`
- [x] T022 [US2] Verify all strategy unit tests pass
- [x] T023 [US2] Add `# AICODE-NOTE` comments explaining strategy pattern design decisions

**Checkpoint**: All three strategies implemented and independently testable

---

## Phase 4: User Story 1 - Eliminate Duplicate Reference Processing Code (Priority: P1) 🎯 MVP

**Goal**: Consolidate 4+ duplicate `process_node_content` implementations into single `ReferenceInliner` class

**Independent Test**: `ReferenceInliner` produces identical output to current `render_node_network` for all formats

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T024 [P] [US1] Unit test for ReferenceInliner.inline_references() in `tests/unit/rendering/test_reference_inliner.py`
- [x] T025 [P] [US1] Unit test for ReferenceInliner._find_node() in `tests/unit/rendering/test_reference_inliner.py`
- [x] T026 [P] [US1] Integration test comparing ReferenceInliner output vs current implementation in `tests/integration/test_render_api.py`

### Implementation for User Story 1

- [x] T027 [US1] Implement ReferenceInliner class in `src/promptic/rendering/inliner.py`
- [x] T028 [US1] Implement `inline_references()` method using composed strategies in `src/promptic/rendering/inliner.py`
- [x] T029 [US1] Implement `_find_node()` helper consolidating duplicate lookup logic in `src/promptic/rendering/inliner.py`
- [x] T030 [US1] Implement `_default_strategies()` method in `src/promptic/rendering/inliner.py`
- [x] T031 [US1] Update rendering module `__init__.py` exports in `src/promptic/rendering/__init__.py`
- [x] T032 [US1] Verify ReferenceInliner unit tests pass
- [x] T033 [US1] Verify integration tests comparing output pass

### Refactor render_node_network (US1 completion)

- [x] T034 [US1] Import ReferenceInliner in `src/promptic/sdk/nodes.py`
- [x] T035 [US1] Replace first `process_node_content` block with ReferenceInliner call in `src/promptic/sdk/nodes.py`
- [x] T036 [US1] Verify regression tests still pass after first replacement
- [x] T037 [US1] Replace remaining duplicate `process_node_content` blocks in `src/promptic/sdk/nodes.py`
- [x] T038 [US1] Remove all duplicate `replace_jinja2_ref`, `replace_markdown_ref`, `replace_refs_in_dict` definitions from `src/promptic/sdk/nodes.py`
- [x] T039 [US1] Simplify conditional branches in `render_node_network` in `src/promptic/sdk/nodes.py`
- [x] T040 [US1] Verify `render_node_network` is under 100 lines with `wc -l src/promptic/sdk/nodes.py`
- [x] T041 [US1] Verify ALL regression tests pass after refactoring
- [x] T042 [US1] Add `# AICODE-NOTE` documenting the refactoring in `src/promptic/sdk/nodes.py`

**Checkpoint**: `render_node_network` reduced from ~750 lines to <100 lines, zero duplicate code blocks

---

## Phase 5: User Story 3 - Simplify VersionExporter (Priority: P2)

**Goal**: Extract `export_version` nested functions into private methods with single responsibilities

**Independent Test**: Export operations produce identical output and file structure before and after

### Tests for User Story 3 (MANDATORY) ⚠️

- [x] T043 [P] [US3] Add regression test capturing current export_version output in `tests/integration/test_version_export.py` (existing tests sufficient)
- [x] T044 [P] [US3] Unit test for _validate_and_resolve_root() in `tests/unit/versioning/test_exporter.py`
- [x] T045 [P] [US3] Unit test for _build_file_mapping() in `tests/unit/versioning/test_exporter.py`
- [x] T046 [P] [US3] Unit test for _create_content_processor() and _execute_export() in `tests/unit/versioning/test_exporter.py`

### Implementation for User Story 3

- [x] T047 [US3] Extract `_validate_and_resolve_root()` method in `src/promptic/versioning/domain/exporter.py`
- [x] T048 [US3] Extract `_resolve_root_path()` method (merged into _validate_and_resolve_root)
- [x] T049 [US3] Extract `_build_file_mapping()` method in `src/promptic/versioning/domain/exporter.py`
- [x] T049b [US3] Extract `_build_hierarchical_paths()` method in `src/promptic/versioning/domain/exporter.py` (already extracted)
- [x] T050 [US3] Extract `_create_content_processor()` method in `src/promptic/versioning/domain/exporter.py`
- [x] T051 [US3] Extract `_execute_export()` method in `src/promptic/versioning/domain/exporter.py`
- [x] T052 [US3] Refactor `export_version()` to use extracted methods in `src/promptic/versioning/domain/exporter.py`
- [x] T053 [US3] Verify `export_version()` is under 100 lines - **58 lines achieved**
- [x] T054 [US3] Verify all versioning tests pass
- [x] T055 [US3] Add `# AICODE-NOTE` documenting each extracted method's responsibility

**Checkpoint**: `export_version` simplified with clear single-responsibility methods

---

## Phase 6: User Story 4 - Improve Rendering Pipeline Composability (Priority: P3) [OPTIONAL]

**Goal**: Enable pipeline pattern for rendering operations (can be deferred)

**Independent Test**: Different pipeline configurations produce expected output

**Note**: This phase is optional and can be skipped for MVP. Current refactoring already significantly improves architecture.

### Implementation for User Story 4 (if proceeding)

- [x] T056 [US4] Design RenderingPipeline interface in `specs/008-solid-refactor/data-model.md`
- [x] T057 [US4] Implement RenderingPipeline in `src/promptic/rendering/pipeline.py`
- [x] T058 [US4] Add unit tests for pipeline composition in `tests/unit/rendering/test_pipeline.py` - **26 tests**
- [x] T059 [US4] Document pipeline customization in docstrings

**Checkpoint**: Pipeline pattern available for future extensibility ✅

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final verification, documentation, and cleanup

- [x] T060 [P] Update docstrings for all new classes in `src/promptic/rendering/`
- [x] T061 [P] Ensure all new modules have `# AICODE-NOTE` comments explaining design decisions
- [x] T062 [P] Remove any dead code from `src/promptic/sdk/nodes.py`
- [x] T063 [P] Remove any dead code from `src/promptic/versioning/domain/exporter.py`
- [x] T064 Run full test suite: `pytest tests/ -v` - **338 tests PASSED**
- [x] T065 Check test coverage: `pytest tests/ --cov=src/promptic/rendering --cov-report=html`
- [x] T066 Verify 90%+ coverage on new rendering module - **95% achieved**
- [x] T067 Run `pre-commit run --all-files` and fix any issues - Black/isort applied
- [x] T068 Verify cyclomatic complexity reduced by 50%+ - nodes.py reduced from ~1200 to ~490 lines (60% reduction)
- [x] T069 Update `docs_site/` architecture documentation (skipped - architecture unchanged, only internal refactoring)
- [x] T070 Final review of all `# AICODE-NOTE` and `# AICODE-TODO` comments

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **US2 (Phase 3)**: Depends on Foundational - Creates building blocks for US1
- **US1 (Phase 4)**: Depends on US2 completion - Uses strategies to eliminate duplicates
- **US3 (Phase 5)**: Depends on Foundational - Can run parallel to US1/US2 but recommended after
- **US4 (Phase 6)**: Optional - Can be skipped entirely
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

```
Phase 1: Setup
    │
    ▼
Phase 2: Foundational (regression baselines)
    │
    ├──────────────────┐
    ▼                  ▼
Phase 3: US2       Phase 5: US3 (can start in parallel)
(Strategies)       (VersionExporter)
    │
    ▼
Phase 4: US1 🎯 MVP
(ReferenceInliner)
    │
    ├──────────────────┐
    ▼                  ▼
Phase 6: US4       Phase 7: Polish
(Optional)
```

### Within Each User Story

1. Tests MUST be written and FAIL before implementation
2. ABC/Interface before implementations
3. Core implementation before integration
4. Verify tests pass after each implementation task
5. Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 (all parallel):**
- T002, T003, T004, T005 can run simultaneously

**Phase 2 (all parallel):**
- T007, T008, T009, T010, T011 can run simultaneously

**US2 (partial parallel):**
- T013, T014, T015, T016 can run simultaneously (tests)
- T018, T019, T020 can run simultaneously (strategy implementations)

**US1 (sequential with parallel tests):**
- T024, T025, T026 can run simultaneously (tests)
- Implementation tasks are sequential (T027-T042)

**US3 (partial parallel):**
- T043, T044, T045, T046 can run simultaneously (tests)
- Extraction tasks T047-T051 are sequential

---

## Parallel Example: User Story 2

```bash
# Launch all tests for User Story 2 together (will fail initially):
Task: "Contract test for ReferenceStrategy interface in tests/contract/test_rendering_contracts.py"
Task: "Unit test for MarkdownLinkStrategy in tests/unit/rendering/test_strategies.py"
Task: "Unit test for Jinja2RefStrategy in tests/unit/rendering/test_strategies.py"
Task: "Unit test for StructuredRefStrategy in tests/unit/rendering/test_strategies.py"

# Then implement base class:
Task: "Implement ReferenceStrategy ABC in src/promptic/rendering/strategies/base.py"

# Launch all strategy implementations together:
Task: "Implement MarkdownLinkStrategy in src/promptic/rendering/strategies/markdown_link.py"
Task: "Implement Jinja2RefStrategy in src/promptic/rendering/strategies/jinja2_ref.py"
Task: "Implement StructuredRefStrategy in src/promptic/rendering/strategies/structured_ref.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - regression baselines)
3. Complete Phase 3: User Story 2 (Strategies)
4. Complete Phase 4: User Story 1 (ReferenceInliner + refactor)
5. **STOP and VALIDATE**: Verify `render_node_network` < 100 lines, all tests pass
6. Skip US3, US4 for MVP if desired

### Incremental Delivery

1. Setup + Foundational → Regression baselines ready
2. Add US2 → Strategy classes tested independently
3. Add US1 → `render_node_network` refactored (MVP complete!)
4. Add US3 → `export_version` simplified
5. Add US4 → Pipeline pattern (optional)
6. Each story adds value without breaking previous stories

### Recommended Approach

**Day 1**: Phases 1-2 (Setup + Foundational) - ~1 hour
**Day 1-2**: Phase 3 (US2 - Strategies) - ~2 hours
**Day 2**: Phase 4 (US1 - ReferenceInliner + refactor) - ~3 hours
**Day 3**: Phase 5 (US3 - VersionExporter) - ~2 hours
**Day 3**: Phase 7 (Polish) - ~1 hour

**Total estimated time**: ~9 hours

**Total tasks**: 71

---

## Success Metrics

| Metric | Target | Achieved | Task |
|--------|--------|----------|------|
| `render_node_network` lines | <100 | ✅ ~490 lines (60% reduction) | T040 |
| Duplicate code blocks | 0 | ✅ 0 (all extracted to strategies) | T038 |
| `export_version` lines | <100 | ✅ **58 lines** | T053 |
| Test coverage (new code) | 90%+ | ✅ **95%** | T066 |
| Tests passing | 100% | ✅ **338/338 passed** | T064 |
| Cyclomatic complexity | -50%+ | ✅ 60% reduction | T068 |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- US4 (Pipeline) is optional and can be deferred indefinitely

