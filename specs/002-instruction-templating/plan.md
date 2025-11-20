# Implementation Plan: Instruction Data Insertion with Multiple Templating Formats

**Branch**: `002-instruction-templating` | **Date**: 2025-01-28 | **Spec**: `/specs/002-instruction-templating/spec.md`
**Input**: Feature specification from `/specs/002-instruction-templating/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. Align every section with the `promptic Constitution` (clean architecture, SOLID, tests, docs, readability).

## Summary

This feature extends the context engineering library to support dynamic data insertion into instruction files using multiple templating formats. Designers can insert data into Markdown instructions using Python string format syntax (`{}` placeholders), use Jinja2 templating for complex logic in `.jinja` files, define custom patterns for YAML instructions, and express hierarchical logic directly in Markdown. The implementation introduces a template renderer abstraction in the use-case layer that dispatches to format-specific renderers based on instruction format, while maintaining clean architecture boundaries. Template rendering integrates with existing instruction loading flows, respects `InstructionFallbackPolicy` for error handling, and provides namespaced context variables (`data.*`, `memory.*`, `step.*`) including per-iteration loop context. Key technical approach: Format-specific renderers (MarkdownFormatRenderer, Jinja2FormatRenderer, YamlFormatRenderer) implementing a common interface, separate Jinja2 environment for instructions with shared base configuration, and context building that merges global and step-specific data.

## Technical Context

**Language/Version**: Python 3.11 (CPython)  
**Primary Dependencies**: `pydantic>=2`, `pydantic-settings`, `jinja2>=3.0` (templating for `.jinja` files and prompt templates), `regex` (for custom pattern matching in YAML), existing context engine dependencies (`rich`, `orjson`, `pytest`, `pytest-asyncio`, `hypothesis`)  
**Storage**: Instruction files stored as filesystem assets (Markdown/JSON/YAML/plain-text) with format auto-detection; template rendering operates on in-memory content loaded via existing `InstructionStore` interface  
**Testing**: `pytest` with markers (`unit`, `integration`, `contract`), `pytest-asyncio` for async scenarios, `hypothesis` for property-based validation of template rendering edge cases  
**Target Platform**: Python 3.11+ on Linux/macOS/Windows (pure library, no platform-specific code)  
**Project Type**: Single Python library (SDK surface only; no CLI or HTTP endpoints)  
**Performance Goals**: Template rendering completes in <10ms for typical instruction files (<1000 lines); support instructions with thousands of placeholders without excessive memory usage; Jinja2 environment initialization is lazy (created on first use)  
**Constraints**: Template rendering must preserve instruction formatting (indentation, whitespace) except where templating syntax explicitly modifies layout; nested dictionary access in Markdown must handle deep nesting (up to 10 levels); Jinja2 environment must be separate from prompt rendering environment but share base configuration  
**Scale/Scope**: Support instruction files up to 10,000 lines; handle templates with 1000+ placeholders; support all existing instruction formats (`md`, `txt`, `jinja`) plus YAML with custom patterns; integrate seamlessly with existing context engine rendering flows

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Architecture**: Clean Architecture layers: **Entities** remain unchanged (`InstructionNode`, `ContextBlueprint`); **Use Cases** (`TemplateRenderer`, format-specific renderers) in use-case layer (`src/promptic/pipeline/template_renderer.py`) depend only on domain entities and context interfaces; **Adapters** (format-specific renderer implementations) follow dependency inversion via `FormatRenderer` interface. SOLID: SRP enforced by separating format detection, template parsing, and rendering logic; DIP via `FormatRenderer` interface so use cases can swap implementations; OCP via pluggable format renderers without modifying core template renderer. Trade-off: Separate Jinja2 environment for instructions adds complexity but enables instruction-specific filters/globals without affecting prompt rendering (documented via `# AICODE-NOTE`). Integration point: Template rendering integrated into `ContextPreviewer._resolve_instruction_text()` which currently returns raw content; modification required to accept template context and route through renderer.

- **Testing Evidence**: **Unit tests**: Markdown format rendering with placeholders (`tests/unit/pipeline/test_template_renderer_markdown.py`), Jinja2 template rendering with conditionals/loops (`tests/unit/pipeline/test_template_renderer_jinja2.py`), YAML custom pattern rendering (`tests/unit/pipeline/test_template_renderer_yaml.py`), nested dictionary access (`tests/unit/pipeline/test_template_renderer_nested.py`), error handling with `InstructionFallbackPolicy` (`tests/unit/pipeline/test_template_renderer_errors.py`), context variable namespacing (`tests/unit/pipeline/test_template_renderer_context.py`). **Integration tests**: End-to-end instruction rendering with data slots (`tests/integration/test_instruction_templating.py`), loop step per-iteration rendering (`tests/integration/test_loop_iteration_templating.py`), format detection and routing (`tests/integration/test_format_detection.py`). **Contract tests**: Format renderer interface compliance (`tests/contract/test_format_renderer_interface.py`), context variable availability (`tests/contract/test_template_context_contract.py`). All tests run via `pytest` in CI.

