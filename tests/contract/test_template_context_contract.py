from promptic.blueprints.models import BlueprintStep, ContextBlueprint, InstructionNode
from promptic.context.template_context import InstructionRenderContext, build_instruction_context
from promptic.pipeline.template_renderer import TemplateRenderer


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
