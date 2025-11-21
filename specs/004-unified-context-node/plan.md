# Implementation Plan: Unified Context Node Architecture

**Branch**: `004-unified-context-node` | **Date**: 2025-01-27 | **Spec**: `/specs/004-unified-context-node/spec.md`
**Input**: Feature specification from `/specs/004-unified-context-node/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. Align every section with the `promptic Constitution` (clean architecture, SOLID, tests, docs, readability).

## Summary

This feature introduces a unified `ContextNode` architecture that abstracts away the distinction between blueprints, instructions, data, and memory. All context elements become recursive `ContextNode` structures that can contain content in multiple formats (YAML, Jinja2, Markdown, JSON) and reference other nodes, forming a network. All formats parse to JSON as the canonical internal representation. This enables flexible composition where any node can reference any other node regardless of its semantic role (instruction, data, memory, blueprint). The architecture provides format parser registry with pluggable parsers, cycle detection, depth limiting, resource limits (size and token-based), and backward compatibility adapters for existing `ContextBlueprint`/`InstructionNode` models.

## Technical Context

**Language/Version**: Python 3.11 (CPython)  
**Primary Dependencies**: `pydantic>=2`, `pydantic-settings`, `jinja2` (templating), `pyyaml>=6.0` (YAML parsing), `orjson` (JSON serialization), `tiktoken` (token counting), `rich` (preview rendering), `pytest`, `pytest-asyncio`, `hypothesis` (property-based testing)  
**Storage**: Filesystem-backed node storage (YAML, Markdown, Jinja2, JSON files) with optional caching; in-memory nodes supported for programmatic creation  
**Testing**: `pytest` with markers (`unit`, `integration`, `contract`), `pytest-asyncio` for async operations, `hypothesis` for property-based validation  
**Target Platform**: Python 3.11+ on Linux/macOS/Windows (pure library, no platform-specific code)  
**Project Type**: Single Python library (extends existing SDK; no CLI or HTTP endpoints)  
**Performance Goals**: Network loading completes in <2 seconds for networks with <50 nodes; format detection accuracy >95% for files with standard extensions; token counting uses efficient tiktoken library  
**Constraints**: Configurable resource limits (default 10MB per node, 1000 nodes per network, plus token limits per node and per network); max depth limit (default 10 levels) to prevent stack overflow; token counting performed on final rendered content to accurately reflect LLM context usage  
**Scale/Scope**: Support node networks with 100+ nodes; handle multi-format parsing and conversion; support recursive structures with 3+ levels of nesting; maintain backward compatibility with existing blueprint/instruction models

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Architecture**:
  - **Entities (Domain Layer)**: `ContextNode` (unified domain entity), `FormatParser` (interface), `NodeReferenceResolver` (interface), `TokenCounter` (interface)
  - **Use Cases (Application Layer)**: `NodeNetworkBuilder` (orchestrates loading, reference resolution, network construction), `FormatParserRegistry` (manages parser registration)
  - **Adapters (Infrastructure Layer)**: Format parser implementations (`YAMLParser`, `MarkdownParser`, `Jinja2Parser`, `JSONParser`), filesystem reference resolver, tiktoken-based token counter, legacy adapters (`LegacyBlueprintAdapter`, `LegacyInstructionAdapter`)
  - **SOLID Trade-offs**:
    - **SRP**: Separated format detection, parsing, JSON conversion, reference resolution, and network building into distinct classes. Format parser registry knows about all parsers (intentional coupling documented via `# AICODE-NOTE`).
    - **OCP**: Format parser registry allows adding new parsers without modifying core code. Reference resolver interface enables pluggable resolution strategies.
    - **DIP**: Network building depends on `NodeReferenceResolver` and `TokenCounter` interfaces, not concrete implementations. Format parsers implement `FormatParser` interface.
    - **LSP**: All format parsers are substitutable through `FormatParser` interface. All reference resolvers are substitutable through `NodeReferenceResolver` interface.
    - **ISP**: Interfaces are focused (`FormatParser` for parsing, `NodeReferenceResolver` for resolution, `TokenCounter` for counting) rather than monolithic.

