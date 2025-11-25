"""Version export use case for exporting complete version snapshots."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# Lazy import to avoid circular dependency
from typing import TYPE_CHECKING, Any, Optional

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
        vars: Optional[dict[str, Any]] = None,
    ) -> ExportResult:
        """
        Export complete version snapshot of prompt hierarchy.

        # AICODE-NOTE: This method orchestrates the export process using helper methods:
        # 1. _validate_and_resolve_root() - validates target and resolves root file
        # 2. _build_file_mapping() - builds source->target file mapping
        # 3. _create_content_processor() - creates processor for path resolution and vars
        # 4. _execute_export() - performs atomic export with cleanup on failure

        Args:
            source_path: Source prompt hierarchy path
            version_spec: Version specification ("latest", "v1", or hierarchical dict)
            target_dir: Target export directory
            overwrite: Whether to overwrite existing target directory
            vars: Optional variables for substitution

        Returns:
            ExportResult with root prompt content and exported files

        Raises:
            ExportError: If export fails (missing files, permission errors)
            ExportDirectoryExistsError: If target directory exists without overwrite
        """
        target = Path(target_dir)

        log_version_operation(
            logger, "export_started", version=str(version_spec), path=source_path, target=target_dir
        )

        # Validate export target
        self.filesystem_exporter.validate_export_target(str(target), overwrite)

        # Step 1: Validate and resolve root
        resolved_root, source_base = self._validate_and_resolve_root(
            source_path, version_spec, target
        )
        root_path = Path(resolved_root)

        # Step 2: Build hierarchical paths if vars present
        hierarchical_paths = self._build_hierarchical_paths(str(root_path)) if vars else {}

        # Step 3: Build file mapping
        file_mapping = self._build_file_mapping(root_path, source_base, target, version_spec)

        # Step 4: Create content processor
        content_processor = self._create_content_processor(
            file_mapping, str(source_base), str(target), vars, hierarchical_paths
        )

        # Step 5: Execute export
        return self._execute_export(file_mapping, target, root_path, content_processor)

    def _validate_and_resolve_root(
        self, source_path: str, version_spec: VersionSpec, target: Path
    ) -> tuple[str, Path]:
        """
        Validate export target and resolve root prompt file.

        # AICODE-NOTE: This method handles:
        # - Resolving directory sources to versioned files via version_resolver
        # - Validating that the resolved root file exists
        # - Determining the source_base for relative path calculations

        Args:
            source_path: Source path (file or directory)
            version_spec: Version specification
            target: Target export directory

        Returns:
            Tuple of (resolved_root_path, source_base_path)

        Raises:
            ExportError: If root file cannot be found
        """
        source = Path(source_path)

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

        # source_base must be resolved to absolute path for consistent relative path calculations
        source_base = (source if source.is_dir() else source.parent).resolve()

        return resolved_root, source_base

    def _build_file_mapping(
        self,
        root_path: Path,
        source_base: Path,
        target: Path,
        version_spec: VersionSpec,
    ) -> dict[str, str]:
        """
        Build source->target file mapping preserving directory structure.

        # AICODE-NOTE: File mapping strategy:
        # 1. Discover explicitly referenced files first (take precedence)
        # 2. Add all versioned files, skipping conflicts with explicit refs
        # 3. Ensure root file is always included
        # 4. Remove version suffixes from target filenames

        Args:
            root_path: Path to resolved root file
            source_base: Base directory for relative path calculation
            target: Target export directory
            version_spec: Version specification for discovery

        Returns:
            Dictionary mapping source paths to target paths
        """
        file_mapping: dict[str, str] = {}
        referenced_base_names: dict[str, str] = {}

        # Discover all versioned files and explicitly referenced files
        all_versioned_files = self.discover_versioned_files(str(source_base), version_spec)
        referenced_files = self.discover_referenced_files(str(root_path))

        # Process explicitly referenced files first
        for ref_file in referenced_files:
            ref_path = Path(ref_file)
            if not ref_path.exists():
                continue

            try:
                ref_relative = ref_path.relative_to(source_base)
            except ValueError:
                continue

            version_suffix = self._extract_version_from_path(ref_path)
            if version_suffix:
                target_ref_file = target / ref_relative
                file_mapping[str(ref_path)] = str(target_ref_file)
                base_name = ref_path.name.replace(version_suffix, "")
                base_path = ref_relative.parent / base_name
                referenced_base_names[str(base_path)] = str(ref_path)
            else:
                target_ref_file = target / ref_relative
                if str(ref_path) not in file_mapping:
                    file_mapping[str(ref_path)] = str(target_ref_file)

        # Add versioned files, skipping explicit reference conflicts
        for versioned_file in all_versioned_files:
            versioned_path = Path(versioned_file)
            if not versioned_path.exists():
                continue

            try:
                versioned_relative = versioned_path.relative_to(source_base)
            except ValueError:
                continue

            version_suffix = self._extract_version_from_path(versioned_path)
            new_name = (
                versioned_path.name.replace(version_suffix, "")
                if version_suffix
                else versioned_path.name
            )

            if versioned_relative.parent != Path("."):
                target_file = target / versioned_relative.parent / new_name
                base_path = versioned_relative.parent / new_name
            else:
                target_file = target / new_name
                base_path = Path(new_name)

            if str(base_path) in referenced_base_names:
                if referenced_base_names[str(base_path)] != str(versioned_path):
                    continue

            if str(versioned_path) not in file_mapping:
                file_mapping[str(versioned_path)] = str(target_file)

        # Ensure root file is included
        root_version_suffix = self._extract_version_from_path(root_path)
        root_target_name = (
            root_path.name.replace(root_version_suffix, "")
            if root_version_suffix
            else root_path.name
        )
        root_target_path = target / root_target_name
        if str(root_path) not in file_mapping:
            file_mapping[str(root_path)] = str(root_target_path)

        return file_mapping

    def _create_content_processor(
        self,
        file_mapping: dict[str, str],
        source_base: str,
        target: str,
        vars: Optional[dict[str, Any]],
        hierarchical_paths: dict[str, str],
    ):
        """
        Create content processor function for path resolution and variable substitution.

        # AICODE-NOTE: The content processor performs two operations:
        # 1. Path resolution - updates file references for exported structure
        # 2. Variable substitution - replaces {{var}} placeholders if vars provided

        Args:
            file_mapping: Source to target path mapping
            source_base: Source base directory
            target: Target directory
            vars: Optional variables for substitution
            hierarchical_paths: Hierarchical path mapping for nodes

        Returns:
            Callable that processes file content
        """

        def content_processor(path: Path, content: str) -> str:
            # 1. Resolve paths
            resolved = self.filesystem_exporter.resolve_paths_in_file(
                content, file_mapping, source_base, target
            )

            # 2. Substitute variables if provided
            if vars:
                from promptic.context.variables import SubstitutionContext, VariableSubstitutor

                node_id = str(path)
                node_name = path.stem
                version_match = re.search(r"_v(\d+(?:\.\d+)*(?:\.\d+)?)", node_name)
                if version_match:
                    node_name = node_name.replace(version_match.group(0), "")

                hier_path = hierarchical_paths.get(str(path), node_name)

                ext = path.suffix.lower()
                fmt = "markdown"
                if ext in {".yaml", ".yml"}:
                    fmt = "yaml"
                elif ext == ".json":
                    fmt = "json"
                elif ext in {".jinja", ".jinja2"}:
                    fmt = "jinja2"

                context = SubstitutionContext(
                    node_id=node_id,
                    node_name=node_name,
                    hierarchical_path=hier_path,
                    content=resolved,
                    format=fmt,
                    variables=vars,
                )
                substitutor = VariableSubstitutor()
                return substitutor.substitute(context)

            return resolved

        return content_processor

    def _execute_export(
        self,
        file_mapping: dict[str, str],
        target: Path,
        root_path: Path,
        content_processor,
    ) -> ExportResult:
        """
        Execute atomic export operation with cleanup on failure.

        # AICODE-NOTE: Atomic export behavior:
        # - All files must export successfully or nothing is exported
        # - On failure, target directory is removed (best-effort cleanup)
        # - Returns ExportResult with processed root content

        Args:
            file_mapping: Source to target path mapping
            target: Target directory
            root_path: Root prompt file path
            content_processor: Function to process file content

        Returns:
            ExportResult with exported files and root content

        Raises:
            ExportError: If export fails
        """
        try:
            exported_files = self.filesystem_exporter.export_files(
                list(file_mapping.keys()),
                str(target),
                preserve_structure=True,
                file_mapping=file_mapping,
                content_processor=content_processor,
            )

            # Read processed root content
            exported_root_path = file_mapping.get(str(root_path))
            if exported_root_path and Path(exported_root_path).exists():
                resolved_content = Path(exported_root_path).read_text(encoding="utf-8")
            else:
                resolved_content = content_processor(
                    root_path, root_path.read_text(encoding="utf-8")
                )

            log_version_operation(
                logger,
                "export_completed",
                version="",
                path=str(root_path),
                exported_count=len(exported_files),
            )

            return ExportResult(
                root_prompt_content=resolved_content,
                exported_files=exported_files,
                structure_preserved=True,
            )

        except Exception as e:
            # Atomic export: clean up on failure
            if target.exists():
                import shutil

                try:
                    shutil.rmtree(target)
                except Exception:
                    pass  # Best effort cleanup

            if isinstance(e, (ExportError, ExportDirectoryExistsError)):
                raise
            raise ExportError(
                source_path=str(root_path),
                missing_files=[],
                message=f"Export failed: {e}",
            ) from e

    def _build_hierarchical_paths(self, root_path: str) -> dict[str, str]:
        """
        Build hierarchical path mapping for files in the prompt network.

        Args:
            root_path: Path to root prompt file

        Returns:
            Dictionary mapping absolute file paths to hierarchical dot-notation paths
            e.g. {"/abs/path/child.md": "root.child"}
        """
        hierarchical_paths: dict[str, str] = {}

        # Helper to extract clean node name
        def get_node_name(path: Path) -> str:
            stem = path.stem
            # Remove version suffix
            version_match = re.search(r"_v(\d+(?:\.\d+)*(?:\.\d+)?)", stem)
            if version_match:
                return stem.replace(version_match.group(0), "")
            return stem

        root = Path(root_path)
        if not root.exists():
            return {}

        root_name = get_node_name(root)
        hierarchical_paths[str(root.resolve())] = root_name

        # Queue: (current_path, current_hier_path)
        to_process: list[tuple[Path, str]] = [(root, root_name)]
        processed: set[str] = set()

        while to_process:
            current_path, current_hier_path = to_process.pop(0)
            if str(current_path) in processed:
                continue
            processed.add(str(current_path))

            try:
                content = current_path.read_text(encoding="utf-8")

                base_dir = current_path.parent

                # Find references
                refs = []
                # Markdown links
                for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", content):
                    ref_str = match.group(2)
                    if not ref_str.startswith(("http://", "https://", "#")):
                        refs.append(ref_str)

                # Include directives
                for match in re.finditer(
                    r"(?:@include|include:)\s*\(?([^)]+)\)?", content, re.IGNORECASE
                ):
                    refs.append(match.group(1).strip())

                for ref_str in refs:
                    resolved = (base_dir / ref_str).resolve()
                    if resolved.exists() and resolved.is_file():
                        if str(resolved) not in hierarchical_paths:
                            child_name = get_node_name(resolved)
                            child_hier_path = f"{current_hier_path}.{child_name}"
                            hierarchical_paths[str(resolved)] = child_hier_path
                            to_process.append((resolved, child_hier_path))
            except Exception:
                continue

        return hierarchical_paths

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
