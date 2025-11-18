from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, MutableMapping, Optional

from promptic.adapters.registry import AdapterRegistry
from promptic.blueprints.models import ExecutionLogEntry
from promptic.instructions.store import FilesystemInstructionStore, InstructionResolver
from promptic.pipeline.context_materializer import ContextMaterializer
from promptic.settings.base import ContextEngineSettings


@dataclass(slots=True)
class PreviewResponse:
    rendered_context: str
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ExecutionResponse:
    run_id: str
    events: list[ExecutionLogEntry] = field(default_factory=list)


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
    instruction_store = FilesystemInstructionStore(runtime_settings.instruction_root)
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


def preview_blueprint(
    *,
    blueprint_id: str,
    sample_data: Mapping[str, Any] | None = None,
    sample_memory: Mapping[str, Any] | None = None,
    settings: ContextEngineSettings | None = None,
) -> PreviewResponse:
    raise NotImplementedError(
        "Blueprint preview is not yet implemented. Track progress in tasks.md (T017-T027)."
    )


def run_pipeline(
    *,
    blueprint_id: str,
    data_inputs: Mapping[str, Any] | None = None,
    memory_inputs: Mapping[str, Any] | None = None,
    settings: ContextEngineSettings | None = None,
) -> ExecutionResponse:
    raise NotImplementedError(
        "Pipeline execution is not yet implemented. Track progress in tasks.md (T038-T047)."
    )


__all__ = [
    "PreviewResponse",
    "ExecutionResponse",
    "build_materializer",
    "preview_blueprint",
    "run_pipeline",
]
