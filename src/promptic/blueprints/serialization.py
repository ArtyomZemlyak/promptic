from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, TextIO

import yaml

from promptic.blueprints.models import ContextBlueprint

TOKEN_REGEX = r"[^\s]+"
_TOKEN_PATTERN = re.compile(TOKEN_REGEX)
_REFERENCE_TOKEN_PATTERN = re.compile(r"[^a-z0-9]+")
_FILE_FIRST_KEY = "file_first"


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


@dataclass(frozen=True)
class FileFirstMetadata:
    """Normalized persona/objectives/overrides for file-first renders."""

    persona: str
    objectives: List[str]
    summary_overrides: Dict[str, str]


def get_file_first_metadata(blueprint: ContextBlueprint) -> FileFirstMetadata:
    """
    Extract normalized metadata used by the file-first renderer.

    # AICODE-NOTE: Metadata stays in the serialization layer so higher-level
    #              strategies consume immutable structures instead of digging
    #              through arbitrary blueprint dictionaries.
    """

    file_first_config = _ensure_mapping((blueprint.metadata or {}).get(_FILE_FIRST_KEY, {}))
    persona = _select_persona(blueprint, file_first_config)
    objectives = _select_objectives(blueprint, file_first_config)
    overrides = summary_overrides_from_metadata(blueprint)
    return FileFirstMetadata(persona=persona, objectives=objectives, summary_overrides=overrides)


def summary_overrides_from_metadata(blueprint: ContextBlueprint) -> Dict[str, str]:
    overrides = _ensure_mapping((blueprint.metadata or {}).get(_FILE_FIRST_KEY, {})).get(
        "summary_overrides", {}
    )
    normalized: Dict[str, str] = {}
    if isinstance(overrides, Mapping):
        for key, value in overrides.items():
            if not isinstance(value, str):
                continue
            normalized[_normalize_reference_key(str(key))] = value.strip()
    return normalized


def build_reference_id(reference_path: str) -> str:
    """Derive deterministic identifier (e.g., instructions_collect_md)."""

    normalized = _normalize_reference_key(reference_path)
    slug = _REFERENCE_TOKEN_PATTERN.sub("_", normalized)
    slug = slug.strip("_")
    if not slug:
        raise ValueError(f"Invalid reference path: {reference_path!r}")
    return slug


def estimate_token_count(text: str) -> int:
    """Lightweight token approximation used for RenderMetrics."""

    return len(_TOKEN_PATTERN.findall(text or ""))


def _write(destination: Path | str | TextIO, data: str) -> None:
    if isinstance(destination, (str, Path)):
        Path(destination).write_text(data, encoding="utf-8")
        return
    destination.write(data)


def _ensure_mapping(value: Any) -> Dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _select_persona(blueprint: ContextBlueprint, config: Mapping[str, Any]) -> str:
    persona = config.get("persona") or (blueprint.metadata or {}).get("persona")
    persona = (str(persona).strip() if persona else "").strip()
    if not persona:
        return blueprint.name
    return persona


def _select_objectives(blueprint: ContextBlueprint, config: Mapping[str, Any]) -> List[str]:
    raw = config.get("objectives")
    if isinstance(raw, Iterable) and not isinstance(raw, (str, bytes)):
        cleaned = [str(item).strip() for item in raw if str(item).strip()]
        if cleaned:
            return cleaned[:5]
    return [step.title for step in blueprint.steps[:5]]


def _normalize_reference_key(value: str) -> str:
    normalized = value.strip().lower().replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


__all__ = [
    "FileFirstMetadata",
    "blueprint_json_schema",
    "build_reference_id",
    "dump_blueprint",
    "estimate_token_count",
    "get_file_first_metadata",
    "load_blueprint",
    "summary_overrides_from_metadata",
]
