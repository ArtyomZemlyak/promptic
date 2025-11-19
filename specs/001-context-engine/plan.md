# Implementation Plan: Context Engineering Library

**Branch**: `001-context-engine` | **Date**: 2025-01-27 | **Spec**: `/specs/001-context-engine/spec.md`
**Input**: Feature specification from `/specs/001-context-engine/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. Align every section with the `promptic Constitution` (clean architecture, SOLID, tests, docs, readability).

## Summary

This feature delivers a pure Python library for context engineering—unifying prompts, instructions, data, and memory into hierarchical, executable blueprints. Designers author blueprints as YAML files without editing Python code; integrators plug arbitrary data/memory adapters; automation engineers execute pipelines with per-step instruction resolution and comprehensive audit logs. The library follows clean architecture (Entities → Use Cases → Adapters) with SOLID boundaries, ensuring preview/execution flows interact with adapters only through the `ContextMaterializer` abstraction.

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

- **Architecture**: Clean architecture layers enforced: Entities (`ContextBlueprint`, `InstructionNode`, `DataSlot`, `MemorySlot`) in domain layer; Use Cases (`BlueprintBuilder`, `ContextPreviewer`, `PipelineExecutor`, `ContextMaterializer`) in application layer; Adapters (`InstructionStore`, `DataSourceAdapter`, `MemoryProvider`) in infrastructure layer with dependencies pointing inward. SOLID principles: SRP (separate authoring, validation, rendering, execution); DIP (use cases depend on adapter interfaces); OCP (new adapters register without core edits); LSP (custom executors extend behavior); ISP (instruction lookups separate from execution control). Trade-offs: `ContextMaterializer` introduces an extra abstraction layer but enforces encapsulation and simplifies testing—documented via `# AICODE-NOTE`.

- **Testing Evidence**: Unit tests for domain models (`tests/unit/blueprints/test_models.py`), adapter contracts (`tests/unit/adapters/test_base.py`), instruction caching (`tests/unit/instructions/test_cache.py`), materializer fallback paths (`tests/unit/pipeline/test_context_materializer.py`). Integration tests: blueprint preview end-to-end (`tests/integration/test_blueprint_preview_sdk.py`), adapter swapping (`tests/integration/test_adapter_swaps.py`), full pipeline execution (`tests/integration/test_pipeline_executor.py`), instruction fallback scenarios (`tests/integration/test_instruction_fallbacks.py`). Contract tests: SDK blueprint preview API (`tests/contract/test_blueprint_preview_sdk.py`), pipeline execution API (`tests/contract/test_pipeline_execute.py`), adapter registration flows (`tests/contract/test_adapter_registry.py`). All tests run via `pytest -m "unit or integration or contract"` in CI.

- **Quality Gates**: Black (line-length 100) and isort (profile black) formatting enforced via `pre-commit` hooks; `pre-commit run --all-files` must pass before commits. Static analysis: mypy type checking (strict mode for public APIs). No contributor may claim tooling unavailable—install dependencies per AGENTS.md.

- **Documentation & Traceability**: Update `docs_site/context-engineering/` with blueprint authoring guide, adapter integration guide, execution recipes, and quickstart validation. Spec (`spec.md`), plan (`plan.md`), and inline docstrings stay synchronized. All `# AICODE-ASK` items resolved before merge; answers recorded in spec clarifications. Examples directory at repository root (`examples/`) organized by user story with README, blueprint YAML, sample data, and runnable Python scripts.

