"""Unit tests for version resolution."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from promptic.versioning.adapters.scanner import VersionedFileScanner
from promptic.versioning.domain.errors import VersionNotFoundError

pytestmark = pytest.mark.unit


class TestVersionResolution:
    """Test version resolution logic (T017)."""

    def test_resolve_latest_version(self):
        """Test resolving latest version from directory."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            # Create versioned files
            (root / "root_prompt_v1.md").write_text("# v1")
            (root / "root_prompt_v2.md").write_text("# v2")
            (root / "root_prompt_v3.md").write_text("# v3")

            scanner = VersionedFileScanner()
            resolved = scanner.resolve_version(str(root), "latest")
            assert resolved == str(root / "root_prompt_v3.md")

    def test_resolve_specific_version(self):
        """Test resolving specific version."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "root_prompt_v1.md").write_text("# v1")
            (root / "root_prompt_v2.md").write_text("# v2")

            scanner = VersionedFileScanner()
            resolved = scanner.resolve_version(str(root), "v1")
            assert resolved == str(root / "root_prompt_v1.md")

    def test_resolve_version_not_found(self):
        """Test resolving non-existent version raises error."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "root_prompt_v1.md").write_text("# v1")

            scanner = VersionedFileScanner()
            with pytest.raises(VersionNotFoundError) as exc_info:
                scanner.resolve_version(str(root), "v5")
            assert exc_info.value.version_spec == "v5"

    def test_resolve_unversioned_fallback(self):
        """Test resolving unversioned file when no versioned files exist."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "root_prompt.md").write_text("# unversioned")

            scanner = VersionedFileScanner()
            resolved = scanner.resolve_version(str(root), "latest")
            assert resolved == str(root / "root_prompt.md")

    def test_resolve_versioned_over_unversioned(self):
        """Test versioned files take precedence over unversioned."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "root_prompt.md").write_text("# unversioned")
            (root / "root_prompt_v1.md").write_text("# v1")

            scanner = VersionedFileScanner()
            resolved = scanner.resolve_version(str(root), "latest")
            # Should prefer versioned file
            assert resolved == str(root / "root_prompt_v1.md")

    def test_resolve_simplified_version_forms(self):
        """Test resolving simplified version forms (v1, v1.1)."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "root_prompt_v1.0.0.md").write_text("# v1.0.0")
            (root / "root_prompt_v1.1.0.md").write_text("# v1.1.0")

            scanner = VersionedFileScanner()
            # v1 should resolve to v1.0.0
            resolved = scanner.resolve_version(str(root), "v1")
            assert resolved == str(root / "root_prompt_v1.0.0.md")

            # v1.1 should resolve to v1.1.0
            resolved = scanner.resolve_version(str(root), "v1.1")
            assert resolved == str(root / "root_prompt_v1.1.0.md")
