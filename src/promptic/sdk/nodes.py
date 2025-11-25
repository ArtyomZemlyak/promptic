"""SDK functions for loading and rendering context nodes."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Optional

from promptic.context.nodes.errors import FormatDetectionError, FormatParseError
from promptic.context.nodes.models import ContextNode, NetworkConfig, NodeNetwork
from promptic.format_parsers.registry import get_default_registry
from promptic.pipeline.network.builder import NodeNetworkBuilder
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

    Renders the network's root node and processes referenced child nodes
    based on the render mode:
    - "file_first": Returns content with file references (links) preserved
    - "full": Inlines all referenced content at the location of references (replaces links)

    Variable substitution is performed after rendering if vars parameter is provided.
    Variables can be scoped to specific nodes or paths:
    - Simple: {"var": "value"} - applies to all nodes
    - Node-scoped: {"node_name.var": "value"} - applies only to nodes with that name
    - Path-scoped: {"root.group.node.var": "value"} - applies only at specific path

    Side Effects:
        - No state mutation (pure function)
        - May import format-specific libraries (yaml, json) on first use
        - Processes child nodes if render_mode="full"
        - Performs variable substitution if vars provided

    Args:
        network: NodeNetwork to render (must have valid root node)
        target_format: Target format to render to (markdown, yaml, json, jinja2).
            If source format matches target_format and render_mode="file_first",
            returns raw content without conversion.
        render_mode: Rendering mode:
            - "file_first": Preserves file references as links (compact output)
            - "full": Replaces references with inline content at their location
        vars: Optional dictionary of variables for substitution. Supports scoped variables:
            - "var" - applies to all nodes
            - "node.var" - applies only to nodes named "node"
            - "root.group.node.var" - applies only at hierarchical path

    Returns:
        Rendered content as string in the specified format with variables substituted.
        For full mode, references are replaced in-place (e.g., [label](file.md) becomes
        the content of file.md at that location).

    Raises:
        ValueError: If target format or render mode is not supported
        KeyError: If content structure doesn't match expected format

    Example:
        >>> network = load_node_network("prompts/note_creation.md")
        >>> # File-first mode: returns markdown with links preserved
        >>> output = render_node_network(network, "markdown", render_mode="file_first")
        >>> # Full mode: replaces [label](file.md) with file content at that location
        >>> full_output = render_node_network(network, "markdown", render_mode="full")
        >>> # With variables
        >>> output_with_vars = render_node_network(
        ...     network, "markdown", vars={"user_name": "Alice", "node.format": "detailed"}
        ... )
    """
    # AICODE-NOTE: Format conversion logic:
    #              - If source format == target format and file_first mode:
    #                return raw_content without conversion (no processing needed)
    #              - Otherwise: convert through JSON intermediate representation
    #              - render_mode determines whether to inline references or keep links

    # Fast path: same format, file_first mode - return raw content
    if (
        render_mode == "file_first"
        and network.root.format == target_format
        and "raw_content" in network.root.content
    ):
        # AICODE-NOTE: For same-format file_first rendering, return original content
        #              as-is without any conversion or processing
        raw_content = network.root.content["raw_content"]
        return str(raw_content) if isinstance(raw_content, str) else str(raw_content)

    # Process references based on render_mode
    if render_mode == "full" and network.root.references:
        # Full mode: inline all referenced content at the location of references
        # AICODE-NOTE: For full mode, we need to replace references in-place,
        #              not append them at the end.

        # Find referenced nodes in network.nodes dict by matching reference path
        referenced_nodes = {}
        for ref in network.root.references:
            # Try to find node by exact path match or by checking if path is in node ID
            child = None
            for node_id, node in network.nodes.items():
                if (
                    node_id == ref.path
                    or ref.path in str(node_id)
                    or str(node_id).endswith(ref.path)
                ):
                    child = node
                    break
            if child:
                # Use ref.path as key to match with links in content
                referenced_nodes[ref.path] = (ref, child)

        if target_format == "markdown":
            # For markdown: render in root node's native format, then wrap in code block
            # If root is yaml → render as yaml, wrap in ```yaml
            # If root is json → render as json, wrap in ```json
            # If root is markdown → just process with reference replacement

            if "raw_content" in network.root.content:
                # For markdown/jinja2 root nodes, process as text with reference replacement
                # Referenced yaml/json files are wrapped in code blocks
                import json
                import re

                import yaml

                def process_node_for_markdown_inline(node: ContextNode) -> str:
                    """Process a node for inline insertion in markdown, with code blocks for yaml/json."""
                    if "raw_content" in node.content:
                        # Text file (markdown/jinja2) - process recursively
                        return process_markdown_string(node.content["raw_content"])
                    else:
                        # Structured file (yaml/json) - render with full reference resolution
                        def process_node_content(n: ContextNode) -> Any:
                            """Process node content and replace all $ref with inline content."""
                            content = n.content.copy()

                            if "raw_content" in content and isinstance(content["raw_content"], str):
                                raw = content["raw_content"]

                                # Process jinja2 refs
                                jinja2_ref_pattern = re.compile(
                                    r"\{\#\s*ref:\s*([^\#]+)\s*\#\}", re.IGNORECASE
                                )

                                def replace_jinja2_ref(match: re.Match[str]) -> str:
                                    path = match.group(1).strip()
                                    child = None
                                    for node_id, nn in network.nodes.items():
                                        if (
                                            path == str(node_id)
                                            or path in str(node_id)
                                            or str(node_id).endswith(path)
                                        ):
                                            child = nn
                                            break
                                    if child:
                                        child_content = process_node_content(child)
                                        if isinstance(child_content, str):
                                            return child_content
                                        else:
                                            if node.format == "yaml":
                                                return yaml.dump(
                                                    child_content,
                                                    default_flow_style=False,
                                                    sort_keys=False,
                                                ).strip()
                                            else:
                                                return json.dumps(child_content, indent=2)
                                    return match.group(0)

                                raw = jinja2_ref_pattern.sub(replace_jinja2_ref, raw)

                                # Process markdown refs
                                markdown_ref_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

                                def replace_markdown_ref(match: re.Match[str]) -> str:
                                    path = match.group(2)
                                    if path.startswith(("http://", "https://", "mailto:")):
                                        return match.group(0)
                                    child = None
                                    for node_id, nn in network.nodes.items():
                                        if (
                                            path == str(node_id)
                                            or path in str(node_id)
                                            or str(node_id).endswith(path)
                                        ):
                                            child = nn
                                            break
                                    if child:
                                        child_content = process_node_content(child)
                                        if isinstance(child_content, str):
                                            return child_content
                                        else:
                                            if node.format == "yaml":
                                                return yaml.dump(
                                                    child_content,
                                                    default_flow_style=False,
                                                    sort_keys=False,
                                                ).strip()
                                            else:
                                                return json.dumps(child_content, indent=2)
                                    return match.group(0)

                                raw = markdown_ref_pattern.sub(replace_markdown_ref, raw)
                                return raw

                            # For yaml/json nodes, process structure
                            def replace_refs_in_dict(data: dict[str, Any]) -> dict[str, Any]:
                                """Recursively replace $ref with referenced content."""
                                result = {}
                                for key, value in data.items():
                                    if isinstance(value, dict):
                                        if "$ref" in value:
                                            ref_path = value["$ref"]
                                            if isinstance(ref_path, str):
                                                child = None
                                                for node_id, nn in network.nodes.items():
                                                    if (
                                                        ref_path == str(node_id)
                                                        or ref_path in str(node_id)
                                                        or str(node_id).endswith(ref_path)
                                                    ):
                                                        child = nn
                                                        break
                                                if child:
                                                    child_content = process_node_content(child)
                                                    result[key] = child_content
                                                else:
                                                    result[key] = value
                                            else:
                                                result[key] = value
                                        else:
                                            result[key] = replace_refs_in_dict(value)
                                    elif isinstance(value, list):
                                        result[key] = [
                                            (
                                                replace_refs_in_dict(item)
                                                if isinstance(item, dict)
                                                else item
                                            )
                                            for item in value
                                        ]
                                    else:
                                        result[key] = value
                                return result

                            return replace_refs_in_dict(content)

                        # Render node with all references resolved, then wrap in code block
                        processed_content = process_node_content(node)
                        if node.format == "yaml":
                            native_str = yaml.dump(
                                processed_content, default_flow_style=False, sort_keys=False
                            ).strip()
                            return f"```yaml\n{native_str}\n```"
                        elif node.format == "json":
                            native_str = json.dumps(processed_content, indent=2)
                            return f"```json\n{native_str}\n```"
                        else:
                            return str(processed_content)

                def process_markdown_string(content: str) -> str:
                    """Recursively process markdown/jinja2 strings, replacing all references."""
                    # Process jinja2 references {# ref: path #}
                    jinja2_ref_pattern = re.compile(r"\{\#\s*ref:\s*([^\#]+)\s*\#\}", re.IGNORECASE)

                    def replace_jinja2_ref(match: re.Match[str]) -> str:
                        path = match.group(1).strip()
                        child = None
                        for node_id, n in network.nodes.items():
                            if (
                                path == str(node_id)
                                or path in str(node_id)
                                or str(node_id).endswith(path)
                            ):
                                child = n
                                break

                        if child:
                            return process_node_for_markdown_inline(child)
                        return match.group(0)

                    content = jinja2_ref_pattern.sub(replace_jinja2_ref, content)

                    # Process markdown links [label](path)
                    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

                    def replace_link(match: re.Match[str]) -> str:
                        path = match.group(2)
                        if path.startswith(("http://", "https://", "mailto:")):
                            return match.group(0)

                        child = None
                        for node_id, n in network.nodes.items():
                            if (
                                path == str(node_id)
                                or path in str(node_id)
                                or str(node_id).endswith(path)
                            ):
                                child = n
                                break

                        if child:
                            return process_node_for_markdown_inline(child)
                        return match.group(0)

                    content = link_pattern.sub(replace_link, content)
                    return content

                output = process_markdown_string(network.root.content["raw_content"])
            else:
                # For yaml/json root nodes: render in native format, then wrap in code block
                root_format = network.root.format

                if root_format == "yaml":
                    # Render as YAML (use the same logic as YAML rendering)
                    import re

                    import yaml

                    def process_node_content(node: ContextNode) -> Any:
                        """Process node content and replace all $ref: with inline content."""
                        content = node.content.copy()

                        if "raw_content" in content and isinstance(content["raw_content"], str):
                            raw = content["raw_content"]

                            # Process jinja2 refs
                            jinja2_ref_pattern = re.compile(
                                r"\{\#\s*ref:\s*([^\#]+)\s*\#\}", re.IGNORECASE
                            )

                            def replace_jinja2_ref(match: re.Match[str]) -> str:
                                path = match.group(1).strip()
                                child = None
                                for node_id, n in network.nodes.items():
                                    if (
                                        path == str(node_id)
                                        or path in str(node_id)
                                        or str(node_id).endswith(path)
                                    ):
                                        child = n
                                        break
                                if child:
                                    child_content = process_node_content(child)
                                    if isinstance(child_content, str):
                                        return child_content
                                    else:
                                        return yaml.dump(
                                            child_content, default_flow_style=False, sort_keys=False
                                        ).strip()
                                return match.group(0)

                            raw = jinja2_ref_pattern.sub(replace_jinja2_ref, raw)

                            # Process markdown refs
                            markdown_ref_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

                            def replace_markdown_ref(match: re.Match[str]) -> str:
                                path = match.group(2)
                                if path.startswith(("http://", "https://", "mailto:")):
                                    return match.group(0)
                                child = None
                                for node_id, n in network.nodes.items():
                                    if (
                                        path == str(node_id)
                                        or path in str(node_id)
                                        or str(node_id).endswith(path)
                                    ):
                                        child = n
                                        break
                                if child:
                                    child_content = process_node_content(child)
                                    if isinstance(child_content, str):
                                        return child_content
                                    else:
                                        return yaml.dump(
                                            child_content, default_flow_style=False, sort_keys=False
                                        ).strip()
                                return match.group(0)

                            raw = markdown_ref_pattern.sub(replace_markdown_ref, raw)
                            return raw

                        # For yaml/json nodes, process structure
                        def replace_refs_in_dict(data: dict[str, Any]) -> dict[str, Any]:
                            """Recursively replace $ref: keys with referenced content."""
                            result = {}
                            for key, value in data.items():
                                if isinstance(value, dict) and "$ref" in value:
                                    ref_path = value["$ref"]
                                    if isinstance(ref_path, str):
                                        child = None
                                        for node_id, n in network.nodes.items():
                                            if (
                                                ref_path == str(node_id)
                                                or ref_path in str(node_id)
                                                or str(node_id).endswith(ref_path)
                                            ):
                                                child = n
                                                break
                                        if child:
                                            child_content = process_node_content(child)
                                            result[key] = child_content
                                        else:
                                            result[key] = replace_refs_in_dict(value)
                                    else:
                                        result[key] = replace_refs_in_dict(value)
                                elif isinstance(value, dict):
                                    result[key] = replace_refs_in_dict(value)
                                elif isinstance(value, list):
                                    result[key] = [
                                        (
                                            replace_refs_in_dict(item)
                                            if isinstance(item, dict)
                                            else item
                                        )
                                        for item in value
                                    ]
                                else:
                                    result[key] = value
                            return result

                        return replace_refs_in_dict(content)

                    processed_content = process_node_content(network.root)
                    yaml_str = yaml.dump(
                        processed_content, default_flow_style=False, sort_keys=False
                    ).strip()
                    output = f"```yaml\n{yaml_str}\n```"

                elif root_format == "json":
                    # Render as JSON (use the same logic as JSON rendering)
                    import json
                    import re

                    def process_node_content(node: ContextNode) -> Any:
                        """Process node content and replace all $ref with inline content."""
                        content = node.content.copy()

                        if "raw_content" in content and isinstance(content["raw_content"], str):
                            raw = content["raw_content"]

                            # Process jinja2 refs
                            jinja2_ref_pattern = re.compile(
                                r"\{\#\s*ref:\s*([^\#]+)\s*\#\}", re.IGNORECASE
                            )

                            def replace_jinja2_ref(match: re.Match[str]) -> str:
                                path = match.group(1).strip()
                                child = None
                                for node_id, n in network.nodes.items():
                                    if (
                                        path == str(node_id)
                                        or path in str(node_id)
                                        or str(node_id).endswith(path)
                                    ):
                                        child = n
                                        break
                                if child:
                                    child_content = process_node_content(child)
                                    if isinstance(child_content, str):
                                        return child_content
                                    else:
                                        return json.dumps(child_content, indent=2)
                                return match.group(0)

                            raw = jinja2_ref_pattern.sub(replace_jinja2_ref, raw)

                            # Process markdown refs
                            markdown_ref_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

                            def replace_markdown_ref(match: re.Match[str]) -> str:
                                path = match.group(2)
                                if path.startswith(("http://", "https://", "mailto:")):
                                    return match.group(0)
                                child = None
                                for node_id, n in network.nodes.items():
                                    if (
                                        path == str(node_id)
                                        or path in str(node_id)
                                        or str(node_id).endswith(path)
                                    ):
                                        child = n
                                        break
                                if child:
                                    child_content = process_node_content(child)
                                    if isinstance(child_content, str):
                                        return child_content
                                    else:
                                        return json.dumps(child_content, indent=2)
                                return match.group(0)

                            raw = markdown_ref_pattern.sub(replace_markdown_ref, raw)
                            return raw

                        # For yaml/json nodes, process structure
                        def replace_refs_in_dict(data: dict[str, Any]) -> dict[str, Any]:
                            """Recursively replace $ref objects with referenced content."""
                            result = {}
                            for key, value in data.items():
                                if isinstance(value, dict):
                                    if "$ref" in value:
                                        ref_path = value["$ref"]
                                        if isinstance(ref_path, str):
                                            child = None
                                            for node_id, n in network.nodes.items():
                                                if (
                                                    ref_path == str(node_id)
                                                    or ref_path in str(node_id)
                                                    or str(node_id).endswith(ref_path)
                                                ):
                                                    child = n
                                                    break
                                            if child:
                                                child_content = process_node_content(child)
                                                result[key] = child_content
                                            else:
                                                result[key] = value
                                        else:
                                            result[key] = value
                                    else:
                                        result[key] = replace_refs_in_dict(value)
                                elif isinstance(value, list):
                                    result[key] = [
                                        (
                                            replace_refs_in_dict(item)
                                            if isinstance(item, dict)
                                            else item
                                        )
                                        for item in value
                                    ]
                                else:
                                    result[key] = value
                            return result

                        return replace_refs_in_dict(content)

                    processed_content = process_node_content(network.root)
                    json_str = json.dumps(processed_content, indent=2)
                    output = f"```json\n{json_str}\n```"
                else:
                    # Fallback for other formats
                    output = render_node(network.root, "markdown")

        elif target_format == "yaml":
            # For YAML, replace $ref: in the structure with inline content
            # Markdown nodes are inserted as strings (raw_content)
            # YAML/JSON nodes are inserted as structure
            import re

            import yaml

            def process_node_content(node: ContextNode) -> Any:
                """Process node content and replace all $ref: with inline content.

                Returns:
                    - For yaml/json nodes: dict structure
                    - For markdown nodes: string (raw_content)
                """
                content = node.content.copy()

                # If this is a markdown/jinja2 node, process raw_content and return as string
                if "raw_content" in content and isinstance(content["raw_content"], str):
                    raw = content["raw_content"]

                    # Process jinja2 refs {# ref: path #}
                    jinja2_ref_pattern = re.compile(r"\{\#\s*ref:\s*([^\#]+)\s*\#\}", re.IGNORECASE)

                    def replace_jinja2_ref(match: re.Match[str]) -> str:
                        path = match.group(1).strip()
                        child = None
                        for node_id, n in network.nodes.items():
                            if (
                                path == str(node_id)
                                or path in str(node_id)
                                or str(node_id).endswith(path)
                            ):
                                child = n
                                break
                        if child:
                            child_content = process_node_content(child)
                            if isinstance(child_content, str):
                                return child_content
                            else:
                                return yaml.dump(
                                    child_content, default_flow_style=False, sort_keys=False
                                ).strip()
                        return match.group(0)

                    raw = jinja2_ref_pattern.sub(replace_jinja2_ref, raw)

                    # Process markdown refs [label](path)
                    markdown_ref_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

                    def replace_markdown_ref(match: re.Match[str]) -> str:
                        path = match.group(2)
                        if path.startswith(("http://", "https://", "mailto:")):
                            return match.group(0)
                        child = None
                        for node_id, n in network.nodes.items():
                            if (
                                path == str(node_id)
                                or path in str(node_id)
                                or str(node_id).endswith(path)
                            ):
                                child = n
                                break
                        if child:
                            child_content = process_node_content(child)
                            if isinstance(child_content, str):
                                return child_content
                            else:
                                return yaml.dump(
                                    child_content, default_flow_style=False, sort_keys=False
                                ).strip()
                        return match.group(0)

                    raw = markdown_ref_pattern.sub(replace_markdown_ref, raw)
                    return raw

                # For yaml/json nodes, process structure
                def replace_refs_in_dict(data: dict[str, Any]) -> dict[str, Any]:
                    """Recursively replace $ref: keys with referenced content."""
                    result = {}
                    for key, value in data.items():
                        # Check if value is a dict with $ref key
                        if isinstance(value, dict) and "$ref" in value:
                            ref_path = value["$ref"]
                            if isinstance(ref_path, str):
                                # Find referenced node in network
                                child = None
                                for node_id, n in network.nodes.items():
                                    if (
                                        ref_path == str(node_id)
                                        or ref_path in str(node_id)
                                        or str(node_id).endswith(ref_path)
                                    ):
                                        child = n
                                        break
                                if child:
                                    # Process child: returns dict for yaml/json, string for markdown
                                    child_content = process_node_content(child)
                                    result[key] = child_content
                                else:
                                    result[key] = replace_refs_in_dict(value)
                            else:
                                result[key] = replace_refs_in_dict(value)
                        elif isinstance(value, dict):
                            result[key] = replace_refs_in_dict(value)
                        elif isinstance(value, list):
                            result[key] = [
                                replace_refs_in_dict(item) if isinstance(item, dict) else item
                                for item in value
                            ]
                        else:
                            result[key] = value
                    return result

                return replace_refs_in_dict(content)

            # Process root content with all refs replaced
            processed_content = process_node_content(network.root)
            output = yaml.dump(processed_content, default_flow_style=False, sort_keys=False)

        elif target_format == "json":
            # For JSON, replace {"$ref": "path"} in the structure with inline content
            # Markdown nodes are inserted as strings (raw_content)
            # YAML/JSON nodes are inserted as structure
            import json
            import re

            def process_node_content(node: ContextNode) -> Any:
                """Process node content and replace all $ref with inline content.

                Returns:
                    - For yaml/json nodes: dict structure
                    - For markdown nodes: string (raw_content)
                """
                content = node.content.copy()

                # If this is a markdown/jinja2 node, process raw_content and return as string
                if "raw_content" in content and isinstance(content["raw_content"], str):
                    raw = content["raw_content"]

                    # Process jinja2 refs {# ref: path #}
                    jinja2_ref_pattern = re.compile(r"\{\#\s*ref:\s*([^\#]+)\s*\#\}", re.IGNORECASE)

                    def replace_jinja2_ref(match: re.Match[str]) -> str:
                        path = match.group(1).strip()
                        child = None
                        for node_id, n in network.nodes.items():
                            if (
                                path == str(node_id)
                                or path in str(node_id)
                                or str(node_id).endswith(path)
                            ):
                                child = n
                                break
                        if child:
                            child_content = process_node_content(child)
                            if isinstance(child_content, str):
                                return child_content
                            else:
                                return json.dumps(child_content, indent=2)
                        return match.group(0)

                    raw = jinja2_ref_pattern.sub(replace_jinja2_ref, raw)

                    # Process markdown refs [label](path)
                    markdown_ref_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

                    def replace_markdown_ref(match: re.Match[str]) -> str:
                        path = match.group(2)
                        if path.startswith(("http://", "https://", "mailto:")):
                            return match.group(0)
                        child = None
                        for node_id, n in network.nodes.items():
                            if (
                                path == str(node_id)
                                or path in str(node_id)
                                or str(node_id).endswith(path)
                            ):
                                child = n
                                break
                        if child:
                            child_content = process_node_content(child)
                            if isinstance(child_content, str):
                                return child_content
                            else:
                                return json.dumps(child_content, indent=2)
                        return match.group(0)

                    raw = markdown_ref_pattern.sub(replace_markdown_ref, raw)
                    return raw

                # For yaml/json nodes, process structure
                def replace_refs_in_dict(data: dict[str, Any]) -> dict[str, Any]:
                    """Recursively replace $ref objects with referenced content."""
                    result = {}
                    for key, value in data.items():
                        if isinstance(value, dict):
                            # Check if this is a $ref object
                            if "$ref" in value:
                                ref_path = value["$ref"]
                                if isinstance(ref_path, str):
                                    # Find referenced node in network
                                    child = None
                                    for node_id, n in network.nodes.items():
                                        if (
                                            ref_path == str(node_id)
                                            or ref_path in str(node_id)
                                            or str(node_id).endswith(ref_path)
                                        ):
                                            child = n
                                            break
                                    if child:
                                        # Process child: returns dict for yaml/json, string for markdown
                                        child_content = process_node_content(child)
                                        result[key] = child_content
                                    else:
                                        result[key] = value
                                else:
                                    result[key] = value
                            else:
                                result[key] = replace_refs_in_dict(value)
                        elif isinstance(value, list):
                            result[key] = [
                                replace_refs_in_dict(item) if isinstance(item, dict) else item
                                for item in value
                            ]
                        else:
                            result[key] = value
                    return result

                return replace_refs_in_dict(content)

            # Process root content with all refs replaced
            processed_content = process_node_content(network.root)
            output = json.dumps(processed_content, indent=2)

    else:
        # file_first mode: render root node and keep references as links
        output = render_node(network.root, target_format)
        # References are already in the content (as links), so we don't need to add anything

    # AICODE-NOTE: Variable substitution happens after rendering is complete
    # This ensures variables are substituted in the final rendered content,
    # after all references have been resolved (in full mode) or preserved (in file_first mode)
    if vars:
        from promptic.context.variables import SubstitutionContext, VariableSubstitutor

        # Extract node name from node ID (filename without path and extension)
        node_name = _extract_node_name(network.root.id)

        # For root node, hierarchical path is just the node name
        # (This will be extended when processing child nodes in the future)
        hierarchical_path = node_name

        # Create substitution context
        context = SubstitutionContext(
            node_id=network.root.id,
            node_name=node_name,
            hierarchical_path=hierarchical_path,
            content=output,
            format=target_format,
            variables=vars,
        )

        # Perform substitution
        substitutor = VariableSubstitutor()
        output = substitutor.substitute(context)

    return output


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
