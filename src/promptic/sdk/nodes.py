"""SDK functions for loading and rendering context nodes."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Literal, Optional

from promptic.context.nodes.errors import FormatDetectionError, FormatParseError
from promptic.context.nodes.models import ContextNode, NetworkConfig, NodeNetwork
from promptic.context.variables import SubstitutionContext, VariableSubstitutor
from promptic.format_parsers.registry import get_default_registry
from promptic.pipeline.network.builder import NodeNetworkBuilder
from promptic.rendering import ReferenceInliner
from promptic.versioning import VersionSpec


def load_node(path: Path | str) -> ContextNode:
    """Load a single node from file path using format detection and parser registry.

    This function performs format detection, parsing, and JSON conversion to create
    a ContextNode instance. The node's references are extracted but not resolved
    (use load_node_network() for recursive loading with reference resolution).

    Side Effects:
        - Reads file from filesystem
        - Uses format parser registry (may trigger parser initialization)
        - No state mutation (pure function except for I/O)

    Args:
        path: File path to load node from (relative or absolute)

    Returns:
        ContextNode instance with parsed content, format, and extracted references.
        The node's children field is empty (not loaded).

    Raises:
        FormatDetectionError: If format cannot be detected from extension or content
        FormatParseError: If parsing fails (malformed content, syntax errors)
        FileNotFoundError: If file does not exist at the specified path

    Example:
        >>> node = load_node("instructions/analyze.md")
        >>> print(node.format)
        'markdown'
        >>> print(len(node.references))
        2
    """
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Node file not found: {path_obj}")

    # Read file content
    content = path_obj.read_text(encoding="utf-8")

    # Detect format and get parser
    registry = get_default_registry()
    try:
        format_name = registry.detect_format(content, path_obj)
    except FormatDetectionError:
        # Try to infer from extension as fallback
        ext = path_obj.suffix.lower()
        if ext in {".yaml", ".yml"}:
            format_name = "yaml"
        elif ext in {".md", ".markdown"}:
            format_name = "markdown"
        elif ext in {".jinja", ".jinja2"}:
            format_name = "jinja2"
        elif ext == ".json":
            format_name = "json"
        else:
            raise FormatDetectionError(f"Could not detect format for {path_obj}")

    parser = registry.get_parser(format_name)

    # Parse content
    parsed = parser.parse(content, path_obj)
    json_content = parser.to_json(parsed)
    references = parser.extract_references(parsed)

    # Create ContextNode
    node = ContextNode(
        id=str(path_obj),
        content=json_content,
        format=format_name,
        references=references,
    )

    return node


def render_node(
    node: ContextNode, target_format: Literal["yaml", "markdown", "json", "jinja2"]
) -> str:
    """Render a single ContextNode to target format.

    Converts the node's JSON content to the specified target format. The rendering
    preserves the content structure while adapting to format-specific conventions.

    Side Effects:
        - No state mutation (pure function)
        - May import format-specific libraries (yaml, json) on first use

    Args:
        node: ContextNode to render (must have valid content)
        target_format: Target format to render to (yaml, markdown, json, jinja2)

    Returns:
        Rendered content as string in the specified format. For markdown and jinja2,
        attempts to preserve original structure if available in content.

    Raises:
        ValueError: If target format is not supported
        KeyError: If content structure doesn't match expected format (for markdown)

    Example:
        >>> node = load_node("instructions/analyze.md")
        >>> yaml_output = render_node(node, "yaml")
        >>> markdown_output = render_node(node, "markdown")
        >>> jinja2_output = render_node(node, "jinja2")
    """
    if target_format == "json":
        import json

        return json.dumps(node.content, indent=2)

    elif target_format == "yaml":
        import yaml

        return yaml.dump(node.content, default_flow_style=False, sort_keys=False)

    elif target_format == "markdown" or target_format == "jinja2":
        # Convert JSON content to Markdown
        content = node.content
        # AICODE-NOTE: For markdown nodes, always prefer raw_content if available
        #              to preserve original formatting and structure
        if "raw_content" in content:
            return str(content["raw_content"])
        elif "paragraphs" in content:
            paragraphs = content["paragraphs"]
            if isinstance(paragraphs, list):
                return "\n\n".join(str(p) for p in paragraphs)
            return str(paragraphs)
        else:
            # Fallback: convert dict to Markdown
            def process_dict_to_markdown(d: dict[str, Any]) -> list[str]:
                """Recursively process dict and extract all string values."""
                lines = []
                for key, value in d.items():
                    if isinstance(value, str):
                        # If value is a string (likely markdown content from processed $ref), embed it directly
                        lines.append(value)
                    elif isinstance(value, dict):
                        # Recursively process nested dicts
                        nested_lines = process_dict_to_markdown(value)
                        lines.extend(nested_lines)
                    elif isinstance(value, list):
                        # Process list items
                        for item in value:
                            if isinstance(item, str):
                                lines.append(item)
                            elif isinstance(item, dict):
                                lines.extend(process_dict_to_markdown(item))
                            else:
                                lines.append(str(item))
                    elif value is None:
                        # Skip None values
                        continue
                else:
                    lines.append(f"**{key}**: {value}")
                return lines

            lines = process_dict_to_markdown(content)
            return "\n\n".join(lines) if lines else ""

    else:
        raise ValueError(f"Unsupported target format: {target_format}")


def load_node_network(
    root_path: Path | str,
    config: NetworkConfig | None = None,
    version: Optional[VersionSpec] = None,
) -> NodeNetwork:
    """Build a node network from a root path with recursive reference resolution.

    This function loads the root node and recursively resolves all references to
    build a complete network. It performs validation including cycle detection,
    depth limiting, and resource limit enforcement.

    # AICODE-NOTE: Token counting removed - not used in examples 003-006.
    # Network metadata now tracks only size and depth, not tokens.

    Side Effects:
        - Reads multiple files from filesystem (recursive loading)
        - Uses format parser registry and reference resolver
        - No state mutation (pure function except for I/O)

    Args:
        root_path: Path to root node file (relative or absolute)
        config: Network configuration (limits).
            Defaults to NetworkConfig() with standard limits (max_depth=10,
            max_node_size=10MB, max_network_size=1000).
        version: Optional version specification for version-aware resolution.

    Returns:
        NodeNetwork instance with all nodes loaded, references resolved, and
        network validated. The network includes metadata (total_size, depth)
        calculated during building.

    Raises:
        NodeNetworkValidationError: If network validation fails (cycles detected)
        NodeNetworkDepthExceededError: If depth exceeds config.max_depth
        NodeReferenceNotFoundError: If any reference cannot be resolved
        NodeResourceLimitExceededError: If resource limits (size) exceeded
        FileNotFoundError: If root file does not exist
        FormatDetectionError: If format cannot be detected for any node
        FormatParseError: If parsing fails for any node

    Example:
        >>> config = NetworkConfig(max_depth=5)
        >>> network = load_node_network("prompts/research.yaml", config)
        >>> print(f"Network depth: {network.depth}")
        Network depth: 3
        >>> print(f"Total nodes: {len(network.nodes)}")
        Total nodes: 5
    """
    path_obj = Path(root_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Root node file not found: {path_obj}")

    builder = NodeNetworkBuilder()
    return builder.build_network(path_obj, config, version=version)


def render_node_network(
    network: NodeNetwork,
    target_format: Literal["yaml", "markdown", "json", "jinja2"],
    render_mode: Literal["full", "file_first"] = "file_first",
    vars: dict[str, Any] | None = None,
) -> str:
    """Render a NodeNetwork to target format with specified render mode and optional variables.

    # AICODE-NOTE: This function was refactored from ~750 lines to ~60 lines as part of
    # the SOLID refactoring (008-solid-refactor). The duplicate reference processing code
    # was extracted into ReferenceInliner and strategy classes.

    Renders the network's root node and processes referenced child nodes
    based on the render mode:
    - "file_first": Returns content with file references (links) preserved
    - "full": Inlines all referenced content at the location of references (replaces links)

    Variable substitution is performed after rendering if vars parameter is provided.
    Variables can be scoped to specific nodes or paths:
    - Simple: {"var": "value"} - applies to all nodes
    - Node-scoped: {"node_name.var": "value"} - applies only to nodes with that name
    - Path-scoped: {"root.group.node.var": "value"} - applies only at specific path

    Args:
        network: NodeNetwork to render (must have valid root node)
        target_format: Target format to render to (markdown, yaml, json, jinja2)
        render_mode: Rendering mode (file_first or full)
        vars: Optional dictionary of variables for substitution

    Returns:
        Rendered content as string in the specified format.

    Example:
        >>> network = load_node_network("prompts/note_creation.md")
        >>> output = render_node_network(network, "markdown", render_mode="full")
    """
    import json

    import yaml

    # Apply variables if provided (operate on deep copy to preserve original)
    if vars:
        network = network.model_copy(deep=True)
        _apply_variables_to_network(network, vars)

    # Fast path: same format, file_first mode - return raw content
    if (
        render_mode == "file_first"
        and network.root.format == target_format
        and "raw_content" in network.root.content
    ):
        raw_content = network.root.content["raw_content"]
        return str(raw_content)

    # Full mode: use ReferenceInliner to process all references
    if render_mode == "full" and network.root.references:
        inliner = ReferenceInliner()
        inlined_content = inliner.inline_references(network.root, network, target_format)

        # Format the output based on target format
        if target_format == "markdown":
            if isinstance(inlined_content, str):
                return inlined_content
            elif network.root.format == "yaml":
                yaml_str = yaml.dump(
                    inlined_content, default_flow_style=False, sort_keys=False
                ).strip()
                return f"```yaml\n{yaml_str}\n```"
            elif network.root.format == "json":
                json_str = json.dumps(inlined_content, indent=2)
                return f"```json\n{json_str}\n```"
            else:
                return str(inlined_content)

        elif target_format == "yaml":
            if isinstance(inlined_content, dict):
                return yaml.dump(inlined_content, default_flow_style=False, sort_keys=False)
            return str(inlined_content)

        elif target_format == "json":
            if isinstance(inlined_content, dict):
                return json.dumps(inlined_content, indent=2)
            return str(inlined_content)

        else:
            # jinja2 or other formats
            return (
                str(inlined_content) if isinstance(inlined_content, str) else str(inlined_content)
            )

    # file_first mode: render root node and keep references as links
    return render_node(network.root, target_format)


def _extract_node_name(node_id: str) -> str:
    """Extract node name from node ID (typically file path).

    # AICODE-NOTE: Node name extraction strategy:
    # - Take the filename from the full path
    # - Remove file extension
    # - Remove version suffix (_v1, _v2, etc.) if present
    # - Result is the base name used for node-scoped variable matching
    #
    # Examples:
    #   "/path/to/instructions_v1.md" -> "instructions"
    #   "templates/data.yaml" -> "data"
    #   "root.md" -> "root"
    """
    from pathlib import Path

    # Get filename without path
    filename = Path(node_id).stem  # stem removes extension

    # Remove version suffix if present (e.g., "_v1", "_v2.0", "_v1.0.0")
    # Pattern: _v{digits} optionally followed by .{digits} and .{digits}
    import re

    version_pattern = re.compile(r"_v\d+(\.\d+)?(\.\d+)?$")
    base_name = version_pattern.sub("", filename)

    return base_name


def _apply_variables_to_network(network: NodeNetwork, variables: dict[str, Any]) -> None:
    """Apply variable substitution to every node in the network copy."""
    if not variables:
        return

    substitutor = VariableSubstitutor()
    visited: set[str] = set()

    root_path = Path(str(network.root.id)).resolve()
    root_dir = root_path.parent
    root_name = _sanitize_path_segment(_extract_node_name(root_path.name))

    def dfs(node: ContextNode) -> None:
        node_id = str(node.id)
        if node_id in visited:
            return
        visited.add(node_id)

        node_path = Path(node_id)
        hierarchical_path = _build_hierarchical_path(
            node_path=node_path, root_dir=root_dir, root_path=root_path, root_name=root_name
        )

        _apply_variables_to_node(
            node=node,
            hierarchical_path=hierarchical_path,
            variables=variables,
            substitutor=substitutor,
        )

        for child in node.children:
            dfs(child)

    dfs(network.root)

    # Ensure disconnected nodes (if any) also receive substitutions
    for node_id, node in network.nodes.items():
        if node_id not in visited:
            dfs(node)


def _apply_variables_to_node(
    node: ContextNode,
    hierarchical_path: str,
    variables: dict[str, Any],
    substitutor: VariableSubstitutor,
) -> None:
    """Apply variables to a single node's content in-place."""
    if not variables:
        return

    node_id = str(node.id)
    node_name = _sanitize_path_segment(_extract_node_name(node_id))

    def build_context(content: str) -> SubstitutionContext:
        return SubstitutionContext(
            node_id=node_id,
            node_name=node_name,
            hierarchical_path=hierarchical_path,
            content=content,
            format=node.format,
            variables=variables,
        )

    if "raw_content" in node.content and isinstance(node.content["raw_content"], str):
        node.content["raw_content"] = substitutor.substitute(
            build_context(node.content["raw_content"])
        )
    else:
        node.content = _apply_variables_to_structure(node.content, build_context, substitutor)


