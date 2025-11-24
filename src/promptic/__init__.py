"""Promptic context engineering library."""

from importlib.metadata import PackageNotFoundError, version

from promptic.sdk.api import (
    bootstrap_runtime,
    cleanup_exported_version,
    export_version,
    load_blueprint,
    load_prompt,
    preview_blueprint,
    render_for_llm,
    render_instruction,
    render_preview,
)

try:  # pragma: no cover - best effort for local development
    __version__ = version("promptic")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "__version__",
    "bootstrap_runtime",
    "cleanup_exported_version",
    "export_version",
    "load_blueprint",
    "load_prompt",
    "preview_blueprint",
    "render_for_llm",
    "render_instruction",
    "render_preview",
]
