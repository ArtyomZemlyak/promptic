# Quickstart: Advanced Versioning

**Feature**: 009-advanced-versioning  
**Date**: 2025-11-27

## Overview

This guide helps you get started with promptic's advanced versioning features: custom delimiters, pre-release handling, and classifiers.

---

## Installation

```bash
pip install promptic
```

No additional dependencies required for basic versioning. For environment variable configuration:

```bash
pip install pydantic-settings
```

---

## Basic Usage (Unchanged)

Existing code works without modification:

```python
from promptic import render, load_prompt

# Render with default versioning (underscore delimiter, latest version)
content = render("prompts/task.md")

# Load specific version
content = load_prompt("prompts/task/", version="v1.0.0")
```

---

## Custom Delimiters

### Single Delimiter

```python
from promptic import render
from promptic.versioning import VersioningConfig

# Use hyphen delimiter for files like prompt-v1.md
config = VersioningConfig(delimiter="-")

content = render(
    "prompts/task.md",
    versioning_config=config
)
```

### Multiple Delimiters

For directories with mixed naming conventions:

```python
config = VersioningConfig(delimiters=["_", "-"])

# Works with both prompt_v1.md and prompt-v2.md
content = render("prompts/", versioning_config=config)
```

**Supported delimiters**: `"_"` (underscore), `"."` (dot), `"-"` (hyphen)

---

## Pre-release Handling

By default, "latest" excludes pre-releases:

```python
from promptic import load_prompt

# Directory contains: prompt_v1.0.0.md, prompt_v1.0.1-alpha.md, prompt_v1.0.1.md

# Returns prompt_v1.0.1.md (ignores alpha)
content = load_prompt("prompts/task/")
```

### Include Pre-releases

```python
from promptic.versioning import VersioningConfig

config = VersioningConfig(include_prerelease=True)

# Now considers prompt_v1.0.1-alpha.md in "latest" resolution
# Still returns prompt_v1.0.1.md because releases > pre-releases
content = load_prompt("prompts/task/", versioning_config=config)
```

### Request Specific Pre-release

```python
# Explicit version request always works
content = load_prompt("prompts/task/", version="v1.0.1-alpha")
```

### Custom Pre-release Order

```python
config = VersioningConfig(
    prerelease_order=["dev", "alpha", "beta", "rc"]
)

# dev < alpha < beta < rc < release
```

---

## Classifiers (Language, Audience, etc.)

Classifiers create prompt variants within a version.

### Define Classifiers

```python
from promptic.versioning import VersioningConfig, ClassifierConfig

config = VersioningConfig(
    classifiers={
        "lang": ClassifierConfig(
            name="lang",
            values=["en", "ru", "de"],
            default="en"
        )
    }
)
```

### File Naming

Files follow the pattern: `base-classifier-version.ext`

```
prompts/
├── task_en_v1.md      # English v1
├── task_ru_v1.md      # Russian v1
├── task_en_v2.md      # English v2
└── task_ru_v2.md      # Russian v2
```

### Load with Classifier

```python
from promptic import load_prompt

# Uses default classifier (en)
content = load_prompt("prompts/task/", versioning_config=config)
# Returns: task_en_v2.md (latest English)

# Specify classifier
content = load_prompt(
    "prompts/task/",
    classifier={"lang": "ru"},
    versioning_config=config
)
# Returns: task_ru_v2.md (latest Russian)
```

### Partial Classifier Coverage

If a classifier value doesn't exist for the latest version:

```python
# Directory: task_ru_v1.md, task_en_v2.md (no Russian v2)

content = load_prompt(
    "prompts/task/",
    classifier={"lang": "ru"},
    versioning_config=config
)
# Returns: task_ru_v1.md (latest version WITH Russian)
```

### Multiple Classifiers

```python
config = VersioningConfig(
    classifiers={
        "lang": ClassifierConfig(name="lang", values=["en", "ru"], default="en"),
        "tone": ClassifierConfig(name="tone", values=["formal", "casual"], default="formal"),
    }
)

# File: task_en_formal_v1.md
content = load_prompt(
    "prompts/task/",
    classifier={"lang": "en", "tone": "casual"},
    versioning_config=config
)
```

---

## Custom Version Patterns

For non-standard version schemes:

```python
config = VersioningConfig(
    version_pattern=r"_rev(?P<major>\d+)"
)

# Works with prompt_rev1.md, prompt_rev42.md
content = load_prompt("prompts/task/", versioning_config=config)
```

**Important**: Custom patterns MUST use named capture groups:
- `(?P<major>\d+)` - required
- `(?P<minor>\d+)` - optional
- `(?P<patch>\d+)` - optional
- `(?P<prerelease>[a-zA-Z0-9.]+)` - optional

---

## Environment Variable Configuration

For applications that want env var resolution:

```python
from promptic.versioning import VersioningSettings

# Reads from PROMPTIC_* environment variables
settings = VersioningSettings()
```

Environment variables:
- `PROMPTIC_DELIMITER`: `"_"`, `"."`, or `"-"`
- `PROMPTIC_INCLUDE_PRERELEASE`: `"true"` or `"false"`
- `PROMPTIC_PRERELEASE_ORDER`: JSON array, e.g., `'["alpha", "beta", "rc"]'`

```bash
export PROMPTIC_DELIMITER="-"
export PROMPTIC_INCLUDE_PRERELEASE=true
```

---

## Embedding in Host Application

For libraries embedding promptic:

```python
from pydantic_settings import BaseSettings
from promptic.versioning import VersioningConfig

class MyAppSettings(BaseSettings):
    """My application settings."""

    # Embed promptic config as nested model
    promptic: VersioningConfig = VersioningConfig()

    # My app's other settings
    api_key: str
    debug: bool = False

# Usage
settings = MyAppSettings()
content = render("prompts/task.md", versioning_config=settings.promptic)
```

**Key benefit**: `VersioningConfig` is a `BaseModel` (not `BaseSettings`), so it won't auto-resolve from environment variables and conflict with your app's namespace.

---

## Error Handling

```python
from promptic.versioning import (
    VersionNotFoundError,
    ClassifierNotFoundError,
    InvalidVersionPatternError,
)

try:
    content = load_prompt("prompts/task/", version="v99")
except VersionNotFoundError as e:
    print(f"Version not found: {e.version_spec}")
    print(f"Available: {e.available_versions}")

try:
    content = load_prompt(
        "prompts/task/",
        classifier={"lang": "es"},
        versioning_config=config
    )
except ClassifierNotFoundError as e:
    print(f"Classifier '{e.classifier_name}' value '{e.requested_value}' not found")
    print(f"Available: {e.available_values}")
```

---

## Complete Example

```python
from promptic import render
from promptic.versioning import VersioningConfig, ClassifierConfig

# Configure versioning for a multilingual project
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

# Directory structure:
# prompts/
# ├── task-en-v1.md
# ├── task-ru-v1.md
# ├── task-en-v2.md
# ├── task-en-v2-beta.md
# └── task-ru-v2.md

# Get latest English version (v2, ignoring beta)
english = render(
    "prompts/task/",
    versioning_config=config
)

# Get latest Russian version
russian = render(
    "prompts/task/",
    classifier={"lang": "ru"},
    versioning_config=config
)

# Get specific version
v1_english = render(
    "prompts/task/",
    version="v1",
    versioning_config=config
)

# Export with classifier
from promptic import export_version

result = export_version(
    "prompts/task/",
    version_spec="v2",
    target_dir="export/task_v2_ru/",
    classifier={"lang": "ru"},
    versioning_config=config
)
```
