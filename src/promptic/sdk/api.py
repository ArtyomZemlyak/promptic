"""Promptic SDK API - simplified version after blueprint/adapter removal.

# AICODE-NOTE: This module was significantly simplified during the 006-remove-unused-code cleanup.
#              All blueprint-related functions (load_blueprint, render_for_llm, preview_blueprint,
#              render_instruction, bootstrap_runtime, build_materializer) have been removed.
#              Only versioning functions remain: load_prompt, export_version, cleanup_exported_version.
#              These functions provide version-aware prompt loading and export capabilities.
#
#              Added render() function that combines load_node_network + render_node_network
#              for simplified one-step rendering from file paths.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Optional

from promptic.context.nodes.models import NetworkConfig
from promptic.sdk.nodes import load_node_network, render_node_network
from promptic.versioning import (
    ExportResult,
    HierarchicalVersionResolver,
    VersionCleanup,
    VersionedFileScanner,
    VersionExporter,
    VersionResolver,
    VersionSpec,
)


def render(
    path: str | Path,
    *,
    target_format: Literal["yaml", "markdown", "json", "jinja2"] = "markdown",
    render_mode: Literal["full", "file_first"] = "full",
    vars: dict[str, Any] | None = None,
    config: NetworkConfig | None = None,
    version: Optional[VersionSpec] = None,
    export_to: str | Path | None = None,
    overwrite: bool = False,
) -> str | ExportResult:
    """
    Load and render a prompt file in one convenient function call.

    # AICODE-NOTE: This is the main entry point for promptic. It combines
    # load_node_network() and render_node_network() into a single convenient
    # function that handles the most common use case: loading a file and
    # rendering it to a target format with optional variable substitution.
    #
    # When export_to is provided, it also handles version export functionality,
    # eliminating the need to call export_version() separately.

    This function provides the complete promptic workflow:
    1. Load the file and build a node network (with reference resolution)
    2. Render the network to the target format with variable substitution
    3. Optionally export to directory (when export_to is provided)

    Args:
        path: Path to the prompt file to render (markdown, yaml, json, jinja2)
        target_format: Target output format (default: "markdown")
            - "markdown": Markdown format
            - "yaml": YAML format
            - "json": JSON format
            - "jinja2": Jinja2 template format
        render_mode: Rendering mode (default: "full")
            - "full": Inline all referenced content at reference locations
            - "file_first": Preserve file references as links
        vars: Optional variables for substitution with scoping support:
            - Simple: {"var": "value"} - applies to all nodes
            - Node-scoped: {"node_name.var": "value"} - applies to specific nodes
            - Path-scoped: {"root.group.node.var": "value"} - applies at specific path
        config: Optional network configuration (max_depth, size limits)
        version: Optional version specification for version-aware loading
        export_to: Optional directory path to export files (instead of returning string)
            When provided, files are exported with version suffixes removed
        overwrite: Whether to overwrite existing export directory (default: False)

    Returns:
        - str: Rendered content as string (when export_to is None)
        - ExportResult: Export result with files and content (when export_to is provided)

    Raises:
        FileNotFoundError: If file doesn't exist
        FormatDetectionError: If format cannot be detected
        FormatParseError: If parsing fails
        NodeNetworkValidationError: If network validation fails (cycles, depth)
        ExportError: If export fails (when export_to is provided)
        ExportDirectoryExistsError: If target exists without overwrite (when export_to is provided)

    Example:
        >>> # Simple: render markdown file with all references inlined
        >>> output = render("prompts/task.md")
        >>> print(output)

        >>> # With variables
        >>> output = render(
        ...     "prompts/task.md",
        ...     vars={"user_name": "Alice", "task_type": "analysis"}
        ... )

        >>> # Convert to different format with file-first mode
        >>> yaml_output = render(
        ...     "prompts/task.md",
        ...     target_format="yaml",
        ...     render_mode="file_first"
        ... )

        >>> # With version specification
        >>> output = render("prompts/task.md", version="v1.0.0")

        >>> # Export to directory instead of returning string
        >>> result = render(
        ...     "prompts/task.md",
        ...     version="v2.0.0",
        ...     export_to="output/task_v2",
        ...     vars={"user": "Alice"}
        ... )
        >>> print(f"Exported {len(result.exported_files)} files")
        >>> print(result.root_prompt_content)
    """
    # AICODE-NOTE: If export_to is provided, use export_version() workflow instead of render_node_network()
    if export_to is not None:
        # Use version export workflow
        exporter = VersionExporter()
        version_spec = version if version is not None else "latest"
        return exporter.export_version(
            source_path=str(path),
            version_spec=version_spec,
            target_dir=str(export_to),
            overwrite=overwrite,
            vars=vars,
        )

    # Standard rendering workflow (return string)
    # Load the node network from file
    network = load_node_network(root_path=path, config=config, version=version)

    # Render the network to target format
    return render_node_network(
        network=network, target_format=target_format, render_mode=render_mode, vars=vars
    )


def load_prompt(
    path: str | Path,
    *,
    version: VersionSpec = "latest",
) -> str:
    """
    Load a prompt from a directory with version-aware resolution.

    # AICODE-NOTE: This function provides version-aware prompt loading for the SDK API.
    It uses VersionedFileScanner for simple version specs and HierarchicalVersionResolver
    for hierarchical specifications. Supports "latest" (default), specific versions
    (v1, v1.1, v1.1.1), and hierarchical version specifications (dict).

    Args:
        path: Directory path containing versioned prompt files
        version: Version specification ("latest", "v1", "v1.1", "v1.1.1", or dict)

    Returns:
        Content of the resolved prompt file

    Raises:
        VersionNotFoundError: If requested version doesn't exist
        FileNotFoundError: If directory doesn't exist

    Example:
        >>> # Load latest version
        >>> content = load_prompt("prompts/task1/")
        >>> # Load specific version
        >>> content = load_prompt("prompts/task1/", version="v1.1.0")
        >>> # Load with hierarchical version specification
        >>> content = load_prompt("prompts/task1/", version={"root": "v1", "instructions/process": "v2"})
    """
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Directory not found: {path}")

    # Use hierarchical resolver if version is a dict, otherwise use simple scanner
    if isinstance(version, dict):
        base_resolver = VersionedFileScanner()
        resolver: VersionResolver = HierarchicalVersionResolver(base_resolver)
    else:
        resolver = VersionedFileScanner()

    resolved_path = resolver.resolve_version(str(path_obj), version)
    return Path(resolved_path).read_text(encoding="utf-8")


def export_version(
    source_path: str | Path,
    version_spec: VersionSpec,
    target_dir: str | Path,
    *,
    overwrite: bool = False,
    vars: dict[str, Any] | None = None,
) -> ExportResult:
    """
    Export a complete version snapshot of a prompt hierarchy.

    # AICODE-NOTE: This function exports a complete version snapshot preserving
    the hierarchical directory structure. Path references in files are resolved
    to work correctly in the exported structure. Export is atomic (all or nothing).
    Supports variable substitution using the vars parameter.

    Args:
        source_path: Source prompt hierarchy path (directory or file)
        version_spec: Version specification ("latest", "v1", "v1.1", or hierarchical dict)
        target_dir: Target export directory
        overwrite: Whether to overwrite existing target directory
        vars: Optional dictionary of variables for substitution

    Returns:
        ExportResult with root prompt content and exported files

    Raises:
        ExportError: If export fails (missing files, permission errors)
        ExportDirectoryExistsError: If target directory exists without overwrite

    Example:
        >>> result = export_version(
        ...     source_path="prompts/task1/",
        ...     version_spec="v2.0.0",
        ...     target_dir="export/task1_v2/",
        ...     vars={"user": "Alice"}
        ... )
        >>> print(result.root_prompt_content)
        >>> print(f"Exported {len(result.exported_files)} files")
    """
    exporter = VersionExporter()
    return exporter.export_version(
        source_path=str(source_path),
        version_spec=version_spec,
        target_dir=str(target_dir),
        overwrite=overwrite,
        vars=vars,
    )


def cleanup_exported_version(export_dir: str | Path, *, require_confirmation: bool = False) -> None:
    """
    Clean up an exported version directory safely.

    # AICODE-NOTE: This function safely removes exported version directories
    with validation to prevent accidental deletion of source prompt directories.
    The cleanup validates that the target is an export directory using heuristics
    before deletion.

    Args:
        export_dir: Export directory path to remove
        require_confirmation: Whether to require explicit confirmation (not implemented yet)

    Raises:
        InvalidCleanupTargetError: If target is source directory
        CleanupTargetNotFoundError: If directory doesn't exist

    Example:
        >>> cleanup_exported_version("export/task1_v2/")
        >>> # Source directories are protected
        >>> cleanup_exported_version("prompts/task1/")  # Raises InvalidCleanupTargetError
    """
    cleanup = VersionCleanup()
    cleanup.cleanup_exported_version(str(export_dir), require_confirmation)


__all__ = [
    "render",
    "load_prompt",
    "export_version",
    "cleanup_exported_version",
]
