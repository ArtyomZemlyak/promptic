# Feature Specification: Instruction Data Insertion with Multiple Templating Formats

**Feature Branch**: `001-instruction-templating`  
**Created**: 2025-01-28  
**Status**: Draft  
**Input**: User description: "Теперь важно подумать как могут у нас вставляться данные в инструкции. Нужно предусмотреть возможность вставки через {} или что-то такое. Наверно нужно уметь поддерживать несколько вариантов. К примеру, если .md - то мы ищем {} для .format, если это .jinja - то там свое. Плюс какой-то вариант с yaml (допустим что можно самим сделать паттерн и прописывать в параметрах yaml). И вот думаю, есть ли вариант как-то сделать иерархическую логику чисто на .md файлах? Можно придумать какой-то вариант, чтобы упростить промпты и не делать yaml (при этом его поддержку оставляем)."
> This specification MUST satisfy the `promptic Constitution`: clean architecture layering, SOLID responsibilities, mandatory tests, documentation updates, and readability.

## Clarifications

### Session 2025-01-28

- Q: What context variables should be available in instruction templates? → A: Both global and step-specific context with clear namespacing (`data.*`, `memory.*`, `step.*`) to avoid conflicts and enable step-aware instructions.
- Q: Should instruction Jinja2 rendering use the same environment as prompt rendering? → A: Separate Jinja2 environments with shared base configuration, allowing instruction-specific filters and globals without affecting prompt rendering.
- Q: How should template rendering errors be handled in instructions? → A: Use existing `InstructionFallbackPolicy` to control template rendering error behavior, aligning with existing fallback semantics.
- Q: For loop steps, should each iteration render instructions with different context? → A: Per-iteration rendering with `step.loop_item` context variable, enabling instructions like "Process source: {{ step.loop_item.title }}" for each loop iteration.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Insertion in Markdown Instructions (Priority: P1)

Designers insert dynamic data into Markdown instruction files using Python string format syntax (`{}` placeholders) without needing YAML configuration files.

**Why this priority**: This is the most common format for instructions and provides the simplest authoring experience. Users can write instruction files that accept data directly without learning additional templating syntax.

**Independent Test**: A designer can create a `.md` instruction file containing placeholders like `Process the item: {item_name}` and render it with data `{"item_name": "Task 1"}` to produce `Process the item: Task 1`. This can be tested independently with a single instruction file and a rendering function call.

**Architecture Impact**: Introduces a template renderer abstraction in the use-case layer that dispatches to format-specific renderers based on instruction format. The existing `InstructionNode.format` field (currently `"md"`, `"txt"`, `"jinja"`) drives the selection. Domain entities remain unchanged; new renderer interfaces are introduced in the use-case layer following dependency inversion. Existing instruction loading flows must route through the renderer when data is provided.

**Quality Signals**: Unit tests for Markdown format parsing and rendering, integration test rendering instruction with data slots, docs_site guide "Data insertion in instructions", `# AICODE-NOTE` documenting format detection and rendering strategy.

**Acceptance Scenarios**:

1. **Given** a Markdown instruction file containing `{variable_name}` placeholders, **When** the instruction is rendered with data `{"variable_name": "value"}`, **Then** the rendered output replaces all placeholders with their corresponding values.
2. **Given** a Markdown instruction file with nested placeholders like `{user.name}`, **When** the instruction is rendered with nested data, **Then** the renderer resolves nested dictionary keys correctly.

---

### User Story 2 - Jinja2 Templating for Complex Logic (Priority: P2)

Designers use Jinja2 templating syntax in `.jinja` instruction files for conditional logic, loops, and complex data transformations without needing external YAML configuration.

**Why this priority**: Advanced use cases require conditional rendering, loops, and filters that go beyond simple string substitution. Jinja2 provides a mature, well-understood syntax for these scenarios.

**Independent Test**: A designer can create a `.jinja` instruction file with conditional blocks like `{% if condition %}...{% endif %}` and render it with context data. This can be tested independently with a single `.jinja` file and a rendering function.

