# promptic

A Python library for managing prompts and context using file-first architecture with cross-references and semantic versioning.

## Overview

**promptic** helps you organize complex prompts and instructions across multiple files with cross-references, version management, and format conversion. Perfect for managing LLM prompts, multi-agent systems, and structured instruction hierarchies.

### Core Features

1. **📁 File Networks** - Load and render hierarchical file structures with cross-references
   - Link files together using references (markdown links, `$ref`, jinja2 comments)
   - Support for YAML, JSON, Markdown, and Jinja2 formats
   - Convert between formats seamlessly
   - Two render modes: inline all content or preserve references

2. **🔖 Semantic Versioning** - Version your prompts with semantic versioning
   - Version files using suffixes: `prompt_v1.0.0.md`, `prompt_v2.md`
   - Load specific versions or always get "latest"
   - Export clean snapshots without version suffixes
   - Hierarchical version resolution

## Installation

```bash
pip install -e .
```

## Quick Start

### 1. Working with File Networks

Create interconnected prompt files and render them:

**Create files with cross-references:**

```markdown
<!-- main.md -->
# Main Prompt

Here are the instructions:
[Process Steps](./steps.md)

Context information:
[Background Info](./context.md)
```

**Load and render:**

```python
from promptic.sdk.nodes import load_node_network, render_node_network

# Load the file network
network = load_node_network("main.md")

# Render with all content inlined
output = render_node_network(
    network,
    target_format="markdown",
    render_mode="full"  # Inlines all referenced content
)
print(output)

# Or preserve references as links
output = render_node_network(
    network,
    target_format="markdown",
    render_mode="file_first"  # Keeps references as links
)
```

**Convert between formats:**

```python
# Load YAML, output as JSON
network = load_node_network("config.yaml")
json_output = render_node_network(network, target_format="json")

# Load Markdown, output as YAML
network = load_node_network("prompt.md")
yaml_output = render_node_network(network, target_format="yaml")
```

### 2. Version Management

Version your prompts and export clean snapshots:

**Version your files:**

```
prompts/
  workflow_v1.0.0.md
  workflow_v2.0.0.md
  tasks/
    definition_v1.0.0.md
    definition_v2.0.0.md
```

**Load specific versions:**

```python
from promptic import load_prompt

# Load latest version
latest = load_prompt("prompts/", version="latest")

# Load specific version
v1 = load_prompt("prompts/", version="v1.0.0")
v2 = load_prompt("prompts/", version="v2.0.0")
```

**Export version snapshots:**

```python
from promptic import export_version

# Export a complete version (removes version suffixes)
result = export_version(
    source_path="prompts/",
    version_spec="v2.0.0",
    target_dir="deployed/v2",
    overwrite=True
)

# Result preserves directory structure:
# deployed/v2/workflow.md  (was workflow_v2.0.0.md)
# deployed/v2/tasks/definition.md  (was definition_v2.0.0.md)
```

## Key Features

### 📁 File Networks with Cross-References

Organize prompts across multiple files and link them together:

**Supported Formats:**
- **Markdown** - Human-readable docs with `[label](path)` links
- **YAML** - Structured data with `{$ref: "path"}` references
- **JSON** - Programmatic access with `{"$ref": "path"}` references
- **Jinja2** - Dynamic templates with `{# ref: path #}` references

**Render Modes:**
- `file_first` - Preserves file references as links (compact output)
- `full` - Inlines all referenced content at reference locations (expanded output)

**Format Conversion:**
Convert between any supported formats while preserving structure and references.

### 🔖 Semantic Versioning

Version your prompts systematically:

**Version Syntax:**
- Full version: `prompt_v1.0.0.md`
- Major.minor: `prompt_v1.2.md`
- Major only: `prompt_v2.md`

**Features:**
- Load specific versions or always use "latest"
- Export clean snapshots (version suffixes removed)
- Hierarchical version resolution (different versions per subdirectory)
- Preserves directory structures on export

### 🎯 Simple API

**Core Functions:**
```python
# Versioning API
from promptic import load_prompt, export_version, cleanup_exported_version

# File Networks API  
from promptic.sdk.nodes import load_node_network, render_node_network
```

That's it! Just 5 functions for all functionality.

## Examples

Complete working examples in `examples/get_started/`:

| Example | Description | Key Concepts |
|---------|-------------|--------------|
| **1-inline-full-render/** | Simple file with includes | Basic loading, full render mode |
| **2-file-first/** | Preserving file references | file_first render mode |
| **3-multiple-files/** | Multiple root files | Shared includes across files |
| **4-file-formats/** | All formats (YAML/JSON/Jinja2/MD) | Format conversion, mixed formats |
| **5-versioning/** | Loading specific versions | Semantic versioning, version resolution |
| **6-version-export/** | Exporting clean snapshots | Version export, deployment |

**Run examples:**

```bash
# Basic file network
python examples/get_started/1-inline-full-render/render.py

# Format conversion
python examples/get_started/4-file-formats/render.py

# Versioning
python examples/get_started/5-versioning/render.py

# Version export
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

## Use Cases

**promptic** is perfect for:

- 🤖 **LLM Prompt Management** - Organize complex prompts across multiple files
- 🔄 **Multi-Agent Systems** - Manage instructions for different agents with shared context
- 📚 **Instruction Hierarchies** - Build structured documentation with cross-references
- 🚀 **Prompt Deployment** - Version and deploy prompts to production environments
- 🧪 **Prompt Testing** - Test different versions side-by-side
- 📝 **Documentation** - Create interconnected documentation with version control

## Architecture

The library follows Clean Architecture principles with clear separation of concerns:

- **Domain Layer**: Core models (`ContextNode`, `NodeNetwork`)
- **Use Cases**: Loading, rendering, version resolution
- **Adapters**: Format parsers (YAML/JSON/Markdown/Jinja2), filesystem operations

See `docs_site/` for detailed architecture documentation.

## Requirements

- Python 3.11+
- Dependencies: `pydantic>=2.6`, `pyyaml>=6.0`, `jinja2>=3.1`, `orjson>=3.9`, `packaging>=23.0`, `regex>=2023.10`

## License

See LICENSE file for details.

## Contributing

This library follows strict code quality standards:

1. **Code Formatting**: All code must pass `black` and `isort` formatting
2. **Tests**: All tests must pass (`pytest tests/ -v`)
3. **Pre-commit Hooks**: Must pass before any commit (`pre-commit run --all-files`)
4. **Documentation**: Update docs for new features

See `AGENTS.md` for detailed contribution guidelines and development workflow.

## Changelog

### v0.1.0 (2025-11-24)

**Initial Release** 🎉

Core functionality:
- ✅ File network loading and rendering with cross-references
- ✅ Support for Markdown, YAML, JSON, and Jinja2 formats
- ✅ Two render modes: `file_first` and `full`
- ✅ Format conversion between all supported formats
- ✅ Semantic versioning with version suffixes
- ✅ Version loading and resolution
- ✅ Version export with clean snapshots
- ✅ Hierarchical version resolution
- ✅ Complete example suite in `examples/get_started/`
- ✅ Full test coverage
