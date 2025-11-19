from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Mapping, Optional, TypeVar

from promptic.adapters.registry import AdapterRegistry
from promptic.blueprints.models import ExecutionLogEntry, FallbackEvent
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
]
