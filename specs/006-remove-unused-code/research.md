# Research: Remove Unused Code from Library

**Date**: 2025-01-27  
**Feature**: Remove Unused Code from Library  
**Status**: Complete

## Research Summary

This research phase analyzed the codebase to identify all code that is not used in examples 003, 004, 005, 006. The goal is to simplify the library to focus solely on node network loading/rendering and versioning features.

## Key Findings

### Code Usage Analysis

**Examples analyzed:**
- Example 003 (`examples/get_started/3-multiple-files/render.py`): Uses `load_node_network`, `render_node_network` from `promptic.sdk.nodes`
- Example 004 (`examples/get_started/4-file-formats/render.py`): Uses `load_node_network`, `render_node_network` from `promptic.sdk.nodes`
- Example 005 (`examples/get_started/5-versioning/render.py`): Uses `load_prompt` from `promptic`
- Example 006 (`examples/get_started/6-version-export/export_demo.py`): Uses `export_version`, `cleanup_exported_version` from `promptic`

**Core functionality required:**
1. Node network loading and rendering (`promptic.sdk.nodes`)
2. Versioning (`promptic.versioning`)
3. Format parsing (`promptic.format_parsers`)
4. Reference resolution (`promptic.resolvers`)
5. Node network builder (`promptic.pipeline.network.builder`)
6. Context node models (`promptic.context.nodes`)

### Modules to Remove

#### 1. Blueprint System (FR-001)
**Decision**: Remove entire `promptic.blueprints` package  
**Rationale**: Blueprints are not used in any examples. The library has moved to a node-based approach (features 003, 004) which is simpler and more flexible.  
**Alternatives considered**:
- Keep blueprints for backward compatibility → Rejected: No examples use them, breaking changes are acceptable
- Migrate blueprints to use node networks → Rejected: Adds unnecessary complexity, blueprints are legacy architecture

#### 2. Adapter System (FR-002)
**Decision**: Remove entire `promptic.adapters` package  
**Rationale**: Adapters are not used in any examples. Node networks work directly with filesystem, no adapter abstraction needed.  
**Alternatives considered**:
- Keep adapters for future extensibility → Rejected: YAGNI principle, can add back if needed
- Simplify adapters to only filesystem → Rejected: Node networks already handle filesystem directly

#### 3. Token Counting (FR-003)
**Decision**: Remove `promptic.token_counting` package  
**Rationale**: Token counting is not used in any examples. Adds dependency (tiktoken) without providing value for current use cases.  
**Alternatives considered**:
- Keep for future use → Rejected: Can add back if needed, currently unused
- Make optional dependency → Rejected: Not used anywhere, simpler to remove

#### 4. Settings Package (FR-025)
**Decision**: Remove `promptic.settings` package entirely  
**Rationale**: Settings are only used by blueprints/adapters. Node network code works without settings. Only import found is in `versioning/utils/logging.py` which is unused (dead import).  
**Alternatives considered**:
- Keep settings for future configuration → Rejected: Node networks don't need settings, YAGNI
- Simplify settings to only node network config → Rejected: No node network settings needed

#### 5. Format Renderers (FR-026)
**Decision**: Remove `promptic.pipeline.format_renderers` package  
**Rationale**: Format renderers are only used by blueprints via `TemplateRenderer`. Node rendering in `sdk/nodes.py` performs direct format conversion without using format_renderers.  
**Alternatives considered**:
- Keep format renderers for node rendering → Rejected: Node rendering doesn't use them, direct conversion works
- Refactor format renderers for node rendering → Rejected: Current direct conversion is simpler

#### 6. Instructions Package (FR-013)
**Decision**: Remove `promptic.instructions` package  
**Rationale**: Only used by blueprints for instruction storage/caching. Node networks load instructions directly from files.  
**Alternatives considered**:
- Keep for node network instruction loading → Rejected: Node networks load files directly, no instruction store needed

