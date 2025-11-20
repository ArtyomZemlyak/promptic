from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from typing import Sequence

from promptic.blueprints.models import InstructionNode
from promptic.instructions.store import InstructionStore


class InstructionCache(InstructionStore):
    """
    InstructionStore wrapper that caches metadata/content using LRU eviction.

    # AICODE-NOTE: Filesystem lookups dominate preview latency on large projects.
    #              LRU caches keep hot instructions in memory without unbounded
    #              growth, while still falling back to the underlying store.
    """

    def __init__(self, store: InstructionStore, *, max_entries: int = 256) -> None:
        self._store = store
        self._max_entries = max_entries
        self._node_cache: OrderedDict[str, InstructionNode] = OrderedDict()
        self._content_cache: OrderedDict[str, str] = OrderedDict()
        self._index: Sequence[str] | None = None

    def list_ids(self) -> Sequence[str]:
        if self._index is None:
            self._index = tuple(self._store.list_ids())
        return self._index

    def get_node(self, instruction_id: str) -> InstructionNode:
        cached = self._node_cache.get(instruction_id)
        if cached:
            self._node_cache.move_to_end(instruction_id)
            return cached
        node = self._store.get_node(instruction_id)
        self._remember_node(instruction_id, node)
        return node

    def load_content(self, instruction_id: str) -> str:
        cached = self._content_cache.get(instruction_id)
        if cached is not None:
            self._content_cache.move_to_end(instruction_id)
            return cached
        content = self._store.load_content(instruction_id)
        self._remember_content(instruction_id, content)
        return content

    def resolve_path(self, instruction_id: str) -> Path:
        return self._store.resolve_path(instruction_id)

    def read_raw(self, relative_path: str) -> str:
        return self._store.read_raw(relative_path)

    def path_exists(self, relative_path: str) -> bool:
        return self._store.path_exists(relative_path)

    def invalidate(self, instruction_id: str | None = None) -> None:
        """Purge one or all cached entries."""

        if instruction_id is None:
            self._node_cache.clear()
            self._content_cache.clear()
            self._index = None
            return
        self._node_cache.pop(instruction_id, None)
        self._content_cache.pop(instruction_id, None)

    def refresh_index(self) -> Sequence[str]:
        """Force a re-scan of underlying stores."""

        self._index = tuple(self._store.list_ids())
        return self._index

    def _remember_node(self, instruction_id: str, node: InstructionNode) -> None:
        self._node_cache[instruction_id] = node
        self._node_cache.move_to_end(instruction_id)
        if len(self._node_cache) > self._max_entries:
            self._node_cache.popitem(last=False)

    def _remember_content(self, instruction_id: str, content: str) -> None:
        self._content_cache[instruction_id] = content
        self._content_cache.move_to_end(instruction_id)
        if len(self._content_cache) > self._max_entries:
            self._content_cache.popitem(last=False)


__all__ = ["InstructionCache"]
