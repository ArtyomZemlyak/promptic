# Feature Specification: Variable Insertion in Prompts

**Feature Branch**: `007-variable-insertion`  
**Created**: 2025-11-25  
**Status**: Draft  
**Input**: User requirement for variable insertion functionality with hierarchical scope resolution

> This specification MUST satisfy the `promptic Constitution`: clean architecture layering, SOLID responsibilities, mandatory tests, documentation updates, and readability.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Simple Variable Insertion (Priority: P1) 🎯 MVP

Users can insert variable values into prompts at render/export time by passing a dictionary of variable names and values. Variables are replaced throughout the entire prompt hierarchy.

**Why this priority**: This is the foundational capability enabling dynamic prompt generation. Without basic variable insertion, users cannot create reusable prompts with runtime-determined values.

**Independent Test**: User creates a prompt `main.md` containing placeholder `{{user_name}}` and renders it with variables `{"user_name": "Alice"}`. Output contains "Alice" instead of "{{user_name}}". This proves basic variable insertion works independently.

**Architecture Impact**: Extends `render_node_network()` and `export_version()` functions to accept optional `vars` parameter (dict). Introduces `VariableSubstitutor` service in domain layer that performs string substitution. Updates all format parsers to support variable markers without conflicts. Maintains SRP by separating variable substitution from rendering logic.

**Quality Signals**: Unit tests for variable substitution logic, integration tests rendering prompts with variables across all formats, contract tests for variable substitution interface, docs_site guide "Variable insertion in prompts", `AICODE-NOTE` explaining substitution strategy.

**Acceptance Scenarios**:

1. **Given** a prompt containing `{{variable_name}}`, **When** rendered with `vars={"variable_name": "value"}`, **Then** output contains "value"
2. **Given** a prompt with multiple occurrences of `{{var}}`, **When** rendered with `vars={"var": "X"}`, **Then** all occurrences are replaced with "X"
3. **Given** a prompt with variables in nested files, **When** rendered with variables dict, **Then** variables in all hierarchy levels are replaced
4. **Given** a prompt with undefined variable `{{missing}}`, **When** rendered without that variable, **Then** placeholder is kept unchanged (graceful degradation)

---

### User Story 2 - Node-Scoped Variable Insertion (Priority: P2)

Users can target variables to specific nodes in the hierarchy using dot notation: `"node_name.variable"` to replace variables only in files matching that node name.

**Why this priority**: Enables precise control when different parts of hierarchy need different values for similarly-named variables. Important for complex hierarchies but can be built after basic insertion works.

**Independent Test**: User has hierarchy with `instructions.md` and `templates.md`, both containing `{{format}}`. User renders with `vars={"instructions.format": "detailed", "templates.format": "brief"}`. Output shows "detailed" in instructions and "brief" in templates. This proves node-scoped variables work independently.

**Architecture Impact**: Extends `VariableSubstitutor` to parse scoped variable names and match against node IDs. Updates variable resolution algorithm to prefer scoped matches over global matches. Maintains SRP by keeping scoping logic separate from substitution logic.

**Quality Signals**: Unit tests for scoped variable parsing, integration tests with hierarchies containing name collisions, docs_site examples showing scoped usage, `AICODE-NOTE` explaining scoping precedence rules.

**Acceptance Scenarios**:

1. **Given** two nodes with same variable placeholder, **When** rendered with node-scoped variables, **Then** each node receives its specific value
2. **Given** scoped variable `"node.var"` and global variable `"var"`, **When** rendered, **Then** scoped variable takes precedence in matching nodes
3. **Given** invalid node name in scoped variable, **When** rendered, **Then** system logs warning and treats as undefined variable (graceful degradation)

---

### User Story 3 - Full-Path Variable Insertion (Priority: P3)

Users can target variables using full hierarchical paths: `"root.group.node.variable"` for maximum precision in complex hierarchies with multiple nesting levels.

**Why this priority**: Provides ultimate precision for deeply nested hierarchies. Less common than simple/node-scoped insertion, can be built after those work.

**Independent Test**: User has hierarchy `root.md` → `group/subgroup.md` → `details.md`, all containing `{{value}}`. User renders with `vars={"root.group.subgroup.details.value": "specific"}`. Only the deepest file shows "specific", others keep placeholder. This proves full-path targeting works independently.

**Architecture Impact**: Extends `VariableSubstitutor` to handle multi-level path matching. Updates node ID tracking to support hierarchical path construction during network building. Maintains SRP by keeping path resolution separate from substitution.

**Quality Signals**: Unit tests for hierarchical path matching, integration tests with 3+ nesting levels, docs_site examples with complex hierarchies, `AICODE-NOTE` explaining path construction strategy.

**Acceptance Scenarios**:

1. **Given** nested hierarchy with path-scoped variables, **When** rendered, **Then** variables match only nodes at exact hierarchical path
2. **Given** partial path match (e.g., `"group.node.var"` matching multiple paths), **When** rendered, **Then** all matching nodes receive the value
3. **Given** full path and node-scoped variables for same placeholder, **When** rendered, **Then** full path takes precedence (most specific wins)

---

### User Story 4 - Format-Specific Variable Syntax (Priority: P2)

Each file format supports variable insertion with syntax that doesn't conflict with format-specific features. Jinja2 uses native Jinja syntax, others use `{{var}}` notation.

**Why this priority**: Ensures variable insertion works reliably across all formats without breaking existing functionality. Critical for multi-format support but can be refined after basic insertion works.

**Independent Test**: User creates prompts in all formats (MD, YAML, JSON, Jinja2) with variable placeholders. Rendering each format with variables produces correct substitutions without syntax errors. This proves format-specific handling works independently.

