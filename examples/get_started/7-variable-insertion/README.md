# Example 7: Variable Insertion with Hierarchical Scope

This example demonstrates variable insertion functionality with all three scoping levels:
- **Simple scope**: Variables applied globally to all nodes
- **Node scope**: Variables targeted to specific nodes by name  
- **Path scope**: Variables targeted to specific positions in hierarchy

## Structure

```
7-variable-insertion/
├── root.md                    # Root prompt with simple variables
├── group/
│   └── instructions.md        # Instructions with node-scoped variables
└── templates/
    └── details.md             # Details with path-scoped variables
```

## Variables Used

### Simple Scope (Global)
- `{{user_name}}` - User's name, appears in all files
- `{{task_type}}` - Type of task, appears in all files

### Node Scope
- `{{instructions.format}}` - Format for instructions node only
- `{{details.level}}` - Detail level for details node only

### Path Scope
- `{{root.group.instructions.style}}` - Style for instructions at specific path
- `{{root.templates.details.verbosity}}` - Verbosity for details at specific path

## Running the Example

```bash
python render.py
```

## Expected Output

The render script demonstrates three scenarios:

1. **Simple variables only**: Basic substitution in all nodes
2. **Node-scoped variables**: Different values for nodes with same name
3. **Path-scoped variables**: Maximum precision targeting

## Key Concepts

- Variables use `{{var_name}}` syntax in Markdown/YAML/JSON files
- Jinja2 files use native `{{ var_name }}` syntax
- Scope precedence: path > node > simple (most specific wins)
- Undefined variables are left unchanged (graceful degradation)
- All occurrences of a variable are replaced within its scope
