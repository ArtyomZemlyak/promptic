# Feature Specification: Remove Unused Code from Library

**Feature Branch**: `006-remove-unused-code`  
**Created**: 2025-01-27  
**Status**: Draft  
**Input**: User description: "Выпили все ненужное из библиотеки, что не учавствует в логике в examples. То есть мне нужны фичи 003 004 005. А вот всякая ерунда которая была ранее - она не нужна. Нужно убрать все лишнее (всякие адаптеры для памяти и данных, подсчет токенов, blueprints как таковой нам не нужен на сколько понимаю). И тд - все нужно проверить на наичие кода, который не соответствует текущей реальности либы (а это 004 и 005). Ну и readme содерждит основной концепт."
> This specification MUST satisfy the `promptic Constitution`: clean architecture layering, SOLID responsibilities, mandatory tests, documentation updates, and readability.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Remove Blueprint System (Priority: P1)

Remove all blueprint-related code that is not used in examples 003, 004, 005, 006. The library should focus on node network loading/rendering and versioning features only.

**Why this priority**: Blueprints are not used in any of the current examples and represent legacy architecture that conflicts with the simplified node-based approach.

**Independent Test**: After removal, examples 003, 004, 005, 006 should continue to work without any changes. All blueprint-related imports and functions should be removed from the public API.

**Architecture Impact**:
- Remove `promptic.blueprints` package entirely (models, serialization, adapters)
- Remove blueprint-related functions from `promptic.sdk.api` (load_blueprint, render_preview, render_for_llm, render_instruction, preview_blueprint)
- Remove `promptic.pipeline.builder`, `promptic.pipeline.previewer`, `promptic.pipeline.executor` if they only support blueprints
- Remove `promptic.context.rendering` if it only supports blueprints
- Remove `promptic.instructions` package (store, cache) if only used by blueprints
- Remove `promptic.context.template_context` if only used by blueprints
- Update `promptic.__init__.py` to remove blueprint exports

**Quality Signals**:
- Unit tests verifying examples 003-006 still work after removal
- Integration tests confirming no blueprint dependencies remain
- Update README.md to reflect simplified architecture
- Remove blueprint-related documentation from docs_site

**Acceptance Scenarios**:

1. **Given** the codebase contains blueprint-related code, **When** running examples 003, 004, 005, 006, **Then** they work without importing any blueprint modules
2. **Given** a developer tries to import blueprint functions, **When** they attempt `from promptic import load_blueprint`, **Then** they receive ImportError indicating the function doesn't exist
3. **Given** the codebase after cleanup, **When** searching for "blueprint" or "Blueprint" in source code, **Then** no results are found (except in comments explaining removal)

---

### User Story 2 - Remove Adapter System (Priority: P1)

Remove all adapter-related code for data and memory sources that is not used in examples 003, 004, 005, 006.

**Why this priority**: Adapters are not used in any current examples and add unnecessary complexity. The library should focus on file-based node networks without adapter abstractions.

**Independent Test**: After removal, examples 003, 004, 005, 006 should continue to work. All adapter-related imports should be removed.

**Architecture Impact**:
- Remove `promptic.adapters` package entirely (registry, data/, memory/)
- Remove `promptic.sdk.adapters` module
- Remove `promptic.pipeline.context_materializer` if it only orchestrates adapters
- Remove `promptic.settings` package entirely (not used by node network code, only contains blueprint/adapter settings)
- Remove `promptic.pipeline.format_renderers` package entirely (not used by node rendering, only used by blueprints)
- Update any code that references adapters, settings, or format_renderers

**Quality Signals**:
- Unit tests verifying examples work without adapters
- Integration tests confirming no adapter dependencies
- Update documentation to remove adapter references

**Acceptance Scenarios**:

1. **Given** the codebase contains adapter code, **When** running examples 003-006, **Then** they work without any adapter imports
2. **Given** a developer tries to import adapter functions, **When** they attempt `from promptic.adapters import AdapterRegistry`, **Then** they receive ImportError
3. **Given** the codebase after cleanup, **When** searching for "adapter" or "Adapter" in source code, **Then** no results are found (except in comments)

---

### User Story 3 - Remove Token Counting (Priority: P2)

Remove token counting functionality that is not used in examples 003, 004, 005, 006.

**Why this priority**: Token counting adds complexity and dependencies without being used in the current examples. The library should focus on core functionality.

**Independent Test**: After removal, examples 003-006 should continue to work. Token counting should not be referenced anywhere.

**Architecture Impact**:
- Remove `promptic.token_counting` package entirely
- Remove token counting from `promptic.context.nodes.models.NetworkConfig` if present
- Remove token-related dependencies (tiktoken) from pyproject.toml if not used elsewhere

**Quality Signals**:
- Unit tests verifying examples work without token counting
- Update dependencies in pyproject.toml
- Remove token counting from documentation

**Acceptance Scenarios**:

1. **Given** the codebase contains token counting code, **When** running examples 003-006, **Then** they work without token counting functionality
2. **Given** the codebase after cleanup, **When** searching for "token" or "TokenCounter" in source code, **Then** no results are found (except in comments)

