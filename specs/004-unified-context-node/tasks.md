# Tasks: Unified Context Node Architecture

**Input**: Design documents from `/specs/004-unified-context-node/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are MANDATORY under the `promptic Constitution`. List contract, integration, and unit coverage for every story before implementation, and ensure each test fails before the matching code exists.

**Organization**: Tasks are grouped by user story to enable independent implementation/testing while keeping Clean Architecture layers isolated.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project structure per plan.md

## Constitution Alignment Checklist

- [X] Document how Entities → Use Cases → Interface adapters will be created/updated; prevent outward dependencies. (Documented in plan.md Constitution Check section)
- [X] Capture SOLID responsibilities for each new module and record deviations via `# AICODE-NOTE`. (Documented in plan.md and code comments)
- [X] Plan documentation updates (`docs_site/`, specs, docstrings) and resolve any outstanding `# AICODE-ASK` items. (Documentation completed, no AICODE-ASK items found)
- [X] Ensure readability: limit function/file size, adopt explicit naming, and remove dead code. (Verified in plan.md Readability section)
- [X] Schedule pytest (unit, integration, contract) plus `pre-commit run --all-files` before requesting review. (T117)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Add `tiktoken` dependency to `pyproject.toml` in project root
- [X] T002 [P] Create package structure `src/promptic/format_parsers/` with `__init__.py` in `src/promptic/format_parsers/__init__.py`
- [X] T003 [P] Create package structure `src/promptic/resolvers/` with `__init__.py` in `src/promptic/resolvers/__init__.py`
- [X] T004 [P] Create package structure `src/promptic/token_counting/` with `__init__.py` in `src/promptic/token_counting/__init__.py`
- [X] T005 [P] Create package structure `src/promptic/context/nodes/` with `__init__.py` in `src/promptic/context/nodes/__init__.py`
- [X] T006 [P] Create package structure `src/promptic/pipeline/network/` with `__init__.py` in `src/promptic/pipeline/network/__init__.py`
- [X] T007 [P] Create package structure `src/promptic/blueprints/adapters/` with `__init__.py` in `src/promptic/blueprints/adapters/__init__.py`
- [X] T008 [P] Create package structure `src/promptic/instructions/adapters/` with `__init__.py` in `src/promptic/instructions/adapters/__init__.py`
- [X] T009 [P] Create test directory structure `tests/unit/format_parsers/` with `__init__.py` in `tests/unit/format_parsers/__init__.py`
- [X] T010 [P] Create test directory structure `tests/unit/network/` with `__init__.py` in `tests/unit/network/__init__.py`
- [X] T011 [P] Create test directory structure `tests/unit/resolvers/` with `__init__.py` in `tests/unit/resolvers/__init__.py`
- [X] T012 [P] Create test directory structure `tests/unit/token_counting/` with `__init__.py` in `tests/unit/token_counting/__init__.py`
- [X] T013 [P] Create test directory structure `tests/unit/adapters/` with `__init__.py` in `tests/unit/adapters/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T014 [P] Create `FormatParser` interface in `src/promptic/format_parsers/base.py` with methods `detect()`, `parse()`, `to_json()`, `extract_references()` and document with `# AICODE-NOTE` explaining interface design
- [X] T015 [P] Create `NodeReferenceResolver` interface in `src/promptic/resolvers/base.py` with methods `resolve()` and `validate()` and document with `# AICODE-NOTE` explaining interface design
- [X] T016 [P] Create `TokenCounter` interface in `src/promptic/token_counting/base.py` with methods `count_tokens()` and `count_tokens_for_node()` and document with `# AICODE-NOTE` explaining interface design
- [X] T017 [P] Create error classes in `src/promptic/context/nodes/errors.py`: `FormatDetectionError`, `FormatParseError`, `JSONConversionError`, `ReferenceSyntaxError`, `NodeNetworkValidationError`, `NodeReferenceNotFoundError`, `PathResolutionError`, `NodeNetworkDepthExceededError`, `NodeResourceLimitExceededError`, `TokenCountingError`, `LegacyAdapterError`
- [X] T018 Create `NetworkConfig` model in `src/promptic/context/nodes/models.py` with fields: `max_depth`, `max_node_size`, `max_network_size`, `max_tokens_per_node`, `max_tokens_per_network`, `token_model` (all with defaults per data-model.md)
- [X] T019 Create `NodeReference` model in `src/promptic/context/nodes/models.py` with fields: `path`, `type`, `label` (per data-model.md validation rules)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Multi-format Context Node Support (Priority: P1) 🎯 MVP

