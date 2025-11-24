from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Generic, Iterator, Mapping, Optional, TypeVar

from promptic.adapters.registry import AdapterRegistry
from promptic.blueprints.models import BlueprintStep, ContextBlueprint, FallbackEvent
from promptic.context.errors import ErrorDetail, PrompticError, describe_error
from promptic.context.nodes.models import NetworkConfig, NodeNetwork
from promptic.context.template_context import build_instruction_context
from promptic.instructions.cache import InstructionCache
from promptic.instructions.store import FilesystemInstructionStore, InstructionResolver
from promptic.pipeline.context_materializer import ContextMaterializer
from promptic.sdk.nodes import load_node_network
from promptic.settings.base import ContextEngineSettings
from promptic.versioning import (
    ExportResult,
    HierarchicalVersionResolver,
    VersionCleanup,
    VersionedFileScanner,
    VersionExporter,
    VersionResolver,
    VersionSpec,
)

TResponse = TypeVar("TResponse")


@dataclass
class PreviewResponse:
    rendered_context: str
    warnings: list[str] = field(default_factory=list)
    instruction_ids: list[str] = field(default_factory=list)
    fallback_events: list[FallbackEvent] = field(default_factory=list)
    markdown: str | None = None
    metadata: Any | None = None


@dataclass
class SdkRuntime:
    settings: ContextEngineSettings
    materializer: ContextMaterializer
    registry: AdapterRegistry


@dataclass
class SdkResult(Generic[TResponse]):
    response: TResponse | None = None
    error: ErrorDetail | None = None
    warnings: list[str] = field(default_factory=list)
    duration_ms: float | None = None


def build_materializer(
    *,
    settings: ContextEngineSettings | None = None,
    registry: AdapterRegistry | None = None,
) -> ContextMaterializer:
    """
    Construct a ContextMaterializer wired with filesystem stores and registry hooks.

    # AICODE-NOTE: The SDK exposes this helper so higher-level modules can share
    #              caching/registry configuration without duplicating wiring.
    """

    runtime_settings = settings or ContextEngineSettings()
    instruction_store = InstructionCache(
        FilesystemInstructionStore(runtime_settings.instruction_root)
    )
    resolver = InstructionResolver(instruction_store)
    adapter_registry = registry or AdapterRegistry()
    adapter_registry.auto_discover(
        module_paths=runtime_settings.adapter_registry.module_paths,
        entry_point_group=runtime_settings.adapter_registry.entry_point_group,
    )
    return ContextMaterializer(
        settings=runtime_settings,
        instruction_resolver=resolver,
        adapter_registry=adapter_registry,
    )


def bootstrap_runtime(
    *,
    settings: ContextEngineSettings | None = None,
    registry: AdapterRegistry | None = None,
) -> SdkRuntime:
    runtime_settings = settings or ContextEngineSettings()
    runtime_settings.ensure_directories()
    runtime_registry = registry or AdapterRegistry()
    materializer = build_materializer(settings=runtime_settings, registry=runtime_registry)
    return SdkRuntime(
        settings=runtime_settings,
        materializer=materializer,
        registry=runtime_registry,
    )


def preview_blueprint(
    *,
    blueprint_id: str,
    sample_data: Mapping[str, Any] | None = None,
    sample_memory: Mapping[str, Any] | None = None,
    settings: ContextEngineSettings | None = None,
    materializer: ContextMaterializer | None = None,
    render_mode: str = "inline",
    base_url: str | None = None,
    depth_limit: int | None = None,
) -> PreviewResponse:
    from promptic.sdk import blueprints as _blueprint_sdk

    return _blueprint_sdk.preview_blueprint(
        blueprint_id=blueprint_id,
        sample_data=sample_data,
        sample_memory=sample_memory,
        settings=settings,
        materializer=materializer,
        render_mode=render_mode,
        base_url=base_url,
        depth_limit=depth_limit,
    )


def preview_blueprint_safe(
    *,
    blueprint_id: str,
    sample_data: Mapping[str, Any] | None = None,
    sample_memory: Mapping[str, Any] | None = None,
    settings: ContextEngineSettings | None = None,
    materializer: ContextMaterializer | None = None,
    render_mode: str = "inline",
    base_url: str | None = None,
    depth_limit: int | None = None,
) -> SdkResult[PreviewResponse]:
    return _execute_with_error_mapping(
        preview_blueprint,
        blueprint_id=blueprint_id,
        sample_data=sample_data,
        sample_memory=sample_memory,
        settings=settings,
        materializer=materializer,
        render_mode=render_mode,
        base_url=base_url,
        depth_limit=depth_limit,
    )


