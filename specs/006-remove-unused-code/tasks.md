# Tasks: Remove Unused Code from Library

**Input**: Design documents from `/specs/006-remove-unused-code/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are MANDATORY under the `promptic Constitution`. List contract, integration, and unit coverage for every story before implementation, and ensure each test fails before the matching code exists.

**Organization**: Tasks are grouped by user story to enable independent implementation/testing while keeping Clean Architecture layers isolated.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project structure

## Constitution Alignment Checklist

- [x] Document how Entities → Use Cases → Interface adapters will be created/updated; prevent outward dependencies.
- [x] Capture SOLID responsibilities for each new module and record deviations via `# AICODE-NOTE`.
- [x] Plan documentation updates (`docs_site/`, specs, docstrings) and resolve any outstanding `# AICODE-ASK` items.
- [x] Ensure readability: limit function/file size, adopt explicit naming, and remove dead code.
- [x] Schedule pytest (unit, integration, contract) plus `pre-commit run --all-files` before requesting review.

## Phase 1: Setup (Verification & Backup)

**Purpose**: Verify current state and prepare for cleanup

- [X] T001 Run all examples 003, 004, 005, 006 and verify they work: `python examples/get_started/3-multiple-files/render.py`, `python examples/get_started/4-file-formats/render.py`, `python examples/get_started/5-versioning/render.py`, `python examples/get_started/6-version-export/export_demo.py`
- [X] T002 Run full test suite and record baseline: `pytest tests/ -v` (267 tests passed)
- [X] T003 [P] Create backup branch: `git checkout -b 006-remove-unused-code-backup`
- [X] T004 [P] Document current public API exports in `src/promptic/__init__.py` (9 functions exported)
- [X] T005 [P] Document current dependencies in `pyproject.toml` (10 dependencies)

---

## Phase 2: Foundational (Pre-Cleanup Verification)

**Purpose**: Verify examples work and identify all code dependencies before removal

**⚠️ CRITICAL**: No removal work can begin until this phase is complete

- [X] T006 [P] ~~Create integration test to verify examples 003-006 work~~ (SKIP - examples already verified in T001)
- [X] T007 [P] ~~Create test to verify current blueprint imports work~~ (SKIP - not needed, will verify removal instead)
- [X] T008 [P] ~~Create test to verify current adapter imports work~~ (SKIP - not needed, will verify removal instead)
- [X] T009 Analyze all imports in `src/promptic/__init__.py` and document blueprint/adapter dependencies (9 functions exported, 6 to remove)
- [X] T010 Analyze all imports in examples 003-006 to confirm they don't use blueprints/adapters/token counting (CONFIRMED - only node networks and versioning)
- [X] T011 Search codebase for "blueprint", "Blueprint" and document all occurrences (519 matches, 38 files)
- [X] T012 Search codebase for "adapter", "Adapter" and document all occurrences (292 matches, 33 files)
- [X] T013 Search codebase for "token", "TokenCounter" and document all occurrences (135 matches, 11 files)
- [X] T014 Search codebase for "settings" imports and verify node network code doesn't use them (VERIFIED - only dead import in versioning/utils/logging.py)

**Checkpoint**: ✅ Foundation ready - removal work can now begin

---

## Phase 3: User Story 1 - Remove Blueprint System (Priority: P1) 🎯 MVP

**Goal**: Remove all blueprint-related code that is not used in examples 003, 004, 005, 006

**Independent Test**: After removal, examples 003, 004, 005, 006 should continue to work without any changes. All blueprint-related imports should raise ImportError.

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T015 [P] [US1] Create integration test for blueprint import errors in `tests/integration/test_import_errors.py` (test `from promptic import load_blueprint` raises ImportError)
- [X] T016 [P] [US1] Create integration test for blueprint package import errors in `tests/integration/test_import_errors.py` (test `from promptic.blueprints import ...` raises ImportError)
- [X] T017 [P] [US1] Create contract test for public API in `tests/contract/test_public_api.py` (verify blueprint functions not exported)
- [X] T018 [P] [US1] Create integration test to verify examples 003-006 still work after blueprint removal in `tests/integration/test_examples_after_cleanup.py`

### Implementation for User Story 1

