# Markdown Templating

Promptic supports dynamic data insertion in Markdown instruction files using Python's string format syntax (`{}`). This allows you to create reusable instruction templates that adapt to context data.

## Syntax

Use curly braces `{}` to insert variables from the context.

```markdown
# Analysis for {data.project_name}

Please analyze the following data:
{data.analysis_target}
```

### Context Variables

Variables are namespaced to avoid collisions:

- **`data`**: Access data slot values (e.g., `{data.user.name}`).
- **`memory`**: Access memory slot values (e.g., `{memory.prior_findings}`).
- **`step`**: Access current step information (e.g., `{step.title}`).
- **`blueprint`**: Access blueprint metadata (e.g., `{blueprint.name}`).

### Nested Access

You can access nested dictionary keys or object attributes using dot notation:

```markdown
User: {data.user.profile.name}
Role: {data.user.settings.role}
```

This works even if the underlying data structure uses dictionaries (which normally require `['key']` access in Python). Promptic handles the resolution automatically.

### Escaping

If you need to include literal curly braces in your content, double them:

- `{{` renders as `{`
- `}}` renders as `}`

**Example:**
```markdown
The JSON format uses {{ curly braces }} to wrap objects.
```
Renders as:
```markdown
The JSON format uses { curly braces } to wrap objects.
```

## Example

**Instruction File (`instruction.md`):**
```markdown
# Task: {step.title}

Analyze the dataset provided in {data.source_file}.

**Context**:
User: {data.user.name} (Role: {data.user.role})
```

**Data:**
```json
{
  "source_file": "sales_2023.csv",
  "user": {
    "name": "Alice",
    "role": "Analyst"
  }
}
```

**Rendered Output:**
```markdown
# Task: Analyze Sales

Analyze the dataset provided in sales_2023.csv.

**Context**:
User: Alice (Role: Analyst)
```

### Hierarchical Extensions

Combine Markdown templating with [Hierarchical Markdown](./hierarchical-markdown.md)
to add heading-aware structure and conditional markers such as
`<!-- if:data.flag --> ... <!-- endif -->`. The hierarchy parser runs before `{}` placeholder
expansion, so you can safely mix data substitutions with lightweight conditional logic.

## Error Handling

If a placeholder references a missing key, Promptic raises a `TemplateRenderError` with details about the missing key and the instruction ID.

To handle optional values, consider using [Jinja2 Templating](./jinja2-templating.md) (User Story 2) which supports conditional logic.
