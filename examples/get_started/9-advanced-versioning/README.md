# Example 9: Advanced Versioning

This example demonstrates the advanced versioning features introduced in spec 009, including configurable delimiters, pre-releases, custom patterns, and classifiers.

## Features Covered

1. **Custom Delimiters** - Use `_`, `.`, or `-` for version patterns
2. **Multiple Delimiters** - Mix naming conventions in one directory
3. **Pre-release Handling** - Support for `-alpha`, `-beta`, `-rc` postfixes
4. **Custom Classifiers** - Language/audience variants (e.g., `_en_`, `_ru_`)
5. **Custom Version Patterns** - Non-standard versioning like `_rev42`
6. **Configuration System** - `VersioningConfig` and `VersioningSettings`

## Directory Structure

```
9-advanced-versioning/
├── README.md
├── demo_delimiters.py           # Custom delimiter examples
├── demo_prereleases.py          # Pre-release handling examples
├── demo_classifiers.py          # Classifier (language) examples
├── demo_custom_patterns.py      # Custom regex pattern examples
├── demo_config.py               # Configuration options overview
│
├── prompts_underscore/          # Standard underscore delimiter (_v1.0.0)
│   └── task_v1.0.0.md
│   └── task_v2.0.0.md
│
├── prompts_hyphen/              # Hyphen delimiter (-v1.0.0)
│   └── task-v1.0.0.md
│   └── task-v2.0.0.md
│
├── prompts_dot/                 # Dot delimiter (.v1.0.0)
│   └── task.v1.0.0.md
│   └── task.v2.0.0.md
│
├── prompts_mixed/               # Multiple delimiters in one directory
│   └── task_v1.0.0.md
│   └── task-v2.0.0.md
│
├── prompts_prerelease/          # Pre-release versions
│   └── task_v1.0.0.md
│   └── task_v1.1.0-alpha.md
│   └── task_v1.1.0-beta.md
│   └── task_v1.1.0-rc.1.md
│   └── task_v1.1.0.md
│   └── task_v2.0.0-alpha.md
│
├── prompts_classified/          # Classifier-based variants (language)
│   └── task_en_v1.0.0.md        # English v1
│   └── task_ru_v1.0.0.md        # Russian v1
│   └── task_en_v2.0.0.md        # English v2
│   └── task_ru_v2.0.0.md        # Russian v2
│   └── task_de_v2.0.0.md        # German v2 (no v1)
│
├── prompts_partial_classifier/  # Partial classifier coverage
│   └── task_en_v1.0.0.md        # English v1
│   └── task_ru_v1.0.0.md        # Russian v1
│   └── task_en_v2.0.0.md        # English v2 (no Russian v2!)
│
└── prompts_custom_pattern/      # Custom version patterns
    └── task_rev1.md             # Revision-based versioning
    └── task_rev2.md
    └── task_rev42.md
```

## Running the Examples

```bash
cd examples/get_started/9-advanced-versioning

# Run individual demos
python demo_delimiters.py
python demo_prereleases.py
python demo_classifiers.py
python demo_custom_patterns.py
python demo_config.py
```

## Key Concepts

### 1. Configurable Delimiters

```python
from promptic.versioning import VersioningConfig

# Use hyphen delimiter for files like task-v1.md
config = VersioningConfig(delimiter="-")
content = render("prompts_hyphen/", versioning_config=config)

# Use dot delimiter for files like task.v1.md
config = VersioningConfig(delimiter=".")
content = render("prompts_dot/", versioning_config=config)
```

### 2. Multiple Delimiters

```python
# Support both underscore and hyphen in the same directory
config = VersioningConfig(delimiters=["_", "-"])
content = render("prompts_mixed/", versioning_config=config)
```

### 3. Pre-release Handling

```python
# By default, pre-releases are excluded from "latest"
content = render("prompts_prerelease/")  # Gets v1.1.0, not v2.0.0-alpha

# Include pre-releases
config = VersioningConfig(include_prerelease=True)
content = render("prompts_prerelease/", versioning_config=config)

# Request specific pre-release
content = render("prompts_prerelease/", version="v1.1.0-beta")
```

### 4. Classifiers (Language Variants)

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

# Get latest English (default)
content = render("prompts_classified/", versioning_config=config)

# Get latest Russian
content = render(
    "prompts_classified/",
    classifier={"lang": "ru"},
    versioning_config=config
)
```

### 5. Custom Version Patterns

```python
# For revision-based versioning like task_rev42.md
config = VersioningConfig(
    version_pattern=r"_rev(?P<major>\d+)"
)
content = render("prompts_custom_pattern/", versioning_config=config)
```

## Ordering Rules

### Pre-release Ordering

```
alpha < beta < rc < release
```

So for version `v1.0.0`:
- `v1.0.0-alpha` < `v1.0.0-beta` < `v1.0.0-rc.1` < `v1.0.0`

### Filename Segment Ordering

```
base-classifier(s)-version-prerelease.ext
```

Examples:
- `task_v1.0.0.md` - simple version
- `task_en_v1.0.0.md` - with classifier
- `task_en_v1.0.0-alpha.md` - with classifier and prerelease
- `task-en-v1-rc.1.md` - hyphen delimiter with classifier and prerelease

## Error Handling

```python
from promptic.versioning import (
    VersionNotFoundError,
    ClassifierNotFoundError,
    InvalidVersionPatternError,
)

# Version not found
try:
    render("prompts/", version="v99")
except VersionNotFoundError as e:
    print(f"Available versions: {e.available_versions}")

# Classifier not found
try:
    render("prompts_classified/", classifier={"lang": "es"}, versioning_config=config)
except ClassifierNotFoundError as e:
    print(f"Available values for '{e.classifier_name}': {e.available_values}")

# Invalid pattern
try:
    VersioningConfig(version_pattern=r"_v(\d+)")  # Missing named group!
except ValueError as e:
    print(f"Pattern error: {e}")
```

## Next Steps

- See `docs_site/guides/versioning-configuration.md` for full configuration reference
- See `docs_site/guides/version-classifiers.md` for classifier best practices
- See `docs_site/guides/version-prereleases.md` for pre-release workflows


