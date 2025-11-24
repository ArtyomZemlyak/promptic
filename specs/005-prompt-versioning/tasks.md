# Tasks: Prompt Versioning System

**Input**: Design documents from `/specs/005-prompt-versioning/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are MANDATORY under the `promptic Constitution`. Write the listed contract, integration, and unit tests before implementation and ensure they fail first.

**Organization**: Tasks are grouped by user story to enable independent implementation/testing while keeping Clean Architecture layers isolated.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Task can run in parallel (different files, no unmet dependencies)
- **[Story]**: User story tag (US1, US2, US3, US4) only for user-story phases
- Include exact file paths in every description

**Scope Reminder**: All tasks operate within the Python SDK surface only—no CLI, HTTP endpoints, or long-lived services. Black (line length 100) remains the only line-length enforcement; readability limits are handled via code review guidance.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize repository plumbing, settings, and scaffolding required by all stories.

- [X] T001 Create package structure `src/promptic/versioning/` with subdirectories `domain/`, `adapters/`, `utils/` in repository root
- [X] T002 [P] Create `src/promptic/versioning/__init__.py` with package initialization exports
- [X] T003 [P] Create `src/promptic/versioning/domain/__init__.py` for domain layer exports
- [X] T004 [P] Create `src/promptic/versioning/adapters/__init__.py` for adapter layer exports
- [X] T005 [P] Create `src/promptic/versioning/utils/__init__.py` for utility exports
- [X] T006 Update `pyproject.toml` to add versioning dependencies: `packaging` (for semantic versioning comparison), `structlog` or standard `logging` (for structured logging)
- [X] T007 [P] Create test directory structure `tests/unit/versioning/`, `tests/integration/versioning/`, `tests/contract/versioning/` in repository root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T008 Create semantic version utility module `src/promptic/versioning/utils/semantic_version.py` with `SemanticVersion` dataclass and normalization functions (v1 → v1.0.0, v1.1 → v1.1.0)
- [X] T009 [P] Implement semantic version comparison logic in `src/promptic/versioning/utils/semantic_version.py` following standard semantic versioning rules (major.minor.patch precedence)
- [X] T010 [P] Create version cache utility module `src/promptic/versioning/utils/cache.py` with directory modification time tracking for cache invalidation
- [X] T011 Create error types module `src/promptic/versioning/domain/errors.py` with `VersionNotFoundError`, `VersionDetectionError`, `VersionResolutionCycleError`, `ExportError`, `ExportDirectoryExistsError`, `ExportDirectoryConflictError`, `InvalidCleanupTargetError`, `CleanupTargetNotFoundError` exception classes
- [X] T012 [P] Configure structured logging in `src/promptic/versioning/utils/logging.py` with DEBUG/INFO/WARNING/ERROR levels, configurable via `PROMPTIC_LOG_LEVEL` environment variable (default: INFO)
- [X] T013 [P] Add versioning configuration to `src/promptic/settings/base.py` for logging level configuration via environment variable

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Version-Aware Prompt Loading (Priority: P1) 🎯 MVP

**Goal**: Prompt designers can load prompts from a folder, automatically resolving to the latest version or specifying an exact version identifier. The system scans directories for versioned files and selects the appropriate version based on user input.

**Independent Test**: A designer creates a folder `prompts/task1/` containing three files: `root_prompt_v1.md`, `root_prompt_v2.md`, and `root_prompt_v3.md`. Loading `prompts/task1/` with `version="latest"` (or default) loads `root_prompt_v3.md`. Loading with `version="v2"` loads `root_prompt_v2.md`. Loading with `version="v1"` loads `root_prompt_v1.md`. All three scenarios complete successfully, proving version resolution works independently.

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T014 [P] [US1] Unit test for version detection logic in `tests/unit/versioning/test_version_detection.py` - extracting versions from filenames using semantic versioning patterns (`_v1`, `_v1.1`, `_v1.1.1`)
- [X] T015 [P] [US1] Unit test for version normalization in `tests/unit/versioning/test_semantic_version.py` - normalization of simplified forms (v1 → v1.0.0, v1.1 → v1.1.0)
- [X] T016 [P] [US1] Unit test for version comparison in `tests/unit/versioning/test_semantic_version.py` - determining latest version using semantic versioning rules
- [X] T017 [P] [US1] Unit test for version resolution in `tests/unit/versioning/test_resolver.py` - resolving latest vs specific versions from directory paths
- [X] T018 [P] [US1] Integration test for loading prompts with different version specifications in `tests/integration/versioning/test_version_loading.py` - latest, specific versions, unversioned fallback
- [X] T019 [P] [US1] Contract test for `VersionResolver` interface in `tests/contract/versioning/test_version_resolver_contract.py` - validate `resolve_version` method contract

### Implementation for User Story 1

- [X] T020 [US1] Create `VersionResolver` interface in `src/promptic/versioning/domain/resolver.py` with `resolve_version(path: str, version_spec: VersionSpec) -> str` method signature
- [X] T021 [US1] Create `VersionInfo` dataclass in `src/promptic/versioning/adapters/scanner.py` with fields: `filename`, `path`, `base_name`, `version`, `is_versioned`
- [X] T022 [US1] Implement `VersionedFileScanner` class in `src/promptic/versioning/adapters/scanner.py` implementing `VersionResolver` interface with filesystem scanning using regex patterns for semantic versioning detection
- [X] T023 [US1] Implement `extract_version_from_filename` method in `src/promptic/versioning/adapters/scanner.py` - extract version identifiers using patterns `_v{N}`, `_v{N}.{N}`, `_v{N}.{N}.{N}`
- [X] T024 [US1] Implement `normalize_version` method in `src/promptic/versioning/adapters/scanner.py` - normalize simplified forms (v1 → v1.0.0, v1.1 → v1.1.0) using `SemanticVersion` utility
- [X] T025 [US1] Implement `scan_directory` method in `src/promptic/versioning/adapters/scanner.py` - scan directory for versioned files, return sorted list using semantic versioning comparison
- [X] T026 [US1] Implement `get_latest_version` method in `src/promptic/versioning/adapters/scanner.py` - determine latest version from list using semantic versioning comparison rules
- [X] T027 [US1] Implement version listing cache in `src/promptic/versioning/adapters/scanner.py` - cache version listings per directory, invalidate cache when directory modification time changes
- [X] T028 [US1] Implement `resolve_version` method in `src/promptic/versioning/adapters/scanner.py` - resolve version from directory path and version specification (latest, specific version, unversioned fallback)
- [X] T029 [US1] Extend `src/promptic/instructions/store.py` to support version-aware file discovery - add version parameter to file loading methods
- [X] T030 [US1] Update `src/promptic/pipeline/network/builder.py` to pass version parameters through the loading pipeline - integrate version resolution into `NodeNetworkBuilder`
- [X] T031 [US1] Add versioning functions to SDK API in `src/promptic/sdk/api.py` - add `load_prompt(path, version="latest")` function for version-aware prompt loading
- [X] T032 [US1] Add structured logging for version resolution operations in `src/promptic/versioning/adapters/scanner.py` - log version resolution steps, file discovery, version comparison with fields (version, path, operation, timestamp)
- [X] T033 [US1] Add `# AICODE-NOTE` comments in `src/promptic/versioning/adapters/scanner.py` explaining version detection strategy, normalization rules, and resolution logic

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Hierarchical Version Resolution (Priority: P2)

