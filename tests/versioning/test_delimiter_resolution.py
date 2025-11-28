"""Integration tests for delimiter-based version resolution.

Tests for:
- Delimiter resolution (T016)
- Custom pattern resolution (T031 - Phase 4)
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


class TestDelimiterResolution:
    """Integration tests for delimiter-based version resolution (T016)."""

    def test_hyphen_delimiter_resolution(self, tmp_path: Path) -> None:
        """Resolution should work with hyphen delimiter."""
        from promptic.versioning.adapters.scanner import VersionedFileScanner
        from promptic.versioning.config import VersioningConfig

        # Create test files with hyphen delimiter
        (tmp_path / "prompt-v1.md").write_text("Version 1")
        (tmp_path / "prompt-v2.md").write_text("Version 2")
        (tmp_path / "prompt-v3.md").write_text("Version 3")

        config = VersioningConfig(delimiter="-")
        scanner = VersionedFileScanner(config=config)

        resolved_path = scanner.resolve_version(str(tmp_path), "latest")

        assert "prompt-v3.md" in resolved_path
        assert Path(resolved_path).read_text() == "Version 3"

    def test_underscore_delimiter_resolution(self, tmp_path: Path) -> None:
        """Resolution should work with underscore delimiter (default)."""
        from promptic.versioning.adapters.scanner import VersionedFileScanner
        from promptic.versioning.config import VersioningConfig

        # Create test files with underscore delimiter
        (tmp_path / "prompt_v1.md").write_text("Version 1")
        (tmp_path / "prompt_v2.md").write_text("Version 2")

        config = VersioningConfig(delimiter="_")
        scanner = VersionedFileScanner(config=config)

        resolved_path = scanner.resolve_version(str(tmp_path), "latest")

        assert "prompt_v2.md" in resolved_path

    def test_dot_delimiter_resolution(self, tmp_path: Path) -> None:
        """Resolution should work with dot delimiter."""
        from promptic.versioning.adapters.scanner import VersionedFileScanner
        from promptic.versioning.config import VersioningConfig

        # Create test files with dot delimiter
        (tmp_path / "prompt.v1.md").write_text("Version 1")
        (tmp_path / "prompt.v2.md").write_text("Version 2")

        config = VersioningConfig(delimiter=".")
        scanner = VersionedFileScanner(config=config)

        resolved_path = scanner.resolve_version(str(tmp_path), "latest")

        assert "prompt.v2.md" in resolved_path

    def test_multiple_delimiters_resolution(self, tmp_path: Path) -> None:
        """Resolution should work with multiple delimiters."""
        from promptic.versioning.adapters.scanner import VersionedFileScanner
        from promptic.versioning.config import VersioningConfig

        # Create test files with mixed delimiters
        (tmp_path / "prompt_v1.md").write_text("Underscore v1")
        (tmp_path / "prompt-v2.md").write_text("Hyphen v2")
        (tmp_path / "task_v3.md").write_text("Underscore v3")

        config = VersioningConfig(delimiters=["_", "-"])
        scanner = VersionedFileScanner(config=config)

        resolved_path = scanner.resolve_version(str(tmp_path), "latest")

        assert "task_v3.md" in resolved_path

    def test_specific_version_resolution_with_delimiter(self, tmp_path: Path) -> None:
        """Specific version resolution should work with custom delimiter."""
        from promptic.versioning.adapters.scanner import VersionedFileScanner
        from promptic.versioning.config import VersioningConfig

        # Create test files
        (tmp_path / "prompt-v1.md").write_text("Version 1")
        (tmp_path / "prompt-v2.md").write_text("Version 2")
        (tmp_path / "prompt-v3.md").write_text("Version 3")

        config = VersioningConfig(delimiter="-")
        scanner = VersionedFileScanner(config=config)

        resolved_path = scanner.resolve_version(str(tmp_path), "v2")

        assert "prompt-v2.md" in resolved_path
        assert Path(resolved_path).read_text() == "Version 2"

    def test_wrong_delimiter_finds_nothing(self, tmp_path: Path) -> None:
        """Wrong delimiter should not find versioned files."""
        from promptic.versioning import VersionNotFoundError
        from promptic.versioning.adapters.scanner import VersionedFileScanner
        from promptic.versioning.config import VersioningConfig

        # Create test files with underscore delimiter
        (tmp_path / "prompt_v1.md").write_text("Version 1")
        (tmp_path / "prompt_v2.md").write_text("Version 2")

        # Use hyphen delimiter - should not match underscore files
        config = VersioningConfig(delimiter="-")
        scanner = VersionedFileScanner(config=config)

        # Should find files but they're unversioned, falls back to first unversioned
        # OR should raise VersionNotFoundError if strict
        result = scanner.scan_directory(str(tmp_path))
        versioned = [v for v in result if v.is_versioned]
        assert len(versioned) == 0


class TestCustomPatternResolution:
    """Integration tests for custom pattern resolution (T031 - Phase 4)."""

    def test_custom_pattern_resolution(self, tmp_path: Path) -> None:
        """Custom pattern should work for version resolution."""
        from promptic.versioning.adapters.scanner import VersionedFileScanner
        from promptic.versioning.config import VersioningConfig

        # Create test files with custom pattern
        (tmp_path / "prompt_rev1.md").write_text("Rev 1")
        (tmp_path / "prompt_rev42.md").write_text("Rev 42")
        (tmp_path / "prompt_rev5.md").write_text("Rev 5")

        config = VersioningConfig(version_pattern=r"_rev(?P<major>\d+)")
        scanner = VersionedFileScanner(config=config)

        resolved_path = scanner.resolve_version(str(tmp_path), "latest")

        assert "prompt_rev42.md" in resolved_path
