r"""Version pattern abstraction for configurable version detection.

# AICODE-NOTE: This module provides VersionPattern class that encapsulates
# version regex patterns and extraction logic. Patterns MUST use named capture
# groups for version components (major, minor, patch, prerelease).

# Pattern structure requirements:
# - (?P<major>\d+) - required, captures major version number
# - (?P<minor>\d+) - optional, captures minor version number
# - (?P<patch>\d+) - optional, captures patch version number
# - (?P<prerelease>[a-zA-Z0-9.-]+) - optional, captures prerelease identifier
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from promptic.versioning.domain.errors import InvalidVersionPatternError

if TYPE_CHECKING:
    from promptic.versioning.config import VersioningConfig


@dataclass(frozen=True)
class VersionComponents:
    """
    Extracted version components from a filename.

    # AICODE-NOTE: This dataclass holds parsed version parts and is used
    # internally for comparison and resolution. It's frozen (immutable)
    # to ensure thread-safety and enable use in caches.

    Attributes:
        major: Major version number (required)
        minor: Minor version number (default: 0)
        patch: Patch version number (default: 0)
        prerelease: Prerelease identifier (e.g., "alpha", "beta.1")
        classifiers: Extracted classifier values (e.g., {"lang": "en"})
    """

    major: int
    minor: int = 0
    patch: int = 0
    prerelease: str | None = None
    classifiers: dict[str, str] = field(default_factory=dict)


class VersionPattern:
    """
    Version detection pattern with compiled regex and extraction logic.

    # AICODE-NOTE: This class encapsulates version regex patterns and provides
    # factory methods for common patterns. Custom patterns must use named
    # capture groups for version components.

    Supported delimiters:
    - "_" (underscore): prompt_v1.md
    - "-" (hyphen): prompt-v1.md
    - "." (dot): prompt.v1.md

    Example:
        >>> pattern = VersionPattern.from_delimiter("_")
        >>> components = pattern.extract_version("prompt_v1.2.3.md")
        >>> components.major, components.minor, components.patch
        (1, 2, 3)
    """

    # Standard patterns for each delimiter
    # Format: delimiter + v + version (major[.minor[.patch]][-prerelease])
    DELIMITER_PATTERNS: dict[str, str] = {
        "_": r"_v",
        "-": r"-v",
        ".": r"\.v",
    }

    # Full version pattern suffix (captures major.minor.patch and optional prerelease)
    # AICODE-NOTE: Pattern structure explained:
    # - (?P<major>\d+) - required major version
    # - (?:\.(?P<minor>\d+))? - optional .minor
    # - (?:\.(?P<patch>\d+))? - optional .patch (only if minor present)
    # - (?:-(?P<prerelease>[a-zA-Z0-9.-]+))? - optional -prerelease
    VERSION_SUFFIX = r"(?P<major>\d+)(?:\.(?P<minor>\d+))?(?:\.(?P<patch>\d+))?(?:-(?P<prerelease>[a-zA-Z0-9.-]+))?"

    def __init__(self, pattern_string: str) -> None:
        """
        Initialize VersionPattern with a regex pattern.

        Args:
            pattern_string: Regex pattern with named capture groups

        Raises:
            InvalidVersionPatternError: If pattern is invalid or missing required groups
        """
        self.pattern_string = pattern_string
        try:
            self._compiled = re.compile(pattern_string, re.IGNORECASE)
        except re.error as e:
            raise InvalidVersionPatternError(
                pattern=pattern_string,
                reason=f"Invalid regex: {e}",
            ) from e

        self._validate_named_groups()

    def _validate_named_groups(self) -> None:
        """Validate that pattern contains required named capture groups."""
        if "major" not in self._compiled.groupindex:
            raise InvalidVersionPatternError(
                pattern=self.pattern_string,
                reason="Pattern must contain (?P<major>...) named group",
            )

    @classmethod
    def from_delimiter(cls, delimiter: str) -> VersionPattern:
        """
        Create pattern for a single delimiter.

        Args:
            delimiter: One of "_", "-", "."

        Returns:
            VersionPattern for the specified delimiter

        Raises:
            ValueError: If delimiter is not supported
        """
        if delimiter not in cls.DELIMITER_PATTERNS:
            raise ValueError(f"Invalid delimiter: {delimiter}. Must be '_', '.', or '-'")

        prefix = cls.DELIMITER_PATTERNS[delimiter]
        pattern = prefix + cls.VERSION_SUFFIX
        return cls(pattern)

    @classmethod
    def from_delimiters(cls, delimiters: list[str]) -> VersionPattern:
        """
        Create pattern for multiple delimiters.

        Args:
            delimiters: List of delimiters (e.g., ["_", "-"])

        Returns:
            Combined VersionPattern matching any of the delimiters

        Raises:
            ValueError: If delimiters list is empty or contains invalid values
        """
        if not delimiters:
            raise ValueError("Delimiters list must not be empty")

        for d in delimiters:
            if d not in cls.DELIMITER_PATTERNS:
                raise ValueError(f"Invalid delimiter: {d}. Must be '_', '.', or '-'")

        # Build alternation pattern: (?:_v|-v|\.v)
        prefixes = [cls.DELIMITER_PATTERNS[d] for d in delimiters]
        combined_prefix = f"(?:{'|'.join(prefixes)})"
        pattern = combined_prefix + cls.VERSION_SUFFIX
        return cls(pattern)

    @classmethod
    def from_config(cls, config: VersioningConfig) -> VersionPattern:
        """
        Create pattern from VersioningConfig.

        Priority:
        1. Custom version_pattern (if provided)
        2. Multiple delimiters (if provided)
        3. Single delimiter (default)

        Args:
            config: VersioningConfig instance

        Returns:
            VersionPattern configured according to settings
        """
        if config.version_pattern is not None:
            return cls(config.version_pattern)

        if config.delimiters is not None:
            return cls.from_delimiters(config.delimiters)

        return cls.from_delimiter(config.delimiter)

    @classmethod
    def default(cls) -> VersionPattern:
        """
        Create default pattern (underscore delimiter).

        Returns:
            VersionPattern with underscore delimiter
        """
        return cls.from_delimiter("_")

    def extract_version(self, filename: str) -> VersionComponents | None:
        """
        Extract version components from a filename.

        # AICODE-NOTE: This method finds all pattern matches in the filename
        # and uses the LAST match if multiple exist. This handles edge cases
        # like "prompt_v1_final_v2.md" deterministically (returns v2).

        Args:
            filename: Filename to parse (e.g., "prompt_v1.2.3.md")

        Returns:
            VersionComponents if version found, None otherwise
        """
        matches = list(self._compiled.finditer(filename))
        if not matches:
            return None

        # Use last match if multiple patterns exist
        match = matches[-1]

        major = int(match.group("major"))

        # Optional groups - check if they exist in the pattern before accessing
        minor_str = match.group("minor") if "minor" in self._compiled.groupindex else None
        patch_str = match.group("patch") if "patch" in self._compiled.groupindex else None
        prerelease = (
            match.group("prerelease") if "prerelease" in self._compiled.groupindex else None
        )

        minor = int(minor_str) if minor_str else 0
        patch = int(patch_str) if patch_str else 0

        return VersionComponents(
            major=major,
            minor=minor,
            patch=patch,
            prerelease=prerelease,
        )

    def get_base_name(self, filename: str) -> str:
        """
        Get base name by removing version pattern from filename.

        Args:
            filename: Filename to process

        Returns:
            Filename with version pattern removed
        """
        return self._compiled.sub("", filename)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"VersionPattern({self.pattern_string!r})"