- **Readability & DX**: Public functions limited to <100 logical lines; descriptive names (e.g., `render_context_preview`, `resolve_data_slot`). Small, intention-revealing modules: `BlueprintBuilder` (<100 lines), `ContextPreviewer` (<100 lines), `PipelineExecutor` (traversal logic <100 lines, delegates to helpers). Dead experimental code deleted after each milestone. SDK façades (`src/promptic/sdk/blueprints.py`, `src/promptic/sdk/pipeline.py`) provide ergonomic entry points; internal complexity hidden behind clean interfaces.

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
src/
└── promptic/
    ├── __init__.py
    ├── blueprints/
    │   ├── __init__.py
    │   ├── models.py          # Domain entities (ContextBlueprint, BlueprintStep, InstructionNodeRef)
    │   └── serialization.py    # YAML/JSON Schema serialization
    ├── instructions/
    │   ├── __init__.py
    │   ├── store.py            # InstructionStore interface + filesystem implementation
    │   └── cache.py            # LRU caching for instruction assets
    ├── pipeline/
    │   ├── __init__.py
    │   ├── builder.py          # BlueprintBuilder use case
    │   ├── previewer.py        # ContextPreviewer use case
    │   ├── executor.py         # PipelineExecutor use case
    │   ├── context_materializer.py  # ContextMaterializer orchestration
    │   ├── validation.py       # BlueprintValidator
    │   ├── policies.py         # Per-step policy enforcement
    │   ├── hooks.py            # Mock agent integration hooks
    │   └── loggers.py          # Execution log writers (JSONL)
    ├── adapters/
    │   ├── __init__.py
    │   ├── registry.py         # AdapterRegistry, BaseAdapter, BaseMemoryProvider
    │   ├── data/
    │   │   ├── __init__.py
    │   │   ├── csv_loader.py   # Sample CSV data adapter
    │   │   └── http_fetcher.py # Sample HTTP data adapter
    │   └── memory/
    │       ├── __init__.py
    │       └── vector_store.py # Sample vector memory provider
    ├── context/
    │   ├── __init__.py
    │   ├── errors.py           # Domain exceptions + structured error types
    │   ├── logging.py           # JSONL event logging utility
    │   └── rendering.py       # Rich-based preview formatting
    ├── settings/
    │   ├── __init__.py
    │   └── base.py             # ContextEngineSettings (pydantic-settings)
    └── sdk/
        ├── __init__.py
        ├── api.py              # SDK façade entry points
        ├── blueprints.py       # Blueprint SDK helpers
        ├── pipeline.py         # Pipeline SDK helpers
        └── adapters.py         # Adapter registration SDK helpers

tests/
├── unit/
│   ├── blueprints/
│   │   ├── test_models.py
│   │   └── test_builder.py
│   ├── adapters/
│   │   ├── test_registry.py
│   │   └── test_base.py
│   ├── instructions/
│   │   └── test_cache.py
│   ├── pipeline/
│   │   ├── test_context_materializer.py
│   │   ├── test_executor.py
│   │   └── test_previewer.py
│   └── context/
│       ├── test_logging.py
│       └── test_errors.py
├── integration/
│   ├── test_blueprint_preview_sdk.py
│   ├── test_adapter_swaps.py
│   ├── test_pipeline_executor.py
│   ├── test_instruction_fallbacks.py
│   ├── test_performance.py
│   └── test_quickstart_validation.py
└── contract/
    ├── test_blueprint_preview_sdk.py
    ├── test_pipeline_execute.py
    └── test_adapter_registry.py

examples/
├── us1-blueprints/
│   ├── README.md
│   ├── simple_blueprint.yaml
│   ├── instructions/
│   │   └── step_instruction.md
│   └── run_preview.py
├── us2-adapters/
│   ├── README.md
│   ├── blueprint.yaml
│   ├── data/
│   │   └── sample.csv
│   └── swap_adapters.py
├── us3-pipelines/
│   ├── README.md
│   ├── hierarchical_blueprint.yaml
│   └── run_pipeline.py
└── complete/
    ├── README.md
    ├── research_flow.yaml
    ├── instructions/
    ├── data/
    └── end_to_end.py
```

**Structure Decision**: Single Python library project structure with clear separation of domain (`blueprints/models.py`), use cases (`pipeline/`), and adapters (`adapters/`). SDK layer (`sdk/`) provides ergonomic entry points while keeping internal complexity hidden. Examples directory at repository root demonstrates all functionality organized by user story plus end-to-end scenarios.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| ContextMaterializer abstraction layer | Enforces clean architecture by preventing preview/executor code from directly accessing adapter registries | Direct adapter lookups in use cases would create tight coupling, harder testing, and violate DIP—materializer interface allows mocking and keeps adapters swappable without core edits |
| Multi-format instruction support with JSON canonical | Supports designer ergonomics (Markdown/YAML) while maintaining internal consistency | Single format (e.g., JSON-only) would force designers to write JSON manually, reducing adoption; conversion layer keeps authoring flexible while preserving structured processing |