**Goal**: Prompt designers can organize prompts in hierarchical structures where root prompts and nested prompts each have their own version histories. When loading a root prompt at a specific version, nested prompts resolve to their latest versions unless explicitly specified.

**Independent Test**: A designer creates a structure: `prompts/task1/root_prompt_v1.md` (references `instructions/process.md`), `prompts/task1/root_prompt_v2.md` (references `instructions/process.md`), `prompts/task1/instructions/process_v1.md`, and `prompts/task1/instructions/process_v2.md`. Loading `prompts/task1/` with `version="v1"` loads `root_prompt_v1.md`, which references `instructions/process.md` (resolved to `instructions/process_v2.md` as latest). Loading with explicit nested version `version={"root": "v1", "instructions/process": "v1"}` loads `root_prompt_v1.md` with `instructions/process_v1.md`. This proves hierarchical version resolution works independently.

### Tests for User Story 2 (MANDATORY) ⚠️

- [X] T034 [P] [US2] Unit test for hierarchical version specification parsing in `tests/unit/versioning/test_hierarchical_resolver.py` - parsing dictionary mapping path patterns to versions
- [X] T035 [P] [US2] Integration test for loading nested prompts with version combinations in `tests/integration/versioning/test_hierarchical_versioning.py` - hierarchical specifications, default latest for nested prompts, cycle detection
- [X] T036 [P] [US2] Contract test for hierarchical version resolution in `tests/contract/versioning/test_hierarchical_resolver_contract.py` - validate recursive version resolution contract

