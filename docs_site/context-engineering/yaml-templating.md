# YAML Custom Templating

Promptic allows you to define **custom placeholder patterns** for YAML files (or any text format). This is useful when you need to adhere to specific syntax requirements or avoid collisions with existing template markers.

## Configuration

To use custom patterns, you must provide a `pattern` regex when defining the `InstructionNode` (or in your blueprint YAML).

### Regex Requirement

The pattern **MUST** be a valid Python regular expression and **MUST** include a named capturing group called `placeholder`.

**Format:** `(?P<placeholder>...)`

### Examples

| Syntax | Regex Pattern | Matches |
|--------|---------------|---------|
| `{{ var }}` | `\{\{(?P<placeholder>[^}]+)\}\}` | `{{ data.name }}` |
| `$(var)` | `\$\((?P<placeholder>[\w\.]+)\)` | `$(data.name)` |
| `%var%` | `%(?P<placeholder>[\w\.]+)%` | `%data.name%` |
| `<%= var %>` | `<%=\s*(?P<placeholder>[\w\.]+)\s*%>` | `<%= data.name %>` |

## Usage in Blueprints

```yaml
global_instructions:
  - instruction_id: "api_config"
    format: "yaml"
    source_uri: "config/api.yaml"
    pattern: "\\$\\((?P<placeholder>[\\w\\.]+)\\)"  # Escaped backslashes for YAML string
```

## Default Behavior

If no `pattern` is provided for a `yaml` or `yml` file, Promptic defaults to the standard `{{ placeholder }}` syntax.

## Rendering

The renderer extracts the text captured in the `placeholder` group, trims whitespace, and resolves it against the context variables (supporting dot notation).

## Error Handling

- **Invalid Pattern**: Raises `TemplateRenderError` (syntax error) if the regex is invalid or missing the `placeholder` group.
- **Missing Data**: Raises `TemplateRenderError` (missing placeholder) if the resolved variable is not found in the context.

> Need a refresher on available variables? See
> [Template Context Variables](./template-context-variables.md) for the full namespace matrix.