- [X] T019 [P] [US1] Remove `promptic.blueprints` package directory: `src/promptic/blueprints/`
- [X] T020 [P] [US1] Remove `promptic.instructions` package directory: `src/promptic/instructions/`
- [X] T021 [P] [US1] Remove `promptic.sdk.blueprints` module: `src/promptic/sdk/blueprints.py`
- [X] T022 [P] [US1] Remove `promptic.pipeline.builder` module: `src/promptic/pipeline/builder.py`
- [X] T023 [P] [US1] Remove `promptic.pipeline.previewer` module: `src/promptic/pipeline/previewer.py`
- [X] T024 [P] [US1] Remove `promptic.pipeline.executor` module: `src/promptic/pipeline/executor.py`
- [X] T025 [P] [US1] Remove `promptic.pipeline.template_renderer` module: `src/promptic/pipeline/template_renderer.py`
- [X] T026 [P] [US1] Remove `promptic.pipeline.validation` module: `src/promptic/pipeline/validation.py`
- [X] T027 [P] [US1] Remove `promptic.pipeline.hooks` module: `src/promptic/pipeline/hooks.py`
- [X] T028 [P] [US1] Remove `promptic.pipeline.loggers` module: `src/promptic/pipeline/loggers.py`
- [X] T029 [P] [US1] Remove `promptic.pipeline.policies` module: `src/promptic/pipeline/policies.py`
- [X] T030 [P] [US1] Remove `promptic.context.rendering` module: `src/promptic/context/rendering.py`
- [X] T031 [P] [US1] Remove `promptic.context.template_context` module: `src/promptic/context/template_context.py`
- [X] T032 [US1] Remove blueprint functions from `promptic.sdk.api` in `src/promptic/sdk/api.py`: `load_blueprint`, `render_preview`, `render_for_llm`, `render_instruction`, `preview_blueprint`, `bootstrap_runtime`, `build_materializer`
- [X] T033 [US1] Remove blueprint exports from `promptic.__init__.py` in `src/promptic/__init__.py`: `bootstrap_runtime`, `load_blueprint`, `preview_blueprint`, `render_for_llm`, `render_instruction`, `render_preview`
- [X] T034 [US1] Remove blueprint-related imports from `src/promptic/sdk/api.py`
- [X] T035 [US1] Add `# AICODE-NOTE: Blueprint system removed - not used in examples 003-006. Use node networks instead.` comment in `src/promptic/__init__.py` where blueprint exports were removed

**Checkpoint**: ✅ User Story 1 COMPLETE - blueprints removed, all examples still work, 17 new tests pass

---

## Phase 4: User Story 2 - Remove Adapter System (Priority: P1) ✅ COMPLETE

**Goal**: Remove all adapter-related code for data and memory sources that is not used in examples 003, 004, 005, 006

**Independent Test**: After removal, examples 003-006 should continue to work. All adapter-related imports should raise ImportError.

### Tests for User Story 2 (MANDATORY) ⚠️

- [X] T036 [P] [US2] Add adapter import error test to `tests/integration/test_import_errors.py` (test `from promptic.adapters import AdapterRegistry` raises ImportError)
- [X] T037 [P] [US2] Add adapter package import error test to `tests/integration/test_import_errors.py` (test `from promptic.adapters import ...` raises ImportError)
- [X] T038 [P] [US2] Update contract test in `tests/contract/test_public_api.py` to verify adapter functions not exported
- [X] T039 [P] [US2] Verify examples 003-006 still work after adapter removal in `tests/integration/test_examples_after_cleanup.py`

### Implementation for User Story 2

- [X] T040 [P] [US2] Remove `promptic.adapters` package directory: `src/promptic/adapters/`
- [X] T041 [P] [US2] Remove `promptic.sdk.adapters` module: `src/promptic/sdk/adapters.py`
- [X] T042 [P] [US2] Remove `promptic.pipeline.context_materializer` module: `src/promptic/pipeline/context_materializer.py`
- [X] T043 [P] [US2] Remove `promptic.settings` package directory: `src/promptic/settings/`
- [X] T044 [P] [US2] Remove `promptic.pipeline.format_renderers` package directory: `src/promptic/pipeline/format_renderers/`
- [X] T045 [P] [US2] Remove `promptic.context.logging` module: `src/promptic/context/logging.py`
- [X] T046 [P] [US2] Remove `promptic.context.errors` module: `src/promptic/context/errors.py` (node network uses `promptic.context.nodes.errors`)
- [X] T047 [US2] Remove adapter-related imports from `src/promptic/sdk/api.py`
- [X] T048 [US2] Remove adapter-related imports from any remaining files (search and remove)
- [X] T049 [US2] Remove settings-related imports from `src/promptic/versioning/utils/logging.py` if present (dead import)
- [X] T050 [US2] Add `# AICODE-NOTE: Adapter system removed - not used in examples 003-006. Node networks work directly with filesystem.` comment where adapters were removed

**Checkpoint**: ✅ User Stories 1 AND 2 COMPLETE - blueprints and adapters removed, examples still work, 15 new tests pass

---

## Phase 5: User Story 3 - Remove Token Counting (Priority: P2) ✅ COMPLETE

