"""Contract tests for VersionResolver interface."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from promptic.versioning.adapters.scanner import VersionedFileScanner
from promptic.versioning.domain.errors import VersionNotFoundError
from promptic.versioning.domain.resolver import VersionResolver

pytestmark = pytest.mark.contract


class TestVersionResolverContract:
    """Contract test for VersionResolver interface (T019)."""

    def test_resolve_version_method_exists(self):
        """Test VersionResolver interface has resolve_version method."""
        # Verify interface exists
        assert hasattr(VersionResolver, "resolve_version")

    def test_scanner_implements_interface(self):
        """Test VersionedFileScanner implements VersionResolver interface."""
        scanner = VersionedFileScanner()
        assert isinstance(scanner, VersionResolver)

    def test_resolve_version_signature(self):
        """Test resolve_version method signature."""
        scanner = VersionedFileScanner()
        # Should accept path and version_spec
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "prompt_v1.md").write_text("# v1")
            resolved = scanner.resolve_version(str(root), "latest")
            assert isinstance(resolved, str)
            assert Path(resolved).exists()

    def test_resolve_version_raises_version_not_found(self):
        """Test resolve_version raises VersionNotFoundError for missing versions."""
        scanner = VersionedFileScanner()
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "prompt_v1.md").write_text("# v1")
            with pytest.raises(VersionNotFoundError):
                scanner.resolve_version(str(root), "v5")

    def test_resolve_version_returns_string_path(self):
        """Test resolve_version returns string path to resolved file."""
        scanner = VersionedFileScanner()
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "prompt_v1.md").write_text("# v1")
            resolved = scanner.resolve_version(str(root), "v1")
            assert isinstance(resolved, str)
            assert Path(resolved).exists()
            assert Path(resolved).is_file()

    def test_resolve_version_handles_latest(self):
        """Test resolve_version handles 'latest' version specification."""
        scanner = VersionedFileScanner()
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "prompt_v1.md").write_text("# v1")
            (root / "prompt_v2.md").write_text("# v2")
            resolved = scanner.resolve_version(str(root), "latest")
            assert resolved == str(root / "prompt_v2.md")

    def test_resolve_version_handles_specific_version(self):
        """Test resolve_version handles specific version strings."""
        scanner = VersionedFileScanner()
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "prompt_v1.md").write_text("# v1")
            (root / "prompt_v2.md").write_text("# v2")
            resolved = scanner.resolve_version(str(root), "v1")
            assert resolved == str(root / "prompt_v1.md")
