# Research: Advanced Versioning System

**Feature**: 009-advanced-versioning  
**Date**: 2025-11-27  
**Status**: Complete

## Overview

This document captures research findings and technical decisions for the advanced versioning feature. All NEEDS CLARIFICATION items from the spec have been resolved during the clarification session.

---

## Decision 1: Configuration Model Design

### Decision
Use pydantic `BaseModel` for `VersioningConfig` (NOT `BaseSettings`) with an optional `VersioningSettings` subclass for applications that want environment variable resolution.

### Rationale
- **Library-safe embedding**: BaseModel doesn't auto-resolve from environment variables, preventing namespace conflicts when promptic is embedded in host applications
- **Explicit over implicit**: Users must explicitly instantiate and pass config, making behavior predictable
- **Composability**: Host apps can embed `VersioningConfig` as a nested model in their own pydantic-settings without conflicts
- **Opt-in auto-config**: `VersioningSettings` (extends BaseSettings) available for apps that WANT env var resolution

### Alternatives Considered
1. **BaseSettings only**: Rejected because auto-resolution causes conflicts in embedded scenarios
2. **Custom config class**: Rejected because pydantic provides validation, serialization, and IDE support
3. **Dict-based config**: Rejected because no type safety or validation

### Implementation Notes
```python
from pydantic import BaseModel, field_validator

class VersioningConfig(BaseModel):
    """Versioning configuration - NOT auto-resolved from env vars."""
    model_config = ConfigDict(frozen=True)  # Immutable after creation

    delimiter: str = "_"
    delimiters: list[str] | None = None
    include_prerelease: bool = False
    # ... other fields

class VersioningSettings(VersioningConfig, BaseSettings):
    """Opt-in env var resolution with PROMPTIC_ prefix."""
    model_config = SettingsConfigDict(env_prefix="PROMPTIC_")
```

---

## Decision 2: Filename Segment Ordering

### Decision
Enforce strict ordering: `base-classifier(s)-version-postfix.ext`

Example: `prompt-en-v1-rc.1.md`
- `prompt` — base name
- `en` — classifier
- `v1` — version
- `rc.1` — prerelease postfix

### Rationale
- **Eliminates ambiguity**: When multiple delimiters are active, strict ordering prevents parsing confusion
- **Predictable parsing**: Classifiers always come before version, postfixes always after
- **Simple regex**: Pattern can match segments in order without backtracking

### Alternatives Considered
1. **Configurable position**: Rejected because it adds complexity and ambiguity
2. **Version first, then classifiers**: Rejected because current spec 005 already shows `prompt_v1_en.md` pattern; changing would break backward compatibility

### Implementation Notes
```python
# Pattern structure:
# {base}{delimiter}{classifier}*{delimiter}v{version}{delimiter}{prerelease}?.{ext}
#
# Examples:
# prompt_en_v1.md          → base=prompt, classifier=en, version=v1, prerelease=None
# prompt-ru-v2.0.0-beta.md → base=prompt, classifier=ru, version=v2.0.0, prerelease=beta
```

---

## Decision 3: Prerelease Handling in "Latest" Resolution

### Decision
- "Latest" excludes prereleases by default (`include_prerelease=False`)
- Releases take precedence over prereleases of the same base version
- Explicit version requests (e.g., `version="v1.0.0-alpha"`) always resolve exactly

### Rationale
- **Production safety**: Prevents alpha/beta prompts from accidentally becoming "latest" in production
- **Semantic versioning alignment**: Follows standard semver practices where releases supersede prereleases
- **Explicit override**: `include_prerelease=True` allows testing workflows to include prereleases

### Alternatives Considered
1. **Include prereleases by default**: Rejected because it would surprise users in production
2. **Separate "latest-prerelease" keyword**: Rejected in favor of boolean flag for simplicity

### Implementation Notes
```python
def resolve_latest(versions: list[SemanticVersion], include_prerelease: bool = False):
    if not include_prerelease:
        versions = [v for v in versions if v.prerelease is None]
    if not versions:
        raise VersionNotFoundError(
            message="No release versions found. Use include_prerelease=True to include pre-releases."
        )
    return max(versions)
```

---

## Decision 4: Classifier Fallback Behavior

### Decision
When classifier value is missing from latest version, return the latest version that HAS the requested classifier value.

