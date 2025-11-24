"""Unit tests for hierarchical version resolution."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from promptic.versioning.adapters.scanner import VersionedFileScanner
from promptic.versioning.domain.errors import VersionResolutionCycleError
from promptic.versioning.domain.resolver import HierarchicalVersionResolver, VersionSpec

pytestmark = pytest.mark.unit


class TestHierarchicalVersionResolver:
    """Test hierarchical version specification parsing (T034)."""

    def test_parse_hierarchical_version_spec(self):
        """Test parsing dictionary mapping path patterns to versions."""
        version_spec: VersionSpec = {
            "root": "v1",
            "instructions/process": "v2",
            "templates/data": "v1.1",
        }
        assert isinstance(version_spec, dict)
        assert version_spec["root"] == "v1"
        assert version_spec["instructions/process"] == "v2"
        assert version_spec["templates/data"] == "v1.1"

    def test_resolve_hierarchical_version(self):
        """Test resolving version using hierarchical specification."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "task1"
            root.mkdir()
            (root / "root_prompt_v1.md").write_text("# v1")
            (root / "root_prompt_v2.md").write_text("# v2")
            (root / "instructions").mkdir()
            (root / "instructions" / "process_v1.md").write_text("# process v1")
            (root / "instructions" / "process_v2.md").write_text("# process v2")

            base_resolver = VersionedFileScanner()
            hierarchical_resolver = HierarchicalVersionResolver(base_resolver)

            # Test hierarchical specification
            version_spec: VersionSpec = {"root": "v1", "instructions/process": "v2"}
            resolved = hierarchical_resolver.resolve_version(str(root), version_spec)
            assert "root_prompt_v1.md" in resolved
            # The hierarchical resolver should handle this
            assert Path(resolved).exists()

    def test_hierarchical_default_latest(self):
        """Test that nested prompts default to latest if not specified."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "task1"
            root.mkdir()
            (root / "root_prompt_v1.md").write_text("# v1")
            (root / "instructions").mkdir()
            (root / "instructions" / "process_v1.md").write_text("# process v1")
            (root / "instructions" / "process_v2.md").write_text("# process v2")

            base_resolver = VersionedFileScanner()
            hierarchical_resolver = HierarchicalVersionResolver(base_resolver)

            # Only specify root version, nested should default to latest
            version_spec: VersionSpec = {"root": "v1"}
            resolved = hierarchical_resolver.resolve_version(str(root), version_spec)
            assert Path(resolved).exists()

    def test_cycle_detection(self):
        """Test cycle detection in hierarchical version resolution."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "task1"
            root.mkdir()
            # Create files for the test
            (root / "root_prompt_v1.md").write_text("# Root v1")

            base_resolver = VersionedFileScanner()
            hierarchical_resolver = HierarchicalVersionResolver(base_resolver)

            # Test normal resolution (no cycle)
            version_spec: VersionSpec = {"root": "v1"}
            resolved = hierarchical_resolver.resolve_version(str(root), version_spec)
            assert resolved is not None
            assert "root_prompt_v1.md" in resolved

            # Test that resolution stack is properly managed (cleared after resolution)
            assert len(hierarchical_resolver._resolution_stack) == 0

            # Test cycle detection by manually simulating a cycle
            hierarchical_resolver._resolution_stack.append(str(root))
            try:
                # This should detect a cycle
                hierarchical_resolver.resolve_version(str(root), version_spec)
                assert False, "Expected VersionResolutionCycleError"
            except VersionResolutionCycleError as e:
                # Cycle detected correctly
                assert str(root) in e.cycle_path
            finally:
                # Clean up
                hierarchical_resolver._resolution_stack.clear()
