from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from promptic.blueprints.models import BlueprintStep, ContextBlueprint
    from promptic.context.nodes.models import NodeNetwork
else:
    from promptic.blueprints.models import ContextBlueprint


@dataclass
class StepContext:
    """Context information for the current execution step."""

    step_id: str
    title: str
    kind: str
    hierarchy: List[str] = field(default_factory=list)
    loop_item: Optional[Any] = None


@dataclass
class InstructionRenderContext:
    """
    Context object passed to renderers containing blueprint data, step information,
    and template variables.
    """

    data: Dict[str, Any] = field(default_factory=dict)
    memory: Dict[str, Any] = field(default_factory=dict)
    step: Optional[StepContext] = None
    blueprint: Dict[str, Any] = field(default_factory=dict)

    def get_template_variables(self) -> Dict[str, Any]:
        """Returns the namespaced dictionary for template rendering."""
        return {
            "data": self.data,
            "memory": self.memory,
            "step": self.step,
            "blueprint": self.blueprint,
        }


def build_instruction_context(
    blueprint: "ContextBlueprint | NodeNetwork",
    data: Dict[str, Any],
    memory: Dict[str, Any],
    step_id: Optional[str] = None,
    loop_item: Optional[Any] = None,
) -> InstructionRenderContext:
    """
    Constructs an InstructionRenderContext from blueprint, data slots, memory slots,
    and step information.

    # AICODE-NOTE: This function accepts both ContextBlueprint and NodeNetwork during
    #              migration. If NodeNetwork is provided, it converts to ContextBlueprint
    #              using the legacy adapter.
    """
    # Convert NodeNetwork to ContextBlueprint for compatibility during migration
    if not isinstance(blueprint, ContextBlueprint):
        from promptic.blueprints.adapters.legacy import network_to_blueprint

        blueprint = network_to_blueprint(blueprint)

    step_context: Optional[StepContext] = None

    if step_id:
        found_step, hierarchy = _find_step_and_hierarchy(blueprint.steps, step_id)
        if found_step:
            step_context = StepContext(
                step_id=found_step.step_id,
                title=found_step.title,
                kind=found_step.kind,
                hierarchy=hierarchy,
                loop_item=loop_item,
            )

    return InstructionRenderContext(
        data=data,
        memory=memory,
        step=step_context,
        blueprint=blueprint.model_dump(mode="json"),
    )


def _find_step_and_hierarchy(
    steps: List[BlueprintStep], target_id: str, current_hierarchy: Optional[List[str]] = None
) -> tuple[Optional[BlueprintStep], List[str]]:
    """Recursively finds a step and its hierarchy path."""
    if current_hierarchy is None:
        current_hierarchy = []

    for step in steps:
        if step.step_id == target_id:
            return step, current_hierarchy

        if step.children:
            found, hierarchy = _find_step_and_hierarchy(
                step.children, target_id, current_hierarchy + [step.step_id]
            )
            if found:
                return found, hierarchy

    return None, []
