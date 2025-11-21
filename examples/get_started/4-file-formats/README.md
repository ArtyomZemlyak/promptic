# File Formats Example

This example demonstrates how to work with multiple file formats (YAML, JSON, Jinja2, Markdown) and render them to different target formats.

## Files

- `root.yaml` - Root file in YAML format (references file.json)
- `file.json` - JSON file (references file.jinja2)
- `file.jinja2` - Jinja2 template file (references file.md)
- `file.md` - Markdown file (final file in the chain)
- `render.py` - Python script that renders to all target formats

## File Reference Chain

```
root.yaml (YAML)
  └─ $ref: file.json
      └─ $ref: file.jinja2
          └─ {# ref: file.md #}
```

## Supported Formats

### Input Formats (can be loaded)
- **YAML** - uses `$ref: path` syntax
- **JSON** - uses `{"$ref": "path"}` syntax
- **Jinja2** - uses `{# ref: path #}` syntax (for references)
- **Markdown** - uses `[label](path)` syntax

### Output/Target Formats (can be rendered to)
- **YAML** - renders structure in YAML format
- **JSON** - renders structure in JSON format
- **Markdown** - renders based on root node format wrapped in code blocks

## Running the Example

```bash
cd examples/get_started/4-file-formats
python render.py
```

## What This Shows

### 1. Format Detection and Loading
- Automatically detects file format from extension
- Loads and parses each format correctly
- Extracts references from each format

### 2. Reference Resolution
- References are resolved recursively
- Each file can reference files in different formats
- Full network is built from root to all dependencies

### 3. Rendering Logic

#### YAML Target Format
- Root and all references rendered as YAML structure
- JSON files converted to YAML format
- Text files (markdown/jinja2) inserted as strings
- All references recursively resolved

#### JSON Target Format
- Root and all references rendered as JSON structure
- YAML files converted to JSON format
- Text files inserted as strings
- All references recursively resolved

#### Markdown Target Format
- **If root is YAML**: entire structure rendered as YAML, wrapped in ````yaml` code block
- **If root is JSON**: entire structure rendered as JSON, wrapped in ````json` code block
- **If root is Markdown**: text processed with references replaced:
  - YAML files inserted as ````yaml` code blocks
  - JSON files inserted as ````json` code blocks
  - Other markdown files inserted inline
- Recursive: references within references are fully resolved

## Output

The script renders `root.yaml` to all target formats:

1. **YAML output** - Complete structure in YAML format
2. **Markdown output** - Complete structure wrapped in ````yaml` code block (since root is YAML)
3. **JSON output** - Complete structure in JSON format

Each output shows all referenced files fully inlined with proper format conversion.

## Key Concepts

### Recursive Format Conversion
When rendering, formats are converted based on the parent node:
- YAML parent → JSON children converted to YAML
- JSON parent → YAML children converted to JSON
- Text files always inserted as strings

### Markdown Code Blocks
For markdown rendering:
- Structured formats (YAML/JSON) are wrapped in appropriate code blocks (````yaml` or ````json`)
- The code block type is determined by the file's native format
- This makes the output readable and properly syntax-highlighted

### Jinja2 Support
- Jinja2 is supported as an **input format only**
- Jinja2 files can be loaded and their references extracted
- When rendered, Jinja2 content is treated as text (like markdown)
- Jinja2 is NOT a target format (you cannot render TO jinja2)