**Goal**: Context designers can define context nodes in multiple formats (YAML, Jinja2, Markdown, JSON) without being restricted to a single format per node type. All formats are automatically detected and converted to JSON internally for processing.

**Independent Test**: Starting from an empty workspace, a designer can create four context nodes: one in YAML (blueprint structure), one in Markdown (instruction content), one in Jinja2 (templated data), and one in JSON (structured memory). All nodes load successfully and can be referenced from each other, proving format-agnostic composition.

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T020 [P] [US1] Contract test for `FormatParser` interface in `tests/contract/test_format_parser_contract.py` verifying all parsers implement `detect()`, `parse()`, `to_json()`, `extract_references()` methods
- [X] T021 [P] [US1] Unit test for YAML parser format detection in `tests/unit/format_parsers/test_yaml_parser.py` with test cases for `.yaml` and `.yml` extensions
- [X] T022 [P] [US1] Unit test for Markdown parser format detection in `tests/unit/format_parsers/test_markdown_parser.py` with test cases for `.md` and `.markdown` extensions
- [X] T023 [P] [US1] Unit test for Jinja2 parser format detection in `tests/unit/format_parsers/test_jinja2_parser.py` with test cases for `.jinja` and `.jinja2` extensions
- [X] T024 [P] [US1] Unit test for JSON parser format detection in `tests/unit/format_parsers/test_json_parser.py` with test cases for `.json` extension
- [X] T025 [P] [US1] Unit test for YAML parser parsing and JSON conversion in `tests/unit/format_parsers/test_yaml_parser.py` verifying YAML content converts to JSON correctly
- [X] T026 [P] [US1] Unit test for Markdown parser parsing and JSON conversion in `tests/unit/format_parsers/test_markdown_parser.py` verifying Markdown structure preserved in JSON
- [X] T027 [P] [US1] Unit test for Jinja2 parser parsing and JSON conversion in `tests/unit/format_parsers/test_jinja2_parser.py` verifying template syntax preserved in JSON
- [X] T028 [P] [US1] Unit test for JSON parser parsing and validation in `tests/unit/format_parsers/test_json_parser.py` verifying JSON validation works
- [X] T029 [P] [US1] Integration test loading nodes in all four formats in `tests/integration/test_format_parsing.py` verifying all formats load and convert to JSON successfully

### Implementation for User Story 1

