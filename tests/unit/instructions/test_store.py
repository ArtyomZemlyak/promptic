from __future__ import annotations

from pathlib import Path

from promptic.blueprints import BlueprintStep, ContextBlueprint, InstructionNodeRef
from promptic.instructions.store import FilesystemInstructionStore, MemoryDescriptorCollector


def test_filesystem_store_exposes_raw_helpers(tmp_path: Path) -> None:
    instruction_root = tmp_path / "instructions"
    instruction_root.mkdir()
    (instruction_root / "collect.md").write_text("Collect", encoding="utf-8")
    (instruction_root / "memory").mkdir()
    (instruction_root / "memory" / "format.md").write_text("Memory format", encoding="utf-8")

    store = FilesystemInstructionStore(instruction_root)

    node = store.get_node("collect")
    assert store.resolve_path("collect").exists()
    assert store.read_raw("memory/format.md") == "Memory format"
    assert store.path_exists("memory/format.md")
    assert node.source_uri.endswith("collect.md")


def test_memory_descriptor_collector_uses_metadata(tmp_path: Path) -> None:
    instruction_root = tmp_path / "instructions"
    instruction_root.mkdir()
    collector = MemoryDescriptorCollector(instruction_root=instruction_root)
    blueprint = ContextBlueprint(
        name="Memory Blueprint",
        prompt_template="Prompt",
        steps=[
            BlueprintStep(
                step_id="only",
                title="Only",
                kind="sequence",
                instruction_refs=[InstructionNodeRef(instruction_id="collect")],
            )
        ],
        metadata={
            "file_first": {
                "memory_channels": [
                    {
                        "location": "memory/log.md",
                        "expected_format": "Markdown bullets",
                        "format_descriptor_path": "memory/format.md",
                        "retention_policy": "Keep for 7 days.",
                        "usage_examples": ["Observation: ..."],
                    }
                ]
            }
        },
    )

    channels = collector.collect(blueprint)

    assert channels[0].location == "memory/log.md"
    assert channels[0].expected_format == "Markdown bullets"
    assert channels[0].usage_examples == ["Observation: ..."]


def test_memory_descriptor_collector_defaults_to_template(tmp_path: Path) -> None:
    instruction_root = tmp_path / "instructions"
    (instruction_root / "memory").mkdir(parents=True)
    (instruction_root / "memory" / "format.md").write_text("Template", encoding="utf-8")
    collector = MemoryDescriptorCollector(instruction_root=instruction_root)
    blueprint = ContextBlueprint(
        name="Default Memory",
        prompt_template="Prompt",
        steps=[
            BlueprintStep(
                step_id="step",
                title="Step",
                kind="sequence",
                instruction_refs=[InstructionNodeRef(instruction_id="collect")],
            )
        ],
    )

    channels = collector.collect(blueprint)

    assert channels
    assert channels[0].format_descriptor_path == "memory/format.md"
