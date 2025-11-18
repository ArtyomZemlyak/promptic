from __future__ import annotations

import pytest
from pydantic import ValidationError

from promptic.blueprints import (
    BlueprintStep,
    ContextBlueprint,
    DataSlot,
    InstructionNodeRef,
    MemorySlot,
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
