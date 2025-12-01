"""Utilities for resolving prompt paths with version-aware semantics."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from promptic.versioning.adapters.scanner import VersionedFileScanner, VersionInfo
from promptic.versioning.domain.errors import VersionNotFoundError
from promptic.versioning.domain.resolver import VersionSpec

try:  # pragma: no cover - optional typing dependency
    from promptic.versioning.config import VersioningConfig
except Exception:  # pragma: no cover
    VersioningConfig = None  # type: ignore


class PromptPathResolver:
    """Resolve prompt entry paths that may omit version, extension, or point to directories."""

    SUPPORTED_EXTENSIONS = (".md", ".markdown", ".yaml", ".yml", ".json", ".jinja2", ".jinja")

    def __init__(self, *, versioning_config: "VersioningConfig | None" = None) -> None:
        self._config = versioning_config
        self._scanner = VersionedFileScanner(config=versioning_config)

    def resolve(
        self,
        raw_path: str | Path,
        *,
        base_dir: Path | None = None,
        version_spec: VersionSpec | None = None,
        classifier: dict[str, str] | None = None,
        default_version: VersionSpec = "latest",
    ) -> Path:
        """
        Resolve a prompt path into a concrete file on disk.

        Supports the following forms:
        - Direct file paths (with or without explicit version suffix)
        - File paths without version suffix (resolved via version scanner)
        - File hints without extension (tries all supported extensions)
        - Directory paths containing versioned prompt files

        Args:
            raw_path: User-provided path or hint.
            base_dir: Base directory for relative paths (defaults to cwd).
            version_spec: Optional version spec to honor (falls back to default_version).
            classifier: Optional classifier constraint propagated to version resolution.
            default_version: Version to use when version_spec is None (defaults to "latest").

        Returns:
            Absolute Path to the resolved prompt file.

        Raises:
            FileNotFoundError: If no matching file/directory exists.
            VersionNotFoundError: If requested version does not exist for the hint.
        """
        path_obj = Path(raw_path)
        anchor_dir = self._normalize_base_dir(base_dir, path_obj)
        relative_hint = path_obj.parts if not path_obj.is_absolute() else None
        candidate = self._make_absolute(path_obj, anchor_dir)

        if candidate.exists():
            if candidate.is_file():
                return candidate
            if candidate.is_dir():
                return self._resolve_from_directory(
                    candidate,
                    version_spec,
                    default_version,
                    classifier,
                )

        return self._resolve_from_parent(
            candidate,
            anchor_dir,
            relative_hint,
            version_spec,
            default_version,
            classifier,
        )

    def _normalize_base_dir(self, base_dir: Path | None, path_obj: Path) -> Path:
        if path_obj.is_absolute():
            return Path("/")
        if base_dir is None:
            return Path.cwd()
        return base_dir.parent if base_dir.is_file() else base_dir

    def _make_absolute(self, path_obj: Path, anchor_dir: Path) -> Path:
        if path_obj.is_absolute():
            return path_obj.resolve()
        return (anchor_dir / path_obj).resolve()

    def _resolve_from_directory(
        self,
        directory: Path,
        version_spec: VersionSpec | None,
        default_version: VersionSpec,
        classifier: dict[str, str] | None,
    ) -> Path:
        effective_version = self._effective_version(version_spec, default_version)
        if isinstance(effective_version, dict):
            # Hierarchical specs are not supported at this stage, default to latest.
            effective_version = "latest"

        resolved = self._scanner.resolve_version(
            str(directory),
            effective_version,
            classifier=classifier,
        )
        return Path(resolved)

    def _resolve_from_parent(
        self,
        candidate: Path,
        anchor_dir: Path,
        relative_hint: Sequence[str] | None,
        version_spec: VersionSpec | None,
        default_version: VersionSpec,
        classifier: dict[str, str] | None,
    ) -> Path:
        parent_dir = candidate.parent
        if not parent_dir.exists():
            parent_dir = self._find_alternate_parent(anchor_dir, relative_hint)
            if parent_dir is None:
                raise FileNotFoundError(f"Prompt path not found: {candidate}")

        targets = self._target_names(candidate)
        scanned = self._scanner.scan_directory(str(parent_dir))

        matching_versioned: list[VersionInfo] = []
        matching_unversioned: list[VersionInfo] = []

        for info in scanned:
            if info.base_name not in targets:
                continue
            if classifier and not self._matches_classifier(info, classifier):
                continue

            if info.is_versioned and info.version is not None:
                matching_versioned.append(info)
            else:
                matching_unversioned.append(info)

        return self._select_match(
            matching_versioned,
            matching_unversioned,
            candidate,
            version_spec,
            default_version,
        )

    def _target_names(self, candidate: Path) -> set[str]:
        if candidate.suffix:
            return {candidate.name}

        targets = {candidate.name}
        for ext in self.SUPPORTED_EXTENSIONS:
            targets.add(f"{candidate.name}{ext}")
        return targets

    def _select_match(
        self,
        versioned: list[VersionInfo],
        unversioned: list[VersionInfo],
        candidate: Path,
        version_spec: VersionSpec | None,
        default_version: VersionSpec,
    ) -> Path:
        effective_version = self._effective_version(version_spec, default_version)

        if effective_version in (None, "latest"):
            if versioned:
                return Path(versioned[0].path)
            if unversioned:
                return Path(unversioned[0].path)
            raise FileNotFoundError(f"No prompt found for: {candidate}")

        if not isinstance(effective_version, str):
            # Hierarchical version specs are not supported per-file; use latest.
            if versioned:
                return Path(versioned[0].path)
            if unversioned:
                return Path(unversioned[0].path)
            raise FileNotFoundError(f"No prompt found for: {candidate}")

        normalized = self._scanner.normalize_version(effective_version)
        for info in versioned:
            if info.version == normalized:
                return Path(info.path)

        available_versions = [str(info.version) for info in versioned]
        raise VersionNotFoundError(
            path=str(candidate),
            version_spec=effective_version,
            available_versions=available_versions,
        )

    def _matches_classifier(self, info: VersionInfo, classifier: dict[str, str]) -> bool:
        if not classifier:
            return True

        for cls_name, cls_value in classifier.items():
            file_value = info.classifiers.get(cls_name)
            if file_value is not None:
                if file_value != cls_value:
                    return False
            else:
                if self._config and self._config.classifiers:
                    cls_config = self._config.classifiers.get(cls_name)
                    if cls_config and cls_config.default != cls_value:
                        return False

        return True

    def _effective_version(
        self,
        version_spec: VersionSpec | None,
        default_version: VersionSpec,
    ) -> VersionSpec | None:
        if isinstance(version_spec, str):
            return version_spec
        if version_spec is None:
            return default_version
        return version_spec

    def _find_alternate_parent(
        self,
        anchor_dir: Path,
        relative_hint: Sequence[str] | None,
    ) -> Path | None:
        if not relative_hint:
            return None

        head, *tail = relative_hint
        if head in ("", ".", ".."):
            return None

        current = anchor_dir
        for _ in range(5):
            potential = current / head
            if potential.exists() and potential.is_dir():
                result = potential
                for part in tail[:-1]:
                    if part in ("", ".", ".."):
                        continue
                    result = result / part
                if result.exists() and result.is_dir():
                    return result
            if current.parent == current:
                break
            current = current.parent

        return None