def _apply_variables_to_structure(
    value: Any,
    context_factory: Callable[[str], SubstitutionContext],
    substitutor: VariableSubstitutor,
) -> Any:
    """Recursively apply substitution to string values inside structured content."""
    if isinstance(value, str):
        return substitutor.substitute(context_factory(value))
    if isinstance(value, dict):
        return {
            key: _apply_variables_to_structure(sub_value, context_factory, substitutor)
            for key, sub_value in value.items()
        }
    if isinstance(value, list):
        return [_apply_variables_to_structure(item, context_factory, substitutor) for item in value]
    return value


def _build_hierarchical_path(
    node_path: Path, root_dir: Path, root_path: Path, root_name: str
) -> str:
    """Construct hierarchical dot path for a node relative to the root."""
    resolved_node = node_path.resolve()
    if resolved_node == root_path:
        return root_name

    try:
        relative_parts = resolved_node.relative_to(root_dir).parts
    except ValueError:
        # Node outside of root directory; fall back to sanitized node name with root prefix
        fallback = _sanitize_path_segment(_extract_node_name(node_path.name))
        return f"{root_name}.{fallback}" if fallback and fallback != root_name else root_name

    segments: list[str] = [root_name]
    if relative_parts:
        *dirs, filename = relative_parts
    else:
        dirs = []
        filename = resolved_node.name

    for directory in dirs:
        sanitized = _sanitize_path_segment(directory)
        if sanitized:
            segments.append(sanitized)

    filename_segment = _sanitize_path_segment(_extract_node_name(filename))
    if filename_segment and filename_segment != root_name:
        segments.append(filename_segment)

    return ".".join(segments)


def _sanitize_path_segment(segment: str) -> str:
    """Sanitize filesystem segment names for variable scoping paths."""
    import re

    sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", segment)
    sanitized = re.sub(r"_+", "_", sanitized).strip("_")
    if not sanitized:
        sanitized = "node"
    if sanitized[0].isdigit():
        sanitized = f"_{sanitized}"
    return sanitized
