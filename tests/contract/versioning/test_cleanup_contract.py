"""Contract tests for cleanup interface."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from promptic.versioning.domain.cleanup import VersionCleanup
from promptic.versioning.domain.errors import CleanupTargetNotFoundError, InvalidCleanupTargetError

pytestmark = pytest.mark.contract


class TestCleanupContract:
    """Contract test for cleanup interface (T062)."""

    def test_cleanup_exported_version_method_exists(self):
        """Test VersionCleanup has cleanup_exported_version method."""
        cleanup = VersionCleanup()
        assert hasattr(cleanup, "cleanup_exported_version")

    def test_safe_deletion_contract(self):
        """Test that cleanup safely deletes export directories."""
        with TemporaryDirectory() as tmpdir:
            export_dir = Path(tmpdir) / "export" / "task1_v2"
            export_dir.mkdir(parents=True)
            (export_dir / "file.md").write_text("# File")

            cleanup = VersionCleanup()
            cleanup.cleanup_exported_version(str(export_dir))

            # Directory should be deleted
            assert not export_dir.exists()

    def test_export_directory_detection(self):
        """Test that cleanup detects export directories correctly."""
        with TemporaryDirectory() as tmpdir:
            export_dir = Path(tmpdir) / "export" / "task1_v2"
            export_dir.mkdir(parents=True)

            cleanup = VersionCleanup()
            # Should be able to clean up export directory
            cleanup.cleanup_exported_version(str(export_dir))
            assert not export_dir.exists()

    def test_source_directory_protection_contract(self):
        """Test that source directories are protected from deletion."""
        with TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "prompts" / "task1"
            source_dir.mkdir(parents=True)
            (source_dir / "root_prompt_v1.md").write_text("# Root")

            cleanup = VersionCleanup()
            with pytest.raises(InvalidCleanupTargetError):
                cleanup.cleanup_exported_version(str(source_dir))

            # Source directory should still exist
            assert source_dir.exists()

    def test_cleanup_target_not_found_contract(self):
        """Test that cleanup raises error for non-existent targets."""
        with TemporaryDirectory() as tmpdir:
            nonexistent = Path(tmpdir) / "export" / "nonexistent"

            cleanup = VersionCleanup()
            with pytest.raises(CleanupTargetNotFoundError):
                cleanup.cleanup_exported_version(str(nonexistent))
