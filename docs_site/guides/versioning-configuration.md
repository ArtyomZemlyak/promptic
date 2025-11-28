# Versioning Configuration Guide

This guide explains how to configure promptic's versioning system for custom delimiters, patterns, and behaviors.

## Overview

Promptic's versioning system is highly configurable through the `VersioningConfig` class. By default, it uses underscore-delimited version patterns (`_v1`, `_v1.1`, `_v1.1.1`), but you can customize:

- **Delimiters**: Use `_`, `-`, or `.` as version separators
- **Multiple delimiters**: Support mixed-convention directories
- **Custom patterns**: Define your own regex patterns
- **Prerelease handling**: Include or exclude alpha/beta/rc versions
- **Classifiers**: Support language/audience/environment variants

## Basic Configuration

### Default Behavior (Backward Compatible)

Without any configuration, promptic uses the default underscore delimiter:

```python
from promptic import render, load_prompt

# Uses default versioning (underscore delimiter)
content = render("prompts/task.md")
content = load_prompt("prompts/task/", version="latest")
```

### Custom Delimiter

To use a different delimiter:

```python
from promptic import render
from promptic.versioning import VersioningConfig

# Use hyphen delimiter for files like prompt-v1.md
config = VersioningConfig(delimiter="-")
content = render("prompts/task.md", versioning_config=config)
```

### Multiple Delimiters

For directories with mixed naming conventions:

```python
from promptic.versioning import VersioningConfig

# Support both underscore and hyphen
config = VersioningConfig(delimiters=["_", "-"])

# Matches: prompt_v1.md, prompt-v2.md, task_v3.md
content = render("prompts/", versioning_config=config)
```

## VersioningConfig Reference

```python
from promptic.versioning import VersioningConfig

config = VersioningConfig(
    # Single delimiter (default: "_")
    delimiter="_",  # Options: "_", "-", "."
    
    # Multiple delimiters (overrides single delimiter)
    delimiters=None,  # e.g., ["_", "-"]
    
    # Custom regex pattern (must use named capture groups)
    version_pattern=None,  # e.g., r"_rev(?P<major>\d+)"
    
    # Include prereleases in "latest" resolution
    include_prerelease=False,
    
    # Prerelease ordering for comparison
    prerelease_order=["alpha", "beta", "rc"],
    
    # Classifier definitions
    classifiers=None,  # e.g., {"lang": ClassifierConfig(...)}
)
```

## Custom Version Patterns

For non-standard versioning schemes (e.g., `_rev42`, `_build123`):

```python
from promptic.versioning import VersioningConfig

# Custom revision pattern
config = VersioningConfig(
    version_pattern=r"_rev(?P<major>\d+)"
)

# Matches: prompt_rev1.md, prompt_rev42.md
```

### Pattern Requirements

Custom patterns **must** use named capture groups:

- `(?P<major>\d+)` - **Required**: Major version number
- `(?P<minor>\d+)` - Optional: Minor version number
- `(?P<patch>\d+)` - Optional: Patch version number
- `(?P<prerelease>[a-zA-Z0-9.-]+)` - Optional: Prerelease identifier

Example with all components:

```python
config = VersioningConfig(
    version_pattern=r"_v(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)(?:-(?P<prerelease>[a-z]+))?"
)
```

## Environment Variable Configuration

For applications that want environment variable resolution, use `VersioningSettings`:

```python
from promptic.versioning import VersioningSettings

# Reads from PROMPTIC_* environment variables
settings = VersioningSettings()
```

Environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `PROMPTIC_DELIMITER` | Version delimiter | `-` |
| `PROMPTIC_INCLUDE_PRERELEASE` | Include prereleases | `true` |
| `PROMPTIC_PRERELEASE_ORDER` | Prerelease order | `'["alpha", "beta", "rc"]'` |

```bash
export PROMPTIC_DELIMITER="-"
export PROMPTIC_INCLUDE_PRERELEASE=true
```

## Embedding in Host Applications

For libraries embedding promptic, use `VersioningConfig` (not `VersioningSettings`) to avoid namespace conflicts:

```python
from pydantic_settings import BaseSettings
from promptic.versioning import VersioningConfig

class MyAppSettings(BaseSettings):
    # Embed promptic config as nested model
    promptic: VersioningConfig = VersioningConfig()
    
    # My app's other settings
    api_key: str
    debug: bool = False

settings = MyAppSettings()
content = render("prompts/task.md", versioning_config=settings.promptic)
```

## Configuration Immutability

`VersioningConfig` is frozen (immutable) after creation:

```python
config = VersioningConfig(delimiter="-")

# This will raise an error:
config.delimiter = "_"  # ValidationError!

# Create a new config instead:
new_config = VersioningConfig(delimiter="_")
```

## See Also

- [Version Classifiers Guide](./version-classifiers.md) - Using language/audience classifiers
- [Version Prereleases Guide](./version-prereleases.md) - Handling alpha/beta/rc versions
- [API Reference](../reference/versioning-api.md) - Complete API documentation

