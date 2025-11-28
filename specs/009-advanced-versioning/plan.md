# Implementation Plan: Advanced Versioning System

**Branch**: `009-advanced-versioning` | **Date**: 2025-11-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/009-advanced-versioning/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. Align every section with the `promptic Constitution` (clean architecture, SOLID, tests, docs, readability).

## Summary

This feature extends the existing filesystem-based versioning system with enhanced configurability: support for multiple version delimiters ("_", ".", "-"), customizable version patterns via pydantic configuration, version postfixes with proper "latest" resolution logic (excluding pre-releases by default), and custom classifiers (e.g., language variants). Configuration is implemented via pydantic BaseModel (NOT BaseSettings) to avoid auto-resolution conflicts with host applications.

**Technical Approach**: Extend the existing `promptic.versioning` module by:
1. Adding `VersioningConfig` pydantic model with configurable delimiter, pattern, prerelease, and classifier settings
2. Refactoring `VersionedFileScanner` to accept config injection instead of hardcoded patterns
3. Extending `SemanticVersion` to support prerelease fields with proper ordering
4. Adding `ClassifierConfig` model and classifier extraction/filtering to version resolution
5. Updating SDK API functions to accept optional `config` parameter

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pydantic>=2.6, pydantic-settings>=2.2 (new), packaging>=23.0, regex>=2023.10  
**Storage**: Filesystem (no database)  
**Testing**: pytest, pytest-asyncio, hypothesis (property-based tests for version ordering)  
**Target Platform**: Cross-platform library (Linux, macOS, Windows)  
**Project Type**: Single Python package (library)  
**Performance Goals**: <100ms for directory scans with 100 files; pattern compilation cached at config instantiation  
**Constraints**: Backward compatibility required—existing code without config parameter must work identically  
**Scale/Scope**: Directories with <1000 versioned files; typical use case is 10-50 files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Architecture (P1: Clean Architecture & SOLID Boundaries)

**Entities → Use Cases → Interface Boundaries**:

```
Domain Layer (Entities):
├── VersioningConfig (pydantic BaseModel)
├── ClassifierConfig (pydantic BaseModel)
├── VersionPattern (regex abstraction)
├── VersionComponents (extracted version parts)
└── SemanticVersion (extended with prerelease)

Use Cases Layer:
├── VersionResolver (interface)
├── HierarchicalVersionResolver (hierarchical specs)
├── VersionExporter (export orchestration)
└── VersionCleanup (cleanup orchestration)

Adapter Layer:
├── VersionedFileScanner (filesystem scanning, receives config via injection)
├── FileSystemExporter (file operations)
└── FileSystemCleanup (directory operations)

SDK/API Layer:
├── render() - accepts optional config parameter
├── load_prompt() - accepts optional config parameter
└── export_version() - accepts optional config parameter
```

**SOLID Trade-offs & Mitigations**:
- **SRP**: `VersioningConfig` only handles validation; `VersionPattern` only handles pattern matching; `ClassifierConfig` only handles classifier definitions. No single class handles both storage and execution.
- **OCP**: New delimiters/classifiers added via configuration, not code changes. `VersionPattern.from_delimiter()` factory enables extension without modification.
- **LSP**: Extended `SemanticVersion` with prerelease still satisfies base comparison interface.
- **ISP**: `VersioningConfig` is a minimal BaseModel; `VersioningSettings` extends for env var resolution (opt-in).
- **DIP**: `VersionedFileScanner` receives `VersioningConfig` via constructor injection; no hardcoded patterns.

### Testing Evidence (P2: Evidence-Driven Testing)

**Unit Tests**:
- `test_versioning_config.py`: Config validation (valid/invalid inputs), default values, immutability
- `test_version_pattern.py`: Pattern generation for each delimiter ("_", ".", "-"), named capture group validation
- `test_semantic_version_prerelease.py`: Prerelease parsing, comparison (alpha < beta < rc < release), custom ordering
- `test_classifier_config.py`: Classifier validation, default value in allowed values
- `test_classifier_extraction.py`: Classifier segment extraction from filenames with strict ordering

**Integration Tests**:
- `test_version_resolution_with_config.py`: Full resolution flow with various config combinations
- `test_delimiter_resolution.py`: Multi-delimiter directory scanning
- `test_prerelease_resolution.py`: Latest resolution with/without prereleases
- `test_classifier_resolution.py`: Classifier filtering with version combinations
- `test_backward_compatibility.py`: Existing code without config works identically

