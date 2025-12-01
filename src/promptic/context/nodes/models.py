"""Context node models for unified context node architecture."""

from __future__ import annotations

from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class NetworkConfig(BaseModel):
    """Configuration for network building operations.

    # AICODE-NOTE: Token counting removed - not used in examples 003-006.
    # Removed fields: max_tokens_per_node, max_tokens_per_network, token_model.
    # Network building now focuses on size and depth limits only.
    """

    max_depth: int = Field(default=10, ge=1, description="Maximum depth limit")
    max_node_size: int = Field(
        default=10 * 1024 * 1024, ge=1, description="Maximum size per node in bytes (default 10MB)"
    )
    max_network_size: int = Field(
        default=1000, ge=1, description="Maximum number of nodes in network"
    )


class NodeReference(BaseModel):
    """Structured reference to another node."""

    path: str = Field(..., min_length=1, description="Reference path (file path or node ID)")
    type: Literal["file", "id", "uri"] = Field(
        ..., description="Reference type determining resolution strategy"
    )
    label: Optional[str] = Field(default=None, description="Optional label for display")
    resolved_path: Optional[str] = Field(
        default=None,
        description=(
            "Resolved absolute path after version-aware resolution. "
            "Populated during network building to disambiguate versioned references."
        ),
    )


class ContextNode(BaseModel):
    """Unified domain entity representing any context element.

    Can represent blueprints, instructions, data, or memory as a unified node
    structure. Supports recursive composition where nodes can contain or
    reference other nodes.
    """

    id: str | UUID = Field(..., description="Node identifier (file path or UUID)")
    content: dict[str, Any] = Field(..., description="Format-agnostic content stored as JSON")
    format: Literal["yaml", "jinja2", "markdown", "json"] = Field(
        ..., description="Source format of the node"
    )
    semantic_type: Optional[Literal["blueprint", "instruction", "data", "memory"]] = Field(
        default=None,
        description="Optional semantic label (metadata only, doesn't affect structure)",
    )
    version: Optional[str] = Field(
        default=None, description="Version field reserved for future use"
    )
    references: list[NodeReference] = Field(
        default_factory=list, description="References to other nodes"
    )
    children: list[ContextNode] = Field(
        default_factory=list, description="Child nodes (for recursive composition)"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata (tags, owner, etc.)"
    )


class NodeNetwork(BaseModel):
    """Container for a complete node network with validation and resource tracking.

    # AICODE-NOTE: Token counting removed - not used in examples 003-006.
    # Removed field: total_tokens. Network tracking now focuses on size and depth only.
    """

    root: ContextNode = Field(..., description="Root node of the network")
    nodes: dict[str, ContextNode] = Field(
        default_factory=dict, description="All nodes in the network by ID"
    )
    total_size: int = Field(default=0, ge=0, description="Total size of all nodes in bytes")
    depth: int = Field(default=0, ge=0, description="Maximum depth of the network")
