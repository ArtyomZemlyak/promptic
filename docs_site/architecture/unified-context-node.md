# Unified Context Node Architecture

The unified context node architecture abstracts away semantic distinctions between blueprints, instructions, data, and memory. All context elements become recursive `ContextNode` structures that can contain content in multiple formats and reference other nodes, forming a network.

## Architecture Overview

The architecture follows clean architecture principles with three main layers:

### Domain Layer (Entities)

- **`ContextNode`**: Unified domain entity representing any context element
- **`NodeReference`**: Structured reference to another node
- **`NodeNetwork`**: Container for a complete node network
- **`NetworkConfig`**: Configuration for network building operations

### Application Layer (Use Cases)

- **`NodeNetworkBuilder`**: Orchestrates loading, reference resolution, and network construction
- **`FormatParserRegistry`**: Manages format parser registration and selection

### Infrastructure Layer (Adapters)

- **Format Parsers**: `YAMLParser`, `MarkdownParser`, `Jinja2Parser`, `JSONParser`
- **Reference Resolvers**: `FilesystemReferenceResolver`
- **Token Counters**: `TiktokenTokenCounter`

## Key Design Principles

### Format Agnostic

All formats (YAML, Markdown, Jinja2, JSON) are converted to JSON internally for processing. This provides:

- Uniform processing regardless of source format
- Consistent internal representation
- Simplified core logic

### Recursive Composition

Any node can reference and contain other nodes, forming a network:

```
Root Node (YAML)
  ├── Instruction Node (Markdown)
  │     └── Data Node (JSON)
  ├── Data Node (JSON)
  └── Memory Node (YAML)
```

### Semantic Abstraction

The system abstracts away semantic distinctions:

- **Blueprints**: Nodes with `semantic_type="blueprint"` (optional metadata)
- **Instructions**: Nodes with `semantic_type="instruction"` (optional metadata)
- **Data**: Nodes with `semantic_type="data"` (optional metadata)
- **Memory**: Nodes with `semantic_type="memory"` (optional metadata)

Semantic types are optional metadata and don't affect structure or processing.

## Core Components

### ContextNode

Unified domain entity with:

- `id`: Node identifier (file path or UUID)
- `content`: Format-agnostic content stored as JSON
- `format`: Source format (yaml, markdown, jinja2, json)
- `semantic_type`: Optional semantic label (blueprint, instruction, data, memory)
- `references`: List of `NodeReference` objects
- `children`: List of child `ContextNode` instances (lazy loaded)
- `metadata`: Additional metadata (tags, owner, etc.)

### FormatParser Interface

Interface for format-specific parsing:

```python
class FormatParser:
    def detect(content: str, path: Path) -> bool
    def parse(content: str, path: Path) -> dict[str, Any]
    def to_json(parsed: dict[str, Any]) -> dict[str, Any]
    def extract_references(parsed: dict[str, Any]) -> list[NodeReference]
```

### NodeNetworkBuilder

Orchestrates network building:

1. Loads root node using format detection
2. Resolves all references recursively
3. Validates network structure (cycles, depth, limits)
4. Builds complete network graph

### Reference Resolution

Pluggable reference resolution via `NodeReferenceResolver` interface:

- `FilesystemReferenceResolver`: Resolves file paths (default)
- Supports relative and absolute paths
- Extensible for URI-based or in-memory resolution

### Token Counting

Model-specific token counting via `TokenCounter` interface:

- `TiktokenTokenCounter`: Uses tiktoken library
- Configurable model specification (gpt-4, gpt-3.5-turbo, etc.)
- Counting performed on final rendered content

## Network Building Flow

```
1. Load Root Node
   ├── Detect format (extension + content analysis)
   ├── Parse content (format-specific parser)
   ├── Convert to JSON (canonical format)
   └── Extract references (format-specific syntax)

2. Resolve References
   ├── For each reference:
   │   ├── Resolve path (relative/absolute)
   │   ├── Load referenced node (recursive)
   │   └── Add to network
   └── Continue until all references resolved

3. Validate Network
   ├── Check for cycles (DFS algorithm)
   ├── Verify depth limits
   ├── Check resource limits (size, tokens)
   └── Validate all references resolve

4. Build Network Graph
   ├── Create NodeNetwork container
   ├── Calculate metadata (size, tokens, depth)
   └── Return complete network
```

## Validation & Error Handling

The system provides domain-specific error types:

- `FormatDetectionError`: Format cannot be detected
- `FormatParseError`: Parsing fails
- `NodeReferenceNotFoundError`: Reference cannot be resolved
- `NodeNetworkValidationError`: Cycle detected
- `NodeNetworkDepthExceededError`: Depth limit exceeded
- `NodeResourceLimitExceededError`: Resource limit exceeded

All errors include actionable messages with context for debugging.

## Resource Management

Configurable resource limits:

- **Node Size**: Maximum size per node (default 10MB)
- **Network Size**: Maximum number of nodes (default 1000)
- **Depth Limit**: Maximum depth (default 10 levels)
- **Token Limits**: Per-node and per-network limits (configurable)

Limits are enforced during network building and raise `NodeResourceLimitExceededError` when exceeded.

## Extension Points

### Custom Format Parsers

Implement `FormatParser` interface and register:

```python
registry.register("custom", CustomParser(), [".custom"])
```

### Custom Reference Resolvers

Implement `NodeReferenceResolver` interface for custom resolution strategies (URIs, databases, etc.).

### Custom Token Counters

Implement `TokenCounter` interface for custom counting strategies.

## Migration from Legacy Architecture

The unified architecture replaces:

- `ContextBlueprint` → `NodeNetwork` (root node)
- `InstructionNode` → `ContextNode` (with `semantic_type="instruction"`)
- Separate blueprint/instruction models → Unified `ContextNode`

Migration path:

1. Load existing blueprints as node networks
2. Convert instruction files to nodes
3. Update code to use `NodeNetwork` and `ContextNode`
4. Remove legacy models and adapters

## Benefits

1. **Flexibility**: Mix formats and semantic types freely
2. **Composition**: Recursive networks enable complex structures
3. **Consistency**: Uniform processing regardless of format
4. **Extensibility**: Pluggable parsers, resolvers, and counters
5. **Simplicity**: Single node model instead of multiple specialized models

## See Also

- [Multi-Format Nodes](../context-engineering/multi-format-nodes.md) - Format support
- [Recursive Networks](../context-engineering/recursive-networks.md) - Network building
- [Format Parser Extension](../context-engineering/format-parser-extension.md) - Custom formats
