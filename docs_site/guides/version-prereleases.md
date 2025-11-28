# Version Prereleases Guide

This guide explains how to handle prerelease versions (alpha, beta, rc) in promptic's versioning system.

## Overview

Promptic supports semantic versioning prerelease identifiers:

- `v1.0.0-alpha` - Alpha release
- `v1.0.0-beta` - Beta release
- `v1.0.0-rc` - Release candidate
- `v1.0.0-alpha.1` - Numbered prerelease

## Default Behavior

**By default, prereleases are excluded from "latest" resolution.** This prevents alpha/beta prompts from accidentally becoming "latest" in production.

```python
from promptic import load_prompt

# Directory contains:
# - prompt_v1.0.0.md
# - prompt_v1.0.1-alpha.md
# - prompt_v1.0.1.md

# Returns prompt_v1.0.1.md (ignores alpha)
content = load_prompt("prompts/task/")
```

## Including Prereleases

To include prereleases in "latest" resolution:

```python
from promptic import load_prompt
from promptic.versioning import VersioningConfig

config = VersioningConfig(include_prerelease=True)

# Now considers all versions including prereleases
content = load_prompt(
    "prompts/task/",
    versioning_config=config
)
```

## Version Ordering

### Releases vs Prereleases

Releases take precedence over prereleases of the same base version:

```
v1.0.0-alpha < v1.0.0-beta < v1.0.0-rc < v1.0.0 (release)
```

### Prerelease Order

Default prerelease ordering: `alpha < beta < rc`

```python
# v1.0.0-alpha < v1.0.0-beta < v1.0.0-rc < v1.0.0
```

### Custom Prerelease Order

You can customize the prerelease ordering:

```python
from promptic.versioning import VersioningConfig

config = VersioningConfig(
    prerelease_order=["dev", "alpha", "beta", "rc", "preview"]
)

# Now: dev < alpha < beta < rc < preview < release
```

### Numbered Prereleases

Numbered prereleases are compared numerically:

```
v1.0.0-alpha.1 < v1.0.0-alpha.2 < v1.0.0-alpha.10
```

## Requesting Specific Prereleases

You can always request a specific prerelease version explicitly:

```python
from promptic import load_prompt

# Explicit request always works, regardless of include_prerelease setting
content = load_prompt(
    "prompts/task/",
    version="v1.0.0-alpha"
)
```

## When Only Prereleases Exist

If a directory contains only prerelease versions and `include_prerelease=False`:

```python
# Directory contains only:
# - prompt_v1.0.0-alpha.md
# - prompt_v1.0.0-beta.md
# - prompt_v1.0.0-rc.md

from promptic import load_prompt
from promptic.versioning import VersioningConfig

config = VersioningConfig(include_prerelease=False)

# Returns prompt_v1.0.0-rc.md (latest prerelease)
# Logs a warning about only prereleases being available
content = load_prompt("prompts/task/", versioning_config=config)
```

## File Naming Convention

Prerelease suffix comes after the version number:

```
prompt_v1.0.0-alpha.md
prompt_v1.0.0-beta.1.md
prompt_v1.0.0-rc.md
prompt-v2.0.0-alpha.md  (with hyphen delimiter)
```

### Strict Ordering

The filename pattern follows: `base_[classifiers]_version[-prerelease].ext`

```
✅ task_en_v1.0.0-alpha.md    (correct)
✅ task_v1.0.0-rc.1.md        (correct)
❌ task_v1.0.0-alpha_en.md    (wrong: classifier after version)
```

## Comparison Examples

```python
from promptic.versioning.utils.semantic_version import SemanticVersion

# Create versions
v1_alpha = SemanticVersion.from_string("v1.0.0-alpha")
v1_beta = SemanticVersion.from_string("v1.0.0-beta")
v1_release = SemanticVersion.from_string("v1.0.0")
v2_alpha = SemanticVersion.from_string("v2.0.0-alpha")

# Comparisons
assert v1_alpha < v1_beta          # alpha < beta
assert v1_beta < v1_release        # prerelease < release
assert v1_release < v2_alpha       # different base: v1 < v2
```

## Use Cases

### Development Workflow

```python
# Development: include prereleases for testing
dev_config = VersioningConfig(include_prerelease=True)

# Production: exclude prereleases for stability
prod_config = VersioningConfig(include_prerelease=False)

# Testing environment gets alpha/beta prompts
test_content = load_prompt("prompts/task/", versioning_config=dev_config)

# Production gets stable releases only
prod_content = load_prompt("prompts/task/", versioning_config=prod_config)
```

### CI/CD Pipeline

```python
import os

# Configuration based on environment
include_prerelease = os.getenv("INCLUDE_PRERELEASE", "false").lower() == "true"

config = VersioningConfig(include_prerelease=include_prerelease)
```

Or using `VersioningSettings`:

```python
from promptic.versioning import VersioningSettings

# Set via environment variable
# export PROMPTIC_INCLUDE_PRERELEASE=true

settings = VersioningSettings()
assert settings.include_prerelease == True
```

## Complete Example

```python
from promptic import load_prompt, export_version
from promptic.versioning import VersioningConfig

# Configuration for testing workflow
config = VersioningConfig(
    include_prerelease=True,
    prerelease_order=["dev", "alpha", "beta", "rc"]
)

# Directory structure:
# prompts/
# ├── task_v1.0.0.md
# ├── task_v1.1.0-dev.md
# ├── task_v1.1.0-alpha.md
# └── task_v1.1.0-beta.md

# Get latest (includes prereleases)
content = load_prompt(
    "prompts/task/",
    versioning_config=config
)
# Returns: task_v1.1.0-beta.md

# Get latest release only
stable_config = VersioningConfig(include_prerelease=False)
stable_content = load_prompt(
    "prompts/task/",
    versioning_config=stable_config
)
# Returns: task_v1.0.0.md

# Export specific prerelease
result = export_version(
    "prompts/task/",
    version_spec="v1.1.0-alpha",
    target_dir="export/task_alpha/"
)
```

## See Also

- [Versioning Configuration Guide](./versioning-configuration.md) - General configuration
- [Version Classifiers Guide](./version-classifiers.md) - Using language/audience classifiers

