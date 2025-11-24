# Implementation Plan: Prompt Versioning System

**Branch**: `005-prompt-versioning` | **Date**: 2025-01-28 | **Spec**: `/specs/005-prompt-versioning/spec.md`
**Input**: Feature specification from `/specs/005-prompt-versioning/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. Align every section with the `promptic Constitution` (clean architecture, SOLID, tests, docs, readability).

## Summary

This feature delivers a filesystem-based versioning system for prompts that operates independently of git or external version control systems. The library provides version management capabilities for both inline and file-first modes, supporting hierarchical versioning structures where root prompts and nested prompts can each have multiple versions. Versioning is handled entirely through file naming conventions (semantic versioning notation like `v1.0.0`, `v1`, `v1.1`) and directory scanning. The system supports loading prompts by folder (defaulting to latest version) or specific version identifiers, hierarchical version specifications for complex prompt hierarchies, exporting complete version snapshots with preserved directory structure, and safe cleanup of exported versions. Key technical approach: `VersionResolver` interface in domain layer, `VersionedFileScanner` adapter for filesystem operations, `VersionExporter` and `VersionCleanup` use cases, semantic versioning with normalization support, structured logging with configurable levels, and caching for performance optimization.

## Technical Context

**Language/Version**: Python 3.11 (CPython)  
**Primary Dependencies**: `pydantic>=2`, `pydantic-settings`, existing promptic dependencies (`rich`, `jinja2`, `orjson`), `pytest`, `pytest-asyncio`, `packaging` (for semantic versioning comparison), `structlog` or standard `logging` (for structured logging)  
**Storage**: Filesystem-based version detection and export operations. Version information stored in file naming conventions (postfixes like `_v1.0.0`, `_v1`, `_v1.1`). Export creates directory structures preserving hierarchical layout. No additional storage requirements beyond filesystem.  
**Testing**: `pytest` with markers (`unit`, `integration`, `contract`), `pytest-asyncio` for async operations if needed, property-based testing with `hypothesis` for version comparison edge cases  
**Target Platform**: Python 3.11+ on Linux/macOS/Windows (pure library, no platform-specific code)  
**Project Type**: Single Python library (SDK surface only; extends existing promptic library)  
**Performance Goals**: Version resolution should complete in <100ms for directories with <50 versioned files. Export operations should complete in <5 seconds for hierarchies with up to 50 referenced files (SC-005). Directory scanning results cached to avoid repeated filesystem operations.  
**Constraints**: Semantic versioning normalization must be consistent and deterministic. Version comparison must follow standard semantic versioning rules (major.minor.patch precedence). Export operations must be atomic (all or nothing) to prevent incomplete hierarchies. Cleanup operations must validate targets to prevent accidental deletion of source prompts. Logging level configurable via environment variable to prevent log noise in production.  
**Scale/Scope**: Support prompt hierarchies with 100+ versioned files per directory. Handle version resolution for nested hierarchies with 3+ levels of depth. Support exporting hierarchies with up to 50 referenced files. Cache version listings per directory with invalidation on directory modification time changes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Architecture**: Clean architecture layers maintained: **Domain layer** contains `VersionResolver` interface (abstraction for version resolution strategies) and use cases `VersionExporter`, `VersionCleanup` (orchestration logic). **Use case layer** (pipeline/) integrates version resolution into `NodeNetworkBuilder` via version parameters. **Adapter layer** (resolvers/, instructions/) contains `VersionedFileScanner` (filesystem scanning implementation), `FileSystemExporter`, `FileSystemCleanup` (filesystem operations). Dependencies point inward: adapters implement domain interfaces, use cases depend on domain abstractions. SOLID enforcement: SRP - version detection, resolution, export, cleanup are separate services; DIP - version resolution depends on `VersionResolver` interface, not concrete filesystem implementations; OCP - new version detection strategies can be added via new adapter implementations. Entities (prompts, nodes) remain unaware of versioning details; versioning applied at loading/rendering boundary.

- **Testing Evidence**: **Unit tests**: version detection logic (filename parsing with semantic versioning patterns, normalization v1→v1.0.0, v1.1→v1.1.0), version comparison (semantic versioning precedence rules, latest determination), version resolution (latest vs specific versions, hierarchical specifications), export orchestration (file discovery, path resolution), cleanup validation (export directory detection, source directory protection). **Integration tests**: loading prompts with various version specifications (latest, specific versions, hierarchical), exporting complex hierarchies (3+ levels of nesting, 50+ referenced files), cleaning up exported directories, version resolution with both inline and file-first render modes. **Contract tests**: `VersionResolver` interface contract (resolve_version method), export interface contract (preserved structure, resolved paths), cleanup interface contract (safe deletion). All run via `pytest tests/ -v` in CI. Test coverage >80% for core use cases (SC-008).

- **Quality Gates**: Black (line-length 100) and isort (profile black) formatting enforced via `pre-commit` hooks; `pre-commit run --all-files` must pass before any commit. Static analysis via mypy (type checking) optional but recommended. No contributor may claim tooling unavailable—install dependencies per AGENTS.md.

- **Documentation & Traceability**: **docs_site/**: Prompt versioning guide (`docs_site/prompt-versioning/versioning-guide.md`) covering version naming conventions, loading specific versions, hierarchical versioning, exporting versions, cleanup operations. **Specs**: `spec.md` and `plan.md` updated alongside code. **Examples**: `examples/versioning/` with versioned prompt hierarchies, export examples, cleanup examples. **AICODE tags**: Use `# AICODE-NOTE` for version detection strategy (semantic versioning patterns, normalization rules), resolution logic (hierarchical specifications, latest defaults), export structure (preserved hierarchy, path resolution), cleanup safeguards (export directory detection). Resolve any `AICODE-ASK` prompts before merge.