**Architecture Impact**: Extends the template renderer abstraction to support Jinja2 rendering. The existing `InstructionNode.format` field already includes `"jinja"`, so this builds on the format detection mechanism. Jinja2 environment configuration uses a separate environment from prompt rendering, with shared base configuration managed through settings following dependency inversion. This allows instruction-specific filters and globals without affecting prompt rendering. Rendering functions inject blueprint context with namespaced variables (`data.*`, `memory.*`, `step.*`) including step hierarchy, step_id, and loop iteration context.

**Quality Signals**: Unit tests for Jinja2 template rendering with various syntax patterns, integration test with conditional logic and loops, docs_site guide "Jinja2 templating in instructions", `# AICODE-NOTE` documenting separate Jinja2 environment setup (shared base config), instruction-specific filters/globals, and available namespaced context variables (`data.*`, `memory.*`, `step.*`).

**Acceptance Scenarios**:

1. **Given** a `.jinja` instruction file with conditional blocks `{% if item.complete %}{{ item.title }}{% endif %}`, **When** the instruction is rendered with context `{"item": {"complete": true, "title": "Task"}}`, **Then** the output includes the title only when the condition is true.
2. **Given** a `.jinja` instruction file with loops `{% for item in items %}{{ item }}{% endfor %}`, **When** the instruction is rendered with a list, **Then** the output iterates over all items correctly.

---

### User Story 3 - Custom Pattern Templating in YAML Instructions (Priority: P3)

Designers define custom placeholder patterns in YAML instruction files through configuration parameters, allowing flexible templating syntax that adapts to specific use cases.

**Why this priority**: Some teams may have existing conventions or require custom syntax that doesn't match standard formats. This provides extensibility while maintaining YAML support as specified in the existing data model.

**Independent Test**: A designer can create a YAML instruction file with a `pattern` field like `pattern: "{{name}}"` and render it with data `{"name": "value"}` to replace the custom pattern. This can be tested independently with a YAML file and custom pattern configuration.

**Architecture Impact**: Extends the template renderer to support configurable pattern-based substitution for YAML format instructions. The `InstructionNode` entity may need optional `pattern` metadata field, or patterns can be specified in instruction provider configuration. Renderer uses regex or string replacement based on configured pattern following the strategy pattern. YAML format detection remains separate from rendering logic (single responsibility).

**Quality Signals**: Unit tests for custom pattern parsing and replacement, integration test with various pattern formats, docs_site guide "Custom patterns in YAML instructions", `# AICODE-NOTE` documenting pattern configuration and escaping rules.

**Acceptance Scenarios**:

1. **Given** a YAML instruction file with `pattern: "{{key}}"` configuration, **When** the instruction is rendered with data `{"key": "value"}`, **Then** all instances of `{{key}}` are replaced with `value`.
2. **Given** a YAML instruction file with an escaped pattern, **When** the instruction is rendered, **Then** escaped characters are handled correctly without breaking pattern matching.

---

### User Story 4 - Hierarchical Logic in Markdown Files (Priority: P3)

Designers express hierarchical logic and conditional rendering directly in Markdown instruction files using a lightweight syntax extension, reducing reliance on YAML blueprints for simple scenarios.

**Why this priority**: This simplifies the authoring experience for common hierarchical patterns. Designers can express step relationships and conditions in the instruction files themselves, making the prompt engineering workflow more streamlined.

**Independent Test**: A designer can create a Markdown instruction file with hierarchical markers like `## Step 1` followed by `### Sub-step 1.1` and the system recognizes the hierarchy. This can be tested independently by parsing a Markdown file and extracting its structure.

**Architecture Impact**: Introduces a Markdown parser extension that extracts hierarchical structure and conditional markers. The parser runs during instruction loading, producing a structured representation that can inform rendering decisions. This extends the instruction format detection without changing core entities. Parsing logic is separated into a dedicated module following single responsibility, and hierarchical structure is represented as metadata that doesn't alter the instruction content.

**Quality Signals**: Unit tests for Markdown hierarchy parsing, integration test with nested instruction structure, docs_site guide "Hierarchical instructions in Markdown", `# AICODE-NOTE` documenting hierarchy syntax and parsing strategy.

**Acceptance Scenarios**:

