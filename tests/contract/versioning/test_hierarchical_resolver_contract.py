"""Contract tests for hierarchical version resolution."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from promptic.versioning.adapters.scanner import VersionedFileScanner
from promptic.versioning.domain.resolver import (
    HierarchicalVersionResolver,
    VersionResolver,
    VersionSpec,
)

pytestmark = pytest.mark.contract


class TestHierarchicalResolverContract:
    """Contract test for hierarchical version resolution (T036)."""

    def test_implements_version_resolver_interface(self):
        """Test HierarchicalVersionResolver implements VersionResolver interface."""
        base_resolver = VersionedFileScanner()
        hierarchical_resolver = HierarchicalVersionResolver(base_resolver)
        assert isinstance(hierarchical_resolver, VersionResolver)

    def test_resolve_version_with_hierarchical_spec(self):
        """Test resolve_version handles hierarchical version specifications."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "task1"
            root.mkdir()
            (root / "root_prompt_v1.md").write_text("# v1")

            base_resolver = VersionedFileScanner()
            hierarchical_resolver = HierarchicalVersionResolver(base_resolver)

            version_spec: VersionSpec = {"root": "v1"}
            resolved = hierarchical_resolver.resolve_version(str(root), version_spec)
            assert isinstance(resolved, str)
            assert Path(resolved).exists()

    def test_resolve_version_with_string_spec(self):
        """Test resolve_version handles string version specifications (delegates to base)."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "task1"
            root.mkdir()
            (root / "root_prompt_v1.md").write_text("# v1")

            base_resolver = VersionedFileScanner()
            hierarchical_resolver = HierarchicalVersionResolver(base_resolver)

            # String spec should delegate to base resolver
            resolved = hierarchical_resolver.resolve_version(str(root), "v1")
            assert isinstance(resolved, str)
            assert Path(resolved).exists()

    def test_hierarchical_resolution_recursive(self):
        """Test that hierarchical resolution applies recursively."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "task1"
            root.mkdir()
            (root / "root_prompt_v1.md").write_text("# Root v1")
            (root / "instructions").mkdir()
            (root / "instructions" / "process_v1.md").write_text("# Process v1")
            (root / "instructions" / "process_v2.md").write_text("# Process v2")

            base_resolver = VersionedFileScanner()
            hierarchical_resolver = HierarchicalVersionResolver(base_resolver)

            # Hierarchical spec with nested paths
            version_spec: VersionSpec = {
                "root": "v1",
                "instructions/process": "v2",
            }
            resolved = hierarchical_resolver.resolve_version(str(root), version_spec)
            assert Path(resolved).exists()
            content = Path(resolved).read_text()
            assert "# Root v1" in content
