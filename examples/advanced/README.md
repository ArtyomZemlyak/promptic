# Advanced Examples

These examples demonstrate real-world use cases with file-first rendering in markdown format.

## Examples

### 1. tg-note-multi-agent-md (`tg-note-multi-agent-md/`)

Markdown-first approach: each .md file is a node that can reference other .md files.

**What you'll learn:**
- How to use markdown files as nodes in a network
- How to reference other markdown files via links
- How to render in file-first mode with format options
- Structure similar to tg-note where prompts are stored as markdown files with links to other instructions

**Files:**
- `note_creation.md` - Root prompt for note creation agent
- `media_processing.md` - Root prompt for media processing agent
- `git_operations.md` - Root prompt for git operations agent
- `common/` - Shared instructions (markdown formatting, git workflow, media handling)
- `note_creation/`, `media_processing/`, `git_operations/` - Agent-specific instructions
- `render_prompt.py` - Python script to render any agent prompt

**Run it:**
```bash
cd examples/advanced/tg-note-multi-agent-md
python3 render_prompt.py note_creation.md
python3 render_prompt.py media_processing.md
python3 render_prompt.py git_operations.md
```

**Output options:**
- Format: markdown (default), yaml, json, jinja2
- Mode: file_first (default, preserves links), full (inlines content)

### 2. tg-note-multi-agent (`tg-note-multi-agent/`)

Blueprint-based approach: using YAML blueprints with file-first rendering.

**What you'll learn:**
- How to use YAML blueprints with file-first rendering
- How to build agent prompts with shared instructions
- How to render with metadata and metrics
- Multi-agent setup where agents share common instructions

**Files:**
- `agents/` - YAML blueprint files for each agent
- `instructions/` - Instruction files (common and agent-specific)
- `render_agent_prompt.py` - Python script to render any agent prompt

**Run it:**
```bash
cd examples/advanced/tg-note-multi-agent
python3 render_agent_prompt.py note_creation
python3 render_agent_prompt.py media_processing
python3 render_agent_prompt.py git_operations
```

**Output includes:**
- File-first markdown with references
- Metadata (token reduction, reference count, etc.)
- Metrics for optimization

## File-First Rendering

Both examples use **file-first rendering** in **markdown format**:
- References to other files are preserved as links
- Output is compact and maintainable
- Files can be edited independently
- Full content can be inlined if needed

## When to Use These Examples

These examples are for users who:
- Understand the basics and want to see real-world applications
- Need multi-agent setups with shared instructions
- Want to optimize token usage with file references
- Prefer markdown-first or blueprint-based approaches

## Next Steps

- **Get Started** (`../get_started/`) - Start here if you're new to promptic
- **Old Examples** (`../old/`) - Previous examples moved for reference
