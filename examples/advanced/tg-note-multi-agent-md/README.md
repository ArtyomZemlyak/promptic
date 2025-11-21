# Multi-Agent Example: Markdown-First (tg-note Style)

This example demonstrates a markdown-first approach where **every file is a node**, similar to how tg-note stores prompts. All prompts and instructions are in Markdown format, making it easy to read, edit, and version control.

## Key Features

- **Markdown-only**: All prompts and instructions are `.md` files
- **Node-based**: Each file is a node that can reference other nodes
- **Minimal code**: Simple Python script with just `load` and `render`
- **tg-note style**: Structure similar to [tg-note prompts](https://github.com/ArtyomZemlyak/tg-note/tree/main/config/prompts)

## Structure

```
tg-note-multi-agent-md/
├── note_creation.md              # Root prompt for note creation agent
├── media_processing.md           # Root prompt for media processing agent
├── git_operations.md              # Root prompt for git operations agent
├── common/                       # Shared instructions
│   ├── markdown_formatting.md
│   ├── git_workflow.md
│   └── media_handling.md
├── note_creation/                # Note creation specific instructions
│   ├── analyze_message.md
│   └── create_note.md
├── media_processing/            # Media processing specific instructions
│   ├── ocr_process.md
│   ├── transcribe_audio.md
│   └── process_video.md
├── git_operations/               # Git operations specific instructions
│   ├── commit_changes.md
│   ├── push_to_github.md
│   └── create_pr.md
├── memory/
│   └── format.md                 # Memory format definition
├── render_prompt.py              # Minimal Python script
└── README.md
```

## Agents

### 1. Note Creation Agent (`note_creation.md`)

Creates structured notes in Markdown format from user messages.

**References:**
- `common/markdown_formatting.md` - Markdown formatting rules
- `common/git_workflow.md` - Git workflow rules
- `note_creation/analyze_message.md` - Message analysis
- `note_creation/create_note.md` - Note creation process
- `common/media_handling.md` - Media handling rules

### 2. Media Processing Agent (`media_processing.md`)

Processes media files (images, audio, video) with OCR and transcription.

**References:**
- `common/media_handling.md` - Media handling rules
- `media_processing/ocr_process.md` - OCR process
- `media_processing/transcribe_audio.md` - Audio transcription
- `media_processing/process_video.md` - Video processing

### 3. Git Operations Agent (`git_operations.md`)

Handles Git operations: commits, pushes, PR creation.

**References:**
- `common/git_workflow.md` - Git workflow rules
- `git_operations/commit_changes.md` - Commit process
- `git_operations/push_to_github.md` - Push process
- `git_operations/create_pr.md` - PR creation

## Usage

### Render Agent Prompt

```bash
# Render note_creation agent prompt (file_first mode, markdown format)
python render_prompt.py note_creation.md

# Render with full mode (inlines all referenced content)
python render_prompt.py note_creation.md markdown full

# Render in YAML format (file_first mode)
python render_prompt.py note_creation.md yaml file_first

# Render in JSON format (full mode)
python render_prompt.py note_creation.md json full
```

### Minimal Code Example

The Python script is extremely simple - just 2 lines of actual work:

```python
from promptic.sdk.nodes import load_node_network, render_node_network

# Load network from markdown file
network = load_node_network("note_creation.md")

# Render with file_first mode (preserves links)
output = render_node_network(
    network,
    target_format="markdown",  # Output format: markdown, yaml, json, jinja2
    render_mode="file_first"   # Rendering mode: file_first (links) or full (inline)
)
```

### Format and Mode Logic

**Format Conversion:**
- If source format == target format and `render_mode="file_first"`: returns raw content without conversion
- Otherwise: converts through JSON intermediate representation

**Render Modes:**
- `file_first`: Preserves file references as links (compact output)
- `full`: Inlines all referenced content into the output (complete output)

That's it! The library handles:
- Format detection (markdown, yaml, json, jinja2)
- Reference resolution (links to other files)
- Network building (recursive loading)
- Format conversion (when needed)
- Rendering (file_first or full mode)

## How It Works

1. **Root Node**: Each agent has a root `.md` file (e.g., `note_creation.md`)
2. **References**: Root file contains markdown links to other instructions
3. **Recursive Loading**: Library automatically loads all referenced files
4. **Network Building**: Creates a network of nodes with all dependencies
5. **Rendering**:
   - **Format**: Determines output format (markdown, yaml, json, jinja2)
   - **Mode**: Determines rendering style:
     - `file_first`: Preserves links (compact, agent reads files on-demand)
     - `full`: Inlines all referenced content (complete, all content in one output)

### Format Conversion Logic

- **Same format + file_first**: Returns raw content without conversion (fast path)
- **Different format or full mode**: Converts through JSON intermediate representation

## Comparison with tg-note

### tg-note Structure
```
config/prompts/
├── agent1.md          # Root prompt
├── agent2.md          # Root prompt
└── instructions/      # Referenced instructions
    ├── common.md
    └── specific.md
```

### This Example
```
tg-note-multi-agent-md/
├── note_creation.md   # Root prompt (node)
├── media_processing.md # Root prompt (node)
└── common/            # Referenced nodes
    └── markdown_formatting.md
```

**Key Difference**: In this example, every file is a **node** that can be loaded and rendered independently, while maintaining the same simple structure as tg-note.

## Benefits

- ✅ **Simple**: Just markdown files with links
- ✅ **Readable**: Easy to read and edit
- ✅ **Versionable**: Git-friendly format
- ✅ **Minimal Code**: 2 lines to load and render
- ✅ **Flexible**: Each file is a node, can be used independently
- ✅ **tg-note Compatible**: Similar structure to tg-note prompts

## Integration with tg-note

This example shows how promptic can be integrated into tg-note:

1. **Replace prompt loading**: Instead of reading `.md` files directly, use `load_node_network()`
2. **Keep structure**: Maintain the same markdown file structure
3. **Add rendering**: Use `render_node_network()` with `file_first` mode for compact prompts
4. **Minimal changes**: Only change the loading/rendering code, not the prompt files

## Example Output

When rendering `note_creation.md` with `file_first` mode:

```markdown
# Note Creation Agent

Ты ассистент для создания заметок в GitHub knowledge base.

## Общие инструкции

- [Markdown форматирование](common/markdown_formatting.md)
- [Git workflow](common/git_workflow.md)

## Шаги работы

1. **Анализ сообщения пользователя**
   - [Подробные инструкции](note_creation/analyze_message.md)
...
```

The agent receives a compact prompt with file references and can read detailed instructions on-demand.
