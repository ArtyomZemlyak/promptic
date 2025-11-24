# Research: Prompt Versioning System

## Semantic Versioning Format & Normalization

- **Decision**: Use semantic versioning notation (v0.0.0) as the standard format, with support for simplified forms: `v1` (normalized to v1.0.0), `v1.1` (normalized to v1.1.0), and `v1.1.1` (full semantic version).
- **Rationale**: Semantic versioning is the industry standard for version notation, provides clear precedence rules (major.minor.patch), and enables intuitive version comparison. Supporting simplified forms (v1, v1.1) improves user ergonomics for common cases while maintaining consistent comparison logic through normalization.
- **Alternatives considered**:
  - Sequential numeric versions (v1, v2, v3): simpler but doesn't support minor/patch increments, making it less flexible for semantic versioning scenarios.
  - Date-based versions (v2024-01-28): provides chronological ordering but doesn't convey semantic meaning (major/minor/patch changes).
  - Custom version format: adds complexity without clear benefits over the established semantic versioning standard.

## Version Detection Strategy

- **Decision**: Extract version identifiers from filenames using regex patterns matching semantic versioning: `_v{N}`, `_v{N}.{N}`, or `_v{N}.{N}.{N}` (e.g., `_v1`, `_v1.1`, `_v1.1.1`). When multiple version patterns exist in a filename, extract the last matching pattern as the version identifier.
- **Rationale**: Filename-based version detection is filesystem-native, doesn't require metadata files, and integrates seamlessly with existing file-first mode. Using the last pattern handles edge cases (e.g., `prompt_v1.0_final_v2.1.md`) deterministically.
- **Alternatives considered**:
  - Metadata files (e.g., `.versions.json`): provides explicit version mapping but adds maintenance overhead and couples versioning with external files.
  - Directory-based versioning (version folders): provides clear separation but requires restructuring existing prompt hierarchies.
  - Git tags or git history: couples versioning with version control, contradicting the requirement for git-independent versioning.

## Version Resolution Architecture

- **Decision**: Separate version detection (extracting versions from filenames), version resolution (selecting appropriate files), and file loading into distinct services with `VersionResolver` interface in domain layer and `VersionedFileScanner` adapter implementation.
- **Rationale**: Clean architecture separation enables swapping version detection strategies without affecting resolution logic, maintains testability through interface mocking, and follows SRP by isolating filesystem operations in adapters. Dependency inversion ensures version resolution depends on abstractions rather than concrete implementations.
- **Alternatives considered**:
  - Monolithic version manager: violates SRP and makes testing difficult; tightly couples domain logic with filesystem operations.
  - Version resolution in file loading layer: mixes concerns and makes version-aware loading opt-in rather than transparent.

## Export Structure Preservation

- **Decision**: Export preserves the hierarchical directory structure of source prompts (not flattened), maintaining nested subdirectories and resolving path references in internal prompts to work correctly within the preserved structure.
- **Rationale**: Preserving structure maintains functional hierarchies in exported snapshots, ensures references remain valid after export, and enables exported hierarchies to work independently of source locations. Flattening would break relative path references and require complex path rewriting.
- **Alternatives considered**:
  - Flattened export structure: simpler directory layout but breaks relative path references and requires complex path resolution logic.
  - Archive-based export (zip, tar): preserves structure but requires extraction step, adds complexity for simple deployment scenarios.

## Cleanup Safety Mechanisms

- **Decision**: Use heuristics to distinguish export directories from source directories: export directories typically have version postfixes in names, contain preserved hierarchical structures matching source layouts, or have metadata indicating they were created by export. If validation is uncertain, require explicit confirmation.
- **Rationale**: Heuristic-based validation prevents accidental deletion of source prompts without requiring explicit marking of export directories. Explicit confirmation provides safety net when heuristics are uncertain.
- **Alternatives considered**:
  - Metadata file marking exports: explicit but adds maintenance overhead and requires cleanup of metadata files.
  - Whitelist/blacklist directories: provides explicit control but requires configuration management and doesn't scale well.

## Structured Logging Strategy

- **Decision**: Provide detailed structured logging with DEBUG/INFO/WARNING/ERROR levels covering all versioning operations, configurable via environment variable (`PROMPTIC_LOG_LEVEL`) with default level INFO. All log entries are structured with fields (version, path, operation, timestamp) for programmatic filtering and analysis.
- **Rationale**: Structured logging enables comprehensive diagnostics for debugging version resolution issues while configurability prevents log noise in production. Field-based structure allows filtering and analysis without parsing unstructured log messages.
- **Alternatives considered**:
  - Minimal logging (errors only): reduces log verbosity but limits diagnostic capabilities.
  - Always-on detailed logging: provides maximum diagnostics but creates excessive log volume in production.
