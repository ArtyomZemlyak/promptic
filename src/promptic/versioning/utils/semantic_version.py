"""Semantic versioning utilities for parsing, normalization, and comparison."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from packaging.version import InvalidVersion, Version


@dataclass(frozen=True)
class SemanticVersion:
    """
    Represents a semantic version (major.minor.patch).

    # AICODE-NOTE: This dataclass uses packaging.Version for parsing and comparison
    to ensure standard semantic versioning rules are followed. The frozen dataclass
    ensures immutability and enables use as dictionary keys.
    """

    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        """Return string representation in v{major}.{minor}.{patch} format."""
        return f"v{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def from_string(cls, version_str: str) -> SemanticVersion:
        """
        Parse a version string into a SemanticVersion.

        Supports formats:
        - v1.0.0 (full semantic version)
        - v1.1.0 (minor version)
        - v1 (major version only, normalized to v1.0.0)

        Args:
            version_str: Version string to parse (e.g., "v1", "v1.1", "v1.1.1")

        Returns:
            SemanticVersion instance

        Raises:
            ValueError: If version string cannot be parsed
        """
        # Remove 'v' prefix if present
        version_str = version_str.lstrip("vV")

        try:
            version = Version(version_str)
            return cls(
                major=version.major,
                minor=version.minor,
                patch=version.micro,  # packaging uses 'micro' for patch
            )
        except InvalidVersion as e:
            raise ValueError(f"Invalid version string: {version_str}") from e

    @classmethod
    def normalize(cls, version_str: str) -> SemanticVersion:
        """
        Normalize a version string to full semantic version format.

        Normalization rules:
        - v1 → v1.0.0
        - v1.1 → v1.1.0
        - v1.1.1 → v1.1.1 (no change)

        Args:
            version_str: Version string to normalize

        Returns:
            Normalized SemanticVersion instance
        """
        return cls.from_string(version_str)

    def __lt__(self, other: SemanticVersion) -> bool:
        """Compare versions using semantic versioning rules (major.minor.patch precedence)."""
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        return self.patch < other.patch

    def __le__(self, other: SemanticVersion) -> bool:
        """Less than or equal comparison."""
        return self < other or self == other

    def __gt__(self, other: SemanticVersion) -> bool:
        """Greater than comparison."""
        return not (self <= other)

    def __ge__(self, other: SemanticVersion) -> bool:
        """Greater than or equal comparison."""
        return not (self < other)


def normalize_version(version_str: str) -> SemanticVersion:
    """
    Normalize a version string to full semantic version format.

    Convenience function that wraps SemanticVersion.normalize().

    Args:
        version_str: Version string to normalize (e.g., "v1", "v1.1", "v1.1.1")

    Returns:
        Normalized SemanticVersion instance
    """
    return SemanticVersion.normalize(version_str)


def compare_versions(version1: SemanticVersion, version2: SemanticVersion) -> int:
    """
    Compare two semantic versions.

    Args:
        version1: First version to compare
        version2: Second version to compare

    Returns:
        -1 if version1 < version2, 0 if equal, 1 if version1 > version2
    """
    if version1 < version2:
        return -1
    if version1 > version2:
        return 1
    return 0


def get_latest_version(versions: list[SemanticVersion]) -> Optional[SemanticVersion]:
    """
    Determine the latest version from a list of versions.

    Args:
        versions: List of SemanticVersion instances

    Returns:
        Latest SemanticVersion, or None if list is empty
    """
    if not versions:
        return None
    return max(versions)
