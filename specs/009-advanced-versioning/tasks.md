# Tasks: Advanced Versioning System

**Input**: Design documents from `/specs/009-advanced-versioning/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Tests are MANDATORY under the `promptic Constitution`. List contract, integration, and unit coverage for every story before implementation, and ensure each test fails before the matching code exists.

**Organization**: Tasks are grouped by user story to enable independent implementation/testing while keeping Clean Architecture layers isolated.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Path Conventions

- **Source**: `src/promptic/versioning/` for versioning module
- **SDK**: `src/promptic/sdk/api.py` for public API
- **Tests**: `tests/versioning/` for versioning tests
- **Docs**: `docs_site/guides/` for user guides

## Constitution Alignment Checklist

- [X] Document how Entities → Use Cases → Interface adapters will be created/updated; prevent outward dependencies.
- [X] Capture SOLID responsibilities for each new module and record deviations via `# AICODE-NOTE`.
- [X] Plan documentation updates (`docs_site/`, specs, docstrings) and resolve any outstanding `# AICODE-ASK` items.
- [X] Ensure readability: limit function/file size, adopt explicit naming, and remove dead code.
- [X] Schedule pytest (unit, integration, contract) plus `pre-commit run --all-files` before requesting review.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add dependencies and create module structure for new files

- [X] T001 Add `pydantic-settings>=2.2` to dependencies in `pyproject.toml`
- [X] T002 [P] Create empty `src/promptic/versioning/config.py` module file
- [X] T003 [P] Create empty `src/promptic/versioning/domain/pattern.py` module file
- [X] T004 [P] Create test directory structure `tests/versioning/` if not exists

---

## Phase 2: Foundational (Configuration Infrastructure) - US5 Base

**Purpose**: Core configuration models that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundational Phase (MANDATORY) ⚠️

- [X] T005 [P] Unit test for ClassifierConfig validation in `tests/versioning/test_config.py`
- [X] T006 [P] Unit test for VersioningConfig validation in `tests/versioning/test_config.py`
- [X] T007 [P] Unit test for VersioningSettings env var resolution in `tests/versioning/test_config.py`

### Implementation for Foundational Phase

- [X] T008 [P] Implement ClassifierConfig pydantic model in `src/promptic/versioning/config.py`
- [X] T009 Implement VersioningConfig pydantic BaseModel in `src/promptic/versioning/config.py`
- [X] T010 Implement VersioningSettings (BaseSettings) in `src/promptic/versioning/config.py`
- [X] T011 [P] Add InvalidVersionPatternError to `src/promptic/versioning/domain/errors.py`
- [X] T012 [P] Add ClassifierNotFoundError to `src/promptic/versioning/domain/errors.py`
- [X] T013 Update `src/promptic/versioning/__init__.py` to export new config classes and errors

**Checkpoint**: Configuration infrastructure ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Configurable Version Delimiters (Priority: P1) 🎯 MVP

**Goal**: Support underscore, dot, and hyphen delimiters for version detection with backward compatibility

**Independent Test**: Configure hyphen delimiter, create `prompt-v1.md`, `prompt-v2.md`, verify "latest" resolves to v2

### Tests for User Story 1 (MANDATORY) ⚠️

- [X] T014 [P] [US1] Unit test for VersionPattern.from_delimiter() in `tests/versioning/test_pattern.py`
- [X] T015 [P] [US1] Unit test for VersionPattern.from_delimiters() in `tests/versioning/test_pattern.py`
- [X] T016 [P] [US1] Integration test for delimiter resolution in `tests/versioning/test_delimiter_resolution.py`
- [X] T017 [P] [US1] Backward compatibility test in `tests/versioning/test_backward_compat.py`

### Implementation for User Story 1

