# Implementation Plan: Remove Unused Code from Library

**Branch**: `006-remove-unused-code` | **Date**: 2025-01-27 | **Spec**: `/specs/006-remove-unused-code/spec.md`
**Input**: Feature specification from `/specs/006-remove-unused-code/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. Align every section with the `promptic Constitution` (clean architecture, SOLID, tests, docs, readability).

## Summary

This feature removes all unused code from the promptic library that is not used in examples 003, 004, 005, 006. The library will be simplified to focus solely on node network loading/rendering (features 003, 004) and versioning (features 005, 006). All blueprint-related code, adapter system, token counting, settings, format renderers, and related pipeline modules will be removed. The technical approach involves systematic code analysis to identify dependencies, removal of unused packages/modules, updating public API exports, cleaning up tests, and updating documentation. This is a breaking change that intentionally removes legacy architecture to align with the simplified node-based approach.

## Technical Context

**Language/Version**: Python 3.11 (CPython, per `pyproject.toml`)  
**Primary Dependencies**: `pydantic>=2.6`, `pyyaml>=6.0`, `jinja2>=3.1`, `orjson>=3.9`, `packaging>=23.0` (for versioning), `regex>=2023.10` (for version parsing). Remove: `tiktoken` (token counting), `pydantic-settings` (if only used by settings), `rich` (if only used by blueprint preview).  
**Storage**: Filesystem-based (no database). Node networks loaded from YAML/Markdown/JSON/Jinja2 files. Versioned prompts stored as files with version suffixes.  
**Testing**: `pytest>=7.4`, `pytest-asyncio>=0.23` for existing tests. Remove tests for deleted features. Add ImportError tests to verify removed features cannot be imported.  
**Target Platform**: Python 3.11+ on Linux/macOS/Windows (pure library, no platform-specific code)  
**Project Type**: Single Python library (SDK surface only; no CLI or HTTP endpoints)  
**Performance Goals**: No performance regressions. Examples 003-006 should run at same or better speed after cleanup (fewer imports, less code to load).  
**Constraints**: Must preserve all functionality used in examples 003-006. Breaking changes are acceptable (intentional removal of unused features). All examples must continue to work without modification.  
**Scale/Scope**: Codebase cleanup affecting ~15-20 packages/modules for removal. Public API reduced from ~10 functions to ~5 functions. Test suite reduced by removing blueprint/adapter/token counting tests.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Architecture**: Clean Architecture preserved - domain entities (ContextNode, NodeNetwork) remain in `promptic.context.nodes`, use cases (node loading, rendering) remain in `promptic.sdk.nodes`, versioning remains in `promptic.versioning`. Removed layers (blueprints, adapters, settings) were adapter/interface layers that are no longer needed. SOLID: Each remaining module has single responsibility (node loading, rendering, versioning, format parsing, reference resolution). No trade-offs needed - removal simplifies architecture.

- **Testing Evidence**:
  - Unit tests: Verify examples 003-006 run successfully after cleanup (`tests/integration/test_*.py` for examples)
  - Integration tests: Verify no blueprint/adapter/token counting imports work (`tests/integration/test_import_errors.py` - new)
  - Contract tests: Verify public API exports only expected functions (`tests/contract/test_public_api.py` - updated)
  - Regression tests: Verify node network loading/rendering still works (`tests/integration/test_node_networks.py`)
  - All tests must pass: `pytest tests/ -v` before and after cleanup

- **Quality Gates**:
  - Black formatting (line-length=100): `black --line-length=100 src/ tests/`
  - isort import sorting: `isort --profile=black --line-length=100 src/ tests/`
  - Pre-commit hooks: `pre-commit run --all-files` (MANDATORY before commit)
  - Static analysis: Verify no unused imports remain (mypy or manual review)
  - Dependency check: Verify removed dependencies (tiktoken, pydantic-settings if unused, rich if unused) are removed from `pyproject.toml`

- **Documentation & Traceability**:
  - Update `README.md` to reflect simplified architecture (remove blueprint/adapter references)
  - Remove blueprint/adapter documentation from `docs_site/` (if exists)
  - Update `specs/006-remove-unused-code/` artifacts (this plan, research.md, data-model.md, quickstart.md)
  - Add `# AICODE-NOTE:` comments in code explaining why certain modules were removed
  - Update `CHANGELOG.md` (if exists) with breaking changes

- **Readability & DX**:
  - Removal of dead code improves readability (fewer files to navigate)
  - Simplified public API (5 functions vs 10) improves developer experience
  - Clear ImportError messages when removed features are imported (helpful error messages)
  - Updated README.md with clear examples of remaining functionality
  - No unnecessary complexity - only code used by examples 003-006 remains

## Project Structure

### Documentation (this feature)

