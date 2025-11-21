from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from promptic.blueprints.serialization import blueprint_json_schema
from promptic.context.errors import PrompticError
from promptic.context.nodes.models import NodeNetwork
from promptic.instructions.cache import InstructionCache
from promptic.instructions.store import FilesystemInstructionStore
from promptic.pipeline.builder import BlueprintBuilder
from promptic.pipeline.context_materializer import ContextMaterializer
from promptic.pipeline.previewer import ContextPreviewer
from promptic.pipeline.validation import BlueprintValidator
from promptic.sdk.api import PreviewResponse, build_materializer
from promptic.sdk.api import load_blueprint as api_load_blueprint
from promptic.sdk.api import render_for_llm as api_render_for_llm
from promptic.settings.base import ContextEngineSettings


def load_blueprint(
    blueprint_id_or_path: str | Path,
    *,
    settings: ContextEngineSettings | None = None,
) -> NodeNetwork:
    """Load a blueprint as a node network with automatic dependency resolution.

    # AICODE-NOTE: This function delegates to api.load_blueprint() which uses
    #              the unified ContextNode architecture. It loads blueprints
    #              as NodeNetwork instances, enabling format-agnostic
    #              composition and recursive node structures.
    """
    return api_load_blueprint(blueprint_id_or_path, settings=settings)


def preview_blueprint(
    *,
    blueprint_id: str,
    sample_data: Mapping[str, Any] | None = None,
    sample_memory: Mapping[str, Any] | None = None,
    settings: ContextEngineSettings | None = None,
    materializer: ContextMaterializer | None = None,
    print_to_console: bool = True,
    render_mode: str = "inline",
    base_url: str | None = None,
    depth_limit: int | None = None,
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
        print_to_console=print_to_console,
        render_mode=render_mode,
        base_url=base_url,
        depth_limit=depth_limit,
    )
    if not result.ok:
        error = result.error or PrompticError("Blueprint preview failed.")
        raise error
    artifact = result.unwrap()
    warnings = result.warnings
    metadata = (
        artifact.file_first_metadata.model_dump(mode="json")
        if artifact.file_first_metadata
        else None
    )
    return PreviewResponse(
        rendered_context=artifact.rendered_context,
        markdown=artifact.file_first_markdown,
        metadata=metadata,
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
    # AICODE-NOTE: BlueprintBuilder no longer requires validator during migration
    #              to NodeNetwork architecture. Validation is handled by NodeNetworkBuilder.
    return BlueprintBuilder(settings=settings, validator=None)


def render_for_llm(
    blueprint: NodeNetwork,
    *,
    sample_data: Mapping[str, Any] | None = None,
    sample_memory: Mapping[str, Any] | None = None,
    settings: ContextEngineSettings | None = None,
    materializer: ContextMaterializer | None = None,
) -> str:
    """Render plain text context ready for LLM input from a NodeNetwork.

    # AICODE-NOTE: This function is part of the migration to unified ContextNode
    #              architecture. It works with NodeNetwork instead of ContextBlueprint.
    #              The implementation currently delegates to api.render_for_llm() but
    #              will be fully migrated to use NodeNetwork directly.
    """
    # TODO: T077 - Fully migrate to use NodeNetwork directly without ContextBlueprint
    # For now, delegate to api.py which may still use ContextBlueprint internally
    # This is a temporary bridge during migration
    from promptic.sdk.nodes import render_node_network

    return render_node_network(blueprint, target_format="markdown")


__all__ = [
    "export_blueprint_schema",
    "list_blueprints",
    "preview_blueprint",
    "load_blueprint",
    "render_for_llm",
]
