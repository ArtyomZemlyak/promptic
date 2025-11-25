"""Core variable substitution service."""

from __future__ import annotations

import re
from typing import Any

from promptic.context.variables.models import SubstitutionContext
from promptic.context.variables.resolver import ScopeResolver


class VariableSubstitutor:
    """Service for performing variable substitution in node content.

    # AICODE-NOTE: Substitution strategy:
    # 1. For Jinja2 files: delegate to Jinja2 templating engine (native support)
    # 2. For other formats: use {{variable_name}} marker pattern
    # 3. Apply scope resolution to determine which variables apply to each node
    # 4. Replace all occurrences of each variable in the content
    # 5. Undefined variables are left unchanged (graceful degradation)
    #
    # Variable marker pattern: {{var_name}}
    # - No spaces allowed inside markers
    # - Variable names must follow identifier rules (letters, numbers, underscores)
    # - Markers are replaced with string values (no type preservation)
    """

    def __init__(self):
        """Initialize variable substitutor with scope resolver."""
        self.resolver = ScopeResolver()

        # AICODE-NOTE: Variable marker pattern for non-Jinja2 formats
        # Matches {{variable_name}} where variable_name is a valid identifier
        # No spaces allowed inside the braces
        self._marker_pattern = re.compile(r"\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}")

    def substitute(self, context: SubstitutionContext) -> str:
        """Perform variable substitution in the given context.

        Args:
            context: Substitution context with node info, content, and variables

        Returns:
            Content with variables substituted according to scope rules

        # AICODE-NOTE: Substitution workflow:
        # 1. Resolve variables applicable to this node (scope resolution)
        # 2. Route to format-specific substitution method:
        #    - Jinja2: use Jinja2 templating engine
        #    - Others: use marker pattern replacement
        # 3. Return substituted content
        """
        if not context.variables:
            # No variables to substitute
            return context.content

        # Resolve variables for this specific node
        node_variables = self.resolver.resolve_variables_for_node(
            context.variables,
            context.node_name,
            context.hierarchical_path,
        )

        if not node_variables:
            # No variables apply to this node
            return context.content

        # Route to format-specific substitution
        if context.format == "jinja2":
            return self._substitute_jinja2(context.content, node_variables)
        else:
            return self._substitute_markers(context.content, node_variables)

    def _substitute_markers(self, content: str, variables: dict[str, Any]) -> str:
        """Substitute {{variable}} markers in content.

        Args:
            content: Content string with {{var}} markers
            variables: Dictionary of variable names to values

        Returns:
            Content with markers replaced by values

        # AICODE-NOTE: Marker substitution implementation:
        # - Find all {{var}} patterns in content
        # - For each match, look up variable in resolved variables dict
        # - If found, replace with string value
        # - If not found, leave marker unchanged (graceful degradation)
        # - All values are converted to strings (no type preservation)
        """

        def replace_marker(match: re.Match[str]) -> str:
            var_name = match.group(1)
            if var_name in variables:
                # Convert value to string
                value = variables[var_name]
                return str(value)
            else:
                # Variable not defined, keep marker unchanged
                return match.group(0)

        return self._marker_pattern.sub(replace_marker, content)

    def _substitute_jinja2(self, content: str, variables: dict[str, Any]) -> str:
        """Substitute variables in Jinja2 template using Jinja2 engine.

        Args:
            content: Jinja2 template content
            variables: Dictionary of variable names to values

        Returns:
            Rendered template with variables substituted

        # AICODE-NOTE: Jinja2 substitution uses native Jinja2 templating:
        # - Create Jinja2 template from content string
        # - Render template with variables dict as context
        # - Jinja2 handles variable syntax {{ var }}, filters, control structures
        # - Undefined variables raise error by default (can configure for graceful handling)
        # - Type preservation works correctly (Jinja2 handles it natively)
        """
        try:
            from jinja2 import DebugUndefined, Template

            # AICODE-NOTE: Using DebugUndefined to gracefully handle missing variables
            # Undefined variables are rendered as empty strings with debug info
            # This matches the graceful degradation behavior of marker substitution
            template = Template(content, undefined=DebugUndefined)
            return template.render(**variables)
        except ImportError as e:
            # AICODE-NOTE: Jinja2 should always be available (it's in dependencies)
            # But gracefully handle import errors just in case
            raise RuntimeError(
                "Jinja2 is required for Jinja2 variable substitution but is not installed"
            ) from e
        except Exception as e:
            # AICODE-NOTE: Jinja2 template rendering can fail for various reasons:
            # - Invalid Jinja2 syntax in template
            # - Variable value is not serializable
            # - Filter or function errors
            # Wrap all Jinja2 errors with context for better debugging
            raise RuntimeError(f"Jinja2 template rendering failed: {e}") from e

    def validate_variables(self, variables: dict[str, Any]) -> list[str]:
        """Validate variable names and return list of invalid names.

        Args:
            variables: Variables dictionary to validate

        Returns:
            List of invalid variable names (empty if all valid)

        # AICODE-NOTE: Validation checks:
        # - Variable keys must follow naming rules (parse and validate)
        # - Variable names (last component after dots) must be valid identifiers
        # - Returns list of problematic keys for user feedback
        """
        invalid = []

        for var_key in variables.keys():
            scope, var_name, path_or_node = self.resolver.parse_variable_name(var_key)

            # Validate the variable name component
            if not self.resolver.validate_variable_name(var_name):
                invalid.append(var_key)
                continue

            # Validate path/node components if present
            if path_or_node:
                # Split path and validate each component
                components = path_or_node.split(".")
                for component in components:
                    if not self.resolver.validate_variable_name(component):
                        invalid.append(var_key)
                        break

        return invalid
