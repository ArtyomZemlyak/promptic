from __future__ import annotations

import pytest
from pydantic import ValidationError

from promptic.blueprints import (
    BlueprintStep,
    ContextBlueprint,
    DataSlot,
    InstructionNodeRef,
    InstructionReference,
    MemoryChannel,
    MemorySlot,
    PromptHierarchyBlueprint,
    RenderMetrics,
)


def test_blueprint_enforces_unique_step_ids() -> None:
    step = BlueprintStep(step_id="collect", title="Collect", kind="sequence")
    with pytest.raises(ValidationError) as excinfo:
        ContextBlueprint(
            name="Research Flow",
            prompt_template="You are a helpful agent.",
            steps=[step, step],
        )
    assert "Duplicate step" in str(excinfo.value)


def test_loop_step_requires_loop_slot() -> None:
    with pytest.raises(ValidationError):
        BlueprintStep(step_id="loop", title="Loop", kind="loop")


def test_slot_lookup_helpers() -> None:
    blueprint = ContextBlueprint(
        name="Research Flow",
        prompt_template="You are a helpful agent.",
        steps=[
            BlueprintStep(
                step_id="collect",
                title="Collect",
                kind="sequence",
                instruction_refs=[InstructionNodeRef(instruction_id="collect.md")],
            )
        ],
        data_slots=[DataSlot(name="sources", adapter_key="csv_loader")],
        memory_slots=[MemorySlot(name="prior", provider_key="vector_db")],
    )

    assert blueprint.get_data_slot("sources").adapter_key == "csv_loader"
    assert blueprint.get_memory_slot("prior").provider_key == "vector_db"
    with pytest.raises(KeyError):
        blueprint.get_data_slot("missing")


def test_prompt_hierarchy_models_accept_nested_children() -> None:
    child = InstructionReference(
        id="instructions_child_md",
        title="Child Step",
        summary="Child summary",
        reference_path="instructions/child.md",
        detail_hint="Open instructions/child.md",
        token_estimate=20,
    )
    parent = InstructionReference(
        id="instructions_parent_md",
        title="Parent Step",
        summary="Parent summary",
        reference_path="instructions/parent.md",
        detail_hint="Open instructions/parent.md",
        token_estimate=40,
        children=[child],
    )
    metrics = RenderMetrics(tokens_before=200, tokens_after=80, reference_count=2)
    memory = MemoryChannel(location="memory/log.md", expected_format="Markdown bullets")
    blueprint = PromptHierarchyBlueprint(
        blueprint_id="demo",
        persona="Assistant",
        objectives=["Collect"],
        steps=[parent],
        memory_channels=[memory],
        metrics=metrics,
    )

    assert blueprint.metrics.tokens_before == 200
    assert blueprint.steps[0].children[0].id == "instructions_child_md"
