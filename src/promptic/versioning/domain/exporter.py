"""Version export use case for exporting complete version snapshots."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# Lazy import to avoid circular dependency
from typing import TYPE_CHECKING, Optional

from promptic.versioning.adapters.scanner import VersionedFileScanner
from promptic.versioning.domain.errors import ExportDirectoryExistsError, ExportError
from promptic.versioning.domain.resolver import VersionResolver, VersionSpec
from promptic.versioning.utils.logging import get_logger, log_version_operation

if TYPE_CHECKING:
    from promptic.versioning.adapters.filesystem_exporter import FileSystemExporter

logger = get_logger(__name__)


@dataclass
class ExportResult:
    """
    Result of version export operation.

    # AICODE-NOTE: This dataclass contains the results of an export operation,
    including the root prompt content (with resolved paths), list of exported
    files, and whether the hierarchical structure was preserved.
    """

    root_prompt_content: str
    exported_files: list[str]
    structure_preserved: bool


class VersionExporter:
    """
    Use case for exporting complete version snapshots of prompt hierarchies.

    # AICODE-NOTE: This use case orchestrates version export operations:
    # 1. Resolves version specifications to determine which files to export
    # 2. Discovers all referenced files in the prompt hierarchy
    # 3. Delegates filesystem operations to FileSystemExporter adapter
    # 4. Ensures atomic export behavior (all or nothing)
    # 5. Preserves hierarchical directory structure (not flattened)
    # 6. Resolves path references in file content to work in exported structure
    """

    def __init__(
        self,
        version_resolver: Optional[VersionResolver] = None,
        filesystem_exporter: Optional["FileSystemExporter"] = None,
    ) -> None:
        """
        Initialize version exporter.

        Args:
            version_resolver: Version resolver for resolving versions during export
            filesystem_exporter: Filesystem exporter adapter for filesystem operations
        """
        from promptic.versioning.adapters.filesystem_exporter import FileSystemExporter

        self.version_resolver = version_resolver or VersionedFileScanner()
        self.filesystem_exporter = filesystem_exporter or FileSystemExporter()

    def export_version(
        self,
        source_path: str,
        version_spec: VersionSpec,
        target_dir: str,
        overwrite: bool = False,
    ) -> ExportResult:
        """
        Export complete version snapshot of prompt hierarchy.

        # AICODE-NOTE: Export structure and behavior:
        # - Preserves hierarchical directory structure (not flattened)
        # - Resolves path references in file content to work in exported structure
        # - Atomic export: either all files export successfully or nothing is exported
        # - Returns root prompt content with resolved paths for immediate use

        Args:
            source_path: Source prompt hierarchy path
            version_spec: Version specification ("latest", "v1", or hierarchical dict)
            target_dir: Target export directory
            overwrite: Whether to overwrite existing target directory

        Returns:
            ExportResult with root prompt content and exported files

        Raises:
            ExportError: If export fails (missing files, permission errors)
            ExportDirectoryExistsError: If target directory exists without overwrite
        """
        source = Path(source_path)
        target = Path(target_dir)

        log_version_operation(
            logger,
            "export_started",
            version=str(version_spec),
            path=source_path,
            target=target_dir,
        )

        # Validate export target
        self.filesystem_exporter.validate_export_target(str(target), overwrite)

        # Resolve root prompt version
        if source.is_dir():
            resolved_root = self.version_resolver.resolve_version(str(source), version_spec)
        else:
            resolved_root = str(source)

        root_path = Path(resolved_root)
        if not root_path.exists():
            raise ExportError(
                source_path=source_path,
                missing_files=[resolved_root],
                message=f"Root prompt not found: {resolved_root}",
            )

        # Discover all files with the same version (recursive scan)
        source_base = source if source.is_dir() else source.parent
        all_versioned_files = self.discover_versioned_files(str(source_base), version_spec)

        # Build file mapping (source -> target) preserving structure
        file_mapping: dict[str, str] = {}

        # AICODE-NOTE: First, discover all explicitly referenced files from the root prompt
        # This ensures that explicit version references take precedence over automatic version resolution
        referenced_files = self.discover_referenced_files(str(root_path))
        referenced_base_names: dict[str, str] = (
            {}
        )  # Maps base name (without version) to actual referenced file

        # Process explicitly referenced files first
        for ref_file in referenced_files:
            ref_path = Path(ref_file)
            if not ref_path.exists():
                continue

            try:
                ref_relative = ref_path.relative_to(source_base)
            except ValueError:
                continue

            # Check if this is a versioned file
            version_suffix = self._extract_version_from_path(ref_path)
            if version_suffix:
                # This is an explicit reference to a versioned file
                # Keep the version suffix in the target name
                target_ref_file = target / ref_relative
                file_mapping[str(ref_path)] = str(target_ref_file)

                # Remember the base name (without version) to avoid adding automatic version
                base_name = ref_path.name.replace(version_suffix, "")
                base_path = ref_relative.parent / base_name
                referenced_base_names[str(base_path)] = str(ref_path)
            else:
                # Non-versioned file reference - add as is
                target_ref_file = target / ref_relative
                if str(ref_path) not in file_mapping:
                    file_mapping[str(ref_path)] = str(target_ref_file)

        # Now add all versioned files, but skip those that have explicit references
        for versioned_file in all_versioned_files:
            versioned_path = Path(versioned_file)
            if versioned_path.exists():
                # Get relative path to preserve directory structure
                try:
                    versioned_relative = versioned_path.relative_to(source_base)
                except ValueError:
                    # File is outside source_base, skip
                    continue

                # Remove version suffix from filename
                version_suffix = self._extract_version_from_path(versioned_path)
                if version_suffix:
                    new_name = versioned_path.name.replace(version_suffix, "")
                else:
                    new_name = versioned_path.name

                # Preserve subdirectory structure
                if versioned_relative.parent != Path("."):
                    target_file = target / versioned_relative.parent / new_name
                    base_path = versioned_relative.parent / new_name
                else:
                    target_file = target / new_name
                    base_path = Path(new_name)

                # Skip if there's an explicit reference to a different version of this file
                if str(base_path) in referenced_base_names:
                    if referenced_base_names[str(base_path)] != str(versioned_path):
                        # There's an explicit reference to a different version - skip this one
                        continue

                # Add to file mapping if not already present
                if str(versioned_path) not in file_mapping:
                    file_mapping[str(versioned_path)] = str(target_file)

        # Export files (atomic operation)
        try:
            exported_files = self.filesystem_exporter.export_files(
                list(file_mapping.keys()),
                str(target),
                preserve_structure=True,
                file_mapping=file_mapping,
            )

            # Resolve paths in root prompt content
            root_content = root_path.read_text(encoding="utf-8")
            resolved_content = self.filesystem_exporter.resolve_paths_in_file(
                root_content, file_mapping, str(source_base), str(target)
            )

            log_version_operation(
                logger,
                "export_completed",
                version=str(version_spec),
                path=source_path,
                exported_count=len(exported_files),
            )

            return ExportResult(
                root_prompt_content=resolved_content,
                exported_files=exported_files,
                structure_preserved=True,
            )

        except Exception as e:
            # Atomic export: if anything fails, clean up and raise error
            if target.exists():
                import shutil

                try:
                    shutil.rmtree(target)
                except Exception:
                    pass  # Best effort cleanup

            if isinstance(e, (ExportError, ExportDirectoryExistsError)):
                raise
            raise ExportError(
                source_path=source_path,
                missing_files=[],
                message=f"Export failed: {e}",
            ) from e

    def discover_versioned_files(self, source_dir: str, version_spec: VersionSpec) -> list[str]:
        """
        Discover all files with the specified version in directory hierarchy.

        # AICODE-NOTE: Version-aware file discovery:
        # - Recursively scans directory and subdirectories
        # - Finds all files matching the specified version
        # - Returns list of absolute file paths

        Args:
            source_dir: Source directory to scan
            version_spec: Version specification to match

        Returns:
            List of versioned file paths
        """
        # Use recursive scanning to find all versioned files
        if isinstance(self.version_resolver, VersionedFileScanner):
            all_files = self.version_resolver.scan_directory(source_dir, recursive=True)
        else:
            all_files = []

        # Extract the version from spec
        target_version = None
        if isinstance(version_spec, str):
            if version_spec == "latest":
                # Find latest version from all files
                versioned = [f for f in all_files if f.is_versioned and f.version]
                if versioned:
                    target_version = versioned[0].version  # Already sorted, latest first
            else:
                # Parse specific version
                if isinstance(self.version_resolver, VersionedFileScanner):
                    target_version = self.version_resolver.normalize_version(version_spec)
                else:
                    # Fallback: use the spec as-is
                    from promptic.versioning.utils.semantic_version import normalize_version

                    target_version = normalize_version(version_spec)

        # Filter files matching the target version
        if target_version:
            matching_files = [
                f.path for f in all_files if f.is_versioned and f.version == target_version
            ]
            return matching_files

        return []

    def discover_referenced_files(self, prompt_path: str) -> list[str]:
        """
        Discover all files referenced by the prompt hierarchy.

        # AICODE-NOTE: File discovery strategy:
        # - Parses file content for common reference patterns (markdown links, includes, etc.)
        # - Recursively discovers referenced files
        # - Returns list of absolute file paths

        Args:
            prompt_path: Path to root prompt file

        Returns:
            List of referenced file paths
        """
        discovered: set[str] = set()
        to_process: list[str] = [prompt_path]
        processed: set[str] = set()

        while to_process:
            current = to_process.pop(0)
            if current in processed:
                continue
            processed.add(current)

            path = Path(current)
            if not path.exists() or not path.is_file():
                continue

            # Read file content and extract references
            try:
                content = path.read_text(encoding="utf-8")
                references = self._extract_references(content, path)

                for ref in references:
                    if ref not in discovered:
                        discovered.add(ref)
                        to_process.append(ref)
            except Exception:
                # Skip files that can't be read
                continue

        return list(discovered)

    def _extract_references(self, content: str, base_path: Path) -> list[str]:
        """Extract file references from content."""
        references: list[str] = []
        base_dir = base_path.parent

        # Pattern for markdown links: [text](path/to/file.md)
        markdown_link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
        for match in markdown_link_pattern.finditer(content):
            ref_path = match.group(2)
            # Skip URLs and anchors
            if ref_path.startswith(("http://", "https://", "#")):
                continue
            resolved = (base_dir / ref_path).resolve()
            if resolved.exists() and resolved.is_file():
                references.append(str(resolved))

        # Pattern for include directives: @include(path/to/file.md) or include: path/to/file.md
        include_pattern = re.compile(r"(?:@include|include:)\s*\(?([^)]+)\)?", re.IGNORECASE)
        for match in include_pattern.finditer(content):
            ref_path = match.group(1).strip()
            resolved = (base_dir / ref_path).resolve()
            if resolved.exists() and resolved.is_file():
                references.append(str(resolved))

        return references

    def _extract_version_from_path(self, path: Path) -> str:
        """Extract version string from file path for replacement."""
        name = path.stem
        version_match = re.search(r"_v(\d+(?:\.\d+)*(?:\.\d+)?)", name)
        if version_match:
            return version_match.group(0)
        return ""