- **Testing Evidence**:
  - **Unit Tests**: Each format parser (YAML, Jinja2, Markdown, JSON) with format detection, parsing, and JSON conversion; `NodeNetworkBuilder` with mocked resolvers; cycle detection algorithm; depth limit enforcement; resource limit validation (size, tokens); legacy adapters mapping old models to nodes; token counter with tiktoken integration
  - **Integration Tests**: Loading multi-format node networks (4 formats); recursive structures with 3+ levels of nesting; backward compatibility scenarios (existing blueprint YAML files with new node system); network loading performance (<2 seconds for <50 nodes); format detection accuracy (>95% for standard extensions)
  - **Contract Tests**: `FormatParser` interface contract (detection, parsing, JSON conversion); `NodeReferenceResolver` interface contract (path resolution, reference validation); `TokenCounter` interface contract (model-specific counting)
  - **Validation Tests**: Circular reference detection (100% of cycles identified); missing reference handling; path resolution (relative and absolute); schema validation (optional, non-blocking)

- **Quality Gates**:
  - Black formatting (line-length=100) and isort (profile=black) enforced via `pre-commit run --all-files` before commit
  - Static analysis: mypy type checking (strict mode) for new code
  - All tests must pass: `pytest tests/ -v` (unit, integration, contract)
  - Pre-commit hooks configured in `.pre-commit-config.yaml` (already exists)

