"""Tests for prerelease version handling.

Tests for:
- SemanticVersion prerelease parsing (T037)
- Prerelease comparison ordering (T038)
- Property-based prerelease ordering consistency (T039)
- Integration test for "latest" with/without include_prerelease (T040)
"""

from __future__ import annotations

from pathlib import Path

import pytest


class TestSemanticVersionPrereleaseParsing:
    """Test SemanticVersion prerelease parsing (T037)."""

    def test_parse_alpha_prerelease(self) -> None:
        """Parse version with alpha prerelease."""
        from promptic.versioning.utils.semantic_version import SemanticVersion

        version = SemanticVersion.from_string("v1.0.0-alpha")

        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0
        assert version.prerelease == "alpha"

    def test_parse_beta_prerelease(self) -> None:
        """Parse version with beta prerelease."""
        from promptic.versioning.utils.semantic_version import SemanticVersion

        version = SemanticVersion.from_string("v2.1.0-beta")

        assert version.prerelease == "beta"

    def test_parse_rc_prerelease(self) -> None:
        """Parse version with rc prerelease."""
        from promptic.versioning.utils.semantic_version import SemanticVersion

        version = SemanticVersion.from_string("v3.0.0-rc")

        assert version.prerelease == "rc"

    def test_parse_numbered_prerelease(self) -> None:
        """Parse version with numbered prerelease like alpha.1."""
        from promptic.versioning.utils.semantic_version import SemanticVersion

        version = SemanticVersion.from_string("v1.0.0-alpha.1")

        assert version.prerelease == "alpha.1"

    def test_parse_version_without_prerelease(self) -> None:
        """Parse version without prerelease."""
        from promptic.versioning.utils.semantic_version import SemanticVersion

        version = SemanticVersion.from_string("v1.0.0")

        assert version.prerelease is None

    def test_str_with_prerelease(self) -> None:
        """String representation should include prerelease."""
        from promptic.versioning.utils.semantic_version import SemanticVersion

        version = SemanticVersion(major=1, minor=0, patch=0, prerelease="alpha")

        assert str(version) == "v1.0.0-alpha"

    def test_str_without_prerelease(self) -> None:
        """String representation without prerelease."""
        from promptic.versioning.utils.semantic_version import SemanticVersion

        version = SemanticVersion(major=1, minor=0, patch=0)

        assert str(version) == "v1.0.0"


class TestPrereleaseComparisonOrdering:
    """Test prerelease comparison ordering (T038)."""

    def test_release_greater_than_prerelease(self) -> None:
        """Release version > prerelease of same base version."""
        from promptic.versioning.utils.semantic_version import SemanticVersion

        release = SemanticVersion(1, 0, 0)
        prerelease = SemanticVersion(1, 0, 0, prerelease="alpha")

        assert release > prerelease
        assert prerelease < release

    def test_alpha_less_than_beta(self) -> None:
        """Alpha < beta of same base version."""
        from promptic.versioning.utils.semantic_version import SemanticVersion

        alpha = SemanticVersion(1, 0, 0, prerelease="alpha")
        beta = SemanticVersion(1, 0, 0, prerelease="beta")

        assert alpha < beta

    def test_beta_less_than_rc(self) -> None:
        """Beta < rc of same base version."""
        from promptic.versioning.utils.semantic_version import SemanticVersion

        beta = SemanticVersion(1, 0, 0, prerelease="beta")
        rc = SemanticVersion(1, 0, 0, prerelease="rc")

        assert beta < rc

    def test_numbered_prerelease_ordering(self) -> None:
        """Numbered prereleases ordered correctly: alpha.1 < alpha.2."""
        from promptic.versioning.utils.semantic_version import SemanticVersion

        alpha1 = SemanticVersion(1, 0, 0, prerelease="alpha.1")
        alpha2 = SemanticVersion(1, 0, 0, prerelease="alpha.2")

        assert alpha1 < alpha2

    def test_different_base_versions(self) -> None:
        """Higher base version > lower base version regardless of prerelease."""
        from promptic.versioning.utils.semantic_version import SemanticVersion

        v1_release = SemanticVersion(1, 0, 0)
        v2_alpha = SemanticVersion(2, 0, 0, prerelease="alpha")

        assert v2_alpha > v1_release

    def test_prerelease_ordering_is_stable(self) -> None:
        """Prerelease ordering should be stable across comparisons."""
        from promptic.versioning.utils.semantic_version import SemanticVersion

        versions = [
            SemanticVersion(1, 0, 0, prerelease="rc"),
            SemanticVersion(1, 0, 0, prerelease="alpha"),
            SemanticVersion(1, 0, 0),
            SemanticVersion(1, 0, 0, prerelease="beta"),
        ]

        sorted_versions = sorted(versions)

        assert sorted_versions[0].prerelease == "alpha"
        assert sorted_versions[1].prerelease == "beta"
        assert sorted_versions[2].prerelease == "rc"
        assert sorted_versions[3].prerelease is None  # Release


