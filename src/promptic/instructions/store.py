from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from promptic.blueprints.models import InstructionNode
from promptic.context.errors import InstructionNotFoundError

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
    def get_node(self, instruction_id: str) -> InstructionNode:
        """Return metadata for an instruction without loading contents."""

    @abstractmethod
    def load_content(self, instruction_id: str) -> str:
        """Return the decoded instruction text."""

    def exists(self, instruction_id: str) -> bool:
        try:
            self.get_node(instruction_id)
        except InstructionNotFoundError:
            return False
        return True


class InstructionResolver:
    """Convenience wrapper that returns both metadata and file contents."""

    def __init__(self, store: InstructionStore) -> None:
        self._store = store

    def resolve(self, instruction_id: str) -> Tuple[InstructionNode, str]:
        node = self._store.get_node(instruction_id)
        content = self._store.load_content(instruction_id)
        return node, content


class FilesystemInstructionStore(InstructionStore):
    """
    File-based instruction implementation with light validation.

    # AICODE-NOTE: Files are resolved relative to `root` and we explicitly reject
    #              attempts to traverse parent directories to keep previews safe.
    """

    def __init__(self, root: Path | str, *, default_locale: str = "en-US") -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.default_locale = default_locale

    def list_ids(self) -> Sequence[str]:
        ids: List[str] = []
        for path in self.root.rglob("*"):
            if path.is_file() and path.suffix in KNOWN_SUFFIXES:
                relative = path.relative_to(self.root).with_suffix("")
                ids.append(relative.as_posix())
        ids.sort()
        return ids

    def get_node(self, instruction_id: str) -> InstructionNode:
        path = self._ensure_path(instruction_id)
        content = path.read_text(encoding="utf-8")
        checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()
        version = str(path.stat().st_mtime_ns)
        format_name = KNOWN_SUFFIXES[path.suffix]
        return InstructionNode(
            instruction_id=instruction_id,
            source_uri=str(path),
            format=format_name,
            checksum=checksum,
            locale=self.default_locale,
            version=version,
        )

    def load_content(self, instruction_id: str) -> str:
        path = self._ensure_path(instruction_id)
        return path.read_text(encoding="utf-8")

    def _ensure_path(self, instruction_id: str) -> Path:
        sanitized = self._sanitize_identifier(instruction_id)
        candidate = self.root / sanitized
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


__all__ = [
    "FilesystemInstructionStore",
    "InstructionResolver",
    "InstructionStore",
]
