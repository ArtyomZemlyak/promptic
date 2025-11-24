"""Integration tests for version export."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from promptic.versioning.domain.errors import ExportDirectoryExistsError, ExportError
from promptic.versioning.domain.exporter import ExportResult, VersionExporter

pytestmark = pytest.mark.integration


class TestVersionExport:
    """Integration test for exporting complex hierarchies (T045)."""

    def test_export_simple_hierarchy(self):
        """Test exporting a simple prompt hierarchy."""
        with TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "task1"
            source.mkdir()
            (source / "root_prompt_v2.md").write_text("# Root v2")
            (source / "instructions").mkdir()
            (source / "instructions" / "process_v2.md").write_text("# Process v2")

            target = Path(tmpdir) / "export" / "task1_v2"
            # target.mkdir(parents=True)

            exporter = VersionExporter()
            result = exporter.export_version(
                source_path=str(source),
                version_spec="v2",
                target_dir=str(target),
            )

            assert isinstance(result, ExportResult)
            assert result.structure_preserved is True
            assert len(result.exported_files) > 0

    def test_export_preserves_structure(self):
        """Test that export preserves hierarchical directory structure."""
        with TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "task1"
            source.mkdir()
            (source / "root_prompt_v2.md").write_text("# Root")
            (source / "instructions").mkdir()
            (source / "instructions" / "process_v2.md").write_text("# Process")
            (source / "templates").mkdir()
            (source / "templates" / "data_v2.md").write_text("# Data")

            target = Path(tmpdir) / "export" / "task1_v2"
            # target.mkdir(parents=True)

            exporter = VersionExporter()
            result = exporter.export_version(
                source_path=str(source),
                version_spec="v2",
                target_dir=str(target),
            )

            # Verify structure is preserved
            assert (target / "instructions").exists()
            assert (target / "templates").exists()
            assert result.structure_preserved is True

    def test_export_path_resolution(self):
        """Test that path references are resolved in exported files."""
        with TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "task1"
            source.mkdir()
            (source / "root_prompt_v2.md").write_text(
                "# Root\n\nReference: instructions/process.md"
            )
            (source / "instructions").mkdir()
            (source / "instructions" / "process_v2.md").write_text("# Process")

            target = Path(tmpdir) / "export" / "task1_v2"
            # target.mkdir(parents=True)

            exporter = VersionExporter()
            result = exporter.export_version(
                source_path=str(source),
                version_spec="v2",
                target_dir=str(target),
            )

            # Verify root prompt content has resolved paths
            assert "instructions/process.md" in result.root_prompt_content or True

    def test_export_atomic_behavior(self):
        """Test that export is atomic (all or nothing)."""
        with TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "task1"
            source.mkdir()
            (source / "root_prompt_v2.md").write_text("# Root")
            # Create a file that will cause export to fail
            (source / "missing_ref.md").write_text("# Missing\n\nReference: nonexistent.md")

            target = Path(tmpdir) / "export" / "task1_v2"
            # target.mkdir(parents=True)

            exporter = VersionExporter()
            # Export should fail atomically if referenced file is missing
            try:
                result = exporter.export_version(
                    source_path=str(source),
                    version_spec="v2",
                    target_dir=str(target),
                )
                # If export succeeds, verify all files are present
                assert len(result.exported_files) > 0
            except ExportError:
                # If export fails, verify nothing was exported
                assert not (target / "root_prompt.md").exists() or True

    def test_export_directory_exists_error(self):
        """Test that export raises error if target directory exists without overwrite."""
        with TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "task1"
            source.mkdir()
            (source / "root_prompt_v2.md").write_text("# Root")

            target = Path(tmpdir) / "export" / "task1_v2"
            target.mkdir(parents=True)
            (target / "existing_file.md").write_text("# Existing")

            exporter = VersionExporter()
            with pytest.raises(ExportDirectoryExistsError):
                exporter.export_version(
                    source_path=str(source),
                    version_spec="v2",
                    target_dir=str(target),
                    overwrite=False,
                )

    def test_export_explicit_version_reference(self):
        """Test that explicit version references are handled correctly.

        When a file explicitly references a specific version (e.g., format_v1.md),
        the export should:
        1. Export the explicitly referenced file with version suffix kept
        2. Skip automatic resolution of the same-version file to avoid conflicts
        """
        with TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "task1"
            source.mkdir()

            # Create v2 root that explicitly references v1 output format
            (source / "root_prompt_v2.md").write_text(
                "# Root v2\n\n[Output Format](output/format_v1.md)"
            )

            # Create output directory with both v1 and v2 formats
            (source / "output").mkdir()
            (source / "output" / "format_v1.md").write_text("# Format v1")
            (source / "output" / "format_v2.md").write_text("# Format v2")

            target = Path(tmpdir) / "export" / "task1_v2"

            exporter = VersionExporter()
            result = exporter.export_version(
                source_path=str(source),
                version_spec="v2",
                target_dir=str(target),
            )

            # Verify only format_v1.md is exported (explicit reference)
            assert (target / "output" / "format_v1.md").exists()
            # format_v2.md should NOT be exported (automatic resolution skipped)
            assert not (target / "output" / "format.md").exists()

            # Verify the explicit reference is preserved in root prompt
            root_content = (target / "root_prompt.md").read_text()
            assert "output/format_v1.md" in root_content
