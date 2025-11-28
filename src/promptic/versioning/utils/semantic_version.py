"""Semantic versioning utilities for parsing, normalization, and comparison."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from packaging.version import InvalidVersion, Version


@dataclass(frozen=True)
class SemanticVersion:
    """
    Represents a semantic version (major.minor.patch) with optional prerelease.

    # AICODE-NOTE: This dataclass uses packaging.Version for parsing and comparison
    to ensure standard semantic versioning rules are followed. The frozen dataclass
    ensures immutability and enables use as dictionary keys.

    Extended in 009-advanced-versioning to support prerelease field.
    Comparison logic: releases > prereleases of same base version.
    Prerelease ordering: alpha < beta < rc (configurable).
    """

    major: int
    minor: int
    patch: int
    prerelease: str | None = None

    def __str__(self) -> str:
        """Return string representation in v{major}.{minor}.{patch}[-prerelease] format."""
        base = f"v{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            return f"{base}-{self.prerelease}"
        return base

    @classmethod
    def from_string(cls, version_str: str) -> SemanticVersion:
        """
        Parse a version string into a SemanticVersion.

        Supports formats:
        - v1.0.0 (full semantic version)
        - v1.1.0 (minor version)
        - v1 (major version only, normalized to v1.0.0)
        - v1.0.0-alpha (with prerelease)
        - v1.0.0-beta.1 (with prerelease and numeric suffix)

        Args:
            version_str: Version string to parse (e.g., "v1", "v1.1", "v1.1.1", "v1.0.0-alpha")

        Returns:
            SemanticVersion instance

        Raises:
            ValueError: If version string cannot be parsed
        """
        # Remove 'v' prefix if present
        version_str = version_str.lstrip("vV")

        # Check for prerelease suffix
        prerelease = None
        if "-" in version_str:
            base_version, prerelease = version_str.split("-", 1)
        else:
            base_version = version_str

        try:
            version = Version(base_version)
            return cls(
                major=version.major,
                minor=version.minor,
                patch=version.micro,  # packaging uses 'micro' for patch
                prerelease=prerelease,
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
        - v1.0.0-alpha → v1.0.0-alpha (preserves prerelease)

        Args:
            version_str: Version string to normalize

        Returns:
            Normalized SemanticVersion instance
        """
        return cls.from_string(version_str)

    @classmethod
    def from_components(cls, components: "VersionComponents") -> SemanticVersion:
        """
        Create SemanticVersion from VersionComponents.

        Args:
            components: VersionComponents instance

        Returns:
            SemanticVersion instance
        """
        from promptic.versioning.domain.pattern import VersionComponents

        return cls(
            major=components.major,
            minor=components.minor,
            patch=components.patch,
            prerelease=components.prerelease,
        )

    def __lt__(self, other: SemanticVersion) -> bool:
        """
        Compare versions using semantic versioning rules.

        # AICODE-NOTE: Comparison logic for prereleases:
        # - Compare major.minor.patch first
        # - Same base version: release > prerelease
        # - Both prereleases: compare by prerelease order (alpha < beta < rc)
        """
        # Compare major.minor.patch first
        if (self.major, self.minor, self.patch) != (other.major, other.minor, other.patch):
            return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

        # Same base version: release > prerelease
        if self.prerelease is None and other.prerelease is not None:
            return False  # self is release, other is prerelease - self > other
        if self.prerelease is not None and other.prerelease is None:
            return True  # self is prerelease, other is release - self < other

        # Both are releases (or both None)
        if self.prerelease is None and other.prerelease is None:
            return False  # Equal

        # Both are prereleases - compare by order
        return self._compare_prerelease(other) < 0

    def _compare_prerelease(self, other: SemanticVersion, order: list[str] | None = None) -> int:
        """
        Compare prerelease identifiers.

        # AICODE-NOTE: Prerelease ordering follows these rules:
        # 1. Known labels compared by configured order (default: alpha < beta < rc)
        # 2. Unknown labels compared lexicographically
        # 3. Numeric suffixes compared numerically (e.g., alpha.1 < alpha.2)

        Args:
            other: Other SemanticVersion to compare against
            order: Prerelease ordering list (default: ["alpha", "beta", "rc"])

        Returns:
            -1 if self < other, 0 if equal, 1 if self > other
        """
        if order is None:
            order = ["alpha", "beta", "rc"]

        self_pre = self.prerelease or ""
        other_pre = other.prerelease or ""

        # Extract base label and numeric suffix
        def parse_prerelease(pre: str) -> tuple[str, int]:
            """Parse prerelease into (label, number)."""
            # Handle formats like "alpha", "alpha.1", "beta.2", "rc1"
            import re

            match = re.match(r"([a-zA-Z]+)\.?(\d+)?", pre)
            if match:
                label = match.group(1).lower()
                num = int(match.group(2)) if match.group(2) else 0
                return (label, num)
            return (pre.lower(), 0)

        self_label, self_num = parse_prerelease(self_pre)
        other_label, other_num = parse_prerelease(other_pre)

        # Get index in order list (-1 if not found)
        def get_order_index(label: str) -> int:
            try:
                return order.index(label)
            except ValueError:
                return len(order)  # Unknown labels come after known ones

        self_idx = get_order_index(self_label)
        other_idx = get_order_index(other_label)

        if self_idx != other_idx:
            return -1 if self_idx < other_idx else 1

        # Same label category, compare by numeric suffix
        if self_num != other_num:
            return -1 if self_num < other_num else 1

        # Same label and number, compare lexicographically
        if self_label != other_label:
            return -1 if self_label < other_label else 1

        return 0

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
