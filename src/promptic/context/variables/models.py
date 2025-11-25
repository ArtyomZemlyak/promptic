"""Domain models for variable substitution."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class VariableScope(str, Enum):
    """Variable resolution scope levels.

    Defines the three levels of variable targeting specificity:
    - SIMPLE: Global variables applied to all nodes (e.g., {"var": "value"})
    - NODE: Node-scoped variables targeting nodes by name (e.g., {"node.var": "value"})
    - PATH: Full-path variables targeting specific hierarchy positions
            (e.g., {"root.group.node.var": "value"})

    Precedence order: PATH > NODE > SIMPLE (most specific wins)
    """

    SIMPLE = "simple"
    NODE = "node"
    PATH = "path"


@dataclass
class SubstitutionContext:
    """Context for variable substitution in a node.

    Contains all information needed to perform variable substitution for a specific
    node in the hierarchy, including node identification, hierarchical position,
    content to process, and format-specific handling requirements.

    Attributes:
        node_id: Unique identifier for the node (typically file path)
        node_name: Short name of the node (filename without extension and version)
        hierarchical_path: Full dot-separated path in hierarchy (e.g., "root.group.node")
        content: Content string to perform variable substitution on
        format: File format identifier (markdown, yaml, json, jinja2)
        variables: Dictionary of variable names to values for substitution
    """

    node_id: str
    node_name: str
    hierarchical_path: str
    content: str
    format: str
    variables: dict[str, Any]

    def __post_init__(self):
        """Validate context fields."""
        if not self.node_id:
            raise ValueError("node_id cannot be empty")
        if not self.node_name:
            raise ValueError("node_name cannot be empty")
        if not self.format:
            raise ValueError("format cannot be empty")
        if self.variables is None:
            raise ValueError("variables cannot be None (use empty dict for no variables)")
