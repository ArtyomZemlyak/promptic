from __future__ import annotations

from pathlib import Path
from typing import Any, TextIO

import yaml

from promptic.blueprints.models import ContextBlueprint


def load_blueprint(source: Path | str | TextIO) -> ContextBlueprint:
    """Load a blueprint from a YAML file or text stream."""

    text = _read(source)
    payload = yaml.safe_load(text) or {}
    return ContextBlueprint.model_validate(payload)


def dump_blueprint(blueprint: ContextBlueprint, destination: Path | str | TextIO) -> None:
    """Persist a blueprint to YAML (stable ordering for diffs)."""

    serialized = yaml.safe_dump(
        blueprint.model_dump(mode="json"),
        sort_keys=False,
        allow_unicode=False,
    )
    _write(destination, serialized)


def blueprint_json_schema() -> dict[str, Any]:
    """
    Return the ContextBlueprint JSON Schema for tooling.

    # AICODE-NOTE: Pydantic already does the heavy lifting; we simply expose a helper
    #              so docs/tests can assert schema stability.
    """

    return ContextBlueprint.model_json_schema()


def _read(source: Path | str | TextIO) -> str:
    if isinstance(source, (str, Path)):
        return Path(source).read_text(encoding="utf-8")
    return source.read()


def _write(destination: Path | str | TextIO, data: str) -> None:
    if isinstance(destination, (str, Path)):
        Path(destination).write_text(data, encoding="utf-8")
        return
    destination.write(data)


__all__ = ["blueprint_json_schema", "dump_blueprint", "load_blueprint"]