class TestPrereleaseOrderingConsistency:
    """Property-based tests for prerelease ordering consistency (T039)."""

    def test_transitivity(self) -> None:
        """If a < b and b < c, then a < c."""
        from promptic.versioning.utils.semantic_version import SemanticVersion

        a = SemanticVersion(1, 0, 0, prerelease="alpha")
        b = SemanticVersion(1, 0, 0, prerelease="beta")
        c = SemanticVersion(1, 0, 0, prerelease="rc")

        assert a < b
        assert b < c
        assert a < c  # Transitivity

    def test_reflexivity(self) -> None:
        """a == a always."""
        from promptic.versioning.utils.semantic_version import SemanticVersion

        a = SemanticVersion(1, 0, 0, prerelease="alpha")

        assert a == a
        assert not (a < a)
        assert not (a > a)

    def test_antisymmetry(self) -> None:
        """If a < b, then not (b < a)."""
        from promptic.versioning.utils.semantic_version import SemanticVersion

        a = SemanticVersion(1, 0, 0, prerelease="alpha")
        b = SemanticVersion(1, 0, 0, prerelease="beta")

        assert a < b
        assert not (b < a)

    def test_total_ordering(self) -> None:
        """All versions should be comparable."""
        from promptic.versioning.utils.semantic_version import SemanticVersion

        versions = [
            SemanticVersion(1, 0, 0),
            SemanticVersion(1, 0, 0, prerelease="alpha"),
            SemanticVersion(1, 0, 0, prerelease="alpha.1"),
            SemanticVersion(1, 0, 0, prerelease="beta"),
            SemanticVersion(1, 0, 1),
            SemanticVersion(2, 0, 0, prerelease="alpha"),
        ]

        # Should be sortable without errors
        sorted_versions = sorted(versions)
        assert len(sorted_versions) == len(versions)


class TestLatestWithPrerelease:
    """Integration tests for "latest" with/without include_prerelease (T040)."""

    def test_latest_excludes_prerelease_by_default(self, tmp_path: Path) -> None:
        """Latest should exclude prereleases by default."""
        from promptic.versioning.adapters.scanner import VersionedFileScanner
        from promptic.versioning.config import VersioningConfig

        # Create files
        (tmp_path / "prompt_v1.0.0.md").write_text("Release v1")
        (tmp_path / "prompt_v1.0.1-alpha.md").write_text("Alpha")
        (tmp_path / "prompt_v1.0.1.md").write_text("Release v1.0.1")

        config = VersioningConfig(include_prerelease=False)
        scanner = VersionedFileScanner(config=config)

        resolved = scanner.resolve_version(str(tmp_path), "latest")

        # Should return v1.0.1 (release), not v1.0.1-alpha
        assert "prompt_v1.0.1.md" in resolved
        assert "alpha" not in resolved.lower()

    def test_latest_includes_prerelease_when_enabled(self, tmp_path: Path) -> None:
        """Latest should include prereleases when include_prerelease=True."""
        from promptic.versioning.adapters.scanner import VersionedFileScanner
        from promptic.versioning.config import VersioningConfig

        # Create files - only prereleases
        (tmp_path / "prompt_v1.0.0.md").write_text("Release v1")
        (tmp_path / "prompt_v2.0.0-alpha.md").write_text("Alpha v2")

        config = VersioningConfig(include_prerelease=True)
        scanner = VersionedFileScanner(config=config)

        resolved = scanner.resolve_version(str(tmp_path), "latest")

        # Should consider alpha in latest calculation
        # v2.0.0-alpha > v1.0.0 (different base versions)
        assert "prompt_v2.0.0-alpha.md" in resolved

    def test_explicit_prerelease_request_works(self, tmp_path: Path) -> None:
        """Explicit prerelease version request should work regardless of setting."""
        from promptic.versioning.adapters.scanner import VersionedFileScanner
        from promptic.versioning.config import VersioningConfig

        (tmp_path / "prompt_v1.0.0.md").write_text("Release")
        (tmp_path / "prompt_v1.0.1-alpha.md").write_text("Alpha")

        # Even with include_prerelease=False
        config = VersioningConfig(include_prerelease=False)
        scanner = VersionedFileScanner(config=config)

        # Explicit request should still work
        # Note: This requires normalizing "v1.0.1-alpha" properly
        resolved = scanner.resolve_version(str(tmp_path), "v1.0.1-alpha")

        assert "alpha" in resolved.lower()

    def test_only_prereleases_returns_first_prerelease(self, tmp_path: Path) -> None:
        """When only prereleases exist, latest should return the latest prerelease."""
        from promptic.versioning.adapters.scanner import VersionedFileScanner
        from promptic.versioning.config import VersioningConfig

        # Only prerelease files
        (tmp_path / "prompt_v1.0.0-alpha.md").write_text("Alpha v1")
        (tmp_path / "prompt_v1.0.0-beta.md").write_text("Beta v1")
        (tmp_path / "prompt_v1.0.0-rc.md").write_text("RC v1")

        config = VersioningConfig(include_prerelease=False)
        scanner = VersionedFileScanner(config=config)

        # Should still return something (the latest prerelease) with warning
        resolved = scanner.resolve_version(str(tmp_path), "latest")

        # Should return rc (latest prerelease)
        assert "prompt_v1.0.0-rc.md" in resolved

    def test_release_takes_precedence_over_prerelease(self, tmp_path: Path) -> None:
        """Release v1.0.1 > prerelease v1.0.1-rc of same base."""
        from promptic.versioning.adapters.scanner import VersionedFileScanner
        from promptic.versioning.config import VersioningConfig

        (tmp_path / "prompt_v1.0.1-rc.md").write_text("RC")
        (tmp_path / "prompt_v1.0.1.md").write_text("Release")

        config = VersioningConfig(include_prerelease=True)
        scanner = VersionedFileScanner(config=config)

        resolved = scanner.resolve_version(str(tmp_path), "latest")

        # Release should win over prerelease of same base version
        assert "prompt_v1.0.1.md" in resolved
        assert "-rc" not in resolved
