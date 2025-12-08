# Feature Specification: Advanced Versioning System

**Feature Branch**: `009-advanced-versioning`  
**Created**: 2025-11-27  
**Status**: Draft  
**Input**: User description: "Доработка версионирования: поддержка различных разделителей, настройка паттернов версий, постфиксы, кастомные классификаторы, pydantic-settings конфиг"
> This specification MUST satisfy the `promptic Constitution`: clean architecture layering, SOLID responsibilities, mandatory tests, documentation updates, and readability.

**Scope Clarification**: This feature extends the existing filesystem-based versioning system (from spec 005-prompt-versioning) with enhanced configurability: support for multiple version delimiters ("_", ".", "-"), customizable version patterns via configuration, version postfixes with proper "latest" resolution logic, and custom classifiers (e.g., language variants). Configuration is implemented via pydantic-settings but is NOT auto-resolved to avoid conflicts with host applications—it must be explicitly passed as a parameter.

**Value Proposition**: Teams using promptic need flexibility in how they organize and name versioned prompts. Different projects may use different naming conventions (e.g., `prompt_v1.md` vs `prompt-v1.md` vs `prompt.v1.md`). Additionally, teams may want to maintain prompt variants (e.g., language-specific prompts like `prompt_en_v1.md`, `prompt_ru_v1.md`) while still leveraging the versioning system. This feature provides configurable versioning that adapts to existing project conventions without forcing migration to a specific naming scheme.

**Problems Solved**: The current versioning system (1) only supports underscore delimiters (`_v1`), forcing projects with different conventions to rename files, (2) lacks support for version postfixes (e.g., `-beta`, `-rc1`), limiting semantic versioning expressiveness, (3) cannot handle prompt variants/classifiers (like language or audience), requiring manual file selection, (4) has hardcoded patterns that cannot be customized per project, (5) lacks a configuration system that can be safely embedded in host applications.

**Real-World Use Cases**:
- A project migrating from another tool with `-v1` naming convention can configure promptic to work with existing files
- A multilingual application maintains `prompt_en_v2.md` and `prompt_ru_v2.md`, selecting the appropriate language variant automatically
- A team uses semantic versioning postfixes (`v1.0.0-beta`, `v1.0.0-rc1`) and needs proper "latest" resolution excluding pre-releases by default
- A larger application embedding promptic has its own pydantic-settings and needs to extend/embed promptic's settings without conflicts

## Clarifications

### Session 2025-11-27

- Q: When classifier value is missing from latest version (e.g., Russian exists for v1 but not v2), what should happen? → A: Return the latest version that HAS the requested classifier value (v1_ru even if v2_en exists). Users requesting a specific classifier want content in that classifier, not a version mismatch.
- Q: Should enhanced versioning extend existing logging to cover config resolution, classifier matching, and pattern compilation? → A: Yes, extend existing structured logging patterns (DEBUG for config/pattern details, INFO for resolution results) to maintain consistency with the codebase.
- Q: When user requests specific version + classifier (e.g., v2 + Russian) but that combination doesn't exist, what happens? → A: Raise `VersionNotFoundError` explaining the specific combination doesn't exist. Explicit version requests expect exact matches; silent fallback would be dangerous.
- Q: How should multi-delimiter ambiguity with classifiers be handled? → A: Enforce strict ordering rule: classifiers BEFORE version, postfixes (prerelease) AFTER version. Example: `prompt-en-v1-rc.1` where `en` is classifier, `v1` is version, `rc.1` is prerelease postfix. This eliminates parsing ambiguity.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configurable Version Delimiters (Priority: P1)

Prompt designers can configure the versioning system to recognize different delimiter patterns between the base filename and version identifier. The system supports underscore (`_`), dot (`.`), and hyphen (`-`) delimiters, with underscore as the default. This allows teams to use their existing naming conventions without file renaming.

**Why this priority**: This is the most common pain point—teams often have established naming conventions that differ from promptic's default. Without delimiter flexibility, adoption requires file renaming across the entire project, which is disruptive and error-prone.

