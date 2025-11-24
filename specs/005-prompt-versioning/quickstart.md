# Quickstart: Prompt Versioning System

**Feature**: Prompt versioning with semantic versioning support, hierarchical version resolution, export functionality, and cleanup operations.

## Prerequisites

```bash
# Install promptic with versioning support
pip install promptic

# Set logging level (optional, default: INFO)
export PROMPTIC_LOG_LEVEL=DEBUG
```

## Basic Usage

### 1. Loading Prompts with Version Resolution

#### Load latest version (default)
```python
from promptic import load_prompt

# Directory contains: root_prompt_v1.0.0.md, root_prompt_v1.1.0.md, root_prompt_v2.0.0.md
prompt = load_prompt("prompts/task1/", version="latest")  # Loads v2.0.0
# Or simply:
prompt = load_prompt("prompts/task1/")  # Latest by default
```

#### Load specific version
```python
# Load v1.1.0 specifically
prompt = load_prompt("prompts/task1/", version="v1.1.0")

# Simplified forms supported (normalized automatically)
prompt = load_prompt("prompts/task1/", version="v1")      # Loads v1.0.0
prompt = load_prompt("prompts/task1/", version="v1.1")    # Loads v1.1.0
prompt = load_prompt("prompts/task1/", version="v1.1.1")  # Loads v1.1.1
```

#### Load by exact file path (bypass version resolution)
```python
# Direct file path bypasses version resolution
prompt = load_prompt("prompts/task1/root_prompt_v2.0.0.md")
```

#### Handle missing versions
```python
from promptic.versioning import VersionNotFoundError

try:
    prompt = load_prompt("prompts/task1/", version="v5.0.0")
except VersionNotFoundError as e:
    print(f"Version not found: {e.available_versions}")  # Shows: ['v1.0.0', 'v1.1.0', 'v2.0.0']
    print(f"Latest available: {e.suggested_version}")    # Shows: v2.0.0 (latest)
```

### 2. Hierarchical Version Resolution

#### Load with hierarchical version specifications
```python
from promptic import load_prompt

# Load root at v1.0.0, but instructions/process.md at v2.0.0
version_spec = {
    "root": "v1.0.0",
    "instructions/process": "v2.0.0"
}
prompt = load_prompt("prompts/task1/", version=version_spec)

# Nested prompts default to latest if not specified
version_spec = {
    "root": "v1.0.0"
    # instructions/process.md will use latest version (v2.0.0)
}
prompt = load_prompt("prompts/task1/", version=version_spec)
```

### 3. Exporting Version Snapshots (File-First Mode)

#### Export complete version snapshot
```python
from promptic.versioning import export_version

# Export prompts/task1/ at v2.0.0 to export/task1_v2/
result = export_version(
    source_path="prompts/task1/",
    version_spec="v2.0.0",
    target_dir="export/task1_v2/"
)

# Returns root prompt content with resolved paths
print(result.root_prompt_content)  # Root prompt with updated path references

# Structure preserved:
# export/task1_v2/
# ├── root_prompt.md          (from root_prompt_v2.0.0.md)
# ├── instructions/
# │   └── process.md          (from instructions/process_v2.0.0.md)
# └── templates/
#     └── data.md             (from templates/data_v2.0.0.md)
```

#### Export with hierarchical version specification
```python
# Export with specific versions for different parts
version_spec = {
    "root": "v1.0.0",
    "instructions/process": "v2.0.0"
}
result = export_version(
    source_path="prompts/task1/",
    version_spec=version_spec,
    target_dir="export/task1_mixed/"
)
```

#### Handle export errors
```python
from promptic.versioning import ExportError, ExportDirectoryExistsError

try:
    result = export_version(
        source_path="prompts/task1/",
        version_spec="v2.0.0",
        target_dir="export/task1_v2/"
    )
except ExportDirectoryExistsError:
    # Directory already exists - use overwrite=True to overwrite
    result = export_version(
        source_path="prompts/task1/",
        version_spec="v2.0.0",
        target_dir="export/task1_v2/",
        overwrite=True
    )
except ExportError as e:
    print(f"Export failed: {e.missing_files}")  # Lists missing files
```