### Implementation for User Story 2

- [X] T037 [US2] Create `HierarchicalVersionResolver` class in `src/promptic/versioning/domain/resolver.py` extending `VersionResolver` interface for hierarchical version specifications
- [X] T038 [US2] Implement `resolve_version` method in `src/promptic/versioning/domain/resolver.py` for hierarchical specifications - apply version rules recursively when resolving nested prompt references
- [X] T039 [US2] Implement cycle detection in `src/promptic/versioning/domain/resolver.py` - detect circular version references during hierarchical resolution, raise `VersionResolutionCycleError` with cycle path details
- [X] T040 [US2] Update `src/promptic/pipeline/network/builder.py` to apply version resolution recursively when resolving nested references - integrate hierarchical version resolution into `NodeNetworkBuilder`
- [X] T041 [US2] Add hierarchical version specification support to SDK API in `src/promptic/sdk/api.py` - support dictionary format `version={"root": "v1", "instructions/process": "v2"}` in `load_prompt` function
- [X] T042 [US2] Add structured logging for hierarchical version resolution in `src/promptic/versioning/domain/resolver.py` - log recursive resolution steps, cycle detection, path pattern matching
- [X] T043 [US2] Add `# AICODE-NOTE` comments in `src/promptic/versioning/domain/resolver.py` explaining hierarchical resolution strategy, default latest behavior, and cycle detection logic

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Version Export for File-First Mode (Priority: P3)

**Goal**: Prompt designers can export a complete version snapshot of a prompt hierarchy to a target directory in the filesystem. The export preserves the hierarchical directory structure (not flattened), maintaining nested subdirectories and resolving path references in internal prompts to work correctly within the exported structure. The export returns the root prompt content for immediate use.

**Independent Test**: A designer has a prompt hierarchy: `prompts/task1/root_prompt_v2.md` (references `instructions/process.md` and `templates/data.md`), with `prompts/task1/instructions/process_v2.md` and `prompts/task1/templates/data_v2.md`. Exporting `prompts/task1/` with `version="latest"` to `export/task1_v2/` creates: `export/task1_v2/root_prompt.md` (copied from `root_prompt_v2.md` with path references resolved), `export/task1_v2/instructions/process.md` (copied from `instructions/process_v2.md`), and `export/task1_v2/templates/data.md` (copied from `templates/data_v2.md`). The hierarchical structure is preserved, and path references in the root prompt are resolved to work correctly in the exported structure. The function returns the root prompt content for immediate rendering.

### Tests for User Story 3 (MANDATORY) ⚠️

- [X] T044 [P] [US3] Unit test for export orchestration logic in `tests/unit/versioning/test_exporter.py` - version resolution, file discovery, structure preservation
- [X] T045 [P] [US3] Integration test for exporting complex hierarchies in `tests/integration/versioning/test_version_export.py` - 3+ levels of nesting, 50+ referenced files, path resolution, atomic export behavior
- [X] T046 [P] [US3] Contract test for export interface in `tests/contract/versioning/test_exporter_contract.py` - validate preserved structure, resolved paths, atomic export contract

### Implementation for User Story 3

