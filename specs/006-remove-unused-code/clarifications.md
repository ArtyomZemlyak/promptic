# Clarifications: Additional Code to Remove

**Date**: 2025-01-27  
**Feature**: Remove Unused Code from Library

## Analysis Summary

After thorough analysis of code dependencies and usage in examples 003, 004, 005, 006, the following additional code should be removed:

## Additional Modules to Remove

### 1. Instructions Package (FR-013)
- **Module**: `promptic.instructions` (entire package)
- **Reason**: Only used by blueprints for instruction storage/caching
- **Files**:
  - `promptic/instructions/store.py`
  - `promptic/instructions/cache.py`
  - `promptic/instructions/adapters/` (if exists)

### 2. SDK Blueprints Module (FR-014)
- **Module**: `promptic.sdk.blueprints`
- **Reason**: Not used in any examples
- **Files**: `promptic/sdk/blueprints.py`

### 3. SDK Adapters Module (FR-015)
- **Module**: `promptic.sdk.adapters`
- **Reason**: Not used in any examples
- **Files**: `promptic/sdk/adapters.py`

### 4. Pipeline Blueprint Modules (FR-016, FR-017, FR-018, FR-019, FR-020)
- **Modules**:
  - `promptic.pipeline.builder` (BlueprintBuilder)
  - `promptic.pipeline.previewer` (ContextPreviewer)
  - `promptic.pipeline.executor` (PipelineExecutor)
  - `promptic.pipeline.context_materializer` (ContextMaterializer)
  - `promptic.pipeline.template_renderer` (TemplateRenderer)
  - `promptic.pipeline.validation` (BlueprintValidator)
  - `promptic.pipeline.hooks` (PipelineHooks)
  - `promptic.pipeline.loggers` (PipelineLogger)
  - `promptic.pipeline.policies` (PolicyEngine)
- **Reason**: Only used by blueprints/adapters
- **Files**: All corresponding files in `promptic/pipeline/` except `network/builder.py`

### 5. Context Blueprint Modules (FR-021, FR-022, FR-023)
- **Modules**:
  - `promptic.context.rendering` (render_context_preview, render_context_for_llm)
  - `promptic.context.template_context` (build_instruction_context)
  - `promptic.context.logging` (JsonlEventLogger)
- **Reason**: Only used by blueprints/adapters
- **Files**: Corresponding files in `promptic/context/`

### 6. Context Errors Module (FR-024)
- **Module**: `promptic.context.errors`
- **Reason**: Only used by blueprints/adapters. Node network code uses `promptic.context.nodes.errors` instead
- **Files**: `promptic/context/errors.py`
- **Note**: Keep `promptic.context.nodes.errors` - it's used by node network builder

### 7. Settings Module (FR-025)
- **Module**: `promptic.settings`
- **Reason**: Need to analyze - likely only used by blueprints/adapters
- **Files**: `promptic/settings/base.py`
- **Action**: Check if `NetworkConfig` or node network code needs any settings. If not, remove or simplify.

### 8. Pipeline Format Renderers (FR-026)
- **Module**: `promptic.pipeline.format_renderers`
- **Reason**: Need to verify - if only used by blueprints/template_renderer, remove
- **Files**:
  - `promptic/pipeline/format_renderers/base.py`
  - `promptic/pipeline/format_renderers/file_first.py`
  - `promptic/pipeline/format_renderers/jinja2.py`
  - `promptic/pipeline/format_renderers/markdown.py`
  - `promptic/pipeline/format_renderers/markdown_hierarchy.py`
  - `promptic/pipeline/format_renderers/yaml.py`
- **Action**: Check if node rendering in `sdk.nodes.render_node_network` uses these. If not, remove.

### 9. SDK API Cleanup (FR-027)
- **Module**: `promptic.sdk.api`
- **Functions to Remove**:
  - `load_blueprint()`
  - `render_preview()`
  - `render_for_llm()`
  - `render_instruction()`
  - `preview_blueprint()`
  - `preview_blueprint_safe()`
  - `bootstrap_runtime()`
  - `build_materializer()`
  - `_create_settings_from_blueprint()`
  - `_extract_blueprint_data_from_network()`
  - `_iter_all_steps()`
- **Functions to Keep**:
  - `load_prompt()` - used in example 005
  - `export_version()` - used in example 006
  - `cleanup_exported_version()` - used in example 006
- **Action**: Refactor `sdk/api.py` to only contain versioning functions, or move them to a separate module

### 10. Public API Cleanup (FR-028)
- **File**: `promptic/__init__.py`
- **Current Exports to Remove**:
  - `bootstrap_runtime`
  - `load_blueprint`
  - `preview_blueprint`
  - `render_for_llm`
  - `render_instruction`
  - `render_preview`
- **Exports to Keep**:
  - `load_prompt`
  - `export_version`
  - `cleanup_exported_version`
  - `__version__`
- **Optional**: Consider exporting `load_node_network` and `render_node_network` from `sdk.nodes` at top level

## Verification Checklist

- [ ] Verify `promptic.context.nodes.errors` is NOT removed (used by node network)
- [ ] Verify `promptic.pipeline.network.builder` is NOT removed (used by node network)
- [ ] Verify `promptic.format_parsers` is NOT removed (used by node network)
- [ ] Verify `promptic.resolvers` is NOT removed (used by node network)
- [ ] Verify `promptic.versioning` is NOT removed (used by examples 005, 006)
- [ ] Verify `promptic.sdk.nodes` is NOT removed (used by examples 003, 004)
- [ ] Check if `promptic.settings` is needed by node network code
- [ ] Check if `promptic.pipeline.format_renderers` is used by node rendering

## Dependencies to Remove from pyproject.toml

After code removal, check if these dependencies are still needed:
- `tiktoken` (token counting)
- `rich` (if only used by blueprint preview)
- `pydantic-settings` (if only used by blueprint settings)
- Any adapter-related extras (httpx, sqlalchemy, faiss-cpu, etc.)

## Test Files to Remove/Update

- Remove all tests in `tests/unit/blueprints/`
- Remove all tests in `tests/unit/adapters/`
- Remove all tests in `tests/unit/instructions/`
- Remove all tests in `tests/integration/` that test blueprints/adapters
- Remove all tests in `tests/contract/` that test blueprint/adapter APIs
- Update tests that import removed modules
- Add tests verifying removed features cannot be imported (ImportError tests)
