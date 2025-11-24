"""Integration tests for loading prompts with version specifications."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from promptic.versioning.adapters.scanner import VersionedFileScanner
from promptic.versioning.domain.errors import VersionNotFoundError

pytestmark = pytest.mark.integration


class TestVersionLoading:
    """Integration test for loading prompts with different version specifications (T018)."""

    def test_load_latest_version(self):
        """Test loading latest version (default behavior)."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "task1"
            root.mkdir()
            (root / "root_prompt_v1.md").write_text("# v1")
            (root / "root_prompt_v2.md").write_text("# v2")
            (root / "root_prompt_v3.md").write_text("# v3")

            scanner = VersionedFileScanner()
            resolved = scanner.resolve_version(str(root), "latest")
            content = Path(resolved).read_text()
            assert content == "# v3"

    def test_load_specific_version(self):
        """Test loading specific version."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "task1"
            root.mkdir()
            (root / "root_prompt_v1.md").write_text("# v1")
            (root / "root_prompt_v2.md").write_text("# v2")
            (root / "root_prompt_v3.md").write_text("# v3")

            scanner = VersionedFileScanner()
            resolved = scanner.resolve_version(str(root), "v2")
            content = Path(resolved).read_text()
            assert content == "# v2"

    def test_load_unversioned_fallback(self):
        """Test loading unversioned file when no versioned files exist."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "task1"
            root.mkdir()
            (root / "root_prompt.md").write_text("# unversioned")

            scanner = VersionedFileScanner()
            resolved = scanner.resolve_version(str(root), "latest")
            content = Path(resolved).read_text()
            assert content == "# unversioned"

    def test_load_version_not_found_error(self):
        """Test loading non-existent version raises error with available versions."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "task1"
            root.mkdir()
            (root / "root_prompt_v1.md").write_text("# v1")
            (root / "root_prompt_v2.md").write_text("# v2")

            scanner = VersionedFileScanner()
            with pytest.raises(VersionNotFoundError) as exc_info:
                scanner.resolve_version(str(root), "v5")
            error = exc_info.value
            assert error.version_spec == "v5"
            assert len(error.available_versions) > 0

    def test_load_multiple_version_formats(self):
        """Test loading with various version formats."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "task1"
            root.mkdir()
            (root / "root_prompt_v1.0.0.md").write_text("# v1.0.0")
            (root / "root_prompt_v1.1.0.md").write_text("# v1.1.0")
            (root / "root_prompt_v2.0.0.md").write_text("# v2.0.0")

            scanner = VersionedFileScanner()
            # Test various formats
            test_cases = [
                ("v1", "v1.0.0"),
                ("v1.1", "v1.1.0"),
                ("v1.1.0", "v1.1.0"),
                ("v2.0.0", "v2.0.0"),
                ("latest", "v2.0.0"),
            ]
            for version_spec, expected_file in test_cases:
                resolved = scanner.resolve_version(str(root), version_spec)
                expected_path = root / f"root_prompt_{expected_file}.md"
                assert resolved == str(expected_path)
