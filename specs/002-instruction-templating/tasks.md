# Tasks: Instruction Data Insertion with Multiple Templating Formats

**Input**: Design documents from `/specs/002-instruction-templating/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are MANDATORY under the `promptic Constitution`. List contract, integration, and unit coverage for every story before implementation, and ensure each test fails before the matching code exists.

**Organization**: Tasks are grouped by user story to enable independent implementation/testing while keeping Clean Architecture layers isolated.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project structure from plan.md

## Constitution Alignment Checklist

- [ ] Document how Entities → Use Cases → Interface adapters will be created/updated; prevent outward dependencies.
- [ ] Capture SOLID responsibilities for each new module and record deviations via `# AICODE-NOTE`.
- [ ] Plan documentation updates (`docs_site/`, specs, docstrings) and resolve any outstanding `# AICODE-ASK` items.
- [ ] Ensure readability: limit function/file size, adopt explicit naming, and remove dead code.
- [ ] Schedule pytest (unit, integration, contract) plus `pre-commit run --all-files` before requesting review.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize template rendering infrastructure and directory structure.

- [x] T001 Create `src/promptic/pipeline/format_renderers/` directory structure with `__init__.py` in `src/promptic/pipeline/format_renderers/__init__.py`
- [x] T002 [P] Add `jinja2>=3.0` and `regex` dependencies to `pyproject.toml` in project root
- [x] T003 [P] Create placeholder for `TemplateRenderError` exception in `src/promptic/context/errors.py` (extends existing error types)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core template rendering infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Define `FormatRenderer` interface (ABC) in `src/promptic/pipeline/format_renderers/base.py` with `render(content: str, context: InstructionRenderContext) -> str` and `supports_format(format: str) -> bool` methods
- [x] T005 [P] Create `InstructionRenderContext` dataclass in `src/promptic/context/template_context.py` with fields: `data: Dict[str, Any]`, `memory: Dict[str, Any]`, `step: Optional[StepContext]`, `blueprint: Dict[str, Any]`
- [x] T006 [P] Create `StepContext` dataclass in `src/promptic/context/template_context.py` with fields: `step_id: str`, `title: str`, `kind: str`, `hierarchy: List[str]`, `loop_item: Optional[Any]`
- [x] T007 [P] Implement `TemplateRenderError` exception class in `src/promptic/context/errors.py` with fields: `instruction_id: str`, `format: str`, `error_type: Literal[...]`, `message: str`, `line_number: Optional[int]`, `placeholder: Optional[str]`
- [x] T008 Implement `TemplateRenderer` dispatcher class in `src/promptic/pipeline/template_renderer.py` that routes to format-specific renderers based on `InstructionNode.format` field
- [x] T009 [P] Add helper function `build_instruction_context()` in `src/promptic/context/template_context.py` that constructs `InstructionRenderContext` from blueprint, data slots, memory slots, and step information with namespacing (`data.*`, `memory.*`, `step.*`)
- [x] T010 Modify `ContextPreviewer._resolve_instruction_text()` in `src/promptic/pipeline/previewer.py` to accept `template_context: InstructionRenderContext` parameter and route instruction content through `TemplateRenderer` before returning

**Checkpoint**: Foundation ready - template rendering infrastructure complete; user story implementation can now begin

---

## Phase 3: User Story 1 - Data Insertion in Markdown Instructions (Priority: P1) 🎯 MVP

**Goal**: Designers insert dynamic data into Markdown instruction files using Python string format syntax (`{}` placeholders) without needing YAML configuration files.

