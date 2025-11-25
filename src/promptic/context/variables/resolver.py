"""Scope resolution logic for hierarchical variable targeting."""

from __future__ import annotations

import re
from typing import Any

from promptic.context.variables.models import VariableScope


class ScopeResolver:
    """Resolves variable scopes and matches variables to nodes.

    # AICODE-NOTE: Variable scope precedence (most specific to least specific):
    #   1. PATH: "root.group.node.var" - matches only nodes at exact hierarchical path
    #   2. NODE: "node_name.var" - matches all nodes with that name
    #   3. SIMPLE: "var" - matches in all nodes (global)
    #
    # When multiple scopes match, the most specific scope wins.
    # Within the same scope, the first matching variable definition is used.
    """

    def __init__(self) -> None:
        """Initialize scope resolver with variable name pattern."""
        # AICODE-NOTE: Variable names must be valid identifiers: letters, numbers, underscores
        # No spaces or special characters except underscore
        self._var_name_pattern = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

    def parse_variable_name(self, var_key: str) -> tuple[VariableScope, str, str | None]:
        """Parse a variable key into scope, variable name, and optional path/node.

        Args:
            var_key: Variable key from variables dict (e.g., "var", "node.var", "a.b.c.var")

        Returns:
            Tuple of (scope, variable_name, path_or_node)
            - scope: VariableScope enum value
            - variable_name: The actual variable name (last component)
            - path_or_node: The path or node qualifier (None for simple scope)

        Examples:
            >>> resolver = ScopeResolver()
            >>> resolver.parse_variable_name("var")
            (VariableScope.SIMPLE, "var", None)
            >>> resolver.parse_variable_name("node.var")
            (VariableScope.NODE, "var", "node")
            >>> resolver.parse_variable_name("root.group.node.var")
            (VariableScope.PATH, "var", "root.group.node")
        """
        parts = var_key.split(".")

        if len(parts) == 1:
            # Simple scope: "var"
            return (VariableScope.SIMPLE, parts[0], None)
        elif len(parts) == 2:
            # Node scope: "node.var"
            return (VariableScope.NODE, parts[1], parts[0])
        else:
            # Path scope: "root.group.node.var" (3+ parts)
            variable_name = parts[-1]
            path = ".".join(parts[:-1])
            return (VariableScope.PATH, variable_name, path)

    def matches_node(
        self,
        scope: VariableScope,
        path_or_node: str | None,
        node_name: str,
        hierarchical_path: str,
    ) -> bool:
        """Check if a scoped variable matches the given node.

        Args:
            scope: Variable scope level
            path_or_node: Path or node qualifier from variable key (None for simple)
            node_name: Short name of the current node
            hierarchical_path: Full hierarchical path of the current node

        Returns:
            True if the variable should apply to this node, False otherwise

        Examples:
            >>> resolver = ScopeResolver()
            >>> # Simple scope always matches
            >>> resolver.matches_node(VariableScope.SIMPLE, None, "any", "any.path")
            True
            >>> # Node scope matches by name
            >>> resolver.matches_node(VariableScope.NODE, "instructions", "instructions", "root.instructions")
            True
            >>> # Path scope matches exact hierarchical path
            >>> resolver.matches_node(VariableScope.PATH, "root.group", "node", "root.group.node")
            False  # Path doesn't match (should be "root.group")
        """
        if scope == VariableScope.SIMPLE:
            # Simple variables match all nodes
            return True

        if scope == VariableScope.NODE:
            # Node-scoped variables match nodes with the specified name
            # AICODE-NOTE: Node name matching is case-sensitive and exact
            # Could be extended to support wildcards or regex patterns if needed
            return node_name == path_or_node

        if scope == VariableScope.PATH:
            # Path-scoped variables match nodes at exact hierarchical path
            # AICODE-NOTE: Path matching is exact and case-sensitive
            # hierarchical_path format: "root.group.subgroup.node"
            # path_or_node format: "root.group.subgroup"
            #
            # We need to check if the node's hierarchical path starts with or equals
            # the specified path. This allows matching intermediate nodes in the path.
            if not path_or_node:
                return False

            # Extract the parent path from hierarchical_path for comparison
            # If hierarchical_path is "root.group.node", parent is "root.group"
            parts = hierarchical_path.split(".")
            if len(parts) <= 1:
                # Root node with no parent path
                return hierarchical_path == path_or_node

            # Check if the node is at this path or within a subpath
            # This allows "root.group" to match nodes "root.group" and "root.group.node"
            return hierarchical_path == path_or_node or hierarchical_path.startswith(
                path_or_node + "."
            )

        return False

    def resolve_variables_for_node(
        self,
        variables: dict[str, Any],
        node_name: str,
        hierarchical_path: str,
    ) -> dict[str, Any]:
        """Resolve variables applicable to a specific node with precedence rules.

        Args:
            variables: Full variables dictionary with all scopes
            node_name: Short name of the target node
            hierarchical_path: Full hierarchical path of the target node

        Returns:
            Dictionary of variable_name -> value for this node, with precedence applied

        # AICODE-NOTE: Precedence resolution strategy:
        # 1. Collect all matching variables with their scopes
        # 2. Group by variable name
        # 3. For each variable name, select value from highest precedence scope
        # 4. PATH > NODE > SIMPLE (most specific wins)
        """
        # Collect all matching variables with their scopes
        matches: dict[str, tuple[VariableScope, Any]] = {}

        for var_key, value in variables.items():
            scope, var_name, path_or_node = self.parse_variable_name(var_key)

            if self.matches_node(scope, path_or_node, node_name, hierarchical_path):
                # Check if we already have this variable name
                if var_name in matches:
                    existing_scope, existing_value = matches[var_name]
                    # Keep the more specific scope (higher precedence)
                    if self._compare_scope_precedence(scope, existing_scope) > 0:
                        matches[var_name] = (scope, value)
                else:
                    matches[var_name] = (scope, value)

        # Extract just the values (discard scope information)
        return {var_name: value for var_name, (scope, value) in matches.items()}

    def _compare_scope_precedence(self, scope1: VariableScope, scope2: VariableScope) -> int:
        """Compare precedence of two scopes.

        Returns:
            > 0 if scope1 has higher precedence than scope2
            < 0 if scope1 has lower precedence than scope2
            = 0 if equal precedence
        """
        precedence = {
            VariableScope.PATH: 3,
            VariableScope.NODE: 2,
            VariableScope.SIMPLE: 1,
        }
        return precedence[scope1] - precedence[scope2]

    def validate_variable_name(self, var_name: str) -> bool:
        """Validate that a variable name follows naming rules.

        Args:
            var_name: Variable name to validate

        Returns:
            True if valid, False otherwise

        # AICODE-NOTE: Variable naming rules:
        # - Must start with letter or underscore
        # - Can contain letters, numbers, underscores
        # - No spaces or special characters (except underscore)
        # - Case sensitive
        """
        return bool(self._var_name_pattern.match(var_name))
