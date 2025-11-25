"""Variable substitution module for dynamic prompt generation.

This module provides functionality for inserting runtime variable values into prompts
with support for hierarchical scope resolution (simple, node-scoped, full-path).
"""

from promptic.context.variables.models import SubstitutionContext, VariableScope
from promptic.context.variables.resolver import ScopeResolver
from promptic.context.variables.substitutor import VariableSubstitutor

__all__ = [
    "VariableScope",
    "SubstitutionContext",
    "ScopeResolver",
    "VariableSubstitutor",
]
