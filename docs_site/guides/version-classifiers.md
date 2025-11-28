# Version Classifiers Guide

Classifiers allow you to create prompt variants within a version for different languages, audiences, tones, or environments.

## Overview

Classifiers extend the versioning system to support variations like:

- **Language**: `prompt_en_v1.md`, `prompt_ru_v1.md`
- **Tone**: `prompt_formal_v1.md`, `prompt_casual_v1.md`
- **Environment**: `prompt_prod_v1.md`, `prompt_dev_v1.md`

## Defining Classifiers

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

### ClassifierConfig Properties

| Property | Description | Required |
|----------|-------------|----------|
| `name` | Classifier identifier | Yes |
| `values` | List of allowed values | Yes |
| `default` | Default value (must be in values) | Yes |

## File Naming Convention

Files follow the pattern: `base_classifier(s)_version.ext`

```
prompts/
├── task_en_v1.md      # English v1
├── task_ru_v1.md      # Russian v1
├── task_en_v2.md      # English v2
└── task_ru_v2.md      # Russian v2
```

### Strict Ordering

Classifiers must appear **before** the version:

```
✅ task_en_v1.md         (correct: classifier before version)
❌ task_v1_en.md         (wrong: classifier after version)
```

## Loading with Classifiers

### Using Default Classifier

```python
from promptic import load_prompt
from promptic.versioning import VersioningConfig, ClassifierConfig

config = VersioningConfig(
    classifiers={
        "lang": ClassifierConfig(name="lang", values=["en", "ru"], default="en")
    }
)

# Uses default classifier (en)
content = load_prompt("prompts/task/", versioning_config=config)
# Returns: task_en_v2.md (latest English)
```

### Specifying a Classifier

```python
# Request Russian version
content = load_prompt(
    "prompts/task/",
    classifier={"lang": "ru"},
    versioning_config=config
)
# Returns: task_ru_v2.md (latest Russian)
```

## Multiple Classifiers

You can define multiple classifiers:

```python
config = VersioningConfig(
    classifiers={
        "lang": ClassifierConfig(
            name="lang",
            values=["en", "ru"],
            default="en"
        ),
        "tone": ClassifierConfig(
            name="tone",
            values=["formal", "casual"],
            default="formal"
        ),
    }
)

# File structure:
# prompts/
# ├── task_en_formal_v1.md
# ├── task_en_casual_v1.md
# ├── task_ru_formal_v1.md
# └── task_ru_casual_v1.md

# Request English casual
content = load_prompt(
    "prompts/task/",
    classifier={"lang": "en", "tone": "casual"},
    versioning_config=config
)
```

## Partial Classifier Coverage (Fallback)

When a classifier value doesn't exist for the latest version, promptic returns the **latest version that HAS the requested classifier**:

```python
# Directory contents:
# - task_en_v1.md
# - task_ru_v1.md
# - task_en_v2.md (no Russian v2!)

content = load_prompt(
    "prompts/task/",
    classifier={"lang": "ru"},
    versioning_config=config
)
# Returns: task_ru_v1.md (latest version WITH Russian)
```

This allows gradual addition of localized content without breaking existing queries.

## Specific Version + Classifier

When requesting a specific version with a classifier, the combination must exist exactly:

```python
# This works:
content = load_prompt(
    "prompts/task/",
    version="v1",
    classifier={"lang": "ru"},
    versioning_config=config
)

# This raises VersionNotFoundError (no Russian v2):
content = load_prompt(
    "prompts/task/",
    version="v2",
    classifier={"lang": "ru"},
    versioning_config=config
)
```

## Error Handling

```python
from promptic.versioning import ClassifierNotFoundError

try:
    content = load_prompt(
        "prompts/task/",
        classifier={"lang": "es"},  # Spanish not available
        versioning_config=config
    )
except ClassifierNotFoundError as e:
    print(f"Classifier '{e.classifier_name}' value '{e.requested_value}' not found")
    print(f"Available: {e.available_values}")
    # Available: ['en', 'ru']
```

## Exporting with Classifiers

```python
from promptic import export_version

result = export_version(
    source_path="prompts/task/",
    version_spec="v2",
    target_dir="export/task_v2_ru/",
    classifier={"lang": "ru"},
    versioning_config=config
)
```

## Complete Example

```python
from promptic import render
from promptic.versioning import VersioningConfig, ClassifierConfig

# Configure versioning for a multilingual project
config = VersioningConfig(
    delimiter="-",
    classifiers={
        "lang": ClassifierConfig(
            name="lang",
            values=["en", "ru", "de"],
            default="en"
        ),
        "tone": ClassifierConfig(
            name="tone",
            values=["formal", "casual"],
            default="formal"
        )
    }
)

# Directory structure:
# prompts/
# ├── task-en-formal-v1.md
# ├── task-en-casual-v1.md
# ├── task-ru-formal-v1.md
# └── task-de-formal-v1.md

# Get formal German version
german_formal = render(
    "prompts/task/",
    classifier={"lang": "de", "tone": "formal"},
    versioning_config=config
)
```

## See Also

- [Versioning Configuration Guide](./versioning-configuration.md) - General configuration
- [Version Prereleases Guide](./version-prereleases.md) - Handling alpha/beta/rc versions

