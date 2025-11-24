"""Integration tests for cleaning up exported directories."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from promptic.versioning.domain.cleanup import VersionCleanup
from promptic.versioning.domain.errors import CleanupTargetNotFoundError, InvalidCleanupTargetError

pytestmark = pytest.mark.integration


class TestVersionCleanup:
    """Integration test for cleaning up exported directories (T061)."""

    def test_cleanup_exported_directory(self):
        """Test safely deleting exported directory."""
        with TemporaryDirectory() as tmpdir:
            export_dir = Path(tmpdir) / "export" / "task1_v2"
            export_dir.mkdir(parents=True)
            (export_dir / "root_prompt.md").write_text("# Root")
            (export_dir / "instructions").mkdir()
            (export_dir / "instructions" / "process.md").write_text("# Process")

            cleanup = VersionCleanup()
            cleanup.cleanup_exported_version(str(export_dir))

            # Directory should be deleted
            assert not export_dir.exists()

    def test_cleanup_recursive_removal(self):
        """Test that cleanup recursively removes directory contents."""
        with TemporaryDirectory() as tmpdir:
            export_dir = Path(tmpdir) / "export" / "task1_v2"
            export_dir.mkdir(parents=True)
            (export_dir / "file1.md").write_text("# File 1")
            (export_dir / "nested").mkdir()
            (export_dir / "nested" / "file2.md").write_text("# File 2")
            (export_dir / "nested" / "deep").mkdir()
            (export_dir / "nested" / "deep" / "file3.md").write_text("# File 3")

            cleanup = VersionCleanup()
            cleanup.cleanup_exported_version(str(export_dir))

            # All nested files and directories should be removed
            assert not export_dir.exists()

    def test_cleanup_source_directory_protection(self):
        """Test that source directories cannot be deleted."""
        with TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "prompts" / "task1"
            source_dir.mkdir(parents=True)
            (source_dir / "root_prompt_v1.md").write_text("# Root v1")
            (source_dir / "root_prompt_v2.md").write_text("# Root v2")

            cleanup = VersionCleanup()
            with pytest.raises(InvalidCleanupTargetError):
                cleanup.cleanup_exported_version(str(source_dir))

            # Source directory should still exist
            assert source_dir.exists()

    def test_cleanup_nonexistent_directory(self):
        """Test that cleanup raises error for non-existent directories."""
        with TemporaryDirectory() as tmpdir:
            nonexistent = Path(tmpdir) / "export" / "nonexistent"

            cleanup = VersionCleanup()
            with pytest.raises(CleanupTargetNotFoundError):
                cleanup.cleanup_exported_version(str(nonexistent))
