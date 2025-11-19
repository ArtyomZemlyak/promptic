from __future__ import annotations

from typing import Any, Mapping
from uuid import uuid4

from promptic.context.errors import PrompticError
from promptic.context.logging import JsonlEventLogger
from promptic.instructions.cache import InstructionCache
from promptic.instructions.store import FilesystemInstructionStore
from promptic.pipeline.builder import BlueprintBuilder
from promptic.pipeline.context_materializer import ContextMaterializer
from promptic.pipeline.executor import PipelineExecutor
from promptic.pipeline.hooks import PipelineHooks
from promptic.pipeline.loggers import PipelineLogger
from promptic.pipeline.policies import PolicyEngine
from promptic.pipeline.validation import BlueprintValidator
from promptic.sdk.api import ExecutionResponse, build_materializer
from promptic.settings.base import ContextEngineSettings


def run_pipeline(
    *,
    blueprint_id: str,
    data_inputs: Mapping[str, Any] | None = None,
    memory_inputs: Mapping[str, Any] | None = None,
    settings: ContextEngineSettings | None = None,
    materializer: ContextMaterializer | None = None,
) -> ExecutionResponse:
    runtime_settings = settings or ContextEngineSettings()
    runtime_settings.ensure_directories()
    builder = _build_builder(runtime_settings)
    pipeline_materializer = materializer or build_materializer(settings=runtime_settings)
    run_id = str(uuid4())
    event_logger = JsonlEventLogger(
        runtime_settings.log_root, blueprint_id=blueprint_id, run_id=run_id
    )
    logger = PipelineLogger(event_logger=event_logger)
    policies = PolicyEngine(settings=runtime_settings)
    executor = PipelineExecutor(
        builder=builder,
        materializer=pipeline_materializer,
        logger=logger,
        policies=policies,
        hooks=PipelineHooks(),
    )
    result = executor.run(
        blueprint_id=blueprint_id,
        data_inputs=data_inputs,
        memory_inputs=memory_inputs,
        run_id=run_id,
    )
    if not result.ok:
        error = result.error or PrompticError("Pipeline execution failed.")
        raise error
    artifact = result.unwrap()
    return ExecutionResponse(
        run_id=artifact.run_id, events=artifact.events, warnings=result.warnings
    )


def _build_builder(settings: ContextEngineSettings) -> BlueprintBuilder:
    instruction_store = InstructionCache(
        FilesystemInstructionStore(settings.instruction_root),
        max_entries=256,
    )
    validator = BlueprintValidator(settings=settings, instruction_store=instruction_store)
    return BlueprintBuilder(settings=settings, validator=validator)


__all__ = ["run_pipeline"]