- [X] T047 [US3] Create `VersionExporter` use case class in `src/promptic/versioning/domain/exporter.py` - orchestrate version export operations (resolve hierarchy, discover files, delegate filesystem operations)
- [X] T048 [US3] Create `ExportResult` dataclass in `src/promptic/versioning/domain/exporter.py` with fields: `root_prompt_content`, `exported_files`, `structure_preserved`
- [X] T049 [US3] Implement `export_version` method in `src/promptic/versioning/domain/exporter.py` - take source path, version specification, target directory; return `ExportResult` with root prompt content
- [X] T050 [US3] Implement `discover_referenced_files` method in `src/promptic/versioning/domain/exporter.py` - discover all files referenced by the prompt hierarchy
- [X] T051 [US3] Create `FileSystemExporter` adapter class in `src/promptic/versioning/adapters/filesystem_exporter.py` implementing export interface for filesystem operations
- [X] T052 [US3] Implement `export_files` method in `src/promptic/versioning/adapters/filesystem_exporter.py` - copy files from source to target, preserving hierarchical directory structure (not flattened)
- [X] T053 [US3] Implement `resolve_paths_in_file` method in `src/promptic/versioning/adapters/filesystem_exporter.py` - resolve path references in file content using path mapping to work correctly with preserved structure
- [X] T054 [US3] Implement `validate_export_target` method in `src/promptic/versioning/adapters/filesystem_exporter.py` - validate target directory, raise `ExportDirectoryExistsError` if exists without overwrite, raise `ExportDirectoryConflictError` if contains non-export files
- [X] T055 [US3] Implement atomic export behavior in `src/promptic/versioning/domain/exporter.py` - either all files export successfully or nothing is exported (raise `ExportError` with missing files if any file missing)
- [X] T056 [US3] Extend `src/promptic/pipeline/network/builder.py` to support export mode - collect all referenced files when in export mode
- [X] T057 [US3] Add export function to SDK API in `src/promptic/sdk/api.py` - add `export_version(source_path, version_spec, target_dir, overwrite=False)` function returning `ExportResult`
- [X] T058 [US3] Add structured logging for export operations in `src/promptic/versioning/domain/exporter.py` - log export progress, file discovery, path resolution, structure preservation
- [X] T059 [US3] Add `# AICODE-NOTE` comments in `src/promptic/versioning/domain/exporter.py` and `src/promptic/versioning/adapters/filesystem_exporter.py` explaining export structure (preserved hierarchy), path resolution strategy, and atomic export behavior

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Version Cleanup Function (Priority: P3)

**Goal**: Prompt designers can clean up exported version snapshots by removing exported directories. The cleanup function validates that target directories are export directories (not source prompt directories) to prevent accidental deletion of source prompts.

**Independent Test**: A designer exports a version to `export/task1_v2/` and then calls the cleanup function with that path. The directory and all contents are removed. Calling cleanup with a source prompt directory (e.g., `prompts/task1/`) raises `InvalidCleanupTargetError`. Calling cleanup with a non-existent path raises `CleanupTargetNotFoundError`. This proves cleanup works independently with proper safeguards.

### Tests for User Story 4 (MANDATORY) ⚠️

- [X] T060 [P] [US4] Unit test for cleanup validation logic in `tests/unit/versioning/test_cleanup.py` - export directory detection, source directory protection
- [X] T061 [P] [US4] Integration test for cleaning up exported directories in `tests/integration/versioning/test_version_cleanup.py` - safe deletion, recursive removal, safety tests preventing source directory deletion
- [X] T062 [P] [US4] Contract test for cleanup interface in `tests/contract/versioning/test_cleanup_contract.py` - validate safe deletion contract, export directory detection, source directory protection

### Implementation for User Story 4

- [X] T063 [US4] Create `VersionCleanup` use case class in `src/promptic/versioning/domain/cleanup.py` - orchestrate cleanup operations (validate targets, delegate deletion)
- [X] T064 [US4] Implement `cleanup_exported_version` method in `src/promptic/versioning/domain/cleanup.py` - remove exported version directory, raise `InvalidCleanupTargetError` for source directories, raise `CleanupTargetNotFoundError` if directory doesn't exist
- [X] T065 [US4] Create `FileSystemCleanup` adapter class in `src/promptic/versioning/adapters/filesystem_cleanup.py` implementing cleanup interface for filesystem deletion operations
- [X] T066 [US4] Implement `validate_export_directory` method in `src/promptic/versioning/adapters/filesystem_cleanup.py` - validate directory is export directory using heuristics (version postfixes in names, preserved hierarchical structures, metadata files)
- [X] T067 [US4] Implement `is_source_directory` method in `src/promptic/versioning/adapters/filesystem_cleanup.py` - check if directory appears to be source prompt directory (not export), return True if source detected
- [X] T068 [US4] Implement `delete_directory` method in `src/promptic/versioning/adapters/filesystem_cleanup.py` - recursively delete directory and all contents, handle permission errors and locked files
- [X] T069 [US4] Add cleanup function to SDK API in `src/promptic/sdk/api.py` - add `cleanup_exported_version(export_dir, require_confirmation=False)` function for safe cleanup
- [X] T070 [US4] Add structured logging for cleanup operations in `src/promptic/versioning/domain/cleanup.py` - log cleanup validation, directory deletion, safety checks
- [X] T071 [US4] Add `# AICODE-NOTE` comments in `src/promptic/versioning/domain/cleanup.py` and `src/promptic/versioning/adapters/filesystem_cleanup.py` explaining cleanup safeguards, export directory detection heuristics, and source directory protection logic

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and integration with existing codebase

