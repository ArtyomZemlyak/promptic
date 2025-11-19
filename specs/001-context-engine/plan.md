# Implementation Plan: Context Engineering Library

**Branch**: `001-context-engine` | **Date**: 2025-01-28 | **Spec**: `/specs/001-context-engine/spec.md`
**Input**: Feature specification from `/specs/001-context-engine/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. Align every section with the `promptic Constitution` (clean architecture, SOLID, tests, docs, readability).

## Summary

This feature delivers a pure Python library for context engineering—constructing LLM-ready contexts from hierarchical blueprints. The library focuses solely on context construction (loading blueprints, rendering text for LLM input); execution is handled by external agent frameworks. Designers author blueprints as YAML files without editing Python code; integrators plug arbitrary data/memory adapters; users render contexts with minimal API (3 lines of Python code). The library follows clean architecture (Entities → Use Cases → Adapters) with SOLID boundaries, ensuring rendering flows interact with adapters only through the `ContextMaterializer` abstraction. Key technical approach: Pydantic models for blueprints, filesystem-backed instruction stores with caching, pluggable adapter registry, and separate rendering functions for preview (Rich formatting) vs LLM text output.

## Technical Context

**Language/Version**: Python 3.11 (CPython)  
**Primary Dependencies**: `pydantic>=2`, `pydantic-settings`, `rich` (preview rendering), `jinja2` (templating), `orjson` (JSON serialization), `pytest`, `pytest-asyncio`, `hypothesis` (property-based testing), optional adapter extras (`httpx`, `sqlalchemy`, `faiss-cpu`)  
**Storage**: Filesystem-backed instruction stores (Markdown/JSON/YAML/plain-text) with optional caching (LRU); data/memory adapters abstract storage (CSV, HTTP, vector DBs, etc.)  
**Testing**: `pytest` with markers (`unit`, `integration`, `contract`), `pytest-asyncio` for async adapters, `hypothesis` for property-based validation  
**Target Platform**: Python 3.11+ on Linux/macOS/Windows (pure library, no platform-specific code)  
**Project Type**: Single Python library (SDK surface only; no CLI or HTTP endpoints)  
**Performance Goals**: Optimize via profiling during development; size budgets (per-step context limits) serve as primary constraint mechanism  
**Constraints**: Per-step context size limits configurable via settings; instruction caching to avoid redundant file reads; streaming/chunking for large data payloads  
**Scale/Scope**: Support blueprints with 100+ steps; handle thousands of items in loop steps via batching; instruction assets stored as files (Git-friendly workflow)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Architecture**: Clean Architecture layers: **Entities** (`ContextBlueprint`, `InstructionNode`, `DataSlot`, `MemorySlot`) in domain layer; **Use Cases** (`BlueprintBuilder`, `ContextPreviewer`, rendering functions) in use-case layer depend only on interfaces (`InstructionStore`, `DataSourceAdapter`, `MemoryProvider`); **Adapters** (filesystem stores, CSV loaders, HTTP fetchers, vector DBs) in adapter layer. SOLID: SRP enforced by separating blueprint authoring, validation, rendering; DIP via `ContextMaterializer` abstraction so use cases never touch adapter registries directly; OCP via pluggable adapter registry. Trade-off: `ContextMaterializer` adds indirection but enables testability and adapter swapping without core changes (documented via `# AICODE-NOTE`).

- **Testing Evidence**: **Unit tests**: Blueprint schema validation (`tests/unit/blueprints/test_models.py`), adapter interface compliance (`tests/unit/adapters/test_contracts.py`), rendering logic (`tests/unit/pipeline/test_previewer.py`), instruction caching (`tests/unit/instructions/test_cache.py`). **Integration tests**: Multi-step blueprint rendering (`tests/integration/test_blueprint_rendering.py`), adapter swapping (`tests/integration/test_adapter_swapping.py`), minimal API usage (`tests/integration/test_minimal_api.py`). **Contract tests**: Adapter registration/resolution (`tests/contract/test_adapters.py`), SDK API contracts (`tests/contract/test_sdk_api.py`). All tests run via `pytest` in CI.

- **Quality Gates**: Black (line-length 100) and isort (profile black) formatting enforced via `pre-commit` hooks; `pre-commit run --all-files` must pass before any commit. Static analysis via mypy (type checking) optional but recommended. No contributor may claim tooling unavailable—install dependencies per AGENTS.md.

