# Data Model: Unified Context Node Architecture

All models will be implemented as `pydantic.BaseModel` subclasses (domain layer) to guarantee validation, serialization, and compatibility with `pydantic-settings`.

## ContextNode

Unified domain entity representing any context element (blueprint, instruction, data, memory). Contains format-agnostic content (stored as JSON), metadata (format, semantic_type, optional version field reserved for future use), and references to other nodes. Supports recursive composition where nodes can contain or reference other nodes.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `id` | `str \| UUID` | Node identifier (file path for filesystem nodes, UUID for in-memory nodes) | Required; immutable after creation |
| `content` | `dict[str, Any]` | Format-agnostic content stored as JSON | Required; validated during parsing |
| `format` | `Literal["yaml", "jinja2", "markdown", "json"]` | Source format of the node | Required; detected during parsing |
| `semantic_type` | `Optional[Literal["blueprint", "instruction", "data", "memory"]]` | Optional semantic label | Optional; metadata only, doesn't affect structure |
| `version` | `Optional[str]` | Version field reserved for future use | Optional; not enforced in current implementation |
| `references` | `list[NodeReference]` | References to other nodes | Optional; validated during network building |
| `children` | `list[ContextNode]` | Child nodes (for recursive composition) | Optional; loaded lazily during network building |
| `metadata` | `dict[str, Any]` | Additional metadata (tags, owner, etc.) | Optional |

**Relationships**:
- Can reference many `ContextNode` instances via `references` field
- Can contain many `ContextNode` instances via `children` field (recursive composition)
- Identity: filesystem nodes identified by file path (e.g., `instructions/think.md`); in-memory nodes use generated UUIDs

**Validation Rules**:
- `id` must be unique within a network
- `references` must resolve to existing nodes during network building
- `content` must be valid JSON (enforced during format parsing)
- Resource limits apply: max node size (default 10MB), max tokens per node (configurable)

## NodeReference

Structured reference to another node, converted from format-specific syntax during parsing.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `path` | `str` | Reference path (file path or node ID) | Required; validated during resolution |
| `type` | `Literal["file", "id", "uri"]` | Reference type | Required; determines resolution strategy |
| `label` | `Optional[str]` | Optional label for display | Optional |

**Relationships**: References a `ContextNode` by path or ID

**Validation Rules**:
- `path` must resolve to existing node during network building
- `type` determines resolution strategy (filesystem, in-memory, URI)

## FormatParser (Interface)

Interface for format-specific parsing. Each parser implements detection, parsing, and JSON conversion.

**Methods**:
- `detect(content: str, path: Path) -> bool`: Identifies if content matches this format
- `parse(content: str, path: Path) -> dict[str, Any]`: Extracts structured content from format
- `to_json(parsed: dict[str, Any]) -> dict[str, Any]`: Converts parsed content to canonical JSON representation
- `extract_references(parsed: dict[str, Any]) -> list[NodeReference]`: Extracts references from format-specific syntax

**Implementations**:
- `YAMLParser`: Parses YAML files, recognizes `$ref:` syntax
- `MarkdownParser`: Parses Markdown files, recognizes link syntax `[label](path)`
- `Jinja2Parser`: Parses Jinja2 templates, recognizes template variables and comments
- `JSONParser`: Parses JSON files, recognizes structured reference objects

## FormatParserRegistry

Service that manages format parser registration and selection.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `parsers` | `dict[str, FormatParser]` | Registered parsers by format name | Required; populated during initialization |
| `extensions` | `dict[str, str]` | File extension to format name mapping | Required; populated during initialization |

**Methods**:
- `register(format_name: str, parser: FormatParser, extensions: list[str])`: Register a parser for a format
- `detect_format(content: str, path: Path) -> str`: Detect format from content and path
- `get_parser(format_name: str) -> FormatParser`: Get parser for a format

## NodeNetworkBuilder

Use case that orchestrates loading multiple nodes, resolving references, and constructing the network graph.

**Dependencies**:
- `NodeReferenceResolver`: Interface for reference resolution strategies
- `TokenCounter`: Interface for token counting
- `FormatParserRegistry`: Registry for format parsers

**Methods**:
- `build_network(root_path: Path, config: NetworkConfig) -> NodeNetwork`: Load nodes, resolve references, build network
- `validate_network(network: NodeNetwork) -> ValidationResult`: Validate network structure (cycles, depth, limits)

**Validation**:
- Detects circular references using DFS algorithm
- Enforces depth limits (default 10 levels)
- Enforces resource limits (node size, network size, token limits)
- Validates all references resolve to existing nodes

## NodeReferenceResolver (Interface)

Interface for pluggable reference resolution strategies.

**Methods**:
- `resolve(path: str, base_path: Path) -> ContextNode`: Resolve a reference path to a node
- `validate(path: str, base_path: Path) -> bool`: Validate that a reference path is valid

**Implementations**:
- `FilesystemReferenceResolver`: Resolves file paths relative to base directory

## TokenCounter (Interface)

Interface for token counting with tiktoken-based implementation.

**Methods**:
- `count_tokens(content: str, model: str) -> int`: Count tokens in content for a specific model
- `count_tokens_for_node(node: ContextNode, model: str) -> int`: Count tokens for a node's rendered content

**Implementation**:
- `TiktokenTokenCounter`: Uses tiktoken library with configurable model specification

## NodeNetwork

Container for a complete node network with validation and resource tracking.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `root` | `ContextNode` | Root node of the network | Required |
| `nodes` | `dict[str, ContextNode]` | All nodes in the network by ID | Required; populated during building |
| `total_size` | `int` | Total size of all nodes in bytes | Calculated during building |
| `total_tokens` | `int` | Total tokens for all nodes (for specified model) | Calculated during building |
| `depth` | `int` | Maximum depth of the network | Calculated during building |

**Validation Rules**:
- No circular references (validated during building)
- Depth within configured limit (default 10 levels)
- Total size within configured limit (default 1000 nodes)
- Total tokens within configured limit (configurable per model)

## NetworkConfig

Configuration for network building operations.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `max_depth` | `int` | Maximum depth limit | Default 10; configurable |
| `max_node_size` | `int` | Maximum size per node in bytes | Default 10MB; configurable |
| `max_network_size` | `int` | Maximum number of nodes | Default 1000; configurable |
| `max_tokens_per_node` | `Optional[int]` | Maximum tokens per node | Optional; configurable |
| `max_tokens_per_network` | `Optional[int]` | Maximum tokens for entire network | Optional; configurable |
| `token_model` | `str` | Model for token counting | Default "gpt-4"; configurable |

## LegacyBlueprintAdapter

Adapter that converts existing `ContextBlueprint` models to `ContextNode` networks for backward compatibility.

**Methods**:
- `to_node_network(blueprint: ContextBlueprint) -> NodeNetwork`: Convert blueprint to node network
- `from_node_network(network: NodeNetwork) -> ContextBlueprint`: Convert node network to blueprint (if possible)

**Mapping Strategy**:
- Blueprint structure (steps, instructions, data slots) mapped to node network with appropriate references
- Instruction references mapped to node references
- Data/memory slots preserved as metadata or separate nodes

## LegacyInstructionAdapter

Adapter that converts existing `InstructionNode` models to `ContextNode` instances for backward compatibility.

**Methods**:
- `to_node(instruction: InstructionNode) -> ContextNode`: Convert instruction to node
- `from_node(node: ContextNode) -> InstructionNode`: Convert node to instruction (if possible)

**Mapping Strategy**:
- Instruction metadata and content preserved in node structure
- Format and source URI preserved
- Fallback policies and placeholders preserved as metadata
