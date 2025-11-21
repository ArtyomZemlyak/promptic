# Multi-Agent Example: tg-note Style

This example demonstrates a multi-agent setup similar to tg-note, where multiple agents share common instructions while each has its own root prompt and specific instructions.

## Structure

```
tg-note-multi-agent/
├── agents/                          # Agent blueprints
│   ├── note_creation.yaml          # Note creation agent
│   ├── media_processing.yaml        # Media processing agent
│   └── git_operations.yaml          # Git operations agent
├── instructions/
│   ├── common/                      # Shared instructions
│   │   ├── markdown_formatting.md  # Common markdown rules
│   │   ├── git_workflow.md          # Common git rules
│   │   └── media_handling.md        # Common media rules
│   ├── note_creation/               # Note creation specific
│   │   ├── analyze_message.md
│   │   └── create_note.md
│   ├── media_processing/            # Media processing specific
│   │   ├── ocr_process.md
│   │   ├── transcribe_audio.md
│   │   └── process_video.md
│   └── git_operations/              # Git operations specific
│       ├── commit_changes.md
│       ├── push_to_github.md
│       └── create_pr.md
├── memory/
│   └── format.md                    # Memory format definition
├── render_agent_prompt.py           # Script to render agent prompts
└── README.md
```

## Agents

### 1. Note Creation Agent

Creates structured notes in Markdown format from user messages.

**Blueprint**: `agents/note_creation.yaml`

**Shared Instructions**:
- `common/markdown_formatting.md` - Markdown formatting rules
- `common/git_workflow.md` - Git workflow rules

**Specific Instructions**:
- `note_creation/analyze_message.md` - Message analysis
- `note_creation/create_note.md` - Note creation process

### 2. Media Processing Agent

Processes media files (images, audio, video) with OCR and transcription.

**Blueprint**: `agents/media_processing.yaml`

**Shared Instructions**:
- `common/media_handling.md` - Media handling rules

**Specific Instructions**:
- `media_processing/ocr_process.md` - OCR process
- `media_processing/transcribe_audio.md` - Audio transcription
- `media_processing/process_video.md` - Video processing

### 3. Git Operations Agent

Handles Git operations: commits, pushes, PR creation.

**Blueprint**: `agents/git_operations.yaml`

**Shared Instructions**:
- `common/git_workflow.md` - Git workflow rules

**Specific Instructions**:
- `git_operations/commit_changes.md` - Commit process
- `git_operations/push_to_github.md` - Push process
- `git_operations/create_pr.md` - PR creation

## Common Instructions

These instructions are shared across multiple agents:

1. **markdown_formatting.md** - Used by note_creation agent
2. **git_workflow.md** - Used by note_creation and git_operations agents
3. **media_handling.md** - Used by note_creation and media_processing agents

## Usage

### Render Agent Prompt with file_first Mode

```bash
# Render note_creation agent prompt
python render_agent_prompt.py note_creation

# Render media_processing agent prompt
python render_agent_prompt.py media_processing

# Render git_operations agent prompt
python render_agent_prompt.py git_operations
```

### Example Output

When rendering with file_first mode, you'll get a compact prompt like:

```markdown
Ты ассистент для создания заметок в GitHub knowledge base.

Твоя задача - анализировать сообщения пользователя и создавать
структурированные заметки в формате Markdown.

## Шаги:

1. Анализ сообщения пользователя (подробнее - note_creation/analyze_message.md)
2. Создание заметки (подробнее - note_creation/create_note.md)
3. Обработка медиа-файлов (подробнее - common/media_handling.md)

## Общие инструкции:

- Markdown форматирование (подробнее - common/markdown_formatting.md)
- Git workflow (подробнее - common/git_workflow.md)
```

The agent receives a compact prompt with file references and can read detailed instructions on-demand.

## Key Features

1. **Shared Instructions**: Common instructions are reused across agents
2. **Agent-Specific Instructions**: Each agent has its own specific instructions
3. **File-First Rendering**: Compact prompts with file references
4. **Hierarchical Structure**: Instructions organized by agent and type

## Integration with tg-note

This example demonstrates how promptic can be integrated into tg-note:

1. **Multiple Agents**: Each agent has its own blueprint
2. **Common Instructions**: Shared instructions reduce duplication
3. **File-First Approach**: Agents receive compact prompts and read detailed instructions on-demand
4. **Media Handling**: Structured approach to OCR and media processing

## Benefits

- **Reduced Context Size**: File-first rendering reduces token usage by 60-80%
- **Maintainability**: Common instructions are updated once, used everywhere
- **Flexibility**: Agents can read detailed instructions only when needed
- **Structure**: Clear organization of instructions by agent and type
