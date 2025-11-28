# Data Model: Advanced Versioning System

**Feature**: 009-advanced-versioning  
**Date**: 2025-11-27

## Overview

This document defines the data entities, their attributes, relationships, and validation rules for the advanced versioning system.

---

## Entities

### 1. VersioningConfig

**Purpose**: Central configuration model for versioning behavior. Immutable after creation.

**Location**: `src/promptic/versioning/config.py`

```python
from pydantic import BaseModel, ConfigDict, field_validator

class VersioningConfig(BaseModel):
    """
    Versioning configuration - NOT auto-resolved from environment variables.
    
    # AICODE-NOTE: This is a BaseModel (not BaseSettings) intentionally.
    # Host applications can embed this model in their own pydantic-settings
    # without conflicts from automatic environment variable resolution.
    """
    model_config = ConfigDict(frozen=True)  # Immutable
    
    # Delimiter configuration
    delimiter: str = "_"
    delimiters: list[str] | None = None  # Multi-delimiter mode
    
    # Version pattern (optional custom regex)
    version_pattern: str | None = None
    
    # Prerelease handling
    include_prerelease: bool = False
    prerelease_order: list[str] = ["alpha", "beta", "rc"]
    
    # Classifiers
    classifiers: dict[str, ClassifierConfig] | None = None
```

**Validation Rules**:
- `delimiter` must be one of: `"_"`, `"."`, `"-"`
- `delimiters` (if set) must contain only valid delimiters
- `version_pattern` (if set) must be valid regex with named capture groups
- `prerelease_order` must be non-empty list of strings
- `classifiers` values must be valid `ClassifierConfig` instances

**Relationships**:
- Contains 0..N `ClassifierConfig` instances
- Used by `VersionedFileScanner`, `VersionResolver`, `VersionExporter`

---

### 2. VersioningSettings

**Purpose**: Opt-in extension for environment variable resolution.

**Location**: `src/promptic/versioning/config.py`

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class VersioningSettings(VersioningConfig, BaseSettings):
    """
    Versioning configuration with environment variable resolution.
    
    Uses PROMPTIC_ prefix for all environment variables.
    
    # AICODE-NOTE: This class is opt-in. promptic itself never instantiates it.
    # Applications that want env var resolution can use this instead of
    # VersioningConfig.
    """
    model_config = SettingsConfigDict(
        env_prefix="PROMPTIC_",
        env_nested_delimiter="__",
    )
```

**Environment Variable Mapping**:
- `PROMPTIC_DELIMITER` → `delimiter`
- `PROMPTIC_INCLUDE_PRERELEASE` → `include_prerelease`
- `PROMPTIC_PRERELEASE_ORDER` → `prerelease_order` (JSON array)
- `PROMPTIC_CLASSIFIERS__LANG__VALUES` → `classifiers["lang"].values`

---

### 3. ClassifierConfig

**Purpose**: Defines a single classifier (e.g., language, audience).

**Location**: `src/promptic/versioning/config.py`

```python
class ClassifierConfig(BaseModel):
    """
    Configuration for a single classifier.
    
    Classifiers create prompt variants within a version. For example,
    language classifiers allow `prompt_en_v1.md` and `prompt_ru_v1.md`.
    """
    model_config = ConfigDict(frozen=True)
    
    name: str
    values: list[str]
    default: str
```

**Validation Rules**:
- `name` must be non-empty alphanumeric string
- `values` must be non-empty list of unique strings
- `default` must be present in `values`

**Examples**:
```python
ClassifierConfig(name="lang", values=["en", "ru", "de"], default="en")
ClassifierConfig(name="tone", values=["formal", "casual"], default="formal")
```

---

### 4. VersionPattern

**Purpose**: Encapsulates version regex pattern and extraction logic.

**Location**: `src/promptic/versioning/domain/pattern.py`

```python
@dataclass
class VersionPattern:
    """
    Version detection pattern with compiled regex and extraction logic.
    
    # AICODE-NOTE: Patterns MUST use named capture groups for version components:
    # - (?P<major>\d+) - required
    # - (?P<minor>\d+) - optional
    # - (?P<patch>\d+) - optional
    # - (?P<prerelease>[a-zA-Z0-9.]+) - optional
    """
    pattern_string: str
    _compiled: re.Pattern = field(init=False, repr=False)
    
    def __post_init__(self):
        self._compiled = re.compile(self.pattern_string, re.IGNORECASE)
        self._validate_named_groups()
```

**Factory Methods**:
```python
@classmethod
def from_delimiter(cls, delimiter: str) -> "VersionPattern":
    """Generate standard pattern for a delimiter."""
    
@classmethod
def from_delimiters(cls, delimiters: list[str]) -> "VersionPattern":
    """Generate combined pattern for multiple delimiters."""
```

**Validation Rules**:
- Pattern must compile as valid regex
- Pattern must contain `(?P<major>...)` named group
- Unnamed groups cause `InvalidVersionPatternError`

---

### 5. VersionComponents

**Purpose**: Holds extracted version parts from filename.

**Location**: `src/promptic/versioning/domain/pattern.py`

```python
@dataclass(frozen=True)
class VersionComponents:
    """
    Extracted version components from a filename.
    
    Used internally for comparison and resolution.
    """
    major: int
    minor: int = 0
    patch: int = 0
    prerelease: str | None = None
    classifiers: dict[str, str] = field(default_factory=dict)
