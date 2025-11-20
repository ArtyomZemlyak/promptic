from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from promptic.context.errors import InstructionNotFoundError
from promptic.sdk import api
from promptic.settings.base import ContextEngineSettings


def test_preview_blueprint_safe_wraps_promptic_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """SDK helper should convert low-level exceptions into structured results."""

    def _boom(**_: Any) -> api.PreviewResponse:
        raise InstructionNotFoundError("missing.md")

    monkeypatch.setattr(api, "preview_blueprint", _boom)

    result = api.preview_blueprint_safe(blueprint_id="demo")

    assert result.response is None
    assert result.error is not None
    assert result.error.code == "INSTRUCTION_NOT_FOUND"
    assert "missing.md" in result.error.message


def test_bootstrap_runtime_ensures_directories(tmp_path: Path) -> None:
    """Runtime helper wires settings and materializer together."""

    settings = ContextEngineSettings(
        blueprint_root=tmp_path / "blueprints",
        instruction_root=tmp_path / "instructions",
        log_root=tmp_path / "logs",
    )

    runtime = api.bootstrap_runtime(settings=settings)

    assert runtime.settings.blueprint_root.exists()
    assert runtime.settings.instruction_root.exists()
    assert runtime.materializer is not None
