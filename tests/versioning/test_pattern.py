"""Unit tests for VersionPattern abstraction.

Tests for:
- VersionPattern.from_delimiter() (T014)
- VersionPattern.from_delimiters() (T015)
- Custom pattern extraction (T028, T029, T030 - Phase 4)
"""

from __future__ import annotations

import pytest


class TestVersionPatternFromDelimiter:
    """Test VersionPattern.from_delimiter() (T014)."""

    def test_underscore_delimiter_pattern(self) -> None:
        """Underscore delimiter should generate correct pattern."""
        from promptic.versioning.domain.pattern import VersionPattern

        pattern = VersionPattern.from_delimiter("_")

        # Should match _v1, _v1.1, _v1.1.1
        assert pattern.extract_version("prompt_v1.md") is not None
        assert pattern.extract_version("prompt_v1.1.md") is not None
        assert pattern.extract_version("prompt_v1.1.1.md") is not None

    def test_hyphen_delimiter_pattern(self) -> None:
        """Hyphen delimiter should generate correct pattern."""
        from promptic.versioning.domain.pattern import VersionPattern

        pattern = VersionPattern.from_delimiter("-")

        # Should match -v1, -v1.1, -v1.1.1
        assert pattern.extract_version("prompt-v1.md") is not None
        assert pattern.extract_version("prompt-v1.1.md") is not None
        assert pattern.extract_version("prompt-v1.1.1.md") is not None

        # Should NOT match underscore delimiter
        assert pattern.extract_version("prompt_v1.md") is None

    def test_dot_delimiter_pattern(self) -> None:
        """Dot delimiter should generate correct pattern."""
        from promptic.versioning.domain.pattern import VersionPattern

        pattern = VersionPattern.from_delimiter(".")

        # Should match .v1, .v1.1, .v1.1.1
        assert pattern.extract_version("prompt.v1.md") is not None
        assert pattern.extract_version("prompt.v1.1.md") is not None
        assert pattern.extract_version("prompt.v1.1.1.md") is not None

    def test_invalid_delimiter_raises(self) -> None:
        """Invalid delimiter should raise ValueError."""
        from promptic.versioning.domain.pattern import VersionPattern

        with pytest.raises(ValueError):
            VersionPattern.from_delimiter("@")

    def test_extract_returns_version_components(self) -> None:
        """extract_version should return VersionComponents with correct values."""
        from promptic.versioning.domain.pattern import VersionPattern

        pattern = VersionPattern.from_delimiter("_")
        components = pattern.extract_version("task_v2.3.4.md")

        assert components is not None
        assert components.major == 2
        assert components.minor == 3
        assert components.patch == 4

    def test_extract_major_only(self) -> None:
        """extract_version should handle major-only versions."""
        from promptic.versioning.domain.pattern import VersionPattern

        pattern = VersionPattern.from_delimiter("_")
        components = pattern.extract_version("task_v5.md")

        assert components is not None
        assert components.major == 5
        assert components.minor == 0
        assert components.patch == 0

    def test_extract_major_minor(self) -> None:
        """extract_version should handle major.minor versions."""
        from promptic.versioning.domain.pattern import VersionPattern

        pattern = VersionPattern.from_delimiter("_")
        components = pattern.extract_version("task_v2.1.md")

        assert components is not None
        assert components.major == 2
        assert components.minor == 1
        assert components.patch == 0


class TestVersionPatternFromDelimiters:
    """Test VersionPattern.from_delimiters() (T015)."""

    def test_multiple_delimiters(self) -> None:
        """Multiple delimiters should match any of them."""
        from promptic.versioning.domain.pattern import VersionPattern

        pattern = VersionPattern.from_delimiters(["_", "-"])

        # Should match both underscore and hyphen
        assert pattern.extract_version("prompt_v1.md") is not None
        assert pattern.extract_version("prompt-v1.md") is not None

    def test_all_three_delimiters(self) -> None:
        """All three delimiters should work together."""
        from promptic.versioning.domain.pattern import VersionPattern

        pattern = VersionPattern.from_delimiters(["_", "-", "."])

        assert pattern.extract_version("prompt_v1.md") is not None
        assert pattern.extract_version("prompt-v1.md") is not None
        assert pattern.extract_version("prompt.v1.md") is not None

    def test_empty_delimiters_raises(self) -> None:
        """Empty delimiters list should raise ValueError."""
        from promptic.versioning.domain.pattern import VersionPattern

        with pytest.raises(ValueError):
            VersionPattern.from_delimiters([])

    def test_invalid_delimiter_in_list_raises(self) -> None:
        """Invalid delimiter in list should raise ValueError."""
        from promptic.versioning.domain.pattern import VersionPattern

        with pytest.raises(ValueError):
            VersionPattern.from_delimiters(["_", "@"])


class TestVersionPatternFromConfig:
    """Test VersionPattern.from_config() factory."""

    def test_from_config_with_single_delimiter(self) -> None:
        """from_config should use single delimiter when delimiters is None."""
        from promptic.versioning.config import VersioningConfig
        from promptic.versioning.domain.pattern import VersionPattern

        config = VersioningConfig(delimiter="-")
        pattern = VersionPattern.from_config(config)

        assert pattern.extract_version("prompt-v1.md") is not None
        assert pattern.extract_version("prompt_v1.md") is None

    def test_from_config_with_multiple_delimiters(self) -> None:
        """from_config should use delimiters list when provided."""
        from promptic.versioning.config import VersioningConfig
        from promptic.versioning.domain.pattern import VersionPattern

        config = VersioningConfig(delimiters=["_", "-"])
        pattern = VersionPattern.from_config(config)

        assert pattern.extract_version("prompt_v1.md") is not None
        assert pattern.extract_version("prompt-v1.md") is not None

    def test_from_config_with_custom_pattern(self) -> None:
        """from_config should use custom pattern when provided."""
        from promptic.versioning.config import VersioningConfig
        from promptic.versioning.domain.pattern import VersionPattern

        config = VersioningConfig(version_pattern=r"_rev(?P<major>\d+)")
        pattern = VersionPattern.from_config(config)

        # Should match custom pattern
        components = pattern.extract_version("prompt_rev42.md")
        assert components is not None
        assert components.major == 42