# Pipeline execution removed - handled by external agent frameworks
# See spec: "Library focuses solely on context construction (loading blueprints, rendering)"


def _execute_with_error_mapping(
    func: Callable[..., TResponse],
    **kwargs: Any,
) -> SdkResult[TResponse]:
    start = time.perf_counter()
    try:
        response = func(**kwargs)
    except PrompticError as exc:
        duration_ms = (time.perf_counter() - start) * 1000
        return SdkResult(
            response=None,
            error=describe_error(exc),
            warnings=[],
            duration_ms=duration_ms,
        )
    duration_ms = (time.perf_counter() - start) * 1000
    warnings = getattr(response, "warnings", [])
    return SdkResult(response=response, warnings=list(warnings), duration_ms=duration_ms)


def load_blueprint(
    blueprint_id_or_path: str | Path,
    *,
    settings: ContextEngineSettings | None = None,
    version: Optional[VersionSpec] = None,
) -> NodeNetwork:
    """
    Load a blueprint as a node network with automatic dependency resolution.

    Supports three variants:
    (A) Auto-discovery by name: load_blueprint("my_blueprint")
    (B) Explicit file path: load_blueprint("path/to/blueprint.yaml")
    (C) With optional settings: load_blueprint("my_blueprint", settings=...)

    All dependencies (instructions, adapters) are resolved automatically.
    Paths are automatically determined relative to blueprint file location.

    # AICODE-NOTE: This function now uses the unified ContextNode architecture.
    #              It loads blueprints as NodeNetwork instances, enabling
    #              format-agnostic composition and recursive node structures.
    """
    # Determine blueprint file path
    blueprint_path: Path | None = None
    if isinstance(blueprint_id_or_path, Path):
        blueprint_path = (
            blueprint_id_or_path.resolve()
            if blueprint_id_or_path.is_absolute()
            else blueprint_id_or_path
        )
    else:
        path = Path(blueprint_id_or_path)
        if path.is_absolute() or (path.exists() and path.is_file()):
            blueprint_path = path.resolve() if path.is_absolute() else path
        elif "/" in str(blueprint_id_or_path) or path.suffix in {".yaml", ".yml", ".json"}:
            blueprint_path = path
        else:
            # Try to find blueprint in default location
            runtime_settings = settings or ContextEngineSettings()
            blueprint_root = runtime_settings.blueprint_root.expanduser()
            if blueprint_root.exists():
                candidates = [
                    blueprint_root / f"{blueprint_id_or_path}.yaml",
                    blueprint_root / f"{blueprint_id_or_path}.yml",
                    blueprint_root / f"{blueprint_id_or_path}.json",
                ]
                for candidate in candidates:
                    if candidate.exists():
                        blueprint_path = candidate
                        break

    if not blueprint_path or not blueprint_path.exists():
        raise FileNotFoundError(f"Blueprint not found: {blueprint_id_or_path}")

    # Create network config from settings if provided
    config = None
    if settings:
        config = NetworkConfig(
            max_depth=settings.size_budget.max_step_depth or 10,
            token_model="gpt-4",  # Default token model
        )

    # Load node network using unified architecture
    network = load_node_network(blueprint_path, config=config, version=version)

    return network


