"""Filesystem cleanup adapter for safe directory deletion."""

from __future__ import annotations

import shutil
from pathlib import Path

from promptic.versioning.utils.logging import get_logger, log_version_operation

logger = get_logger(__name__)


class FileSystemCleanup:
    """
    Filesystem cleanup adapter for safe directory deletion.

    # AICODE-NOTE: This adapter handles filesystem deletion operations with safety checks:
    # - Validates directories are export directories using heuristics
    # - Detects source directories to prevent accidental deletion
    # - Recursively deletes directories and all contents
    # - Handles permission errors and locked files gracefully
    """

    def validate_export_directory(self, directory: str) -> bool:
        """
        Validate directory is export directory using heuristics.

        # AICODE-NOTE: Export directory detection heuristics:
        # - Version postfixes in directory names (e.g., task1_v2, task1_v2.0.0)
        # - Located in common export directories (export/, exports/, deploy/)
        # - Contains files without version postfixes (exported files are unversioned)
        # - Preserved hierarchical structures matching source layouts

        Args:
            directory: Directory path to validate

        Returns:
            True if directory appears to be export directory, False if uncertain
        """
        path = Path(directory)

        # Check for version postfixes in directory name
        name = path.name
        if "_v" in name.lower() or any(char.isdigit() and "_" in name for char in name):
            return True

        # Check if in common export directories
        path_str = str(path)
        export_indicators = ["export", "exports", "deploy", "deployment"]
        if any(indicator in path_str.lower() for indicator in export_indicators):
            return True

        # Check if directory contains unversioned files (exported files are unversioned)
        if path.exists() and path.is_dir():
            files = list(path.rglob("*.md"))
            if files:
                # If all files are unversioned (no _v pattern), likely export directory
                versioned_count = sum(1 for f in files if "_v" in f.stem.lower())
                if versioned_count == 0 and len(files) > 0:
                    return True

        # Uncertain - return False
        return False

    def is_source_directory(self, directory: str) -> bool:
        """
        Check if directory appears to be source prompt directory.

        # AICODE-NOTE: Source directory detection heuristics:
        # - Contains versioned files (files with _v patterns in names)
        # - Located in common source directories (prompts/, instructions/, templates/)
        # - Multiple versioned files for same base name (version history present)

        Args:
            directory: Directory path to check

        Returns:
            True if directory appears to be source directory, False otherwise
        """
        path = Path(directory)

        if not path.exists() or not path.is_dir():
            return False

        # Check for versioned files
        versioned_files = list(path.rglob("*_v*.md")) + list(path.rglob("*_v*.txt"))
        if len(versioned_files) > 0:
            # Multiple versioned files indicate source directory
            return True

        # Check if in common source directories
        path_str = str(path)
        source_indicators = ["prompts", "instructions", "templates", "blueprints"]
        if any(indicator in path_str.lower() for indicator in source_indicators):
            # If in source directory and has files, likely source
            if list(path.glob("*.md")) or list(path.glob("*.txt")):
                return True

        return False

    def delete_directory(self, directory: str) -> None:
        """
        Recursively delete directory and all contents.

        # AICODE-NOTE: Deletion behavior:
        # - Recursively removes all files and subdirectories
        # - Handles permission errors gracefully
        # - Removes directory itself after contents are deleted

        Args:
            directory: Directory path to delete

        Raises:
            PermissionError: If deletion fails due to permissions
            OSError: If deletion fails for other reasons
        """
        path = Path(directory)

        if not path.exists():
            return

        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        log_version_operation(
            logger,
            "directory_deletion_started",
            path=directory,
        )

        try:
            shutil.rmtree(path)
            log_version_operation(
                logger,
                "directory_deletion_completed",
                path=directory,
            )
        except PermissionError as e:
            log_version_operation(
                logger,
                "directory_deletion_failed",
                path=directory,
                error="Permission denied",
            )
            raise PermissionError(f"Permission denied when deleting {directory}: {e}") from e
        except OSError as e:
            log_version_operation(
                logger,
                "directory_deletion_failed",
                path=directory,
                error=str(e),
            )
            raise OSError(f"Failed to delete {directory}: {e}") from e
