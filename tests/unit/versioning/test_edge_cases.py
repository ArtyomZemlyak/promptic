from pathlib import Path

import pytest

from promptic.versioning.adapters.scanner import VersionedFileScanner
from promptic.versioning.domain.errors import VersionDetectionError, VersionNotFoundError
from promptic.versioning.domain.resolver import VersionResolver
from promptic.versioning.utils.semantic_version import SemanticVersion


class TestEdgeCases:
    def test_ambiguous_version_detection(self):
        """Test that ambiguous versions are handled correctly or raise error."""
        # Assuming scanner behavior, if we have file_v1.md and file_v1.0.0.md,
        # they normalize to the same version.
        # The scanner might deduplicate or raise error.
        # Let's see what it does.

        scanner = VersionedFileScanner()
        # We mock the filesystem scan
        # Actually, let's test the normalization logic directly first

        v1 = SemanticVersion.from_string("v1")
        v1_0_0 = SemanticVersion.from_string("v1.0.0")
        assert v1 == v1_0_0

    def test_empty_directory_scan(self, tmp_path):
        """Test scanning an empty directory."""
        scanner = VersionedFileScanner()
        versions = scanner.scan_directory(str(tmp_path))
        assert len(versions) == 0

        # get_latest_version expects a list of versions, not a path
        latest = scanner.get_latest_version([])
        assert latest is None

    def test_mixed_content_scan(self, tmp_path):
        """Test scanning a directory with versioned and unversioned files."""
        (tmp_path / "file.md").touch()
        (tmp_path / "file_v1.md").touch()
        (tmp_path / "file_v2.md").touch()
        (tmp_path / "other.txt").touch()

        scanner = VersionedFileScanner()
        versions = scanner.scan_directory(str(tmp_path))

        # Should find all 4 files (v1, v2, file.md, other.txt)
        assert len(versions) == 4

        # First two should be versioned and sorted
        assert versions[0].version == SemanticVersion.from_string("v2.0.0")
        assert versions[1].version == SemanticVersion.from_string("v1.0.0")

        # Latest resolution should work via resolve_version
        path = scanner.resolve_version(str(tmp_path), "latest")
        assert path.endswith("file_v2.md")

    def test_unversioned_only(self, tmp_path):
        """Test scanning a directory with only unversioned files."""
        (tmp_path / "file.md").touch()

        scanner = VersionedFileScanner()
        versions = scanner.scan_directory(str(tmp_path))

        # Should find 1 unversioned file
        assert len(versions) == 1
        assert versions[0].is_versioned is False

        resolved = scanner.resolve_version(str(tmp_path), "latest")
        assert resolved == str(tmp_path / "file.md")

    def test_version_not_found(self, tmp_path):
        """Test requesting a non-existent version."""
        (tmp_path / "file_v1.md").touch()

        scanner = VersionedFileScanner()
        with pytest.raises(VersionNotFoundError):
            scanner.resolve_version(str(tmp_path), "v2")

    def test_directory_without_files(self, tmp_path):
        """Test resolving in a directory with no files."""
        scanner = VersionedFileScanner()
        with pytest.raises(VersionNotFoundError):
            scanner.resolve_version(str(tmp_path), "latest")

    def test_multiple_files_same_base_different_versions(self, tmp_path):
        """Test directory with multiple versioned files with same base name."""
        (tmp_path / "prompt_v1.0.0.md").write_text("Version 1.0.0")
        (tmp_path / "prompt_v1.1.0.md").write_text("Version 1.1.0")
        (tmp_path / "prompt_v2.0.0.md").write_text("Version 2.0.0")
        (tmp_path / "prompt_v2.1.0.md").write_text("Version 2.1.0")

        scanner = VersionedFileScanner()

        # Resolve latest (should be v2.1.0)
        latest = scanner.resolve_version(str(tmp_path), "latest")
        assert latest.endswith("prompt_v2.1.0.md")
        assert Path(latest).read_text() == "Version 2.1.0"

        # Resolve specific versions
        v1 = scanner.resolve_version(str(tmp_path), "v1.0.0")
        assert v1.endswith("prompt_v1.0.0.md")

        v2 = scanner.resolve_version(str(tmp_path), "v2.0.0")
        assert v2.endswith("prompt_v2.0.0.md")

    def test_simplified_version_resolution(self, tmp_path):
        """Test that simplified version specs resolve correctly."""
        (tmp_path / "prompt_v1.0.0.md").write_text("Version 1.0.0")
        (tmp_path / "prompt_v1.1.0.md").write_text("Version 1.1.0")
        (tmp_path / "prompt_v2.0.0.md").write_text("Version 2.0.0")

        scanner = VersionedFileScanner()

        # v1 (normalized to v1.0.0) should match prompt_v1.0.0.md exactly
        v1_resolved = scanner.resolve_version(str(tmp_path), "v1")
        assert v1_resolved.endswith("prompt_v1.0.0.md")

        # v1.1 (normalized to v1.1.0) should match prompt_v1.1.0.md exactly
        v1_1_resolved = scanner.resolve_version(str(tmp_path), "v1.1")
        assert v1_1_resolved.endswith("prompt_v1.1.0.md")

        # v2 (normalized to v2.0.0) should match prompt_v2.0.0.md exactly
        v2_resolved = scanner.resolve_version(str(tmp_path), "v2")
        assert v2_resolved.endswith("prompt_v2.0.0.md")

    def test_invalid_version_spec_format(self, tmp_path):
        """Test handling of invalid version specifications."""
        (tmp_path / "prompt_v1.md").write_text("Version 1")

        scanner = VersionedFileScanner()

        # Invalid version format should raise error
        with pytest.raises((VersionNotFoundError, ValueError)):
            scanner.resolve_version(str(tmp_path), "invalid")

        with pytest.raises((VersionNotFoundError, ValueError)):
            scanner.resolve_version(str(tmp_path), "v1.x.x")

    def test_nonexistent_directory(self):
        """Test resolving in a nonexistent directory."""
        scanner = VersionedFileScanner()
        nonexistent = Path("/tmp/nonexistent_test_dir_12345")

        with pytest.raises((VersionNotFoundError, FileNotFoundError)):
            scanner.resolve_version(str(nonexistent), "latest")

    def test_cache_invalidation_on_directory_change(self, tmp_path):
        """Test that cache is invalidated when directory contents change."""
        import os
        import time

        (tmp_path / "prompt_v1.md").write_text("Version 1")

        scanner = VersionedFileScanner()

        # First scan (cache populated)
        first_scan = scanner.scan_directory(str(tmp_path))
        assert len(first_scan) == 1

        # Add new file
        time.sleep(0.1)  # Ensure mtime changes
        (tmp_path / "prompt_v2.md").write_text("Version 2")

        # Touch the directory to update modification time
        os.utime(tmp_path, None)

        # Second scan (should detect new file after cache invalidation)
        second_scan = scanner.scan_directory(str(tmp_path))
        assert len(second_scan) == 2