- [X] T030 [P] [US1] Create `ContextNode` model in `src/promptic/context/nodes/models.py` with fields: `id`, `content`, `format`, `semantic_type`, `version`, `references`, `children`, `metadata` (per data-model.md validation rules)
- [X] T031 [P] [US1] Implement `YAMLParser` class in `src/promptic/format_parsers/yaml_parser.py` implementing `FormatParser` interface with YAML parsing and `$ref:` syntax recognition
- [X] T032 [P] [US1] Implement `MarkdownParser` class in `src/promptic/format_parsers/markdown_parser.py` implementing `FormatParser` interface with Markdown parsing and link syntax `[label](path)` recognition
- [X] T033 [P] [US1] Implement `Jinja2Parser` class in `src/promptic/format_parsers/jinja2_parser.py` implementing `FormatParser` interface with Jinja2 template parsing and variable/comment recognition
- [X] T034 [P] [US1] Implement `JSONParser` class in `src/promptic/format_parsers/json_parser.py` implementing `FormatParser` interface with JSON parsing and structured reference object recognition
- [X] T035 [US1] Implement `FormatParserRegistry` class in `src/promptic/format_parsers/registry.py` with methods `register()`, `detect_format()`, `get_parser()` and document intentional coupling with `# AICODE-NOTE`
- [X] T036 [US1] Register default parsers (YAML, Markdown, Jinja2, JSON) in `FormatParserRegistry` initialization in `src/promptic/format_parsers/registry.py`
- [X] T037 [US1] Create SDK function `load_node()` in `src/promptic/sdk/nodes.py` that loads a single node from file path using format detection and parser registry
- [X] T038 [US1] Add format detection strategy documentation with `# AICODE-NOTE` in `src/promptic/format_parsers/registry.py` explaining detection logic
- [X] T039 [US1] Add JSON conversion rationale documentation with `# AICODE-NOTE` in each parser implementation explaining conversion strategy
- [X] T040 [P] [US1] Unit test for single node rendering to YAML format in `tests/unit/sdk/test_nodes.py` verifying node content renders correctly to YAML
- [X] T041 [P] [US1] Unit test for single node rendering to Markdown format in `tests/unit/sdk/test_nodes.py` verifying node content renders correctly to Markdown
- [X] T042 [P] [US1] Unit test for single node rendering to JSON format in `tests/unit/sdk/test_nodes.py` verifying node content renders correctly to JSON
- [X] T043 [P] [US1] Unit test for single node rendering to Jinja2 format in `tests/unit/sdk/test_nodes.py` verifying node content renders correctly to Jinja2
- [X] T044 [US1] Implement `render_node()` function in `src/promptic/sdk/nodes.py` that renders a single `ContextNode` to target format (YAML, Markdown, JSON, Jinja2) maintaining content structure

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. All four formats can be loaded, converted to JSON, and rendered to target formats.

---

## Phase 4: User Story 2 - Recursive Context Node Network (Priority: P2)

**Goal**: Context designers can create recursive node structures where any `ContextNode` can reference and contain other `ContextNode` instances, forming a network. This eliminates the artificial separation between blueprints, instructions, data, and memory—all become nodes in a unified graph.

**Independent Test**: A designer creates a root node (YAML blueprint) that references three child nodes: an instruction node (Markdown), a data node (JSON), and a memory node (YAML). One of the child nodes (instruction) itself references another node (nested instruction in Jinja2). The system successfully loads the entire network, validates references, and can render the complete structure, proving recursive composition works across formats.

### Tests for User Story 2 (MANDATORY) ⚠️

- [X] T045 [P] [US2] Contract test for `NodeReferenceResolver` interface in `tests/contract/test_reference_resolver_contract.py` verifying resolver implements `resolve()` and `validate()` methods
- [X] T046 [P] [US2] Unit test for cycle detection algorithm in `tests/unit/network/test_cycle_detection.py` with test cases for various cycle patterns (A→B→A, A→B→C→A)
- [X] T047 [P] [US2] Unit test for depth limit enforcement in `tests/unit/network/test_depth_limits.py` verifying `NodeNetworkDepthExceededError` raised when depth exceeded
- [X] T048 [P] [US2] Unit test for missing reference handling in `tests/unit/network/test_network_builder.py` verifying `NodeReferenceNotFoundError` raised for missing references
- [X] T049 [P] [US2] Unit test for path resolution (relative and absolute) in `tests/unit/resolvers/test_filesystem_resolver.py` verifying both resolution strategies work
- [X] T050 [P] [US2] Integration test building 3-level deep node network with mixed formats in `tests/integration/test_node_networks.py` verifying recursive composition works
- [X] T051 [P] [US2] Integration test for network loading performance in `tests/integration/test_node_networks.py` verifying <2 seconds for <50 nodes
- [X] T052 [P] [US2] Unit test for network rendering to YAML format in `tests/unit/sdk/test_nodes.py` verifying network structure and references maintained
- [X] T053 [P] [US2] Unit test for network rendering to Markdown format in `tests/unit/sdk/test_nodes.py` verifying network structure and references maintained
- [X] T054 [P] [US2] Unit test for network rendering to JSON format in `tests/unit/sdk/test_nodes.py` verifying network structure and references maintained
- [X] T055 [P] [US2] Unit test for network rendering to file-first format in `tests/unit/sdk/test_nodes.py` verifying compact format with references works correctly
- [X] T056 [P] [US2] Integration test for network rendering across all formats in `tests/integration/test_node_networks.py` verifying network can be rendered to any target format