**Independent Test**: Configure promptic to use hyphen delimiter. Create files `prompt-v1.md`, `prompt-v2.md`, `prompt-v3.md`. Load with `version="latest"` resolves to `prompt-v3.md`. Load with `version="v2"` resolves to `prompt-v2.md`. The same test passes with dot delimiter and files `prompt.v1.md`, `prompt.v2.md`.

**Architecture Impact**: Extends `VersionedFileScanner` to accept a delimiter configuration parameter. The regex pattern for version detection is dynamically generated based on configured delimiter(s). `VersioningConfig` (new entity) stores delimiter preferences. Maintains SRP—delimiter configuration doesn't change resolution logic, only pattern matching. Uses DIP—scanner receives delimiter config via injection rather than hardcoding.

**Quality Signals**: Unit tests for each delimiter type, integration tests with mixed delimiter configs, property-based tests ensuring delimiter changes don't affect version comparison logic, docs_site guide "Configuring version delimiters".

**Acceptance Scenarios**:

1. **Given** versioning config with `delimiter="_"` (default), **When** loading files named `prompt_v1.md`, `prompt_v2.md`, **Then** the system correctly detects versions v1.0.0, v2.0.0.
2. **Given** versioning config with `delimiter="-"`, **When** loading files named `prompt-v1.md`, `prompt-v2.md`, **Then** the system correctly detects versions v1.0.0, v2.0.0.
3. **Given** versioning config with `delimiter="."`, **When** loading files named `prompt.v1.md`, `prompt.v2.md`, **Then** the system correctly detects versions v1.0.0, v2.0.0.
4. **Given** versioning config with `delimiters=["_", "-"]` (multiple), **When** loading a directory with mixed naming (`prompt_v1.md`, `prompt-v2.md`), **Then** the system detects both versions and resolves "latest" correctly.
5. **Given** no explicit config (using defaults), **When** loading files with underscore delimiter, **Then** behavior matches current implementation (backward compatible).

---

### User Story 2 - Custom Version Patterns (Priority: P1)

Prompt designers can define custom regex patterns for version detection, either globally via configuration or per-call via function parameters. This enables support for non-standard versioning schemes (e.g., `prompt_rev42.md`, `prompt_build123.md`) or strict semantic versioning enforcement.

**Why this priority**: Some organizations have unique versioning schemes that don't follow standard patterns. Requiring pattern changes globally or per-project makes promptic adaptable to enterprise environments with existing conventions.

**Independent Test**: Configure a custom pattern `r"_rev(?P<major>\d+)"` that captures revision numbers. Create files `prompt_rev1.md`, `prompt_rev2.md`, `prompt_rev3.md`. Load with `version="latest"` resolves to `prompt_rev3.md`. Load with `version="rev2"` resolves to `prompt_rev2.md`.

**Architecture Impact**: Introduces `VersionPattern` domain entity encapsulating pattern matching logic. `VersionedFileScanner` accepts `VersionPattern` injection. `VersioningConfig` stores default and named patterns. The pattern abstraction allows different version comparison strategies (numeric, semantic, chronological). Maintains OCP—new patterns can be added without modifying existing code.

**Quality Signals**: Unit tests for custom patterns, integration tests with various pattern configurations, negative tests for invalid patterns, docs_site guide "Custom version patterns".

**Acceptance Scenarios**:

1. **Given** a custom pattern `r"_rev(\d+)"` in config, **When** loading files named `prompt_rev1.md`, `prompt_rev42.md`, **Then** the system detects rev1 and rev42 as versions.
2. **Given** a custom pattern passed to `render()` function via `version_pattern` parameter, **When** loading, **Then** the custom pattern overrides the global config for that call.
3. **Given** a custom pattern with named capture groups, **When** extracting version, **Then** the system uses the captured groups correctly for comparison.
4. **Given** an invalid regex pattern, **When** configuring, **Then** the system raises `InvalidVersionPatternError` with helpful message.
5. **Given** custom pattern config, **When** using hierarchical version resolution, **Then** the custom pattern applies at all hierarchy levels.

---

### User Story 3 - Version Postfixes (Priority: P2)

Prompt designers can use version postfixes (e.g., `-alpha`, `-beta`, `-rc1`, `-final`) following the version number. The "latest" resolution logic correctly handles postfixes: by default, pre-release postfixes (`-alpha`, `-beta`, `-rc`) are excluded from "latest" resolution unless explicitly requested. The postfix `_final` or no postfix is considered a release version.

