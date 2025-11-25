# Variable Insertion Guide

## Overview

Variable insertion allows you to pass runtime values into prompts at render/export time. This enables dynamic prompt generation with reusable templates.

## Basic Usage

### Simple Variables (Global Scope)

Apply variables throughout the entire prompt hierarchy:

```python
from promptic.sdk.nodes import load_node_network, render_node_network

network = load_node_network("prompts/root.md")

output = render_node_network(
    network,
    target_format="markdown",
    render_mode="full",
    vars={"user_name": "Alice", "task_type": "analysis"}
)
```

In your prompt files, use `{{variable_name}}` syntax:

```markdown
# Welcome {{user_name}}

Your task is: {{task_type}}
```

## Scoping Methods

### 1. Simple Scope (Global)

Variables apply to all nodes in the hierarchy.

**Syntax**: `{"variable": "value"}`

**Example**:
```python
vars = {
    "user_name": "Alice",
    "task_type": "analysis"
}
```

### 2. Node Scope

Target specific nodes by name. Useful when multiple nodes might have similarly-named variables.

**Syntax**: `{"node_name.variable": "value"}`

**Example**:
```python
vars = {
    "user_name": "Alice",  # Global
    "instructions.format": "detailed",  # Only for "instructions" nodes
    "templates.format": "brief"  # Only for "templates" nodes
}
```

**In prompts**:
- `instructions.md` with `{{format}}` gets "detailed"
- `templates.md` with `{{format}}` gets "brief"
- Any other node with `{{format}}` keeps the placeholder

### 3. Path Scope

Target nodes at specific positions in the hierarchy. Maximum precision.

**Syntax**: `{"root.group.node.variable": "value"}`

**Example**:
```python
vars = {
    "user_name": "Alice",  # Global
    "instructions.format": "detailed",  # Node scope
    "root.group.instructions.style": "technical"  # Path scope - only at this path
}
```

**In prompts**:
- `root/group/instructions.md` at path `root.group.instructions` gets all three variables
- `root/other/instructions.md` gets only `user_name` and `format` (not `style`)

## Precedence Rules

When multiple scopes define the same variable, the most specific wins:

**Priority**: Path > Node > Simple

**Example**:
```python
vars = {
    "format": "default",  # Simple scope
    "instructions.format": "node-specific",  # Node scope
    "root.group.instructions.format": "path-specific"  # Path scope
}
```

Results:
- At `root.group.instructions`: "path-specific" (highest precedence)
- At `root.other.instructions`: "node-specific" (node scope wins)
- At any other node: "default" (simple scope)

## Format-Specific Behavior

### Markdown, YAML, JSON

Use `{{variable_name}}` marker syntax:

**Markdown**:
```markdown
Hello {{user_name}}!
```

**YAML**:
```yaml
user: {{user_name}}
task: {{task_type}}
```

**JSON**:
```json
{
  "user": "{{user_name}}",
  "task": "{{task_type}}"
}
```

### Jinja2

Use native Jinja2 syntax with spaces:

```jinja2
Hello {{ user_name }}!

{% if task_type == "analysis" %}
Analysis mode active
{% endif %}
```

Jinja2 variables support:
- Filters: `{{ name|upper }}`
- Control structures: `{% if ... %}`
- Template inheritance: `{% extends ... %}`

## Variable Naming Rules

Valid variable names:
- Start with letter or underscore: `name`, `_private`
- Contain letters, numbers, underscores: `user_name`, `taskType`, `var123`
- Case sensitive: `Name` and `name` are different

Invalid variable names:
- Start with number: `123var` ❌
- Contain spaces: `user name` ❌
- Contain special characters: `user-name`, `user.name` ❌

## Undefined Variables

Variables not provided in the `vars` dict are left unchanged:

**Prompt**:
```markdown
Hello {{user_name}}, your {{undefined}} is ready.
```

**With** `vars={"user_name": "Bob"}`:
```markdown
Hello Bob, your {{undefined}} is ready.
```

This graceful degradation allows optional variables and helps identify missing values.

## Render Modes

### Full Mode

Variables are substituted in the final rendered output after all references are inlined:

```python
output = render_node_network(
    network,
    target_format="markdown",
    render_mode="full",
    vars={"user_name": "Alice"}
)
```

### File-First Mode

Variables are substituted in the root content while preserving file references:

```python
output = render_node_network(
    network,
    target_format="markdown",
    render_mode="file_first",
    vars={"user_name": "Alice"}
)
```

## Type Conversion

All variable values are converted to strings during substitution:

```python
vars = {
    "count": 42,         # Becomes "42"
    "active": True,      # Becomes "True"
    "price": 19.99,      # Becomes "19.99"
}
```

For type-aware substitution in structured formats, use Jinja2 files.

## Examples

See `examples/get_started/7-variable-insertion/` for complete working examples demonstrating all scoping methods.

## Best Practices

1. **Use meaningful names**: `user_name` > `un`, `task_type` > `tt`
2. **Apply appropriate scope**:
   - Simple scope for truly global values (user names, dates)
   - Node scope for node-specific formatting
   - Path scope for precise targeting in complex hierarchies
3. **Document expected variables**: List required variables in prompt comments
4. **Provide defaults**: Check for undefined variables or use Jinja2 defaults
5. **Validate before rendering**: Use `VariableSubstitutor.validate_variables()` to check variable names

## Integration with Versioning

Variables work seamlessly with versioned prompts:

```python
from promptic import load_prompt

# Load versioned prompt
content = load_prompt("prompts/task1/", version="v2.0.0")

# Render with variables
network = load_node_network("prompts/task1/")
output = render_node_network(
    network,
    target_format="markdown",
    vars={"user_name": "Alice"}
)
```

## Error Handling

Invalid variable names raise errors during validation:

```python
from promptic.context.variables import VariableSubstitutor

substitutor = VariableSubstitutor()

vars = {
    "123invalid": "value",  # Invalid: starts with number
    "user-name": "value"    # Invalid: contains dash
}

invalid_names = substitutor.validate_variables(vars)
# Returns: ["123invalid", "user-name"]
```

Check variables before rendering to catch errors early.
