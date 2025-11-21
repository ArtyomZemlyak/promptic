# Quickstart: Unified Context Node Architecture

## 1. Install & Configure

```bash
pip install -e .[dev]
```

The unified context node architecture extends the existing promptic library. No additional configuration is required for basic usage. For token counting, ensure `tiktoken` is installed:

```bash
pip install tiktoken
```

## 2. Create Multi-Format Context Nodes

Create nodes in different formats:

**YAML Node** (`blueprints/research.yaml`):
```yaml
name: Research Workflow
prompt_template: >
  You are a research assistant...
steps:
  - step_id: collect
    title: Collect Sources
    instruction_refs:
      - $ref: instructions/analyze.md
      - $ref: instructions/summarize.md
data_slots:
  - name: sources
    adapter_key: csv_loader
```

**Markdown Instruction** (`instructions/analyze.md`):
```markdown
# Analyze Source

Analyze the provided source material and extract key insights.

For detailed analysis steps, see [analysis guide](instructions/analysis_guide.md).

## Output Format

- Summary
- Key points
- References
```

**Jinja2 Template** (`templates/data.jinja2`):
```jinja2
Source: {{ source.title }}
URL: {{ source.url }}

{% if source.summary %}
Summary: {{ source.summary }}
{% endif %}

{% for tag in source.tags %}
- {{ tag }}
{% endfor %}
```

**JSON Memory** (`memory/format.json`):
```json
{
  "format": "hierarchical_markdown",
  "structure": {
    "entries": [
      {
        "timestamp": "{{ timestamp }}",
        "content": "{{ content }}",
        "references": [
          {
            "type": "reference",
            "path": "sources/{{ source_id }}.md"
          }
        ]
      }
    ]
  }
}
```

## 3. Load and Build Node Networks

```python
from promptic.sdk.nodes import load_node_network
from promptic.context.nodes.models import NetworkConfig
from pathlib import Path

# Load a node network from a root node
config = NetworkConfig(
    max_depth=10,
    max_node_size=10 * 1024 * 1024,  # 10MB
    max_network_size=1000,
    token_model="gpt-4"
)

network = load_node_network(
    root_path=Path("blueprints/research.yaml"),
    config=config
)

# Access nodes
root_node = network.root
all_nodes = network.nodes  # dict[str, ContextNode]

# Check network metrics
print(f"Network depth: {network.depth}")
print(f"Total size: {network.total_size} bytes")
print(f"Total tokens: {network.total_tokens}")
```

## 4. Render Node Networks

```python
from promptic.sdk.nodes import render_node_network

# Render to file-first format (compact with references)
compact = render_node_network(
    network,
    target_format="file_first"
)
print(compact)

# Render to JSON (for programmatic access)
json_output = render_node_network(
    network,
    target_format="json"
)

# Render to Markdown (for documentation)
markdown_output = render_node_network(
    network,
    target_format="markdown"
)
```

## 5. Work with Format Parsers

```python
from promptic.format_parsers.registry import get_default_registry
from promptic.format_parsers.yaml_parser import YAMLParser
from promptic.format_parsers.markdown_parser import MarkdownParser

# Access the registry
registry = get_default_registry()

# Register a custom parser (if needed)
# registry.register("custom_format", CustomParser(), [".custom"])

# Detect format from file
from pathlib import Path
file_path = Path("instructions/analyze.md")
content = file_path.read_text()

format_name = registry.detect_format(content, file_path)
print(f"Detected format: {format_name}")

# Get parser and parse
parser = registry.get_parser(format_name)
parsed = parser.parse(content, file_path)
json_content = parser.to_json(parsed)
```

## 6. Reference Resolution

```python
from promptic.resolvers.filesystem import FilesystemReferenceResolver
from pathlib import Path

# Create a resolver
resolver = FilesystemReferenceResolver()

# Resolve a reference
node = resolver.resolve("instructions/analyze.md", base_path=Path("blueprints"))

# Validate a reference
is_valid = resolver.validate("instructions/analyze.md", base_path=Path("blueprints"))
```

## 7. Token Counting

