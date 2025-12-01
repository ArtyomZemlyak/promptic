# Versioning API Reference

Complete API reference for promptic's versioning system.

## Configuration Classes

### VersioningConfig

Central configuration model for versioning behavior. Immutable after creation.

```python
from promptic.versioning import VersioningConfig

config = VersioningConfig(
    delimiter: str = "_",
    delimiters: list[str] | None = None,
    version_pattern: str | None = None,
    include_prerelease: bool = False,
    prerelease_order: list[str] = ["alpha", "beta", "rc"],
    classifiers: dict[str, ClassifierConfig] | None = None,
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `delimiter` | `str` | `"_"` | Single version delimiter. One of `"_"`, `"-"`, `"."` |
| `delimiters` | `list[str] \| None` | `None` | Multiple delimiters for mixed directories. Overrides `delimiter` |
| `version_pattern` | `str \| None` | `None` | Custom regex pattern with named capture groups |
| `include_prerelease` | `bool` | `False` | Include prereleases in "latest" resolution |
| `prerelease_order` | `list[str]` | `["alpha", "beta", "rc"]` | Ordering for prerelease comparison |
| `classifiers` | `dict[str, ClassifierConfig] \| None` | `None` | Classifier definitions |

#### Validation

- `delimiter` must be one of: `"_"`, `"."`, `"-"`
- `delimiters` (if set) must contain only valid delimiters
- `version_pattern` (if set) must be valid regex with `(?P<major>...)` named group
- Configuration is frozen (immutable) after creation

---

### ClassifierConfig

Configuration for a single classifier (e.g., language, audience).

```python
from promptic.versioning import ClassifierConfig

classifier = ClassifierConfig(
    name: str,
    values: list[str],
    default: str,
)
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Classifier identifier (e.g., "lang", "tone") |
| `values` | `list[str]` | List of allowed values |
| `default` | `str` | Default value (must be in `values`) |

#### Example

```python
ClassifierConfig(name="lang", values=["en", "ru", "de"], default="en")
ClassifierConfig(name="tone", values=["formal", "casual"], default="formal")
```

---

### VersioningSettings

Versioning configuration with environment variable resolution.

```python
from promptic.versioning import VersioningSettings

settings = VersioningSettings()  # Reads from PROMPTIC_* env vars
```

#### Environment Variables

| Variable | Type | Description |
|----------|------|-------------|
| `PROMPTIC_DELIMITER` | `str` | Version delimiter |
| `PROMPTIC_INCLUDE_PRERELEASE` | `bool` | Include prereleases ("true"/"false") |
| `PROMPTIC_PRERELEASE_ORDER` | `str` | JSON array of prerelease order |

---

## SDK Functions

### render()

Load and render a prompt file with optional versioning configuration.

```python
from promptic import render

result = render(
    path: str | Path,
    *,
    target_format: Literal["yaml", "markdown", "json", "jinja2"] = "markdown",
    render_mode: Literal["full", "file_first"] = "full",
    vars: dict[str, Any] | None = None,
    config: NetworkConfig | None = None,
    version: VersionSpec | None = None,
    export_to: str | Path | None = None,
    overwrite: bool = False,
    versioning_config: VersioningConfig | None = None,
) -> str | ExportResult
```

`path` accepts several forms:

- Exact prompt files (with or without explicit version suffix)
- File hints without version suffix (use the `version` parameter or default to latest)
- File hints without extensions (the resolver tries common extensions)
- Directories that contain versioned prompt files

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `str \| Path` | Prompt file, base filename, or directory hint |
| `target_format` | `str` | Output format: "markdown", "yaml", "json", "jinja2" |
| `render_mode` | `str` | "full" (inline) or "file_first" (preserve refs) |
| `vars` | `dict \| None` | Variables for substitution |
| `config` | `NetworkConfig \| None` | Network configuration |
| `version` | `VersionSpec \| None` | Version specification |
| `classifier` | `dict \| None` | Classifier filter propagated to nested prompts |
| `export_to` | `str \| Path \| None` | Export directory |
| `overwrite` | `bool` | Overwrite existing export |
| `versioning_config` | `VersioningConfig \| None` | Versioning configuration |

#### Returns

- `str`: Rendered content (when `export_to` is None)
- `ExportResult`: Export result (when `export_to` is provided)

---

### load_prompt()