```

**Relationships**:
- Created by `VersionPattern.extract_version()`
- Converted to `SemanticVersion` via `SemanticVersion.from_components()`

---

### 6. SemanticVersion (Extended)

**Purpose**: Represents a semantic version with optional prerelease.

**Location**: `src/promptic/versioning/utils/semantic_version.py` (extended)

```python
@dataclass(frozen=True)
class SemanticVersion:
    """
    Semantic version with optional prerelease support.
    
    # AICODE-NOTE: Extended from original to support prerelease field.
    # Comparison logic updated: releases > prereleases of same base version.
    # Prerelease ordering: alpha < beta < rc (configurable).
    """
    major: int
    minor: int
    patch: int
    prerelease: str | None = None
    
    def __lt__(self, other: "SemanticVersion") -> bool:
        # Compare major.minor.patch first
        if (self.major, self.minor, self.patch) != (other.major, other.minor, other.patch):
            return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
        # Same base version: release > prerelease
        if self.prerelease is None and other.prerelease is not None:
            return False  # self is release, other is prerelease
        if self.prerelease is not None and other.prerelease is None:
            return True   # self is prerelease, other is release
        # Both prereleases: compare by order
        return self._compare_prerelease(other) < 0
```

**Prerelease Comparison**:
- Uses configurable ordering list (default: `["alpha", "beta", "rc"]`)
- Unknown labels compared lexicographically
- Numeric suffixes compared numerically (e.g., `alpha.1 < alpha.2`)

---

### 7. VersionInfo (Extended)

**Purpose**: Information about a versioned file.

**Location**: `src/promptic/versioning/adapters/scanner.py` (extended)

```python
@dataclass
class VersionInfo:
    """
    Information about a versioned file.
    
    Extended to include extracted classifiers.
    """
    filename: str
    path: str
    base_name: str
    version: SemanticVersion | None
    is_versioned: bool
    classifiers: dict[str, str] = field(default_factory=dict)  # NEW
```

---

## Error Types (Extended)

### InvalidVersionPatternError (NEW)

```python
class InvalidVersionPatternError(Exception):
    """Raised when custom version pattern is malformed."""
    def __init__(
        self,
        pattern: str,
        reason: str,
        message: str | None = None,
    ):
        self.pattern = pattern
        self.reason = reason
        # ...
```

### ClassifierNotFoundError (NEW)

```python
class ClassifierNotFoundError(Exception):
    """Raised when requested classifier value doesn't exist."""
    def __init__(
        self,
        classifier_name: str,
        requested_value: str,
        available_values: list[str],
        message: str | None = None,
    ):
        self.classifier_name = classifier_name
        self.requested_value = requested_value
        self.available_values = available_values
        # ...
```

---

## Entity Relationships

```
┌─────────────────────┐
│   VersioningConfig  │
│  (pydantic model)   │
├─────────────────────┤
│ delimiter           │
│ delimiters          │
│ version_pattern     │────────────┐
│ include_prerelease  │            │
│ prerelease_order    │            │
│ classifiers ────────┼──┐         │
└─────────────────────┘  │         │
                         │         │
         ┌───────────────┘         │
         ▼                         ▼
┌─────────────────────┐   ┌─────────────────────┐
│  ClassifierConfig   │   │   VersionPattern    │
│  (pydantic model)   │   │    (dataclass)      │
├─────────────────────┤   ├─────────────────────┤
│ name                │   │ pattern_string      │
│ values              │   │ _compiled           │
│ default             │   └─────────────────────┘
└─────────────────────┘            │
                                   │ extract_version()
                                   ▼
                         ┌─────────────────────┐
                         │  VersionComponents  │
                         │    (dataclass)      │
                         ├─────────────────────┤
                         │ major               │
                         │ minor               │
                         │ patch               │
                         │ prerelease          │
                         │ classifiers         │
                         └─────────────────────┘
                                   │
                                   │ from_components()
                                   ▼
                         ┌─────────────────────┐
                         │   SemanticVersion   │
                         │    (dataclass)      │
                         ├─────────────────────┤
                         │ major               │
                         │ minor               │
                         │ patch               │
                         │ prerelease          │
                         └─────────────────────┘
```

---

## State Transitions

### Config Lifecycle

```
┌──────────────┐
│   Created    │ ──── VersioningConfig(...)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Validated   │ ──── pydantic validation on instantiation
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Frozen     │ ──── model_config = ConfigDict(frozen=True)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    Used      │ ──── Passed to versioning functions
└──────────────┘
```

### Version Resolution Flow

```
Directory Path + Config
       │
       ▼
┌──────────────────────┐
│   Scan Directory     │ ──── VersionedFileScanner.scan_directory()
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Extract Versions    │ ──── VersionPattern.extract_version() for each file
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Filter by Classifier │ ──── If classifier specified
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Filter by Prerelease │ ──── If include_prerelease=False
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Resolve Version     │ ──── "latest" → max(), specific → exact match
└──────────┬───────────┘
           │
           ▼
      Resolved Path
```