1. **Given** a Markdown instruction file with heading-based hierarchy `## Parent` followed by `### Child`, **When** the instruction is loaded, **Then** the system recognizes the parent-child relationship.
2. **Given** a Markdown instruction file with conditional markers like `<!-- if:condition -->`, **When** the instruction is rendered with context, **Then** conditional sections are included or excluded based on context data.

---

### Edge Cases

- **Missing placeholder values**: When rendering a Markdown instruction with `{missing_var}` but data doesn't contain the key, the system raises a `TemplateRenderError` with a descriptive message indicating which placeholder is missing and where it appears in the instruction.
- **Invalid Jinja2 syntax**: When a `.jinja` instruction file contains syntax errors, the system raises a `TemplateRenderError` with the Jinja2 error details, including line number and specific syntax issue.
- **Pattern collision**: When a YAML instruction uses a custom pattern that conflicts with literal text in the instruction content, the system provides escape mechanisms or raises a validation warning during instruction loading.
- **Nested placeholder complexity**: When a Markdown instruction contains deeply nested placeholders like `{outer.middle.inner.key}`, the renderer handles nested dictionary traversal correctly and raises errors for missing keys at any level.
- **Jinja2 context variable conflicts**: Context variables are namespaced (`data.*`, `memory.*`, `step.*`) to prevent conflicts with user-provided data keys. The system documents namespace usage and precedence rules to ensure clear variable resolution.
- **Large template rendering**: When instructions are very large (thousands of lines) with many placeholders, the renderer completes without excessive memory usage and provides progress indicators for long-running render operations.
- **Circular references in Jinja2**: When Jinja2 templates include other templates that create circular dependencies, the system detects cycles and raises `TemplateRenderError` with cycle details.
- **Mixed format detection**: When an instruction file extension doesn't match its actual format (e.g., `.md` file contains Jinja2 syntax), the system provides a way to override format detection or auto-detect based on content.
- **Readability safeguards**: Template rendering preserves instruction readability by maintaining proper indentation and whitespace when inserting data, and provides warnings when rendered output exceeds recommended length limits.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST support inserting data into Markdown instruction files using Python string format syntax (`{}` placeholders) where placeholders are replaced with values from a provided data dictionary.
- **FR-002**: The system MUST support inserting data into Jinja2 instruction files (`.jinja` format) where templates can use Jinja2 syntax including conditionals, loops, filters, and variable interpolation.
- **FR-003**: The system MUST support configurable custom placeholder patterns for YAML instruction files where the pattern syntax is defined in instruction metadata or provider configuration.
- **FR-004**: The system MUST automatically detect instruction format based on file extension (`.md` → Markdown format, `.jinja` → Jinja2, `.yaml`/`.yml` → YAML) and route to the appropriate renderer.
- **FR-005**: The system MUST allow format detection override when file extension doesn't match content or when explicitly specified in `InstructionNode.format` field.
- **FR-006**: The system MUST provide blueprint context (data slots, memory slots, step hierarchy, step_id) as variables during template rendering so instructions can reference blueprint state. Context variables MUST be namespaced (`data.*`, `memory.*`, `step.*`) to avoid conflicts. For loop steps, each iteration MUST render instructions with per-iteration context including `step.loop_item` containing the current iteration item.
- **FR-007**: The system MUST handle template rendering errors according to `InstructionFallbackPolicy` configured for the instruction. When policy is `error`, the system MUST raise `TemplateRenderError` with descriptive messages when placeholder resolution fails (missing keys, syntax errors, type mismatches). When policy is `warn` or `noop`, the system MUST emit structured warnings and continue with fallback behavior (placeholder substitution or empty string).
- **FR-008**: The system MUST support nested dictionary access in Markdown format placeholders (e.g., `{user.profile.name}` resolves to `data["user"]["profile"]["name"]`).
- **FR-009**: The system MUST support Markdown hierarchy parsing where heading levels indicate parent-child relationships and optional conditional markers control section inclusion.
- **FR-010**: The system MUST preserve instruction file formatting (indentation, line breaks, whitespace) when inserting data, except where templating syntax explicitly modifies layout.
- **FR-011**: The system MUST support escaping placeholder syntax in Markdown instructions (e.g., `{{` renders as literal `{`).
- **FR-012**: The system MUST validate custom patterns in YAML instructions to ensure they are valid regex patterns or provide safe string replacement semantics.

