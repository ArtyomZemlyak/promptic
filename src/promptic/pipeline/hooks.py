from __future__ import annotations

from typing import Any, Mapping

from promptic.blueprints.models import BlueprintStep, ContextBlueprint


class PipelineHooks:
    """Extensibility points for pipeline execution."""

    def before_step(
        self,
        *,
        blueprint: ContextBlueprint,
        step: BlueprintStep,
        context: Mapping[str, Any],
    ) -> None:
        return

    def after_step(
        self,
        *,
        blueprint: ContextBlueprint,
        step: BlueprintStep,
        context: Mapping[str, Any],
    ) -> None:
        return

    def on_loop_item(
        self,
        *,
        blueprint: ContextBlueprint,
        step: BlueprintStep,
        item: Any,
        index: int,
    ) -> None:
        return


__all__ = ["PipelineHooks"]
