# Implementation Plan: File-First Prompt Hierarchy

**Branch**: `003-file-first-prompts` | **Date**: 2025-11-20 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/003-file-first-prompts/spec.md`

## Summary

Implement a `file_first` render mode that converts any blueprint into a compact persona/goals summary, emits references to on-disk instruction files, surfaces memory/log destinations, and provides structured metadata plus render metrics. The solution extends existing rendering pipelines (`promptic.pipeline.template_renderer`), blueprint serialization, and instruction stores while keeping the domain entities independent of delivery channels (CLI, SDK, hosted agents). Tests will verify token reduction, metadata integrity, reference validation, and backward compatibility with existing modes.

## Technical Context

**Language/Version**: Python ≥3.11 (per `pyproject.toml`)  
**Primary Dependencies**: Promptic core modules (pydantic, jinja2, rich, orjson, yaml) plus filesystem I/O  
**Storage**: File-based blueprints/instructions/memory folders (no new DB)  
**Testing**: pytest (+ pytest-asyncio) with existing unit/contract/integration suites  
**Target Platform**: Linux CLI + Python SDK (works cross-platform)  
**Project Type**: Single Python package under `src/promptic`  
**Performance Goals**: ≥60% token reduction compared to inline render (§SC-001) while keeping render latency near current preview mode (<500ms on sample blueprints)  
**Constraints**: Summary cap ≤120 tokens per instruction, nested references depth ≤3 by default, deterministic missing-file validation, zero additional internal throttling  
**Scale/Scope**: Blueprints with up to ~50 steps and nested instruction trees; expected to support dozens of concurrent renders executed via orchestration tools

## Constitution Check

- **Architecture**:  
  - Entities stay within `promptic.blueprints.models` and new DTOs (PromptHierarchyBlueprint, InstructionReference, MemoryChannel, RenderMetrics).  
  - Use cases (render orchestration) live in `promptic.pipeline.template_renderer` and builder/executor layers; new strategy registered without leaking IO beyond adapters.  
  - Interface adapters (CLI/SDK) only call exposed strategy and read metadata; dependency inversion maintained by injecting summary/reference services.  
  - SOLID deviations: none anticipated; each new helper (e.g., `FileSummaryService`, `ReferenceFormatter`) owns a single responsibility.
- **Testing Evidence**:  
  - Unit: new tests for summary generation, metadata tree building, file validation, base URL conversion, metrics calculations.  
  - Integration: `tests/integration/test_blueprint_preview_sdk.py` and `tests/integration/test_instruction_templating.py` extended to cover file-first flows.  
  - Contract: `tests/contract/test_template_context_contract.py` validates metadata schema (matching `contracts/file_first_renderer.yaml`).  
  - Regression: ensure legacy render modes remain unchanged (compare outputs in tests).  
- **Quality Gates**:  
  - Run Black/isort via pre-commit; ensure new files respect line-length 100.  
  - Add mypy coverage for new classes; update configuration if needed.  
  - `pytest tests -k file_first` plus full suite before PR.  
- **Documentation & Traceability**:  
  - Update `docs_site/context-engineering/blueprint-guide.md`, quickstart docs, and inline `AICODE-NOTE` markers near renderer entry points.  
  - Maintain spec/plan/research/data-model/quickstart/contract artifacts under `specs/003-file-first-prompts`.  
- **Readability & DX**:  
  - Keep helper functions under 40 LOC, prefer descriptive names (`build_reference_outline`, `format_memory_section`).  
  - Reuse existing builder hooks to avoid new god objects; document tricky logic with `AICODE-NOTE`.

## Project Structure

### Documentation (this feature)

```text
specs/003-file-first-prompts/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── file_first_renderer.yaml
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
src/promptic/
├── blueprints/
│   ├── models.py
│   └── serialization.py
├── instructions/
│   ├── store.py
│   └── cache.py
├── pipeline/
│   ├── builder.py
│   ├── context_materializer.py
│   ├── executor.py
│   ├── template_renderer.py
│   └── format_renderers/
└── sdk/
    └── blueprints.py

tests/
├── contract/
│   ├── test_blueprint_preview_sdk.py
│   ├── test_template_context_contract.py
│   └── test_pipeline_execute.py
├── integration/
│   ├── test_blueprint_preview_sdk.py
│   ├── test_instruction_templating.py
│   └── test_pipeline_executor.py
└── unit/
    ├── pipeline/test_template_renderer.py
    ├── blueprints/test_serialization.py
    └── instructions/test_store.py
