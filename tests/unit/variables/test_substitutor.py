"""Unit tests for VariableSubstitutor."""

import pytest

from promptic.context.variables.models import SubstitutionContext
from promptic.context.variables.substitutor import VariableSubstitutor


class TestVariableSubstitutor:
    """Test VariableSubstitutor variable substitution logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.substitutor = VariableSubstitutor()

    def test_substitute_simple_variable(self):
        """Test basic variable substitution."""
        context = SubstitutionContext(
            node_id="test.md",
            node_name="test",
            hierarchical_path="test",
            content="Hello {{name}}!",
            format="markdown",
            variables={"name": "Alice"},
        )

        result = self.substitutor.substitute(context)
        assert result == "Hello Alice!"

    def test_substitute_multiple_occurrences(self):
        """Test that all occurrences are replaced."""
        context = SubstitutionContext(
            node_id="test.md",
            node_name="test",
            hierarchical_path="test",
            content="{{name}} says hello to {{name}}",
            format="markdown",
            variables={"name": "Bob"},
        )

        result = self.substitutor.substitute(context)
        assert result == "Bob says hello to Bob"

    def test_substitute_multiple_variables(self):
        """Test substitution of multiple different variables."""
        context = SubstitutionContext(
            node_id="test.md",
            node_name="test",
            hierarchical_path="test",
            content="{{greeting}} {{name}}, your task is {{task}}.",
            format="markdown",
            variables={"greeting": "Hello", "name": "Charlie", "task": "review"},
        )

        result = self.substitutor.substitute(context)
        assert result == "Hello Charlie, your task is review."

    def test_substitute_undefined_variable(self):
        """Test that undefined variables are left unchanged."""
        context = SubstitutionContext(
            node_id="test.md",
            node_name="test",
            hierarchical_path="test",
            content="Hello {{name}}, your {{undefined}} is waiting.",
            format="markdown",
            variables={"name": "Diana"},
        )

        result = self.substitutor.substitute(context)
        assert result == "Hello Diana, your {{undefined}} is waiting."

    def test_substitute_no_variables(self):
        """Test that content is unchanged when no variables provided."""
        context = SubstitutionContext(
            node_id="test.md",
            node_name="test",
            hierarchical_path="test",
            content="Hello {{name}}!",
            format="markdown",
            variables={},
        )

        result = self.substitutor.substitute(context)
        assert result == "Hello {{name}}!"

    def test_substitute_node_scoped_variable(self):
        """Test that node-scoped variables apply only to matching nodes."""
        variables = {"name": "Alice", "instructions.format": "detailed"}

        # For instructions node
        context_instructions = SubstitutionContext(
            node_id="instructions.md",
            node_name="instructions",
            hierarchical_path="root.instructions",
            content="Format: {{format}}",
            format="markdown",
            variables=variables,
        )
        result_instructions = self.substitutor.substitute(context_instructions)
        assert result_instructions == "Format: detailed"

        # For different node
        context_other = SubstitutionContext(
            node_id="templates.md",
            node_name="templates",
            hierarchical_path="root.templates",
            content="Format: {{format}}",
            format="markdown",
            variables=variables,
        )
        result_other = self.substitutor.substitute(context_other)
        assert result_other == "Format: {{format}}"  # Undefined, kept unchanged

    def test_substitute_path_scoped_variable(self):
        """Test that path-scoped variables apply only at specific paths."""
        variables = {
            "name": "Bob",
            "root.group.instructions.style": "technical",
        }

        # At exact path
        context_exact = SubstitutionContext(
            node_id="instructions.md",
            node_name="instructions",
            hierarchical_path="root.group.instructions",
            content="Style: {{style}}",
            format="markdown",
            variables=variables,
        )
        result_exact = self.substitutor.substitute(context_exact)
        assert result_exact == "Style: technical"

        # At different path
        context_other = SubstitutionContext(
            node_id="instructions.md",
            node_name="instructions",
            hierarchical_path="root.other.instructions",
            content="Style: {{style}}",
            format="markdown",
            variables=variables,
        )
        result_other = self.substitutor.substitute(context_other)
        assert result_other == "Style: {{style}}"  # Undefined, kept unchanged

    def test_substitute_with_type_conversion(self):
        """Test that non-string values are converted to strings."""
        context = SubstitutionContext(
            node_id="test.md",
            node_name="test",
            hierarchical_path="test",
            content="Count: {{count}}, Active: {{active}}",
            format="markdown",
            variables={"count": 42, "active": True},
        )

        result = self.substitutor.substitute(context)
        assert result == "Count: 42, Active: True"

    def test_validate_variables_valid(self):
        """Test validation of valid variable names."""
        variables = {
            "user_name": "Alice",
            "instructions.format": "detailed",
            "root.group.node.style": "technical",
        }

        invalid = self.substitutor.validate_variables(variables)
        assert invalid == []

    def test_validate_variables_invalid(self):
        """Test validation of invalid variable names."""
        variables = {
            "123invalid": "value",  # Starts with number
            "user-name": "value",  # Contains dash
            "valid_var": "value",
        }

        invalid = self.substitutor.validate_variables(variables)
        assert "123invalid" in invalid
        assert "user-name" in invalid
        assert "valid_var" not in invalid

    def test_jinja2_format_uses_jinja2_engine(self):
        """Test that Jinja2 format uses Jinja2 templating engine."""
        context = SubstitutionContext(
            node_id="template.jinja2",
            node_name="template",
            hierarchical_path="root.template",
            content="Hello {{ name }}!",  # Note: Jinja2 allows spaces
            format="jinja2",
            variables={"name": "Eva"},
        )

        result = self.substitutor.substitute(context)
        assert result == "Hello Eva!"

    def test_jinja2_with_filters(self):
        """Test Jinja2 variable substitution with filters."""
        context = SubstitutionContext(
            node_id="template.jinja2",
            node_name="template",
            hierarchical_path="root.template",
            content="Hello {{ name|upper }}!",
            format="jinja2",
            variables={"name": "frank"},
        )

        result = self.substitutor.substitute(context)
        assert result == "Hello FRANK!"

    def test_jinja2_undefined_variable(self):
        """Test Jinja2 handles undefined variables gracefully."""
        context = SubstitutionContext(
            node_id="template.jinja2",
            node_name="template",
            hierarchical_path="root.template",
            content="Hello {{ name }}, your {{ undefined }} is waiting.",
            format="jinja2",
            variables={"name": "Grace"},
        )

        result = self.substitutor.substitute(context)
        # DebugUndefined renders undefined as empty string
        assert "Hello Grace" in result
        assert "undefined" in result.lower()  # DebugUndefined includes debug info
