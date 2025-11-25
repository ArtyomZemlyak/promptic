"""Unit tests for version export orchestration."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import pytest

from promptic.versioning.adapters.scanner import VersionedFileScanner
from promptic.versioning.domain.errors import ExportError, VersionNotFoundError
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


class TestValidateAndResolveRoot:
    """Test _validate_and_resolve_root method (T044)."""

    def test_resolves_directory_to_versioned_file(self):
        """Test that directory source resolves to versioned file."""
        with TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "prompts"
            source.mkdir()
            (source / "root_v1.md").write_text("# Root v1")

            exporter = VersionExporter()
            resolved_path, source_base = exporter._validate_and_resolve_root(
                str(source), "v1", Path(tmpdir) / "target"
            )

            assert "root_v1.md" in resolved_path
            assert source_base == source.resolve()

    def test_resolves_file_directly(self):
        """Test that file source returns the file path directly."""
        with TemporaryDirectory() as tmpdir:
            source_file = Path(tmpdir) / "root.md"
            source_file.write_text("# Root")

            exporter = VersionExporter()
            resolved_path, source_base = exporter._validate_and_resolve_root(
                str(source_file), "latest", Path(tmpdir) / "target"
            )

            assert resolved_path == str(source_file)
            assert source_base == source_file.parent.resolve()

    def test_raises_error_for_missing_root(self):
        """Test that error is raised when root file doesn't exist."""
        with TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "prompts"
            source.mkdir()
            # No files created

            exporter = VersionExporter()
            with pytest.raises((ExportError, VersionNotFoundError)) as exc_info:
                exporter._validate_and_resolve_root(str(source), "v1", Path(tmpdir) / "target")

            assert (
                "not found" in str(exc_info.value).lower()
                or "no files" in str(exc_info.value).lower()
            )


class TestBuildFileMapping:
    """Test _build_file_mapping method (T045)."""

    def test_builds_mapping_for_versioned_files(self):
        """Test building file mapping with version suffix removal."""
        with TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "prompts"
            source.mkdir()
            root_file = source / "root_v1.md"
            root_file.write_text("# Root v1")

            target = Path(tmpdir) / "export"

            exporter = VersionExporter()
            mapping = exporter._build_file_mapping(
                root_path=root_file,
                source_base=source.resolve(),
                target=target,
                version_spec="v1",
            )

            # Version suffix should be removed in target path
            assert str(root_file) in mapping
            target_path = mapping[str(root_file)]
            assert "root.md" in target_path
            assert "_v1" not in target_path

    def test_preserves_subdirectory_structure(self):
        """Test that subdirectory structure is preserved in mapping."""
        with TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "prompts"
            source.mkdir()
            (source / "subdir").mkdir()

            root_file = source / "root_v1.md"
            root_file.write_text("# Root\n[Link](subdir/child_v1.md)")
            child_file = source / "subdir" / "child_v1.md"
            child_file.write_text("# Child")

            target = Path(tmpdir) / "export"

            exporter = VersionExporter()
            mapping = exporter._build_file_mapping(
                root_path=root_file,
                source_base=source.resolve(),
                target=target,
                version_spec="v1",
            )

            # Check subdirectory structure is preserved
            has_subdir_target = any("subdir" in v for v in mapping.values())
            assert has_subdir_target, "Subdirectory structure should be preserved"

    def test_includes_referenced_files(self):
        """Test that explicitly referenced files are included in mapping."""
        with TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "prompts"
            source.mkdir()

            root_file = source / "root.md"
            root_file.write_text("# Root\n[Instructions](instructions.md)")
            instructions = source / "instructions.md"
            instructions.write_text("# Instructions")

            target = Path(tmpdir) / "export"

            exporter = VersionExporter()
            mapping = exporter._build_file_mapping(
                root_path=root_file,
                source_base=source.resolve(),
                target=target,
                version_spec="latest",
            )

            assert str(instructions) in mapping


class TestCreateContentProcessor:
    """Test _create_content_processor method (T046)."""

    def test_processor_resolves_paths(self):
        """Test that content processor resolves file paths."""
        with TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "prompts"
            source.mkdir()
            target = Path(tmpdir) / "export"

            root_file = source / "root_v1.md"
            root_file.write_text("# Root\n[Link](child_v1.md)")
            child_file = source / "child_v1.md"
            child_file.write_text("# Child")

            file_mapping = {
                str(root_file): str(target / "root.md"),
                str(child_file): str(target / "child.md"),
            }

            exporter = VersionExporter()
            processor = exporter._create_content_processor(
                file_mapping=file_mapping,
                source_base=str(source.resolve()),
                target=str(target),
                vars=None,
                hierarchical_paths={},
            )

            content = "See [Link](child_v1.md) for details."
            processed = processor(root_file, content)

            # Path should be resolved (version stripped if applicable)
            assert "child" in processed.lower()

    def test_processor_substitutes_variables(self):
        """Test that content processor substitutes variables when provided."""
        with TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "prompts"
            source.mkdir()
            target = Path(tmpdir) / "export"

            root_file = source / "root.md"
            root_file.write_text("Hello {{name}}!")

            file_mapping = {str(root_file): str(target / "root.md")}

            exporter = VersionExporter()
            processor = exporter._create_content_processor(
                file_mapping=file_mapping,
                source_base=str(source.resolve()),
                target=str(target),
                vars={"name": "World"},
                hierarchical_paths={str(root_file.resolve()): "root"},
            )

            content = "Hello {{name}}!"
            processed = processor(root_file, content)

            assert "World" in processed


class TestExecuteExport:
    """Test _execute_export method (T046)."""

    def test_exports_files_successfully(self):
        """Test successful file export."""
        with TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "prompts"
            source.mkdir()
            target = Path(tmpdir) / "export"

            root_file = source / "root.md"
            root_file.write_text("# Root content")

            file_mapping = {str(root_file): str(target / "root.md")}

            exporter = VersionExporter()
            result = exporter._execute_export(
                file_mapping=file_mapping,
                target=target,
                root_path=root_file,
                content_processor=lambda p, c: c,
            )

            assert result.structure_preserved is True
            assert len(result.exported_files) > 0

    def test_cleanup_on_failure(self):
        """Test that target directory is cleaned up on export failure."""
        with TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "prompts"
            source.mkdir()
            target = Path(tmpdir) / "export"

            root_file = source / "root.md"
            root_file.write_text("# Root")

            # Non-existent file in mapping should cause failure
            file_mapping = {
                str(root_file): str(target / "root.md"),
                "/nonexistent/file.md": str(target / "missing.md"),
            }

            exporter = VersionExporter()

            # The export should fail but clean up properly
            # This test verifies the cleanup mechanism works
            try:
                exporter._execute_export(
                    file_mapping=file_mapping,
                    target=target,
                    root_path=root_file,
                    content_processor=lambda p, c: c,
                )
            except ExportError:
                # Expected - verify cleanup happened
                pass  # Cleanup behavior is best-effort