**Why this priority**: Semantic versioning postfixes are standard practice in software development. Teams expect to mark experimental prompts as alpha/beta without them being picked up by "latest" resolution in production workflows.

**Independent Test**: Create files `prompt_v1.0.0.md` (release), `prompt_v1.0.1-alpha.md` (pre-release), `prompt_v1.0.1-beta.md` (pre-release), `prompt_v1.0.1.md` (release). Load with `version="latest"` resolves to `prompt_v1.0.1.md`. Load with `version="latest-prerelease"` resolves to `prompt_v1.0.1-beta.md`. Load with `version="v1.0.1-alpha"` resolves to `prompt_v1.0.1-alpha.md`.

**Architecture Impact**: Extends `SemanticVersion` dataclass to include optional `prerelease` field. Updates version comparison logic to handle prerelease ordering (alpha < beta < rc < release). Adds `include_prerelease` flag to version resolution functions. `VersioningConfig` stores default prerelease inclusion behavior. Maintains LSP—extended SemanticVersion still satisfies base interface.

**Quality Signals**: Unit tests for prerelease parsing and comparison, integration tests for "latest" with/without prereleases, property-based tests for prerelease ordering, docs_site guide "Version postfixes and pre-releases".

**Acceptance Scenarios**:

1. **Given** files with postfixes `v1.0.0`, `v1.0.1-alpha`, `v1.0.1-beta`, `v1.0.1`, **When** loading with `version="latest"` (default), **Then** system resolves to `v1.0.1` (ignoring pre-releases).
2. **Given** same files, **When** loading with `version="latest"` and `include_prerelease=True`, **Then** system resolves to `v1.0.1` (releases still take precedence over pre-releases of same version).
3. **Given** files with only pre-releases `v1.0.0-alpha`, `v1.0.0-beta`, **When** loading with `version="latest"`, **Then** system raises `VersionNotFoundError` suggesting to use `include_prerelease=True`.
4. **Given** files with only pre-releases, **When** loading with `version="latest"` and `include_prerelease=True`, **Then** system resolves to highest pre-release (`v1.0.0-beta`).
5. **Given** version request `version="v1.0.1-alpha"` (explicit pre-release), **When** loading, **Then** system resolves to exactly that pre-release file.
6. **Given** prerelease ordering config customized to `["dev", "alpha", "beta", "rc"]`, **When** comparing `v1.0.0-dev` and `v1.0.0-alpha`, **Then** `alpha` is considered newer than `dev`.

---

### User Story 4 - Custom Classifiers (Priority: P2)

Prompt designers can define custom classifiers (like language, audience, or environment) that create prompt variants within a version. For example, `prompt_v1_en.md` and `prompt_v1_ru.md` are both version 1 but for different languages. The system can filter by classifier when resolving versions, with configurable default classifier selection.

**Why this priority**: Multilingual and multi-audience prompt management is a common requirement. Without classifier support, teams resort to manual path management or separate directory hierarchies, losing the benefits of unified versioning.

**Independent Test**: Configure classifier `lang` with values `["en", "ru", "de"]` and default `"en"`. Create files `prompt_en_v1.md`, `prompt_ru_v1.md`, `prompt_en_v2.md`. Load with `version="latest"` and no classifier resolves to `prompt_en_v2.md` (default language). Load with `version="latest"` and `classifier={"lang": "ru"}` resolves to `prompt_ru_v1.md` (latest Russian version).

**Architecture Impact**: Introduces `ClassifierConfig` domain entity defining classifier names, values, and defaults. Extends `VersionInfo` to include extracted classifiers. Updates `VersionedFileScanner` pattern to capture classifier segments. Adds classifier filtering to version resolution. `VersioningConfig` stores classifier definitions. Maintains SRP—classifier extraction is separate from version detection.

**Quality Signals**: Unit tests for classifier parsing, integration tests for multi-classifier scenarios, tests for classifier-version interaction, docs_site guide "Working with prompt classifiers".

**Acceptance Scenarios**:

