"""Filesystem-based reference resolver implementation."""

from __future__ import annotations

from pathlib import Path

from promptic.context.nodes.errors import NodeReferenceNotFoundError, PathResolutionError
from promptic.context.nodes.models import ContextNode
from promptic.resolvers.base import NodeReferenceResolver


class FilesystemReferenceResolver(NodeReferenceResolver):
    """Filesystem-based reference resolver.

    Resolves file paths relative to a base directory or as absolute paths.
    Supports both relative and absolute path resolution strategies.
    """

    def __init__(self, root: Path | None = None):
        """Initialize filesystem reference resolver.

        Args:
            root: Root directory for resolving relative paths. If None, uses current working directory.
        """
        self.root = root or Path.cwd()

    def resolve(self, path: str, base_path: Path) -> ContextNode:
        """Resolve a reference path to a node.

        Args:
            path: Reference path (file path)
            base_path: Base path for relative resolution

        Returns:
            Resolved ContextNode instance

        Raises:
            NodeReferenceNotFoundError: If reference cannot be resolved
            PathResolutionError: If path resolution fails
        """
        # Resolve path (relative or absolute)
        resolved_path = self._resolve_path(path, base_path)

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

    def validate(self, path: str, base_path: Path) -> bool:
        """Validate that a reference path is valid.

        Args:
            path: Reference path to validate
            base_path: Base path for relative resolution

        Returns:
            True if path is valid, False otherwise
        """
        try:
            resolved_path = self._resolve_path(path, base_path)
            return resolved_path.exists()
        except Exception:
            return False

    def _resolve_path(self, path: str, base_path: Path) -> Path:
        """Resolve a path (relative or absolute) to a full path.

        Args:
            path: Path to resolve
            base_path: Base path for relative resolution

        Returns:
            Resolved Path object

        Raises:
            PathResolutionError: If path resolution fails
        """
        path_obj = Path(path)

        # If path is absolute, use it directly
        if path_obj.is_absolute():
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
            return resolved
        except Exception as e:
            raise PathResolutionError(f"Failed to resolve path {path} from {base_path}: {e}") from e
