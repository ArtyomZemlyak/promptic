from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from promptic.blueprints.models import ContextBlueprint, InstructionNode, MemoryChannel
from promptic.context.errors import InstructionNotFoundError
from promptic.versioning import VersionedFileScanner, VersionSpec

KNOWN_SUFFIXES: Dict[str, str] = {
    ".md": "md",
    ".markdown": "md",
    ".txt": "txt",
    ".jinja": "jinja",
}


class InstructionStore(ABC):
    """Abstract storage engine for instruction assets."""

    @abstractmethod
    def list_ids(self) -> Sequence[str]:
        """Return all known instruction identifiers."""

    @abstractmethod
    def get_node(
        self, instruction_id: str, version: Optional[VersionSpec] = None
    ) -> InstructionNode:
        """Return metadata for an instruction without loading contents.

        Args:
            instruction_id: Instruction identifier
            version: Optional version specification for version-aware resolution
        """

    @abstractmethod
    def load_content(self, instruction_id: str, version: Optional[VersionSpec] = None) -> str:
        """Return the decoded instruction text.

        Args:
            instruction_id: Instruction identifier
            version: Optional version specification for version-aware resolution
        """

    def exists(self, instruction_id: str) -> bool:
        try:
            self.get_node(instruction_id)
        except InstructionNotFoundError:
            return False
        return True

    def resolve_path(self, instruction_id: str, version: Optional[VersionSpec] = None) -> Path:
        """Return the absolute path for an instruction if available.

        Args:
            instruction_id: Instruction identifier
            version: Optional version specification for version-aware resolution
        """

        raise NotImplementedError("resolve_path is not supported by this store.")

    def read_raw(self, relative_path: str) -> str:
        """Read arbitrary files relative to the instruction root (e.g., memory descriptors)."""

        raise NotImplementedError("read_raw is not supported by this store.")

    def path_exists(self, relative_path: str) -> bool:
        """Check if a relative path exists under the instruction root."""

        raise NotImplementedError("path_exists is not supported by this store.")


class InstructionResolver:
    """Convenience wrapper that returns both metadata and file contents."""

    def __init__(self, store: InstructionStore) -> None:
        self._store = store

    def resolve(
        self, instruction_id: str, version: Optional[VersionSpec] = None
    ) -> Tuple[InstructionNode, str]:
        node = self._store.get_node(instruction_id, version=version)
        content = self._store.load_content(instruction_id, version=version)
        return node, content