---

### User Story 4 - Verify Core Features Work (Priority: P1)

Ensure that after cleanup, all features used in examples 003, 004, 005, 006 continue to work correctly.

**Why this priority**: This is the primary validation that the cleanup didn't break existing functionality.

**Independent Test**: Run all examples 003, 004, 005, 006 and verify they produce expected output without errors.

**Architecture Impact**:
- Keep `promptic.sdk.nodes` (load_node_network, render_node_network)
- Keep `promptic.versioning` (load_prompt, export_version, cleanup_exported_version)
- Keep `promptic.context.nodes` (ContextNode, NodeNetwork, models)
- Keep `promptic.format_parsers` (yaml, markdown, json, jinja2)
- Keep `promptic.pipeline.network.builder` (NodeNetworkBuilder)
- Keep `promptic.resolvers` (filesystem resolver)

**Quality Signals**:
- All examples run successfully
- Integration tests pass
- README.md accurately reflects current capabilities

**Acceptance Scenarios**:

1. **Given** examples 003, 004, 005, 006 exist, **When** running each example script, **Then** they execute successfully and produce expected output
2. **Given** the cleaned codebase, **When** importing `from promptic.sdk.nodes import load_node_network, render_node_network`, **Then** imports succeed
3. **Given** the cleaned codebase, **When** importing `from promptic import load_prompt, export_version, cleanup_exported_version`, **Then** imports succeed

---

### Edge Cases

- What happens when code references both removed and kept features? → Remove all references to removed features, update imports
- How to handle tests that depend on removed features? → Remove or update tests to use only kept features
- What if some code is shared between removed and kept features? → Refactor to extract shared code, remove blueprint/adapter-specific parts
- Does cleanup introduce any breaking changes for external users? → Yes, but this is intentional - document breaking changes in CHANGELOG
- How to ensure no dead code remains? → Use static analysis tools, verify all imports are used, check for unreachable code
- What about `promptic.context.errors`? → Remove - only used by blueprints/adapters, node network uses `promptic.context.nodes.errors`
- What about `promptic.settings`? → Remove - not used by node network code or examples 003-006, only contains blueprint/adapter settings
- What about `promptic.pipeline.format_renderers`? → Remove - not used by node rendering, only used by blueprints via TemplateRenderer

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST remove all blueprint-related code (blueprints package, blueprint functions from SDK API)
- **FR-002**: System MUST remove all adapter-related code (adapters package, adapter registry, data/memory adapters)
- **FR-003**: System MUST remove all token counting code (token_counting package, token-related dependencies)
- **FR-004**: System MUST preserve node network loading and rendering functionality (load_node_network, render_node_network)
- **FR-005**: System MUST preserve versioning functionality (load_prompt, export_version, cleanup_exported_version)
- **FR-006**: System MUST preserve format parsing functionality (yaml, markdown, json, jinja2 parsers)
- **FR-007**: System MUST preserve reference resolution functionality (filesystem resolver)
- **FR-008**: System MUST update public API (`promptic.__init__.py`) to remove removed functions
- **FR-009**: System MUST update README.md to reflect simplified architecture
- **FR-010**: System MUST ensure all examples 003, 004, 005, 006 continue to work after cleanup
- **FR-011**: System MUST remove or update tests that depend on removed features
- **FR-012**: System MUST update documentation to remove references to removed features
- **FR-013**: System MUST remove `promptic.instructions` package (store, cache) - only used by blueprints
- **FR-014**: System MUST remove `promptic.sdk.blueprints` module - not used in examples
- **FR-015**: System MUST remove `promptic.sdk.adapters` module - not used in examples
- **FR-016**: System MUST remove `promptic.pipeline.builder`, `promptic.pipeline.previewer`, `promptic.pipeline.executor` - only used by blueprints
- **FR-017**: System MUST remove `promptic.pipeline.context_materializer` - only used by blueprints/adapters
- **FR-018**: System MUST remove `promptic.pipeline.template_renderer` - only used by blueprints
- **FR-019**: System MUST remove `promptic.pipeline.validation` - only used by blueprints
- **FR-020**: System MUST remove `promptic.pipeline.hooks`, `promptic.pipeline.loggers`, `promptic.pipeline.policies` - only used by blueprints
- **FR-021**: System MUST remove `promptic.context.rendering` - only used by blueprints
- **FR-022**: System MUST remove `promptic.context.template_context` - only used by blueprints
- **FR-023**: System MUST remove `promptic.context.logging` - only used by blueprints/adapters
- **FR-024**: System MUST remove `promptic.context.errors` - only used by blueprints/adapters, NOT by node network code
- **FR-025**: System MUST remove `promptic.settings` package entirely - not used by node network code or examples 003-006, only contains blueprint/adapter settings (blueprint_root, instruction_root, adapter_registry, size_budget)
- **FR-026**: System MUST remove `promptic.pipeline.format_renderers` package entirely - not used by node rendering, only used by blueprints via TemplateRenderer
- **FR-027**: System MUST clean up `promptic.sdk.api` - remove all blueprint-related functions (load_blueprint, render_preview, render_for_llm, render_instruction, preview_blueprint, bootstrap_runtime, build_materializer)
- **FR-028**: System MUST update `promptic.__init__.py` to export only: load_prompt, export_version, cleanup_exported_version (and potentially load_node_network, render_node_network if exposed at top level)

