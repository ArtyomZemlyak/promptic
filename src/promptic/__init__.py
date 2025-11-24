"""Promptic context engineering library - simplified after cleanup.

# AICODE-NOTE: Blueprint system removed (spec 006-remove-unused-code) - not used in examples 003-006.
#              The library now focuses solely on:
#              1. Node networks (load_node_network, render_node_network in sdk.nodes)
#              2. Versioning (load_prompt, export_version, cleanup_exported_version)
#
#              Removed functions (now raise ImportError):
#              - bootstrap_runtime: Blueprint runtime initialization
#              - load_blueprint: Blueprint loading (use node networks instead)
#              - preview_blueprint: Blueprint preview (use node network rendering)
#              - render_for_llm: Blueprint rendering (use render_node_network)
#              - render_instruction: Blueprint instruction rendering
#              - render_preview: Blueprint console preview
#
#              Migration: Use node networks (examples/get_started/3-multiple-files/)
#              instead of blueprints for hierarchical file loading and rendering.
"""

from importlib.metadata import PackageNotFoundError, version

from promptic.sdk.api import cleanup_exported_version, export_version, load_prompt

try:  # pragma: no cover - best effort for local development
    __version__ = version("promptic")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "__version__",
    "cleanup_exported_version",
    "export_version",
    "load_prompt",
]
