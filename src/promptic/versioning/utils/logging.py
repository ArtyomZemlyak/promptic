"""Structured logging configuration for versioning operations."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict

from promptic.settings.base import ContextEngineSettings


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger configured for versioning operations.

    # AICODE-NOTE: This logger uses structured logging with configurable levels
    via PROMPTIC_LOG_LEVEL environment variable. Default level is INFO to prevent
    log noise in production while enabling DEBUG diagnostics when needed.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Configure level from environment variable or settings
    log_level_str = os.getenv("PROMPTIC_LOG_LEVEL", "INFO").upper()
    try:
        log_level = getattr(logging, log_level_str)
    except AttributeError:
        log_level = logging.INFO

    logger.setLevel(log_level)

    # Add handler if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(log_level)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def log_version_operation(
    logger: logging.Logger,
    operation: str,
    version: str | None = None,
    path: str | None = None,
    **kwargs: Any,
) -> None:
    """
    Log a versioning operation with structured fields.

    Args:
        logger: Logger instance
        operation: Operation type (e.g., "version_resolved", "export_started")
        version: Version identifier (optional)
        path: File or directory path (optional)
        **kwargs: Additional structured fields to log
    """
    fields: Dict[str, Any] = {
        "operation": operation,
    }
    if version is not None:
        fields["version"] = version
    if path is not None:
        fields["path"] = path
    fields.update(kwargs)

    # Format as structured log message
    field_str = ", ".join(f"{k}={v}" for k, v in fields.items())
    logger.info(f"Versioning operation: {field_str}")
