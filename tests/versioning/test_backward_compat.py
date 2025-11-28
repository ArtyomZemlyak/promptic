"""Backward compatibility tests for versioning system.

Tests for:
- Backward compatibility (T017)

Ensures existing code without versioning_config parameter works identically.
"""

from __future__ import annotations

from pathlib import Path

import pytest


class TestBackwardCompatibility:
    """Backward compatibility tests (T017)."""

    def test_scanner_without_config_uses_defaults(self, tmp_path: Path) -> None:
        """VersionedFileScanner without config should use default underscore delimiter."""
        from promptic.versioning.adapters.scanner import VersionedFileScanner

        # Create test files with underscore delimiter (default)
        (tmp_path / "prompt_v1.md").write_text("Version 1")
        (tmp_path / "prompt_v2.md").write_text("Version 2")

        # Scanner without config parameter
        scanner = VersionedFileScanner()

        resolved_path = scanner.resolve_version(str(tmp_path), "latest")

        assert "prompt_v2.md" in resolved_path

    def test_scanner_none_config_uses_defaults(self, tmp_path: Path) -> None:
        """VersionedFileScanner with config=None should use default underscore delimiter."""
        from promptic.versioning.adapters.scanner import VersionedFileScanner

        (tmp_path / "prompt_v1.md").write_text("Version 1")
        (tmp_path / "prompt_v2.md").write_text("Version 2")

        scanner = VersionedFileScanner(config=None)

        resolved_path = scanner.resolve_version(str(tmp_path), "latest")

        assert "prompt_v2.md" in resolved_path

    def test_existing_api_load_prompt_without_config(self, tmp_path: Path) -> None:
        """load_prompt without versioning_config should work as before."""
        from promptic.sdk.api import load_prompt

        (tmp_path / "prompt_v1.md").write_text("Content v1")
        (tmp_path / "prompt_v2.md").write_text("Content v2")

        # Original API call without versioning_config
        content = load_prompt(str(tmp_path), version="latest")

        assert content == "Content v2"

    def test_existing_api_load_prompt_specific_version(self, tmp_path: Path) -> None:
        """load_prompt with specific version should work as before."""
        from promptic.sdk.api import load_prompt

        (tmp_path / "task_v1.md").write_text("Task v1")
        (tmp_path / "task_v2.md").write_text("Task v2")
        (tmp_path / "task_v3.md").write_text("Task v3")

        content = load_prompt(str(tmp_path), version="v2")

        assert content == "Task v2"

    def test_version_pattern_compatibility(self, tmp_path: Path) -> None:
        """Default pattern should match same files as original implementation."""
        from promptic.versioning.adapters.scanner import VersionedFileScanner

        # Test various version formats that original implementation supported
        (tmp_path / "prompt_v1.md").write_text("v1")
        (tmp_path / "prompt_v1.1.md").write_text("v1.1")
        (tmp_path / "prompt_v1.1.1.md").write_text("v1.1.1")
        (tmp_path / "prompt_v10.md").write_text("v10")
        (tmp_path / "prompt_v2.0.md").write_text("v2.0")

        scanner = VersionedFileScanner()
        files = scanner.scan_directory(str(tmp_path))

        versioned = [f for f in files if f.is_versioned]

        # All files should be detected as versioned
        assert len(versioned) == 5

        # Latest should be v10 (highest major version)
        resolved = scanner.resolve_version(str(tmp_path), "latest")
        assert "prompt_v10.md" in resolved

    def test_unversioned_fallback_compatibility(self, tmp_path: Path) -> None:
        """Unversioned file fallback should work as before."""
        from promptic.versioning.adapters.scanner import VersionedFileScanner

        # Only unversioned files
        (tmp_path / "prompt.md").write_text("Unversioned content")

        scanner = VersionedFileScanner()
        resolved = scanner.resolve_version(str(tmp_path), "latest")

        assert "prompt.md" in resolved
        assert Path(resolved).read_text() == "Unversioned content"

    def test_hierarchical_resolver_compatibility(self, tmp_path: Path) -> None:
        """HierarchicalVersionResolver should work without config."""
        from promptic.versioning import HierarchicalVersionResolver, VersionedFileScanner

        # Create hierarchical structure
        root = tmp_path / "root"
        root.mkdir()
        (root / "main_v1.md").write_text("Main v1")
        (root / "main_v2.md").write_text("Main v2")

        sub = root / "sub"
        sub.mkdir()
        (sub / "task_v1.md").write_text("Task v1")
        (sub / "task_v3.md").write_text("Task v3")

        base_resolver = VersionedFileScanner()
        resolver = HierarchicalVersionResolver(base_resolver)

        # Should work with "latest" as before
        resolved = resolver.resolve_version(str(root), "latest")
        assert "main_v2.md" in resolved
