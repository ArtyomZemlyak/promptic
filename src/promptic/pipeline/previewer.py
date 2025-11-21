from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from promptic.blueprints.adapters.legacy import network_to_blueprint
from promptic.blueprints.models import (
    BlueprintStep,
    ContextBlueprint,
    FallbackEvent,
    InstructionNodeRef,
    PromptHierarchyBlueprint,
)
from promptic.context.errors import OperationResult, PrompticError, TemplateRenderError
from promptic.context.nodes.models import NodeNetwork
from promptic.context.rendering import render_context_preview
from promptic.context.template_context import InstructionRenderContext, build_instruction_context
from promptic.pipeline.builder import BlueprintBuilder
from promptic.pipeline.context_materializer import ContextMaterializer
from promptic.pipeline.template_renderer import TemplateRenderer

logger = logging.getLogger(__name__)


@dataclass
class PreviewArtifact:
    blueprint: ContextBlueprint | NodeNetwork  # Support both during migration
    rendered_context: str
    instruction_ids: list[str] = field(default_factory=list)
    fallback_events: list[FallbackEvent] = field(default_factory=list)
    file_first_markdown: str | None = None
    file_first_metadata: PromptHierarchyBlueprint | None = None


class ContextPreviewer:
    """High-level orchestration for building and rendering blueprint previews."""

    def __init__(
        self,
        *,
        builder: BlueprintBuilder,
        materializer: ContextMaterializer,
        template_renderer: TemplateRenderer | None = None,
    ) -> None:
        self._builder = builder
        self._materializer = materializer
        self._template_renderer = template_renderer or TemplateRenderer()

    def preview(
        self,
        *,
        blueprint_id: str,
        sample_data: Mapping[str, Any] | None = None,
        sample_memory: Mapping[str, Any] | None = None,
        print_to_console: bool = True,
        render_mode: str = "inline",
        base_url: str | None = None,
        depth_limit: int | None = None,
    ) -> OperationResult[PreviewArtifact]:
        sample_data = sample_data or {}
        sample_memory = sample_memory or {}
        aggregate_warnings: list[str] = []
        fallback_events: list[FallbackEvent] = []

        blueprint_result = self._builder.load(blueprint_id)
        if not blueprint_result.ok:
            error = self._ensure_error(blueprint_result.error, "Blueprint load failed.")
            return OperationResult.failure(error, warnings=blueprint_result.warnings)
        network = blueprint_result.unwrap()
        aggregate_warnings.extend(blueprint_result.warnings)

        # Convert NodeNetwork to ContextBlueprint for compatibility during migration
        # AICODE-NOTE: This is a temporary adapter during migration. Once all code is
        #              migrated to work with NodeNetwork directly, this conversion will be removed.
        blueprint = network_to_blueprint(network)

        warm_result = self._materializer.prefetch_instructions(blueprint)
        aggregate_warnings.extend(warm_result.warnings)
        fallback_events.extend(self._materializer.consume_fallback_events())
        if not warm_result.ok:
            error = self._ensure_error(
                warm_result.error, "Instruction warm-up failed before preview."
            )
            return OperationResult.failure(error, warnings=aggregate_warnings)

        if render_mode == "file_first":
            return self._render_file_first(
                blueprint=blueprint,
                base_url=base_url,
                depth_limit=depth_limit or 3,
                aggregate_warnings=aggregate_warnings,
                fallback_events=fallback_events,
            )

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

        # Build base render context
        render_context = build_instruction_context(
            blueprint=blueprint,
            data=data_values,
            memory=memory_values,
        )

        instruction_ids: list[str] = []
        global_instruction_text, warnings, instruction_error = self._resolve_instruction_text(
            blueprint.global_instructions,
            instruction_ids,
            context=render_context,
        )
        aggregate_warnings.extend(warnings)
        fallback_events.extend(self._materializer.consume_fallback_events())
        if instruction_error:
            return OperationResult.failure(instruction_error, warnings=aggregate_warnings)

        step_text, step_warnings, step_error = self._resolve_step_instructions(
            blueprint.steps,
            instruction_ids,
            blueprint=blueprint,
            data=data_values,
            memory=memory_values,
        )
        aggregate_warnings.extend(step_warnings)
        fallback_events.extend(self._materializer.consume_fallback_events())
        if step_error:
            return OperationResult.failure(step_error, warnings=aggregate_warnings)

        template_context = render_context.get_template_variables()
        template_context.update(
            {
                # Back-compat names used throughout the docs.
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
            print_to_console=print_to_console,
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
            blueprint=network,  # Store NodeNetwork for future use
            rendered_context=render_result.text,
            instruction_ids=instruction_ids,
            fallback_events=fallback_events,
        )
        return OperationResult.success(artifact, warnings=aggregate_warnings)

    def _resolve_step_instructions(
        self,
        steps: Sequence[BlueprintStep],
        instruction_ids: list[str],
        blueprint: ContextBlueprint,
        data: dict[str, Any],
        memory: dict[str, Any],
    ) -> tuple[dict[str, list[str]], list[str], PrompticError | None]:
        mapping: dict[str, list[str]] = {}
        warnings: list[str] = []
        encountered_error: PrompticError | None = None

        def _walk(step: BlueprintStep) -> bool:
            nonlocal encountered_error

            step_context = build_instruction_context(
                blueprint=blueprint,
                data=data,
                memory=memory,
                step_id=step.step_id,
            )

            texts, step_warnings, error = self._resolve_instruction_text(
                step.instruction_refs,
                instruction_ids,
                context=step_context,
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

    def _render_file_first(
        self,
        *,
        blueprint: ContextBlueprint,
        base_url: str | None,
        depth_limit: int,
        aggregate_warnings: list[str],
        fallback_events: list[FallbackEvent],
    ) -> OperationResult[PreviewArtifact]:
        try:
            result = self._template_renderer.render_file_first(
                blueprint=blueprint,
                materializer=self._materializer,
                base_url=base_url,
                depth_limit=depth_limit,
                summary_overrides={},
            )
        except TemplateRenderError as error:
            return OperationResult.failure(error, warnings=aggregate_warnings)

        fallback_events.extend(self._materializer.consume_fallback_events())
        # Store the original blueprint (ContextBlueprint) for compatibility
        artifact = PreviewArtifact(
            blueprint=blueprint,
            rendered_context="",
            instruction_ids=[],
            fallback_events=fallback_events,
            file_first_markdown=result.markdown,
            file_first_metadata=result.metadata,
        )
        combined_warnings = aggregate_warnings + result.warnings
        return OperationResult.success(artifact, warnings=combined_warnings)

    def _resolve_instruction_text(
        self,
        refs: Sequence[InstructionNodeRef],
        instruction_ids: list[str],
        context: InstructionRenderContext,
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
            try:
                rendered = self._template_renderer.render(node, content, context)
                payloads.append(rendered)
            except PrompticError as e:
                # If rendering fails, we should probably fail the whole operation
                # or degrade gracefully depending on policy?
                # For now, returning error.
                return [], warnings, e
        return payloads, warnings, None

    @staticmethod
    def _ensure_error(error: PrompticError | None, message: str) -> PrompticError:
        return error if error else PrompticError(message)


__all__ = ["ContextPreviewer", "PreviewArtifact"]