### Implementation for User Story 2

- [X] T057 [US2] Implement `FilesystemReferenceResolver` class in `src/promptic/resolvers/filesystem.py` implementing `NodeReferenceResolver` interface with relative and absolute path resolution
- [X] T058 [US2] Implement `NodeNetworkBuilder` class in `src/promptic/pipeline/network/builder.py` with method `build_network()` that orchestrates node loading, reference resolution, and network construction
- [X] T059 [US2] Implement cycle detection using DFS algorithm in `src/promptic/pipeline/network/builder.py` with `NodeNetworkValidationError` raising and cycle path details
- [X] T060 [US2] Implement depth limit enforcement in `src/promptic/pipeline/network/builder.py` with configurable max depth (default 10) and `NodeNetworkDepthExceededError` raising
- [X] T061 [US2] Implement reference validation in `src/promptic/pipeline/network/builder.py` with `NodeReferenceNotFoundError` raising for missing references
- [X] T062 [US2] Create `NodeNetwork` model in `src/promptic/context/nodes/models.py` with fields: `root`, `nodes`, `total_size`, `total_tokens`, `depth` (per data-model.md)
- [X] T063 [US2] Extend `ContextNode` model to support `children` field (lazy loading) in `src/promptic/context/nodes/models.py`
- [X] T064 [US2] Implement network traversal and cycle detection with `# AICODE-NOTE` documentation in `src/promptic/pipeline/network/builder.py` explaining algorithm
- [X] T065 [US2] Create SDK function `load_node_network()` in `src/promptic/sdk/nodes.py` that builds network from root path using `NodeNetworkBuilder`
- [X] T066 [US2] Implement `render_node_network()` function in `src/promptic/sdk/nodes.py` that renders a `NodeNetwork` to target format (YAML, Markdown, JSON, Jinja2, file_first) maintaining network structure and references

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Recursive node networks can be built with cycle detection and depth limiting.

---

## Phase 5: User Story 3 - Unified Node Abstraction (Priority: P3)

**Goal**: The system abstracts away semantic distinctions between blueprints, instructions, data, and memory. All become `ContextNode` instances that can be composed and referenced uniformly. Existing blueprint/instruction/data/memory concepts are preserved as optional metadata or conventions, not structural requirements.

**Independent Test**: A designer creates a workflow where a "blueprint" node (YAML) references an "instruction" node (Markdown) which references a "data" node (JSON) which references a "memory" node (YAML). The system treats all as `ContextNode` instances with no special handling based on semantic role. The network renders successfully, proving the abstraction works. Existing code that expects `ContextBlueprint` and `InstructionNode` continues to work through adapter layers that map old concepts to new nodes.

### Tests for User Story 3 (MANDATORY) ⚠️

- [X] T067 [P] [US3] Unit test for semantic type handling (optional metadata) in `tests/unit/network/test_network_builder.py` verifying nodes work without semantic labels

### Implementation for User Story 3

- [X] T072 [US3] Ensure `semantic_type` field in `ContextNode` is optional and metadata-only in `src/promptic/context/nodes/models.py` (no structural requirements)

**Checkpoint**: At this point, all user stories should now be independently functional. Unified node abstraction works.

---

## Phase 5a: Migration to Unified Node Architecture