### 4. Cleaning Up Exported Versions

#### Remove exported version directory
```python
from promptic.versioning import cleanup_exported_version

# Safe cleanup of export directory
cleanup_exported_version("export/task1_v2/")
```

#### Handle cleanup errors
```python
from promptic.versioning import InvalidCleanupTargetError, CleanupTargetNotFoundError

try:
    cleanup_exported_version("prompts/task1/")  # Source directory - protected
except InvalidCleanupTargetError:
    print("Cannot delete source prompt directory - use export directory only")

try:
    cleanup_exported_version("export/nonexistent/")
except CleanupTargetNotFoundError:
    print("Export directory not found")
```

## Complete Example: Version Workflow

```python
from promptic import load_prompt
from promptic.versioning import export_version, cleanup_exported_version

# 1. Load prompt at specific version
prompt = load_prompt("prompts/note_creation/", version="v1.1.0")

# 2. Export version snapshot for deployment
result = export_version(
    source_path="prompts/note_creation/",
    version_spec="v1.1.0",
    target_dir="deploy/prompts_v1.1.0/"
)

# Use exported root prompt
print(result.root_prompt_content)

# 3. After deployment, cleanup export
cleanup_exported_version("deploy/prompts_v1.1.0/")
```

## Version Naming Conventions

### Semantic Versioning Format

Files are versioned using semantic versioning postfixes:
- `_v1` or `_v1.0.0` → Normalized to v1.0.0
- `_v1.1` or `_v1.1.0` → Normalized to v1.1.0
- `_v1.1.1` → Full semantic version

### File Structure Example

```
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

- **If versioned files exist**: System uses versioned files only, ignores unversioned files with same base name
- **If only unversioned files exist**: System uses unversioned files as default version (backward compatibility)
- **Example**: Directory with both `prompt.md` and `prompt_v1.0.0.md` → System uses `prompt_v1.0.0.md`, ignores `prompt.md`

## Logging Configuration

```python
import os
import logging

# Configure logging level via environment variable
os.environ["PROMPTIC_LOG_LEVEL"] = "DEBUG"  # Options: DEBUG, INFO, WARNING, ERROR

# Structured logging output includes:
# - version: Version identifier
# - path: File path
# - operation: Operation type (resolve, export, cleanup)
# - timestamp: Operation timestamp

# Example DEBUG log:
# {
#   "version": "v1.1.0",
#   "path": "prompts/task1/root_prompt_v1.1.0.md",
#   "operation": "version_resolved",
#   "timestamp": "2025-01-28T10:30:00Z"
# }
```

## Error Handling Summary

| Error | When Raised | Resolution |
|-------|-------------|------------|
| `VersionNotFoundError` | Requested version doesn't exist | Check `available_versions` for valid options |
| `VersionDetectionError` | Ambiguous version detection | Ensure filename has single clear version postfix |
| `VersionResolutionCycleError` | Circular version references | Review hierarchical version specifications |
| `ExportError` | Missing files during export | Ensure all referenced files exist |
| `ExportDirectoryExistsError` | Target directory exists | Use `overwrite=True` or choose different target |
| `InvalidCleanupTargetError` | Attempting to delete source directory | Use export directory paths only |
| `CleanupTargetNotFoundError` | Export directory doesn't exist | Verify export directory path |

## Integration with Existing Workflows

### Inline Mode
```python
from promptic import load_blueprint, render_for_llm

# Version resolution applies at loading stage
blueprint = load_blueprint("blueprints/task1/", version="v1.1.0")

# Rendering inlines content (loses version info in output)
rendered = render_for_llm(blueprint, render_mode="inline")
```

### File-First Mode
```python
from promptic import load_blueprint, render_for_llm

# Version resolution applies at loading stage
blueprint = load_blueprint("blueprints/task1/", version="v1.1.0")

# Rendering preserves file references (version info in source files)
rendered = render_for_llm(blueprint, render_mode="file_first")
```

## Next Steps

- See `docs_site/prompt-versioning/versioning-guide.md` for comprehensive documentation
- Check `examples/versioning/` for complete example projects
- Review `specs/005-prompt-versioning/spec.md` for detailed requirements