**Independent Test**: A designer can create a `.md` instruction file containing placeholders like `Process the item: {item_name}` and render it with data `{"item_name": "Task 1"}` to produce `Process the item: Task 1`. This can be tested independently with a single instruction file and a rendering function call.

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T011 [P] [US1] Contract test for format renderer interface compliance in `tests/contract/test_format_renderer_interface.py` verifying `MarkdownFormatRenderer` implements `FormatRenderer` interface
- [x] T012 [P] [US1] Unit test for Markdown placeholder rendering in `tests/unit/pipeline/test_template_renderer_markdown.py` covering simple placeholders, nested access (`{user.name}`), and escaping (`{{` → `{`)
- [x] T013 [P] [US1] Unit test for nested dictionary access in `tests/unit/pipeline/test_template_renderer_nested.py` covering deep nesting (up to 10 levels) and error handling for missing keys
- [x] T014 [P] [US1] Integration test for Markdown instruction rendering with data slots in `tests/integration/test_instruction_templating.py` verifying end-to-end rendering with blueprint context

### Implementation for User Story 1

- [x] T015 [US1] Implement `MarkdownFormatRenderer` class in `src/promptic/pipeline/format_renderers/markdown.py` implementing `FormatRenderer` interface with Python string format syntax (`{}` placeholders)
- [x] T016 [US1] Add nested dictionary access parser in `src/promptic/pipeline/format_renderers/markdown.py` that handles dot notation (`{user.profile.name}`) with traversal up to 10 levels deep
- [x] T017 [US1] Add escaping support in `src/promptic/pipeline/format_renderers/markdown.py` that converts `{{` to literal `{` and `}}` to literal `}`
- [x] T018 [US1] Add formatting preservation logic in `src/promptic/pipeline/format_renderers/markdown.py` that maintains indentation, line breaks, and whitespace when inserting data
- [x] T019 [US1] Register `MarkdownFormatRenderer` in `TemplateRenderer` dispatcher in `src/promptic/pipeline/template_renderer.py` for format `"md"`
- [x] T020 [US1] Add error handling in `MarkdownFormatRenderer` that raises `TemplateRenderError` with descriptive messages for missing placeholders, including line number and placeholder name
- [x] T021 [US1] Add logging instrumentation in `src/promptic/pipeline/format_renderers/markdown.py` with `# AICODE-NOTE` documenting format detection and rendering strategy
- [x] T022 [US1] Create example directory `examples/markdown-templating/` with `README.md`, sample instruction file `instruction.md`, and runnable Python script `render_example.py` demonstrating Markdown templating
- [x] T023 [US1] Write documentation guide `docs_site/context-engineering/markdown-templating.md` covering Markdown data insertion syntax, nested access, escaping, and examples

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Markdown instructions can be rendered with data placeholders.

---

## Phase 4: User Story 2 - Jinja2 Templating for Complex Logic (Priority: P2)

**Goal**: Designers use Jinja2 templating syntax in `.jinja` instruction files for conditional logic, loops, and complex data transformations without needing external YAML configuration.

**Independent Test**: A designer can create a `.jinja` instruction file with conditional blocks like `{% if condition %}...{% endif %}` and render it with context data. This can be tested independently with a single `.jinja` file and a rendering function.

### Tests for User Story 2 (MANDATORY) ⚠️

- [x] T024 [P] [US2] Unit test for Jinja2 template rendering in `tests/unit/pipeline/test_template_renderer_jinja2.py` covering conditionals, loops, filters, and variable interpolation
- [x] T025 [P] [US2] Unit test for Jinja2 environment configuration in `tests/unit/pipeline/test_template_renderer_jinja2.py` verifying separate environment from prompt rendering with shared base config
- [x] T026 [P] [US2] Unit test for context variable namespacing in `tests/unit/pipeline/test_template_renderer_context.py` verifying `data.*`, `memory.*`, `step.*` variables are accessible in Jinja2 templates
- [x] T027 [P] [US2] Integration test for Jinja2 instruction rendering with conditional logic and loops in `tests/integration/test_instruction_templating.py` extending existing test file
- [x] T028 [P] [US2] Unit test for error handling with `InstructionFallbackPolicy` in `tests/unit/pipeline/test_template_renderer_errors.py` covering `error`, `warn`, and `noop` policies for Jinja2 syntax errors

### Implementation for User Story 2

