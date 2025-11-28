"""Versioned file scanner for filesystem-based version detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from promptic.versioning.domain.errors import ClassifierNotFoundError, VersionNotFoundError
from promptic.versioning.domain.pattern import VersionComponents, VersionPattern
from promptic.versioning.domain.resolver import VersionResolver, VersionSpec
from promptic.versioning.utils.cache import VersionCache
from promptic.versioning.utils.logging import get_logger, log_version_operation
from promptic.versioning.utils.semantic_version import (
    SemanticVersion,
    get_latest_version,
    normalize_version,
)

if TYPE_CHECKING:
    from promptic.versioning.config import VersioningConfig

logger = get_logger(__name__)


@dataclass
class VersionInfo:
    """
    Information about a versioned file.

    # AICODE-NOTE: This dataclass stores metadata about versioned files discovered
    during directory scanning. It includes the filename, full path, base name
    (without version), parsed semantic version, and whether the file is versioned.

    Extended in 009-advanced-versioning to include classifiers field for
    supporting language/audience/environment classifiers.
    """

    filename: str
    path: str
    base_name: str
    version: Optional[SemanticVersion]
    is_versioned: bool
    classifiers: dict[str, str] = field(default_factory=dict)


class VersionedFileScanner(VersionResolver):
    """
    Scanner that detects and resolves versioned files from filesystem.

    # AICODE-NOTE: This scanner implements version detection using configurable
    patterns via VersioningConfig. When config is not provided, defaults to
    underscore delimiter (_v1, _v1.1, _v1.1.1) for backward compatibility.

    Config injection allows:
    - Custom delimiters ("_", "-", ".")
    - Multiple delimiters for mixed-convention directories
    - Custom regex patterns for non-standard versioning schemes
    - Prerelease filtering (exclude from "latest" by default)
    - Classifier-based filtering

    When multiple patterns exist in a filename, the last matching pattern is
    used as the version identifier. Version comparison follows standard
    semantic versioning rules (major.minor.patch precedence).
    """

    def __init__(self, config: "VersioningConfig | None" = None) -> None:
        """
        Initialize scanner with version detection patterns and cache.

        Args:
            config: Optional VersioningConfig for customization.
                   If None, uses default configuration (underscore delimiter).
        """
        self._config = config
        self._pattern = self._create_pattern(config)
        self.cache: VersionCache[list[VersionInfo]] = VersionCache()

        # Log config loading at DEBUG level
        if config is not None:
            log_version_operation(
                logger,
                "config_loaded",
                delimiter=config.delimiter,
                delimiters=str(config.delimiters) if config.delimiters else None,
                custom_pattern=config.version_pattern,
            )

    def _create_pattern(self, config: "VersioningConfig | None") -> VersionPattern:
        """Create VersionPattern from config or use default."""
        if config is not None:
            pattern = VersionPattern.from_config(config)
            log_version_operation(
                logger,
                "pattern_compiled",
                pattern=pattern.pattern_string,
            )
            return pattern
        return VersionPattern.default()

    @property
    def config(self) -> "VersioningConfig | None":
        """Get the current configuration."""
        return self._config

    @property
    def version_pattern(self) -> VersionPattern:
        """Get the current version pattern."""
        return self._pattern

    def _extract_classifiers(self, filename: str) -> dict[str, str]:
        """
        Extract classifier values from filename.

        # AICODE-NOTE: Classifier extraction follows strict ordering:
        # base-classifier(s)-version-postfix.ext
        # For example: prompt_en_v1.md -> {"lang": "en"}
        #              prompt_en_formal_v1.md -> {"lang": "en", "tone": "formal"}

        Args:
            filename: Filename to extract classifiers from

        Returns:
            Dictionary of classifier name -> value
        """
        if self._config is None or self._config.classifiers is None:
            return {}

        classifiers: dict[str, str] = {}

        # Get stem (remove extension)
        stem = Path(filename).stem

        # Remove version pattern to get base + classifiers
        base_with_classifiers = self._pattern.get_base_name(stem + ".tmp").replace(".tmp", "")

        # Check each configured classifier
        for classifier_name, classifier_config in self._config.classifiers.items():
            for value in classifier_config.values:
                # Determine delimiter to check
                delimiter = self._config.delimiter
                if self._config.delimiters:
                    delimiter = self._config.delimiters[0]

                # Check if value appears in filename with delimiter
                patterns_to_check = [
                    f"{delimiter}{value}{delimiter}",  # _en_
                    f"{delimiter}{value}",  # ends with _en (before version)
                ]

                for pattern in patterns_to_check:
                    if pattern in base_with_classifiers or base_with_classifiers.endswith(
                        f"{delimiter}{value}"
                    ):
                        classifiers[classifier_name] = value
                        break

                if classifier_name in classifiers:
                    break

        return classifiers

    def extract_version_from_filename(self, filename: str) -> Optional[SemanticVersion]:
        """
        Extract version identifier from filename using configured pattern.

        # AICODE-NOTE: This method uses the configured VersionPattern to find
        version patterns in filenames. When multiple patterns exist, the last
        matching pattern is used (handles edge cases like "prompt_v1.0_final_v2.1.md"
        deterministically).

        The filename is processed as stem (without extension) to prevent the
        prerelease pattern from capturing file extensions like ".md".

        Args:
            filename: Filename to extract version from

        Returns:
            SemanticVersion if version detected, None otherwise
        """
        # Use stem to avoid prerelease pattern capturing file extensions
        stem = Path(filename).stem
        components = self._pattern.extract_version(stem)
        if components is None:
            return None

        return SemanticVersion(
            major=components.major,
            minor=components.minor,
            patch=components.patch,
            prerelease=components.prerelease,
        )

    def normalize_version(self, version_str: str) -> SemanticVersion:
        """
        Normalize version string to full semantic version format.

        # AICODE-NOTE: Normalization rules:
        # - v1 → v1.0.0
        # - v1.1 → v1.1.0
        # - v1.1.1 → v1.1.1 (no change)

        Args:
            version_str: Version string to normalize

        Returns:
            Normalized SemanticVersion
        """
        return normalize_version(version_str)

    def scan_directory(self, directory: str, recursive: bool = False) -> list[VersionInfo]:
        """
        Scan directory for versioned files, return sorted list.

        # AICODE-NOTE: This method scans a directory for files matching version
        patterns, extracts version information and classifiers, and returns a
        sorted list using semantic versioning comparison. Results are cached
        and invalidated when directory modification time changes.

        Args:
            directory: Directory path to scan
            recursive: Whether to scan subdirectories recursively (default: False)

        Returns:
            Sorted list of VersionInfo (latest first)
        """
        # Check cache first (include config in cache key for correct invalidation)
        config_id = id(self._config) if self._config else "default"
        cache_key = f"{directory}:recursive={recursive}:config={config_id}"
        cached: list[VersionInfo] | None = self.cache.get(cache_key)
        if cached is not None:
            return cached

        path = Path(directory)
        if not path.exists() or not path.is_dir():
            return []

        versioned_files: list[VersionInfo] = []
        unversioned_files: list[VersionInfo] = []

        # Use rglob for recursive or iterdir for single level
        file_iterator = path.rglob("*") if recursive else path.iterdir()

        for file_path in file_iterator:
            if not file_path.is_file():
                continue

            filename = file_path.name
            version = self.extract_version_from_filename(filename)

            if version is not None:
                # Extract base name (remove version pattern)
                base_name = self._pattern.get_base_name(filename)
                # Extract classifiers
                classifiers = self._extract_classifiers(filename)

                versioned_files.append(
                    VersionInfo(
                        filename=filename,
                        path=str(file_path),
                        base_name=base_name,
                        version=version,
                        is_versioned=True,
                        classifiers=classifiers,
                    )
                )
            else:
                # Unversioned file
                unversioned_files.append(
                    VersionInfo(
                        filename=filename,
                        path=str(file_path),
                        base_name=filename,
                        version=None,
                        is_versioned=False,
                    )
                )

        # Sort versioned files by version (latest first)
        versioned_files_with_version: list[VersionInfo] = [
            v for v in versioned_files if v.version is not None
        ]

        # Filter by prerelease if configured
        if self._config is not None and not self._config.include_prerelease:
            release_files = [
                v
                for v in versioned_files_with_version
                if v.version and v.version.prerelease is None
            ]
            prerelease_files = [
                v
                for v in versioned_files_with_version
                if v.version and v.version.prerelease is not None
            ]
            release_files.sort(
                key=lambda v: v.version if v.version is not None else SemanticVersion(0, 0, 0),
                reverse=True,
            )
            prerelease_files.sort(
                key=lambda v: v.version if v.version is not None else SemanticVersion(0, 0, 0),
                reverse=True,
            )
            versioned_files = release_files + prerelease_files
        else:
            versioned_files_with_version.sort(
                key=lambda v: v.version if v.version is not None else SemanticVersion(0, 0, 0),
                reverse=True,
            )
            versioned_files = versioned_files_with_version

        result = versioned_files + unversioned_files
        self.cache.set(cache_key, result)

        log_version_operation(
            logger,
            "directory_scanned",
            path=directory,
            versioned_count=len(versioned_files),
            unversioned_count=len(unversioned_files),
        )

        return result

    def get_latest_version(self, versions: list[SemanticVersion]) -> Optional[SemanticVersion]:
        """
        Determine latest version from list using semantic versioning comparison.

        Args:
            versions: List of SemanticVersion instances

        Returns:
            Latest SemanticVersion, or None if list is empty
        """
        return get_latest_version(versions)

    def _matches_classifier(self, version_info: VersionInfo, classifier: dict[str, str]) -> bool:
        """
        Check if a version info matches the requested classifier filter.

        # AICODE-NOTE: Classifier matching rules:
        # 1. If file has the requested classifier value, it matches
        # 2. If file doesn't have classifier but default matches request, it matches
        # 3. If classifier not in request, use default from config

        Args:
            version_info: Version info to check
            classifier: Requested classifier filter

        Returns:
            True if version info matches classifier filter
        """
        if not classifier:
            return True

        for cls_name, cls_value in classifier.items():
            file_value = version_info.classifiers.get(cls_name)

            if file_value is not None:
                # File has this classifier
                if file_value != cls_value:
                    return False
            else:
                # File doesn't have this classifier explicitly
                # Check if this is a config-defined classifier with default
                if self._config and self._config.classifiers:
                    cls_config = self._config.classifiers.get(cls_name)
                    if cls_config:
                        # File implicitly has default value
                        if cls_config.default != cls_value:
                            return False

        return True

    def _get_available_classifier_values(
        self, versioned_files: list[VersionInfo], classifier_name: str
    ) -> list[str]:
        """Get list of available values for a classifier from versioned files."""
        values = set()
        for v in versioned_files:
            if classifier_name in v.classifiers:
                values.add(v.classifiers[classifier_name])

        # Add default if configured
        if self._config and self._config.classifiers:
            cls_config = self._config.classifiers.get(classifier_name)
            if cls_config:
                values.add(cls_config.default)

        return sorted(values)

    def resolve_version(
        self,
        path: str,
        version_spec: VersionSpec,
        classifier: dict[str, str] | None = None,
    ) -> str:
        """
        Resolve version from directory path and version specification.

        # AICODE-NOTE: This method implements version resolution logic:
        # - "latest" (or default): Resolve to latest versioned file
        # - Specific version (v1, v1.1, v1.1.1): Resolve to matching version
        # - Unversioned fallback: If no versioned files exist, use unversioned files
        # - Classifier filtering: Filter by classifier if specified
        # - Classifier fallback: For "latest", return latest version WITH classifier

        Args:
            path: Directory path containing versioned files
            version_spec: Version specification ("latest", "v1", "v1.1", "v1.1.1")
            classifier: Optional classifier filter (e.g., {"lang": "ru"})

        Returns:
            Resolved file path

        Raises:
            VersionNotFoundError: If requested version doesn't exist
            ClassifierNotFoundError: If requested classifier value doesn't exist
        """
        if isinstance(version_spec, dict):
            version_spec = "latest"

        scanned = self.scan_directory(path)
        if not scanned:
            raise VersionNotFoundError(
                path=path,
                version_spec=str(version_spec),
                available_versions=[],
                message=f"No files found in directory: {path}",
            )

        versioned = [v for v in scanned if v.is_versioned]
        unversioned = [v for v in scanned if not v.is_versioned]

        # Apply classifier filter if specified
        if classifier:
            classifier_matched = [v for v in versioned if self._matches_classifier(v, classifier)]

            if not classifier_matched:
                # No files match the classifier
                for cls_name, cls_value in classifier.items():
                    available = self._get_available_classifier_values(versioned, cls_name)
                    if cls_value not in available:
                        raise ClassifierNotFoundError(
                            classifier_name=cls_name,
                            requested_value=cls_value,
                            available_values=available,
                        )

                raise VersionNotFoundError(
                    path=path,
                    version_spec=str(version_spec),
                    available_versions=[str(v.version) for v in versioned],
                    message=f"No files match classifier {classifier}",
                )

            versioned = classifier_matched

            log_version_operation(
                logger,
                "classifier_matched",
                classifier=str(classifier),
                matched_count=len(versioned),
            )

        # Handle "latest" or default
        if version_spec == "latest" or version_spec is None:
            if versioned:
                if self._config is not None and not self._config.include_prerelease:
                    release_versions = [
                        v for v in versioned if v.version and v.version.prerelease is None
                    ]
                    if release_versions:
                        latest = release_versions[0]
                    elif versioned:
                        log_version_operation(
                            logger,
                            "prerelease_only_warning",
                            path=path,
                            message="Only prerelease versions found.",
                        )
                        latest = versioned[0]
                    else:
                        latest = None
                else:
                    latest = versioned[0]

                if latest:
                    log_version_operation(
                        logger,
                        "version_resolved",
                        version=str(latest.version),
                        path=latest.path,
                        classifier=str(latest.classifiers) if latest.classifiers else None,
                    )
                    return latest.path

            if unversioned:
                log_version_operation(
                    logger,
                    "version_resolved",
                    path=unversioned[0].path,
                )
                return unversioned[0].path
            else:
                raise VersionNotFoundError(
                    path=path,
                    version_spec=str(version_spec),
                    available_versions=[],
                )

        # Handle specific version
        try:
            requested_version = self.normalize_version(version_spec)
        except ValueError as e:
            raise VersionNotFoundError(
                path=path,
                version_spec=version_spec,
                available_versions=[str(v.version) for v in versioned],
                message=f"Invalid version specification: {version_spec}",
            ) from e

        # Find matching version
        for version_info in versioned:
            if version_info.version == requested_version:
                log_version_operation(
                    logger,
                    "version_resolved",
                    version=str(version_info.version),
                    path=version_info.path,
                )
                return version_info.path

        available_versions = [str(v.version) for v in versioned]
        raise VersionNotFoundError(
            path=path,
            version_spec=version_spec,
            available_versions=available_versions,
        )
