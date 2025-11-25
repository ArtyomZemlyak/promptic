"""Contract definition for ReferenceInliner service.

# AICODE-NOTE: This file defines the contract for the ReferenceInliner service
# that orchestrates reference resolution strategies.

This is a SPECIFICATION file, not implementation code.
See data-model.md for full class documentation.
"""

from typing import Any, Protocol


class ContextNodeProtocol(Protocol):
    """Protocol matching ContextNode interface."""

    @property
    def id(self) -> str: ...

    @property
    def content(self) -> dict[str, Any]: ...

    @property
    def format(self) -> str: ...


class NodeNetworkProtocol(Protocol):
    """Protocol matching NodeNetwork interface."""

    @property
    def root(self) -> ContextNodeProtocol: ...

    @property
    def nodes(self) -> dict[str, ContextNodeProtocol]: ...


class ReferenceInlinerContract:
    """Contract for ReferenceInliner service.

    All implementations MUST satisfy these requirements:

    1. BACKWARD COMPATIBILITY: Output must be identical to current render_node_network
    2. STRATEGY COMPOSITION: Must apply all registered strategies
    3. RECURSIVE PROCESSING: Must process nested references
    4. CYCLE HANDLING: Must handle circular references gracefully (use network's cycle detection)
    5. FORMAT PRESERVATION: Must respect target_format parameter

    Contract Tests:
        See tests/contract/test_rendering_contracts.py

    Regression Tests:
        See tests/integration/test_render_api.py
    """

    def inline_references(
        self,
        node: ContextNodeProtocol,
        network: NodeNetworkProtocol,
        target_format: str,
    ) -> str | dict[str, Any]:
        """Inline all references in node content.

        Requirements:
            - Must produce identical output to current render_node_network
            - Must recursively process all nested references
            - Must apply all registered strategies in order
            - Must handle both text (raw_content) and structured content

        Args:
            node: Node to process
            network: Network containing all nodes for lookup
            target_format: Target output format (yaml, json, markdown, jinja2)

        Returns:
            Content with references inlined:
            - str for text formats (markdown, jinja2 with raw_content)
            - dict for structured formats (yaml, json without raw_content)

        Raises:
            No exceptions - gracefully handles all edge cases
        """
        raise NotImplementedError("Contract specification only")


# Regression test specification
REGRESSION_TEST_SPEC = """
# These tests MUST pass before and after refactoring

def test_markdown_with_markdown_link_reference():
    '''Test [text](file.md) reference inlining.'''
    # Create network with root.md referencing child.md
    # Assert: child content is inlined where link was

def test_markdown_with_jinja2_reference():
    '''Test {# ref: file.md #} reference inlining.'''
    # Create network with root.jinja referencing data.yaml
    # Assert: data content is inlined where ref was

def test_yaml_with_ref_reference():
    '''Test {"$ref": "file.yaml"} reference inlining.'''
    # Create network with root.yaml containing $ref
    # Assert: referenced content replaces $ref object

def test_nested_references():
    '''Test multi-level reference resolution.'''
    # root.md -> child.md -> grandchild.md
    # Assert: all levels are inlined

def test_mixed_format_references():
    '''Test markdown referencing yaml.'''
    # root.md -> data.yaml (via link)
    # Assert: yaml content wrapped in code block

def test_circular_reference_handling():
    '''Test that circular refs are handled.'''
    # a.md -> b.md -> a.md
    # Assert: no infinite loop, graceful handling

def test_missing_reference_preserved():
    '''Test missing refs keep original content.'''
    # root.md -> nonexistent.md
    # Assert: original [text](nonexistent.md) preserved

def test_external_links_unchanged():
    '''Test http:// links are not processed.'''
    # root.md with [link](https://example.com)
    # Assert: link unchanged in output
"""

# Output comparison specification
OUTPUT_COMPARISON_SPEC = """
# For each test case, compare:
# 1. Current render_node_network output (baseline)
# 2. New ReferenceInliner output (refactored)
# 3. Assert byte-for-byte equality

import hashlib

def compare_outputs(baseline: str, refactored: str) -> bool:
    '''Compare outputs for regression testing.'''
    baseline_hash = hashlib.sha256(baseline.encode()).hexdigest()
    refactored_hash = hashlib.sha256(refactored.encode()).hexdigest()
    return baseline_hash == refactored_hash
"""
