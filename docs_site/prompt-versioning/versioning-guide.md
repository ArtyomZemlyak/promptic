# Prompt Versioning Guide

This guide covers the prompt versioning system in `promptic`. The versioning system allows you to manage multiple versions of prompts, resolve dependencies hierarchically, and export version snapshots for deployment.

## Overview

The prompt versioning system provides:
- **Semantic Versioning**: Support for standard semantic versioning (v1.0.0, v1.1.0, etc.).
- **Hierarchical Resolution**: Ability to version root prompts and nested prompts independently.
- **Version-Aware Loading**: Load prompts by version ("latest" or specific version).
- **Export Functionality**: Export complete version snapshots (file-first mode compatible).
- **Cleanup Operations**: Safe cleanup of exported version directories.

## File Structure & Naming

Prompts are versioned using file naming conventions. The system scans directories for files with version postfixes.

### Format
Files must follow the pattern `filename_v{MAJOR}.{MINOR}.{PATCH}.ext` or simplified forms `_v{MAJOR}` and `_v{MAJOR}.{MINOR}`.

### Example Structure
```text
prompts/task1/
├── root_prompt_v1.0.0.md     # Version 1.0.0
├── root_prompt_v1.1.0.md     # Version 1.1.0 (patch update)
├── root_prompt_v2.0.0.md     # Version 2.0.0 (major update)
├── instructions/
│   ├── process_v1.0.0.md     # Nested prompt v1.0.0
│   ├── process_v1.1.0.md     # Nested prompt v1.1.0
│   └── process_v2.0.0.md     # Nested prompt v2.0.0
└── templates/
    ├── data_v1.0.0.md        # Template v1.0.0
    └── data_v2.0.0.md        # Template v2.0.0
```

### Versioned vs Unversioned Files
- **Versioned Files**: If versioned files exist, the system uses them for resolution.
- **Unversioned Files**: If only unversioned files exist (e.g., `prompt.md`), they are treated as the default version for backward compatibility.
- **Precedence**: Versioned files take precedence over unversioned files when versioning is active.

## Basic Usage

### Loading Prompts

```python
from promptic import load_prompt

# Load latest version (default)
prompt = load_prompt("prompts/task1/", version="latest")
# Or simply:
prompt = load_prompt("prompts/task1/")

# Load specific version
prompt = load_prompt("prompts/task1/", version="v1.1.0")

# Simplified forms are normalized automatically
prompt = load_prompt("prompts/task1/", version="v1")      # v1.0.0
prompt = load_prompt("prompts/task1/", version="v1.1")    # v1.1.0
```

### Hierarchical Resolution

You can specify different versions for different parts of the prompt hierarchy using a dictionary.

```python
# Load root at v1.0.0, but instructions/process at v2.0.0
version_spec = {
    "root": "v1.0.0",
    "instructions/process": "v2.0.0"
}
prompt = load_prompt("prompts/task1/", version=version_spec)

# Nested prompts default to "latest" if not specified
version_spec = {
    "root": "v1.0.0"
}
prompt = load_prompt("prompts/task1/", version=version_spec)
```

## Exporting Versions

The export function allows you to create a standalone snapshot of a specific version hierarchy. This is useful for deploying prompts or freezing a version for production.

### Usage

```python
from promptic.versioning import export_version

# Export version v2.0.0 to a target directory
result = export_version(
    source_path="prompts/task1/",
    version_spec="v2.0.0",
    target_dir="export/task1_v2/"
)

# The result contains the root prompt content with resolved paths
print(result.root_prompt_content)
print(f"Exported {len(result.exported_files)} files")
```

### Export Structure
The export preserves the hierarchical directory structure but removes version postfixes from filenames.

```text
export/task1_v2/
├── root_prompt.md          (from root_prompt_v2.0.0.md)
├── instructions/
│   └── process.md          (from instructions/process_v2.0.0.md)
└── templates/
    └── data.md             (from templates/data_v2.0.0.md)
```

Path references in files are automatically updated to work in the exported structure.

## Cleanup Operations

To manage disk space or remove temporary exports, use the cleanup function.

### Usage

```python
from promptic.versioning import cleanup_exported_version

# Clean up an exported directory
cleanup_exported_version("export/task1_v2/")
```

### Safety Checks
The cleanup function includes safeguards to prevent accidental deletion of source prompt directories:
- Validates that the target directory looks like an export (not a source directory).
- Raises `InvalidCleanupTargetError` if called on a source directory.
- Raises `CleanupTargetNotFoundError` if the directory doesn't exist.

## SDK Integration

Versioning is integrated into the core SDK functions:

- `load_prompt(path, version=...)`
- `load_blueprint(path, version=...)`

And via the `promptic.versioning` module:

- `export_version(source, version, target)`
- `cleanup_exported_version(path)`

## Error Handling

| Error | Description | Resolution |
|-------|-------------|------------|
| `VersionNotFoundError` | The requested version does not exist. | Check available versions in the error message. |
| `VersionDetectionError` | Ambiguous versioning (e.g., multiple files for same version). | Ensure unique version postfixes. |
| `VersionResolutionCycleError` | Circular dependency in hierarchical versions. | Check your version specifications. |
| `ExportError` | Failed to export files (e.g., missing references). | Ensure all referenced files exist. |
| `ExportDirectoryExistsError` | Target directory exists. | Use `overwrite=True` or a different path. |
| `InvalidCleanupTargetError` | Attempted to clean up a source directory. | Use only on exported directories. |

## Best Practices

1. **Semantic Versioning**: Stick to standard semantic versioning (major.minor.patch) to ensure predictable resolution.
2. **Atomic Exports**: Use `export_version` for deployments to ensure you have a self-contained, immutable snapshot.
3. **Hierarchical Management**: Version shared components (like instructions or templates) independently to reuse them across different root prompts.
4. **Testing**: Test your version resolution logic locally using the `load_prompt` function before exporting.
