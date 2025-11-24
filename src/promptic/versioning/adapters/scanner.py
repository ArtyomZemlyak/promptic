"""Versioned file scanner for filesystem-based version detection."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from promptic.versioning.domain.errors import VersionNotFoundError
from promptic.versioning.domain.resolver import VersionResolver, VersionSpec
from promptic.versioning.utils.cache import VersionCache
from promptic.versioning.utils.logging import get_logger, log_version_operation
from promptic.versioning.utils.semantic_version import (
    SemanticVersion,
    get_latest_version,
    normalize_version,
)

logger = get_logger(__name__)


@dataclass
class VersionInfo:
    """
    Information about a versioned file.

    # AICODE-NOTE: This dataclass stores metadata about versioned files discovered
    during directory scanning. It includes the filename, full path, base name
    (without version), parsed semantic version, and whether the file is versioned.
    """

    filename: str
    path: str
    base_name: str
    version: Optional[SemanticVersion]
    is_versioned: bool


class VersionedFileScanner(VersionResolver):
    """
    Scanner that detects and resolves versioned files from filesystem.

    # AICODE-NOTE: This scanner implements version detection using regex patterns
    matching semantic versioning notation (_v1, _v1.1, _v1.1.1). When multiple
    patterns exist in a filename, the last matching pattern is used as the version
    identifier. Version comparison follows standard semantic versioning rules
    (major.minor.patch precedence). Directory scans are cached and invalidated
    when directory modification times change.
    """

    def __init__(self) -> None:
        """Initialize scanner with version detection patterns and cache."""
        # AICODE-NOTE: Version detection patterns match semantic versioning notation:
        # _v{N}, _v{N}.{N}, _v{N}.{N}.{N} (e.g., _v1, _v1.1, _v1.1.1)
        # The pattern captures the version part for extraction
        self.version_pattern = re.compile(r"_v(\d+)(?:\.(\d+))?(?:\.(\d+))?", re.IGNORECASE)
        self.cache: VersionCache[list[VersionInfo]] = VersionCache()

    def extract_version_from_filename(self, filename: str) -> Optional[SemanticVersion]:
        """
        Extract version identifier from filename using regex patterns.

        # AICODE-NOTE: This method uses regex to find version patterns in filenames.
        When multiple patterns exist, the last matching pattern is used (handles
        edge cases like "prompt_v1.0_final_v2.1.md" deterministically).

        Args:
            filename: Filename to extract version from

        Returns:
            SemanticVersion if version detected, None otherwise
        """
        matches = list(self.version_pattern.finditer(filename))
        if not matches:
            return None

        # Use last match if multiple patterns exist
        match = matches[-1]
        major = int(match.group(1))
        minor = int(match.group(2)) if match.group(2) else 0
        patch = int(match.group(3)) if match.group(3) else 0

        return SemanticVersion(major=major, minor=minor, patch=patch)

    def normalize_version(self, version_str: str) -> SemanticVersion:
        """
        Normalize version string to full semantic version format.

        # AICODE-NOTE: Normalization rules:
        # - v1 → v1.0.0
        # - v1.1 → v1.1.0
        # - v1.1.1 → v1.1.1 (no change)

        Args:
            version_str: Version string to normalize

        Returns:
            Normalized SemanticVersion
        """
        return normalize_version(version_str)

    def scan_directory(self, directory: str, recursive: bool = False) -> list[VersionInfo]:
        """
        Scan directory for versioned files, return sorted list.

        # AICODE-NOTE: This method scans a directory for files matching version
        patterns, extracts version information, and returns a sorted list using
        semantic versioning comparison. Results are cached and invalidated when
        directory modification time changes. Supports recursive scanning to
        discover versioned files in subdirectories.

        Args:
            directory: Directory path to scan
            recursive: Whether to scan subdirectories recursively (default: False)

        Returns:
            Sorted list of VersionInfo (latest first)
        """
        # Check cache first (only for non-recursive scans)
        cache_key = f"{directory}:recursive={recursive}"
        cached: list[VersionInfo] | None = self.cache.get(cache_key)
        if cached is not None:
            return cached

        path = Path(directory)
        if not path.exists() or not path.is_dir():
            return []

        versioned_files: list[VersionInfo] = []
        unversioned_files: list[VersionInfo] = []

        # Use rglob for recursive or iterdir for single level
        file_iterator = path.rglob("*") if recursive else path.iterdir()

        for file_path in file_iterator:
            if not file_path.is_file():
                continue

            filename = file_path.name
            version = self.extract_version_from_filename(filename)

            if version is not None:
                # Extract base name (remove version pattern)
                base_name = self.version_pattern.sub("", filename)
                versioned_files.append(
                    VersionInfo(
                        filename=filename,
                        path=str(file_path),
                        base_name=base_name,
                        version=version,
                        is_versioned=True,
                    )
                )
            else:
                # Unversioned file
                unversioned_files.append(
                    VersionInfo(
                        filename=filename,
                        path=str(file_path),
                        base_name=filename,
                        version=None,
                        is_versioned=False,
                    )
                )

        # Sort versioned files by version (latest first)
        # Filter out None versions before sorting
        versioned_files_with_version: list[VersionInfo] = [
            v for v in versioned_files if v.version is not None
        ]
        versioned_files_with_version.sort(
            key=lambda v: v.version if v.version is not None else SemanticVersion(0, 0, 0),
            reverse=True,
        )
        versioned_files = versioned_files_with_version

        # Combine: versioned files first, then unversioned
        result = versioned_files + unversioned_files

        # Cache result
        self.cache.set(cache_key, result)

        log_version_operation(
            logger,
            "directory_scanned",
            path=directory,
            versioned_count=len(versioned_files),
            unversioned_count=len(unversioned_files),
        )

        return result

    def get_latest_version(self, versions: list[SemanticVersion]) -> Optional[SemanticVersion]:
        """
        Determine latest version from list using semantic versioning comparison.

        Args:
            versions: List of SemanticVersion instances

        Returns:
            Latest SemanticVersion, or None if list is empty
        """
        return get_latest_version(versions)

    def resolve_version(self, path: str, version_spec: VersionSpec) -> str:
        """
        Resolve version from directory path and version specification.

        # AICODE-NOTE: This method implements version resolution logic:
        # - "latest" (or default): Resolve to latest versioned file
        # - Specific version (v1, v1.1, v1.1.1): Resolve to matching version
        # - Unversioned fallback: If no versioned files exist, use unversioned files
        # Versioned files take precedence over unversioned files with same base name.

        Args:
            path: Directory path containing versioned files
            version_spec: Version specification ("latest", "v1", "v1.1", "v1.1.1")

        Returns:
            Resolved file path

        Raises:
            VersionNotFoundError: If requested version doesn't exist
        """
        if isinstance(version_spec, dict):
            # Hierarchical version specs handled by HierarchicalVersionResolver
            # For now, treat as "latest"
            version_spec = "latest"

        scanned = self.scan_directory(path)
        if not scanned:
            raise VersionNotFoundError(
                path=path,
                version_spec=str(version_spec),
                available_versions=[],
                message=f"No files found in directory: {path}",
            )

        # Separate versioned and unversioned files
        versioned = [v for v in scanned if v.is_versioned]
        unversioned = [v for v in scanned if not v.is_versioned]

        # Handle "latest" or default
        if version_spec == "latest" or version_spec is None:
            if versioned:
                latest = versioned[0]  # Already sorted, latest first
                log_version_operation(
                    logger,
                    "version_resolved",
                    version=str(latest.version),
                    path=latest.path,
                )
                return latest.path
            elif unversioned:
                # Fallback to unversioned
                log_version_operation(
                    logger,
                    "version_resolved",
                    path=unversioned[0].path,
                )
                return unversioned[0].path
            else:
                raise VersionNotFoundError(
                    path=path,
                    version_spec=str(version_spec),
                    available_versions=[],
                )

        # Handle specific version
        try:
            requested_version = self.normalize_version(version_spec)
        except ValueError as e:
            raise VersionNotFoundError(
                path=path,
                version_spec=version_spec,
                available_versions=[str(v.version) for v in versioned],
                message=f"Invalid version specification: {version_spec}",
            ) from e

        # Find matching version
        for version_info in versioned:
            if version_info.version == requested_version:
                log_version_operation(
                    logger,
                    "version_resolved",
                    version=str(version_info.version),
                    path=version_info.path,
                )
                return version_info.path

        # Version not found
        available_versions = [str(v.version) for v in versioned]
        raise VersionNotFoundError(
            path=path,
            version_spec=version_spec,
            available_versions=available_versions,
        )