def _create_settings_from_blueprint(
    blueprint: ContextBlueprint, base_settings: ContextEngineSettings | None = None
) -> ContextEngineSettings:
    """Create ContextEngineSettings from blueprint settings."""
    runtime_settings = base_settings or ContextEngineSettings()

    # Apply instruction_root from blueprint if specified
    if blueprint.settings.instruction_root:
        instruction_path = Path(blueprint.settings.instruction_root)
        # If relative path, resolve relative to blueprint file location (if known)
        if not instruction_path.is_absolute():
            blueprint_path = None
            if blueprint.metadata and "_source_path" in blueprint.metadata:
                blueprint_path = Path(blueprint.metadata["_source_path"])
            if blueprint_path and blueprint_path.exists():
                blueprint_dir = blueprint_path.parent.resolve()
                instruction_path = (blueprint_dir / instruction_path).resolve()
            else:
                # Fallback to current working directory if blueprint path unknown
                instruction_path = (Path.cwd() / instruction_path).resolve()
        runtime_settings.instruction_root = instruction_path

    # Apply adapter defaults from blueprint
    if blueprint.settings.adapter_defaults:
        for adapter_key, adapter_config in blueprint.settings.adapter_defaults.items():
            # Copy config to avoid modifying original
            config_copy = dict(adapter_config)
            # Resolve relative paths in adapter config
            if "path" in config_copy and isinstance(config_copy["path"], str):
                path_obj = Path(config_copy["path"])
                if not path_obj.is_absolute():
                    blueprint_path = None
                    if blueprint.metadata and "_source_path" in blueprint.metadata:
                        blueprint_path = Path(blueprint.metadata["_source_path"])
                    if blueprint_path and blueprint_path.exists():
                        blueprint_dir = blueprint_path.parent.resolve()
                        path_obj = (blueprint_dir / path_obj).resolve()
                    else:
                        # Fallback to current working directory if blueprint path unknown
                        path_obj = (Path.cwd() / path_obj).resolve()
                config_copy["path"] = str(path_obj)
            runtime_settings.adapter_registry.data_defaults[adapter_key] = config_copy

    # Apply size budgets from blueprint if specified
    if blueprint.settings.max_context_chars:
        runtime_settings.size_budget.max_context_chars = blueprint.settings.max_context_chars
    if blueprint.settings.max_step_depth:
        runtime_settings.size_budget.max_step_depth = blueprint.settings.max_step_depth
    if blueprint.settings.per_step_budget_chars:
        runtime_settings.size_budget.per_step_budget_chars = (
            blueprint.settings.per_step_budget_chars
        )

    return runtime_settings


def render_preview(
    blueprint: ContextBlueprint | NodeNetwork,
    *,
    sample_data: Mapping[str, Any] | None = None,
    sample_memory: Mapping[str, Any] | None = None,
    settings: ContextEngineSettings | None = None,
    materializer: ContextMaterializer | None = None,
) -> None:
    """
    Render a Rich-formatted preview of the blueprint to the console.

    # AICODE-NOTE: This function prints directly to console using Rich formatting.
    #              For programmatic access to preview text, use preview_blueprint().
    #              Settings from blueprint.yaml are used if settings not provided.
    """
    from promptic.context.rendering import render_context_preview
    from promptic.pipeline.previewer import ContextPreviewer
    from promptic.sdk import blueprints as _blueprint_sdk

    # Convert NodeNetwork to ContextBlueprint for compatibility during migration
    if not isinstance(blueprint, ContextBlueprint):
        from promptic.blueprints.adapters.legacy import network_to_blueprint

        blueprint = network_to_blueprint(blueprint)

    runtime_settings = _create_settings_from_blueprint(blueprint, settings)
    runtime_settings.ensure_directories()
    builder = _blueprint_sdk._build_builder(runtime_settings)
    preview_materializer = materializer or build_materializer(settings=runtime_settings)
    previewer = ContextPreviewer(builder=builder, materializer=preview_materializer)

    sample_data = sample_data or {}
    sample_memory = sample_memory or {}

    # Resolve data and memory slots
    data_result = preview_materializer.resolve_data_slots(blueprint, overrides=sample_data)
    if not data_result.ok:
        error = data_result.error or PrompticError("Failed to resolve data slots.")
        raise error
    data_values = data_result.unwrap()

    memory_result = preview_materializer.resolve_memory_slots(blueprint, overrides=sample_memory)
    if not memory_result.ok:
        error = memory_result.error or PrompticError("Failed to resolve memory slots.")
        raise error
    memory_values = memory_result.unwrap()

    render_context = build_instruction_context(
        blueprint=blueprint,
        data=data_values,
        memory=memory_values,
    )

    # Resolve instructions
    instruction_ids: list[str] = []
    global_instruction_text, warnings, instruction_error = previewer._resolve_instruction_text(
        blueprint.global_instructions, instruction_ids, context=render_context
    )
    if instruction_error:
        raise instruction_error

    step_text, step_warnings, step_error = previewer._resolve_step_instructions(
        blueprint.steps,
        instruction_ids,
        blueprint=blueprint,
        data=data_values,
        memory=memory_values,
    )
    if step_error:
        raise step_error

    template_context = render_context.get_template_variables()
    template_context.update(
        {
            "sample_data": data_values or sample_data,
            "sample_memory": memory_values or sample_memory,
        }
    )

    render_result = render_context_preview(
        blueprint=blueprint,
        template_context=template_context,
        global_instructions=global_instruction_text,
        step_instructions=step_text,
        data_preview=data_values or sample_data,
        memory_preview=memory_values or sample_memory,
        print_to_console=True,
    )


