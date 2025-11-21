"""Base interface for reference resolvers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from promptic.context.nodes.models import ContextNode


class NodeReferenceResolver(ABC):
    """Interface for pluggable reference resolution strategies.

    # AICODE-NOTE: This interface enables pluggable resolution strategies
    (filesystem, URIs, node IDs) without hardcoding assumptions, satisfying
    DIP principle. Implementations can support different resolution strategies
    (relative paths, absolute paths, URIs) while maintaining a unified interface.
    """

    @abstractmethod
    def resolve(self, path: str, base_path: Path) -> "ContextNode":
        """Resolve a reference path to a node.

        Args:
            path: Reference path (file path, node ID, or URI)
            base_path: Base path for relative resolution

        Returns:
            Resolved ContextNode instance

        Raises:
            NodeReferenceNotFoundError: If reference cannot be resolved
            PathResolutionError: If path resolution fails
        """
        pass

    @abstractmethod
    def validate(self, path: str, base_path: Path) -> bool:
        """Validate that a reference path is valid.

        Args:
            path: Reference path to validate
            base_path: Base path for relative resolution

        Returns:
            True if path is valid, False otherwise
        """
        pass
