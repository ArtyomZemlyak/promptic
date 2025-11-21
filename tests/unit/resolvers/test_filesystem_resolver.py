"""Unit tests for filesystem reference resolver."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from promptic.context.nodes.errors import NodeReferenceNotFoundError, PathResolutionError
from promptic.resolvers.filesystem import FilesystemReferenceResolver


def test_path_resolution_relative():
    """Test relative path resolution."""
    # This test will fail until FilesystemReferenceResolver is implemented
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        resolver = FilesystemReferenceResolver(root=root)

        # Create a test file
        test_file = root / "test.md"
        test_file.write_text("# Test\n\nContent")

        # Resolve relative path
        base_path = root
        resolved = resolver.resolve("test.md", base_path)

        # Should return ContextNode
        assert resolved is not None
        # TODO: Implement FilesystemReferenceResolver and update this test
        pass


def test_path_resolution_absolute():
    """Test absolute path resolution."""
    # This test will fail until FilesystemReferenceResolver is implemented
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        resolver = FilesystemReferenceResolver(root=root)

        # Create a test file
        test_file = root / "test.md"
        test_file.write_text("# Test\n\nContent")

        # Resolve absolute path
        base_path = root
        resolved = resolver.resolve(str(test_file.absolute()), base_path)

        # Should return ContextNode
        assert resolved is not None
        # TODO: Implement FilesystemReferenceResolver and update this test
        pass


def test_path_resolution_missing_file():
    """Test that NodeReferenceNotFoundError is raised for missing files."""
    # This test will fail until FilesystemReferenceResolver is implemented
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        resolver = FilesystemReferenceResolver(root=root)

        # Try to resolve non-existent file
        base_path = root
        with pytest.raises(NodeReferenceNotFoundError):
            resolver.resolve("nonexistent.md", base_path)

        # TODO: Implement FilesystemReferenceResolver and update this test
        pass


def test_path_validation():
    """Test path validation."""
    # This test will fail until FilesystemReferenceResolver is implemented
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        resolver = FilesystemReferenceResolver(root=root)

        # Create a test file
        test_file = root / "test.md"
        test_file.write_text("# Test\n\nContent")

        # Validate existing path
        base_path = root
        assert resolver.validate("test.md", base_path) is True

        # Validate non-existent path
        assert resolver.validate("nonexistent.md", base_path) is False

        # TODO: Implement FilesystemReferenceResolver and update this test
        pass
