import pytest

from promptic.blueprints.models import BlueprintStep, ContextBlueprint, InstructionNode
from promptic.context.template_context import build_instruction_context
from promptic.pipeline.template_renderer import TemplateRenderer


@pytest.mark.parametrize(
    "items",
    [
        [{"title": "Source A", "url": "https://a"}, {"title": "Source B", "url": "https://b"}],
        [{"title": "Doc 1", "url": "https://doc"}],
    ],
)
def test_loop_iteration_context_renders_unique_content(items):
    renderer = TemplateRenderer()
    node = InstructionNode(
        instruction_id="loop-demo",
        source_uri="file://loop.md",
        format="md",
        checksum="0" * 32,
    )
    content = "Review: {step.loop_item.title} ({step.loop_item.url})"

    blueprint = ContextBlueprint(
        name="Loop Demo",
        prompt_template="Prompt",
        steps=[
            BlueprintStep(
                step_id="process_source",
                title="Process Source",
                kind="loop",
                loop_slot="sources",
                instruction_refs=[],
                children=[],
            )
        ],
    )

    rendered = []
    for item in items:
        context = build_instruction_context(
            blueprint=blueprint,
            data={"sources": items},
            memory={},
            step_id="process_source",
            loop_item=item,
        )
        rendered.append(renderer.render(node, content, context))

    assert len(rendered) == len(items)
    for output, item in zip(rendered, items):
        assert item["title"] in output
        assert item["url"] in output