- [X] T018 [P] [US1] Implement VersionComponents dataclass in `src/promptic/versioning/domain/pattern.py`
- [X] T019 [US1] Implement VersionPattern class with from_delimiter() factory in `src/promptic/versioning/domain/pattern.py`
- [X] T020 [US1] Add from_delimiters() factory for multi-delimiter mode in `src/promptic/versioning/domain/pattern.py`
- [X] T021 [US1] Add from_config() factory method in `src/promptic/versioning/domain/pattern.py`
- [X] T022 [US1] Refactor VersionedFileScanner to accept config injection in `src/promptic/versioning/adapters/scanner.py`
- [X] T023 [US1] Update VersionedFileScanner.extract_version_from_filename() to use VersionPattern in `src/promptic/versioning/adapters/scanner.py`
- [X] T024 [US1] Add `versioning_config` parameter to SDK render() function in `src/promptic/sdk/api.py`
- [X] T025 [US1] Add `versioning_config` parameter to SDK load_prompt() function in `src/promptic/sdk/api.py`
- [X] T026 [US1] Add `versioning_config` parameter to SDK export_version() function in `src/promptic/sdk/api.py`
- [X] T027 [US1] Add structured logging for pattern compilation (DEBUG) in `src/promptic/versioning/utils/logging.py`
- [X] T027a [US1] Add structured logging for config loading (DEBUG) in `src/promptic/versioning/utils/logging.py`

**Checkpoint**: Delimiter configuration works; backward compatibility verified; can deliver as MVP

---

## Phase 4: User Story 2 - Custom Version Patterns (Priority: P1)

**Goal**: Allow custom regex patterns for non-standard versioning schemes (e.g., `_rev42`, `_build123`)

**Independent Test**: Configure pattern `r"_rev(?P<major>\d+)"`, create `prompt_rev1.md`, `prompt_rev42.md`, verify "latest" resolves to rev42

### Tests for User Story 2 (MANDATORY) ⚠️

- [X] T028 [P] [US2] Unit test for custom pattern extraction in `tests/versioning/test_pattern.py`
- [X] T029 [P] [US2] Unit test for pattern validation (named groups) in `tests/versioning/test_pattern.py`
- [X] T030 [P] [US2] Unit test for InvalidVersionPatternError in `tests/versioning/test_pattern.py`
- [X] T031 [P] [US2] Integration test for custom pattern resolution in `tests/versioning/test_delimiter_resolution.py`

### Implementation for User Story 2

- [X] T032 [US2] Add custom pattern support to VersionPattern.__init__() in `src/promptic/versioning/domain/pattern.py`
- [X] T033 [US2] Add _validate_named_groups() method in `src/promptic/versioning/domain/pattern.py`
- [X] T034 [US2] Update VersioningConfig validator for custom patterns in `src/promptic/versioning/config.py`
- [X] T035 [US2] Propagate custom pattern through resolution chain in `src/promptic/versioning/adapters/scanner.py`
- [X] T036 [US2] Add `# AICODE-NOTE` explaining pattern structure requirements in `src/promptic/versioning/domain/pattern.py`

**Checkpoint**: Custom patterns work with named capture groups; invalid patterns raise clear errors

---

## Phase 5: User Story 3 - Version Postfixes (Priority: P2)

**Goal**: Support pre-release postfixes (-alpha, -beta, -rc) with proper "latest" exclusion by default

**Independent Test**: Create `prompt_v1.0.0.md`, `prompt_v1.0.1-alpha.md`, `prompt_v1.0.1.md`; verify "latest" returns v1.0.1 (ignoring alpha)

### Tests for User Story 3 (MANDATORY) ⚠️

- [X] T037 [P] [US3] Unit test for SemanticVersion prerelease parsing in `tests/versioning/test_prerelease.py`
- [X] T038 [P] [US3] Unit test for prerelease comparison ordering in `tests/versioning/test_prerelease.py`
- [X] T039 [P] [US3] Property-based test for prerelease ordering consistency in `tests/versioning/test_prerelease.py`
- [X] T040 [P] [US3] Integration test for "latest" with/without include_prerelease in `tests/versioning/test_prerelease.py`

### Implementation for User Story 3

