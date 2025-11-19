from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from promptic.blueprints.serialization import blueprint_json_schema
from promptic.context.errors import PrompticError
from promptic.instructions.cache import InstructionCache
from promptic.instructions.store import FilesystemInstructionStore
from promptic.pipeline.builder import BlueprintBuilder
from promptic.pipeline.context_materializer import ContextMaterializer
from promptic.pipeline.previewer import ContextPreviewer
from promptic.pipeline.validation import BlueprintValidator
from promptic.sdk.api import PreviewResponse, build_materializer
from promptic.settings.base import ContextEngineSettings


def preview_blueprint(
    *,
    blueprint_id: str,
    sample_data: Mapping[str, Any] | None = None,
    sample_memory: Mapping[str, Any] | None = None,
    settings: ContextEngineSettings | None = None,
    materializer: ContextMaterializer | None = None,
) -> PreviewResponse:
    runtime_settings = settings or ContextEngineSettings()
    runtime_settings.ensure_directories()
    builder = _build_builder(runtime_settings)
    preview_materializer = materializer or build_materializer(settings=runtime_settings)
    previewer = ContextPreviewer(builder=builder, materializer=preview_materializer)
    result = previewer.preview(
        blueprint_id=blueprint_id,
        sample_data=sample_data,
        sample_memory=sample_memory,
    )
    if not result.ok:
        error = result.error or PrompticError("Blueprint preview failed.")
        raise error
    artifact = result.unwrap()
    warnings = result.warnings
    return PreviewResponse(
        rendered_context=artifact.rendered_context,
        warnings=warnings,
        instruction_ids=artifact.instruction_ids,
        fallback_events=artifact.fallback_events,
    )


def list_blueprints(settings: ContextEngineSettings | None = None) -> Sequence[str]:
    runtime_settings = settings or ContextEngineSettings()
    builder = _build_builder(runtime_settings)
    return builder.list_blueprints()


def export_blueprint_schema(destination: Path | str | None = None) -> dict[str, Any]:
    schema = blueprint_json_schema()
    if destination:
        path = Path(destination)
        path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    return schema


def _build_builder(settings: ContextEngineSettings) -> BlueprintBuilder:
    instruction_store = InstructionCache(
        FilesystemInstructionStore(settings.instruction_root),
        max_entries=256,
    )
    validator = BlueprintValidator(settings=settings, instruction_store=instruction_store)
    return BlueprintBuilder(settings=settings, validator=validator)


__all__ = ["export_blueprint_schema", "list_blueprints", "preview_blueprint"]
