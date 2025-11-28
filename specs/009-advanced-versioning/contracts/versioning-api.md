# API Contract: Versioning Configuration

**Feature**: 009-advanced-versioning  
**Date**: 2025-11-27  
**Type**: Internal Python API

## Overview

This document defines the API contracts for the enhanced versioning system. These are internal Python interfaces, not REST/GraphQL endpoints.

---

## Public API Functions

### render()

**Location**: `src/promptic/sdk/api.py`

```python
def render(
    path: str | Path,
    *,
    target_format: Literal["yaml", "markdown", "json", "jinja2"] = "markdown",
    render_mode: Literal["full", "file_first"] = "full",
    vars: dict[str, Any] | None = None,
    config: NetworkConfig | None = None,
    version: VersionSpec | None = None,
    export_to: str | Path | None = None,
    overwrite: bool = False,
    classifier: dict[str, str] | None = None,  # NEW in 009-advanced-versioning
    versioning_config: VersioningConfig | None = None,  # NEW
) -> str | ExportResult:
    """
    Load and render a prompt file with optional versioning configuration.
    
    Args:
        path: Path to the prompt file
        target_format: Output format
        render_mode: "full" (inline) or "file_first" (preserve refs)
        vars: Variables for substitution
        config: Network configuration (max_depth, limits)
        version: Version specification ("latest", "v1", or hierarchical dict)
        export_to: Export directory (returns ExportResult instead of str)
        overwrite: Overwrite existing export directory
        classifier: Classifier filter (NEW in 009-advanced-versioning)
            - {"lang": "ru"} → filter to Russian language files
            - Multiple classifiers: {"lang": "ru", "tone": "formal"}
            - Applied when version is specified or export_to is used
        versioning_config: Versioning configuration (NEW)
            - If None, uses default configuration (backward compatible)
            - Controls delimiter, patterns, prerelease, classifiers
    
    Returns:
        str: Rendered content (when export_to is None)
        ExportResult: Export result (when export_to is provided)
    
    Raises:
        FileNotFoundError: File doesn't exist
        VersionNotFoundError: Requested version doesn't exist
        ClassifierNotFoundError: Requested classifier value doesn't exist
        InvalidVersionPatternError: Custom pattern is malformed
    """
```

### load_prompt()

**Location**: `src/promptic/sdk/api.py`

```python
def load_prompt(
    path: str | Path,
    *,
    version: VersionSpec = "latest",
    classifier: dict[str, str] | None = None,  # NEW
    versioning_config: VersioningConfig | None = None,  # NEW
) -> str:
    """
    Load a prompt with version-aware resolution.
    
    Args:
        path: Directory path containing versioned prompts
        version: Version specification
        classifier: Classifier filter (NEW)
            - {"lang": "ru"} → filter to Russian language files
            - Multiple classifiers: {"lang": "ru", "tone": "formal"}
        versioning_config: Versioning configuration (NEW)
    
    Returns:
        str: Content of resolved prompt file
    
    Raises:
        VersionNotFoundError: Version doesn't exist
        ClassifierNotFoundError: Classifier value doesn't exist
    """
```

### export_version()

**Location**: `src/promptic/sdk/api.py`

```python
def export_version(
    source_path: str | Path,
    version_spec: VersionSpec,
    target_dir: str | Path,
    *,
    overwrite: bool = False,
    vars: dict[str, Any] | None = None,
    classifier: dict[str, str] | None = None,  # NEW
    versioning_config: VersioningConfig | None = None,  # NEW
) -> ExportResult:
    """
    Export a version snapshot with optional classifier filtering.
    
    Args:
        source_path: Source prompt hierarchy
        version_spec: Version specification
        target_dir: Export directory
        overwrite: Overwrite existing directory
        vars: Variables for substitution
        classifier: Classifier filter (NEW)
        versioning_config: Versioning configuration (NEW)
    
    Returns:
        ExportResult: Export result with files and content
    """
```

---

## Configuration Classes

### VersioningConfig

**Location**: `src/promptic/versioning/config.py`

```python
class VersioningConfig(BaseModel):
    """
    Versioning configuration.
    
    Attributes:
        delimiter: Single delimiter for version detection (default: "_")
        delimiters: Multiple delimiters for mixed directories (overrides delimiter)
        version_pattern: Custom regex pattern (must use named capture groups)
        include_prerelease: Include prereleases in "latest" resolution
        prerelease_order: Order for prerelease comparison
        classifiers: Classifier definitions
    
    Example:
        config = VersioningConfig(
            delimiter="-",
            include_prerelease=True,
            classifiers={
                "lang": ClassifierConfig(name="lang", values=["en", "ru"], default="en")
            }
        )
    """
    model_config = ConfigDict(frozen=True)
    
    delimiter: str = "_"
    delimiters: list[str] | None = None
    version_pattern: str | None = None
    include_prerelease: bool = False
    prerelease_order: list[str] = ["alpha", "beta", "rc"]
    classifiers: dict[str, ClassifierConfig] | None = None
    
    @field_validator("delimiter")
    @classmethod
    def validate_delimiter(cls, v: str) -> str:
        if v not in ("_", ".", "-"):
            raise ValueError(f"Invalid delimiter: {v}. Must be '_', '.', or '-'")
        return v
    
    @field_validator("delimiters")
    @classmethod
    def validate_delimiters(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            for d in v:
                if d not in ("_", ".", "-"):
                    raise ValueError(f"Invalid delimiter: {d}")
        return v
    
    @field_validator("version_pattern")
    @classmethod
    def validate_pattern(cls, v: str | None) -> str | None:
        if v is not None:
            try:
                compiled = re.compile(v)
                if "major" not in compiled.groupindex:
                    raise ValueError("Pattern must contain (?P<major>...) named group")
            except re.error as e:
                raise ValueError(f"Invalid regex pattern: {e}")
        return v
```

