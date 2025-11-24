"""Unit tests for version detection logic."""

import pytest

from promptic.versioning.adapters.scanner import VersionedFileScanner
from promptic.versioning.utils.semantic_version import SemanticVersion

pytestmark = pytest.mark.unit


class TestVersionDetection:
    """Test version detection from filenames (T014)."""

    def test_extract_version_v1(self):
        """Test extracting version _v1 from filename."""
        scanner = VersionedFileScanner()
        version = scanner.extract_version_from_filename("prompt_v1.md")
        assert version is not None
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0

    def test_extract_version_v1_1(self):
        """Test extracting version _v1.1 from filename."""
        scanner = VersionedFileScanner()
        version = scanner.extract_version_from_filename("prompt_v1.1.md")
        assert version is not None
        assert version.major == 1
        assert version.minor == 1
        assert version.patch == 0

    def test_extract_version_v1_1_1(self):
        """Test extracting version _v1.1.1 from filename."""
        scanner = VersionedFileScanner()
        version = scanner.extract_version_from_filename("prompt_v1.1.1.md")
        assert version is not None
        assert version.major == 1
        assert version.minor == 1
        assert version.patch == 1

    def test_extract_version_no_version(self):
        """Test extracting version from unversioned filename returns None."""
        scanner = VersionedFileScanner()
        version = scanner.extract_version_from_filename("prompt.md")
        assert version is None

    def test_extract_version_multiple_patterns(self):
        """Test extracting version when multiple patterns exist (uses last)."""
        scanner = VersionedFileScanner()
        # Filename with multiple version patterns
        version = scanner.extract_version_from_filename("prompt_v1.0_final_v2.1.md")
        assert version is not None
        # Should use last pattern (v2.1)
        assert version.major == 2
        assert version.minor == 1

    def test_extract_version_various_formats(self):
        """Test extracting versions in various formats."""
        scanner = VersionedFileScanner()
        test_cases = [
            ("root_prompt_v1.md", 1, 0, 0),
            ("root_prompt_v1.0.md", 1, 0, 0),
            ("root_prompt_v1.0.0.md", 1, 0, 0),
            ("root_prompt_v2.1.md", 2, 1, 0),
            ("root_prompt_v2.1.3.md", 2, 1, 3),
        ]
        for filename, major, minor, patch in test_cases:
            version = scanner.extract_version_from_filename(filename)
            assert version is not None, f"Failed to extract version from {filename}"
            assert version.major == major
            assert version.minor == minor
            assert version.patch == patch
