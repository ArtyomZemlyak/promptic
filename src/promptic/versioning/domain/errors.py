"""Error types for versioning operations."""

from __future__ import annotations


class VersionNotFoundError(Exception):
    """Raised when a requested version doesn't exist in directory."""

    def __init__(
        self,
        path: str,
        version_spec: str,
        available_versions: list[str] | None = None,
        message: str | None = None,
    ) -> None:
        """
        Initialize VersionNotFoundError.

        Args:
            path: Directory path where version was searched
            version_spec: Version specification that was requested
            available_versions: List of available versions in directory
            message: Custom error message
        """
        self.path = path
        self.version_spec = version_spec
        self.available_versions = available_versions or []
        if message is None:
            versions_str = ", ".join(self.available_versions) if self.available_versions else "none"
            message = (
                f"Version '{version_spec}' not found in '{path}'. "
                f"Available versions: {versions_str}"
            )
        self.message = message
        super().__init__(self.message)


class VersionDetectionError(Exception):
    """Raised when version detection is ambiguous or fails."""

    def __init__(
        self,
        filename: str,
        matched_patterns: list[str] | None = None,
        message: str | None = None,
    ) -> None:
        """
        Initialize VersionDetectionError.

        Args:
            filename: Filename where version detection failed
            matched_patterns: List of patterns that matched (if ambiguous)
            message: Custom error message
        """
        self.filename = filename
        self.matched_patterns = matched_patterns or []
        if message is None:
            patterns_str = ", ".join(self.matched_patterns) if self.matched_patterns else "none"
            message = (
                f"Ambiguous version detection in '{filename}'. " f"Matched patterns: {patterns_str}"
            )
        self.message = message
        super().__init__(self.message)


class VersionResolutionCycleError(Exception):
    """Raised when circular version references are detected in hierarchical resolution."""

    def __init__(self, cycle_path: list[str], message: str | None = None) -> None:
        """
        Initialize VersionResolutionCycleError.

        Args:
            cycle_path: List of paths forming the cycle
            message: Custom error message
        """
        self.cycle_path = cycle_path
        if message is None:
            path_str = " -> ".join(cycle_path)
            message = f"Circular version reference detected: {path_str}"
        self.message = message
        super().__init__(self.message)


class ExportError(Exception):
    """Raised when export operation fails."""

    def __init__(
        self,
        source_path: str,
        missing_files: list[str] | None = None,
        message: str | None = None,
    ) -> None:
        """
        Initialize ExportError.

        Args:
            source_path: Source path where export was attempted
            missing_files: List of files that were missing during export
            message: Custom error message
        """
        self.source_path = source_path
        self.missing_files = missing_files or []
        if message is None:
            files_str = ", ".join(self.missing_files) if self.missing_files else "unknown"
            message = f"Export failed for '{source_path}'. Missing files: {files_str}"
        self.message = message
        super().__init__(self.message)


class ExportDirectoryExistsError(Exception):
    """Raised when target export directory exists without overwrite flag."""

    def __init__(self, target_dir: str, message: str | None = None) -> None:
        """
        Initialize ExportDirectoryExistsError.

        Args:
            target_dir: Target directory that already exists
            message: Custom error message
        """
        self.target_dir = target_dir
        if message is None:
            message = (
                f"Export directory '{target_dir}' already exists. "
                "Use overwrite=True to overwrite."
            )
        self.message = message
        super().__init__(self.message)


class ExportDirectoryConflictError(Exception):
    """Raised when export directory contains non-export files."""

    def __init__(self, target_dir: str, message: str | None = None) -> None:
        """
        Initialize ExportDirectoryConflictError.

        Args:
            target_dir: Target directory with conflicts
            message: Custom error message
        """
        self.target_dir = target_dir
        if message is None:
            message = (
                f"Export directory '{target_dir}' contains non-export files. "
                "Cannot safely overwrite."
            )
        self.message = message
        super().__init__(self.message)


class InvalidCleanupTargetError(Exception):
    """Raised when cleanup target is a source directory (not export directory)."""

    def __init__(self, target_dir: str, message: str | None = None) -> None:
        """
        Initialize InvalidCleanupTargetError.

        Args:
            target_dir: Target directory that is invalid for cleanup
            message: Custom error message
        """
        self.target_dir = target_dir
        if message is None:
            message = (
                f"Cannot delete source prompt directory '{target_dir}'. "
                "Use export directory paths only."
            )
        self.message = message
        super().__init__(self.message)


class CleanupTargetNotFoundError(Exception):
    """Raised when cleanup target directory doesn't exist."""

    def __init__(self, target_dir: str, message: str | None = None) -> None:
        """
        Initialize CleanupTargetNotFoundError.

        Args:
            target_dir: Target directory that doesn't exist
            message: Custom error message
        """
        self.target_dir = target_dir
        if message is None:
            message = f"Export directory '{target_dir}' not found."
        self.message = message
        super().__init__(self.message)
