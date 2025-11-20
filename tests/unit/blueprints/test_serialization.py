from __future__ import annotations

from promptic.blueprints import BlueprintStep, ContextBlueprint, InstructionNodeRef
from promptic.blueprints.serialization import (
    FileFirstMetadata,
    build_reference_id,
    estimate_token_count,
    get_file_first_metadata,
    summary_overrides_from_metadata,
)


def _blueprint(metadata: dict | None = None) -> ContextBlueprint:
    return ContextBlueprint(
        name="Research Flow",
        prompt_template="You are a helpful agent.",
        steps=[
            BlueprintStep(
                step_id="collect",
                title="Collect Sources",
                kind="sequence",
                instruction_refs=[InstructionNodeRef(instruction_id="collect.md")],
                children=[
                    BlueprintStep(
                        step_id="summarize",
                        title="Summarize",
                        kind="sequence",
                        instruction_refs=[InstructionNodeRef(instruction_id="summarize.md")],
                    )
                ],
            )
        ],
        metadata=metadata or {},
    )


def test_get_file_first_metadata_uses_overrides() -> None:
    blueprint = _blueprint(
        metadata={
            "file_first": {
                "persona": "Curator",
                "objectives": ["Collect", "Summarize"],
                "summary_overrides": {"collect.md": "Short override"},
            }
        }
    )

    meta = get_file_first_metadata(blueprint)
    assert isinstance(meta, FileFirstMetadata)
    assert meta.persona == "Curator"
    assert meta.objectives == ["Collect", "Summarize"]
    assert meta.summary_overrides["collect.md"] == "Short override"


def test_get_file_first_metadata_falls_back_to_step_titles() -> None:
    blueprint = _blueprint(metadata={"file_first": {}})
    meta = get_file_first_metadata(blueprint)
    assert meta.persona == "Research Flow"
    assert meta.objectives == ["Collect Sources"]


def test_summary_overrides_normalize_paths() -> None:
    blueprint = _blueprint(
        metadata={
            "file_first": {
                "summary_overrides": {
                    "./instructions/collect.md": "Use dataset A",
                    "INSTRUCTIONS/summarize.MD": "Keep it short",
                }
            }
        }
    )
    overrides = summary_overrides_from_metadata(blueprint)
    assert overrides["instructions/collect.md"] == "Use dataset A"
    assert overrides["instructions/summarize.md"] == "Keep it short"


def test_build_reference_id_and_token_estimate() -> None:
    assert build_reference_id("instructions/Collect-Step.md") == "instructions_collect_step_md"
    assert estimate_token_count("hello world  here") == 3