- [x] T029 [US2] Implement `Jinja2FormatRenderer` class in `src/promptic/pipeline/format_renderers/jinja2.py` implementing `FormatRenderer` interface
- [x] T030 [US2] Create separate Jinja2 environment factory in `src/promptic/pipeline/format_renderers/jinja2.py` that builds instruction-specific environment with shared base configuration from settings
- [x] T031 [US2] Add instruction-specific filters and globals to Jinja2 environment in `src/promptic/pipeline/format_renderers/jinja2.py` (e.g., `format_step()`, `get_parent_step()`) with `# AICODE-NOTE` documenting environment setup
- [x] T032 [US2] Implement context variable injection in `Jinja2FormatRenderer` that provides namespaced variables (`data.*`, `memory.*`, `step.*`) to templates
- [x] T033 [US2] Add error handling in `Jinja2FormatRenderer` that respects `InstructionFallbackPolicy` (raises `TemplateRenderError` for `error` policy, emits warnings for `warn` policy, returns empty string for `noop` policy)
- [x] T034 [US2] Register `Jinja2FormatRenderer` in `TemplateRenderer` dispatcher in `src/promptic/pipeline/template_renderer.py` for format `"jinja"`
- [x] T035 [US2] Add lazy initialization for Jinja2 environment in `Jinja2FormatRenderer` (created on first use) with `# AICODE-NOTE` documenting performance considerations
- [x] T036 [US2] Create example directory `examples/jinja2-templating/` with `README.md`, sample instruction file `instruction.jinja`, and runnable Python script `render_example.py` demonstrating Jinja2 templating
- [x] T037 [US2] Write documentation guide `docs_site/context-engineering/jinja2-templating.md` covering Jinja2 syntax, available filters/globals, context variables, and examples
- [x] T038 [US2] Add `# AICODE-NOTE` comments in `src/promptic/pipeline/format_renderers/jinja2.py` documenting separate environment setup, instruction-specific filters/globals, and available namespaced context variables

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Jinja2 instructions can be rendered with conditional logic and loops.

---

## Phase 5: User Story 3 - Custom Pattern Templating in YAML Instructions (Priority: P3)

**Goal**: Designers define custom placeholder patterns in YAML instruction files through configuration parameters, allowing flexible templating syntax that adapts to specific use cases.

**Independent Test**: A designer can create a YAML instruction file with a `pattern` field like `pattern: "{{name}}"` and render it with data `{"name": "value"}` to replace the custom pattern. This can be tested independently with a YAML file and custom pattern configuration.

### Tests for User Story 3 (MANDATORY) ⚠️

- [x] T039 [P] [US3] Unit test for YAML custom pattern rendering in `tests/unit/pipeline/test_template_renderer_yaml.py` covering various pattern formats and replacement semantics
- [x] T040 [P] [US3] Unit test for pattern validation in `tests/unit/pipeline/test_template_renderer_yaml.py` verifying regex patterns and safe string replacement
- [x] T041 [P] [US3] Unit test for pattern collision detection in `tests/unit/pipeline/test_template_renderer_yaml.py` covering escape mechanisms and validation warnings
- [x] T042 [P] [US3] Integration test for YAML pattern rendering in `tests/integration/test_format_detection.py` extending existing test file

### Implementation for User Story 3

- [x] T043 [US3] Add optional `pattern` field to `InstructionNode` model in `src/promptic/blueprints/models.py` with validation for regex patterns or safe string replacement
- [x] T044 [US3] Implement `YamlFormatRenderer` class in `src/promptic/pipeline/format_renderers/yaml.py` implementing `FormatRenderer` interface
- [x] T045 [US3] Add pattern-based substitution logic in `YamlFormatRenderer` that uses regex or string replacement based on configured pattern from `InstructionNode.pattern`
- [x] T046 [US3] Add pattern validation in `YamlFormatRenderer` that ensures patterns are valid regex or provide safe string replacement semantics, raising validation warnings during instruction loading if invalid
- [x] T047 [US3] Add escape mechanism support in `YamlFormatRenderer` for handling pattern collisions with literal text in instruction content
- [x] T048 [US3] Register `YamlFormatRenderer` in `TemplateRenderer` dispatcher in `src/promptic/pipeline/template_renderer.py` for formats `"yaml"` and `"yml"`
- [x] T049 [US3] Add `# AICODE-NOTE` comments in `src/promptic/pipeline/format_renderers/yaml.py` documenting pattern configuration and escaping rules
- [x] T050 [US3] Create example directory `examples/yaml-patterns/` with `README.md`, sample instruction file `instruction.yaml`, and runnable Python script `render_example.py` demonstrating YAML custom patterns
- [x] T051 [US3] Write documentation guide `docs_site/context-engineering/yaml-templating.md` covering custom pattern configuration, validation, escaping, and examples

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently. YAML instructions can be rendered with custom placeholder patterns.