```python
from promptic.token_counting.tiktoken_counter import TiktokenTokenCounter

# Create token counter
counter = TiktokenTokenCounter()

# Count tokens for content
content = "This is some text to count tokens for."
token_count = counter.count_tokens(content, model="gpt-4")
print(f"Token count: {token_count}")

# Count tokens for a node
from promptic.sdk.nodes import render_node
rendered = render_node(network.root, "yaml")
token_count = counter.count_tokens_for_node(network.root, model="gpt-4")
```

## 8. Backward Compatibility

```python
from promptic.blueprints.adapters import LegacyBlueprintAdapter
from promptic.blueprints.models import ContextBlueprint
from promptic.sdk.nodes import load_node_network

# Load existing blueprint
blueprint = ContextBlueprint.load("blueprints/research.yaml")

# Convert to node network
adapter = LegacyBlueprintAdapter()
network = adapter.to_node_network(blueprint)

# Use unified node APIs
rendered = render_node_network(network, target_format="file_first")

# Convert back to blueprint (if possible)
blueprint_restored = adapter.from_node_network(network)
```

## 9. Error Handling

```python
from promptic.sdk.nodes import load_node_network
from promptic.context.nodes.models import NetworkConfig
from promptic.context.nodes.errors import (
    NodeNetworkValidationError,
    NodeResourceLimitExceededError,
    NodeReferenceNotFoundError
)

try:
    network = load_node_network(
        root_path=Path("blueprints/research.yaml"),
        config=NetworkConfig(max_depth=5)
    )
except NodeNetworkValidationError as e:
    if "circular_reference" in str(e):
        print(f"Cycle detected: {e.details.get('cycle_path')}")
    elif "depth_exceeded" in str(e):
        print(f"Depth limit exceeded: {e.details.get('max_depth')}")
except NodeResourceLimitExceededError as e:
    print(f"Resource limit exceeded: {e.limit_type}")
    print(f"Current: {e.current_value}, Max: {e.max_value}")
except NodeReferenceNotFoundError as e:
    print(f"Missing reference: {e.reference_path}")
    print(f"Suggestions: {e.suggestions}")
```

## 10. Advanced: Custom Format Parser

```python
from promptic.format_parsers.base import FormatParser
from pathlib import Path
from typing import Any

class CustomFormatParser(FormatParser):
    """Custom parser for a new format."""

    def detect(self, content: str, path: Path) -> bool:
        # Detect if content matches this format
        return path.suffix == ".custom" or "CUSTOM_FORMAT" in content

    def parse(self, content: str, path: Path) -> dict[str, Any]:
        # Parse content to structured format
        # Extract references using format-specific syntax
        return {
            "content": self._parse_custom_format(content),
            "references": self._extract_references(content)
        }

    def to_json(self, parsed: dict[str, Any]) -> dict[str, Any]:
        # Convert to canonical JSON
        return {
            "content": parsed["content"],
            "references": [
                {"path": ref, "type": "file"}
                for ref in parsed["references"]
            ]
        }

    def extract_references(self, parsed: dict[str, Any]) -> list[dict[str, Any]]:
        # Extract references from parsed content
        return parsed.get("references", [])

# Register custom parser
from promptic.format_parsers.registry import get_default_registry
registry = get_default_registry()
registry.register("custom", CustomFormatParser(), [".custom"])
```

## 11. Integration Example: tg-note

```python
from promptic.sdk.nodes import load_node_network, render_node_network
from promptic.context.nodes.models import NetworkConfig
from pathlib import Path

# Load node network for note creation
network = load_node_network(
    root_path=Path("config/prompts/note_creation.yaml"),
    config=NetworkConfig(token_model="gpt-4")
)

# Render compact prompt with file-first approach
compact_prompt = render_node_network(
    network,
    target_format="file_first"
)

# Pass to LLM agent
# Agent receives compact prompt with references
# Agent decides which instructions to read based on context
response = llm_agent.run(compact_prompt)
```

## Next Steps

- Read the [data model documentation](data-model.md) for detailed entity definitions
- Review the [API contracts](contracts/unified-context-node.yaml) for complete API reference
- Check the [research document](research.md) for design decisions and rationale
- Explore the [architecture documentation](../../docs_site/architecture/) for system design
