# Feature Specification: SOLID Refactoring - Code Deduplication & Clean Architecture

**Feature Branch**: `008-solid-refactor`  
**Created**: 2025-11-25  
**Status**: Ready for Implementation  
**Input**: User description: "необходимо провести рефакторинг библиотеки с уменьшением дублирующегося кода, чтобы все было по SOLID, качественно с чистой архитектурой"
> This specification MUST satisfy the `promptic Constitution`: clean architecture layering, SOLID responsibilities, mandatory tests, documentation updates, and readability.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Eliminate Duplicate Reference Processing Code (Priority: P1)

As a library maintainer, I want to eliminate the duplicate reference processing code in `render_node_network` so that future changes only need to be made in one place.

**Why this priority**: The `render_node_network` function (~750+ lines) contains `process_node_content`, `replace_jinja2_ref`, `replace_markdown_ref`, and `replace_refs_in_dict` functions defined multiple times (4+ duplications). This is the most severe DRY violation and impacts maintainability the most.

**Independent Test**: Can be tested by verifying all rendering scenarios (markdown, yaml, json, full mode, file_first mode) produce identical output before and after refactoring.

**Architecture Impact**:
- **Entities**: `ContextNode`, `NodeNetwork`, `NodeReference`
- **Use Cases**: Reference resolution, content rendering
- **Interface Adapters**: Format parsers
- **SOLID Considerations**:
  - SRP violation: single function handles all reference types and all formats
  - DRY violation: identical code blocks repeated 4+ times
  - Mitigation: Extract dedicated `ReferenceInliner` class with single responsibility

**Quality Signals**:
- Unit tests for each extracted helper class
- Integration tests covering all render modes and formats
- No change in test output (regression prevention)

**Acceptance Scenarios**:

1. **Given** a markdown file with jinja2 references, **When** rendered with "full" mode, **Then** output is identical to current implementation
2. **Given** a YAML file with $ref references, **When** rendered with "full" mode, **Then** output is identical to current implementation
3. **Given** a JSON file with nested references, **When** rendered with "full" mode, **Then** output is identical to current implementation
4. **Given** any file, **When** rendered with "file_first" mode, **Then** output is identical to current implementation

---

### User Story 2 - Extract Reference Resolution Strategies (Priority: P1)

As a library maintainer, I want reference resolution patterns extracted into dedicated strategy classes so that each format's reference handling is isolated and testable.

**Why this priority**: Critical for achieving SRP - each strategy handles one type of reference (markdown links, jinja2 refs, yaml/json $ref). Enables OCP for adding new reference types.

**Independent Test**: Can be tested by running each strategy independently against sample content and verifying reference replacement works correctly.

**Architecture Impact**:
- **Entities**: New `ReferenceStrategy` interface
- **Use Cases**: Reference resolution
- **Interface Adapters**: Format-specific strategy implementations
- **SOLID Considerations**:
  - OCP: New reference types can be added without modifying existing code
  - SRP: Each strategy handles one reference type only
  - DIP: Rendering depends on abstractions (ReferenceStrategy), not concretions

**Quality Signals**:
- Unit tests for each strategy class
- Contract tests ensuring strategy interface compliance
- Documentation for adding new reference types

**Acceptance Scenarios**:

1. **Given** content with markdown links `[text](path)`, **When** MarkdownLinkStrategy processes it, **Then** links are replaced with resolved content
2. **Given** content with jinja2 refs `{# ref: path #}`, **When** Jinja2RefStrategy processes it, **Then** refs are replaced with resolved content
3. **Given** content with YAML/JSON `$ref`, **When** StructuredRefStrategy processes it, **Then** $ref objects are replaced with resolved content

---

### User Story 3 - Simplify VersionExporter (Priority: P2)

As a library maintainer, I want the `export_version` function in `VersionExporter` simplified by extracting helper methods so that each method has a single responsibility.

**Why this priority**: The function is ~230 lines with complex nested logic. Splitting improves testability and readability, but has lower impact than P1 items.

**Independent Test**: Can be tested by verifying export operations produce identical output and file structure before and after refactoring.

**Architecture Impact**:
- **Entities**: `ExportResult`, file mappings
- **Use Cases**: Version export
- **Interface Adapters**: FileSystemExporter
- **SOLID Considerations**:
  - SRP violation: function handles validation, discovery, mapping, processing, and export
  - Mitigation: Extract private methods for each distinct responsibility

**Quality Signals**:
- Unit tests for each extracted method
- Integration tests for complete export workflow
- `AICODE-NOTE` comments documenting each method's responsibility

**Acceptance Scenarios**:

1. **Given** a source directory with versioned files, **When** exported, **Then** output structure is identical to current implementation
2. **Given** variables for substitution, **When** exported, **Then** variables are correctly substituted in all files
3. **Given** hierarchical references, **When** exported, **Then** all paths are correctly resolved

---

