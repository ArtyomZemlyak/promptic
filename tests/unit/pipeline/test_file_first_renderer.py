from __future__ import annotations

import pytest

from promptic.blueprints import BlueprintStep, ContextBlueprint, InstructionNodeRef
from promptic.context.errors import InstructionNotFoundError, TemplateRenderError
from promptic.pipeline.format_renderers.file_first import (
    FileFirstRenderer,
    ReferenceFormatter,
    ReferenceTreeBuilder,
    SummaryResult,
)
from promptic.sdk.api import build_materializer
from promptic.settings.base import ContextEngineSettings


class StubSummaryService:
    def __init__(self) -> None:
        self.values: dict[str, SummaryResult] = {}

    def add(self, instruction_id: str, summary: str) -> None:
        self.values[instruction_id] = SummaryResult(
            instruction_id=instruction_id,
            reference_path=f"instructions/{instruction_id}",
            summary=summary,
            token_estimate=len(summary.split()),
        )

    def summarize(self, instruction_id: str, version: str | None = None) -> SummaryResult:
        if instruction_id not in self.values:
            raise InstructionNotFoundError(instruction_id)
        return self.values[instruction_id]


@pytest.fixture
def sample_blueprint() -> ContextBlueprint:
    return ContextBlueprint(
        name="Research Flow",
        prompt_template="N/A",
        steps=[
            BlueprintStep(
                step_id="collect",
                title="Collect Sources",
                kind="sequence",
                instruction_refs=[InstructionNodeRef(instruction_id="collect")],
                children=[
                    BlueprintStep(
                        step_id="summarize",
                        title="Summarize",
                        kind="sequence",
                        instruction_refs=[InstructionNodeRef(instruction_id="summarize")],
                    )
                ],
            )
        ],
    )


def test_reference_tree_builder_enforces_depth_limit(sample_blueprint: ContextBlueprint) -> None:
    service = StubSummaryService()
    service.add("collect", "Collect summary")
    service.add("summarize", "Summarize summary")
    builder = ReferenceTreeBuilder(
        blueprint=sample_blueprint,
        summary_service=service,
        formatter=ReferenceFormatter(),
        depth_limit=1,
    )

    result = builder.build()

    assert result.references[0].children == []
    assert "Depth limit" in result.warnings[0]


def test_reference_tree_builder_handles_cycles_and_missing(
    sample_blueprint: ContextBlueprint,
) -> None:
    # Introduce a naive cycle by pointing child back to parent
    sample_blueprint.steps[0].children.append(sample_blueprint.steps[0])
    service = StubSummaryService()
    service.add("collect", "Collect summary")
    formatter = ReferenceFormatter(base_url="https://example.com")
    builder = ReferenceTreeBuilder(
        blueprint=sample_blueprint,
        summary_service=service,
        formatter=formatter,
        depth_limit=3,
    )

    result = builder.build()

    assert result.references[0].detail_hint.startswith("See more:")
    assert "Cycle detected" in result.warnings[-1]
    assert result.missing_paths == ["summarize"]


def _setup_materializer(tmp_path):
    settings = ContextEngineSettings(
        blueprint_root=tmp_path / "blueprints",
        instruction_root=tmp_path / "instructions",
        log_root=tmp_path / "logs",
    )
    settings.ensure_directories()
    materializer = build_materializer(settings=settings)
    return settings, materializer


def _write_instruction(root, name: str, content: str) -> None:
    path = root / f"{name}.md"
    path.write_text(content, encoding="utf-8")


def _blueprint_with_metadata(metadata: dict | None = None) -> ContextBlueprint:
    return ContextBlueprint(
        name="Research Flow",
        prompt_template="N/A",
        steps=[
            BlueprintStep(
                step_id="collect",
                title="Collect Sources",
                kind="sequence",
                instruction_refs=[InstructionNodeRef(instruction_id="collect")],
                children=[
                    BlueprintStep(
                        step_id="summarize",
                        title="Summarize",
                        kind="sequence",
                        instruction_refs=[InstructionNodeRef(instruction_id="summarize")],
                    )
                ],
            )
        ],
        metadata=metadata or {},
    )


def test_file_first_renderer_truncates_summary_and_builds_metrics(tmp_path) -> None:
    settings, materializer = _setup_materializer(tmp_path)
    large_content = " ".join(["token"] * 200)
    _write_instruction(settings.instruction_root, "collect", large_content)
    _write_instruction(settings.instruction_root, "summarize", "short summary")
    blueprint = _blueprint_with_metadata(
        {
            "file_first": {
                "persona": "Curator",
                "objectives": ["Collect"],
            }
        }
    )

    renderer = FileFirstRenderer(max_summary_tokens=10)
    result = renderer.render(
        blueprint=blueprint,
        materializer=materializer,
        base_url=None,
        depth_limit=3,
        summary_overrides={},
    )

    assert result.metadata.persona == "Curator"
    assert result.metadata.steps[0].summary.endswith("...")
    assert result.metadata.metrics.reference_count == 2
    assert result.metadata.metrics.tokens_before > result.metadata.metrics.tokens_after


def test_file_first_renderer_raises_missing_file(tmp_path) -> None:
    settings, materializer = _setup_materializer(tmp_path)
    _write_instruction(settings.instruction_root, "collect", "content")
    blueprint = _blueprint_with_metadata()

    renderer = FileFirstRenderer()
    with pytest.raises(TemplateRenderError) as excinfo:
        renderer.render(
            blueprint=blueprint,
            materializer=materializer,
            base_url=None,
            depth_limit=2,
            summary_overrides={},
        )

    assert "Missing" in excinfo.value.message or "missing" in excinfo.value.message.lower()
