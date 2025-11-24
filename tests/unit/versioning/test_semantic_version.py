"""Unit tests for semantic versioning utilities."""

import pytest

from promptic.versioning.utils.semantic_version import (
    SemanticVersion,
    compare_versions,
    get_latest_version,
    normalize_version,
)

pytestmark = pytest.mark.unit


class TestSemanticVersion:
    """Test SemanticVersion dataclass."""

    def test_from_string_full_version(self):
        """Test parsing full semantic version (v1.0.0)."""
        version = SemanticVersion.from_string("v1.0.0")
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0

    def test_from_string_minor_version(self):
        """Test parsing minor version (v1.1.0)."""
        version = SemanticVersion.from_string("v1.1.0")
        assert version.major == 1
        assert version.minor == 1
        assert version.patch == 0

    def test_from_string_patch_version(self):
        """Test parsing patch version (v1.1.1)."""
        version = SemanticVersion.from_string("v1.1.1")
        assert version.major == 1
        assert version.minor == 1
        assert version.patch == 1

    def test_from_string_without_v_prefix(self):
        """Test parsing version without 'v' prefix."""
        version = SemanticVersion.from_string("1.0.0")
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0

    def test_from_string_invalid(self):
        """Test parsing invalid version string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid version string"):
            SemanticVersion.from_string("invalid")

    def test_str_representation(self):
        """Test string representation."""
        version = SemanticVersion(major=1, minor=2, patch=3)
        assert str(version) == "v1.2.3"

    def test_comparison_less_than(self):
        """Test version comparison (less than)."""
        v1 = SemanticVersion(major=1, minor=0, patch=0)
        v2 = SemanticVersion(major=2, minor=0, patch=0)
        assert v1 < v2

    def test_comparison_equal(self):
        """Test version comparison (equal)."""
        v1 = SemanticVersion(major=1, minor=0, patch=0)
        v2 = SemanticVersion(major=1, minor=0, patch=0)
        assert v1 == v2

    def test_comparison_greater_than(self):
        """Test version comparison (greater than)."""
        v1 = SemanticVersion(major=2, minor=0, patch=0)
        v2 = SemanticVersion(major=1, minor=0, patch=0)
        assert v1 > v2

    def test_comparison_minor_version(self):
        """Test comparison with different minor versions."""
        v1 = SemanticVersion(major=1, minor=0, patch=0)
        v2 = SemanticVersion(major=1, minor=1, patch=0)
        assert v1 < v2

    def test_comparison_patch_version(self):
        """Test comparison with different patch versions."""
        v1 = SemanticVersion(major=1, minor=1, patch=0)
        v2 = SemanticVersion(major=1, minor=1, patch=1)
        assert v1 < v2


class TestNormalizeVersion:
    """Test version normalization (T015)."""

    def test_normalize_v1_to_v1_0_0(self):
        """Test normalization of v1 to v1.0.0."""
        normalized = normalize_version("v1")
        assert normalized.major == 1
        assert normalized.minor == 0
        assert normalized.patch == 0

    def test_normalize_v1_1_to_v1_1_0(self):
        """Test normalization of v1.1 to v1.1.0."""
        normalized = normalize_version("v1.1")
        assert normalized.major == 1
        assert normalized.minor == 1
        assert normalized.patch == 0

    def test_normalize_v1_1_1_unchanged(self):
        """Test normalization of v1.1.1 (no change)."""
        normalized = normalize_version("v1.1.1")
        assert normalized.major == 1
        assert normalized.minor == 1
        assert normalized.patch == 1

    def test_normalize_without_v_prefix(self):
        """Test normalization without 'v' prefix."""
        normalized = normalize_version("1.0.0")
        assert normalized.major == 1
        assert normalized.minor == 0
        assert normalized.patch == 0


class TestCompareVersions:
    """Test version comparison logic (T016)."""

    def test_compare_versions_less_than(self):
        """Test comparing versions (less than)."""
        v1 = SemanticVersion(major=1, minor=0, patch=0)
        v2 = SemanticVersion(major=2, minor=0, patch=0)
        assert compare_versions(v1, v2) == -1

    def test_compare_versions_equal(self):
        """Test comparing versions (equal)."""
        v1 = SemanticVersion(major=1, minor=0, patch=0)
        v2 = SemanticVersion(major=1, minor=0, patch=0)
        assert compare_versions(v1, v2) == 0

    def test_compare_versions_greater_than(self):
        """Test comparing versions (greater than)."""
        v1 = SemanticVersion(major=2, minor=0, patch=0)
        v2 = SemanticVersion(major=1, minor=0, patch=0)
        assert compare_versions(v1, v2) == 1

    def test_compare_versions_semantic_precedence(self):
        """Test semantic versioning precedence rules (major.minor.patch)."""
        versions = [
            SemanticVersion(major=1, minor=0, patch=0),
            SemanticVersion(major=1, minor=1, patch=0),
            SemanticVersion(major=1, minor=1, patch=1),
            SemanticVersion(major=2, minor=0, patch=0),
        ]
        # Verify ordering
        assert versions[0] < versions[1] < versions[2] < versions[3]


class TestGetLatestVersion:
    """Test latest version determination (T016)."""

    def test_get_latest_version_single(self):
        """Test getting latest from single version."""
        versions = [SemanticVersion(major=1, minor=0, patch=0)]
        latest = get_latest_version(versions)
        assert latest == versions[0]

    def test_get_latest_version_multiple(self):
        """Test getting latest from multiple versions."""
        versions = [
            SemanticVersion(major=1, minor=0, patch=0),
            SemanticVersion(major=1, minor=1, patch=0),
            SemanticVersion(major=2, minor=0, patch=0),
        ]
        latest = get_latest_version(versions)
        assert latest == versions[2]  # v2.0.0

    def test_get_latest_version_empty(self):
        """Test getting latest from empty list returns None."""
        latest = get_latest_version([])
        assert latest is None

    def test_get_latest_version_semantic_ordering(self):
        """Test latest version uses semantic versioning comparison rules."""
        versions = [
            SemanticVersion(major=1, minor=2, patch=3),
            SemanticVersion(major=1, minor=0, patch=0),
            SemanticVersion(major=1, minor=1, patch=0),
        ]
        latest = get_latest_version(versions)
        assert latest == versions[0]  # v1.2.3
