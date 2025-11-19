# Jinja2 Templating

For complex instruction logic involving conditionals, loops, or data transformations, Promptic supports [Jinja2](https://jinja.palletsprojects.com/) templating. This allows you to create dynamic instructions that adapt structure based on context.

## Usage

Use `.jinja` extension for your instruction files to automatically enable Jinja2 rendering.

```jinja
# Review for {{ data.ticket_id }}

{% if data.is_critical %}
**WARNING: CRITICAL INCIDENT**
Please handle with extreme urgency.
{% endif %}

## Affected Systems
{% for system in data.affected_systems %}
- {{ system.name }} (Status: {{ system.status }})
{% endfor %}
```

## Features

### Variables
Access context variables using double curly braces: `{{ data.variable }}`.

### Conditionals
Control flow with `if/else` blocks:

```jinja
{% if data.user.role == 'admin' %}
You have full access.
{% else %}
Read-only access.
{% endif %}
```

### Loops
Iterate over lists or dictionaries:

```jinja
{% for item in data.items %}
- {{ loop.index }}. {{ item }}
{% endfor %}
```

### Filters
Apply Jinja2 filters to transform data:

```jinja
Title: {{ data.title | upper }}
Count: {{ data.items | length }}
default: {{ data.missing | default('N/A') }}
```

## Context Variables

Same namespaces as Markdown templating:
- `data`: Adapter data
- `memory`: Memory slots
- `step`: Step context
- `blueprint`: Blueprint metadata

## Environment

Promptic uses a dedicated Jinja2 environment for instructions, separate from the prompt rendering environment. This ensures security and isolation.

- **Auto-escaping**: Disabled (instructions are text/markdown)
- **Undefined**: Strict (raises error on missing variables)
- **Trim Blocks**: Enabled by default

### Instruction-Specific Helpers

`Jinja2FormatRenderer` registers a few helpers that only exist inside instruction
templates:

- `format_step(step)` → Renders `[step_id] title` for quick breadcrumbs.
- `get_parent_step(step)` → Returns the parent step ID from the hierarchy list.

These helpers live alongside the standard filters/globals and are documented via
`# AICODE-NOTE` comments inside the renderer for future extension.

## Error Handling

Missing variables or syntax errors will raise a `TemplateRenderError` with details about the error location. Use `{{ data.var | default('fallback') }}` to handle optional data gracefully.