### Key Entities

- **TemplateRenderer**: Abstraction in the use-case layer that coordinates format-specific rendering. Dispatches to format-specific renderers based on instruction format. Provides unified interface for rendering instructions with data context.

- **FormatRenderer**: Interface for format-specific rendering implementations (MarkdownFormatRenderer, Jinja2FormatRenderer, YamlFormatRenderer). Each implements the same interface but handles format-specific syntax and rules.

- **InstructionRenderContext**: Context object passed to renderers containing blueprint data (data slots, memory slots), current step information, hierarchical position, and user-provided template variables. Context variables are namespaced: `data.*` for data slot values, `memory.*` for memory slot values, `step.*` for step-specific information (step_id, title, kind, hierarchy, loop_item for loop iterations).

- **TemplateRenderError**: Domain exception raised when template rendering fails (missing placeholders, syntax errors, type mismatches). Includes detailed error information for debugging.

- **MarkdownHierarchyParser**: Optional parser that extracts hierarchical structure from Markdown instruction files based on heading levels and conditional markers. Produces structured metadata that informs rendering decisions.

### Architecture & Quality Constraints *(from Constitution)*

- **AQ-001**: Template rendering logic is separated into use-case layer modules following clean architecture. Domain entities (`InstructionNode`) remain unaware of rendering details. Format-specific renderers are interfaces implemented by adapters, following dependency inversion. The renderer abstraction allows swapping implementations without modifying use cases.

- **AQ-002**: Single responsibility: Each format renderer handles one format type. The template renderer dispatcher coordinates format selection but doesn't implement rendering logic. Markdown hierarchy parsing is a separate concern from rendering. Open/closed principle: New format renderers can be added by implementing the `FormatRenderer` interface without modifying existing code. Dependency inversion: Use cases depend on renderer abstractions, not concrete implementations.

- **AQ-003**: Unit tests: Each format renderer has comprehensive unit tests covering placeholder resolution, edge cases, error handling. Integration tests: End-to-end tests rendering instructions from files with various data contexts. Contract tests: Verify renderer interface compliance when swapping implementations. All tests run in CI on every commit.

- **AQ-004**: Documentation updates: `docs_site/` guides for each format (Markdown data insertion, Jinja2 templating, YAML patterns, hierarchical Markdown). API reference documentation for renderer interfaces. Inline docstrings for all public renderer methods. `# AICODE-NOTE` comments documenting format detection strategies, context variable availability, and rendering precedence rules.

- **AQ-005**: Renderer functions are kept focused and small (single responsibility per function). Format detection logic is separated from rendering logic. Error messages use clear, descriptive language. Code avoids deep nesting in template parsing. Naming conventions: `render_*` for rendering functions, `parse_*` for parsing functions, `*Renderer` for renderer classes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Designers can successfully render Markdown instructions with data placeholders in 100% of test cases covering simple placeholders, nested access, and escaping scenarios.
- **SC-002**: Designers can successfully render Jinja2 instructions with conditional logic and loops in 100% of test cases covering all common Jinja2 patterns used in instruction files.
- **SC-003**: System provides clear error messages for template rendering failures, with 95% of test cases validating that error messages identify the specific placeholder, line number, and issue type.
- **SC-004**: Format detection automatically selects the correct renderer based on file extension in 100% of cases, with override mechanism available for edge cases.
- **SC-005**: Template rendering preserves instruction formatting (indentation, whitespace) correctly in 100% of test cases where formatting preservation is expected.
- **SC-006**: Blueprint context variables are accessible during template rendering, with all documented context variables (step_id, data_slots, memory_slots, hierarchy) available in 100% of test scenarios.
- **SC-007**: All related pytest suites (unit, integration, contract) pass locally and in CI with evidence linked in the PR.
- **SC-008**: Relevant docs_site pages, specs, and inline comments are updated and reviewed alongside the code change.
