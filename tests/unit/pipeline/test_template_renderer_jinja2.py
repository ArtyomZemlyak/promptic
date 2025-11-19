import textwrap

import pytest
from jinja2 import Environment, StrictUndefined

from promptic.context.template_context import InstructionRenderContext, StepContext


@pytest.fixture
def renderer():
    try:
        from promptic.pipeline.format_renderers.jinja2 import Jinja2FormatRenderer
    except ImportError:
        pytest.skip("Jinja2FormatRenderer not implemented yet")
    return Jinja2FormatRenderer()


def test_renders_conditionals_loops_and_filters(renderer):
    content = textwrap.dedent(
        """
        Task: {{ data.task | upper }}
        {% if data.urgent %}PRIORITY: HIGH{% endif %}
        Steps:
        {% for step_name in data.steps %}
        - {{ loop.index }}. {{ step_name }}
        {% endfor %}
        Owner: {{ memory.owner }}
        Step: {{ format_step(step) }}
        """
    ).strip()

    context = InstructionRenderContext(
        data={"task": "deploy", "urgent": True, "steps": ["build", "test", "release"]},
        memory={"owner": "ops"},
        step=StepContext(step_id="process", title="Process Items", kind="sequence"),
    )

    result = renderer.render(content, context)

    assert "Task: DEPLOY" in result
    assert "PRIORITY: HIGH" in result
    assert "- 1. build" in result
    assert "- 3. release" in result
    assert "Owner: ops" in result
    assert "Step: [process] Process Items" in result


def test_environment_configuration(renderer):
    env = renderer.env
    assert isinstance(env, Environment)
    assert env.undefined is StrictUndefined
    assert env.autoescape is False
    assert env.keep_trailing_newline is True
    assert "format_step" in env.filters
    assert "get_parent_step" in env.globals

    # Lazy initialization returns the same environment per renderer
    assert renderer.env is env

    other_renderer = type(renderer)()
    assert other_renderer.env is not env