**Goal**: Remove token counting functionality that is not used in examples 003, 004, 005, 006

**Independent Test**: After removal, examples 003-006 should continue to work. Token counting should not be referenced anywhere.

### Tests for User Story 3 (MANDATORY) ⚠️

- [X] T051 [P] [US3] Add token counting import error test to `tests/integration/test_import_errors.py` (test `from promptic.token_counting import TokenCounter` raises ImportError)
- [X] T052 [P] [US3] Verify examples 003-006 still work after token counting removal in `tests/integration/test_examples_after_cleanup.py`
- [X] T053 [P] [US3] Add test to verify no token-related code remains in `tests/integration/test_no_token_references.py`

### Implementation for User Story 3

- [X] T054 [P] [US3] Remove `promptic.token_counting` package directory: `src/promptic/token_counting/`
- [X] T055 [US3] Remove token counting references from `promptic.context.nodes.models.NetworkConfig` in `src/promptic/context/nodes/models.py` if present
- [X] T056 [US3] Remove `tiktoken` dependency from `pyproject.toml` if not used elsewhere
- [X] T057 [US3] Remove token-related imports from any remaining files (search and remove)
- [X] T058 [US3] Add `# AICODE-NOTE: Token counting removed - not used in examples 003-006.` comment where token counting was removed

**Checkpoint**: ✅ User Stories 1, 2, AND 3 COMPLETE - blueprints, adapters, and token counting removed, examples still work, all tests pass

---

## Phase 6: User Story 4 - Verify Core Features Work (Priority: P1) ✅ COMPLETE (verified via example tests)

**Goal**: Ensure that after cleanup, all features used in examples 003, 004, 005, 006 continue to work correctly

**Independent Test**: Run all examples 003, 004, 005, 006 and verify they produce expected output without errors.

### Tests for User Story 4 (MANDATORY) ⚠️

- [X] T059 [P] [US4] ~~Create integration test for example 003~~ (covered by test_examples_after_cleanup.py)
- [X] T060 [P] [US4] ~~Create integration test for example 004~~ (covered by test_examples_after_cleanup.py)
- [X] T061 [P] [US4] ~~Create integration test for example 005~~ (covered by test_examples_after_cleanup.py)
- [X] T062 [P] [US4] ~~Create integration test for example 006~~ (covered by test_examples_after_cleanup.py)
- [X] T063 [P] [US4] Update contract test in `tests/contract/test_public_api.py` to verify only expected functions exported

### Implementation for User Story 4

- [X] T064 [US4] Verify `promptic.sdk.nodes` module exists and exports `load_node_network`, `render_node_network`
- [X] T065 [US4] Verify `promptic.versioning` module exists and exports `load_prompt`, `export_version`, `cleanup_exported_version`
- [X] T066 [US4] Verify `promptic.context.nodes` module exists with `ContextNode`, `NodeNetwork` models
- [X] T067 [US4] Verify `promptic.format_parsers` package exists with yaml, markdown, json, jinja2 parsers
- [X] T068 [US4] Verify `promptic.pipeline.network.builder` module exists with `NodeNetworkBuilder`
- [X] T069 [US4] Verify `promptic.resolvers` package exists with filesystem resolver
- [X] T070 [US4] Run examples 003, 004, 005, 006 manually and verify they produce expected output
- [X] T071 [US4] Verify all imports in examples 003-006 succeed

**Checkpoint**: ✅ All user stories COMPLETE - cleanup done, all examples work, all core features verified

---

## Phase 7: Polish & Cross-Cutting Concerns ✅ COMPLETE

**Purpose**: Final cleanup, documentation, and verification

