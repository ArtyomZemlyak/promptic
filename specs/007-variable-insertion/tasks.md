# Tasks: Variable Insertion in Prompts

**Input**: Design documents from `/specs/007-variable-insertion/`
**Prerequisites**: spec.md (completed), plan.md (completed)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Constitution Alignment Checklist

- [x] Domain layer (variables/) separated from adapters (format_parsers/) and SDK (nodes.py, api.py)
- [x] SOLID: VariableSubstitutor (substitution), ScopeResolver (scope matching), formatparsers (format-specific handling)
- [x] Documentation: docs_site/variables/, inline docstrings, AICODE-NOTE comments
- [x] Readability: Functions <80 lines, clear names, simple patterns
- [x] Tests: unit (scope, substitution), integration (hierarchies), contract (interfaces)

---

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Create project structure: `src/promptic/context/variables/` directory
- [x] T002 Create test structure: `tests/unit/variables/` directory
- [x] T003 [P] Create specification documents in `specs/007-variable-insertion/`

---

## Phase 2: User Story 1 - Simple Variable Insertion (P1) 🎯 MVP

**Goal**: Enable basic variable replacement with global scope

**Independent Test**: Render prompt with `{{var}}` using `vars={"var": "value"}`, output contains "value"

### Tests for User Story 1 (MANDATORY) ⚠️

- [ ] T004 [P] [US1] Unit test for basic substitution in `tests/unit/variables/test_substitutor.py`
- [ ] T005 [P] [US1] Unit test for multiple occurrences in `tests/unit/variables/test_substitutor.py`
- [ ] T006 [P] [US1] Contract test for VariableSubstitutor interface in `tests/contract/test_variable_contract.py`

### Implementation for User Story 1

- [ ] T007 [P] [US1] Create `src/promptic/context/variables/__init__.py` with exports
- [ ] T008 [P] [US1] Create `src/promptic/context/variables/models.py` with VariableScope enum and SubstitutionContext
- [ ] T009 [US1] Create `src/promptic/context/variables/substitutor.py` with VariableSubstitutor service (basic substitution)
- [ ] T010 [US1] Update `src/promptic/sdk/nodes.py` - add `vars` parameter to `render_node_network()`
- [ ] T011 [US1] Integrate VariableSubstitutor into rendering pipeline in `render_node_network()`
- [ ] T012 [US1] Add docstrings and AICODE-NOTE explaining substitution strategy

**Checkpoint**: Basic variable insertion works end-to-end for simple {{var}} replacement

---

## Phase 3: User Story 4 - Format-Specific Variable Syntax (P2)

**Goal**: Support variables in all file formats without syntax conflicts

**Independent Test**: Render prompts in MD, YAML, JSON, Jinja2 with variables, all produce correct output

### Tests for User Story 4 (MANDATORY) ⚠️

- [ ] T013 [P] [US4] Unit test for Markdown variable handling in `tests/unit/format_parsers/test_markdown_parser.py`
- [ ] T014 [P] [US4] Unit test for YAML variable handling in `tests/unit/format_parsers/test_yaml_parser.py`
- [ ] T015 [P] [US4] Unit test for JSON variable handling in `tests/unit/format_parsers/test_json_parser.py`
- [ ] T016 [P] [US4] Unit test for Jinja2 native variables in `tests/unit/variables/test_jinja2_variables.py`
- [ ] T017 [P] [US4] Integration test for mixed formats with variables in `tests/integration/test_variable_insertion.py`

### Implementation for User Story 4

- [ ] T018 [P] [US4] Update `src/promptic/format_parsers/markdown_parser.py` - preserve {{var}} during parsing
- [ ] T019 [P] [US4] Update `src/promptic/format_parsers/yaml_parser.py` - handle variables in values
- [ ] T020 [P] [US4] Update `src/promptic/format_parsers/json_parser.py` - handle variables in strings
- [ ] T021 [US4] Create `src/promptic/context/variables/jinja2_renderer.py` - native Jinja2 variable rendering
- [ ] T022 [US4] Update `src/promptic/format_parsers/jinja2_parser.py` - integrate Jinja2VariableRenderer
- [ ] T023 [US4] Update VariableSubstitutor to route Jinja2 files to Jinja2VariableRenderer
- [ ] T024 [US4] Add AICODE-NOTE in each parser explaining variable handling strategy

