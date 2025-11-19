from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Generic, Iterator, Mapping, Optional, TypeVar

from promptic.adapters.registry import AdapterRegistry
from promptic.blueprints.models import (
    BlueprintStep,
    ContextBlueprint,
    ExecutionLogEntry,
    FallbackEvent,
)
from promptic.context.errors import ErrorDetail, PrompticError, describe_error
from promptic.instructions.cache import InstructionCache
from promptic.instructions.store import FilesystemInstructionStore, InstructionResolver
from promptic.pipeline.context_materializer import ContextMaterializer
from promptic.settings.base import ContextEngineSettings

TResponse = TypeVar("TResponse")


@dataclass
class PreviewResponse:
    rendered_context: str
    warnings: list[str] = field(default_factory=list)
    instruction_ids: list[str] = field(default_factory=list)
    fallback_events: list[FallbackEvent] = field(default_factory=list)


@dataclass
class ExecutionResponse:
    run_id: str
    events: list[ExecutionLogEntry] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    fallback_events: list[FallbackEvent] = field(default_factory=list)


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
) -> PreviewResponse:
    from promptic.sdk import blueprints as _blueprint_sdk

    return _blueprint_sdk.preview_blueprint(
        blueprint_id=blueprint_id,
        sample_data=sample_data,
        sample_memory=sample_memory,
        settings=settings,
        materializer=materializer,
    )


def preview_blueprint_safe(
    *,
    blueprint_id: str,
    sample_data: Mapping[str, Any] | None = None,
    sample_memory: Mapping[str, Any] | None = None,
    settings: ContextEngineSettings | None = None,
    materializer: ContextMaterializer | None = None,
) -> SdkResult[PreviewResponse]:
    return _execute_with_error_mapping(
        preview_blueprint,
        blueprint_id=blueprint_id,
        sample_data=sample_data,
        sample_memory=sample_memory,
        settings=settings,
        materializer=materializer,
    )


def run_pipeline(
    *,
    blueprint_id: str,
    data_inputs: Mapping[str, Any] | None = None,
    memory_inputs: Mapping[str, Any] | None = None,
    settings: ContextEngineSettings | None = None,
    materializer: ContextMaterializer | None = None,
) -> ExecutionResponse:
    from promptic.sdk import pipeline as _pipeline_sdk

    return _pipeline_sdk.run_pipeline(
        blueprint_id=blueprint_id,
        data_inputs=data_inputs,
        memory_inputs=memory_inputs,
        settings=settings,
        materializer=materializer,
    )


def run_pipeline_safe(
    *,
    blueprint_id: str,
    data_inputs: Mapping[str, Any] | None = None,
    memory_inputs: Mapping[str, Any] | None = None,
    settings: ContextEngineSettings | None = None,
    materializer: ContextMaterializer | None = None,
) -> SdkResult[ExecutionResponse]:
    return _execute_with_error_mapping(
        run_pipeline,
        blueprint_id=blueprint_id,
        data_inputs=data_inputs,
        memory_inputs=memory_inputs,
        settings=settings,
        materializer=materializer,
    )


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
) -> ContextBlueprint:
    """
    Load a blueprint with automatic dependency resolution.

    Supports three variants:
    (A) Auto-discovery by name: load_blueprint("my_blueprint")
    (B) Explicit file path: load_blueprint("path/to/blueprint.yaml")
    (C) With optional settings: load_blueprint("my_blueprint", settings=...)

    All dependencies (instructions, adapters) are resolved automatically.

    # AICODE-NOTE: This is the minimal API entry point that hides all complexity
    #              of blueprint loading, validation, and dependency resolution.
    """
    from promptic.sdk import blueprints as _blueprint_sdk

    runtime_settings = settings or ContextEngineSettings()
    runtime_settings.ensure_directories()
    builder = _blueprint_sdk._build_builder(runtime_settings)

    # Check if it's an explicit path
    path = Path(blueprint_id_or_path)
    if path.is_absolute() or (path.exists() and path.is_file()):
        result = builder.load_from_path(path)
    elif "/" in str(blueprint_id_or_path) or path.suffix in {".yaml", ".yml", ".json"}:
        # Looks like a path even if it doesn't exist yet
        result = builder.load_from_path(path)
    else:
        # Treat as blueprint_id for auto-discovery
        result = builder.load(str(blueprint_id_or_path))

    if not result.ok:
        error = result.error or PrompticError("Failed to load blueprint.")
        raise error

    return result.unwrap()


def render_preview(
    blueprint: ContextBlueprint,
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
    """
    from promptic.context.rendering import render_context_preview
    from promptic.pipeline.previewer import ContextPreviewer
    from promptic.sdk import blueprints as _blueprint_sdk

    runtime_settings = settings or ContextEngineSettings()
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

    # Resolve instructions
    instruction_ids: list[str] = []
    global_instruction_text, warnings, instruction_error = previewer._resolve_instruction_text(
        blueprint.global_instructions, instruction_ids
    )
    if instruction_error:
        raise instruction_error

    step_text, step_warnings, step_error = previewer._resolve_step_instructions(
        blueprint.steps, instruction_ids
    )
    if step_error:
        raise step_error

    template_context = {
        "blueprint": blueprint.model_dump(),
        "data": data_values,
        "memory": memory_values,
        "sample_data": data_values or sample_data,
        "sample_memory": memory_values or sample_memory,
    }

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
    blueprint: ContextBlueprint,
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
    """
    from promptic.context.rendering import render_context_for_llm
    from promptic.pipeline.previewer import ContextPreviewer
    from promptic.sdk import blueprints as _blueprint_sdk

    runtime_settings = settings or ContextEngineSettings()
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

    # Resolve instructions
    instruction_ids: list[str] = []
    global_instruction_text, warnings, instruction_error = previewer._resolve_instruction_text(
        blueprint.global_instructions, instruction_ids
    )
    if instruction_error:
        raise instruction_error

    step_text, step_warnings, step_error = previewer._resolve_step_instructions(
        blueprint.steps, instruction_ids
    )
    if step_error:
        raise step_error

    template_context = {
        "blueprint": blueprint.model_dump(),
        "data": data_values,
        "memory": memory_values,
        "sample_data": data_values or sample_data,
        "sample_memory": memory_values or sample_memory,
    }

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
    else:
        # Render single instruction by ID
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
                        break
            if not refs:
                raise ValueError(f"Instruction '{instruction_id}' not found in blueprint.")
        else:
            raise ValueError("Either instruction_id or step_id must be provided.")

    instruction_ids: list[str] = []
    texts, warnings, error = previewer._resolve_instruction_text(refs, instruction_ids)
    if error:
        raise error
    return "\n\n".join(texts)


def _iter_all_steps(steps: list[BlueprintStep]) -> Iterator[BlueprintStep]:
    """Helper to iterate all steps recursively."""
    for step in steps:
        yield step
        yield from _iter_all_steps(step.children)


__all__ = [
    "PreviewResponse",
    "ExecutionResponse",
    "build_materializer",
    "bootstrap_runtime",
    "preview_blueprint",
    "preview_blueprint_safe",
    "run_pipeline",
    "run_pipeline_safe",
    "SdkResult",
    "SdkRuntime",
    "load_blueprint",
    "render_preview",
    "render_for_llm",
    "render_instruction",
]