- [X] T072 [P] Remove all blueprint-related tests (already removed)
- [X] T073 [P] Remove all adapter-related tests (already removed)  
- [X] T074 [P] Remove all instructions-related tests (already removed)
- [X] T075 [P] Remove all token_counting-related tests (already removed)
- [X] T076 [P] Remove blueprint/adapter integration tests (already removed)
- [X] T077 [P] Remove blueprint/adapter contract tests (already removed)
- [X] T078 [P] Update `README.md` (DONE - replaced with proper English README for simplified library)
- [X] T079 [P] Remove blueprint/adapter documentation from `docs_site/` (DONE - removed 10 blueprint/adapter docs, updated others)
- [X] T080 [P] Verify no "blueprint" references in source (verified - only AICODE-NOTE comments remain)
- [X] T081 [P] Verify no "adapter" references in source (verified - only versioning adapters and comments remain)
- [X] T082 [P] Verify no "token" references in source (verified - only AICODE-NOTE comments remain)
- [X] T083 [P] Verify no "settings" references in source (verified - removed)
- [X] T084 [P] Verify no "format_renderers" references in source (verified - removed)
- [X] T085 [P] Removed `pydantic-settings` from `pyproject.toml` (DONE in T056)
- [X] T086 [P] Removed `rich` from `pyproject.toml` (DONE in T056)
- [ ] T087 [P] Update `CHANGELOG.md` (SKIP - file doesn't exist)
- [X] T088 [P] Add `# AICODE-NOTE` comments (DONE throughout implementation)
- [X] T089 Run full test suite: 179 tests PASSED ✓
- [X] T090 Run examples 003-006: All examples work ✓
- [X] T091 Format code with Black ✓
- [X] T092 Sort imports with isort ✓
- [X] T093 Run pre-commit: All hooks PASSED ✓
- [ ] T094 Verify code coverage (DEFERRED - tests pass, coverage can be checked separately)
- [ ] T095 Execute quickstart.md validation (DEFERRED - examples verified via tests)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User Story 1 (P1): Remove Blueprints - can start after Foundational
  - User Story 2 (P1): Remove Adapters - can start after Foundational (independent of US1)
  - User Story 3 (P2): Remove Token Counting - can start after Foundational (independent of US1, US2)
  - User Story 4 (P1): Verify Core Features - MUST run after US1, US2, US3 complete
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Independent of US1, can run in parallel
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Independent of US1, US2, can run in parallel
- **User Story 4 (P1)**: MUST run after US1, US2, US3 complete - verifies everything still works

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Removal tasks can run in parallel (different files)
- Verification tasks run after removal
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, User Stories 1, 2, 3 can start in parallel (if team capacity allows)
- All removal tasks within a story marked [P] can run in parallel (different files)
- All test tasks marked [P] can run in parallel
- User Stories 1, 2, 3 can be worked on in parallel by different team members (but US4 must wait for all)

---

## Parallel Example: User Story 1

```bash
# Launch all removal tasks for User Story 1 together (different files):
Task: "Remove promptic.blueprints package directory: src/promptic/blueprints/"
Task: "Remove promptic.instructions package directory: src/promptic/instructions/"
Task: "Remove promptic.sdk.blueprints module: src/promptic/sdk/blueprints.py"
Task: "Remove promptic.pipeline.builder module: src/promptic/pipeline/builder.py"
Task: "Remove promptic.pipeline.previewer module: src/promptic/pipeline/previewer.py"
# ... etc (all [P] tasks can run simultaneously)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify examples work)
2. Complete Phase 2: Foundational (analyze dependencies)
3. Complete Phase 3: User Story 1 (Remove Blueprints)
4. **STOP and VALIDATE**: Test examples 003-006 still work, verify blueprints removed
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Remove Blueprints) → Test independently → Verify examples work (MVP!)
3. Add User Story 2 (Remove Adapters) → Test independently → Verify examples work
4. Add User Story 3 (Remove Token Counting) → Test independently → Verify examples work
5. Add User Story 4 (Verify Core Features) → Test all examples → Final validation
6. Add Polish phase → Documentation, cleanup, final verification
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Remove Blueprints)
   - Developer B: User Story 2 (Remove Adapters)
   - Developer C: User Story 3 (Remove Token Counting)
3. All complete, then Developer A: User Story 4 (Verify Core Features)
4. Team: Polish phase together

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- This is a cleanup task - removal is the primary work, verification is critical
- Always verify examples 003-006 work after each removal phase

---

## Task Summary

**Total Tasks**: 95
- Phase 1 (Setup): 5 tasks
- Phase 2 (Foundational): 9 tasks
- Phase 3 (US1 - Remove Blueprints): 21 tasks (4 tests + 17 implementation)
- Phase 4 (US2 - Remove Adapters): 15 tasks (4 tests + 11 implementation)
- Phase 5 (US3 - Remove Token Counting): 8 tasks (3 tests + 5 implementation)
- Phase 6 (US4 - Verify Core Features): 13 tasks (5 tests + 8 implementation)
- Phase 7 (Polish): 24 tasks

**Parallel Opportunities**:
- Phase 1: 3 tasks can run in parallel
- Phase 2: 9 tasks can run in parallel
- Phase 3: 16 tasks can run in parallel (all [P] marked)
- Phase 4: 11 tasks can run in parallel (all [P] marked)
- Phase 5: 5 tasks can run in parallel (all [P] marked)
- Phase 6: 8 tasks can run in parallel (all [P] marked)
- Phase 7: 24 tasks can run in parallel (all [P] marked)

**Suggested MVP Scope**: Phase 1 + Phase 2 + Phase 3 (User Story 1 - Remove Blueprints) = 35 tasks