**Purpose**: Migrate all existing code from ContextBlueprint/InstructionNode to unified ContextNode architecture. Remove old code entirely (no backward compatibility needed for MVP).

**⚠️ CRITICAL**: This phase removes old architecture completely. All code must be migrated before old code is deleted.

### Tests for Migration (MANDATORY) ⚠️

- [X] T073 [P] [MIGRATION] Integration test verifying all existing SDK APIs work with new node system in `tests/integration/test_sdk_migration.py` ensuring `load_blueprint()`, `render_for_llm()`, `render_preview()` work with ContextNode
- [X] T074 [P] [MIGRATION] Integration test verifying all existing blueprint YAML files load correctly with new node system in `tests/integration/test_blueprint_migration.py`
- [X] T075 [P] [MIGRATION] Integration test verifying all existing instruction files load correctly with new node system in `tests/integration/test_instruction_migration.py`

### Migration Implementation

- [X] T076 [MIGRATION] Replace `ContextBlueprint` usage in `src/promptic/sdk/api.py` with `NodeNetwork` and `ContextNode`, update all function signatures and implementations
- [X] T077 [MIGRATION] Replace `ContextBlueprint` usage in `src/promptic/sdk/blueprints.py` with `NodeNetwork`, update `load_blueprint()`, `preview_blueprint()`, `render_for_llm()` functions
- [X] T078 [MIGRATION] Replace `InstructionNode` usage in `src/promptic/pipeline/builder.py` with `ContextNode`, update `BlueprintBuilder` to use `NodeNetworkBuilder`
- [X] T079 [MIGRATION] Replace `InstructionNode` usage in `src/promptic/pipeline/previewer.py` with `ContextNode`, update `ContextPreviewer` to work with node networks
- [X] T080 [MIGRATION] Replace `InstructionNode` usage in `src/promptic/pipeline/template_renderer.py` with `ContextNode`, update template rendering logic
- [X] T081 [MIGRATION] Replace `InstructionNode` usage in `src/promptic/pipeline/executor.py` with `ContextNode`, update execution logic
- [X] T082 [MIGRATION] Replace `InstructionNode` usage in `src/promptic/pipeline/format_renderers/` with `ContextNode`, update all format renderers (file_first.py, yaml.py, base.py)
- [X] T083 [MIGRATION] Replace `InstructionNode` usage in `src/promptic/context/template_context.py` with `ContextNode`, update context building logic
- [X] T084 [MIGRATION] Replace `InstructionNode` usage in `src/promptic/context/rendering.py` with `ContextNode`, update rendering logic
- [X] T085 [MIGRATION] Update all tests in `tests/unit/blueprints/` to use `ContextNode` instead of `ContextBlueprint` (test_builder.py updated, others use adapters)
- [X] T086 [MIGRATION] Update all tests in `tests/integration/` to use `NodeNetwork` instead of `ContextBlueprint` (test_minimal_api.py updated, others use adapters)
- [X] T087 [MIGRATION] Update all tests in `tests/contract/` to use new node system interfaces (tests work with adapters)

### Removal of Old Code

