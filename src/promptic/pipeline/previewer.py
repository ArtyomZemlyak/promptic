from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from promptic.blueprints.models import (
    BlueprintStep,
    ContextBlueprint,
    FallbackEvent,
    InstructionNodeRef,
)
from promptic.context.errors import OperationResult, PrompticError
from promptic.context.rendering import render_context_preview
from promptic.pipeline.builder import BlueprintBuilder
from promptic.pipeline.context_materializer import ContextMaterializer

logger = logging.getLogger(__name__)


@dataclass
class PreviewArtifact:
    blueprint: ContextBlueprint
    rendered_context: str
    instruction_ids: list[str] = field(default_factory=list)
    fallback_events: list[FallbackEvent] = field(default_factory=list)


class ContextPreviewer:
    """High-level orchestration for building and rendering blueprint previews."""

    def __init__(
        self,
        *,
        builder: BlueprintBuilder,
        materializer: ContextMaterializer,
    ) -> None:
        self._builder = builder
        self._materializer = materializer

    def preview(
        self,
        *,
        blueprint_id: str,
        sample_data: Mapping[str, Any] | None = None,
        sample_memory: Mapping[str, Any] | None = None,
    ) -> OperationResult[PreviewArtifact]:
        sample_data = sample_data or {}
        sample_memory = sample_memory or {}
        aggregate_warnings: list[str] = []
        fallback_events: list[FallbackEvent] = []

        blueprint_result = self._builder.load(blueprint_id)
        if not blueprint_result.ok:
            error = self._ensure_error(blueprint_result.error, "Blueprint load failed.")
            return OperationResult.failure(error, warnings=blueprint_result.warnings)
        blueprint = blueprint_result.unwrap()
        aggregate_warnings.extend(blueprint_result.warnings)

        warm_result = self._materializer.prefetch_instructions(blueprint)
        aggregate_warnings.extend(warm_result.warnings)
        fallback_events.extend(self._materializer.consume_fallback_events())
        if not warm_result.ok:
            error = self._ensure_error(
                warm_result.error, "Instruction warm-up failed before preview."
            )
            return OperationResult.failure(error, warnings=aggregate_warnings)

        data_result = self._materializer.resolve_data_slots(
            blueprint,
            overrides=sample_data,
        )
        aggregate_warnings.extend(data_result.warnings)
        fallback_events.extend(self._materializer.consume_fallback_events())
        if not data_result.ok:
            data_error = self._ensure_error(
                data_result.error, "Failed to resolve required data slots."
            )
            return OperationResult.failure(data_error, warnings=aggregate_warnings)
        data_values = data_result.unwrap()

        memory_result = self._materializer.resolve_memory_slots(
            blueprint,
            overrides=sample_memory,
        )
        aggregate_warnings.extend(memory_result.warnings)
        fallback_events.extend(self._materializer.consume_fallback_events())
        if not memory_result.ok:
            memory_error = self._ensure_error(
                memory_result.error, "Failed to resolve required memory slots."
            )
            return OperationResult.failure(memory_error, warnings=aggregate_warnings)
        memory_values = memory_result.unwrap()

        instruction_ids: list[str] = []
        global_instruction_text, warnings, instruction_error = self._resolve_instruction_text(
            blueprint.global_instructions,
            instruction_ids,
        )
        aggregate_warnings.extend(warnings)
        fallback_events.extend(self._materializer.consume_fallback_events())
        if instruction_error:
            return OperationResult.failure(instruction_error, warnings=aggregate_warnings)

        step_text, step_warnings, step_error = self._resolve_step_instructions(
            blueprint.steps, instruction_ids
        )
        aggregate_warnings.extend(step_warnings)
        fallback_events.extend(self._materializer.consume_fallback_events())
        if step_error:
            return OperationResult.failure(step_error, warnings=aggregate_warnings)

        template_context = {
            "blueprint": blueprint.model_dump(),
            "data": data_values,
            "memory": memory_values,
            # Back-compat names used throughout the docs.
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
        )
        aggregate_warnings.extend(render_result.warnings)

        if instruction_ids:
            # AICODE-NOTE: Preview logging exposes which instruction assets influenced a run.
            logger.info(
                "preview instruction_ids=%s blueprint_id=%s",
                instruction_ids,
                blueprint.id,
            )

        artifact = PreviewArtifact(
            blueprint=blueprint,
            rendered_context=render_result.text,
            instruction_ids=instruction_ids,
            fallback_events=fallback_events,
        )
        return OperationResult.success(artifact, warnings=aggregate_warnings)

    def _resolve_step_instructions(
        self,
        steps: Sequence[BlueprintStep],
        instruction_ids: list[str],
    ) -> tuple[dict[str, list[str]], list[str], PrompticError | None]:
        mapping: dict[str, list[str]] = {}
        warnings: list[str] = []
        encountered_error: PrompticError | None = None

        def _walk(step: BlueprintStep) -> bool:
            nonlocal encountered_error
            texts, step_warnings, error = self._resolve_instruction_text(
                step.instruction_refs, instruction_ids
            )
            warnings.extend(step_warnings)
            if error:
                encountered_error = error
                return False
            mapping[step.step_id] = texts
            for child in step.children:
                if not _walk(child):
                    return False
            return True

        for step in steps:
            if not _walk(step):
                return (
                    mapping,
                    warnings,
                    self._ensure_error(encountered_error, "Instruction resolution failed."),
                )
        return mapping, warnings, encountered_error

    def _resolve_instruction_text(
        self,
        refs: Sequence[InstructionNodeRef],
        instruction_ids: list[str],
    ) -> tuple[list[str], list[str], PrompticError | None]:
        if not refs:
            return [], [], None
        result = self._materializer.resolve_instruction_refs(refs)
        warnings = list(result.warnings)
        if not result.ok:
            error = result.error or PrompticError("Instruction resolution failed.")
            return [], warnings, error
        payloads = []
        for node, content in result.unwrap():
            instruction_ids.append(node.instruction_id)
            payloads.append(content)
        return payloads, warnings, None

    @staticmethod
    def _ensure_error(error: PrompticError | None, message: str) -> PrompticError:
        return error if error else PrompticError(message)


__all__ = ["ContextPreviewer", "PreviewArtifact"]
