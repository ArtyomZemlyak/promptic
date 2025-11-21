# Recursive Node Networks

The unified context node architecture supports recursive node structures where any `ContextNode` can reference and contain other `ContextNode` instances, forming a network. This eliminates artificial separation between blueprints, instructions, data, and memory—all become nodes in a unified graph.

## Network Structure

A node network consists of:

- **Root Node**: Entry point for the network
- **Child Nodes**: Nodes referenced by the root or other nodes
- **References**: Links between nodes using `NodeReference` objects
- **Network Metadata**: Total size, token count, depth, and validation status

## Building Networks

Use `load_node_network()` to build a network from a root node:

```python
from promptic.sdk.nodes import load_node_network, NetworkConfig
from pathlib import Path

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
```

The `NodeNetworkBuilder` orchestrates:
1. Loading the root node
2. Resolving all references recursively
3. Validating network structure (cycles, depth, limits)
4. Building the complete network graph

## Reference Resolution

References are resolved using the `NodeReferenceResolver` interface. The default `FilesystemReferenceResolver` supports:

- **Relative Paths**: Resolved relative to the referencing node's directory
- **Absolute Paths**: Explicit paths from a configured root
- **Node IDs**: UUID-based references for in-memory nodes

Example with relative paths:

```yaml
# blueprints/research.yaml
name: Research Workflow
steps:
  - step_id: analyze
    instruction_refs:
      - $ref: ../instructions/analyze.md
      - $ref: ../data/sources.json
```

The resolver automatically resolves `../instructions/analyze.md` relative to the blueprint's directory.

## Recursive Composition

Nodes can reference other nodes at any depth:

**Root Node** (`blueprints/research.yaml`):
```yaml
name: Research Workflow
steps:
  - step_id: analyze
    instruction_refs:
      - $ref: instructions/analyze.md
```

**Instruction Node** (`instructions/analyze.md`):
```markdown
# Analyze Source

See [data guide](data/guide.md) for data structure details.

Reference [memory format](memory/format.md) for memory structure.
```

**Data Guide** (`data/guide.md`):
```markdown
# Data Guide

Data structure documentation.

See [examples](data/examples.json) for examples.
```

The system loads the entire network recursively, resolving all references and building the complete graph.

## Cycle Detection

The network builder detects circular references using a depth-first search (DFS) algorithm:

```python
# Cycle: A → B → C → A
# Raises NodeNetworkValidationError with cycle path details
```

Example error:

```
NodeNetworkValidationError: Circular reference detected:
blueprints/research.yaml → instructions/analyze.md → data/guide.md → blueprints/research.yaml
```

## Depth Limiting

Depth limits prevent stack overflow from extremely deep but valid trees:

```python
config = NetworkConfig(max_depth=10)  # Default limit
```

If depth exceeds the limit, `NodeNetworkDepthExceededError` is raised with the current depth and limit.

## Resource Limits

Network building enforces configurable resource limits:

- **Node Size**: Maximum size per node (default 10MB)
- **Network Size**: Maximum number of nodes (default 1000)
- **Token Limits**: Per-node and per-network token limits (configurable)

Example with token limits:

```python
config = NetworkConfig(
    max_tokens_per_node=10000,
    max_tokens_per_network=100000,
    token_model="gpt-4"
)
```

Token counting uses tiktoken with configurable model specification. Counting is performed on final rendered content to accurately reflect LLM context usage.

## Network Validation

The network builder validates:

1. **Reference Resolution**: All references must resolve to existing nodes
2. **Cycle Detection**: No circular references allowed
3. **Depth Limits**: Depth within configured limit
4. **Resource Limits**: Size and token limits not exceeded

Validation errors raise domain-specific exceptions:
- `NodeReferenceNotFoundError`: Missing reference
- `NodeNetworkValidationError`: Cycle detected
- `NodeNetworkDepthExceededError`: Depth limit exceeded
- `NodeResourceLimitExceededError`: Resource limit exceeded

## Network Rendering

Render networks to different formats:

```python
from promptic.sdk.nodes import render_node_network

# Render to YAML
yaml_output = render_node_network(network, "yaml")

# Render to Markdown
markdown_output = render_node_network(network, "markdown")

# Render to file-first format
file_first_output = render_node_network(network, "file_first")
```

The `file_first` format provides a compact representation with references:

```markdown
# blueprints/research.yaml

name: Research Workflow
steps:
  - step_id: analyze
    instruction_refs:
      - $ref: instructions/analyze.md

## References

- [Analysis Guide](instructions/analyze.md)
- [Data Guide](data/guide.md)
```

## Network Traversal

Access network structure programmatically:

```python
# Root node
root = network.root

# All nodes by ID
all_nodes = network.nodes

# Network metadata
total_size = network.total_size
total_tokens = network.total_tokens
depth = network.depth

# Traverse children
for child in root.children:
    print(f"Child: {child.id}")
    for grandchild in child.children:
        print(f"  Grandchild: {grandchild.id}")
```

## Best Practices

1. **Shallow Hierarchies**: Prefer shallow networks (2-3 levels) for readability
2. **Explicit References**: Use clear, descriptive reference paths
3. **Relative Paths**: Use relative paths for portability
4. **Resource Awareness**: Monitor network size and token usage
5. **Validation**: Validate networks before production use
6. **Documentation**: Document network structure and dependencies

## Example: Multi-Level Network

Create a 3-level network:

**Level 1** (`blueprints/research.yaml`):
```yaml
name: Research Workflow
steps:
  - step_id: analyze
    instruction_refs:
      - $ref: instructions/analyze.md
```

**Level 2** (`instructions/analyze.md`):
```markdown
# Analyze Source

See [data guide](data/guide.md) for data structure.
```

**Level 3** (`data/guide.md`):
```markdown
# Data Guide

Data structure documentation.
```

Load and validate:

```python
network = load_node_network(Path("blueprints/research.yaml"))
assert network.depth == 3
assert len(network.nodes) == 3
```

## See Also

- [Multi-Format Nodes](multi-format-nodes.md) - Format support
- [Unified Node Architecture](../architecture/unified-context-node.md) - Architecture overview
- [Format Parser Extension](format-parser-extension.md) - Custom formats