Load a prompt with version-aware resolution.

```python
from promptic import load_prompt

content = load_prompt(
    path: str | Path,
    *,
    version: VersionSpec = "latest",
    classifier: dict[str, str] | None = None,
    versioning_config: VersioningConfig | None = None,
) -> str
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `str \| Path` | Directory path with versioned prompts |
| `version` | `VersionSpec` | Version specification |
| `classifier` | `dict \| None` | Classifier filter (e.g., `{"lang": "ru"}`) |
| `versioning_config` | `VersioningConfig \| None` | Versioning configuration |

#### Returns

`str`: Content of resolved prompt file

---

### export_version()

Export a complete version snapshot with optional classifier filtering.

```python
from promptic import export_version

result = export_version(
    source_path: str | Path,
    version_spec: VersionSpec,
    target_dir: str | Path,
    *,
    overwrite: bool = False,
    vars: dict[str, Any] | None = None,
    classifier: dict[str, str] | None = None,
    versioning_config: VersioningConfig | None = None,
) -> ExportResult
```

---

## Error Classes

### InvalidVersionPatternError

Raised when custom version pattern is malformed.

```python
from promptic.versioning import InvalidVersionPatternError

error = InvalidVersionPatternError(
    pattern: str,      # The invalid pattern
    reason: str,       # Why it's invalid
    message: str | None = None,
)

# Attributes
error.pattern      # The invalid pattern string
error.reason       # Explanation of the error
error.message      # Human-readable message
```

---

### ClassifierNotFoundError

Raised when requested classifier value doesn't exist.

```python
from promptic.versioning import ClassifierNotFoundError

error = ClassifierNotFoundError(
    classifier_name: str,
    requested_value: str,
    available_values: list[str] | None = None,
    message: str | None = None,
)

# Attributes
error.classifier_name    # e.g., "lang"
error.requested_value    # e.g., "es"
error.available_values   # e.g., ["en", "ru", "de"]
error.message            # Human-readable message
```

---

## Domain Classes

### SemanticVersion

Represents a semantic version with optional prerelease.

```python
from promptic.versioning import SemanticVersion

version = SemanticVersion(
    major: int,
    minor: int,
    patch: int,
    prerelease: str | None = None,
)

# Class methods
SemanticVersion.from_string("v1.2.3-alpha")
SemanticVersion.normalize("v1")  # Returns v1.0.0

# Comparison
v1_alpha < v1_beta < v1_release
```

---

### VersionInfo

Information about a versioned file.

```python
from promptic.versioning import VersionInfo

info = VersionInfo(
    filename: str,                    # "prompt_v1.md"
    path: str,                        # "/full/path/prompt_v1.md"
    base_name: str,                   # "prompt.md"
    version: SemanticVersion | None,  # SemanticVersion(1, 0, 0)
    is_versioned: bool,               # True
    classifiers: dict[str, str],      # {"lang": "en"}
)
```

---

## Type Aliases

### VersionSpec

Version specification type.

```python
VersionSpec = str | dict[str, str]

# Examples:
"latest"           # Latest version
"v1"               # Specific major version
"v1.2.3"           # Specific version
"v1.0.0-alpha"     # Prerelease version
{"root": "v1"}     # Hierarchical specification
```

---

## Complete Example

```python
from promptic import render, load_prompt, export_version
from promptic.versioning import (
    VersioningConfig,
    ClassifierConfig,
    VersionNotFoundError,
    ClassifierNotFoundError,
)

# Configure versioning
config = VersioningConfig(
    delimiter="-",
    include_prerelease=False,
    classifiers={
        "lang": ClassifierConfig(
            name="lang",
            values=["en", "ru", "de"],
            default="en"
        )
    }
)

# Load with classifier
try:
    content = load_prompt(
        "prompts/task/",
        classifier={"lang": "ru"},
        versioning_config=config
    )
except ClassifierNotFoundError as e:
    print(f"Classifier not found: {e.available_values}")
except VersionNotFoundError as e:
    print(f"Version not found: {e.available_versions}")

# Render with versioning
output = render(
    "prompts/task.md",
    version="v2.0.0",
    versioning_config=config
)

# Export with classifier
result = export_version(
    "prompts/task/",
    version_spec="latest",
    target_dir="export/",
    classifier={"lang": "de"},
    versioning_config=config
)
```

