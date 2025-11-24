from __future__ import annotations

import json
import time
from collections import OrderedDict
from dataclasses import dataclass
from threading import RLock
from typing import Any, Callable, Dict, Mapping, MutableMapping, Optional, Sequence, Tuple

from promptic.adapters.registry import AdapterRegistry, BaseDataAdapter, BaseMemoryProvider
from promptic.blueprints.models import (
    BlueprintStep,
    ContextBlueprint,
    DataSlot,
    FallbackEvent,
    InstructionFallbackConfig,
    InstructionFallbackPolicy,
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
    PrompticError,
)
from promptic.instructions.store import InstructionResolver
from promptic.settings.base import ContextEngineSettings
from promptic.versioning import VersionSpec


@dataclass
class MaterializerStats:
    instruction_hits: int = 0
    instruction_misses: int = 0
    data_cache_hits: int = 0
    data_cache_misses: int = 0
    memory_cache_hits: int = 0
    memory_cache_misses: int = 0
    data_adapter_instances: int = 0
    memory_provider_instances: int = 0


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
        self._data_adapters: Dict[str, BaseDataAdapter] = {}
        self._memory_providers: Dict[str, BaseMemoryProvider] = {}
        self._instruction_cache_size = instruction_cache_size
        self._lock = RLock()
        self._stats = MaterializerStats()
        self._fallback_events: list[FallbackEvent] = []

    def resolve_instruction(
        self, instruction_id: str, version: Optional[VersionSpec] = None
    ) -> OperationResult[Tuple[InstructionNode, str]]:
        cache_key = f"{instruction_id}:{version}" if version else instruction_id
        with self._lock:
            cached = self._instruction_cache.get(cache_key)
            if cached:
                self._instruction_cache.move_to_end(cache_key)
                self._stats.instruction_hits += 1
                return OperationResult.success(cached)
        try:
            node, content = self._resolver.resolve(instruction_id, version=version)
        except InstructionNotFoundError as exc:
            return OperationResult.failure(exc)
        self._stats.instruction_misses += 1
        with self._lock:
            self._instruction_cache[cache_key] = (node, content)
            self._instruction_cache.move_to_end(cache_key)
            if len(self._instruction_cache) > self._instruction_cache_size:
                self._instruction_cache.popitem(last=False)
        return OperationResult.success((node, content))

    def resolve_instruction_refs(
        self, refs: Sequence[InstructionNodeRef]
    ) -> OperationResult[Sequence[Tuple[InstructionNode, str]]]:
        resolved: list[Tuple[InstructionNode, str]] = []
        aggregated_warnings: list[str] = []
        for ref in refs:
            result = self.resolve_instruction(ref.instruction_id, version=ref.version)
            aggregated_warnings.extend(result.warnings)
            if not result.ok:
                fallback_config = ref.fallback or InstructionFallbackConfig()
                fallback = self._apply_instruction_fallback(
                    ref=ref,
                    config=fallback_config,
                    error=result.error,
                )
                if fallback is None:
                    error = result.error or ContextMaterializationError(
                        f"Failed to resolve instruction '{ref.instruction_id}'."
                    )
                    return OperationResult.failure(error, warnings=aggregated_warnings)
                resolved.append(fallback)
                aggregated_warnings.append(
                    f"Applied instruction fallback '{fallback_config.mode.value}' "
                    f"for '{ref.instruction_id}'."
                )
                continue
            resolved.append(result.unwrap())
        return OperationResult.success(tuple(resolved), warnings=aggregated_warnings)

    def consume_fallback_events(self) -> list[FallbackEvent]:
        """Return and clear any recorded fallback events since the last call."""

        with self._lock:
            events = list(self._fallback_events)
            self._fallback_events.clear()
        return events

    def resolve_data_slots(
        self,
        blueprint: ContextBlueprint,
        *,
        overrides: Mapping[str, Any] | None = None,
    ) -> OperationResult[dict[str, Any]]:
        overrides = overrides or {}
        values: dict[str, Any] = {}
        warnings: list[str] = []
        for slot in blueprint.data_slots:
            resolved = self.resolve_data(blueprint, slot.name, overrides=overrides)
            warnings.extend(resolved.warnings)
            if not resolved.ok:
                error = resolved.error or ContextMaterializationError(
                    f"Failed to resolve data slot '{slot.name}'."
                )
                return OperationResult.failure(error, warnings=warnings)
            values[slot.name] = resolved.unwrap()
        return OperationResult.success(values, warnings=warnings)

    def resolve_memory_slots(
        self,
        blueprint: ContextBlueprint,
        *,
        overrides: Mapping[str, Any] | None = None,
    ) -> OperationResult[dict[str, Any]]:
        overrides = overrides or {}
        values: dict[str, Any] = {}
        warnings: list[str] = []
        for slot in blueprint.memory_slots:
            resolved = self.resolve_memory(blueprint, slot.name, overrides=overrides)
            warnings.extend(resolved.warnings)
            if not resolved.ok:
                error = resolved.error or ContextMaterializationError(
                    f"Failed to resolve memory slot '{slot.name}'."
                )
                return OperationResult.failure(error, warnings=warnings)
            values[slot.name] = resolved.unwrap()
        return OperationResult.success(values, warnings=warnings)

    def resolve_data(
        self,
        blueprint: ContextBlueprint,
        slot_name: str,
        *,
        overrides: Mapping[str, Any] | None = None,
    ) -> OperationResult[Any]:
        slot = blueprint.get_data_slot(slot_name)
        overrides = overrides or {}
        if slot.name in overrides:
            value = overrides[slot.name]
            self._set_cached_value(self._data_cache, slot.name, value, ttl=slot.ttl_seconds)
            return OperationResult.success(value)
        cached = self._get_cached_value(self._data_cache, slot.name)
        if cached is not _CACHE_MISS:
            self._stats.data_cache_hits += 1
            return OperationResult.success(cached)
        self._stats.data_cache_misses += 1
        try:
            config_override = self.settings.adapter_registry.data_defaults.get(slot.adapter_key)
            adapter = self._get_data_adapter(slot.adapter_key, config_override)
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
        overrides = overrides or {}
        if slot.name in overrides:
            value = overrides[slot.name]
            self._set_cached_value(self._memory_cache, slot.name, value)
            return OperationResult.success(value)
        cached = self._get_cached_value(self._memory_cache, slot.name)
        if cached is not _CACHE_MISS:
            self._stats.memory_cache_hits += 1
            return OperationResult.success(cached)
        self._stats.memory_cache_misses += 1
        try:
            config_override = self.settings.adapter_registry.memory_defaults.get(slot.provider_key)
            provider = self._get_memory_provider(slot.provider_key, config_override)
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
            self._data_adapters.clear()
            self._memory_providers.clear()

    def prefetch_instructions(self, blueprint: ContextBlueprint) -> OperationResult[int]:
        warmed = 0
        warnings: list[str] = []
        requirements = self._collect_instruction_requirements(blueprint)
        for (instruction_id, version), require_strict in requirements.items():
            result = self.resolve_instruction(instruction_id, version=version)
            warnings.extend(result.warnings)
            if not result.ok:
                if require_strict:
                    error = result.error or ContextMaterializationError(
                        f"Failed to preload instruction '{instruction_id}'."
                    )
                    return OperationResult.failure(error, warnings=warnings)
                warnings.append(
                    f"Prefetch skipped for optional instruction '{instruction_id}': "
                    f"{result.error or 'missing asset'}"
                )
                continue
            warmed += 1
        return OperationResult.success(warmed, warnings=warnings)

    def snapshot_stats(self) -> MaterializerStats:
        with self._lock:
            return MaterializerStats(**self._stats.__dict__)

    def reset_stats(self) -> None:
        with self._lock:
            self._stats = MaterializerStats()

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

    def _get_data_adapter(
        self,
        key: str,
        config: Mapping[str, Any] | Any,
    ) -> BaseDataAdapter:
        cache_key = self._make_cache_key(key, config)
        with self._lock:
            cached = self._data_adapters.get(cache_key)
            if cached:
                return cached
        adapter = self._registry.create_data_adapter(key, config=config)
        with self._lock:
            self._data_adapters[cache_key] = adapter
            self._stats.data_adapter_instances += 1
        return adapter

    def _get_memory_provider(
        self,
        key: str,
        config: Mapping[str, Any] | Any,
    ) -> BaseMemoryProvider:
        cache_key = self._make_cache_key(key, config)
        with self._lock:
            cached = self._memory_providers.get(cache_key)
            if cached:
                return cached
        provider = self._registry.create_memory_provider(key, config=config)
        with self._lock:
            self._memory_providers[cache_key] = provider
            self._stats.memory_provider_instances += 1
        return provider

    def _collect_instruction_requirements(
        self, blueprint: ContextBlueprint
    ) -> dict[Tuple[str, Optional[str]], bool]:
        requirements: dict[Tuple[str, Optional[str]], bool] = {}

        def _register(ref: InstructionNodeRef) -> None:
            fallback = ref.fallback or InstructionFallbackConfig()
            strict = fallback.mode == InstructionFallbackPolicy.ERROR
            key = (ref.instruction_id, ref.version)
            existing = requirements.get(key, False)
            requirements[key] = existing or strict

        for ref in blueprint.global_instructions:
            _register(ref)

        def _walk_steps(steps: Sequence[BlueprintStep]) -> None:
            for step in steps:
                for ref in step.instruction_refs:
                    _register(ref)
                _walk_steps(step.children)

        _walk_steps(blueprint.steps)
        return requirements

    @staticmethod
    def _make_cache_key(key: str, config: Mapping[str, Any] | Any) -> str:
        return f"{key}:{ContextMaterializer._fingerprint_config(config)}"

    @staticmethod
    def _fingerprint_config(config: Mapping[str, Any] | Any) -> str:
        if config is None:
            return "default"
        if hasattr(config, "model_dump"):
            payload = config.model_dump()
        elif isinstance(config, Mapping):
            payload = dict(config)
        else:
            return repr(config)
        try:
            return json.dumps(payload, sort_keys=True, default=str)
        except TypeError:
            return repr(payload)

    def _apply_instruction_fallback(
        self,
        *,
        ref: InstructionNodeRef,
        config: InstructionFallbackConfig,
        error: PrompticError | None,
    ) -> Tuple[InstructionNode, str] | None:
        if config.mode == InstructionFallbackPolicy.ERROR:
            return None
        placeholder = config.placeholder or self._default_placeholder(
            instruction_id=ref.instruction_id,
            mode=config.mode,
        )
        inserted_text = "" if config.mode == InstructionFallbackPolicy.NOOP else placeholder
        reported_placeholder = (
            placeholder if config.mode != InstructionFallbackPolicy.NOOP else config.placeholder
        )
        message = (
            f"{config.mode.value} fallback applied for '{ref.instruction_id}': "
            f"{error or 'instruction unavailable'}"
        )
        # AICODE-NOTE: Recording fallback events keeps SDK responses and pipeline logs aligned.
        event = FallbackEvent(
            instruction_id=ref.instruction_id,
            mode=config.mode,
            message=message,
            placeholder_used=reported_placeholder or None,
            log_key=config.log_key or ref.instruction_id,
        )
        self._record_fallback_event(event)
        return self._make_placeholder_node(ref.instruction_id), inserted_text

    def _record_fallback_event(self, event: FallbackEvent) -> None:
        with self._lock:
            self._fallback_events.append(event)

    @staticmethod
    def _default_placeholder(*, instruction_id: str, mode: InstructionFallbackPolicy) -> str:
        if mode == InstructionFallbackPolicy.NOOP:
            return ""
        return f"[instruction {instruction_id} unavailable]"

    @staticmethod
    def _make_placeholder_node(instruction_id: str) -> InstructionNode:
        return InstructionNode(
            instruction_id=instruction_id,
            source_uri=f"fallback://{instruction_id}",
            format="md",
            checksum=_FALLBACK_CHECKSUM,
            locale="und",
            version="fallback",
            provider_key="fallback",
        )


__all__ = ["ContextMaterializer", "MaterializerStats"]


_FALLBACK_CHECKSUM = "0" * 32
_CACHE_MISS = object()