### Key Entities

- **ContextNode**: Core entity representing a single file node with content, format, and references (KEEP)
- **NodeNetwork**: Core entity representing a network of connected nodes (KEEP)
- **ContextBlueprint**: Blueprint entity for hierarchical context definition (REMOVE)
- **AdapterRegistry**: Registry for data and memory adapters (REMOVE)
- **TokenCounter**: Token counting service (REMOVE)
- **VersionResolver**: Version resolution service for prompts (KEEP)
- **FormatParser**: Parser for different file formats (KEEP)

### Architecture & Quality Constraints *(from Constitution)*

- **AQ-001**: Clean Architecture layering must be preserved - domain entities (ContextNode, NodeNetwork) remain, use cases (node loading, rendering) remain, but adapter/blueprint layers are removed
- **AQ-002**: SOLID principles - each remaining module should have single responsibility (node loading, rendering, versioning, format parsing)
- **AQ-003**: All tests for examples 003-006 must pass. Remove tests for removed features. Add tests verifying removed features are truly gone (ImportError tests)
- **AQ-004**: Update README.md, remove blueprint/adapter documentation, update examples documentation
- **AQ-005**: Code readability - remove dead code, update imports, ensure no unused dependencies remain

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All examples 003, 004, 005, 006 execute successfully without errors after cleanup
- **SC-002**: Zero blueprint-related code remains in the codebase (verified by search)
- **SC-003**: Zero adapter-related code remains in the codebase (verified by search)
- **SC-004**: Zero token counting code remains in the codebase (verified by search)
- **SC-011**: Zero settings-related code remains in the codebase (verified by search)
- **SC-012**: Zero format_renderers code remains in the codebase (verified by search)
- **SC-005**: Public API (`promptic.__init__.py`) contains only functions used in examples 003-006
- **SC-006**: All pytest test suites pass (unit, integration tests for remaining features)
- **SC-007**: README.md accurately describes current library capabilities (node networks, versioning)
- **SC-008**: No unused dependencies remain in pyproject.toml (verified by dependency analysis)
- **SC-009**: Code coverage for remaining features maintains or improves (no dead code)
- **SC-010**: ImportError tests verify removed features cannot be imported

## Assumptions

- Examples 003, 004, 005, 006 represent the complete set of features needed
- No external users depend on blueprint/adapter/token counting APIs (breaking changes are acceptable)
- The simplified architecture (node networks + versioning) is the desired end state
- Format parsers and reference resolvers are core functionality that must be preserved
- README.md contains the main concept and should be updated to reflect reality

## Dependencies

- Examples 003, 004, 005, 006 must be analyzed to identify all used code paths
- Tests must be updated or removed based on feature removal
- Documentation must be updated to reflect changes

## Clarifications

### Session 2025-01-27

- Q: `promptic.settings` - нужен ли node network коду? → A: Удалить полностью - не используется в примерах 003-006, содержит только настройки для blueprints/adapters (blueprint_root, instruction_root, adapter_registry, size_budget). Единственный импорт в `versioning/utils/logging.py` не используется (мертвый импорт). Node network код работает без settings.
- Q: `promptic.pipeline.format_renderers` - используется ли node rendering? → A: Удалить полностью - используется только для blueprints через `TemplateRenderer`, НЕ используется node rendering. Node rendering в `sdk/nodes.py` использует прямую конвертацию форматов без format_renderers. Импорты `ContextNode` в `file_first.py` и `yaml.py` - только для совместимости (конвертация в `InstructionNode`), не для node rendering.

## Additional Code Analysis Results

After thorough code analysis, the following additional modules were identified for removal:

**Confirmed for Removal:**
- `promptic.instructions` package (FR-013)
- `promptic.sdk.blueprints` module (FR-014)
- `promptic.sdk.adapters` module (FR-015)
- `promptic.pipeline.builder`, `previewer`, `executor`, `context_materializer`, `template_renderer`, `validation`, `hooks`, `loggers`, `policies` (FR-016 to FR-020)
- `promptic.context.rendering`, `template_context`, `logging` (FR-021 to FR-023)
- `promptic.context.errors` - confirmed only used by blueprints/adapters, NOT by node network (FR-024)
- `promptic.settings` - confirmed NOT used by node network code or examples 003-006, only contains blueprint/adapter settings (FR-025)
- `promptic.pipeline.format_renderers` - confirmed NOT used by node rendering, only used by blueprints via TemplateRenderer (FR-026)

**Key Finding:** Node network code uses `promptic.context.nodes.errors` (not `promptic.context.errors`), so `context.errors` can be safely removed. Node rendering in `sdk/nodes.py` performs direct format conversion without using format_renderers.