1. **Given** classifier config `lang: ["en", "ru"]` with default `"en"`, **When** loading files `prompt_en_v1.md`, `prompt_ru_v1.md` without specifying classifier, **Then** system resolves to `prompt_en_v1.md` (default).
2. **Given** same files, **When** loading with `classifier={"lang": "ru"}`, **Then** system resolves to `prompt_ru_v1.md`.
3. **Given** files with multiple classifiers `prompt_en_formal_v1.md`, `prompt_en_casual_v1.md`, **When** config defines `lang` and `tone` classifiers, **Then** both classifiers can be used for filtering.
4. **Given** a classifier value that doesn't exist (e.g., `lang="es"` but no Spanish files), **When** loading, **Then** system raises `ClassifierNotFoundError` listing available values.
5. **Given** mixed files—some with classifiers, some without (`prompt_v1.md`, `prompt_en_v1.md`), **When** loading without classifier filter, **Then** system treats unclassified files as having "default" classifier values.
6. **Given** hierarchical version spec with classifiers, **When** loading, **Then** classifiers apply at each level independently.
7. **Given** files `prompt_ru_v1.md`, `prompt_en_v2.md` (Russian only in v1), **When** loading with `classifier={"lang": "ru"}`, **Then** system resolves to `prompt_ru_v1.md` (latest version with requested classifier).
8. **Given** files `prompt_ru_v1.md`, `prompt_en_v2.md`, **When** loading with `version="v2"` and `classifier={"lang": "ru"}`, **Then** system raises `VersionNotFoundError` indicating v2 + Russian combination doesn't exist.

---

### User Story 5 - Pydantic-Settings Configuration (Priority: P1)

The versioning configuration is implemented using pydantic-settings, providing type-safe configuration with validation. The config is NOT auto-resolved from environment variables or files—it must be explicitly instantiated and passed to promptic functions. This allows host applications to embed promptic's config model into their own pydantic-settings without conflicts.

**Why this priority**: Configuration management is foundational for all other features. The explicit-pass design is critical for library consumers who have their own settings systems and cannot tolerate automatic environment variable resolution that might conflict with their namespaces.

**Independent Test**: Create `VersioningConfig(delimiter="-")`. Pass to `render()` function. Verify hyphen delimiter is used. Create a host app with its own pydantic-settings that embeds `VersioningConfig` as a nested model. Verify both configs work independently without namespace conflicts.

**Architecture Impact**: Introduces `VersioningConfig` as a pydantic `BaseModel` (NOT `BaseSettings`) to prevent auto-resolution. Provides `VersioningSettings` (extends `BaseSettings`) for apps that WANT environment variable resolution—but this is opt-in. All versioning functions accept optional `config` parameter. Config is propagated through the resolution chain. Maintains ISP—config interface is minimal; extended settings are separate.

**Quality Signals**: Unit tests for config validation, integration tests for config propagation, tests for embedding in host app settings, docs_site guide "Configuring versioning".

**Acceptance Scenarios**:

1. **Given** `VersioningConfig` instantiated with custom values, **When** passed to `render()`, **Then** those values are used for version resolution.
2. **Given** no config passed, **When** calling `render()`, **Then** default config values are used (backward compatible).
3. **Given** `VersioningConfig` embedded in a host app's pydantic-settings, **When** host app resolves its settings from env vars, **Then** promptic's nested config doesn't conflict or auto-resolve separately.
4. **Given** `VersioningSettings` (the env-var-aware version), **When** instantiated, **Then** it reads from environment variables with `PROMPTIC_` prefix.
5. **Given** invalid config values (e.g., empty delimiter), **When** instantiating `VersioningConfig`, **Then** pydantic validation raises clear error.
6. **Given** config passed to `load_prompt()` and `export_version()`, **When** executing, **Then** config is applied consistently across all versioning operations.

---

### Edge Cases