- **Readability & DX**: Public functions limited to <100 logical lines; descriptive names (`resolve_version_from_directory`, `extract_version_from_filename`, `normalize_semantic_version`, `export_version_hierarchy`, `cleanup_exported_version`); small, focused modules (one class per file where possible). Version detection uses clear regex patterns with comments explaining semantic versioning matching rules. Version comparison logic avoids complex nested conditionals by normalizing to full semantic versions first. All public APIs include docstrings explaining side effects, error handling (VersionNotFoundError, ExportError, etc.), contracts. Private helpers include inline comments when logic is non-obvious (version normalization, path resolution during export). No `.md`/`.txt` status dumps in repo root—knowledge lives in specs, docs_site, or inline comments.

## Project Structure

### Documentation (this feature)

```text
specs/005-prompt-versioning/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── prompt-versioning.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/promptic/
├── versioning/           # New package for versioning functionality
│   ├── __init__.py
│   ├── domain/           # Domain layer: interfaces and use cases
│   │   ├── __init__.py
│   │   ├── resolver.py   # VersionResolver interface
│   │   ├── exporter.py   # VersionExporter use case
│   │   └── cleanup.py    # VersionCleanup use case
│   ├── adapters/         # Adapter layer: filesystem implementations
│   │   ├── __init__.py
│   │   ├── scanner.py    # VersionedFileScanner
│   │   ├── filesystem_exporter.py  # FileSystemExporter
│   │   └── filesystem_cleanup.py   # FileSystemCleanup
│   └── utils/            # Versioning utilities
│       ├── __init__.py
│       ├── semantic_version.py  # Semantic version parsing, normalization, comparison
│       └── cache.py      # Version listing cache
├── resolvers/             # Existing package - extend with version-aware resolution
│   ├── __init__.py
│   ├── base.py          # Extend base resolver interface
│   └── filesystem.py    # Extend filesystem resolver with version support
├── pipeline/
│   └── network/
│       └── builder.py   # Update NodeNetworkBuilder to accept version parameters
├── instructions/
│   └── store.py         # Extend to support version-aware file discovery
└── sdk/
    └── api.py           # Add versioning functions to SDK API

tests/
├── unit/
│   └── versioning/      # Unit tests for versioning components
│       ├── test_semantic_version.py
│       ├── test_resolver.py
│       ├── test_exporter.py
│       └── test_cleanup.py
├── integration/
│   └── versioning/      # Integration tests for versioning workflows
│       ├── test_version_loading.py
│       ├── test_version_export.py
│       └── test_version_cleanup.py
└── contract/
    └── versioning/      # Contract tests for versioning interfaces
        ├── test_version_resolver_contract.py
        └── test_exporter_contract.py
```

**Structure Decision**: Following existing promptic library structure, versioning functionality is organized as a new `versioning/` package within `src/promptic/` with clear separation between domain layer (interfaces and use cases), adapter layer (filesystem implementations), and utility modules (semantic versioning logic, caching). Existing packages (`resolvers/`, `pipeline/network/`, `instructions/`, `sdk/`) are extended to integrate versioning capabilities without disrupting existing functionality. Test structure mirrors source structure with dedicated `versioning/` directories under `unit/`, `integration/`, and `contract/` test categories.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| | | |