class FilesystemInstructionStore(InstructionStore):
    """
    File-based instruction implementation with light validation.

    # AICODE-NOTE: Files are resolved relative to `root` and we explicitly reject
    #              attempts to traverse parent directories to keep previews safe.
    Supports version-aware file discovery when version parameter is provided.
    """

    def __init__(
        self,
        root: Path | str,
        *,
        default_locale: str = "en-US",
        version: Optional[VersionSpec] = None,
    ) -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.default_locale = default_locale
        self.version = version
        self.version_scanner = VersionedFileScanner() if version is not None else None

    def list_ids(self) -> Sequence[str]:
        ids: List[str] = []
        for path in self.root.rglob("*"):
            if path.is_file() and path.suffix in KNOWN_SUFFIXES:
                relative = path.relative_to(self.root).with_suffix("")
                ids.append(relative.as_posix())
        ids.sort()
        return ids

    def get_node(
        self, instruction_id: str, version: Optional[VersionSpec] = None
    ) -> InstructionNode:
        """Return metadata for an instruction without loading contents.

        # AICODE-NOTE: Version-aware file discovery: If version is provided (either via
        constructor or method parameter), the store uses VersionedFileScanner to resolve
        versioned files. The method parameter takes precedence over the constructor parameter.

        Args:
            instruction_id: Instruction identifier (relative path)
            version: Optional version specification (overrides constructor version if provided)

        Returns:
            InstructionNode with metadata
        """
        effective_version = version if version is not None else self.version
        path = self._ensure_path(instruction_id, effective_version)
        content = path.read_text(encoding="utf-8")
        checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()
        file_version = str(path.stat().st_mtime_ns)
        format_name = KNOWN_SUFFIXES[path.suffix]
        return InstructionNode(
            instruction_id=instruction_id,
            source_uri=str(path),
            format=format_name,
            checksum=checksum,
            locale=self.default_locale,
            version=file_version,
        )

    def load_content(self, instruction_id: str, version: Optional[VersionSpec] = None) -> str:
        """Return the decoded instruction text.

        # AICODE-NOTE: Version-aware file discovery: If version is provided, the store
        uses VersionedFileScanner to resolve versioned files before loading content.

        Args:
            instruction_id: Instruction identifier (relative path)
            version: Optional version specification (overrides constructor version if provided)

        Returns:
            Instruction content as string
        """
        effective_version = version if version is not None else self.version
        path = self._ensure_path(instruction_id, effective_version)
        return path.read_text(encoding="utf-8")

    def resolve_path(self, instruction_id: str, version: Optional[VersionSpec] = None) -> Path:
        """Return the absolute path for an instruction if available.

        # AICODE-NOTE: Version-aware file discovery: If version is provided, the store
        uses VersionedFileScanner to resolve versioned files before returning path.

        Args:
            instruction_id: Instruction identifier (relative path)
            version: Optional version specification (overrides constructor version if provided)

        Returns:
            Absolute Path to instruction file
        """
        effective_version = version if version is not None else self.version
        return self._ensure_path(instruction_id, effective_version)

    def read_raw(self, relative_path: str) -> str:
        path = self._resolve_relative(relative_path)
        return path.read_text(encoding="utf-8")

    def path_exists(self, relative_path: str) -> bool:
        try:
            self._resolve_relative(relative_path)
        except FileNotFoundError:
            return False
        return True

    def _ensure_path(self, instruction_id: str, version: Optional[VersionSpec] = None) -> Path:
        """Ensure path exists and return it, with optional version resolution.

        # AICODE-NOTE: Version-aware path resolution: If version is provided and the
        candidate path is a directory, use VersionedFileScanner to resolve the versioned
        file. This enables loading instructions from versioned directories.

        Args:
            instruction_id: Instruction identifier (relative path)
            version: Optional version specification for version-aware resolution

        Returns:
            Resolved Path to instruction file

        Raises:
            InstructionNotFoundError: If instruction cannot be found
        """
        sanitized = self._sanitize_identifier(instruction_id)
        candidate = self.root / sanitized

        # If candidate is a directory and version is provided, use version scanner
        if version is not None and candidate.is_dir():
            if self.version_scanner is None:
                self.version_scanner = VersionedFileScanner()
            try:
                resolved_file = self.version_scanner.resolve_version(str(candidate), version)
                return Path(resolved_file)
            except Exception:
                # If version resolution fails, fall back to normal resolution
                pass

        # Normal file resolution (existing logic)
        if candidate.is_file() and candidate.suffix in KNOWN_SUFFIXES:
            return candidate
        if candidate.suffix:
            raise InstructionNotFoundError(instruction_id)
        for suffix in KNOWN_SUFFIXES:
            with_suffix = candidate.with_suffix(suffix)
            if with_suffix.is_file():
                return with_suffix
        raise InstructionNotFoundError(instruction_id)

    def _sanitize_identifier(self, instruction_id: str) -> Path:
        relative = Path(instruction_id)
        if relative.is_absolute():
            raise InstructionNotFoundError(instruction_id)
        if any(part == ".." for part in relative.parts):
            raise InstructionNotFoundError(instruction_id)
        return relative

    def _resolve_relative(self, relative_path: str) -> Path:
        relative = self._sanitize_identifier(relative_path)
        candidate = (self.root / relative).resolve()
        if candidate.exists():
            return candidate
        raise FileNotFoundError(relative_path)


class MemoryDescriptorCollector:
    """Scans instruction roots and metadata for memory/log descriptors."""

    def __init__(self, *, instruction_root: Path | str) -> None:
        self._instruction_root = Path(instruction_root).expanduser().resolve()

    def collect(self, blueprint: ContextBlueprint) -> list[MemoryChannel]:
        config = self._file_first_config(blueprint)
        channels = self._channels_from_metadata(config)
        if channels:
            return channels
        default_descriptor = self._instruction_root / "memory" / "format.md"
        if default_descriptor.exists():
            return [
                MemoryChannel(
                    location="memory/",
                    expected_format="Hierarchical markdown log (default template)",
                    format_descriptor_path="memory/format.md",
                    retention_policy="Rotate with project milestones.",
                    usage_examples=[],
                )
            ]
        return []

    def _channels_from_metadata(self, config: Dict[str, Any]) -> list[MemoryChannel]:
        raw_channels = config.get("memory_channels")
        if not isinstance(raw_channels, list):
            return []
        channels: list[MemoryChannel] = []
        for entry in raw_channels:
            if not isinstance(entry, dict):
                continue
            descriptor = entry.get("format_descriptor_path")
            if descriptor and not self._descriptor_exists(descriptor):
                descriptor = None
            raw_usage = entry.get("usage_examples")
            usage_examples = (
                [str(item) for item in raw_usage] if isinstance(raw_usage, list) else []
            )
            channels.append(
                MemoryChannel(
                    location=str(entry.get("location", "memory/")),
                    expected_format=str(entry.get("expected_format", "User-defined format")),
                    format_descriptor_path=descriptor,
                    retention_policy=entry.get("retention_policy"),
                    usage_examples=usage_examples,
                )
            )
        return channels

    def _descriptor_exists(self, descriptor: str) -> bool:
        candidate = (self._instruction_root / descriptor).resolve()
        return candidate.exists()

    @staticmethod
    def _file_first_config(blueprint: ContextBlueprint) -> Dict[str, Any]:
        metadata = blueprint.metadata or {}
        file_first = metadata.get("file_first", {})
        return dict(file_first) if isinstance(file_first, dict) else {}


__all__ = [
    "FilesystemInstructionStore",
    "InstructionResolver",
    "InstructionStore",
    "MemoryDescriptorCollector",
]
