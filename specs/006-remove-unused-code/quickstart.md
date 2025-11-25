# Quickstart: Simplified promptic Library

**Date**: 2025-01-27  
**Feature**: Remove Unused Code from Library

## Overview

After cleanup, the promptic library focuses on two core features:
1. **Node Networks**: Load and render hierarchical file structures (examples 003, 004)
2. **Versioning**: Load and export versioned prompts (examples 005, 006)

## Installation

```bash
pip install -e .
```

## Core Features

### 1. Node Network Loading and Rendering

Load a network of connected files and render them in various formats.

**Example 003: Multiple Root Files**

```python
from promptic.sdk.nodes import load_node_network, render_node_network
from pathlib import Path

# Load a node network from a root file
root_path = Path("examples/get_started/3-multiple-files/root-1.md")
network = load_node_network(root_path)

# Render the network to markdown
output = render_node_network(
    network,
    target_format="markdown",
    render_mode="full",
)
print(output)
```

**Example 004: Different File Formats**

```python
from promptic.sdk.nodes import load_node_network, render_node_network
from pathlib import Path

# Load a YAML file network
root_path = Path("examples/get_started/4-file-formats/root.yaml")
network = load_node_network(root_path)

# Render to different formats
for target_format in ["yaml", "markdown", "json"]:
    output = render_node_network(
        network,
        target_format=target_format,
        render_mode="full",
    )
    print(f"Rendered to {target_format}:")
    print(output)
```

**Supported formats**: YAML, Markdown, JSON, Jinja2  
**Supported target formats**: YAML, Markdown, JSON

### 2. Versioned Prompt Loading

Load specific versions of prompts from a directory structure with versioned files.

**Example 005: Load Versions**

```python
from promptic import load_prompt
from pathlib import Path

prompts_dir = Path("examples/get_started/5-versioning/prompts")

# Load latest version
latest = load_prompt(prompts_dir, version="latest")
print(latest)

# Load specific version
v1 = load_prompt(prompts_dir, version="v1.0.0")
print(v1)

# Load with partial version (resolves to v2.0.0)
v2 = load_prompt(prompts_dir, version="v2")
print(v2)
```

**Version naming**: Files use version suffixes like `_v1.0.0`, `_v1`, `_v1.1`

### 3. Version Export

Export a specific version of a prompt structure, preserving directory layout and removing version suffixes.

**Example 006: Export Versions**

```python
from promptic import export_version, cleanup_exported_version
from pathlib import Path

prompts_dir = Path("examples/get_started/6-version-export/prompts")
export_dir = Path("examples/get_started/6-version-export/exported/workflow_v1")

# Export version 1.0.0
result = export_version(
    source_path=prompts_dir,
    version_spec="v1.0.0",
    target_dir=export_dir,
    overwrite=True,
)

print(f"Exported {len(result.exported_files)} files")
print(f"Root prompt: {result.root_prompt_content[:100]}...")

# Clean up exported version
cleanup_exported_version(export_dir)
```

**Export behavior**:
- Preserves directory structure
- Removes version suffixes from filenames (e.g., `workflow_v1.0.0.md` → `workflow.md`)
- Keeps explicit version references (e.g., `format_v1.0.0.md` stays as-is if explicitly referenced)

## Public API

### Top-level Exports (`from promptic import ...`)

- `load_prompt(prompts_dir, version)`: Load a versioned prompt
- `export_version(source_path, version_spec, target_dir, overwrite)`: Export a version
- `cleanup_exported_version(target_dir)`: Clean up exported version directory
- `__version__`: Library version string

### Node Network API (`from promptic.sdk.nodes import ...`)

- `load_node_network(root_path)`: Load a node network from a root file
- `render_node_network(network, target_format, render_mode)`: Render a node network

## What Was Removed

The following features were removed as they were not used in examples 003-006:

- **Blueprints**: Entire `promptic.blueprints` package and blueprint-related functions
- **Adapters**: Entire `promptic.adapters` package (data/memory adapters)
- **Token Counting**: `promptic.token_counting` package
- **Settings**: `promptic.settings` package
- **Format Renderers**: `promptic.pipeline.format_renderers` package
- **Instructions**: `promptic.instructions` package
- **Pipeline modules**: Various pipeline modules only used by blueprints

## Migration Guide

If you were using removed features, you need to migrate:

### From Blueprints to Node Networks

**Before (blueprints)**:
```python
from promptic import load_blueprint, render_for_llm

blueprint = load_blueprint("blueprint.yaml")
context = render_for_llm(blueprint)
```

**After (node networks)**:
```python
from promptic.sdk.nodes import load_node_network, render_node_network
from pathlib import Path

network = load_node_network(Path("root.md"))
context = render_node_network(network, target_format="markdown", render_mode="full")
```

### From Adapters to Direct File Access

**Before (adapters)**:
```python
from promptic.adapters import AdapterRegistry
# ... adapter setup ...
```

**After (direct files)**:
Node networks work directly with filesystem. No adapters needed.

## Testing

Run all tests:
```bash
pytest tests/ -v
```

Run examples:
```bash
python examples/get_started/3-multiple-files/render.py
python examples/get_started/4-file-formats/render.py
python examples/get_started/5-versioning/render.py
python examples/get_started/6-version-export/export_demo.py
```

## Next Steps

1. Review the simplified API and ensure it meets your needs
2. Migrate any code using removed features to node networks/versioning
3. Update documentation to reflect simplified architecture
4. Run tests to verify everything works
