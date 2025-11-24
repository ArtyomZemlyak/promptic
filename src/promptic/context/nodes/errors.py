"""Error classes for context node operations."""

from __future__ import annotations

from typing import Optional


class FormatDetectionError(Exception):
    """Raised when format detection fails."""

    pass


class FormatParseError(Exception):
    """Raised when format parsing fails."""

    pass


class JSONConversionError(Exception):
    """Raised when JSON conversion fails."""

    pass


class ReferenceSyntaxError(Exception):
    """Raised when reference syntax is invalid."""

    pass


class NodeNetworkValidationError(Exception):
    """Raised when node network validation fails (e.g., cycles detected)."""

    def __init__(self, message: str, details: Optional[dict] = None):
        """Initialize validation error.

        Args:
            message: Error message
            details: Optional error details dictionary
        """
        super().__init__(message)
        self.details = details or {}


class NodeReferenceNotFoundError(Exception):
    """Raised when a node reference cannot be resolved."""

    def __init__(
        self,
        message: str,
        reference_path: Optional[str] = None,
        suggestions: Optional[list[str]] = None,
    ):
        """Initialize reference not found error.

        Args:
            message: Error message
            reference_path: Path that could not be resolved
            suggestions: Optional list of suggested paths
        """
        super().__init__(message)
        self.reference_path = reference_path
        self.suggestions = suggestions or []


class PathResolutionError(Exception):
    """Raised when path resolution fails."""

    pass


class NodeNetworkDepthExceededError(Exception):
    """Raised when network depth exceeds configured limit."""

    def __init__(
        self, message: str, current_depth: Optional[int] = None, max_depth: Optional[int] = None
    ):
        """Initialize depth exceeded error.

        Args:
            message: Error message
            current_depth: Current depth that exceeded limit
            max_depth: Maximum allowed depth
        """
        super().__init__(message)
        self.current_depth = current_depth
        self.max_depth = max_depth


class NodeResourceLimitExceededError(Exception):
    """Raised when resource limits are exceeded (size, depth, etc.).

    # AICODE-NOTE: Token counting removed - not used in examples 003-006.
    # Limit types are now: "node_size", "network_size", "depth"
    """

    def __init__(
        self,
        message: str,
        limit_type: Optional[str] = None,
        current_value: Optional[int] = None,
        max_value: Optional[int] = None,
    ):
        """Initialize resource limit exceeded error.

        Args:
            message: Error message
            limit_type: Type of limit exceeded (e.g., "node_size", "network_size", "depth")
            current_value: Current value that exceeded limit
            max_value: Maximum allowed value
        """
        super().__init__(message)
        self.limit_type = limit_type
        self.current_value = current_value
        self.max_value = max_value


class LegacyAdapterError(Exception):
    """Raised when legacy adapter operations fail."""

    pass
