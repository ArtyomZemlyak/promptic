from __future__ import annotations

from typing import Iterable, List, Set

from promptic.blueprints.models import BlueprintStep, ContextBlueprint
from promptic.context.errors import BlueprintValidationError, OperationResult
from promptic.instructions.store import InstructionStore
from promptic.settings.base import ContextEngineSettings


class BlueprintValidator:
    """Runs structural validations against ContextBlueprint instances."""

    def __init__(
        self,
        *,
        settings: ContextEngineSettings,
        instruction_store: InstructionStore | None = None,
    ) -> None:
        self.settings = settings
        self._store = instruction_store

    def validate(self, blueprint: ContextBlueprint) -> OperationResult[ContextBlueprint]:
        errors: List[str] = []
        warnings: List[str] = []

        depth = self._max_depth(blueprint.steps)
        max_allowed = self.settings.size_budget.max_step_depth
        if depth > max_allowed:
            errors.append(f"Blueprint depth ({depth}) exceeds permitted depth ({max_allowed}).")
        elif depth == max_allowed:
            warnings.append(
                "Blueprint depth equals configured maximum; nested updates may fail validation."
            )

        prompt_len = len(blueprint.prompt_template)
        if prompt_len > self.settings.size_budget.max_context_chars:
            errors.append(
                "Prompt template exceeds configured max_context_chars "
                f"({prompt_len} > {self.settings.size_budget.max_context_chars})."
            )

        missing_instructions = self._missing_instructions(blueprint)
        if missing_instructions:
            errors.append(
                f"Instruction assets missing for ids: {', '.join(sorted(missing_instructions))}"
            )

        if errors:
            return OperationResult.failure(
                BlueprintValidationError("; ".join(errors)),
                warnings=warnings,
            )
        return OperationResult.success(blueprint, warnings=warnings)

    def _missing_instructions(self, blueprint: ContextBlueprint) -> Set[str]:
        if not self._store:
            return set()
        instruction_ids = {ref.instruction_id for ref in blueprint.global_instructions}
        instruction_ids.update(self._collect_step_instruction_ids(blueprint.steps))
        missing = {
            instruction_id
            for instruction_id in instruction_ids
            if not self._store.exists(instruction_id)
        }
        return missing

    @staticmethod
    def _collect_step_instruction_ids(steps: Iterable[BlueprintStep]) -> List[str]:
        collected: List[str] = []
        for step in steps:
            collected.extend(ref.instruction_id for ref in step.instruction_refs)
            collected.extend(BlueprintValidator._collect_step_instruction_ids(step.children))
        return collected

    @staticmethod
    def _max_depth(steps: Iterable[BlueprintStep], current: int = 1) -> int:
        depth = current
        for step in steps:
            child_depth = BlueprintValidator._max_depth(step.children, current + 1)
            depth = max(depth, child_depth)
        return depth


__all__ = ["BlueprintValidator"]
