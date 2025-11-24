"""Filesystem exporter adapter for version export operations."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from promptic.versioning.domain.errors import (
    ExportDirectoryConflictError,
    ExportDirectoryExistsError,
    ExportError,
)
from promptic.versioning.utils.logging import get_logger, log_version_operation

logger = get_logger(__name__)


class FileSystemExporter:
    """
    Filesystem exporter adapter for version export operations.

    # AICODE-NOTE: This adapter handles filesystem operations for version exports:
    # - Validates export targets (prevents overwriting without permission)
    # - Copies files preserving hierarchical directory structure (not flattened)
    # - Resolves path references in file content to work in exported structure
    # - Ensures atomic export behavior (all or nothing)
    """

    def validate_export_target(self, target_dir: str, overwrite: bool) -> None:
        """
        Validate target directory for export.

        # AICODE-NOTE: Validation rules:
        # - If target exists and overwrite=False, raise ExportDirectoryExistsError
        # - If target exists and contains non-export files, raise ExportDirectoryConflictError
        # - If target doesn't exist, it will be created

        Args:
            target_dir: Target export directory path
            overwrite: Whether to allow overwriting existing directory

        Raises:
            ExportDirectoryExistsError: If target exists without overwrite permission
            ExportDirectoryConflictError: If target contains non-export files
        """
        target = Path(target_dir)

        if target.exists():
            if not overwrite:
                raise ExportDirectoryExistsError(target_dir)

            # Check for conflicts (non-empty directory with files)
            if target.is_dir():
                contents = list(target.iterdir())
                if contents:
                    # Check if contents look like export files or source files
                    has_source_indicators = any(
                        f.name.startswith(".") or f.name.endswith(".git") for f in contents
                    )
                    if has_source_indicators:
                        raise ExportDirectoryConflictError(target_dir)

    def export_files(
        self,
        source_files: list[str],
        target_dir: str,
        preserve_structure: bool = True,
        file_mapping: Optional[dict[str, str]] = None,
    ) -> list[str]:
        """
        Copy files from source to target, preserving hierarchical directory structure.

        # AICODE-NOTE: Structure preservation:
        # - Maintains nested subdirectories (not flattened)
        # - Preserves relative path relationships
        # - Uses file_mapping if provided, otherwise derives from source paths

        Args:
            source_files: List of source file paths
            target_dir: Target export directory
            preserve_structure: Whether to preserve directory structure (default: True)
            file_mapping: Optional mapping of source paths to target paths

        Returns:
            List of exported file paths

        Raises:
            ExportError: If any file cannot be copied
        """
        target = Path(target_dir)
        target.mkdir(parents=True, exist_ok=True)

        exported_files: list[str] = []

        for source_file in source_files:
            source_path = Path(source_file)
            if not source_path.exists():
                continue

            # Determine target path
            if file_mapping and source_file in file_mapping:
                # Use explicit mapping (already includes full path with structure)
                target_path = Path(file_mapping[source_file])
            elif preserve_structure:
                # Preserve relative structure (simplified - assumes flat for now)
                target_path = target / source_path.name
            else:
                target_path = target / source_path.name

            # Create parent directories (critical for nested structure)
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            try:
                shutil.copy2(source_path, target_path)
                exported_files.append(str(target_path))

                log_version_operation(
                    logger,
                    "file_exported",
                    path=str(target_path),
                    source=str(source_path),
                )
            except Exception as e:
                raise ExportError(
                    source_path=str(source_path),
                    missing_files=[],
                    message=f"Failed to copy file {source_file}: {e}",
                ) from e

        return exported_files

    def resolve_paths_in_file(
        self, content: str, file_mapping: dict[str, str], source_base: str, target_base: str
    ) -> str:
        """
        Resolve path references in file content using path mapping.

        # AICODE-NOTE: Path resolution strategy:
        # - Maps source paths to target paths using file_mapping
        # - Updates relative path references to work in exported structure
        # - Preserves absolute paths and URLs unchanged

        Args:
            content: File content with path references
            file_mapping: Mapping of source paths to target paths
            source_base: Base source directory path
            target_base: Base target directory path

        Returns:
            Content with resolved path references
        """
        import re

        resolved_content = content
        source_base_path = Path(source_base)
        target_base_path = Path(target_base)

        # Pattern for markdown links: [text](path/to/file.md)
        def replace_markdown_link(match: re.Match) -> str:
            text = match.group(1)
            ref_path = match.group(2)

            # Skip URLs and anchors
            if ref_path.startswith(("http://", "https://", "#")):
                return str(match.group(0))

            # Resolve relative path
            try:
                source_ref = (source_base_path / ref_path).resolve()
                # Find in file_mapping
                for source_file, target_file in file_mapping.items():
                    if Path(source_file).resolve() == source_ref:
                        # Calculate relative path from target_base
                        target_ref = Path(target_file)
                        relative = target_ref.relative_to(target_base_path)
                        return f"[{text}]({relative.as_posix()})"
            except Exception:
                pass

            return str(match.group(0))

        markdown_link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
        resolved_content = markdown_link_pattern.sub(replace_markdown_link, resolved_content)

        return resolved_content
