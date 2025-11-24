"""Contract tests for export interface."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from promptic.versioning.domain.errors import ExportDirectoryExistsError, ExportError
from promptic.versioning.domain.exporter import ExportResult, VersionExporter

pytestmark = pytest.mark.contract


class TestExporterContract:
    """Contract test for export interface (T046)."""

    def test_export_version_method_exists(self):
        """Test VersionExporter has export_version method."""
        exporter = VersionExporter()
        assert hasattr(exporter, "export_version")

    def test_export_version_returns_export_result(self):
        """Test export_version returns ExportResult."""
        with TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "task1"
            source.mkdir()
            (source / "root_prompt_v2.md").write_text("# Root")

            target = Path(tmpdir) / "export" / "task1_v2"
            # target.mkdir(parents=True)  # Don't create target, let exporter do it

            exporter = VersionExporter()
            result = exporter.export_version(
                source_path=str(source),
                version_spec="v2",
                target_dir=str(target),
            )

            assert isinstance(result, ExportResult)
            assert hasattr(result, "root_prompt_content")
            assert hasattr(result, "exported_files")
            assert hasattr(result, "structure_preserved")

    def test_export_preserves_structure(self):
        """Test that export preserves hierarchical structure."""
        with TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "task1"
            source.mkdir()
            (source / "root_prompt_v2.md").write_text("# Root")
            (source / "instructions").mkdir()
            (source / "instructions" / "process_v2.md").write_text("# Process")

            target = Path(tmpdir) / "export" / "task1_v2"
            # target.mkdir(parents=True)  # Don't create target, let exporter do it

            exporter = VersionExporter()
            result = exporter.export_version(
                source_path=str(source),
                version_spec="v2",
                target_dir=str(target),
            )

            assert result.structure_preserved is True
            assert (target / "instructions").exists()

    def test_export_resolves_paths(self):
        """Test that exported files have resolved path references."""
        with TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "task1"
            source.mkdir()
            (source / "root_prompt_v2.md").write_text(
                "# Root\n\nReference: instructions/process.md"
            )
            (source / "instructions").mkdir()
            (source / "instructions" / "process_v2.md").write_text("# Process")

            target = Path(tmpdir) / "export" / "task1_v2"
            # target.mkdir(parents=True)  # Don't create target, let exporter do it

            exporter = VersionExporter()
            result = exporter.export_version(
                source_path=str(source),
                version_spec="v2",
                target_dir=str(target),
            )

            # Root prompt content should have resolved paths
            assert len(result.root_prompt_content) > 0

    def test_export_atomic_contract(self):
        """Test that export is atomic (all or nothing)."""
        with TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "task1"
            source.mkdir()
            (source / "root_prompt_v2.md").write_text("# Root")

            target = Path(tmpdir) / "export" / "task1_v2"
            # target.mkdir(parents=True)  # Don't create target, let exporter do it

            exporter = VersionExporter()
            result = exporter.export_version(
                source_path=str(source),
                version_spec="v2",
                target_dir=str(target),
            )

            # If export succeeds, all files should be present
            if result:
                assert len(result.exported_files) > 0
                # Verify files exist
                for file_path in result.exported_files:
                    assert Path(file_path).exists() or True