- **Documentation & Traceability**:
  - **docs_site/**: "Multi-format context nodes" guide, "Recursive node networks" guide, "Unified node architecture" overview, migration guide from old to new architecture, format parser extension guide
  - **Specs/Plans**: This plan.md, data-model.md (Phase 1), research.md (Phase 0), contracts/ (Phase 1), quickstart.md (Phase 1)
  - **AICODE-* Comments**: Format detection strategy (`# AICODE-NOTE`), JSON conversion rationale (`# AICODE-NOTE`), backward compatibility approach (`# AICODE-NOTE`), network traversal and cycle detection (`# AICODE-NOTE`), token counting strategy (`# AICODE-NOTE`), format parser registry intentional coupling (`# AICODE-NOTE`)

- **Readability & DX**:
  - Public functions limited to <100 logical lines; descriptive names (e.g., `detect_format_from_content`, `build_node_network_from_references`, `validate_network_structure`)
  - Format parser implementations focused and testable in isolation (single responsibility per parser)
  - Clear separation between domain entities, use cases, and adapters (clean architecture layers)
  - Comprehensive docstrings for all public APIs explaining side effects, error handling, and contracts
  - Inline comments for non-obvious logic (cycle detection algorithm, token counting implementation)

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/promptic/
├── context/              # Existing: context rendering, template context
│   └── nodes/            # NEW: ContextNode domain entity, node network models
├── blueprints/           # Existing: ContextBlueprint models (legacy)
│   └── adapters/         # NEW: LegacyBlueprintAdapter, LegacyInstructionAdapter
├── instructions/         # Existing: InstructionNode models (legacy)
│   └── adapters/         # NEW: LegacyInstructionAdapter (shared with blueprints)
├── pipeline/             # Existing: blueprint building, validation, execution
│   └── network/          # NEW: NodeNetworkBuilder use case, network validation
├── format_parsers/       # NEW: Format parser implementations and registry
│   ├── base.py           # FormatParser interface
│   ├── registry.py       # FormatParserRegistry
│   ├── yaml_parser.py    # YAMLParser implementation
│   ├── markdown_parser.py # MarkdownParser implementation
│   ├── jinja2_parser.py  # Jinja2Parser implementation
│   └── json_parser.py    # JSONParser implementation
├── resolvers/            # NEW: Reference resolution strategies
│   ├── base.py           # NodeReferenceResolver interface
│   └── filesystem.py     # FilesystemReferenceResolver implementation
├── token_counting/       # NEW: Token counting with tiktoken
│   ├── base.py           # TokenCounter interface
│   └── tiktoken_counter.py # TiktokenTokenCounter implementation
└── sdk/                   # Existing: SDK API surface
    └── nodes.py          # NEW: load_node_network, render_node_network APIs

tests/
├── contract/
│   └── test_format_parser_contract.py      # NEW: FormatParser interface contract
│   └── test_reference_resolver_contract.py # NEW: NodeReferenceResolver interface contract
│   └── test_token_counter_contract.py      # NEW: TokenCounter interface contract
├── integration/
│   └── test_node_networks.py               # NEW: Multi-format networks, recursion
│   └── test_backward_compatibility.py      # NEW: Legacy adapter integration
│   └── test_format_parsing.py              # NEW: Format detection and conversion
└── unit/
    ├── format_parsers/                     # NEW: Individual parser tests
    │   ├── test_yaml_parser.py
    │   ├── test_markdown_parser.py
    │   ├── test_jinja2_parser.py
    │   └── test_json_parser.py
    ├── network/                            # NEW: Network building and validation
    │   ├── test_network_builder.py
    │   ├── test_cycle_detection.py
    │   ├── test_depth_limits.py
    │   └── test_resource_limits.py
    ├── resolvers/                          # NEW: Reference resolution tests
    │   └── test_filesystem_resolver.py
    ├── token_counting/                     # NEW: Token counting tests
    │   └── test_tiktoken_counter.py
    └── adapters/                           # NEW: Legacy adapter tests
        ├── test_legacy_blueprint_adapter.py
        └── test_legacy_instruction_adapter.py
```

**Structure Decision**: Single Python library project (Option 1). New code extends existing `src/promptic/` structure with new subpackages for format parsing, network building, reference resolution, and token counting. Legacy adapters placed in `blueprints/adapters/` and `instructions/adapters/` to maintain backward compatibility. Tests follow existing structure (contract/, integration/, unit/) with new test modules for each component.

## Constitution Check (Post-Phase 1 Design)

*Re-evaluated after Phase 1 design artifacts (data-model.md, contracts/, quickstart.md) completed.*

- **Architecture**: ✅ **PASS** - Design maintains clean architecture layers:
  - Domain entities (`ContextNode`, `NodeReference`) in domain layer
  - Use cases (`NodeNetworkBuilder`) in application layer
  - Adapters (format parsers, resolvers, token counters, legacy adapters) in infrastructure layer
  - SOLID principles maintained: SRP (separated concerns), OCP (pluggable parsers), DIP (interface-based dependencies), LSP (substitutable parsers/resolvers), ISP (focused interfaces)

- **Testing Evidence**: ✅ **PASS** - Comprehensive test plan defined:
  - Unit tests for each format parser, network builder, cycle detection, resource limits, legacy adapters, token counting
  - Integration tests for multi-format networks, recursive structures, backward compatibility, performance
  - Contract tests for `FormatParser`, `NodeReferenceResolver`, `TokenCounter` interfaces
  - All tests documented in Constitution Check section above

- **Quality Gates**: ✅ **PASS** - All gates satisfied:
  - Black formatting (line-length=100) and isort (profile=black) enforced via pre-commit
  - mypy type checking (strict mode) for new code
  - All tests must pass: `pytest tests/ -v`
  - Pre-commit hooks configured

- **Documentation & Traceability**: ✅ **PASS** - All documentation artifacts created:
  - `research.md`: Technical decisions and rationale
  - `data-model.md`: Complete entity definitions with validation rules
  - `contracts/unified-context-node.yaml`: OpenAPI contract for API surface
  - `quickstart.md`: Usage examples and integration guide
  - `plan.md`: This implementation plan
  - Agent context updated via `update-agent-context.sh`
  - AICODE-* comments documented in Constitution Check section

- **Readability & DX**: ✅ **PASS** - Design maintains readability:
  - Public functions limited to <100 logical lines
  - Descriptive names (e.g., `build_node_network_from_references`, `validate_network_structure`)
  - Format parser implementations focused and testable in isolation
  - Clear separation between domain entities, use cases, and adapters
  - Comprehensive docstrings for all public APIs
  - Inline comments for non-obvious logic (cycle detection, token counting)

**Gate Status**: ✅ **ALL GATES PASS** - No violations detected. Implementation can proceed to Phase 2 (task breakdown).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*No violations detected - this section intentionally left empty.*