def render_for_llm(
    blueprint: ContextBlueprint | NodeNetwork,
    *,
    sample_data: Mapping[str, Any] | None = None,
    sample_memory: Mapping[str, Any] | None = None,
    settings: ContextEngineSettings | None = None,
    materializer: ContextMaterializer | None = None,
) -> str:
    """
    Render plain text context ready for LLM input.

    Returns a plain text string without any formatting artifacts.

    # AICODE-NOTE: This function produces clean text suitable for direct LLM
    #              consumption, separate from the Rich-formatted preview.
    #              Settings from blueprint.yaml are used if settings not provided.
    """
    from promptic.context.rendering import render_context_for_llm
    from promptic.pipeline.previewer import ContextPreviewer
    from promptic.sdk import blueprints as _blueprint_sdk

    # Convert NodeNetwork to ContextBlueprint for compatibility during migration
    if not isinstance(blueprint, ContextBlueprint):
        from promptic.blueprints.adapters.legacy import network_to_blueprint

        blueprint = network_to_blueprint(blueprint)

    runtime_settings = _create_settings_from_blueprint(blueprint, settings)
    runtime_settings.ensure_directories()
    builder = _blueprint_sdk._build_builder(runtime_settings)
    preview_materializer = materializer or build_materializer(settings=runtime_settings)
    previewer = ContextPreviewer(builder=builder, materializer=preview_materializer)

    sample_data = sample_data or {}
    sample_memory = sample_memory or {}

    # Resolve data and memory slots
    data_result = preview_materializer.resolve_data_slots(blueprint, overrides=sample_data)
    if not data_result.ok:
        error = data_result.error or PrompticError("Failed to resolve data slots.")
        raise error
    data_values = data_result.unwrap()

    memory_result = preview_materializer.resolve_memory_slots(blueprint, overrides=sample_memory)
    if not memory_result.ok:
        error = memory_result.error or PrompticError("Failed to resolve memory slots.")
        raise error
    memory_values = memory_result.unwrap()

    render_context = build_instruction_context(
        blueprint=blueprint,
        data=data_values,
        memory=memory_values,
    )

    # Resolve instructions
    instruction_ids: list[str] = []
    global_instruction_text, warnings, instruction_error = previewer._resolve_instruction_text(
        blueprint.global_instructions, instruction_ids, context=render_context
    )
    if instruction_error:
        raise instruction_error

    step_text, step_warnings, step_error = previewer._resolve_step_instructions(
        blueprint.steps,
        instruction_ids,
        blueprint=blueprint,
        data=data_values,
        memory=memory_values,
    )
    if step_error:
        raise step_error

    template_context = render_context.get_template_variables()
    template_context.update(
        {
            "sample_data": data_values or sample_data,
            "sample_memory": memory_values or sample_memory,
        }
    )

    render_result = render_context_for_llm(
        blueprint=blueprint,
        template_context=template_context,
        global_instructions=global_instruction_text,
        step_instructions=step_text,
    )
    return render_result.text


