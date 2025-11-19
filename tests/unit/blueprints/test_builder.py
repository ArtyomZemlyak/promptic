from __future__ import annotations

from pathlib import Path

from promptic.context import BlueprintValidationError
from promptic.instructions.store import FilesystemInstructionStore
from promptic.pipeline.builder import BlueprintBuilder
from promptic.pipeline.validation import BlueprintValidator
from promptic.settings.base import ContextEngineSettings


def _make_builder(tmp_path: Path) -> tuple[BlueprintBuilder, Path]:
    blueprint_root = tmp_path / "blueprints"
    instruction_root = tmp_path / "instructions"
    blueprint_root.mkdir()
    instruction_root.mkdir()
    (instruction_root / "intro.md").write_text("Intro", encoding="utf-8")
    settings = ContextEngineSettings(
        blueprint_root=blueprint_root,
        instruction_root=instruction_root,
        log_root=tmp_path / "logs",
    )
    validator = BlueprintValidator(
        settings=settings,
        instruction_store=FilesystemInstructionStore(instruction_root),
    )
    builder = BlueprintBuilder(settings=settings, validator=validator)
    return builder, blueprint_root


def test_builder_loads_blueprint(tmp_path: Path) -> None:
    builder, root = _make_builder(tmp_path)
    root.joinpath("demo.yaml").write_text(
        """
name: Demo Flow
prompt_template: Hello
steps:
  - step_id: intro
    title: Intro
    kind: sequence
""",
        encoding="utf-8",
    )

    result = builder.load("demo")
    assert result.ok
    blueprint = result.unwrap()
    assert blueprint.name == "Demo Flow"


def test_builder_missing_file_returns_failure(tmp_path: Path) -> None:
    builder, _ = _make_builder(tmp_path)
    result = builder.load("missing")
    assert not result.ok
    assert "missing" in str(result.error)


def test_builder_reports_validation_errors(tmp_path: Path) -> None:
    builder, root = _make_builder(tmp_path)
    root.joinpath("invalid.yaml").write_text(
        """
name: Invalid
prompt_template: Hello
steps:
  - step_id: intro
    title: Intro
    kind: sequence
  - step_id: intro
    title: Duplicate
    kind: sequence
""",
        encoding="utf-8",
    )

    result = builder.load("invalid")
    assert not result.ok
    assert isinstance(result.error, BlueprintValidationError)