---

## Phase 6: User Story 4 - Hierarchical Logic in Markdown Files (Priority: P3)

**Goal**: Designers express hierarchical logic and conditional rendering directly in Markdown instruction files using a lightweight syntax extension, reducing reliance on YAML blueprints for simple scenarios.

**Independent Test**: A designer can create a Markdown instruction file with hierarchical markers like `## Step 1` followed by `### Sub-step 1.1` and the system recognizes the hierarchy. This can be tested independently by parsing a Markdown file and extracting its structure.

### Tests for User Story 4 (MANDATORY) ⚠️

- [x] T052 [P] [US4] Unit test for Markdown hierarchy parsing in `tests/unit/pipeline/test_template_renderer_markdown.py` extending existing test file to cover heading-based hierarchy extraction
- [x] T053 [P] [US4] Unit test for conditional marker parsing in `tests/unit/pipeline/test_template_renderer_markdown.py` covering `<!-- if:condition -->` markers and section inclusion/exclusion
- [x] T054 [P] [US4] Integration test for hierarchical Markdown rendering in `tests/integration/test_instruction_templating.py` extending existing test file

### Implementation for User Story 4

- [x] T055 [US4] Implement `MarkdownHierarchyParser` class in `src/promptic/pipeline/format_renderers/markdown_hierarchy.py` with `parse(content: str) -> MarkdownHierarchy` method
- [x] T056 [US4] Add heading-based hierarchy extraction in `MarkdownHierarchyParser` that recognizes parent-child relationships from heading levels (`##`, `###`, etc.)
- [x] T057 [US4] Add conditional marker extraction in `MarkdownHierarchyParser` with `extract_conditionals(content: str) -> List[ConditionalSection]` method for `<!-- if:condition -->` markers
- [x] T058 [US4] Integrate `MarkdownHierarchyParser` into instruction loading flow (optional, runs during instruction loading) producing structured metadata that informs rendering decisions
- [x] T059 [US4] Add conditional section rendering logic that includes/excludes sections based on context data during template rendering
- [x] T060 [US4] Add `# AICODE-NOTE` comments in `src/promptic/pipeline/format_renderers/markdown_hierarchy.py` documenting hierarchy syntax and parsing strategy
- [x] T061 [US4] Create example directory `examples/hierarchical-markdown/` with `README.md`, sample instruction file `instruction.md` with hierarchical structure, and runnable Python script `render_example.py`
- [x] T062 [US4] Write documentation guide `docs_site/context-engineering/hierarchical-markdown.md` covering hierarchy syntax, conditional markers, and examples

**Checkpoint**: At this point, all user stories should work independently. Markdown instructions can express hierarchical logic and conditional rendering.

---

## Phase 7: Loop Step Per-Iteration Context (Clarification 4)

**Purpose**: Implement per-iteration rendering for loop steps with `step.loop_item` context variable.

- [x] T063 [P] Add per-iteration context building logic in `build_instruction_context()` in `src/promptic/context/template_context.py` that includes `step.loop_item` for loop steps
- [x] T064 [P] Add integration test for loop step per-iteration rendering in `tests/integration/test_loop_iteration_templating.py` verifying instructions render with different `step.loop_item` for each iteration
- [x] T065 Update documentation in `docs_site/context-engineering/template-context-variables.md` covering `step.loop_item` usage in loop steps

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories, documentation, and quality gates.

