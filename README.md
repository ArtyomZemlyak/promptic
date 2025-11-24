# promptic

Easy prompt management for Python projects using file-first architecture and versioning.

## Overview

**promptic** is a Python library for managing prompts and context using a file-first approach. It focuses on two core features:

1. **Node Networks**: Load and render hierarchical file structures with references
2. **Versioning**: Manage and export versioned prompts with semantic versioning

## Installation

```bash
pip install -e .
```

## Quick Start

### Node Networks

Load interconnected files and render them in various formats:

```python
from promptic.sdk.nodes import load_node_network, render_node_network
from pathlib import Path

# Load a node network from a root file
network = load_node_network(Path("prompts/root.md"))

# Render to markdown (or yaml, json)
output = render_node_network(
    network,
    target_format="markdown",
    render_mode="full",
)
print(output)
```

### Versioning

Load and export specific versions of your prompts:

```python
from promptic import load_prompt, export_version
from pathlib import Path

# Load a specific version
prompt = load_prompt(
    prompts_dir=Path("prompts"),
    version="v1.0.0"  # or "latest"
)

# Export a version (removes version suffixes)
result = export_version(
    source_path=Path("prompts"),
    version_spec="v1.0.0",
    target_dir=Path("exported/v1"),
    overwrite=True
)
```

## Features

### File-First Architecture

Organize your prompts as interconnected files in any supported format:
- **YAML**: Structured data with references
- **Markdown**: Human-readable documentation
- **JSON**: Programmatic access
- **Jinja2**: Dynamic templating

Files can reference each other, creating hierarchical structures that are easy to navigate and maintain.

### Semantic Versioning

Version your prompts using semantic versioning conventions:
- Files use version suffixes: `prompt_v1.0.0.md`, `prompt_v2.md`
- Load specific versions or "latest"
- Export versions with clean filenames (suffixes removed)
- Preserve directory structures

### Simple API

The library exports just what you need:
- `load_prompt()` - Load versioned prompts
- `export_version()` - Export a version to a directory
- `cleanup_exported_version()` - Clean up exported files
- `load_node_network()` - Load file networks (from `promptic.sdk.nodes`)
- `render_node_network()` - Render networks (from `promptic.sdk.nodes`)

## Examples

See the `examples/get_started/` directory for complete examples:

- **003-multiple-files**: Load and render networks with multiple root files
- **004-file-formats**: Work with different file formats (YAML, Markdown, JSON, Jinja2)
- **005-versioning**: Load different versions of prompts
- **006-version-export**: Export versions with directory structure preservation

Run examples:

```bash
python examples/get_started/3-multiple-files/render.py
python examples/get_started/4-file-formats/render.py
python examples/get_started/5-versioning/render.py
python examples/get_started/6-version-export/export_demo.py
```

## Development

### Setup

```bash
# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=promptic --cov-report=html
```

### Code Quality

```bash
# Format code
black --line-length=100 src/ tests/
isort --profile=black --line-length=100 src/ tests/

# Run pre-commit hooks (MANDATORY before commit)
pre-commit run --all-files
```

## Architecture

The library follows Clean Architecture principles:

- **Entities**: `ContextNode`, `NodeNetwork` (domain models)
- **Use Cases**: Node loading, rendering, version resolution
- **Interface Adapters**: Format parsers, filesystem resolvers

All dependencies point inward toward the domain layer.

## Documentation

Additional documentation is available in `docs_site/`:
- Architecture documentation
- Versioning guide
- Integration examples

## Requirements

- Python 3.11+
- Dependencies: `pydantic>=2.6`, `pyyaml>=6.0`, `jinja2>=3.1`, `orjson>=3.9`, `packaging>=23.0`, `regex>=2023.10`

## License

See LICENSE file for details.

## Contributing

This library follows strict code quality standards:
1. All code must pass `black` and `isort` formatting
2. All tests must pass (`pytest tests/ -v`)
3. Pre-commit hooks must pass (`pre-commit run --all-files`)
4. See `AGENTS.md` for detailed contribution guidelines

## What Changed (v0.7.0)

This version significantly simplifies the library by removing unused features:

**Removed**:
- Blueprint system (legacy architecture)
- Adapter system (data/memory adapters)
- Token counting functionality
- Settings package
- Various pipeline modules

**Why**: These features were not used in examples 003-006 and added unnecessary complexity. The library now focuses solely on node networks and versioning, which are the core features actively used.

**Migration**: If you were using blueprints, migrate to node networks (see examples). The node network API is simpler and more flexible.
