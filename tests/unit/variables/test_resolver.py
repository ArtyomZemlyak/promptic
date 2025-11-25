"""Unit tests for ScopeResolver."""

import pytest

from promptic.context.variables.models import VariableScope
from promptic.context.variables.resolver import ScopeResolver


class TestScopeResolver:
    """Test ScopeResolver variable scope parsing and matching."""

    def setup_method(self):
        """Set up test fixtures."""
        self.resolver = ScopeResolver()

    def test_parse_simple_variable(self):
        """Test parsing simple variable name."""
        scope, var_name, path_or_node = self.resolver.parse_variable_name("user_name")

        assert scope == VariableScope.SIMPLE
        assert var_name == "user_name"
        assert path_or_node is None

    def test_parse_node_scoped_variable(self):
        """Test parsing node-scoped variable."""
        scope, var_name, path_or_node = self.resolver.parse_variable_name("instructions.format")

        assert scope == VariableScope.NODE
        assert var_name == "format"
        assert path_or_node == "instructions"

    def test_parse_path_scoped_variable(self):
        """Test parsing path-scoped variable."""
        scope, var_name, path_or_node = self.resolver.parse_variable_name(
            "root.group.node.variable"
        )

        assert scope == VariableScope.PATH
        assert var_name == "variable"
        assert path_or_node == "root.group.node"

    def test_simple_scope_matches_all_nodes(self):
        """Test that simple scope matches any node."""
        assert self.resolver.matches_node(VariableScope.SIMPLE, None, "any_node", "any.path")
        assert self.resolver.matches_node(
            VariableScope.SIMPLE, None, "another_node", "another.path"
        )

    def test_node_scope_matches_by_name(self):
        """Test that node scope matches nodes by name."""
        # Should match nodes with name "instructions"
        assert self.resolver.matches_node(
            VariableScope.NODE, "instructions", "instructions", "root.instructions"
        )
        assert self.resolver.matches_node(
            VariableScope.NODE, "instructions", "instructions", "group.instructions"
        )

        # Should not match nodes with different names
        assert not self.resolver.matches_node(
            VariableScope.NODE, "instructions", "templates", "root.templates"
        )

    def test_path_scope_matches_exact_path(self):
        """Test that path scope matches exact hierarchical path."""
        # Should match node at exact path
        assert self.resolver.matches_node(
            VariableScope.PATH, "root.group", "node", "root.group.node"
        )

        # Should match intermediate node in path
        assert self.resolver.matches_node(VariableScope.PATH, "root.group", "group", "root.group")

        # Should not match different paths
        assert not self.resolver.matches_node(
            VariableScope.PATH, "root.group", "node", "root.other.node"
        )

    def test_resolve_variables_simple_scope(self):
        """Test resolving simple scope variables for a node."""
        variables = {
            "user_name": "Alice",
            "task_type": "analysis",
        }

        resolved = self.resolver.resolve_variables_for_node(variables, "any_node", "any.path")

        assert resolved == {"user_name": "Alice", "task_type": "analysis"}

    def test_resolve_variables_node_scope(self):
        """Test resolving node-scoped variables."""
        variables = {
            "user_name": "Alice",
            "instructions.format": "detailed",
            "templates.level": "advanced",
        }

        # For instructions node
        resolved_instructions = self.resolver.resolve_variables_for_node(
            variables, "instructions", "root.instructions"
        )
        assert resolved_instructions == {"user_name": "Alice", "format": "detailed"}

        # For templates node
        resolved_templates = self.resolver.resolve_variables_for_node(
            variables, "templates", "root.templates"
        )
        assert resolved_templates == {"user_name": "Alice", "level": "advanced"}

    def test_resolve_variables_path_scope(self):
        """Test resolving path-scoped variables."""
        variables = {
            "user_name": "Alice",
            "root.group.instructions.style": "technical",
        }

        # For instructions at correct path
        resolved = self.resolver.resolve_variables_for_node(
            variables, "instructions", "root.group.instructions"
        )
        assert resolved == {"user_name": "Alice", "style": "technical"}

        # For instructions at different path (should not get path-scoped var)
        resolved_other = self.resolver.resolve_variables_for_node(
            variables, "instructions", "root.other.instructions"
        )
        assert resolved_other == {"user_name": "Alice"}

    def test_scope_precedence(self):
        """Test that more specific scopes take precedence."""
        variables = {
            "format": "default",  # Simple scope
            "instructions.format": "node-specific",  # Node scope
            "root.group.instructions.format": "path-specific",  # Path scope
        }

        # At exact path: path scope wins
        resolved = self.resolver.resolve_variables_for_node(
            variables, "instructions", "root.group.instructions"
        )
        assert resolved["format"] == "path-specific"

        # At different path but same node name: node scope wins
        resolved_other = self.resolver.resolve_variables_for_node(
            variables, "instructions", "root.other.instructions"
        )
        assert resolved_other["format"] == "node-specific"

        # Different node name and path: simple scope
        resolved_different = self.resolver.resolve_variables_for_node(
            variables, "templates", "root.templates"
        )
        assert resolved_different["format"] == "default"

    def test_validate_variable_name_valid(self):
        """Test validation of valid variable names."""
        assert self.resolver.validate_variable_name("user_name")
        assert self.resolver.validate_variable_name("taskType")
        assert self.resolver.validate_variable_name("_private")
        assert self.resolver.validate_variable_name("var123")

    def test_validate_variable_name_invalid(self):
        """Test validation of invalid variable names."""
        assert not self.resolver.validate_variable_name("123var")  # Starts with number
        assert not self.resolver.validate_variable_name("user-name")  # Contains dash
        assert not self.resolver.validate_variable_name("user name")  # Contains space
        assert not self.resolver.validate_variable_name("user.name")  # Contains dot