- [x] T066 [P] Write context variables reference guide `docs_site/context-engineering/template-context-variables.md` documenting all namespaced variables (`data.*`, `memory.*`, `step.*`, `blueprint.*`) with examples
- [x] T067 [P] Update integration analysis document `specs/002-instruction-templating/integration-analysis.md` with implementation notes and resolved clarifications
- [x] T068 [P] Add contract test for context variable availability in `tests/contract/test_template_context_contract.py` verifying all documented context variables are accessible
- [x] T069 [P] Add contract test for format detection and routing in `tests/contract/test_format_renderer_interface.py` extending existing test file
- [x] T070 Harden error messages and exception mapping across template rendering modules in `src/promptic/context/errors.py` and format renderers
- [x] T071 [P] Optimize template rendering hot paths (Markdown parsing, Jinja2 environment reuse) and add performance benchmarks in `tests/integration/test_template_performance.py`
- [x] T072 [P] Expand unit test coverage for uncovered branches reported by coverage in `tests/unit/pipeline/`
- [x] T073 Run `quickstart.md` end-to-end validation and capture output snapshots in `docs_site/context-engineering/`
- [x] T074 Execute `pytest -m "unit or integration or contract"` and `pre-commit run --all-files`; attach evidence to PR
- [x] T075 Close any outstanding `# AICODE-ASK` items and document answers as `# AICODE-NOTE` comments
- [x] T076 Finalize documentation updates in `docs_site/context-engineering/` for all templating formats

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can proceed in priority order (P1 → P2 → P3)
  - Or in parallel if team capacity allows (each story is independently testable)
- **Loop Context (Phase 7)**: Can proceed in parallel with user stories once Foundational is complete
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Builds on TemplateRenderer from US1 but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Builds on TemplateRenderer from US1 but independently testable
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Extends MarkdownFormatRenderer from US1 but independently testable

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Format renderer implementation before registration
- Core rendering logic before error handling
- Error handling before integration
- Examples and docs after implementation
- Story complete before moving to next priority

### Parallel Opportunities

- **Setup phase**: T002, T003 can run in parallel
- **Foundational phase**: T005, T006, T007, T009 can run in parallel
- **User Story 1 tests**: T011, T012, T013, T014 can run in parallel
- **User Story 2 tests**: T024, T025, T026, T027, T028 can run in parallel
- **User Story 3 tests**: T039, T040, T041, T042 can run in parallel
- **User Story 4 tests**: T052, T053, T054 can run in parallel
- **Different user stories**: Can be worked on in parallel by different team members after Foundational phase
- **Polish phase**: T066, T067, T068, T069, T071, T072 can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
pytest tests/contract/test_format_renderer_interface.py -v
pytest tests/unit/pipeline/test_template_renderer_markdown.py -v
pytest tests/unit/pipeline/test_template_renderer_nested.py -v
pytest tests/integration/test_instruction_templating.py -v

# Implementation can proceed after tests are written (and failing)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Markdown templating)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Markdown) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (Jinja2) → Test independently → Deploy/Demo
4. Add User Story 3 (YAML patterns) → Test independently → Deploy/Demo
5. Add User Story 4 (Markdown hierarchy) → Test independently → Deploy/Demo
6. Add Loop Context (Phase 7) → Test independently → Deploy/Demo
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Markdown - P1 MVP)
   - Developer B: User Story 2 (Jinja2 - P2)
   - Developer C: User Story 3 (YAML - P3) or User Story 4 (Markdown hierarchy - P3)
3. Stories complete and integrate independently
4. Polish phase can proceed in parallel with later user stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Integration point: `ContextPreviewer._resolve_instruction_text()` modification (T010) is critical for all user stories
- Context variable namespacing (`data.*`, `memory.*`, `step.*`) must be consistent across all format renderers
- Separate Jinja2 environment for instructions (shared base config) enables instruction-specific filters without affecting prompt rendering
- Error handling via `InstructionFallbackPolicy` provides consistent behavior across all format renderers