def render_instruction(
    blueprint: ContextBlueprint,
    instruction_id: str | None = None,
    *,
    step_id: str | None = None,
    settings: ContextEngineSettings | None = None,
    materializer: ContextMaterializer | None = None,
) -> str:
    """
    Render specific instruction(s) from a blueprint.

    Supports three variants:
    (A) render_instruction(blueprint, instruction_id, step_id=None)
    (B) render_instruction(blueprint, step_id=step_id)
    (C) blueprint.render_instruction(instruction_id) - method on blueprint

    # AICODE-NOTE: This function provides fine-grained access to individual
    #              instructions within a blueprint for debugging or selective rendering.
    """
    from promptic.pipeline.previewer import ContextPreviewer
    from promptic.sdk import blueprints as _blueprint_sdk

    if instruction_id is None and step_id is None:
        raise ValueError("Either instruction_id or step_id must be provided.")

    runtime_settings = settings or ContextEngineSettings()
    runtime_settings.ensure_directories()
    builder = _blueprint_sdk._build_builder(runtime_settings)
    preview_materializer = materializer or build_materializer(settings=runtime_settings)
    previewer = ContextPreviewer(builder=builder, materializer=preview_materializer)

    if step_id:
        # Render all instructions for a step
        step = next((s for s in _iter_all_steps(blueprint.steps) if s.step_id == step_id), None)
        if not step:
            raise ValueError(f"Step '{step_id}' not found in blueprint.")
        refs = step.instruction_refs
        context_step_id = step_id
    else:
        # Render single instruction by ID
        context_step_id = None
        if instruction_id:
            # Find instruction in global or step instructions
            refs = [
                ref for ref in blueprint.global_instructions if ref.instruction_id == instruction_id
            ]
            if not refs:
                for step in _iter_all_steps(blueprint.steps):
                    refs = [
                        ref for ref in step.instruction_refs if ref.instruction_id == instruction_id
                    ]
                    if refs:
                        context_step_id = step.step_id
                        break
            if not refs:
                raise ValueError(f"Instruction '{instruction_id}' not found in blueprint.")
        else:
            raise ValueError("Either instruction_id or step_id must be provided.")

    # Resolve data/memory if needed? render_instruction currently doesn't take inputs.
    # We assume empty/default context if not provided.
    # TODO: Consider if render_instruction should accept data/memory inputs.
    # For now, we build context with empty data/memory.
    render_context = build_instruction_context(
        blueprint=blueprint,
        data={},
        memory={},
        step_id=context_step_id,
    )

    instruction_ids: list[str] = []
    texts, warnings, error = previewer._resolve_instruction_text(
        refs, instruction_ids, context=render_context
    )
    if error:
        raise error
    return "\n\n".join(texts)


def _iter_all_steps(steps: list[BlueprintStep]) -> Iterator[BlueprintStep]:
    """Helper to iterate all steps recursively."""
    for step in steps:
        yield step
        yield from _iter_all_steps(step.children)


def _extract_blueprint_data_from_network(network: NodeNetwork) -> dict[str, Any]:
    """Extract blueprint structure from NodeNetwork root content.

    # AICODE-NOTE: This helper function extracts the blueprint structure
    #              (steps, global_instructions, data_slots, memory_slots, etc.)
    #              from a NodeNetwork's root node content. This enables migration
    #              from ContextBlueprint to NodeNetwork while maintaining compatibility
    #              with existing code that expects blueprint structure.
    """
    content = network.root.content
    return {
        "steps": content.get("steps", []),
        "global_instructions": content.get("global_instructions", []),
        "data_slots": content.get("data_slots", []),
        "memory_slots": content.get("memory_slots", []),
        "prompt_template": content.get("prompt_template", ""),
        "name": content.get("name", ""),
        "metadata": network.root.metadata,
    }


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
) -> ExportResult:
    """
    Export a complete version snapshot of a prompt hierarchy.

    # AICODE-NOTE: This function exports a complete version snapshot preserving
    the hierarchical directory structure. Path references in files are resolved
    to work correctly in the exported structure. Export is atomic (all or nothing).

    Args:
        source_path: Source prompt hierarchy path (directory or file)
        version_spec: Version specification ("latest", "v1", "v1.1", or hierarchical dict)
        target_dir: Target export directory
        overwrite: Whether to overwrite existing target directory

    Returns:
        ExportResult with root prompt content and exported files

    Raises:
        ExportError: If export fails (missing files, permission errors)
        ExportDirectoryExistsError: If target directory exists without overwrite

    Example:
        >>> result = export_version(
        ...     source_path="prompts/task1/",
        ...     version_spec="v2.0.0",
        ...     target_dir="export/task1_v2/"
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
    "PreviewResponse",
    "build_materializer",
    "bootstrap_runtime",
    "preview_blueprint",
    "preview_blueprint_safe",
    "SdkResult",
    "SdkRuntime",
    "load_blueprint",
    "load_prompt",
    "export_version",
    "cleanup_exported_version",
    "render_preview",
    "render_for_llm",
    "render_instruction",
]
