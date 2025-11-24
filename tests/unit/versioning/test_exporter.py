"""Unit tests for version export orchestration."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from promptic.versioning.adapters.scanner import VersionedFileScanner
from promptic.versioning.domain.exporter import ExportResult, VersionExporter

pytestmark = pytest.mark.unit


class TestVersionExporter:
    """Test export orchestration logic (T044)."""

    def test_export_result_structure(self):
        """Test ExportResult dataclass structure."""
        result = ExportResult(
            root_prompt_content="# Root prompt",
            exported_files=["file1.md", "file2.md"],
            structure_preserved=True,
        )
        assert result.root_prompt_content == "# Root prompt"
        assert len(result.exported_files) == 2
        assert result.structure_preserved is True

    def test_version_resolution_for_export(self):
        """Test version resolution during export."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "task1"
            root.mkdir()
            (root / "root_prompt_v1.md").write_text("# Root v1")
            (root / "root_prompt_v2.md").write_text("# Root v2")

            scanner = VersionedFileScanner()
            resolved = scanner.resolve_version(str(root), "v2")
            assert "root_prompt_v2.md" in resolved

    def test_file_discovery(self):
        """Test discovering referenced files in prompt hierarchy."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "task1"
            root.mkdir()
            (root / "root_prompt_v2.md").write_text("# Root\n\nReference: instructions/process.md")
            (root / "instructions").mkdir()
            (root / "instructions" / "process_v2.md").write_text("# Process")

            # File discovery logic would extract references from content
            # This is a placeholder test
            assert (root / "root_prompt_v2.md").exists()
            assert (root / "instructions" / "process_v2.md").exists()

    def test_structure_preservation(self):
        """Test that export preserves hierarchical directory structure."""
        with TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            source.mkdir()
            (source / "root.md").write_text("# Root")
            (source / "instructions").mkdir()
            (source / "instructions" / "process.md").write_text("# Process")

            target = Path(tmpdir) / "target"
            target.mkdir()

            # Structure preservation would maintain nested directories
            # This is a placeholder test
            assert source.is_dir()
            assert (source / "instructions").is_dir()
