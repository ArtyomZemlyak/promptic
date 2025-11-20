from pathlib import Path

from promptic.blueprints.models import (
    BlueprintStep,
    ContextBlueprint,
    InstructionNode,
    InstructionNodeRef,
)
from promptic.context.template_context import InstructionRenderContext, build_instruction_context
from promptic.pipeline.template_renderer import TemplateRenderer
from promptic.sdk.api import build_materializer
from promptic.settings.base import ContextEngineSettings


def test_template_context_exposes_all_namespaces():
    blueprint = ContextBlueprint(
        name="Contract Blueprint",
        prompt_template="Prompt",
        steps=[
            BlueprintStep(
                step_id="analyze",
                title="Analyze",
                kind="sequence",
                instruction_refs=[],
                children=[],
            )
        ],
    )
    data = {"user": {"name": "Ada"}}
    memory = {"owner": "ops-team"}
    context = build_instruction_context(
        blueprint=blueprint,
        data=data,
        memory=memory,
        step_id="analyze",
    )
    variables = context.get_template_variables()

    assert variables["data"]["user"]["name"] == "Ada"
    assert variables["memory"]["owner"] == "ops-team"
    assert variables["blueprint"]["name"] == "Contract Blueprint"
    assert variables["step"].step_id == "analyze"

    node = InstructionNode(
        instruction_id="contract-md",
        source_uri="file://contract.md",
        format="md",
        checksum="0" * 32,
    )
    renderer = TemplateRenderer()
    content = (
        "User: {data.user.name}\n"
        "Owner: {memory.owner}\n"
        "Step: {step.step_id}\n"
        "Blueprint: {blueprint.name}"
    )
    rendered = renderer.render(node, content, context)

    assert "User: Ada" in rendered
    assert "Owner: ops-team" in rendered
    assert "Step: analyze" in rendered
    assert "Blueprint: Contract Blueprint" in rendered


def test_file_first_contract_schema(tmp_path: Path) -> None:
    instruction_root = tmp_path / "instructions"
    instruction_root.mkdir()
    (instruction_root / "collect.md").write_text("Collect " * 50, encoding="utf-8")
    settings = ContextEngineSettings(
        blueprint_root=tmp_path / "blueprints",
        instruction_root=instruction_root,
        log_root=tmp_path / "logs",
    )
    settings.ensure_directories()
    materializer = build_materializer(settings=settings)
    blueprint = ContextBlueprint(
        name="Contract Blueprint",
        prompt_template="Prompt",
        steps=[
            BlueprintStep(
                step_id="collect",
                title="Collect",
                kind="sequence",
                instruction_refs=[],
                children=[
                    BlueprintStep(
                        step_id="summary",
                        title="Summary",
                        kind="sequence",
                        instruction_refs=[InstructionNodeRef(instruction_id="collect")],
                    )
                ],
            )
        ],
        metadata={"file_first": {"persona": "Persona", "objectives": ["Goal"]}},
    )

    renderer = TemplateRenderer()
    result = renderer.render_file_first(
        blueprint=blueprint,
        materializer=materializer,
        base_url="https://example.com/docs",
        depth_limit=2,
        summary_overrides={},
    )

    payload = result.metadata.model_dump(mode="json")
    assert payload["steps"][0]["reference_path"].startswith("https://example.com/docs")
    assert "metrics" in payload and payload["metrics"]["reference_count"] == len(payload["steps"])
    assert "memory_channels" in payload
