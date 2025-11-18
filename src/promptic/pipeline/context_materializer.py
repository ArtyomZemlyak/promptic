from __future__ import annotations

from collections import OrderedDict
from threading import RLock
from typing import Any, Dict, Mapping, MutableMapping, Sequence, Tuple

from promptic.adapters.registry import AdapterRegistry
from promptic.blueprints.models import (
    ContextBlueprint,
    DataSlot,
    InstructionNode,
    InstructionNodeRef,
    MemorySlot,
)
from promptic.context.errors import (
    AdapterExecutionError,
    AdapterNotRegisteredError,
    ContextMaterializationError,
    InstructionNotFoundError,
    OperationResult,
)
from promptic.instructions.store import InstructionResolver
from promptic.settings.base import ContextEngineSettings


class ContextMaterializer:
    """
    Resolves instructions, data slots, and memory slots for preview/execution flows.

    # AICODE-NOTE: This layer centralizes adapter lookups so preview/executor
    #              pipelines do not couple directly to registry plumbing.
    """

    def __init__(
        self,
        *,
        settings: ContextEngineSettings,
        instruction_resolver: InstructionResolver,
        adapter_registry: AdapterRegistry,
        instruction_cache_size: int = 64,
    ) -> None:
        self.settings = settings
        self._resolver = instruction_resolver
        self._registry = adapter_registry
        self._instruction_cache: "OrderedDict[str, Tuple[InstructionNode, str]]" = OrderedDict()
        self._data_cache: Dict[str, Any] = {}
        self._memory_cache: Dict[str, Any] = {}
        self._instruction_cache_size = instruction_cache_size
        self._lock = RLock()

    def resolve_instruction(
        self, instruction_id: str
    ) -> OperationResult[Tuple[InstructionNode, str]]:
        with self._lock:
            cached = self._instruction_cache.get(instruction_id)
            if cached:
                self._instruction_cache.move_to_end(instruction_id)
                return OperationResult.success(cached)
        try:
            node, content = self._resolver.resolve(instruction_id)
        except InstructionNotFoundError as exc:
            return OperationResult.failure(exc)
        with self._lock:
            self._instruction_cache[instruction_id] = (node, content)
            self._instruction_cache.move_to_end(instruction_id)
            if len(self._instruction_cache) > self._instruction_cache_size:
                self._instruction_cache.popitem(last=False)
        return OperationResult.success((node, content))

    def resolve_instruction_refs(
        self, refs: Sequence[InstructionNodeRef]
    ) -> OperationResult[Sequence[Tuple[InstructionNode, str]]]:
        resolved: list[Tuple[InstructionNode, str]] = []
        aggregated_warnings: list[str] = []
        for ref in refs:
            result = self.resolve_instruction(ref.instruction_id)
            aggregated_warnings.extend(result.warnings)
            if not result.ok:
                error = result.error or ContextMaterializationError(
                    f"Failed to resolve instruction '{ref.instruction_id}'."
                )
                return OperationResult.failure(error, warnings=aggregated_warnings)
            resolved.append(result.unwrap())
        return OperationResult.success(tuple(resolved), warnings=aggregated_warnings)

    def resolve_data(
        self,
        blueprint: ContextBlueprint,
        slot_name: str,
        *,
        overrides: Mapping[str, Any] | None = None,
    ) -> OperationResult[Any]:
        slot = blueprint.get_data_slot(slot_name)
        if overrides and slot.name in overrides:
            value = overrides[slot.name]
            self._data_cache[slot.name] = value
            return OperationResult.success(value)
        if slot.name in self._data_cache:
            return OperationResult.success(self._data_cache[slot.name])
        try:
            adapter = self._registry.create_data_adapter(slot.adapter_key)
        except AdapterNotRegisteredError as exc:
            return OperationResult.failure(exc)
        try:
            value = adapter.fetch(slot)
        except Exception as exc:  # pragma: no cover - adapter specific
            return OperationResult.failure(AdapterExecutionError(str(exc)))
        self._data_cache[slot.name] = value
        return OperationResult.success(value)

    def resolve_memory(
        self,
        blueprint: ContextBlueprint,
        slot_name: str,
        *,
        overrides: Mapping[str, Any] | None = None,
    ) -> OperationResult[Any]:
        slot = blueprint.get_memory_slot(slot_name)
        if overrides and slot.name in overrides:
            value = overrides[slot.name]
            self._memory_cache[slot.name] = value
            return OperationResult.success(value)
        if slot.name in self._memory_cache:
            return OperationResult.success(self._memory_cache[slot.name])
        try:
            provider = self._registry.create_memory_provider(slot.provider_key)
        except AdapterNotRegisteredError as exc:
            return OperationResult.failure(exc)
        try:
            value = provider.load(slot)
        except Exception as exc:  # pragma: no cover - adapter specific
            return OperationResult.failure(AdapterExecutionError(str(exc)))
        self._memory_cache[slot.name] = value
        return OperationResult.success(value)

    def reset_caches(self) -> None:
        with self._lock:
            self._data_cache.clear()
            self._memory_cache.clear()
            self._instruction_cache.clear()


__all__ = ["ContextMaterializer"]