**Checkpoint**: Variables work correctly in all file formats

---

## Phase 4: User Story 2 - Node-Scoped Variable Insertion (P2)

**Goal**: Enable targeting variables to specific nodes using "node.var" syntax

**Independent Test**: Hierarchy with two nodes containing {{var}}, render with node-scoped vars, each node gets correct value

### Tests for User Story 2 (MANDATORY) ⚠️

- [ ] T025 [P] [US2] Unit test for node scope parsing in `tests/unit/variables/test_scope_resolution.py`
- [ ] T026 [P] [US2] Unit test for node matching in `tests/unit/variables/test_scope_resolution.py`
- [ ] T027 [P] [US2] Integration test with node-scoped collisions in `tests/integration/test_variable_insertion.py`

### Implementation for User Story 2

- [ ] T028 [US2] Create `src/promptic/context/variables/resolver.py` with ScopeResolver service
- [ ] T029 [US2] Implement node scope parsing logic (extract node name from "node.var")
- [ ] T030 [US2] Implement node matching logic (compare node name from variable with node ID)
- [ ] T031 [US2] Update VariableSubstitutor to use ScopeResolver for node-scoped variables
- [ ] T032 [US2] Update rendering pipeline to pass node context to substitutor
- [ ] T033 [US2] Add AICODE-NOTE explaining scope precedence rules

**Checkpoint**: Node-scoped variables work independently of simple variables

---

## Phase 5: User Story 3 - Full-Path Variable Insertion (P3)

**Goal**: Enable targeting variables using full hierarchical paths "root.group.node.var"

**Independent Test**: Deep hierarchy with path-scoped vars, only matching nodes receive values

### Tests for User Story 3 (MANDATORY) ⚠️

- [ ] T034 [P] [US3] Unit test for path scope parsing in `tests/unit/variables/test_scope_resolution.py`
- [ ] T035 [P] [US3] Unit test for hierarchical path matching in `tests/unit/variables/test_scope_resolution.py`
- [ ] T036 [P] [US3] Integration test with 3+ nesting levels in `tests/integration/test_variable_insertion.py`

### Implementation for User Story 3

- [ ] T037 [US3] Extend ScopeResolver with hierarchical path matching logic
- [ ] T038 [US3] Update NodeNetworkBuilder to track hierarchical paths during network building
- [ ] T039 [US3] Update SubstitutionContext model to include hierarchical_path field
- [ ] T040 [US3] Update VariableSubstitutor precedence logic: path > node > simple
- [ ] T041 [US3] Add AICODE-NOTE explaining path construction and matching strategy

**Checkpoint**: All three scoping levels work together with correct precedence

---

## Phase 6: Export Function Integration

**Goal**: Enable variable substitution in export_version() for file-first mode

- [ ] T042 [P] [Export] Unit test for export with variables in `tests/unit/versioning/test_exporter.py`
- [ ] T043 [P] [Export] Integration test for versioned export with variables in `tests/integration/versioning/test_version_export.py`
- [ ] T044 [Export] Update `src/promptic/sdk/api.py` - add `vars` parameter to `export_version()`
- [ ] T045 [Export] Update `src/promptic/versioning/domain/exporter.py` - integrate VariableSubstitutor
- [ ] T046 [Export] Ensure variables applied after version resolution but before file writing

**Checkpoint**: Variables work in both render and export functions

---

## Phase 7: Example 7 - Variable Insertion Demo

**Goal**: Create comprehensive example demonstrating all variable features

