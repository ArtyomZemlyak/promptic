# Multi-Format Context Nodes

The unified context node architecture supports multiple file formats for authoring context nodes. All formats are automatically detected and converted to JSON internally for processing, enabling format-agnostic composition.

## Supported Formats

The system supports four primary formats:

- **YAML** (`.yaml`, `.yml`): Structured data with `$ref:` syntax for references
- **Markdown** (`.md`, `.markdown`): Text content with link syntax `[label](path)` for references
- **Jinja2** (`.jinja`, `.jinja2`): Templated content with variable substitution
- **JSON** (`.json`): Structured data with reference objects

## Format Detection

Format detection uses a two-step process:

1. **File Extension**: Primary signal for format detection
2. **Content Analysis**: Fallback for files without standard extensions

The `FormatParserRegistry` manages format detection and parser selection. Each parser implements the `FormatParser` interface with methods for detection, parsing, JSON conversion, and reference extraction.

## Format-Specific Reference Syntax

Each format uses native reference syntax that is converted to a canonical structured format during parsing:

### YAML References

```yaml
steps:
  - step_id: analyze
    instruction_refs:
      - $ref: instructions/analyze.md
      - $ref: instructions/summarize.yaml
```

The `$ref:` syntax is recognized by the YAML parser and converted to `NodeReference` objects.

### Markdown References

```markdown
# Analysis Guide

For detailed steps, see [analysis guide](instructions/analysis_guide.md).

See also [summary template](templates/summary.jinja2).
```

Link syntax `[label](path)` is recognized by the Markdown parser and converted to `NodeReference` objects with optional labels.

### JSON References

```json
{
  "steps": [
    {
      "step_id": "analyze",
      "instruction_refs": [
        {
          "type": "reference",
          "path": "instructions/analyze.md",
          "label": "Analysis Guide"
        }
      ]
    }
  ]
}
```

Structured reference objects are recognized by the JSON parser.

### Jinja2 References

Jinja2 templates can include references in comments or template variables:

```jinja2
{# Reference: instructions/analyze.md #}
Source: {{ source.title }}

{% include "templates/summary.jinja2" %}
```

The Jinja2 parser recognizes template includes and comment-based references.

## JSON as Canonical Format

All formats are converted to JSON internally for processing. This provides:

- **Uniform Processing**: Format-agnostic network building and validation
- **Consistent Structure**: All nodes have the same internal representation
- **Simplified Logic**: Core system doesn't need format-specific handling

The conversion preserves the original content structure while normalizing format-specific syntax.

## Example: Multi-Format Node Network

Create a network with nodes in different formats:

**Root Node** (`blueprints/research.yaml`):
```yaml
name: Research Workflow
prompt_template: >
  You are a research assistant...
steps:
  - step_id: collect
    title: Collect Sources
    instruction_refs:
      - $ref: instructions/analyze.md
      - $ref: data/sources.json
```

**Instruction Node** (`instructions/analyze.md`):
```markdown
# Analyze Source

Analyze the provided source material.

See [analysis guide](instructions/analysis_guide.md) for details.
```

**Data Node** (`data/sources.json`):
```json
{
  "sources": [
    {
      "title": "Example Source",
      "url": "https://example.com",
      "references": [
        {
          "type": "reference",
          "path": "memory/format.md"
        }
      ]
    }
  ]
}
```

**Memory Node** (`memory/format.md`):
```markdown
# Memory Format

Structured memory entries with references.
```

Load the network:

```python
from promptic.sdk.nodes import load_node_network
from pathlib import Path

network = load_node_network(Path("blueprints/research.yaml"))
```

All nodes are loaded regardless of format, and references are resolved across format boundaries.

## Format Parser Extension

New formats can be added by implementing the `FormatParser` interface:

```python
from promptic.format_parsers.base import FormatParser
from promptic.context.nodes.models import NodeReference
from pathlib import Path

class CustomParser(FormatParser):
    def detect(self, content: str, path: Path) -> bool:
        # Detect if content matches this format
        return path.suffix == ".custom"

    def parse(self, content: str, path: Path) -> dict[str, Any]:
        # Parse content to structured dict
        ...

    def to_json(self, parsed: dict[str, Any]) -> dict[str, Any]:
        # Convert to canonical JSON format
        ...

    def extract_references(self, parsed: dict[str, Any]) -> list[NodeReference]:
        # Extract references from format-specific syntax
        ...
```

Register the parser:

```python
from promptic.format_parsers.registry import get_default_registry

registry = get_default_registry()
registry.register("custom", CustomParser(), [".custom"])
```

## Best Practices

1. **Use Native Syntax**: Prefer format-specific reference syntax over generic formats
2. **Consistent Naming**: Use consistent file naming conventions across formats
3. **Format Selection**: Choose formats based on content type:
   - YAML for structured configuration
   - Markdown for text instructions
   - Jinja2 for templated content
   - JSON for data structures
4. **Reference Paths**: Use relative paths for portability
5. **Format Detection**: Include standard file extensions for reliable detection

## See Also

- [Recursive Node Networks](recursive-networks.md) - Building networks with references
- [Unified Node Architecture](../architecture/unified-context-node.md) - Architecture overview
- [Format Parser Extension](format-parser-extension.md) - Adding custom formats
