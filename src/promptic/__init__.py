"""Promptic context engineering library."""

from importlib.metadata import PackageNotFoundError, version

try:  # pragma: no cover - best effort for local development
    __version__ = version("promptic")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = ["__version__"]