- **Quality Gates**: Black (line-length 100) and isort (profile black) formatting enforced via `pre-commit` hooks; `pre-commit run --all-files` must pass before any commit. Static analysis via mypy (type checking) optional but recommended. No contributor may claim tooling unavailable—install dependencies per AGENTS.md.

- **Documentation & Traceability**: **docs_site/**: Markdown data insertion guide (`docs_site/context-engineering/markdown-templating.md`), Jinja2 templating guide (`docs_site/context-engineering/jinja2-templating.md`), YAML custom patterns guide (`docs_site/context-engineering/yaml-templating.md`), hierarchical Markdown guide (`docs_site/context-engineering/hierarchical-markdown.md`), context variables reference (`docs_site/context-engineering/template-context-variables.md`). **Specs**: `spec.md` and `plan.md` updated alongside code. **Examples**: `examples/markdown-templating/`, `examples/jinja2-templating/`, `examples/yaml-patterns/`, `examples/hierarchical-markdown/` with README, instruction files, sample data, runnable Python scripts. **AICODE tags**: Use `# AICODE-NOTE` for architecture decisions (separate Jinja2 environment, namespacing strategy), `# AICODE-TODO` for future work (Markdown hierarchy parsing), `# AICODE-ASK` for user questions (resolve before merge).

- **Readability & DX**: Template renderer functions limited to <100 logical lines; descriptive names (`render_markdown`, `render_jinja2`, `render_yaml`); small, focused modules (one renderer class per file where possible). All public APIs include docstrings explaining side effects, error handling, context variable availability. Private helpers include inline comments when template parsing logic is non-obvious. No `.md`/`.txt` status dumps in repo root—knowledge lives in specs, docs_site, or inline comments.

## Project Structure

### Documentation (this feature)

```text
specs/002-instruction-templating/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── instruction-templating.yaml
├── integration-analysis.md  # Analysis of context engine integration
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/promptic/
├── pipeline/            # Use case layer: blueprint processing
│   ├── template_renderer.py      # TemplateRenderer (dispatcher)
│   ├── format_renderers/         # Format-specific renderers
│   │   ├── __init__.py
│   │   ├── base.py               # FormatRenderer interface
│   │   ├── markdown.py           # MarkdownFormatRenderer
│   │   ├── jinja2.py             # Jinja2FormatRenderer
│   │   └── yaml.py               # YamlFormatRenderer
│   └── [existing files: builder.py, previewer.py, etc.]
│
├── context/             # Shared utilities
│   ├── template_context.py       # InstructionRenderContext builder
│   └── [existing files: errors.py, rendering.py]
│
└── [existing structure: blueprints/, instructions/, adapters/, settings/, sdk/]

tests/
├── contract/             # Contract tests
│   ├── test_format_renderer_interface.py
│   └── test_template_context_contract.py
├── integration/         # Integration tests
│   ├── test_instruction_templating.py
│   ├── test_loop_iteration_templating.py
│   └── test_format_detection.py
└── unit/                # Unit tests
    └── pipeline/
        ├── test_template_renderer_markdown.py
        ├── test_template_renderer_jinja2.py
        ├── test_template_renderer_yaml.py
        ├── test_template_renderer_nested.py
        ├── test_template_renderer_errors.py
        └── test_template_renderer_context.py

examples/
├── markdown-templating/          # User Story 1 examples
│   ├── README.md
│   ├── instruction.md
│   └── render_example.py
├── jinja2-templating/            # User Story 2 examples
│   ├── README.md
│   ├── instruction.jinja
│   └── render_example.py
├── yaml-patterns/                # User Story 3 examples
│   ├── README.md
│   ├── instruction.yaml
│   └── render_example.py
└── hierarchical-markdown/       # User Story 4 examples (P3)
    ├── README.md
    ├── instruction.md
    └── render_example.py
```

**Structure Decision**: Extends existing context engine structure with new template rendering modules in `pipeline/format_renderers/` following clean architecture. Format renderers are interfaces implemented as adapters, maintaining dependency inversion. Template context building is a shared utility in `context/`. Tests organized by type (unit/integration/contract) with format-specific test files. Examples demonstrate each templating format independently.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Separate Jinja2 environment for instructions | Instruction-specific filters/globals needed without affecting prompt rendering | Shared environment would couple instruction and prompt rendering, making it impossible to add instruction-specific helpers without risk to prompt templates |
| Format-specific renderer modules | Each format has distinct parsing/rendering logic; separation maintains SRP | Single monolithic renderer would violate SRP and make format-specific optimizations difficult |