**Architecture Impact**: Updates each format parser to recognize and preserve variable markers. For Jinja2, uses native Jinja2 templating engine for variable substitution. For other formats, uses custom marker pattern `{{var}}`. Maintains SRP by keeping format-specific logic in respective parsers.

**Quality Signals**: Unit tests for each format with variables, integration tests mixing formats in hierarchies, docs_site format-specific examples, `AICODE-NOTE` explaining format considerations.

**Acceptance Scenarios**:

1. **Given** Markdown with `{{var}}`, **When** rendered with variables, **Then** replacement works without breaking markdown syntax
2. **Given** YAML with `{{var}}` in value fields, **When** rendered with variables, **Then** YAML structure remains valid
3. **Given** JSON with `{{var}}` in string values, **When** rendered with variables, **Then** JSON remains valid after substitution
4. **Given** Jinja2 with `{{ var }}` (native syntax), **When** rendered with variables, **Then** Jinja2 engine handles substitution correctly
5. **Given** variable in YAML key (invalid), **When** rendered, **Then** system raises error or skips (documented behavior)

---

### Edge Cases

- **Circular variable references**: `{{var1}}` contains `{{var2}}`, `{{var2}}` contains `{{var1}}`. System detects cycles and raises error or limits recursion depth.
- **Variable names with special characters**: `{{my-var}}`, `{{my_var}}`, `{{my.var}}`. System defines allowed characters and documents limitations.
- **Nested variable syntax**: `{{ {{inner}} }}`. System clarifies whether nested variables are supported or treated as literal text.
- **Variable escaping**: User wants literal `{{text}}` in output without substitution. System provides escape mechanism (e.g., `\{{text}}` or `{{{text}}}`).
- **Type preservation in structured formats**: In YAML/JSON, should `{{var}}` preserve type (if value is int/bool) or always substitute as string? Document behavior.
- **Variables in references**: `[link]({{path}}/file.md)`. System clarifies whether variables in references are expanded before or after reference resolution.
- **Performance with many variables**: Hierarchy with 100+ nodes and 50+ variables. System should efficiently apply substitutions without repeated scans.
- **Variable precedence conflicts**: Both `"var"` and `"node.var"` defined. System must have clear precedence rules (most specific wins).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept `vars` parameter (dict) in `render_node_network()` and `export_version()` functions
- **FR-002**: System MUST replace variable placeholders `{{variable_name}}` with provided values throughout entire hierarchy
- **FR-003**: System MUST support simple variable names: `{"var": "value"}`
- **FR-004**: System MUST support node-scoped variables: `{"node_name.var": "value"}`
- **FR-005**: System MUST support full-path variables: `{"root.group.node.var": "value"}`
- **FR-006**: System MUST apply most-specific-match precedence: full-path > node-scoped > simple
- **FR-007**: System MUST replace all occurrences of a variable within matching scope
- **FR-008**: System MUST handle undefined variables gracefully (keep placeholder unchanged)
- **FR-009**: System MUST work with all file formats (Markdown, YAML, JSON, Jinja2)
- **FR-010**: For Jinja2 files, system MUST use native Jinja2 variable syntax and templating engine
- **FR-011**: For non-Jinja2 files, system MUST use `{{var}}` marker pattern for variables
- **FR-012**: System MUST perform variable substitution after reference resolution in "full" render mode
- **FR-013**: System MUST perform variable substitution on final content in "file_first" render mode
- **FR-014**: System MUST preserve format validity after variable substitution (YAML/JSON remain parseable)
- **FR-015**: System MUST document variable naming rules (allowed characters, case sensitivity)
- **FR-016**: System MUST provide clear error messages when variable substitution fails

### Key Entities

- **VariableSubstitutor**: Domain service that performs variable substitution with hierarchical scope resolution. Takes content string, variables dict, and node context (ID/path). Returns content with variables replaced according to precedence rules.

- **VariableScope**: Value object representing variable resolution scope (simple/node/path). Contains logic for matching variable names against node identifiers and determining precedence.

- **Jinja2VariableRenderer**: Specialized adapter for Jinja2 files that uses Jinja2 templating engine for variable substitution instead of simple string replacement.

### Architecture & Quality Constraints

- **AQ-001**: Keep `VariableSubstitutor` in domain layer, format-specific rendering adapters in adapter layer. Entities remain unaware of variable substitution (applied at rendering boundary).
- **AQ-002**: Apply SRP by separating variable parsing, scope resolution, and substitution logic. Document coupling between substitutor and network builder via `AICODE-NOTE`.
- **AQ-003**: Provide unit tests for variable parsing, scope matching, precedence rules, and substitution. Integration tests with hierarchies and all formats. Contract tests for substitution interface.
- **AQ-004**: Update docs_site with "Variable insertion" guide covering all syntax forms, format-specific notes, and examples. Add `AICODE-NOTE` comments explaining substitution strategy.
- **AQ-005**: Limit substitution functions to <100 lines, use descriptive names, avoid complex regex where simple string methods suffice.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can insert variables in prompts with 100% success rate for all three scoping methods (simple, node, path)
- **SC-002**: Variable substitution works correctly in all file formats (MD, YAML, JSON, Jinja2) verified by integration tests
- **SC-003**: Hierarchies with 10+ nodes and 20+ variables render correctly within 1 second
- **SC-004**: All pytest suites pass with >85% coverage for variable substitution code
- **SC-005**: Documentation includes working examples for each scoping method
- **SC-006**: Example 7 demonstrates variable insertion in multi-level hierarchy with all three scoping methods