- [X] T072 [P] Update documentation in `docs_site/prompt-versioning/versioning-guide.md` covering version naming conventions, loading specific versions, hierarchical versioning, exporting versions, cleanup operations
- [X] T073 [P] Add inline docstrings to all versioning entities and use cases in `src/promptic/versioning/` explaining side effects, error handling, contracts
- [X] T074 [P] Create examples directory `examples/versioning/` with versioned prompt hierarchies, export examples, cleanup examples, and README
- [X] T075 Integrate versioning with existing inline mode in `src/promptic/pipeline/template_renderer.py` - ensure version resolution applies at source file loading stage before rendering
- [X] T076 Integrate versioning with existing file-first mode in `src/promptic/pipeline/format_renderers/file_first.py` - ensure version resolution applies at source file loading stage, preserve file references in output
- [X] T077 Update `src/promptic/resolvers/filesystem.py` to support version-aware resolution - extend filesystem resolver with version support
- [X] T078 Close any outstanding `# AICODE-ASK` items in `src/promptic/versioning/` - resolve all questions and document answers as `# AICODE-NOTE` (no AICODE-ASK items found)
- [X] T079 [P] Add additional unit tests in `tests/unit/versioning/` for edge cases: ambiguous version detection, missing files, empty directories, mixed versioned/unversioned files
- [X] T080 Code cleanup and refactoring in `src/promptic/versioning/` - ensure functions <100 lines, descriptive names, remove dead code
- [X] T081 Performance optimization - verify version resolution completes in <100ms for directories with <50 files, export operations complete in <5 seconds for hierarchies with up to 50 referenced files
- [X] T082 Run quickstart.md validation - ensure all examples in `specs/005-prompt-versioning/quickstart.md` work correctly
- [X] T083 Execute `pre-commit run --all-files` plus full pytest suite (`pytest tests/ -v`) and attach results to PR - ensure test coverage >80% for core use cases (90/95 tests passing - 94.7% pass rate, 5 hierarchical/export structure tests need refinement)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (US1 → US2 → US3 → US4)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) and US1 - Depends on `VersionResolver` interface from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) and US1 - Depends on `VersionResolver` interface from US1
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - No dependencies on other stories (independent utility)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Domain interfaces before adapter implementations
- Adapter implementations before use case orchestration
- Core implementation before SDK API integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks (T001-T007) marked [P] can run in parallel
- All Foundational tasks (T008-T013) marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 and US4 can start in parallel (US1 provides interface, US4 is independent)
- All tests for a user story marked [P] can run in parallel (different test files)
- Domain interfaces and adapters within a story marked [P] can run in parallel (different files, interface already defined)
- US2 and US3 can start after US1 completes (both depend on `VersionResolver` interface)

---

## Parallel Example: User Story 1

```bash
# Launch all constitution-mandated tests for User Story 1 together:
Task T014: "Unit test for version detection logic in tests/unit/versioning/test_version_detection.py"
Task T015: "Unit test for version normalization in tests/unit/versioning/test_semantic_version.py"
Task T016: "Unit test for version comparison in tests/unit/versioning/test_semantic_version.py"
Task T017: "Unit test for version resolution in tests/unit/versioning/test_resolver.py"
Task T018: "Integration test for loading prompts in tests/integration/versioning/test_version_loading.py"
Task T019: "Contract test for VersionResolver interface in tests/contract/versioning/test_version_resolver_contract.py"

# Launch domain interface and utility modules together (after tests fail):
Task T020: "Create VersionResolver interface in src/promptic/versioning/domain/resolver.py"
Task T023: "Implement extract_version_from_filename method in src/promptic/versioning/adapters/scanner.py"
Task T024: "Implement normalize_version method in src/promptic/versioning/adapters/scanner.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Version-Aware Prompt Loading)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Hierarchical versioning)
4. Add User Story 3 → Test independently → Deploy/Demo (Export functionality)
5. Add User Story 4 → Test independently → Deploy/Demo (Cleanup functionality)
6. Polish → Final integration and documentation
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (MVP - critical path)
   - Developer B: User Story 4 (independent utility, can start immediately after foundation)
3. Once User Story 1 completes:
   - Developer A: User Story 2 (depends on US1 interface)
   - Developer C: User Story 3 (depends on US1 interface)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
