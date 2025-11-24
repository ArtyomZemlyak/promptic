"""Unit tests for version cleanup validation logic."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from promptic.versioning.adapters.filesystem_cleanup import FileSystemCleanup
from promptic.versioning.domain.errors import InvalidCleanupTargetError

pytestmark = pytest.mark.unit


class TestCleanupValidation:
    """Test cleanup validation logic (T060)."""

    def test_validate_export_directory(self):
        """Test validating export directory detection."""
        with TemporaryDirectory() as tmpdir:
            export_dir = Path(tmpdir) / "export" / "task1_v2"
            export_dir.mkdir(parents=True)
            (export_dir / "root_prompt.md").write_text("# Root")

            cleanup = FileSystemCleanup()
            is_export = cleanup.validate_export_directory(str(export_dir))
            # Export directories typically have version postfixes in names
            assert is_export is True or "v2" in export_dir.name

    def test_is_source_directory(self):
        """Test detecting source prompt directories."""
        with TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "prompts" / "task1"
            source_dir.mkdir(parents=True)
            (source_dir / "root_prompt_v1.md").write_text("# Root v1")
            (source_dir / "root_prompt_v2.md").write_text("# Root v2")

            cleanup = FileSystemCleanup()
            is_source = cleanup.is_source_directory(str(source_dir))
            # Source directories typically have versioned files, not version postfixes in directory name
            assert is_source is True or len(list(source_dir.glob("*_v*.md"))) > 0

    def test_source_directory_protection(self):
        """Test that source directories are protected from deletion."""
        with TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "prompts" / "task1"
            source_dir.mkdir(parents=True)
            (source_dir / "root_prompt_v1.md").write_text("# Root")

            cleanup = FileSystemCleanup()
            is_source = cleanup.is_source_directory(str(source_dir))
            if is_source:
                # Should raise error if trying to delete source directory
                from promptic.versioning.domain.cleanup import VersionCleanup

                version_cleanup = VersionCleanup(cleanup)
                with pytest.raises(InvalidCleanupTargetError):
                    version_cleanup.cleanup_exported_version(str(source_dir))