- [X] T041 [US3] Extend SemanticVersion dataclass with prerelease field in `src/promptic/versioning/utils/semantic_version.py`
- [X] T042 [US3] Update SemanticVersion.__lt__() for prerelease ordering in `src/promptic/versioning/utils/semantic_version.py`
- [X] T043 [US3] Add _compare_prerelease() method with configurable ordering in `src/promptic/versioning/utils/semantic_version.py`
- [X] T044 [US3] Add SemanticVersion.from_string() support for prerelease suffix in `src/promptic/versioning/utils/semantic_version.py`
- [X] T045 [US3] Update VersionPattern to capture prerelease in extract_version() in `src/promptic/versioning/domain/pattern.py`
- [X] T046 [US3] Update resolve_version() to filter prereleases by default in `src/promptic/versioning/adapters/scanner.py`
- [X] T047 [US3] Add helpful error message when only prereleases exist in `src/promptic/versioning/adapters/scanner.py`
- [X] T048 [US3] Add `# AICODE-NOTE` explaining prerelease ordering rules in `src/promptic/versioning/utils/semantic_version.py`

**Checkpoint**: Prerelease versions correctly excluded from "latest"; explicit requests work; ordering is consistent

---

## Phase 6: User Story 4 - Custom Classifiers (Priority: P2)

**Goal**: Support language/audience/environment classifiers for prompt variants within versions

**Independent Test**: Configure lang classifier ["en", "ru"], create `prompt_en_v1.md`, `prompt_ru_v1.md`, `prompt_en_v2.md`; verify default (en) returns v2, classifier=ru returns v1

### Tests for User Story 4 (MANDATORY) ⚠️

- [X] T049 [P] [US4] Unit test for classifier extraction from filename in `tests/versioning/test_classifier.py`
- [X] T050 [P] [US4] Unit test for classifier filtering logic in `tests/versioning/test_classifier.py`
- [X] T051 [P] [US4] Unit test for ClassifierNotFoundError in `tests/versioning/test_classifier.py`
- [X] T052 [P] [US4] Integration test for multi-classifier scenarios in `tests/versioning/test_classifier.py`
- [X] T053 [P] [US4] Integration test for classifier fallback (return latest with classifier) in `tests/versioning/test_classifier.py`

### Implementation for User Story 4

- [X] T054 [US4] Extend VersionInfo dataclass with classifiers field in `src/promptic/versioning/adapters/scanner.py`
- [X] T055 [US4] Implement classifier extraction in VersionPattern.extract_version() in `src/promptic/versioning/domain/pattern.py`
- [X] T056 [US4] Add _extract_classifiers() method in `src/promptic/versioning/adapters/scanner.py`
- [X] T057 [US4] Add classifier filtering to resolve_version() in `src/promptic/versioning/adapters/scanner.py`
- [X] T058 [US4] Implement classifier fallback (return latest version WITH classifier) in `src/promptic/versioning/adapters/scanner.py`
- [X] T059 [US4] Add `classifier` parameter to SDK load_prompt() in `src/promptic/sdk/api.py`
- [X] T059a [US4] Add `classifier` parameter to SDK render() in `src/promptic/sdk/api.py`
- [X] T060 [US4] Add `classifier` parameter to SDK export_version() in `src/promptic/sdk/api.py`
- [X] T060a [US4] Add `classifier` parameter to VersionExporter.export_version() in `src/promptic/versioning/domain/exporter.py`
- [X] T060b [US4] Wire classifier from SDK export_version() to VersionExporter in `src/promptic/sdk/api.py`
- [X] T060c [US4] Wire classifier from SDK render() to VersionExporter in `src/promptic/sdk/api.py`
- [X] T061 [US4] Update HierarchicalVersionResolver for classifier propagation in `src/promptic/versioning/domain/resolver.py`
- [X] T062 [US4] Add structured logging for classifier matching (DEBUG) in `src/promptic/versioning/utils/logging.py`
- [X] T062a [US4] Add structured logging for version resolution results (INFO) in `src/promptic/versioning/utils/logging.py`

**Checkpoint**: Classifiers filter correctly; fallback to latest version with classifier works; multiple classifiers supported

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, final integration, and quality assurance

### Documentation