**Property-Based Tests** (hypothesis):
- Version ordering consistency: `∀ v1, v2, v3: if v1 < v2 and v2 < v3 then v1 < v3`
- Prerelease ordering: `alpha < beta < rc < release` for any version base
- Classifier filtering idempotency: filtering twice with same classifier yields same result

### Quality Gates (P3: Automated Quality Gates)

- Black (line-length=100), isort (profile=black) formatting enforced
- `pre-commit run --all-files` required before commit
- `pytest tests/ -v` must pass with >90% coverage on new code
- mypy type checking for all new modules
- No linter errors in changed files

### Documentation & Traceability (P4)

**docs_site/ Updates**:
- `docs_site/guides/versioning-configuration.md` - Comprehensive config guide with examples
- `docs_site/reference/versioning-api.md` - API reference for `VersioningConfig`, `VersioningSettings`
- `docs_site/guides/version-classifiers.md` - Working with prompt classifiers
- `docs_site/guides/version-prereleases.md` - Pre-release handling and "latest" logic

**AICODE Comments**:
- `# AICODE-NOTE` in `VersioningConfig` explaining BaseModel vs BaseSettings choice
- `# AICODE-NOTE` in `VersionPattern` explaining regex pattern structure
- `# AICODE-NOTE` in prerelease comparison explaining ordering rules

### Readability & DX (P5)

- Config classes use descriptive field names (`delimiter`, `include_prerelease`, `prerelease_order`)
- Pattern generation in dedicated factory method `VersionPattern.from_delimiter()`
- Version comparison uses lookup table for prerelease ordering (no complex conditionals)
- All public APIs have docstrings explaining parameters, return values, and raised exceptions
- Files kept small: `config.py` (~150 lines), `pattern.py` (~100 lines), `classifier.py` (~80 lines)

## Project Structure

### Documentation (this feature)

```text
specs/009-advanced-versioning/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (internal API contracts)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/promptic/versioning/
├── __init__.py                 # Updated exports (VersioningConfig, ClassifierConfig)
├── config.py                   # NEW: VersioningConfig, VersioningSettings, ClassifierConfig
├── domain/
│   ├── __init__.py
│   ├── resolver.py             # MODIFIED: Accept config, classifier filtering
│   ├── exporter.py             # MODIFIED: Accept config parameter
│   ├── cleanup.py              # MODIFIED: Accept config parameter
│   ├── errors.py               # EXTENDED: InvalidVersionPatternError, ClassifierNotFoundError
│   └── pattern.py              # NEW: VersionPattern abstraction
├── adapters/
│   ├── __init__.py
│   └── scanner.py              # MODIFIED: Config injection, classifier extraction
└── utils/
    ├── __init__.py
    ├── cache.py                # EXISTING: Pattern cache
    ├── logging.py              # EXTENDED: Config/classifier logging
    └── semantic_version.py     # EXTENDED: Prerelease support

src/promptic/sdk/
└── api.py                      # MODIFIED: render(), load_prompt(), export_version() accept config

tests/versioning/
├── test_config.py              # NEW: Config validation tests
├── test_pattern.py             # NEW: Pattern generation tests
├── test_prerelease.py          # NEW: Prerelease comparison tests
├── test_classifier.py          # NEW: Classifier extraction/filtering tests
├── test_delimiter_resolution.py # NEW: Multi-delimiter integration tests
└── test_backward_compat.py     # NEW: Backward compatibility tests

docs_site/guides/
├── versioning-configuration.md # NEW: Config guide
├── version-classifiers.md      # NEW: Classifier guide
└── version-prereleases.md      # NEW: Prerelease guide
```

**Structure Decision**: Extends existing `src/promptic/versioning/` module with new files for config and pattern abstractions. Maintains clean architecture layering with domain entities separate from adapters.

## Complexity Tracking

> No Constitution violations requiring justification. All changes follow established patterns.

| Aspect | Complexity | Justification |
|--------|------------|---------------|
| `VersioningConfig` vs `VersioningSettings` | Moderate | Deliberate separation to prevent auto-resolution conflicts; well-documented pattern in pydantic ecosystem |
| Classifier segment ordering | Low | Strict ordering rule (`base-classifier-version-postfix`) eliminates parsing ambiguity |
| Prerelease comparison | Low | Standard semantic versioning rules; lookup table avoids complex conditionals |
