from __future__ import annotations

from typing import List

from promptic.blueprints.models import BlueprintStep
from promptic.settings.base import ContextEngineSettings


class PolicyEngine:
    """Evaluates per-step policies such as size budgets."""

    def __init__(self, *, settings: ContextEngineSettings) -> None:
        self.settings = settings

    def evaluate_step_budget(self, step: BlueprintStep, text: str) -> List[str]:
        limit = self.settings.size_budget.per_step_budget_chars
        if len(text) <= limit:
            return []
        return [
            f"Step '{step.step_id}' exceeded per-step budget ({len(text)} > {limit}).",
        ]


__all__ = ["PolicyEngine"]
