"""Version resolution interface and implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Union

from promptic.versioning.domain.errors import VersionResolutionCycleError
from promptic.versioning.utils.logging import get_logger, log_version_operation

if TYPE_CHECKING:
    from promptic.versioning.config import VersioningConfig

logger = get_logger(__name__)

# AICODE-NOTE: VersionSpec can be a string ("latest", "v1", "v1.1", "v1.1.1")
# or a dictionary for hierarchical specifications ({"root": "v1", "instructions/process": "v2"})
VersionSpec = Union[str, Dict[str, str]]


class VersionResolver(ABC):
    """
    Interface for version resolution strategies.

    # AICODE-NOTE: This interface defines the contract for resolving prompt versions
    from directory paths and version specifications. Implementations handle filesystem
    scanning, version detection, and version comparison to select appropriate files.
    """

    @abstractmethod
    def resolve_version(
        self,
        path: str,
        version_spec: VersionSpec,
        classifier: dict[str, str] | None = None,
    ) -> str:
        """
        Resolve version from directory path and version specification.

        Args:
            path: Directory path containing versioned files
            version_spec: Version specification ("latest", "v1", "v1.1", "v1.1.1", or dict)
            classifier: Optional classifier filter (e.g., {"lang": "ru"})

        Returns:
            Resolved file path

        Raises:
            VersionNotFoundError: If requested version doesn't exist
            ClassifierNotFoundError: If requested classifier value doesn't exist
        """
        pass


class HierarchicalVersionResolver(VersionResolver):
    """
    Hierarchical version resolver that supports version specifications per path pattern.

    # AICODE-NOTE: This resolver extends VersionResolver to support hierarchical version
    specifications where different parts of a prompt hierarchy can use different versions.
    When resolving nested prompt references, it applies version rules recursively:
    - If a path pattern matches, use the specified version
    - If no pattern matches, default to "latest" for nested prompts
    - Detects circular version references to prevent infinite loops
    - Classifier is propagated through the resolution chain for consistent filtering
    """

    def __init__(self, base_resolver: VersionResolver) -> None:
        """
        Initialize hierarchical version resolver.

        Args:
            base_resolver: Base resolver for single-file version resolution
        """
        self.base_resolver = base_resolver
        self._resolution_stack: list[str] = []  # Track resolution path for cycle detection

    def resolve_version(
        self,
        path: str,
        version_spec: VersionSpec,
        classifier: dict[str, str] | None = None,
    ) -> str:
        """
        Resolve version using hierarchical specifications with classifier propagation.

        # AICODE-NOTE: Hierarchical resolution strategy:
        # 1. If version_spec is a string, delegate to base resolver (simple case)
        # 2. If version_spec is a dict, apply hierarchical rules:
        #    - Match path against version map patterns
        #    - Use specified version if pattern matches
        #    - Default to "latest" for unmatched paths
        # 3. Cycle detection: Track resolution path, raise error if cycle detected
        # 4. Default latest behavior: Nested prompts use latest if not explicitly specified
        # 5. Classifier propagation: Classifier filter is passed through the entire
        #    resolution chain to ensure consistent filtering across hierarchical prompts

        Args:
            path: Directory path containing versioned files
            version_spec: Version specification (string or hierarchical dict)
            classifier: Optional classifier filter (e.g., {"lang": "ru"})

        Returns:
            Resolved file path

        Raises:
            VersionNotFoundError: If requested version doesn't exist
            VersionResolutionCycleError: If circular version references detected
            ClassifierNotFoundError: If requested classifier value doesn't exist
        """
        # If version_spec is a string, delegate to base resolver
        if isinstance(version_spec, str):
            return self.base_resolver.resolve_version(path, version_spec, classifier)

        # Hierarchical specification (dict)
        if not isinstance(version_spec, dict):
            raise ValueError(f"Invalid version_spec type: {type(version_spec)}")

        # Check for cycles
        if path in self._resolution_stack:
            cycle_path = self._resolution_stack + [path]
            raise VersionResolutionCycleError(cycle_path)

        # Find matching version specification for this path (before adding to stack)
        # This allows "root" key to work for the first resolution
        matched_version = self._match_path_pattern(path, version_spec, len(self._resolution_stack))

        # Add to resolution stack
        self._resolution_stack.append(path)

        try:
            # Resolve using matched version (or "latest" if no match)
            # Propagate classifier through the resolution chain
            resolved = self.base_resolver.resolve_version(path, matched_version, classifier)

            log_version_operation(
                logger,
                "hierarchical_version_resolved",
                version=matched_version,
                path=path,
                classifier=str(classifier) if classifier else None,
            )

            return resolved
        finally:
            # Remove from resolution stack (backtrack)
            if self._resolution_stack and self._resolution_stack[-1] == path:
                self._resolution_stack.pop()

    def _match_path_pattern(
        self, path: str, version_map: dict[str, str], stack_depth: int = 0
    ) -> str:
        """
        Match path against version map patterns and return matched version.

        # AICODE-NOTE: Path pattern matching strategy:
        # - "root" key: Special key that matches the current path (base directory)
        # - Exact match: If path exactly matches a key, use that version
        # - Prefix match: If path starts with a key (with / separator), use that version
        # - Basename match: Match against directory basename for relative references
        # - Default: Return "latest" if no pattern matches

        Args:
            path: Path to match
            version_map: Dictionary mapping path patterns to versions
            stack_depth: Current depth in resolution stack (0 = root)

        Returns:
            Matched version specification or "latest"
        """
        from pathlib import Path

        # Special handling for "root" key - it matches the current path
        if "root" in version_map and stack_depth == 0:
            # First resolution (root level)
            return version_map["root"]

        # Try exact match first
        if path in version_map:
            return version_map[path]

        # Try prefix match (path starts with pattern)
        for pattern, version in version_map.items():
            if path.startswith(pattern + "/") or path == pattern:
                return version

        # Try basename match (for relative path patterns)
        path_obj = Path(path)
        for pattern, version in version_map.items():
            # Skip "root" as it's handled above
            if pattern == "root":
                continue
            # Check if pattern matches the end of the path
            if path.endswith(pattern) or str(path_obj).endswith(pattern):
                return version

        # Default to latest if no pattern matches
        return "latest"