class TestCustomPatternExtraction:
    """Test custom pattern extraction (T028)."""

    def test_custom_rev_pattern(self) -> None:
        """Custom rev pattern should extract version correctly."""
        from promptic.versioning.domain.pattern import VersionPattern

        pattern = VersionPattern(r"_rev(?P<major>\d+)")
        components = pattern.extract_version("prompt_rev42.md")

        assert components is not None
        assert components.major == 42
        assert components.minor == 0
        assert components.patch == 0

    def test_custom_build_pattern(self) -> None:
        """Custom build pattern should extract version correctly."""
        from promptic.versioning.domain.pattern import VersionPattern

        pattern = VersionPattern(r"_build(?P<major>\d+)_(?P<minor>\d+)")
        components = pattern.extract_version("prompt_build123_456.md")

        assert components is not None
        assert components.major == 123
        assert components.minor == 456

    def test_custom_pattern_with_prerelease(self) -> None:
        """Custom pattern with prerelease capture should work."""
        from promptic.versioning.domain.pattern import VersionPattern

        pattern = VersionPattern(r"_v(?P<major>\d+)-(?P<prerelease>[a-z]+)")
        components = pattern.extract_version("prompt_v1-alpha.md")

        assert components is not None
        assert components.major == 1
        assert components.prerelease == "alpha"


class TestPatternValidation:
    """Test pattern validation for named groups (T029)."""

    def test_pattern_requires_major_group(self) -> None:
        """Pattern must have major named group."""
        from promptic.versioning.domain.errors import InvalidVersionPatternError
        from promptic.versioning.domain.pattern import VersionPattern

        with pytest.raises(InvalidVersionPatternError) as exc_info:
            VersionPattern(r"_v(\d+)")

        assert "major" in str(exc_info.value).lower()

    def test_pattern_with_only_unnamed_groups_fails(self) -> None:
        """Pattern with only unnamed groups should fail."""
        from promptic.versioning.domain.errors import InvalidVersionPatternError
        from promptic.versioning.domain.pattern import VersionPattern

        with pytest.raises(InvalidVersionPatternError):
            VersionPattern(r"_v(\d+)\.(\d+)")

    def test_pattern_with_mixed_groups_works(self) -> None:
        """Pattern with named major and unnamed others should work."""
        from promptic.versioning.domain.pattern import VersionPattern

        # This should work as long as major is named
        pattern = VersionPattern(r"_v(?P<major>\d+)\.(\d+)")
        components = pattern.extract_version("prompt_v1.2.md")

        assert components is not None
        assert components.major == 1


class TestInvalidVersionPatternError:
    """Test InvalidVersionPatternError (T030)."""

    def test_error_contains_pattern(self) -> None:
        """Error should contain the invalid pattern."""
        from promptic.versioning.domain.errors import InvalidVersionPatternError

        error = InvalidVersionPatternError(
            pattern=r"_v(\d+)",
            reason="Missing named group",
        )

        assert r"_v(\d+)" in error.pattern
        assert "Missing named group" in error.reason
        assert r"_v(\d+)" in str(error)

    def test_error_with_custom_message(self) -> None:
        """Error should use custom message when provided."""
        from promptic.versioning.domain.errors import InvalidVersionPatternError

        error = InvalidVersionPatternError(
            pattern=r"[invalid",
            reason="Invalid regex",
            message="Custom error message",
        )

        assert str(error) == "Custom error message"

    def test_error_raised_by_version_pattern(self) -> None:
        """VersionPattern should raise InvalidVersionPatternError."""
        from promptic.versioning.domain.errors import InvalidVersionPatternError
        from promptic.versioning.domain.pattern import VersionPattern

        with pytest.raises(InvalidVersionPatternError) as exc_info:
            VersionPattern(r"[invalid(regex")

        assert "regex" in str(exc_info.value).lower()


class TestVersionComponents:
    """Test VersionComponents dataclass."""

    def test_version_components_creation(self) -> None:
        """VersionComponents should store version parts."""
        from promptic.versioning.domain.pattern import VersionComponents

        components = VersionComponents(major=1, minor=2, patch=3)

        assert components.major == 1
        assert components.minor == 2
        assert components.patch == 3
        assert components.prerelease is None
        assert components.classifiers == {}

    def test_version_components_with_prerelease(self) -> None:
        """VersionComponents should store prerelease."""
        from promptic.versioning.domain.pattern import VersionComponents

        components = VersionComponents(major=1, minor=0, patch=0, prerelease="alpha")

        assert components.prerelease == "alpha"

    def test_version_components_with_classifiers(self) -> None:
        """VersionComponents should store classifiers."""
        from promptic.versioning.domain.pattern import VersionComponents

        components = VersionComponents(
            major=1, minor=0, patch=0, classifiers={"lang": "en", "tone": "formal"}
        )

        assert components.classifiers == {"lang": "en", "tone": "formal"}

    def test_version_components_is_frozen(self) -> None:
        """VersionComponents should be immutable."""
        from promptic.versioning.domain.pattern import VersionComponents

        components = VersionComponents(major=1, minor=0, patch=0)

        with pytest.raises(Exception):  # FrozenInstanceError
            components.major = 2  # type: ignore[misc]