#### 7. Pipeline Blueprint Modules (FR-016 to FR-020)
**Decision**: Remove `promptic.pipeline.builder`, `previewer`, `executor`, `context_materializer`, `template_renderer`, `validation`, `hooks`, `loggers`, `policies`  
**Rationale**: All only used by blueprints/adapters. Node networks use `pipeline.network.builder` which is separate.  
**Alternatives considered**:
- Keep for future blueprint support → Rejected: Blueprints are being removed entirely

#### 8. Context Blueprint Modules (FR-021 to FR-023)
**Decision**: Remove `promptic.context.rendering`, `template_context`, `logging`  
**Rationale**: Only used by blueprints/adapters. Node networks use `context.nodes` models directly.  
**Alternatives considered**:
- Keep for node network rendering → Rejected: Node networks render directly in `sdk.nodes`, no separate rendering module needed

#### 9. Context Errors Module (FR-024)
**Decision**: Remove `promptic.context.errors`  
**Rationale**: Only used by blueprints/adapters. Node network code uses `promptic.context.nodes.errors` instead.  
**Alternatives considered**:
- Keep for shared error handling → Rejected: Node networks have their own error module, no sharing needed

#### 10. SDK Blueprints/Adapters Modules (FR-014, FR-015)
**Decision**: Remove `promptic.sdk.blueprints`, `promptic.sdk.adapters`  
**Rationale**: Not used in any examples.  
**Alternatives considered**: None - clearly unused

### Public API Changes

**Functions to remove from `promptic.__init__.py`:**
- `bootstrap_runtime`
- `load_blueprint`
- `preview_blueprint`
- `render_for_llm`
- `render_instruction`
- `render_preview`

**Functions to keep in `promptic.__init__.py`:**
- `load_prompt` (used in example 005)
- `export_version` (used in example 006)
- `cleanup_exported_version` (used in example 006)
- `__version__`

**Optional**: Consider exporting `load_node_network` and `render_node_network` from `sdk.nodes` at top level for convenience.

### Dependencies to Remove

After code removal, verify if these can be removed from `pyproject.toml`:
- `tiktoken` (token counting) → **REMOVE**
- `pydantic-settings` (if only used by settings) → **VERIFY**: Check if used elsewhere
- `rich` (if only used by blueprint preview) → **VERIFY**: Check if used elsewhere

### Test Impact

**Tests to remove:**
- All tests in `tests/unit/blueprints/`
- All tests in `tests/unit/adapters/`
- All tests in `tests/unit/instructions/`
- All tests in `tests/unit/token_counting/`
- Blueprint/adapter integration tests in `tests/integration/`
- Blueprint/adapter contract tests in `tests/contract/`

**Tests to add:**
- ImportError tests verifying removed features cannot be imported (`tests/integration/test_import_errors.py`)

**Tests to keep:**
- Node network tests (`tests/unit/nodes/`, `tests/integration/test_node_networks.py`)
- Versioning tests (`tests/unit/versioning/`, `tests/integration/test_versioning.py`)
- Format parser tests (`tests/unit/format_parsers/`)
- Reference resolver tests (`tests/unit/resolvers/`)

## Verification Strategy

1. **Code search**: Search for "blueprint", "adapter", "token", "settings" in source code to verify removal
2. **Import verification**: Attempt to import removed modules, verify ImportError
3. **Example execution**: Run examples 003, 004, 005, 006 to verify they still work
4. **Test execution**: Run `pytest tests/ -v` to verify all remaining tests pass
5. **Dependency check**: Verify removed dependencies are removed from `pyproject.toml`

## Risks and Mitigations

**Risk**: Accidentally removing code that is used indirectly  
**Mitigation**: Thorough code analysis, verify all imports, run examples and tests

**Risk**: Breaking external users (if any)  
**Mitigation**: Breaking changes are intentional and documented. Check if any external dependencies exist (unlikely for early-stage library)

**Risk**: Missing shared code between removed and kept features  
**Mitigation**: Careful code review, verify no circular dependencies, test thoroughly

## Conclusion

All research is complete. The codebase has been thoroughly analyzed, and all modules to remove have been identified. The cleanup will simplify the library significantly while preserving all functionality used in examples 003-006. No further research is needed - proceed to Phase 1 design.

