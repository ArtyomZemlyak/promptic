# Removal Analysis: Code Dependencies and References

**Date**: 2025-11-24  
**Purpose**: Document all occurrences of blueprint, adapter, and token counting code before removal

## Summary

- **Blueprint references**: 519 matches across 38 files in src/
- **Adapter references**: 292 matches across 33 files in src/
- **Token references**: 135 matches across 11 files in src/
- **Settings imports**: 8 files import settings (only 1 in versioning - DEAD IMPORT)
- **Examples usage**: NO blueprint/adapter/token usage - only node networks and versioning

## Blueprint References

### Source Code Search Results (519 matches, 38 files)

Key files to remove:
- `src/promptic/blueprints/` (entire package)
- `src/promptic/sdk/blueprints.py`
- `src/promptic/pipeline/builder.py`
- `src/promptic/pipeline/previewer.py`
- `src/promptic/pipeline/executor.py`
- Blueprint-related functions in `src/promptic/sdk/api.py`
- Blueprint exports in `src/promptic/__init__.py`

## Adapter References

### Source Code Search Results (292 matches, 33 files)

Key files to remove:
- `src/promptic/adapters/` (entire package)
- `src/promptic/sdk/adapters.py`
- `src/promptic/pipeline/context_materializer.py`
- `src/promptic/settings/` (entire package - only used by adapters/blueprints)
- Adapter references in versioning (only in filesystem adapters - KEEP these)

## Token Counting References

### Source Code Search Results (135 matches, 11 files)

Key files to remove:
- `src/promptic/token_counting/` (entire package)
- Token counting references in node models (optional field)
- Token counting in network builder (optional feature)

## Settings References

### Settings Import Analysis (8 files)

Settings are imported in:
1. `versioning/utils/logging.py` - **DEAD IMPORT** (imported but never used)
2. `pipeline/context_materializer.py` - To be removed with adapters
3. `sdk/api.py` - To be removed with blueprint functions
4. `pipeline/builder.py` - To be removed with blueprints
5. `sdk/blueprints.py` - To be removed with blueprints
6. `blueprints/models.py` - To be removed with blueprints
7. `pipeline/validation.py` - To be removed with blueprints
8. `pipeline/policies.py` - To be removed with blueprints

**Conclusion**: Settings package can be safely removed. Only dead import in versioning.

## Examples Analysis

### Example 003 (3-multiple-files)
Imports: `from promptic.sdk.nodes import load_node_network, render_node_network`
✅ No blueprint/adapter/token usage

### Example 004 (4-file-formats)
Imports: `from promptic.sdk.nodes import load_node_network, render_node_network`
✅ No blueprint/adapter/token usage

### Example 005 (5-versioning)
Imports: `from promptic import load_prompt`
✅ No blueprint/adapter/token usage

### Example 006 (6-version-export)
Imports: `from promptic import cleanup_exported_version, export_version`
✅ No blueprint/adapter/token usage

## Public API Analysis

### Current Exports (src/promptic/__init__.py)

```python
__all__ = [
    "__version__",
    "bootstrap_runtime",        # REMOVE - blueprint related
    "cleanup_exported_version", # KEEP - used in example 006
    "export_version",           # KEEP - used in example 006
    "load_blueprint",           # REMOVE - blueprint system
    "load_prompt",              # KEEP - used in example 005
    "preview_blueprint",        # REMOVE - blueprint system
    "render_for_llm",           # REMOVE - blueprint system
    "render_instruction",       # REMOVE - blueprint system
    "render_preview",           # REMOVE - blueprint system
]
```

### After Cleanup (Expected)

```python
__all__ = [
    "__version__",
    "cleanup_exported_version", # KEEP
    "export_version",           # KEEP
    "load_prompt",              # KEEP
]
```

## Dependencies Analysis (pyproject.toml)

### Current Dependencies (10 packages)

```toml
dependencies = [
    "pydantic>=2.6",          # KEEP - used by models
    "pydantic-settings>=2.2", # REMOVE - only used by settings package
    "rich>=13.7",             # REMOVE - only used by blueprint preview
    "jinja2>=3.1",            # KEEP - used by format parsers
    "orjson>=3.9",            # KEEP - used by JSON parsing
    "pyyaml>=6.0",            # KEEP - used by YAML parsing
    "regex>=2023.10",         # KEEP - used by versioning
    "eval_type_backport>=0.2",# KEEP - used by pydantic
    "tiktoken>=0.5.0",        # REMOVE - token counting
    "packaging>=23.0",        # KEEP - used by versioning
]
```

### After Cleanup (Expected: 7 packages)

Remove:
- `pydantic-settings>=2.2` (verify not used elsewhere)
- `rich>=13.7` (verify not used elsewhere)
- `tiktoken>=0.5.0` (token counting)

## Verification Summary

✅ All examples (003-006) run successfully without blueprint/adapter/token code
✅ Examples only use node networks and versioning features
✅ Settings package only used by code being removed (plus 1 dead import)
✅ No circular dependencies between kept and removed code
✅ All removed code is clearly identified and documented
✅ Public API changes clearly documented

**Phase 2 Complete**: Foundation ready for code removal