### Rationale
- **User intent**: Users requesting a specific classifier want content in that classifier, not a version mismatch
- **Graceful degradation**: Allows gradual addition of localized content without breaking existing queries
- **Principle of least surprise**: Better to return older Russian version than error or fallback to English

### Alternatives Considered
1. **Error on missing classifier**: Rejected because it prevents gradual localization
2. **Fallback to default classifier**: Rejected because it silently returns wrong language
3. **Return file without classifier**: Rejected because it's unpredictable

### Implementation Notes
```python
def resolve_with_classifier(
    versions: list[VersionInfo],
    classifier: dict[str, str],
    version_spec: str
) -> str:
    if version_spec == "latest":
        # Filter to versions with matching classifier, then get latest
        matching = [v for v in versions if matches_classifier(v, classifier)]
        if not matching:
            raise ClassifierNotFoundError(classifier, available_values=[...])
        return max(matching, key=lambda v: v.version)
    else:
        # Explicit version request - must match exactly
        matching = [v for v in versions
                    if v.version == version_spec and matches_classifier(v, classifier)]
        if not matching:
            raise VersionNotFoundError(f"Version {version_spec} with classifier {classifier} not found")
        return matching[0]
```

---

## Decision 5: Delimiter Support

### Decision
Support three delimiters: underscore (`_`), dot (`.`), hyphen (`-`). Allow multiple active delimiters for mixed-convention directories.

### Rationale
- **Migration support**: Projects can adopt promptic without renaming files
- **Flexibility**: Different teams prefer different conventions
- **Backward compatibility**: Default underscore matches existing behavior

### Alternatives Considered
1. **Underscore only**: Rejected because it forces file renaming
2. **Arbitrary delimiter string**: Rejected because it complicates pattern generation
3. **Single delimiter only**: Rejected because mixed directories exist in real projects

### Implementation Notes
```python
class VersionPattern:
    DELIMITER_PATTERNS = {
        "_": r"_v",
        "-": r"-v",
        ".": r"\.v",
    }

    @classmethod
    def from_delimiters(cls, delimiters: list[str]) -> "VersionPattern":
        pattern_parts = [cls.DELIMITER_PATTERNS[d] for d in delimiters]
        combined = f"(?:{'|'.join(pattern_parts)})"
        return cls(pattern=combined)
```

---

## Decision 6: Structured Logging Extension

### Decision
Extend existing `promptic.versioning.utils.logging` with DEBUG level for config/pattern details and INFO level for resolution results.

### Rationale
- **Consistency**: Follows existing logging patterns in the codebase
- **Debuggability**: Classifier and pattern matching can be complex; DEBUG logs help troubleshoot
- **Production-safe**: INFO level provides operation summaries without noise

### Implementation Notes
```python
# Extend existing log_version_operation
log_version_operation(logger, "config_loaded", config=config.model_dump())
log_version_operation(logger, "pattern_compiled", pattern=pattern.pattern_string)
log_version_operation(logger, "classifier_matched", classifier={"lang": "ru"}, file="prompt_ru_v1.md")
log_version_operation(logger, "version_resolved", version="v1.0.0", file="prompt_v1.0.0.md")
```

---

## Dependencies

### New Dependency: pydantic-settings

**Package**: `pydantic-settings>=2.2`  
**Purpose**: Provides `BaseSettings` for optional environment variable resolution  
**Impact**: Small addition; pydantic already a dependency  
**Installation**: Add to `pyproject.toml` dependencies

```toml
dependencies = [
    "pydantic>=2.6",
    "pydantic-settings>=2.2",  # NEW
    # ... existing deps
]
```

---

## Performance Considerations

1. **Pattern Caching**: Compiled regex patterns cached at `VersioningConfig` instantiation
2. **Directory Scan Caching**: Existing `VersionCache` handles directory scan results
3. **Classifier Filtering**: O(n) filter operation on already-scanned files; acceptable for <1000 files
4. **Config Propagation**: Config passed by reference through resolution chain; no serialization overhead

---

## Migration Path

### For Existing Users
- No action required; default config matches current behavior
- Existing code without `config` parameter works identically

### For New Features
1. Create `VersioningConfig` with desired settings
2. Pass to `render()`, `load_prompt()`, or `export_version()`
3. For env var resolution, use `VersioningSettings` instead

### For Library Consumers
1. Import `VersioningConfig` from `promptic.versioning`
2. Embed as nested model in host app's pydantic-settings
3. No namespace conflicts with host app's env vars
