"""Promptic context package - simplified after blueprint/adapter removal.

# AICODE-NOTE: Blueprint and adapter error classes removed. Only node network
#              error classes remain (in context.nodes.errors). Logging module
#              removed as it was only used by blueprints.
"""

# Note: Most error classes are now defined in context.nodes.errors
# This module is kept minimal for backward compatibility during migration

__all__ = []  # type: ignore[var-annotated]
