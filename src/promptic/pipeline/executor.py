from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Mapping, Sequence
from uuid import uuid4

from promptic.blueprints.models import (
    BlueprintStep,
    ContextBlueprint,
    ExecutionLogEntry,
    FallbackEvent,
    InstructionNode,
    InstructionNodeRef,
)
from promptic.context.errors import OperationResult, PrompticError
from promptic.pipeline.builder import BlueprintBuilder
from promptic.pipeline.context_materializer import ContextMaterializer
from promptic.pipeline.hooks import PipelineHooks
from promptic.pipeline.loggers import PipelineLogger
from promptic.pipeline.policies import PolicyEngine


@dataclass
class ExecutionArtifact:
    """In-memory representation of a pipeline run."""

    run_id: str
    events: List[ExecutionLogEntry] = field(default_factory=list)
    fallback_events: List[FallbackEvent] = field(default_factory=list)


class PipelineExecutor:
    """
    Traverses blueprint steps, resolving instructions/data/memory via the materializer.

    # AICODE-NOTE: Traversal is depth-first so event logs mirror blueprint structure.
    #              Adapter failures bubble immediately to keep error boundaries explicit.
    """

    def __init__(
        self,
        *,
        builder: BlueprintBuilder,
        materializer: ContextMaterializer,
        logger: PipelineLogger,
        policies: PolicyEngine,
        hooks: PipelineHooks | None = None,
    ) -> None:
        self._builder = builder
        self._materializer = materializer
        self._logger = logger
        self._policies = policies
        self._hooks = hooks or PipelineHooks()
        self._fallback_events: list[FallbackEvent] = []

    def run(
        self,
        *,
        blueprint_id: str,
        data_inputs: Mapping[str, Any] | None = None,
        memory_inputs: Mapping[str, Any] | None = None,
        run_id: str | None = None,
    ) -> OperationResult[ExecutionArtifact]:
        data_inputs = data_inputs or {}
        memory_inputs = memory_inputs or {}
        aggregate_warnings: list[str] = []
        self._fallback_events.clear()

        blueprint_result = self._builder.load(blueprint_id)
        if not blueprint_result.ok:
            error = self._ensure_error(blueprint_result.error, "Blueprint load failed.")
            return OperationResult.failure(error, warnings=blueprint_result.warnings)
        blueprint = blueprint_result.unwrap()
        aggregate_warnings.extend(blueprint_result.warnings)

        self._logger.events.clear()
        self._logger.blueprint_id = str(blueprint.id)

        warm_result = self._materializer.prefetch_instructions(blueprint)
        aggregate_warnings.extend(warm_result.warnings)
        self._log_fallback_events(step_id="__prefetch__")
        if not warm_result.ok:
            error = self._ensure_error(warm_result.error, "Instruction warm-up failed.")
            return OperationResult.failure(error, warnings=aggregate_warnings)

        data_result = self._materializer.resolve_data_slots(
            blueprint,
            overrides=data_inputs,
        )
        aggregate_warnings.extend(data_result.warnings)
        self._log_fallback_events(step_id="__data__")
        if not data_result.ok:
            error = self._ensure_error(data_result.error, "Failed to resolve required data slots.")
            return OperationResult.failure(error, warnings=aggregate_warnings)
        resolved_data = data_result.unwrap()
        for data_slot in blueprint.data_slots:
            self._logger.emit(
                step_id=data_slot.name,
                event_type="data_resolved",
                payload={"adapter_key": data_slot.adapter_key},
                reference_ids=[data_slot.name],
            )

        memory_result = self._materializer.resolve_memory_slots(
            blueprint,
            overrides=memory_inputs,
        )
        aggregate_warnings.extend(memory_result.warnings)
        self._log_fallback_events(step_id="__memory__")
        if not memory_result.ok:
            error = self._ensure_error(
                memory_result.error, "Failed to resolve required memory slots."
            )
            return OperationResult.failure(error, warnings=aggregate_warnings)
        resolved_memory = memory_result.unwrap()
        for memory_slot in blueprint.memory_slots:
            self._logger.emit(
                step_id=memory_slot.name,
                event_type="memory_resolved",
                payload={"provider_key": memory_slot.provider_key},
                reference_ids=[memory_slot.name],
            )

        run_identifier = run_id or str(uuid4())
        context = {
            "blueprint": blueprint,
            "data": resolved_data,
            "memory": resolved_memory,
        }
        for step in blueprint.steps:
            execution = self._execute_step(step=step, blueprint=blueprint, context=context)
            if not execution.ok:
                error = self._ensure_error(execution.error, "Pipeline step failed.")
                combined_warnings = aggregate_warnings + execution.warnings
                return OperationResult.failure(error, warnings=combined_warnings)
            aggregate_warnings.extend(execution.warnings)

        artifact = ExecutionArtifact(
            run_id=run_identifier,
            events=self._logger.snapshot(),
            fallback_events=list(self._fallback_events),
        )
        return OperationResult.success(artifact, warnings=aggregate_warnings)

    def _execute_step(
        self,
        *,
        step: BlueprintStep,
        blueprint: ContextBlueprint,
        context: Mapping[str, Any],
        loop_item: Any | None = None,
        loop_index: int | None = None,
    ) -> OperationResult[None]:
        enriched_context = dict(context)
        if loop_item is not None:
            enriched_context["loop_item"] = loop_item
            enriched_context["loop_index"] = loop_index

        self._hooks.before_step(blueprint=blueprint, step=step, context=enriched_context)

        instructions = self._materializer.resolve_instruction_refs(step.instruction_refs)
        if not instructions.ok:
            error = self._ensure_error(
                instructions.error, f"Instruction resolution failed for step '{step.step_id}'."
            )
            return OperationResult.failure(error, warnings=instructions.warnings)
        instruction_payloads = instructions.unwrap()
        self._log_fallback_events(step.step_id)

        text_buffer: list[str] = []
        for node, content in instruction_payloads:
            text_buffer.append(content)
            self._logger.emit(
                step_id=step.step_id,
                event_type="instruction_loaded",
                payload={
                    "instruction_id": node.instruction_id,
                    "reference_path": str(node.source_uri),
                },
                reference_ids=[node.instruction_id],
            )

        warnings = self._policies.evaluate_step_budget(step, "\n".join(text_buffer))
        for warning in warnings:
            self._logger.emit(
                step_id=step.step_id,
                event_type="size_warning",
                payload={"message": warning},
            )

        if step.kind == "loop":
            records = enriched_context["data"].get(step.loop_slot, [])
            for index, item in enumerate(records):
                self._hooks.on_loop_item(
                    blueprint=blueprint,
                    step=step,
                    item=item,
                    index=index,
                )
                for child in step.children:
                    child_result = self._execute_step(
                        step=child,
                        blueprint=blueprint,
                        context=enriched_context,
                        loop_item=item,
                        loop_index=index,
                    )
                    if not child_result.ok:
                        error = self._ensure_error(child_result.error, "Child step failed.")
                        combined = warnings + child_result.warnings
                        return OperationResult.failure(error, warnings=combined)
                    warnings.extend(child_result.warnings)
        else:
            for child in step.children:
                child_result = self._execute_step(
                    step=child,
                    blueprint=blueprint,
                    context=enriched_context,
                    loop_item=loop_item,
                    loop_index=loop_index,
                )
                if not child_result.ok:
                    error = self._ensure_error(child_result.error, "Child step failed.")
                    combined = warnings + child_result.warnings
                    return OperationResult.failure(error, warnings=combined)
                warnings.extend(child_result.warnings)

        self._hooks.after_step(blueprint=blueprint, step=step, context=enriched_context)
        return OperationResult.success(None, warnings=warnings)

    @staticmethod
    def _ensure_error(error: PrompticError | None, message: str) -> PrompticError:
        return error if error else PrompticError(message)

    def _log_fallback_events(self, step_id: str) -> None:
        events = self._materializer.consume_fallback_events()
        if not events:
            return
        self._fallback_events.extend(events)
        for event in events:
            self._logger.emit(
                step_id=step_id,
                event_type="instruction_fallback",
                payload={
                    "instruction_id": event.instruction_id,
                    "mode": getattr(event.mode, "value", event.mode),
                    "message": event.message,
                    "placeholder_used": event.placeholder_used,
                    "log_key": event.log_key,
                },
                reference_ids=[event.instruction_id],
            )


__all__ = ["ExecutionArtifact", "PipelineExecutor"]
