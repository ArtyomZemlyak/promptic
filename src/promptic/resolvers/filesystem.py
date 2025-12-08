"""Filesystem-based reference resolver implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from promptic.context.nodes.errors import NodeReferenceNotFoundError, PathResolutionError
from promptic.context.nodes.models import ContextNode
from promptic.resolvers.base import NodeReferenceResolver
from promptic.versioning import VersionSpec
from promptic.versioning.adapters.scanner import VersionedFileScanner
from promptic.versioning.domain.errors import VersionNotFoundError
from promptic.versioning.utils.path_resolver import PromptPathResolver

try:  # pragma: no cover - optional typing dependency
    from promptic.versioning.config import VersioningConfig
except Exception:  # pragma: no cover
    VersioningConfig = None  # type: ignore


class FilesystemReferenceResolver(NodeReferenceResolver):
    """Filesystem-based reference resolver.

    Resolves prompt references that may omit explicit version suffixes, extensions,
    or point to prompt directories. Integrates version-aware resolution (including
    classifiers) via PromptPathResolver so callers can link to high-level prompt
    folders or base filenames and still get a concrete file.
    """

    def __init__(
        self,
        root: Path | None = None,
        version: Optional[VersionSpec] = None,
        *,
        classifier: dict[str, str] | None = None,
        versioning_config: "VersioningConfig | None" = None,
    ):
        """Initialize filesystem reference resolver.

        Args:
            root: Root directory for resolving relative paths. If None, uses current working directory.
            version: Optional version specification for version-aware resolution ("latest", "v1", etc.)
            classifier: Optional classifier filter propagated to nested resolution.
            versioning_config: Optional VersioningConfig shared with the VersionedFileScanner.
        """
        self.root = root or Path.cwd()
        self.version = version
        self.classifier = classifier
        self._path_resolver = PromptPathResolver(versioning_config=versioning_config)

    def resolve(
        self, path: str, base_path: Path, version: Optional[VersionSpec] = None
    ) -> ContextNode:
        """Resolve a reference path to a node.

        # AICODE-NOTE: Version-aware resolution: If version is provided (either via constructor
        or method parameter), the resolver uses VersionedFileScanner to resolve versioned files.
        The method parameter takes precedence over the constructor parameter, enabling
        hierarchical version specifications.

        Args:
            path: Reference path (file path)
            base_path: Base path for relative resolution
            version: Optional version specification (overrides constructor version if provided)

        Returns:
            Resolved ContextNode instance

        Raises:
            NodeReferenceNotFoundError: If reference cannot be resolved
            PathResolutionError: If path resolution fails
        """
        effective_version = version if version is not None else self.version

        try:
            resolved_path = self._resolve_path(path, base_path, effective_version)
        except (FileNotFoundError, VersionNotFoundError) as exc:
            raise NodeReferenceNotFoundError(f"Reference not found: {path} ({exc})") from exc

        # Load node using SDK function (lazy import to avoid circular dependency)
        try:
            from promptic.sdk.nodes import load_node

            return load_node(resolved_path)
        except Exception as e:
            raise PathResolutionError(f"Failed to load node from {resolved_path}: {e}") from e

    def validate(self, path: str, base_path: Path, version: Optional[VersionSpec] = None) -> bool:
        """Validate that a reference path is valid.

        Args:
            path: Reference path to validate
            base_path: Base path for relative resolution
            version: Optional version specification for version-aware validation

        Returns:
            True if path is valid, False otherwise
        """
        try:
            version_to_use = self._determine_version_spec(path, version)
            resolved_path = self._resolve_path(path, base_path, version_to_use)
            return resolved_path.exists()
        except (FileNotFoundError, VersionNotFoundError, PathResolutionError):
            return False

    def _resolve_path(
        self, path: str, base_path: Path, version: Optional[VersionSpec] = None
    ) -> Path:
        base_dir = base_path.parent if base_path.is_file() else base_path

        try:
            version_to_use = self._determine_version_spec(path, version)
            return self._path_resolver.resolve(
                raw_path=path,
                base_dir=base_dir,
                version_spec=version_to_use,
                classifier=self.classifier,
                default_version="latest",
            )
        except (FileNotFoundError, VersionNotFoundError):
            raise
        except Exception as e:
            raise PathResolutionError(f"Failed to resolve path {path} from {base_path}: {e}") from e

    def _determine_version_spec(
        self, ref_path: str, provided_version: Optional[VersionSpec]
    ) -> Optional[VersionSpec]:
        """
        Decide which version spec to use for a reference.

        Rules:
        - If reference name already includes version suffix -> use provided/self version
        - Otherwise -> fall back to latest (None here; PromptPathResolver will use default_version)
        """

        version_to_use = provided_version if provided_version is not None else self.version
        if version_to_use is None:
            return None

        scanner = VersionedFileScanner(config=self._path_resolver._config)
        basename = Path(ref_path).name
        has_version = scanner.extract_version_from_filename(basename) is not None

        return version_to_use if has_version else None