### ClassifierConfig

```python
class ClassifierConfig(BaseModel):
    """
    Single classifier configuration.
    
    Attributes:
        name: Classifier name (e.g., "lang", "tone")
        values: Allowed values (e.g., ["en", "ru", "de"])
        default: Default value (must be in values)
    """
    model_config = ConfigDict(frozen=True)
    
    name: str
    values: list[str]
    default: str
    
    @model_validator(mode="after")
    def validate_default_in_values(self) -> "ClassifierConfig":
        if self.default not in self.values:
            raise ValueError(f"Default '{self.default}' must be in values: {self.values}")
        return self
```

### VersioningSettings

```python
class VersioningSettings(VersioningConfig, BaseSettings):
    """
    Versioning configuration with environment variable resolution.
    
    Environment variables (PROMPTIC_ prefix):
        PROMPTIC_DELIMITER: "_" | "." | "-"
        PROMPTIC_INCLUDE_PRERELEASE: "true" | "false"
        PROMPTIC_PRERELEASE_ORDER: '["alpha", "beta", "rc"]' (JSON)
    
    Example:
        # From environment
        export PROMPTIC_DELIMITER="-"
        export PROMPTIC_INCLUDE_PRERELEASE=true
        
        settings = VersioningSettings()
        assert settings.delimiter == "-"
        assert settings.include_prerelease == True
    """
    model_config = SettingsConfigDict(
        env_prefix="PROMPTIC_",
        env_nested_delimiter="__",
    )
```

---

## Domain Interfaces

### VersionResolver

**Location**: `src/promptic/versioning/domain/resolver.py`

```python
class VersionResolver(ABC):
    """
    Interface for version resolution strategies.
    """
    
    @abstractmethod
    def resolve_version(
        self,
        path: str,
        version_spec: VersionSpec,
        config: VersioningConfig | None = None,  # NEW parameter
        classifier: dict[str, str] | None = None,  # NEW parameter
    ) -> str:
        """
        Resolve version from path and specification.
        
        Args:
            path: Directory path
            version_spec: Version specification
            config: Versioning configuration
            classifier: Classifier filter
        
        Returns:
            Resolved file path
        """
        pass
```

### VersionPattern

**Location**: `src/promptic/versioning/domain/pattern.py`

```python
class VersionPattern:
    """
    Version detection pattern.
    """
    
    def __init__(self, pattern_string: str):
        """
        Initialize pattern.
        
        Args:
            pattern_string: Regex pattern with named capture groups
        
        Raises:
            InvalidVersionPatternError: If pattern is invalid
        """
    
    @classmethod
    def from_delimiter(cls, delimiter: str) -> "VersionPattern":
        """
        Create pattern for single delimiter.
        
        Args:
            delimiter: "_", ".", or "-"
        
        Returns:
            VersionPattern for the delimiter
        """
    
    @classmethod
    def from_delimiters(cls, delimiters: list[str]) -> "VersionPattern":
        """
        Create pattern for multiple delimiters.
        
        Args:
            delimiters: List of delimiters
        
        Returns:
            Combined VersionPattern
        """
    
    @classmethod
    def from_config(cls, config: VersioningConfig) -> "VersionPattern":
        """
        Create pattern from configuration.
        
        Uses custom pattern if set, otherwise generates from delimiters.
        """
    
    def extract_version(self, filename: str) -> VersionComponents | None:
        """
        Extract version components from filename.
        
        Args:
            filename: Filename to parse
        
        Returns:
            VersionComponents if version found, None otherwise
        """
```

---

## Error Contracts

### InvalidVersionPatternError

```python
class InvalidVersionPatternError(Exception):
    """
    Raised when custom version pattern is malformed.
    
    Attributes:
        pattern: The invalid pattern string
        reason: Why the pattern is invalid
        message: Human-readable error message
    
    Example:
        InvalidVersionPatternError(
            pattern=r"v(\d+)",
            reason="Missing named capture group (?P<major>...)",
        )
    """
```

### ClassifierNotFoundError

```python
class ClassifierNotFoundError(Exception):
    """
    Raised when requested classifier value doesn't exist.
    
    Attributes:
        classifier_name: Name of the classifier (e.g., "lang")
        requested_value: Value that was requested (e.g., "es")
        available_values: Values that exist (e.g., ["en", "ru"])
        message: Human-readable error message
    
    Example:
        ClassifierNotFoundError(
            classifier_name="lang",
            requested_value="es",
            available_values=["en", "ru", "de"],
        )
        # Message: "Classifier 'lang' value 'es' not found. Available: en, ru, de"
    """
```

---

## Backward Compatibility Contract

All existing code MUST work without modification:

```python
# Existing code (no config parameter)
from promptic import render, load_prompt, export_version

# These must work identically to before
content = render("prompts/task.md")
content = load_prompt("prompts/task/")
result = export_version("prompts/", "latest", "export/")

# New code (with config parameter)
from promptic.versioning import VersioningConfig

config = VersioningConfig(delimiter="-")
content = render("prompts/task.md", versioning_config=config)
```