- **Multiple delimiter patterns in one filename**: When a filename like `prompt_v1-v2.md` contains multiple potential version patterns, the system uses the LAST pattern matching the configured delimiter(s). Document this behavior clearly.
- **Strict segment ordering**: Filename segments follow strict order: `base-classifier(s)-version-postfix.ext`. Example: `prompt-en-v1-rc.1.md` where `en` is classifier, `v1` is version, `rc.1` is prerelease. This eliminates ambiguity in multi-delimiter scenarios.
- **Empty classifier values**: When a classifier is configured but files don't have that classifier segment, treat them as "default" classifier value, not missing.
- **Config inheritance in hierarchical resolution**: When resolving nested prompts, child prompts inherit parent's config unless explicitly overridden in hierarchical spec.
- **Pattern capture group naming**: Custom patterns MUST use named capture groups (`(?P<major>\d+)`) for reliable extraction. Unnamed groups cause `InvalidVersionPatternError`.
- **Prerelease sorting stability**: When multiple prereleases have the same label (e.g., `v1.0.0-alpha.1`, `v1.0.0-alpha.2`), numeric suffixes are compared numerically.
- **Config serialization for export**: When exporting versions, the config used during export is NOT stored in exported files—exports are config-agnostic artifacts.
- **Performance with custom patterns**: Complex regex patterns may impact directory scanning performance. Cache compiled patterns at config instantiation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support configurable version delimiters: underscore (`_`), dot (`.`), and hyphen (`-`), with underscore as the default.
- **FR-002**: System MUST allow multiple delimiters to be active simultaneously (e.g., `delimiters=["_", "-"]`) for mixed-convention directories.
- **FR-003**: System MUST support custom regex patterns for version detection, accepting patterns via configuration or function parameter.
- **FR-004**: Custom patterns MUST use named capture groups for version components (`major`, `minor`, `patch`, `prerelease`).
- **FR-005**: System MUST support version postfixes following semantic versioning conventions (`-alpha`, `-beta`, `-rc`, `-final`, or custom).
- **FR-006**: "Latest" version resolution MUST exclude pre-release versions by default (configurable via `include_prerelease` flag).
- **FR-007**: Pre-release ordering MUST follow: `alpha < beta < rc < release`, with configurable ordering for custom prerelease labels.
- **FR-008**: System MUST support custom classifiers with configurable names, allowed values, and defaults.
- **FR-009**: Classifier filtering MUST be combinable with version specification (e.g., "latest v2 in Russian").
- **FR-010**: System MUST provide `VersioningConfig` as a pydantic BaseModel (NOT BaseSettings) for explicit instantiation.
- **FR-011**: System MAY provide `VersioningSettings` (extends BaseSettings) for applications wanting environment variable resolution.
- **FR-012**: All versioning functions (`render`, `load_prompt`, `export_version`) MUST accept optional `config` parameter.
- **FR-013**: When no config is provided, system MUST use sensible defaults matching current behavior (backward compatibility).
- **FR-014**: Config validation MUST fail fast with clear error messages for invalid configurations.
- **FR-015**: Configuration MUST propagate through hierarchical version resolution without requiring re-specification at each level.
- **FR-016**: System MUST raise `InvalidVersionPatternError` for malformed custom patterns with diagnostic information.
- **FR-017**: System MUST raise `ClassifierNotFoundError` when requested classifier value doesn't exist in ANY version, listing available values.
- **FR-018**: When requested classifier exists in some versions but not the latest, system MUST return the latest version that HAS the requested classifier value.
- **FR-019**: Environment variable prefix for `VersioningSettings` MUST be `PROMPTIC_` (e.g., `PROMPTIC_VERSION_DELIMITER`).
- **FR-020**: System MUST extend existing structured logging to cover: config loading (DEBUG), pattern compilation (DEBUG), classifier matching (DEBUG), and version resolution results (INFO).

### Key Entities *(include if feature involves data)*

- **VersioningConfig**: Pydantic BaseModel containing all versioning configuration. Fields: `delimiter` (str, default="_"), `delimiters` (list[str], optional for multi-delimiter mode), `version_pattern` (str, optional custom regex), `include_prerelease` (bool, default=False), `classifiers` (dict[str, ClassifierConfig], optional), `prerelease_order` (list[str], default=["alpha", "beta", "rc"]). Immutable after instantiation. Validates patterns at construction time.

- **VersioningSettings**: Pydantic BaseSettings extending VersioningConfig for environment variable resolution. Uses `PROMPTIC_` prefix. Opt-in usage for applications wanting auto-configuration. NOT used internally by promptic.

