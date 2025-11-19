from __future__ import annotations

import time
from collections import OrderedDict
from threading import RLock
from typing import Any, Callable, Dict, Mapping, MutableMapping, Sequence, Tuple

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
    AdapterRetryError,
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
        self._data_cache: Dict[str, Tuple[Any, float | None]] = {}
        self._memory_cache: Dict[str, Tuple[Any, float | None]] = {}
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
            self._set_cached_value(self._data_cache, slot.name, value, ttl=slot.ttl_seconds)
            return OperationResult.success(value)
        cached = self._get_cached_value(self._data_cache, slot.name)
        if cached is not _CACHE_MISS:
            return OperationResult.success(cached)
        try:
            config_override = self.settings.adapter_registry.data_defaults.get(slot.adapter_key)
            adapter = self._registry.create_data_adapter(
                slot.adapter_key,
                config=config_override,
            )
        except AdapterNotRegisteredError as exc:
            return OperationResult.failure(exc)
        fetch_result = self._call_with_retries(lambda: adapter.fetch(slot), slot.adapter_key)
        if not fetch_result.ok:
            return fetch_result
        value = fetch_result.unwrap()
        self._set_cached_value(self._data_cache, slot.name, value, ttl=slot.ttl_seconds)
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
            self._set_cached_value(self._memory_cache, slot.name, value)
            return OperationResult.success(value)
        cached = self._get_cached_value(self._memory_cache, slot.name)
        if cached is not _CACHE_MISS:
            return OperationResult.success(cached)
        try:
            config_override = self.settings.adapter_registry.memory_defaults.get(slot.provider_key)
            provider = self._registry.create_memory_provider(
                slot.provider_key, config=config_override
            )
        except AdapterNotRegisteredError as exc:
            return OperationResult.failure(exc)
        load_result = self._call_with_retries(lambda: provider.load(slot), slot.provider_key)
        if not load_result.ok:
            return load_result
        value = load_result.unwrap()
        self._set_cached_value(self._memory_cache, slot.name, value)
        return OperationResult.success(value)

    def reset_caches(self) -> None:
        with self._lock:
            self._data_cache.clear()
            self._memory_cache.clear()
            self._instruction_cache.clear()

    def _call_with_retries(
        self,
        func: Callable[[], Any],
        adapter_key: str,
    ) -> OperationResult[Any]:
        attempts = max(1, self.settings.adapter_registry.max_retries + 1)
        last_error: AdapterExecutionError | None = None
        for attempt in range(1, attempts + 1):
            try:
                return OperationResult.success(func())
            except AdapterExecutionError as exc:
                last_error = exc
            except Exception as exc:  # pragma: no cover - adapter specific
                last_error = AdapterExecutionError(str(exc))
            if attempt < attempts:
                continue
        return OperationResult.failure(
            AdapterRetryError(adapter_key, attempts, last_error or AdapterExecutionError("failure"))
        )

    def _get_cached_value(
        self,
        cache: MutableMapping[str, Tuple[Any, float | None]],
        key: str,
    ) -> Any:
        entry = cache.get(key)
        if not entry:
            return _CACHE_MISS
        value, expires_at = entry
        if expires_at and expires_at < time.time():
            cache.pop(key, None)
            return _CACHE_MISS
        return value

    def _set_cached_value(
        self,
        cache: MutableMapping[str, Tuple[Any, float | None]],
        key: str,
        value: Any,
        *,
        ttl: int | None = None,
    ) -> None:
        expires_at = time.time() + ttl if ttl else None
        cache[key] = (value, expires_at)


__all__ = ["ContextMaterializer"]


_CACHE_MISS = object()
