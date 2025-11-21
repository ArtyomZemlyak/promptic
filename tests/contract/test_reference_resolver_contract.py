"""Contract test for NodeReferenceResolver interface."""

from pathlib import Path

import pytest

from promptic.resolvers.base import NodeReferenceResolver


def test_reference_resolver_interface_contract():
    """Verify NodeReferenceResolver interface contract.

    This test ensures all reference resolver implementations follow the interface
    contract defined in NodeReferenceResolver base class.
    """
    # This test will fail until resolvers are implemented
    # Once resolvers exist, we'll import and test them here
    from promptic.resolvers.filesystem import FilesystemReferenceResolver

    resolver = FilesystemReferenceResolver(root=Path("."))

    # Verify resolver implements NodeReferenceResolver interface
    assert issubclass(type(resolver), NodeReferenceResolver)
    assert isinstance(resolver, NodeReferenceResolver)

    # Verify all required methods exist
    assert hasattr(resolver, "resolve")
    assert hasattr(resolver, "validate")

    # Verify methods are callable
    assert callable(resolver.resolve)
    assert callable(resolver.validate)

    # Test method signatures with sample data
    test_path = "test.md"
    test_base_path = Path(".")

    # validate() should return bool
    result = resolver.validate(test_path, test_base_path)
    assert isinstance(result, bool)

    # resolve() should return ContextNode (may raise exceptions)
    # We'll test this with actual file paths in integration tests
    # For contract test, we just verify the method exists and is callable
    assert callable(resolver.resolve)
