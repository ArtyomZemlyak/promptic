import time

from promptic.blueprints.models import InstructionNode
from promptic.context.template_context import InstructionRenderContext
from promptic.pipeline.template_renderer import TemplateRenderer


def test_markdown_rendering_stays_within_budget():
    renderer = TemplateRenderer()
    node = InstructionNode(
        instruction_id="perf-md",
        source_uri="file://perf.md",
        format="md",
        checksum="0" * 32,
    )
    content = "\n".join([f"- Item {i}: {{data.item_{i}.title}}" for i in range(10)])
    context = InstructionRenderContext(
        data={f"item_{i}": {"title": f"title-{i}"} for i in range(10)}
    )

    start = time.perf_counter()
    for _ in range(200):
        renderer.render(node, content, context)
    duration = time.perf_counter() - start

    assert duration < 1.0, f"Markdown rendering took {duration:.3f}s (>1.0s budget)"


def test_jinja_rendering_stays_within_budget():
    renderer = TemplateRenderer()
    node = InstructionNode(
        instruction_id="perf-jinja",
        source_uri="file://perf.jinja",
        format="jinja",
        checksum="0" * 32,
    )
    content = """
    {% for item in data.records %}
    - {{ loop.index }}. {{ item.title }}
    {% endfor %}
    """
    context = InstructionRenderContext(
        data={"records": [{"title": f"title-{i}"} for i in range(50)]}
    )

    start = time.perf_counter()
    for _ in range(100):
        renderer.render(node, content, context)
    duration = time.perf_counter() - start

    assert duration < 1.0, f"Jinja rendering took {duration:.3f}s (>1.0s budget)"