- [X] T063 [P] Create versioning configuration guide in `docs_site/guides/versioning-configuration.md`
- [X] T064 [P] Create classifier usage guide in `docs_site/guides/version-classifiers.md`
- [X] T065 [P] Create prerelease handling guide in `docs_site/guides/version-prereleases.md`
- [X] T066 [P] Update API reference for VersioningConfig in `docs_site/reference/versioning-api.md`

### Final Integration

- [X] T067 Update `src/promptic/versioning/__init__.py` with all new exports
- [X] T068 Update `src/promptic/__init__.py` if needed for public API exposure
- [X] T069 Verify all existing tests pass (backward compatibility)

### Quality Assurance

- [X] T070 Run quickstart.md validation scenarios
- [X] T071 Execute `pre-commit run --all-files` and fix any issues
- [X] T072 Run full pytest suite with coverage report
- [X] T073 Verify >90% coverage on new code

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup ─────────────────────────────────────────────┐
    │                                                        │
    ▼                                                        │
Phase 2: Foundational (US5 Config) ──────────────────────────┤
    │                                                        │
    ├──────────────┬──────────────┬──────────────┐          │
    ▼              ▼              ▼              ▼          │
Phase 3: US1   Phase 4: US2   Phase 5: US3   Phase 6: US4  │
(Delimiters)   (Patterns)    (Postfixes)   (Classifiers)   │
    │              │              │              │          │
    └──────────────┴──────────────┴──────────────┘          │
                        │                                    │
                        ▼                                    │
                Phase 7: Polish ◄────────────────────────────┘
```

### User Story Dependencies

| Story | Depends On | Can Parallel With |
|-------|------------|-------------------|
| **US1** (Delimiters) | Phase 2 (Foundational) | US3, US5 |
| **US2** (Patterns) | US1 (uses VersionPattern) | US3, US4, US5 |
| **US3** (Postfixes) | Phase 2 (Foundational) | US1, US4, US5 |
| **US4** (Classifiers) | US1 (uses VersionPattern) | US3, US5 |
| **US5** (Config) | Phase 2 IS this story | N/A |

### Within Each User Story

1. Tests MUST be written and FAIL before implementation
2. Domain entities before adapters
3. Adapters before SDK API updates
4. Core implementation before integration
5. Logging/documentation last

### Parallel Opportunities

**Phase 2** (can run in parallel):
- T005, T006, T007 (all tests)
- T008, T011, T012 (independent models/errors)

**Phase 3 US1** (can run in parallel):
- T014, T015, T016, T017 (all tests)
- T018 (VersionComponents) independent of pattern

**After Foundational completes**:
- US1 and US3 can run in parallel (different files)
- US2 depends on US1 completion
- US4 depends on US1 completion

---

## Parallel Example: Phase 3 (User Story 1)

```bash
# Launch all tests for User Story 1 together:
Task: T014 "Unit test for VersionPattern.from_delimiter()"
Task: T015 "Unit test for VersionPattern.from_delimiters()"
Task: T016 "Integration test for delimiter resolution"
Task: T017 "Backward compatibility test"

# After tests written, launch independent implementations:
Task: T018 "Implement VersionComponents dataclass"
# Then sequential: T019 → T020 → T021 (build on each other)
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 5 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (config models)
3. Complete Phase 3: User Story 1 (delimiters)
4. **STOP and VALIDATE**: Test delimiter configuration works
5. Deploy/demo - users can now use different delimiters

### Incremental Delivery

| Increment | Delivers | User Value |
|-----------|----------|------------|
| MVP | US5 + US1 | Configure delimiters, backward compatible |
| +US2 | Custom patterns | Enterprise versioning schemes |
| +US3 | Prereleases | Semantic versioning alpha/beta/rc |
| +US4 | Classifiers | Multilingual/multi-audience prompts |

### Estimated Task Counts

| Phase | Tasks | Parallelizable |
|-------|-------|----------------|
| Setup | 4 | 3 |
| Foundational | 9 | 6 |
| US1 (Delimiters) | 15 | 5 |
| US2 (Patterns) | 8 | 4 |
| US3 (Postfixes) | 12 | 4 |
| US4 (Classifiers) | 19 | 5 |
| Polish | 11 | 4 |
| **Total** | **78** | **31** |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