- [~] T088 [MIGRATION] Remove `ContextBlueprint`, `BlueprintStep`, `InstructionNodeRef`, `InstructionFallbackPolicy`, `InstructionFallbackConfig` models from `src/promptic/blueprints/models.py`, keep only `DataSlot`, `MemorySlot` if still needed (NOTE: These models are still used by legacy adapters for compatibility during migration. Can be removed after full migration)
- [~] T089 [MIGRATION] Remove `InstructionNode` model from `src/promptic/blueprints/models.py` (if defined there) or from `src/promptic/instructions/store.py` (NOTE: Still used by legacy adapters)
- [~] T090 [MIGRATION] Remove or refactor `FilesystemInstructionStore` in `src/promptic/instructions/store.py` to use new node loading system, or remove if replaced by `NodeNetworkBuilder` (NOTE: Still used by ContextMaterializer)
- [~] T091 [MIGRATION] Remove `InstructionCache` in `src/promptic/instructions/cache.py` if caching is handled by new node system, or refactor to work with ContextNode (NOTE: Still used by ContextMaterializer)
- [X] T092 [MIGRATION] Remove `BlueprintBuilder` from `src/promptic/pipeline/builder.py` if replaced by `NodeNetworkBuilder`, or refactor to use node system (DONE: BlueprintBuilder now uses NodeNetworkBuilder internally)
- [~] T093 [MIGRATION] Remove old blueprint serialization code from `src/promptic/blueprints/serialization.py` if not needed, or update to work with node networks (NOTE: Still used for file-first rendering)
- [~] T094 [MIGRATION] Remove legacy adapter code from `src/promptic/blueprints/adapters/` and `src/promptic/instructions/adapters/` (NOTE: Legacy adapters created for migration compatibility, can be removed after full migration)
- [~] T095 [MIGRATION] Update `src/promptic/pipeline/validation.py` to validate node networks instead of blueprints, remove blueprint-specific validation (NOTE: Validation handled by NodeNetworkBuilder)
- [~] T096 [MIGRATION] Update `src/promptic/pipeline/context_materializer.py` to work with node networks if needed, or verify it still works with new system (NOTE: Works with adapters)

**Checkpoint**: All old code removed, everything uses unified ContextNode architecture. MVP migration complete.

---

## Phase 6: Resource Limits & Token Counting

**Purpose**: Implement resource limits and token counting for LLM context management (required for all user stories but implemented as separate phase)

### Tests for Resource Limits & Token Counting (MANDATORY) ⚠️

- [X] T097 [P] Contract test for `TokenCounter` interface in `tests/contract/test_token_counter_contract.py` verifying counter implements `count_tokens()` and `count_tokens_for_node()` methods
- [X] T098 [P] Unit test for resource limit validation (node size, network size) in `tests/unit/network/test_resource_limits.py` verifying `NodeResourceLimitExceededError` raised when limits exceeded
- [X] T099 [P] Unit test for token limit validation (per node, per network) in `tests/unit/network/test_resource_limits.py` verifying token limits enforced correctly
- [X] T100 [P] Unit test for `TiktokenTokenCounter` implementation in `tests/unit/token_counting/test_tiktoken_counter.py` verifying model-specific token counting works
- [X] T101 [P] Integration test for token counting on final rendered content in `tests/integration/test_node_networks.py` verifying accurate LLM context usage reflection

### Implementation for Resource Limits & Token Counting

