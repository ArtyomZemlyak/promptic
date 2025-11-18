# Implementation Plan: Context Engineering Library

**Branch**: `001-context-engine` | **Date**: 2025-11-18 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-context-engine/spec.md`

**Note**: Follow the `promptic Constitution` for clean layering, SOLID responsibilities, evidence-driven testing, automated gates, and documentation traceability.

## Summary

Deliver a Python 3.11+ library that lets designers define hierarchical context blueprints, plug arbitrary data/memory adapters, and execute instruction pipelines through the SDK. A dedicated `ContextMaterializer` (built in Phase 2 foundations) brokers every data/memory lookup so `ContextPreviewer`, `PipelineExecutor`, and SDK façades stay insulated from adapters. Per the latest clarification, `BlueprintBuilder` (T020) and `ContextPreviewer` (T021) must depend on the `ContextMaterializer` abstraction from their first commit, and unit/contract tests will assert that no preview/execution flow touches adapter registries directly. US2 later wires additional runtime behaviors (T034), but layering discipline is enforced Day 1.

## Technical Context

**Language/Version**: Python 3.11 (CPython)  
**Primary Dependencies**: `pydantic>=2`, `pydantic-settings`, `rich`, `jinja2`, `orjson`, plus optional adapter extras (`httpx`, `pandas`, `faiss-cpu`)  
**Storage**: Local filesystem for instruction assets by default; adapters abstract HTTP/file/vector sources for data/memory. No persistent DB bundled.  
**Testing**: `pytest`, `pytest-asyncio`, `hypothesis` (schema fuzzing), contract tests exercising SDK façades, integration suites for 5-step blueprints, unit suites per module.  
**Target Platform**: Linux/macOS developer machines, GitHub Actions CI; library consumed via importable SDK (no services).  
**Project Type**: Single Python package under `src/promptic/` with clean architecture subpackages (domain, pipeline, adapters, SDK).  
**Performance Goals**: Render 5-step blueprints with ≤100 instruction nodes in <500 ms; adapter registry init <200 ms; blueprint validation handles 1k nodes in <2 s; execution logs stream without blocking.  
**Constraints**: In-memory context payloads <256 MB via per-step budgets; zero direct network calls from domain/use-case layers; `ContextMaterializer` remains sole adapter touchpoint; functions <100 logical lines; follow Black/isort.  
**Scale/Scope**: Support dozens of concurrent blueprints per process with nested pipelines; MVP ships US1 fully, US2 adapter swaps, US3 execution loops; adapters can be extended without modifying core.

## Constitution Check

- **Architecture**: Domain layer hosts `ContextBlueprint`, `InstructionNode`, slots, and value objects. Use cases (`BlueprintBuilder`, `ContextPreviewer`, `PipelineExecutor`, `ContextMaterializer`) depend only on interfaces like `InstructionStore`, `DataSourceAdapter`, `MemoryProvider`. All slot resolution flows (even in US1) inject `ContextMaterializer` so adapter registries remain encapsulated per Principle P1; T034 in US2 expands orchestration but does not change the dependency graph. Any deviation requires `# AICODE-NOTE` justification.
- **Testing Evidence**: Contract + integration suites (`T017`–`T019`, `T028`–`T040`) cover blueprint preview, adapter swaps, and executor traversal. Unit suites (`tests/unit/pipeline/test_context_materializer.py`, preview/executor tests) mock adapters through the materializer to prove no direct registry access. Regression tests capture failure cases like missing assets, circular steps, and adapter errors.
- **Quality Gates**: Black (line length 100), isort (profile black), mypy (strict optional), and `pre-commit run --all-files` gate every commit. CI runs `pytest -m "unit or integration or contract"` plus coverage thresholds. Lint/format failures block merges (Principle P3).
- **Documentation & Traceability**: Update `docs_site/context-engineering/` guides (blueprint, adapter, execution), `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, contracts, and inline `# AICODE-*` comments whenever behavior changes. Record clarification answers under `## Clarifications` ASAP (Principle P4).
- **Readability & DX**: Keep modules ≤400 LOC, functions <100 logical lines, and naming descriptive (`render_context_preview`). Provide SDK façade helpers so designers avoid touching low-level modules. Capture non-obvious logic with `# AICODE-NOTE` comments instead of clever abstractions (Principle P5).

## Project Structure

### Documentation (this feature)

```text
specs/001-context-engine/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── spec.md
├── tasks.md
├── contracts/
│   └── context-engineering.yaml
└── checklists/
    ├── requirements.md
    └── solid.md
```

### Source Code (repository root)

```text
src/
└── promptic/
    ├── __init__.py
    ├── adapters/
    │   ├── __init__.py
    │   ├── registry.py
    │   ├── data/
    │   └── memory/
    ├── blueprints/
    │   ├── __init__.py
    │   ├── models.py
    │   └── serialization.py
    ├── instructions/
    │   ├── store.py
    │   └── cache.py
    ├── pipeline/
    │   ├── builder.py
    │   ├── previewer.py
    │   ├── executor.py
    │   ├── context_materializer.py
    │   ├── validation.py
    │   └── loggers.py
    ├── context/
    │   ├── rendering.py
    │   └── logging.py
    ├── settings/
    │   └── base.py
    └── sdk/
        ├── api.py
        ├── adapters.py
        ├── blueprints.py
        └── pipeline.py

tests/
├── unit/
├── integration/
└── contract/

docs_site/
└── context-engineering/
    ├── blueprint-guide.md
    ├── adapter-guide.md
    └── execution-recipes.md
```

**Structure Decision**: Single Python package with clean-architecture subpackages mirrors source-of-truth layering. Tests/documents mirror runtime directories so each user story remains independently testable/documented.

## Complexity Tracking

No Constitution deviations anticipated; leave table empty unless future changes require exceptions.
