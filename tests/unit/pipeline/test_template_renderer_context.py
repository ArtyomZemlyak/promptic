import textwrap

import pytest

from promptic.context.template_context import InstructionRenderContext, StepContext


@pytest.fixture
def renderer():
    try:
        from promptic.pipeline.format_renderers.jinja2 import Jinja2FormatRenderer
    except ImportError:
        pytest.skip("Jinja2FormatRenderer not implemented yet")
    return Jinja2FormatRenderer()


def test_namespaced_context_variables_are_accessible(renderer):
    content = textwrap.dedent(
        """
        Data: {{ data.key }}
        Memory: {{ memory.history }}
        Step: {{ step.title }}
        Blueprint: {{ blueprint.name }}
        """
    )
    context = InstructionRenderContext(
        data={"key": "value"},
        memory={"history": "log"},
        step=StepContext(step_id="s1", title="Step 1", kind="sequence"),
        blueprint={"name": "My Blueprint"},
    )

    result = renderer.render(content, context)
    assert "Data: value" in result
    assert "Memory: log" in result
    assert "Step: Step 1" in result
    assert "Blueprint: My Blueprint" in result


def test_loop_item_exposed_in_step_namespace(renderer):
    content = textwrap.dedent(
        """
        Current Item: {{ step.loop_item.title }} ({{ step.loop_item.index }})
        """
    ).strip()
    step_context = StepContext(
        step_id="loop-step",
        title="Loop Step",
        kind="loop",
        hierarchy=["parent"],
        loop_item={"title": "Source 1", "index": 0},
    )
    context = InstructionRenderContext(step=step_context)

    result = renderer.render(content, context)

    assert "Current Item: Source 1 (0)" in result