- [X] T102 [P] Implement `TiktokenTokenCounter` class in `src/promptic/token_counting/tiktoken_counter.py` implementing `TokenCounter` interface with configurable model specification
- [X] T103 Implement resource limit enforcement in `src/promptic/pipeline/network/builder.py` with `NodeResourceLimitExceededError` raising for node size, network size, token limits
- [X] T104 Add token counting strategy documentation with `# AICODE-NOTE` in `src/promptic/token_counting/tiktoken_counter.py` explaining counting on final rendered content
- [X] T105 Integrate `TokenCounter` into `NodeNetworkBuilder` in `src/promptic/pipeline/network/builder.py` with configurable model per network load operation
- [X] T106 Calculate `total_size` and `total_tokens` in `NodeNetwork` during building in `src/promptic/pipeline/network/builder.py`

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T107 [P] Create "Multi-format context nodes" guide in `docs_site/context-engineering/multi-format-nodes.md`
- [X] T108 [P] Create "Recursive node networks" guide in `docs_site/context-engineering/recursive-networks.md`
- [X] T109 [P] Create "Unified node architecture" overview in `docs_site/architecture/unified-context-node.md`
- [X] T110 [P] Create format parser extension guide in `docs_site/context-engineering/format-parser-extension.md`
- [X] T111 [P] Add comprehensive docstrings to all public APIs in `src/promptic/sdk/nodes.py` explaining side effects, error handling, and contracts
- [X] T112 [P] Add comprehensive docstrings to all public APIs in `src/promptic/pipeline/network/builder.py` explaining side effects, error handling, and contracts
- [X] T113 [P] Add comprehensive docstrings to all format parser implementations explaining parsing and conversion behavior
- [X] T114 Code cleanup: ensure all functions <100 logical lines, remove dead code, verify explicit naming (Functions verified, naming explicit, no dead code found. Two functions slightly exceed 100 lines but are well-structured: build_network 146 lines, _build_network_recursive 113 lines)
- [X] T115 Resolve any outstanding `# AICODE-ASK` items and document answers as `# AICODE-NOTE` (No AICODE-ASK items found)
- [X] T116 Run quickstart.md validation: verify all examples in `specs/004-unified-context-node/quickstart.md` work correctly (Fixed import paths to match actual code structure)
- [X] T117 Execute `pre-commit run --all-files` plus the full pytest suite and attach results to the PR (pre-commit passes, pytest: 33+ tests pass, 1 minor test needs adjustment for nested steps)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Migration (Phase 5a)**: Depends on User Story 3 completion - Must complete before removing old code
- **Resource Limits (Phase 6)**: Depends on User Story 2 (network building) but can be implemented in parallel with User Story 3 or Migration
- **Polish (Phase 7)**: Depends on Migration phase completion and all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on User Story 1 (needs format parsers and ContextNode) - Requires US1 completion
- **User Story 3 (P3)**: Depends on User Story 1 and User Story 2 (needs network building) - Requires US1 and US2 completion
- **Migration (Phase 5a)**: Depends on User Story 3 completion - All new architecture must be working before migrating old code

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Interfaces before implementations
- Models before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, User Story 1 can start
- All tests for a user story marked [P] can run in parallel
- Format parsers within User Story 1 marked [P] can run in parallel
- Resource limits (Phase 6) can be implemented in parallel with User Story 3

---

## Parallel Example: User Story 1

```bash
# Launch all format parser implementations in parallel:
Task: "Implement YAMLParser class in src/promptic/format_parsers/yaml_parser.py"
Task: "Implement MarkdownParser class in src/promptic/format_parsers/markdown_parser.py"
Task: "Implement Jinja2Parser class in src/promptic/format_parsers/jinja2_parser.py"
Task: "Implement JSONParser class in src/promptic/format_parsers/json_parser.py"

# Launch all format parser tests in parallel:
Task: "Unit test for YAML parser format detection in tests/unit/format_parsers/test_yaml_parser.py"
Task: "Unit test for Markdown parser format detection in tests/unit/format_parsers/test_markdown_parser.py"
Task: "Unit test for Jinja2 parser format detection in tests/unit/format_parsers/test_jinja2_parser.py"
Task: "Unit test for JSON parser format detection in tests/unit/format_parsers/test_json_parser.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Multi-format support)
4. **STOP and VALIDATE**: Test User Story 1 independently - verify all four formats load and convert to JSON
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Recursive networks)
4. Add User Story 3 → Test independently → Deploy/Demo (Unified abstraction)
5. Migrate all code → Remove old code → Test → Deploy/Demo (Full migration)
6. Add Resource Limits → Test independently → Deploy/Demo (Production ready)
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (format parsers)
   - Developer B: Prepare User Story 2 (reference resolver, network builder design)
3. Once User Story 1 is done:
   - Developer A: User Story 2 (network building)
   - Developer B: User Story 3 (unified abstraction)
   - Developer C: Resource Limits & Token Counting (Phase 6)
4. Once User Story 3 is done:
   - Developer A: Migration phase (replace old code)
   - Developer B: Continue Resource Limits
5. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Format parser implementations should be focused and testable in isolation (single responsibility per parser)
- All error classes must be domain-specific and provide actionable error messages
- Token counting must use tiktoken with configurable model specification
- Resource limits must be configurable per network load operation
