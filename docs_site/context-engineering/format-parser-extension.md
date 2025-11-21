# Format Parser Extension Guide

The unified context node architecture supports custom format parsers through the `FormatParser` interface. This guide explains how to implement and register custom parsers.

## FormatParser Interface

All format parsers must implement the `FormatParser` interface:

```python
from promptic.format_parsers.base import FormatParser
from promptic.context.nodes.models import NodeReference
from pathlib import Path
from typing import Any

class CustomParser(FormatParser):
    def detect(self, content: str, path: Path) -> bool:
        """Detect if content matches this format.

        Args:
            content: File content as string
            path: File path

        Returns:
            True if content matches this format
        """
        ...

    def parse(self, content: str, path: Path) -> dict[str, Any]:
        """Parse content to structured dict.

        Args:
            content: File content as string
            path: File path

        Returns:
            Structured dict representation
        """
        ...

    def to_json(self, parsed: dict[str, Any]) -> dict[str, Any]:
        """Convert parsed content to canonical JSON format.

        Args:
            parsed: Parsed content from parse()

        Returns:
            JSON-compatible dict
        """
        ...

    def extract_references(self, parsed: dict[str, Any]) -> list[NodeReference]:
        """Extract references from format-specific syntax.

        Args:
            parsed: Parsed content from parse()

        Returns:
            List of NodeReference objects
        """
        ...
```

## Implementation Example

Example: TOML parser:

```python
from promptic.format_parsers.base import FormatParser
from promptic.context.nodes.models import NodeReference
from pathlib import Path
from typing import Any
import tomllib  # Python 3.11+

class TOMLParser(FormatParser):
    """Parser for TOML format files."""

    def detect(self, content: str, path: Path) -> bool:
        """Detect TOML format by extension."""
        return path.suffix in {".toml", ".tml"}

    def parse(self, content: str, path: Path) -> dict[str, Any]:
        """Parse TOML content."""
        try:
            return tomllib.loads(content)
        except Exception as e:
            raise FormatParseError(f"Failed to parse TOML: {e}")

    def to_json(self, parsed: dict[str, Any]) -> dict[str, Any]:
        """Convert TOML to JSON (already JSON-compatible)."""
        return parsed

    def extract_references(self, parsed: dict[str, Any]) -> list[NodeReference]:
        """Extract references from TOML structure.

        TOML references use inline table syntax:
        [references]
        instruction = { path = "instructions/analyze.md", label = "Analysis" }
        """
        references = []

        # Check for references section
        if "references" in parsed:
            refs_section = parsed["references"]
            if isinstance(refs_section, dict):
                for key, value in refs_section.items():
                    if isinstance(value, dict) and "path" in value:
                        references.append(
                            NodeReference(
                                path=value["path"],
                                type="file",
                                label=value.get("label")
                            )
                        )

        return references
```

## Reference Syntax

Each parser must recognize format-specific reference syntax and convert to `NodeReference` objects:

### YAML Syntax

```yaml
steps:
  - $ref: instructions/analyze.md
```

### Markdown Syntax

```markdown
See [analysis guide](instructions/analyze.md)
```

### JSON Syntax

```json
{
  "references": [
    {
      "type": "reference",
      "path": "instructions/analyze.md",
      "label": "Analysis Guide"
    }
  ]
}
```

### Custom Syntax

Define your own reference syntax. For example, TOML:

```toml
[references]
instruction = { path = "instructions/analyze.md", label = "Analysis" }
```

## Registration

Register your parser with the default registry:

```python
from promptic.format_parsers.registry import get_default_registry

registry = get_default_registry()
registry.register("toml", TOMLParser(), [".toml", ".tml"])
```

Or create a custom registry:

```python
from promptic.format_parsers.registry import FormatParserRegistry

registry = FormatParserRegistry()
registry.register("toml", TOMLParser(), [".toml", ".tml"])
```

## Format Detection Strategy

Format detection uses a two-step process:

1. **File Extension**: Primary signal (fast, reliable)
2. **Content Analysis**: Fallback for files without standard extensions

Your `detect()` method should handle both:

```python
def detect(self, content: str, path: Path) -> bool:
    # Primary: Check extension
    if path.suffix in {".toml", ".tml"}:
        return True

    # Fallback: Content analysis
    try:
        # Try parsing a sample
        tomllib.loads(content[:1000])  # Sample first 1KB
        return True
    except:
        return False
```

## JSON Conversion

The `to_json()` method must convert format-specific structures to JSON-compatible dicts:

- Preserve structure and semantics
- Normalize format-specific syntax
- Ensure JSON serializability

Example for TOML (already JSON-compatible):

```python
def to_json(self, parsed: dict[str, Any]) -> dict[str, Any]:
    # TOML is already JSON-compatible
    return parsed
```

Example for custom format with special types:

```python
def to_json(self, parsed: dict[str, Any]) -> dict[str, Any]:
    # Convert custom types to JSON-compatible types
    result = {}
    for key, value in parsed.items():
        if isinstance(value, CustomType):
            result[key] = value.to_dict()
        else:
            result[key] = value
    return result
```

## Error Handling

Raise appropriate errors:

- `FormatDetectionError`: Format cannot be detected
- `FormatParseError`: Parsing fails

```python
from promptic.context.nodes.errors import FormatParseError

def parse(self, content: str, path: Path) -> dict[str, Any]:
    try:
        return parse_custom_format(content)
    except ParseError as e:
        raise FormatParseError(f"Failed to parse {path}: {e}")
```

## Testing

Write tests for your parser:

```python
def test_toml_parser_detection():
    parser = TOMLParser()
    assert parser.detect("", Path("test.toml"))
    assert not parser.detect("", Path("test.yaml"))

def test_toml_parser_parsing():
    parser = TOMLParser()
    content = """
    [config]
    name = "test"
    """
    parsed = parser.parse(content, Path("test.toml"))
    assert parsed["config"]["name"] == "test"

def test_toml_parser_references():
    parser = TOMLParser()
    content = """
    [references]
    instruction = { path = "instructions/analyze.md", label = "Analysis" }
    """
    parsed = parser.parse(content, Path("test.toml"))
    references = parser.extract_references(parsed)
    assert len(references) == 1
    assert references[0].path == "instructions/analyze.md"
```

## Best Practices

1. **Clear Detection**: Make `detect()` fast and reliable
2. **Robust Parsing**: Handle edge cases and malformed content
3. **Consistent JSON**: Ensure `to_json()` produces consistent structure
4. **Reference Extraction**: Support format-native reference syntax
5. **Error Messages**: Provide actionable error messages
6. **Testing**: Write comprehensive tests for all methods

## Integration

Once registered, your parser is automatically used:

```python
from promptic.sdk.nodes import load_node

# Your parser is used automatically
node = load_node("config.toml")
```

## See Also

- [Multi-Format Nodes](multi-format-nodes.md) - Format support overview
- [Recursive Networks](recursive-networks.md) - Network building
- [Unified Node Architecture](../architecture/unified-context-node.md) - Architecture overview