- [ ] T047 [P] [Example] Create `examples/get_started/7-variable-insertion/` directory
- [ ] T048 [P] [Example] Create `root.md` with simple and scoped variables
- [ ] T049 [P] [Example] Create `group/instructions.md` with node-scoped variables
- [ ] T050 [P] [Example] Create `templates/details.md` with path-scoped variables
- [ ] T051 [Example] Create `render.py` demonstrating all three scoping methods
- [ ] T052 [Example] Create `README.md` explaining the example structure and usage
- [ ] T053 [Example] Test example runs successfully and produces expected output

**Checkpoint**: Example 7 demonstrates complete variable insertion functionality

---

## Phase 8: Documentation

**Goal**: Comprehensive documentation for variable insertion feature

- [ ] T054 [P] [Docs] Create `docs_site/variables/` directory
- [ ] T055 [P] [Docs] Write `docs_site/variables/insertion-guide.md` with comprehensive examples
- [ ] T056 [P] [Docs] Update `README.md` with variable insertion quick start section
- [ ] T057 [P] [Docs] Add docstrings to all new classes and functions
- [ ] T058 [Docs] Verify all AICODE-NOTE comments are in place and clear

**Checkpoint**: Documentation covers all variable insertion features

---

## Phase 9: Polish & Quality Gates

**Goal**: Ensure code quality and test coverage

- [ ] T059 [P] [Quality] Run full test suite: `pytest tests/ -v`
- [ ] T060 [P] [Quality] Check coverage: `pytest tests/ --cov=promptic.context.variables --cov-report=term`
- [ ] T061 [P] [Quality] Format code: `black --line-length=100 src/promptic/context/variables/ tests/unit/variables/ tests/integration/test_variable_insertion.py`
- [ ] T062 [P] [Quality] Sort imports: `isort --profile=black --line-length=100 src/promptic/context/variables/ tests/unit/variables/ tests/integration/test_variable_insertion.py`
- [ ] T063 [Quality] Run pre-commit: `pre-commit run --all-files`
- [ ] T064 [Quality] Fix any linting/formatting issues
- [ ] T065 [Quality] Verify example 7 runs without errors
- [ ] T066 [Quality] Review all AICODE-NOTE comments for clarity

**Checkpoint**: All quality gates pass, ready for review

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - start immediately
- **Phase 2 (US1 - Simple)**: Depends on Phase 1 completion - FOUNDATIONAL
- **Phase 3 (US4 - Formats)**: Depends on Phase 2 completion - format support builds on basic substitution
- **Phase 4 (US2 - Node-scoped)**: Depends on Phase 2 completion - extends basic substitution
- **Phase 5 (US3 - Path-scoped)**: Depends on Phase 4 completion - extends node-scoped
- **Phase 6 (Export)**: Depends on Phase 5 completion - needs full substitution capability
- **Phase 7 (Example)**: Depends on Phase 6 completion - needs all features working
- **Phase 8 (Docs)**: Can start after Phase 2, complete after Phase 7
- **Phase 9 (Quality)**: Depends on all phases complete

### Parallel Opportunities

- All tests marked [P] can run in parallel
- All parser updates in Phase 3 can run in parallel
- All example files in Phase 7 can be created in parallel
- All documentation files in Phase 8 can be written in parallel
- All quality checks in Phase 9 can run in parallel

### Critical Path

1. Phase 1 → Phase 2 (MVP - basic substitution)
2. Phase 2 → Phase 3 (format support)
3. Phase 2 → Phase 4 (node scoping)
4. Phase 4 → Phase 5 (path scoping)
5. Phase 5 → Phase 6 (export integration)
6. Phase 6 → Phase 7 (example)
7. Phase 7 → Phase 9 (quality gates)

---

## Notes

- Tests MUST be written before implementation (TDD approach)
- Verify tests fail before implementing features
- Each user story should be independently testable
- Stop at checkpoints to validate functionality
- Use `AICODE-NOTE` for complex logic explanations
- Keep functions focused and <80 lines
