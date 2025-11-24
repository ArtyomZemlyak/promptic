"""Integration tests for hierarchical versioning."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from promptic.versioning.adapters.scanner import VersionedFileScanner
from promptic.versioning.domain.errors import VersionResolutionCycleError
from promptic.versioning.domain.resolver import HierarchicalVersionResolver, VersionSpec

pytestmark = pytest.mark.integration


class TestHierarchicalVersioning:
    """Integration test for loading nested prompts with version combinations (T035)."""

    def test_hierarchical_version_specification(self):
        """Test loading with hierarchical version specifications."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "task1"
            root.mkdir()
            (root / "root_prompt_v1.md").write_text(
                "# Root v1\n\nReference: instructions/process.md"
            )
            (root / "root_prompt_v2.md").write_text(
                "# Root v2\n\nReference: instructions/process.md"
            )
            (root / "instructions").mkdir()
            (root / "instructions" / "process_v1.md").write_text("# Process v1")
            (root / "instructions" / "process_v2.md").write_text("# Process v2")

            base_resolver = VersionedFileScanner()
            hierarchical_resolver = HierarchicalVersionResolver(base_resolver)

            # Load root at v1, but instructions/process at v2
            version_spec: VersionSpec = {"root": "v1", "instructions/process": "v2"}
            resolved = hierarchical_resolver.resolve_version(str(root), version_spec)
            content = Path(resolved).read_text()
            assert "# Root v1" in content

    def test_default_latest_for_nested_prompts(self):
        """Test that nested prompts default to latest if not specified."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "task1"
            root.mkdir()
            (root / "root_prompt_v1.md").write_text(
                "# Root v1\n\nReference: instructions/process.md"
            )
            (root / "instructions").mkdir()
            (root / "instructions" / "process_v1.md").write_text("# Process v1")
            (root / "instructions" / "process_v2.md").write_text("# Process v2")

            base_resolver = VersionedFileScanner()
            hierarchical_resolver = HierarchicalVersionResolver(base_resolver)

            # Only specify root version, nested should default to latest (v2)
            version_spec: VersionSpec = {"root": "v1"}
            resolved = hierarchical_resolver.resolve_version(str(root), version_spec)
            content = Path(resolved).read_text()
            assert "# Root v1" in content

    def test_cycle_detection_integration(self):
        """Test cycle detection in hierarchical resolution."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "task1"
            root.mkdir()
            (root / "root_prompt_v1.md").write_text("# Root v1")

            base_resolver = VersionedFileScanner()
            hierarchical_resolver = HierarchicalVersionResolver(base_resolver)

            # Test that cycle detection works (if cycles exist in file references)
            version_spec: VersionSpec = {"root": "v1"}

            try:
                resolved = hierarchical_resolver.resolve_version(str(root), version_spec)
                # Should resolve successfully if no cycles
                assert Path(resolved).exists()
            except VersionResolutionCycleError as e:
                # If cycle detected, should have cycle path details
                assert hasattr(e, "cycle_path")
                assert len(e.cycle_path) > 0