- **ClassifierConfig**: Pydantic model defining a single classifier. Fields: `name` (str), `values` (list[str]), `default` (str, must be in values). Classifiers are ALWAYS positioned before the version segment (enforced ordering: `base-classifier-version-postfix.ext`). Used within VersioningConfig.

- **VersionPattern**: Domain entity encapsulating version regex pattern and extraction logic. Provides `extract_version(filename) -> VersionComponents` method. Compiles and caches regex. Validates pattern structure (named groups). Factory method `from_delimiter(delimiter)` generates standard patterns.

- **VersionComponents**: Dataclass holding extracted version parts: `major` (int), `minor` (int, default 0), `patch` (int, default 0), `prerelease` (str | None), `classifiers` (dict[str, str]). Used internally for comparison and resolution.

- **SemanticVersion** (extended): Existing dataclass extended with `prerelease: str | None` field. Comparison updated to handle prerelease ordering. Factory method `from_components(VersionComponents)`.

### Architecture & Quality Constraints *(from Constitution)*

- **AQ-001**: `VersioningConfig` and `ClassifierConfig` are Entities in domain layer. `VersionPattern` is a domain service. `VersionedFileScanner` adapter receives config via constructor injection. Config flows from SDK API → Use Cases → Adapters. No hardcoded patterns in adapters.
- **AQ-002**: SRP: `VersioningConfig` handles configuration validation only. `VersionPattern` handles pattern matching only. `ClassifierConfig` handles classifier definitions only. No single class handles both config storage and pattern execution.
- **AQ-003**: OCP: New delimiters/classifiers are added via configuration, not code changes. `VersionPattern.from_delimiter()` factory enables extension without modification.
- **AQ-004**: Unit tests for config validation (valid/invalid inputs), pattern generation for each delimiter, version comparison with prereleases, classifier extraction. Integration tests for full resolution flow with various configs. Property-based tests for version ordering consistency.
- **AQ-005**: docs_site updates: "Configuring versioning" guide covering all config options with examples. API reference for `VersioningConfig`, `VersioningSettings`. Migration guide from default to custom configs.
- **AQ-006**: Readability: Config classes use descriptive field names with clear docstrings. Pattern generation logic in dedicated factory methods. No complex conditionals in comparison logic—use lookup tables for prerelease ordering.

### Assumptions

- Custom patterns must use named capture groups; positional groups are not supported for clarity and maintainability.
- Filename segments follow strict ordering: `base-classifier(s)-version-postfix.ext` (e.g., `prompt-en-v1-rc.1.md`). Classifier segments use the same delimiter as versions.
- Pre-release labels are case-insensitive (`-Alpha` equals `-alpha`).
- The default prerelease order (`alpha < beta < rc`) covers most use cases; custom ordering is available for edge cases.
- Host applications embedding `VersioningConfig` are responsible for their own environment variable namespace management.
- Performance impact of custom regex patterns is acceptable for typical directory sizes (<1000 files); caching mitigates repeated scans.
- `VersioningSettings` environment variable resolution uses standard pydantic-settings behavior (`.env` files, environment variables).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All three delimiter types (underscore, dot, hyphen) correctly detect versions with 100% accuracy in unit tests.
- **SC-002**: Custom patterns with named capture groups correctly extract version components in 100% of test cases.
- **SC-003**: Pre-release exclusion from "latest" works correctly; `include_prerelease=True` includes them appropriately.
- **SC-004**: Classifier filtering returns correct files in 100% of test cases for single and multi-classifier scenarios.
- **SC-005**: `VersioningConfig` validation catches invalid configurations with clear error messages.
- **SC-006**: Backward compatibility: existing code without config parameter works identically to before.
- **SC-007**: `VersioningConfig` can be embedded in host app pydantic-settings without namespace conflicts (verified by integration test).
- **SC-008**: All related pytest suites (unit, integration) pass with >90% coverage for new code.
- **SC-009**: docs_site includes comprehensive configuration guide with working examples.
- **SC-010**: Performance: directory scans with custom patterns complete in <100ms for directories with 100 files.
