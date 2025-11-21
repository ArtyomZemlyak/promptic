# Examples

This directory contains examples organized by complexity and use case.

## Directory Structure

### 📚 Get Started (`get_started/`)

Simple examples for beginners to quickly understand the basics of promptic.

- **Simple Include** - Minimal example showing file-first rendering with markdown includes

**Start here if:** You're new to promptic and want to learn the fundamentals.

### 🔧 Advanced (`advanced/`)

Advanced examples demonstrating real-world use cases with file-first rendering.

- **tg-note-multi-agent-md** - Markdown-first approach: each .md file is a node that can reference other .md files
- **tg-note-multi-agent** - Blueprint-based approach: using YAML blueprints with file-first rendering

**Start here if:** You understand the basics and want to see real-world applications.

### 📦 Old (`old/`)

Previous examples that have been moved here for reference. These examples may use older patterns or be superseded by examples in other directories.

## Quick Start

1. **New to promptic?** → Start with `get_started/simple-include/`
2. **Ready for real-world examples?** → Check out `advanced/`

## Running Examples

### Get Started Example

The simplest example showing file-first rendering:

```bash
cd examples/get_started/simple-include
python3 render.py
```

This example demonstrates:
- Loading a markdown file with references to other files
- Rendering in file-first mode (preserving links)
- Minimal setup (just 3 files and ~30 lines of code)

### Advanced Examples

#### Markdown-First Approach (tg-note-multi-agent-md)

```bash
cd examples/advanced/tg-note-multi-agent-md
python3 render_prompt.py note_creation.md
```

This example shows how to:
- Use markdown files as nodes in a network
- Reference other markdown files via links
- Render in file-first mode with format options

#### Blueprint-Based Approach (tg-note-multi-agent)

```bash
cd examples/advanced/tg-note-multi-agent
python3 render_agent_prompt.py note_creation
```

This example demonstrates:
- Using YAML blueprints with file-first rendering
- Building agent prompts with shared instructions
- Rendering with metadata and metrics

## File-First Rendering

All examples use **file-first rendering** in **markdown format**. This means:
- References to other files are preserved as links
- Output is compact and maintainable
- Files can be edited independently
- Full content can be inlined if needed (using `render_mode="full"`)

## Documentation

Each directory contains a README with detailed information about the examples it contains.
