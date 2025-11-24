"""Prompt versioning system for filesystem-based version management."""

from pathlib import Path
from typing import Union

from promptic.versioning.adapters.scanner import VersionedFileScanner, VersionInfo
from promptic.versioning.domain.cleanup import VersionCleanup
from promptic.versioning.domain.errors import (
    CleanupTargetNotFoundError,
    ExportDirectoryConflictError,
    ExportDirectoryExistsError,
    ExportError,
    InvalidCleanupTargetError,
    VersionDetectionError,
    VersionNotFoundError,
    VersionResolutionCycleError,
)
from promptic.versioning.domain.exporter import ExportResult, VersionExporter
from promptic.versioning.domain.resolver import (
    HierarchicalVersionResolver,
    VersionResolver,
    VersionSpec,
)
from promptic.versioning.utils.semantic_version import SemanticVersion


def export_version(
    source_path: Union[str, Path],
    version_spec: VersionSpec,
    target_dir: Union[str, Path],
    overwrite: bool = False,
) -> ExportResult:
    """Export a complete version snapshot of a prompt hierarchy."""
    return VersionExporter().export_version(
        str(source_path), version_spec, str(target_dir), overwrite
    )


def cleanup_exported_version(
    export_dir: Union[str, Path], require_confirmation: bool = False
) -> None:
    """Clean up an exported version directory safely."""
    VersionCleanup().cleanup_exported_version(str(export_dir), require_confirmation)


__all__ = [
    "VersionNotFoundError",
    "VersionDetectionError",
    "VersionResolutionCycleError",
    "ExportError",
    "ExportDirectoryExistsError",
    "ExportDirectoryConflictError",
    "InvalidCleanupTargetError",
    "CleanupTargetNotFoundError",
    "VersionResolver",
    "HierarchicalVersionResolver",
    "VersionSpec",
    "VersionedFileScanner",
    "VersionInfo",
    "SemanticVersion",
    "VersionExporter",
    "ExportResult",
    "VersionCleanup",
    "export_version",
    "cleanup_exported_version",
]