```text
specs/006-remove-unused-code/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
├── spec.md              # Feature specification (input)
├── clarifications.md    # Additional code analysis (input)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/promptic/
├── __init__.py                    # Public API (KEEP: load_prompt, export_version, cleanup_exported_version)
├── sdk/
│   ├── __init__.py
│   ├── nodes.py                   # KEEP: load_node_network, render_node_network
│   ├── api.py                      # UPDATE: Remove blueprint functions, keep versioning functions
│   ├── blueprints.py               # REMOVE (FR-014)
│   └── adapters.py                 # REMOVE (FR-015)
├── context/
│   ├── __init__.py
│   ├── nodes/                      # KEEP: ContextNode, NodeNetwork, models, errors
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── errors.py               # KEEP (used by node network)
│   │   └── ...
│   ├── rendering.py                # REMOVE (FR-021)
│   ├── template_context.py         # REMOVE (FR-022)
│   ├── logging.py                  # REMOVE (FR-023)
│   └── errors.py                   # REMOVE (FR-024, node network uses nodes.errors)
├── pipeline/
│   ├── __init__.py
│   ├── network/
│   │   └── builder.py              # KEEP: NodeNetworkBuilder
│   ├── builder.py                  # REMOVE (FR-016)
│   ├── previewer.py                # REMOVE (FR-016)
│   ├── executor.py                 # REMOVE (FR-016)
│   ├── context_materializer.py     # REMOVE (FR-017)
│   ├── template_renderer.py        # REMOVE (FR-018)
│   ├── validation.py               # REMOVE (FR-019)
│   ├── hooks.py                    # REMOVE (FR-020)
│   ├── loggers.py                  # REMOVE (FR-020)
│   ├── policies.py                 # REMOVE (FR-020)
│   └── format_renderers/           # REMOVE (FR-026)
│       ├── base.py
│       ├── file_first.py
│       ├── jinja2.py
│       ├── markdown.py
│       ├── markdown_hierarchy.py
│       └── yaml.py
├── versioning/                     # KEEP: load_prompt, export_version, cleanup_exported_version
│   ├── __init__.py
│   ├── resolver.py
│   └── ...
├── format_parsers/                  # KEEP: yaml, markdown, json, jinja2 parsers
│   ├── __init__.py
│   ├── yaml.py
│   ├── markdown.py
│   ├── json.py
│   └── jinja2.py
├── resolvers/                       # KEEP: filesystem resolver
│   ├── __init__.py
│   └── filesystem.py
├── blueprints/                      # REMOVE (FR-001): entire package
├── adapters/                        # REMOVE (FR-002): entire package
├── instructions/                    # REMOVE (FR-013): entire package
├── settings/                        # REMOVE (FR-025): entire package
└── token_counting/                 # REMOVE (FR-003): entire package

tests/
├── contract/
│   ├── test_public_api.py           # UPDATE: Verify only expected functions exported
│   └── ...                         # REMOVE: blueprint/adapter contract tests
├── integration/
│   ├── test_node_networks.py        # KEEP: Verify examples 003-006 work
│   ├── test_import_errors.py        # NEW: Verify removed features cannot be imported
│   └── ...                         # REMOVE: blueprint/adapter integration tests
└── unit/
    ├── blueprints/                  # REMOVE: entire directory
    ├── adapters/                    # REMOVE: entire directory
    ├── instructions/                # REMOVE: entire directory
    ├── token_counting/              # REMOVE: entire directory
    ├── nodes/                       # KEEP: node network tests
    ├── versioning/                  # KEEP: versioning tests
    └── ...
```

**Structure Decision**: Single Python library project. Code removal affects ~15-20 packages/modules. Structure remains the same, but many subdirectories are removed entirely. Core functionality (node networks, versioning, format parsing, reference resolution) is preserved in simplified structure.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations - code removal simplifies architecture and improves readability. All removals are justified by lack of usage in examples 003-006.

## Constitution Check (Post-Design)

*Re-evaluated after Phase 1 design completion.*

- **Architecture**: ✅ PASS - Clean Architecture preserved. Domain entities (ContextNode, NodeNetwork) remain isolated. Use cases (node loading, rendering, versioning) remain in SDK layer. Removed layers were adapter/interface layers that added unnecessary complexity. SOLID principles maintained - each remaining module has single responsibility.

- **Testing Evidence**: ✅ PASS - Test strategy defined:
  - Unit tests for examples 003-006 (existing)
  - Integration tests for import errors (new: `test_import_errors.py`)
  - Contract tests for public API (updated: `test_public_api.py`)
  - Regression tests for node networks (existing)
  - All tests documented in research.md and quickstart.md

- **Quality Gates**: ✅ PASS - All quality gates defined:
  - Black/isort formatting specified
  - Pre-commit hooks mandatory
  - Static analysis (mypy/manual review)
  - Dependency cleanup verification
  - All gates documented in Constitution Check section

- **Documentation & Traceability**: ✅ PASS - Documentation plan complete:
  - `research.md` documents all removal decisions
  - `data-model.md` describes remaining entities
  - `quickstart.md` provides usage examples
  - `contracts/cleanup-contract.yaml` defines API contract
  - README.md update planned
  - AICODE-NOTE comments planned for code

- **Readability & DX**: ✅ PASS - Readability improved:
  - Dead code removal reduces navigation complexity
  - Simplified public API (5 functions vs 10)
  - Clear examples in quickstart.md
  - Migration guide provided for users of removed features
  - No unnecessary complexity added

**GATE STATUS**: ✅ ALL GATES PASS - Ready to proceed to Phase 2 (task breakdown)
