# Implementation Plan: Instruction Provider Fallbacks

**Branch**: `001-context-engine` | **Date**: 2025-11-19 | **Spec**: [`spec.md`](./spec.md)  
**Input**: Feature specification from `/specs/001-context-engine/spec.md`

**Note**: This plan focuses on closing SOLID checklist gap **CHK016** by defining explicit fallback semantics when alternate instruction providers substitute into preview/execution flows.

## Summary

Define contractual fallback policies for instruction providers so blueprint previews and pipeline executions remain LSP-compliant when swapping instruction stores. Work adds policy metadata to instruction assets/materializer contracts, updates acceptance tests/docs, and wires SDK guidance so adapters can degrade predictably (error, warn-with-placeholder, noop). Deliverables include updated spec/plan/tasks, expanded research, data model changes, contract additions, and quickstart guidance proving adapters can swap without core code edits.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.11 (CPython)  
**Primary Dependencies**: `pydantic`, `pydantic-settings`, `rich`, `jinja2`, `orjson`, `pytest`, `pytest-asyncio`, `hypothesis`  
**Storage**: Local filesystem instruction assets by default; adapters encapsulate HTTP/CSV/vector stores  
**Testing**: `pytest` (unit/integration/contract) with adapter/materializer stubs for substitution scenarios  
**Target Platform**: Importable Python SDK (no CLI/HTTP services) running on Linux/macOS dev hosts + CI  
**Project Type**: Single Python package under `src/promptic/` with clean architecture subpackages  
**Performance Goals**: Preserve existing preview/execution budgets (≤500 ms preview for 5-step blueprints; adapter registry init <200 ms) while adding fallback checks with <5% overhead  
**Constraints**: Context payloads <256 MB, functions <100 logical lines, adapters accessed only via `ContextMaterializer`  
**Scale/Scope**: Support dozens of blueprints per process; multiple instruction providers (filesystem + remote) can coexist without core changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Architecture**: Instruction fallback logic lives in the use-case layer (`ContextMaterializer` and `PipelineExecutor`). Domain models (`InstructionNode`, `InstructionProviderPolicy`) describe allowable degradation. SDK façade remains adapter-agnostic—only receives policy outcomes. No direct adapter imports outside materializer.
- **Testing Evidence**:
  - Unit: `tests/unit/pipeline/test_context_materializer.py` extended for fallback policies, plus new instruction cache/provider tests.
  - Integration: `tests/integration/test_pipeline_executor.py` and `test_adapter_swaps.py` prove degraded runs still pass without core edits.
  - Contract: `tests/contract/test_pipeline_execute.py` + new contract cases verifying structured fallback diagnostics.
- **Quality Gates**: Run Black/isort with line length 100, `pytest -m "unit or integration or contract"`, and `pre-commit run --all-files` before committing.
- **Documentation & Traceability**: Update `spec.md` (Edge Cases + FR-004), `plan.md`, `tasks.md`, `data-model.md`, `contracts/context-engineering.yaml`, `docs_site/context-engineering/adapter-guide.md`, `execution-recipes.md`, and quickstart fallback section. Capture rationale in `# AICODE-NOTE` near fallback code.
- **Readability & DX**: Introduce `InstructionFallbackPolicy` enum + helper functions (<100 lines each). Reuse existing logging infrastructure for diagnostics instead of bespoke systems.

## Project Structure

### Documentation (this feature)

```text
specs/001-context-engine/
├── plan.md              # Updated with fallback strategy (this file)
├── research.md          # Phase 0 findings (includes fallback semantics)
├── data-model.md        # Phase 1 entity rules (to include fallback policy fields)
├── quickstart.md        # Phase 1 guide (will gain fallback usage section)
├── contracts/
│   └── context-engineering.yaml  # Phase 1 API contracts
└── tasks.md             # Produced separately by /speckit.tasks
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
src/
└── promptic/
    ├── adapters/
    │   ├── data/
    │   └── memory/
    ├── blueprints/
    ├── context/
    ├── instructions/
    ├── pipeline/
    └── sdk/

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: Single Python package with clean architecture layering; fallback work touches `instructions/`, `pipeline/context_materializer.py`, `pipeline/executor.py`, and SDK façades while keeping adapters isolated.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| _None_ | — | — |

## Phase 0: Outline & Research

- Capture the CHK016 gap as a research question: “What observable fallback modes keep instruction providers LSP-compliant?”  
- Summarize findings (filesystem vs remote store parity, diagnostics expectations) inside `research.md` with Decision/Rationale/Alternatives.  
- Identify dependencies (existing `InstructionNode`, `ContextMaterializer`, logging) and ensure no new runtime tech is required.  
- Output: updated `research.md` (already revised with fallback semantics).

## Phase 1: Design & Contracts

1. **Data Model updates** (`data-model.md`):
   - Add `InstructionFallbackPolicy` enum and describe validation (default `error`).
   - Document how policies attach to instruction providers or blueprint references.
2. **Contracts** (`contracts/context-engineering.yaml`):
   - Extend preview/execution responses to include `fallback_mode`, `warnings`, and `placeholder` payloads.
   - Clarify adapter registration metadata for supported fallback policies.
3. **Quickstart & Docs** (`quickstart.md`, `docs_site/context-engineering/{adapter-guide,execution-recipes}.md`):
   - Add scenarios showing provider swap (filesystem → HTTP) that triggers `warn` fallback, including log snippet.
4. **Agent context**:
   - Run `.specify/scripts/bash/update-agent-context.sh cursor-agent` so shared memory records the new fallback requirement.

## Phase 2: Planning Outcomes

- Re-evaluate Constitution Check after design artifacts are updated; ensure SRP/OCP proof now includes fallback policies.  
- Produce handoff summary for `/speckit.tasks` describing implementation/test/doc updates needed (materializer, executor, SDK, docs).  
- Artifacts ready: `plan.md` (this file), refreshed `research.md`, plus TODOs for data-model, contracts, quickstart/doc updates.