- **Documentation & Traceability**: **docs_site/**: Blueprint schema reference (`docs_site/context-engineering/blueprint-schema.md`), adapter integration guide (`docs_site/context-engineering/adapter-guide.md`), rendering walkthrough (`docs_site/context-engineering/rendering-guide.md`), minimal API quickstart (`docs_site/context-engineering/quickstart.md`). **Specs**: `spec.md` and `plan.md` updated alongside code. **Examples**: `examples/us1-blueprints/`, `examples/us2-adapters/`, `examples/complete/` with README, blueprint YAML, sample data, runnable Python scripts (3 lines max for basic usage). **AICODE tags**: Use `# AICODE-NOTE` for architecture decisions, `# AICODE-TODO` for future work, `# AICODE-ASK` for user questions (resolve before merge).

- **Readability & DX**: Public functions limited to <100 logical lines; descriptive names (`load_blueprint`, `render_preview`, `render_for_llm`); small, focused modules (one class per file where possible). All public APIs include docstrings explaining side effects, error handling, contracts. Private helpers include inline comments when logic is non-obvious. No `.md`/`.txt` status dumps in repo root—knowledge lives in specs, docs_site, or inline comments.

## Project Structure

### Documentation (this feature)

```text
specs/001-context-engine/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── context-engineering.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/promptic/
├── __init__.py
├── blueprints/          # Domain layer: blueprint entities
│   ├── __init__.py
│   ├── models.py        # ContextBlueprint, BlueprintStep, DataSlot, MemorySlot
│   └── serialization.py
├── instructions/        # Domain/Adapter layer: instruction assets
│   ├── __init__.py
│   ├── cache.py         # InstructionCache (LRU)
│   └── store.py         # FilesystemInstructionStore
├── pipeline/            # Use case layer: blueprint processing
│   ├── __init__.py
│   ├── builder.py       # BlueprintBuilder
│   ├── validation.py   # BlueprintValidator
│   ├── previewer.py    # ContextPreviewer
│   ├── context_materializer.py  # ContextMaterializer (adapter orchestration)
│   └── policies.py      # PolicyEngine (size budgets)
├── adapters/            # Adapter layer: data/memory sources
│   ├── __init__.py
│   ├── registry.py      # AdapterRegistry
│   ├── data/            # DataSourceAdapter implementations
│   │   ├── __init__.py
│   │   ├── csv_loader.py
│   │   └── http_fetcher.py
│   └── memory/          # MemoryProvider implementations
│       ├── __init__.py
│       └── vector_store.py
├── context/             # Shared utilities
│   ├── __init__.py
│   ├── errors.py        # Domain exceptions
│   └── rendering.py     # Rendering utilities
├── settings/             # Configuration
│   ├── __init__.py
│   └── base.py          # ContextEngineSettings
└── sdk/                  # Public API surface
    ├── __init__.py
    ├── api.py            # Core SDK functions (load_blueprint, render_preview, render_for_llm)
    ├── blueprints.py     # Blueprint-specific SDK
    └── adapters.py       # Adapter registration helpers

tests/
├── contract/             # Contract tests
│   ├── test_adapters.py
│   └── test_sdk_api.py
├── integration/         # Integration tests
│   ├── test_blueprint_rendering.py
│   ├── test_adapter_swapping.py
│   └── test_minimal_api.py
└── unit/                # Unit tests
    ├── blueprints/
    │   └── test_models.py
    ├── adapters/
    │   └── test_contracts.py
    ├── pipeline/
    │   └── test_previewer.py
    └── instructions/
        └── test_cache.py

examples/
├── us1-blueprints/       # User Story 1 examples
│   ├── README.md
│   ├── simple_blueprint.yaml
│   └── run_preview.py
├── us2-adapters/         # User Story 2 examples
│   ├── README.md
│   ├── blueprint.yaml
│   └── swap_adapters.py
└── complete/            # End-to-end examples
    ├── README.md
    ├── blueprint.yaml
    └── end_to_end.py
```

**Structure Decision**: Single Python library structure with clean architecture layers. Domain entities in `blueprints/`, use cases in `pipeline/`, adapters in `adapters/`, public API in `sdk/`. Tests organized by type (unit/integration/contract). Examples demonstrate minimal API usage (3 lines max for basic usage).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