### User Story 4 - Improve Rendering Pipeline Composability (Priority: P3)

As a library maintainer, I want rendering operations to follow a pipeline pattern so that processing steps can be composed and reordered easily.

**Why this priority**: Enables cleaner separation of concerns and easier testing of individual steps. Lower priority as current behavior works.

**Independent Test**: Can be tested by composing different pipeline configurations and verifying output.

**Architecture Impact**:
- **Entities**: New `RenderingPipeline` abstraction
- **Use Cases**: Content rendering
- **SOLID Considerations**:
  - OCP: New rendering steps can be added without modifying pipeline
  - SRP: Each step handles one transformation

**Quality Signals**:
- Unit tests for pipeline composition
- Documentation showing pipeline customization

**Acceptance Scenarios**:

1. **Given** a rendering pipeline with reference resolution step, **When** executed, **Then** references are resolved
2. **Given** a rendering pipeline with format conversion step, **When** executed, **Then** format is converted correctly
3. **Given** a custom pipeline configuration, **When** executed, **Then** steps execute in correct order

---

### Edge Cases

- What happens when reference resolution encounters circular references? → Must preserve existing cycle detection behavior
- How does system handle partial refactoring during migration? → Each extracted component must be backward compatible
- Does this introduce any Clean Architecture boundary violations? → No, extracting classes improves layer separation
- What readability risks exist? → Large PR risk; mitigate by breaking into smaller, incremental PRs

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST maintain identical behavior for all existing rendering operations after refactoring
- **FR-002**: System MUST extract duplicate `process_node_content` implementations into single reusable class
- **FR-003**: System MUST extract reference replacement patterns (jinja2, markdown, $ref) into dedicated strategy classes
- **FR-004**: System MUST reduce `render_node_network` function from ~750 lines to under 100 lines
- **FR-005**: System MUST extract `export_version` nested functions into private methods
- **FR-006**: System MUST preserve all existing test coverage (no regression)
- **FR-007**: System MUST maintain backward compatibility for public API

### Key Entities

- **ReferenceInliner**: Service for inlining referenced content into parent nodes, replacing duplicate `process_node_content` implementations
- **ReferenceStrategy**: Interface for format-specific reference resolution (markdown links, jinja2 refs, yaml/json $ref)
- **MarkdownLinkStrategy**: Strategy for replacing `[text](path)` references
- **Jinja2RefStrategy**: Strategy for replacing `{# ref: path #}` references
- **StructuredRefStrategy**: Strategy for replacing `{"$ref": "path"}` objects in YAML/JSON

### Architecture & Quality Constraints *(from Constitution)*

- **AQ-001**: Clean Architecture layering must be preserved:
  - Entities: `ContextNode`, `NodeNetwork`, `NodeReference` (unchanged)
  - Use Cases: `ReferenceInliner`, `NodeContentProcessor` (new)
  - Interface Adapters: Strategy implementations (new)
  - Dependency flow: adapters → use cases → entities

- **AQ-002**: SOLID responsibilities:
  - **SRP**: Each new class has single responsibility (reference inlining, format-specific resolution, content processing)
  - **OCP**: Strategy pattern allows adding new reference types without modifying existing code
  - **LSP**: All strategy implementations are substitutable through `ReferenceStrategy` interface
  - **ISP**: Minimal interfaces - strategies only expose `process(content, context) -> content`
  - **DIP**: High-level rendering depends on `ReferenceStrategy` abstraction, not concrete implementations

- **AQ-003**: Required tests:
  - Unit tests for `ReferenceInliner`, `NodeContentProcessor`, each strategy class
  - Integration tests for complete rendering workflow with all formats
  - Contract tests verifying strategy implementations meet interface requirements
  - Regression tests comparing output before/after refactoring

- **AQ-004**: Documentation updates:
  - Update docstrings for all new classes and methods
  - Add `AICODE-NOTE` comments explaining design decisions
  - Update `docs_site/` architecture documentation to reflect new structure

- **AQ-005**: Readability requirements:
  - Maximum function size: 50 lines (excluding comments)
  - Clear naming conventions following existing patterns
  - No dead code - remove all duplicate implementations after extraction

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `render_node_network` function reduced from ~750 lines to under 100 lines total, with individual functions under 50 lines each (86%+ reduction)
- **SC-002**: Zero duplicate code blocks for reference processing (currently 4+ duplications)
- **SC-003**: 100% of existing tests pass without modification (regression prevention)
- **SC-004**: New code achieves 90%+ test coverage
- **SC-005**: All related pytest suites (unit, integration, contract) pass locally and in CI with evidence linked in the PR
- **SC-006**: Relevant docs_site pages, specs, and inline comments are updated and reviewed alongside the code change
- **SC-007**: Each new class has corresponding docstring and `AICODE-NOTE` comments
- **SC-008**: Cyclomatic complexity of refactored functions reduced by at least 50%