```

**Structure Decision**: Continue with the existing single-package layout. New code will live inside `src/promptic/pipeline`, `src/promptic/blueprints`, and `src/promptic/instructions`, while tests are added to the matching unit/integration/contract suites shown above.

## Complexity Tracking

No Constitution violations anticipated; table intentionally left blank.

## Phase 0 – Research & Unknown Resolution

- Conducted desk research on metadata transport, reference linking, memory format governance, and rate-limiting (see `research.md`).  
- Outcomes:  
  - Confirmed JSON envelope structure and deterministic `id` derivation from file paths.  
  - Established optional `base_url` to produce absolute links when agents lack filesystem access.  
  - Codified user-defined memory formats with a documented fallback hierarchical `.md` template.  
  - Decided against internal throttling; instead expose render metrics so orchestrators can enforce their own limits.  
- Status: All open questions resolved; no `NEEDS CLARIFICATION` markers remain.

## Phase 1 – Design & Contracts

### Data Model
- Documented `PromptHierarchyBlueprint`, `InstructionReference`, `MemoryChannel`, and `RenderMetrics` entities (see `data-model.md`).  
- Defined constraints: summary token caps, tree depth, uniqueness of `id`s, mandatory memory guidance fields, and validation rules for missing files.

### Contracts & APIs
- Authored `contracts/file_first_renderer.yaml` (OpenAPI 3.0.3) to describe the SDK/CLI contract for `file_first` renders, including parameters (`base_url`, `depth_limit`), response schema, and error payloads.  
- Contract will be referenced by contract tests to ensure metadata stays backwards-compatible.

### Quickstart & Documentation Hooks
- `quickstart.md` shows CLI and SDK usage, optional memory format descriptors, and test commands.  
- docs_site updates will cite these steps and explain extension points (base URL, summary overrides, depth limit).  
- Inline `AICODE-NOTE` comments will point to spec sections when referencing file-first logic.

### Agent Context Update
- Run `.specify/scripts/bash/update-agent-context.sh cursor-agent` after code scaffolding to ensure Cursor agent instructions mention new render mode touchpoints (pipeline renderer, blueprint serialization, memory descriptors).

### Constitution Re-check
- **Architecture**: Entities/interfaces remain separated; injection-based strategy ensures DIP compliance.  
- **Testing**: Coverage plan mapped to concrete suites; render metrics validated via unit + integration tests.  
- **Quality Gates**: Black/isort/pre-commit remain mandatory; new OpenAPI contract included in CI.  
- **Documentation**: Quickstart + docs_site updates enumerated; spec/plan artifacts kept current.  
- **Readability**: Helper boundaries defined; tree traversal + summarization modules capped in size.

## Phase 2 – Build Plan & Validation

1. **Renderer Strategy & Metadata Builders**
   - Extend `template_renderer` with a `file_first` strategy that orchestrates persona, goals, step summaries, memory sections, and metrics.
   - Introduce helper classes (`FileSummaryService`, `ReferenceFormatter`, `MemoryDescriptorCollector`) wired through dependency injection.
2. **Blueprint & Instruction Enhancements**
   - Update `blueprints.serialization` to emit deterministic step IDs and to read optional summary overrides from blueprint metadata.
   - Enhance `instructions.store` to expose memory format descriptors and validate files upfront.
3. **CLI/SDK Surface**
   - Add `--render-mode file_first` and `--base-url` flags to CLI preview commands plus corresponding kwargs in SDK previewer.
   - Ensure CLI output aligns with quickstart examples (persona/goals block, steps list, memory block).
4. **Validation & Metrics**
   - Implement depth-limited tree traversal with cycle detection; raise descriptive errors for missing files or invalid recursion.
   - Compute `RenderMetrics` (before/after token counts, reference counts, missing paths) and expose in metadata JSON.
5. **Testing**
   - Unit tests for new helper classes and error cases.  
   - Integration tests covering sample blueprints (token reduction, reference validity, base URL output).  
   - Contract tests asserting response schema matches `file_first_renderer.yaml`.  
   - Regression tests ensuring legacy render modes still inline instructions by default.
6. **Documentation & Tooling**
   - Update docs_site guides, quickstart instructions, and add `AICODE-NOTE` markers in code.  
   - Run `pytest tests -k file_first`, full pytest suite, and `pre-commit run --all-files`.  
   - Capture metrics screenshots/logs for PR description.
