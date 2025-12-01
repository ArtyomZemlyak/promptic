"""Service for inlining referenced content into nodes.

# AICODE-NOTE: This class consolidates all duplicate process_node_content
# implementations from the original render_node_network function (~750 lines).
# It orchestrates multiple strategies to handle different reference types:
# - Jinja2RefStrategy: {# ref: path #}
# - MarkdownLinkStrategy: [text](path)
# - StructuredRefStrategy: {"$ref": "path"}

The inliner uses strategy pattern for reference resolution, allowing new
reference types to be added without modifying existing code (OCP).
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Optional

import yaml

from promptic.rendering.strategies import (
    Jinja2RefStrategy,
    MarkdownLinkStrategy,
    ReferenceStrategy,
    StructuredRefStrategy,
)

if TYPE_CHECKING:
    from promptic.context.nodes.models import ContextNode, NodeNetwork


class ReferenceInliner:
    """Service for inlining referenced content into nodes.

    This class consolidates duplicate reference processing code into a single,
    testable, and maintainable implementation using the Strategy pattern.

    Usage:
        inliner = ReferenceInliner()
        content = inliner.inline_references(node, network, "markdown")

    The inliner:
    1. Detects the content type (text vs structured)
    2. Applies all registered strategies to resolve references
    3. Recursively processes nested references
    4. Returns processed content in the appropriate format
    """

    def __init__(self, strategies: list[ReferenceStrategy] | None = None):
        """Initialize with reference strategies.

        Args:
            strategies: List of strategies to use. Defaults to all built-in strategies.
        """
        self.strategies = strategies or self._default_strategies()

    def _default_strategies(self) -> list[ReferenceStrategy]:
        """Get default strategy instances.

        # AICODE-NOTE: Order matters! Jinja2 refs are processed first to handle
        # cases where jinja2 refs contain markdown links.
        """
        return [
            Jinja2RefStrategy(),
            MarkdownLinkStrategy(),
            StructuredRefStrategy(),
        ]

    def inline_references(
        self,
        node: ContextNode,
        network: NodeNetwork,
        target_format: str,
    ) -> str | dict[str, Any]:
        """Inline all references in node content.

        Args:
            node: Node to process
            network: Network containing all nodes for lookup
            target_format: Target output format (yaml, json, markdown, jinja2)

        Returns:
            Content with references inlined:
            - str for text formats (markdown, jinja2 with raw_content)
            - dict for structured formats (yaml, json without raw_content)
        """
        content = node.content.copy()

        # Create lookup function that finds nodes by path
        def node_lookup(path: str) -> Optional[ContextNode]:
            resolved = self._lookup_resolved_reference(node, path, network)
            if resolved is not None:
                return resolved
            return self._find_node(path, network)

        # Create content renderer that recursively processes child nodes
        def content_renderer(child_node: ContextNode, fmt: str) -> Any:
            return self._render_child(child_node, network, fmt, target_format)

        # Process based on content type
        if "raw_content" in content and isinstance(content["raw_content"], str):
            # Text content (markdown, jinja2)
            processed = content["raw_content"]
            for strategy in self.strategies:
                if strategy.can_process(processed):
                    processed = strategy.process_string(
                        processed, node_lookup, content_renderer, target_format
                    )
            return processed
        else:
            # Structured content (yaml, json)
            processed = content
            for strategy in self.strategies:
                if strategy.can_process(processed):
                    processed = strategy.process_structure(
                        processed, node_lookup, content_renderer, target_format
                    )
            return processed

    def _find_node(self, path: str, network: NodeNetwork) -> Optional[ContextNode]:
        """Find node in network by path.

        # AICODE-NOTE: This consolidates the duplicate node lookup logic
        # that was repeated 12+ times in render_node_network. The lookup
        # strategy tries exact match, partial match, and suffix match
        # to handle various path formats (relative, absolute, with/without extension).
        # Also handles versioned files by matching base names (without version suffix).
        """
        from pathlib import Path
        import re

        # Normalize the search path
        search_path = Path(path)
        search_name = search_path.name
        search_base = search_name.rsplit(".", 1)[0] if "." in search_name else search_name
        search_ext = search_path.suffix

        for node_id, node in network.nodes.items():
            node_path = Path(node_id)

            # Exact match
            if path == str(node_id) or path in str(node_id) or str(node_id).endswith(path):
                return node

            # Match by base name (handles versioned files)
            # Check if the node path ends with the same directory structure and base name
            node_name = node_path.name
            node_base = node_name.rsplit(".", 1)[0] if "." in node_name else node_name
            node_ext = node_path.suffix

            # Remove version suffix from node base name for comparison
            version_match = re.search(r"_v(\d+(?:\.\d+)*(?:\.\d+)?)", node_base)
            if version_match:
                node_base_no_version = node_base.replace(version_match.group(0), "")
            else:
                node_base_no_version = node_base

            # Check if base names and extensions match, and directory structure matches
            if (
                node_base_no_version == search_base
                and node_ext == search_ext
                and (
                    str(node_path.parent).endswith(str(search_path.parent))
                    or str(search_path.parent) in str(node_path.parent)
                )
            ):
                return node

        return None

    def _lookup_resolved_reference(
        self, owner: ContextNode, path: str, network: NodeNetwork
    ) -> Optional[ContextNode]:
        """Return node using the resolver metadata captured during network build."""
        resolved_candidates: list[str] = []

        for reference in owner.references:
            if reference.path != path:
                continue
            resolved_path = getattr(reference, "resolved_path", None)
            if resolved_path:
                resolved_candidates.append(resolved_path)

        for candidate in resolved_candidates:
            node = network.nodes.get(candidate)
            if node is not None:
                return node

        return None

    def _render_child(
        self,
        child: ContextNode,
        network: NodeNetwork,
        child_format: str,
        parent_format: str,
    ) -> Any:
        """Render a child node for inline insertion.

        # AICODE-NOTE: This handles format conversion when embedding content:
        # - Text nodes: recursively inline their references
        # - Structured nodes: resolve references and format appropriately
        # - Cross-format embedding: wrap YAML/JSON in code blocks for markdown

        Args:
            child: Child node to render
            network: Network for recursive lookups
            child_format: Format requested for the child content
            parent_format: Target format of the parent (for wrapping decisions)

        Returns:
            Rendered content (string or dict depending on formats)
        """
        # Recursively process the child node
        child_content = self.inline_references(child, network, child_format)

        # Handle wrapping for cross-format embedding
        if parent_format == "markdown":
            # When embedding in markdown, wrap structured content in code blocks
            if child.format in ("yaml", "json") and isinstance(child_content, dict):
                if child.format == "yaml":
                    native_str = yaml.dump(
                        child_content, default_flow_style=False, sort_keys=False
                    ).strip()
                    return f"```yaml\n{native_str}\n```"
                else:
                    native_str = json.dumps(child_content, indent=2)
                    return f"```json\n{native_str}\n```"

        # For non-markdown parent formats or when child is text, return as-is
        if isinstance(child_content, str):
            return child_content

        # Convert structured content to string if needed
        if child_format in ("yaml",) and isinstance(child_content, dict):
            return yaml.dump(child_content, default_flow_style=False, sort_keys=False).strip()
        elif child_format in ("json",) and isinstance(child_content, dict):
            return json.dumps(child_content, indent=2)

        return child_content
