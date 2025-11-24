"""Version cleanup use case for safely removing exported version directories."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from promptic.versioning.adapters.filesystem_cleanup import FileSystemCleanup
from promptic.versioning.domain.errors import CleanupTargetNotFoundError, InvalidCleanupTargetError
from promptic.versioning.utils.logging import get_logger, log_version_operation

logger = get_logger(__name__)


class VersionCleanup:
    """
    Use case for cleaning up exported version directories.

    # AICODE-NOTE: This use case orchestrates cleanup operations with safety checks:
    # 1. Validates that target directory is an export directory (not source directory)
    # 2. Checks if directory exists
    # 3. Delegates deletion to FileSystemCleanup adapter
    # 4. Ensures source directories are never accidentally deleted
    """

    def __init__(self, filesystem_cleanup: Optional[FileSystemCleanup] = None) -> None:
        """
        Initialize version cleanup.

        Args:
            filesystem_cleanup: Filesystem cleanup adapter for deletion operations
        """
        from promptic.versioning.adapters.filesystem_cleanup import FileSystemCleanup

        self.filesystem_cleanup = filesystem_cleanup or FileSystemCleanup()

    def cleanup_exported_version(self, export_dir: str, require_confirmation: bool = False) -> None:
        """
        Remove exported version directory with safety validation.

        # AICODE-NOTE: Cleanup safeguards:
        # - Validates directory is export directory using heuristics
        # - Protects source directories from accidental deletion
        # - Raises clear errors for invalid targets
        # - Recursively deletes directory and all contents

        Args:
            export_dir: Export directory path to remove
            require_confirmation: Whether to require explicit confirmation (not implemented yet)

        Raises:
            InvalidCleanupTargetError: If target is source directory
            CleanupTargetNotFoundError: If directory doesn't exist
        """
        export_path = Path(export_dir)

        # Check if directory exists
        if not export_path.exists():
            raise CleanupTargetNotFoundError(export_dir)

        # Validate it's an export directory (not source directory)
        if self.filesystem_cleanup.is_source_directory(str(export_path)):
            raise InvalidCleanupTargetError(export_dir)

        # Validate export directory
        if not self.filesystem_cleanup.validate_export_directory(str(export_path)):
            # If validation is uncertain, require confirmation or raise error
            if require_confirmation:
                raise InvalidCleanupTargetError(
                    export_dir,
                    message=(
                        f"Uncertain if '{export_dir}' is an export directory. "
                        "Use require_confirmation=False to proceed anyway."
                    ),
                )

        log_version_operation(
            logger,
            "cleanup_started",
            path=export_dir,
        )

        # Delete directory
        try:
            self.filesystem_cleanup.delete_directory(str(export_path))

            log_version_operation(
                logger,
                "cleanup_completed",
                path=export_dir,
            )
        except Exception as e:
            log_version_operation(
                logger,
                "cleanup_failed",
                path=export_dir,
                error=str(e),
            )
            raise
