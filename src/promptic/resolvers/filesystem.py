"""Filesystem-based reference resolver implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from promptic.context.nodes.errors import NodeReferenceNotFoundError, PathResolutionError
from promptic.context.nodes.models import ContextNode
from promptic.resolvers.base import NodeReferenceResolver
from promptic.versioning import VersionedFileScanner, VersionSpec


class FilesystemReferenceResolver(NodeReferenceResolver):
    """Filesystem-based reference resolver.

    Resolves file paths relative to a base directory or as absolute paths.
    Supports both relative and absolute path resolution strategies.
    Supports version-aware resolution when version parameter is provided.

    # AICODE-NOTE: Version-aware resolution is integrated at the path resolution level.
    When a version specification is provided, the resolver uses VersionedFileScanner
    to resolve versioned files before loading nodes. This enables hierarchical versioning
    where different parts of a prompt hierarchy can use different versions.
    """

    def __init__(self, root: Path | None = None, version: Optional[VersionSpec] = None):
        """Initialize filesystem reference resolver.

        Args:
            root: Root directory for resolving relative paths. If None, uses current working directory.
            version: Optional version specification for version-aware resolution ("latest", "v1", etc.)
        """
        self.root = root or Path.cwd()
        self.version = version
        self.version_scanner = VersionedFileScanner() if version is not None else None

    def resolve(
        self, path: str, base_path: Path, version: Optional[VersionSpec] = None
    ) -> ContextNode:
        """Resolve a reference path to a node.

        # AICODE-NOTE: Version-aware resolution: If version is provided (either via constructor
        or method parameter), the resolver uses VersionedFileScanner to resolve versioned files.
        The method parameter takes precedence over the constructor parameter, enabling
        hierarchical version specifications.

        Args:
            path: Reference path (file path)
            base_path: Base path for relative resolution
            version: Optional version specification (overrides constructor version if provided)

        Returns:
            Resolved ContextNode instance

        Raises:
            NodeReferenceNotFoundError: If reference cannot be resolved
            PathResolutionError: If path resolution fails
        """
        # Use method parameter version if provided, otherwise use constructor version
        effective_version = version if version is not None else self.version

        # Resolve path (relative or absolute)
        resolved_path = self._resolve_path(path, base_path, effective_version)

        # Check if file exists
        if not resolved_path.exists():
            raise NodeReferenceNotFoundError(
                f"Reference not found: {path} (resolved to {resolved_path})"
            )

        # Load node using SDK function (lazy import to avoid circular dependency)
        try:
            from promptic.sdk.nodes import load_node

            return load_node(resolved_path)
        except Exception as e:
            raise PathResolutionError(f"Failed to load node from {resolved_path}: {e}") from e

    def validate(self, path: str, base_path: Path, version: Optional[VersionSpec] = None) -> bool:
        """Validate that a reference path is valid.

        Args:
            path: Reference path to validate
            base_path: Base path for relative resolution
            version: Optional version specification for version-aware validation

        Returns:
            True if path is valid, False otherwise
        """
        try:
            effective_version = version if version is not None else self.version
            resolved_path = self._resolve_path(path, base_path, effective_version)
            return resolved_path.exists()
        except Exception:
            return False

    def _resolve_path(
        self, path: str, base_path: Path, version: Optional[VersionSpec] = None
    ) -> Path:
        """Resolve a path (relative or absolute) to a full path with optional version resolution.

        # AICODE-NOTE: Version-aware path resolution: If version is provided and the path
        is a directory, use VersionedFileScanner to resolve the versioned file. If the path
        is already a file, return it as-is (bypasses version resolution for explicit file paths).

        Args:
            path: Path to resolve
            base_path: Base path for relative resolution
            version: Optional version specification for version-aware resolution

        Returns:
            Resolved Path object

        Raises:
            PathResolutionError: If path resolution fails
        """
        path_obj = Path(path)

        # If path is absolute, use it directly (but check for version resolution if it's a directory)
        if path_obj.is_absolute():
            if version is not None and path_obj.is_dir():
                # Use version scanner to resolve versioned file from directory
                if self.version_scanner is None:
                    self.version_scanner = VersionedFileScanner()
                try:
                    resolved_file = self.version_scanner.resolve_version(str(path_obj), version)
                    return Path(resolved_file)
                except Exception:
                    # If version resolution fails, fall back to original path
                    return path_obj
            return path_obj

        # Otherwise, resolve relative to base_path
        # If base_path is a file, use its parent directory
        if base_path.is_file():
            base_dir = base_path.parent
        else:
            base_dir = base_path

        # Resolve relative path
        try:
            resolved = (base_dir / path_obj).resolve()

            # If version is provided and resolved path is a directory, use version scanner
            if version is not None and resolved.is_dir():
                if self.version_scanner is None:
                    self.version_scanner = VersionedFileScanner()
                try:
                    resolved_file = self.version_scanner.resolve_version(str(resolved), version)
                    return Path(resolved_file)
                except Exception:
                    # If version resolution fails, fall back to resolved path
                    return resolved

            return resolved
        except Exception as e:
            raise PathResolutionError(f"Failed to resolve path {path} from {base_path}: {e}") from e
