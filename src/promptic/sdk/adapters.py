from __future__ import annotations

from typing import Iterable, Mapping, Optional

from pydantic_settings import BaseSettings

from promptic.adapters.data import (
    CSVAdapterSettings,
    CSVDataAdapter,
    HttpAdapterSettings,
    HttpJSONAdapter,
)
from promptic.adapters.memory import (
    StaticMemoryProvider,
    StaticMemorySettings,
    VectorMemoryProvider,
    VectorMemorySettings,
)
from promptic.adapters.registry import (
    AdapterFactory,
    AdapterRegistration,
    AdapterRegistry,
    BaseDataAdapter,
    BaseMemoryProvider,
)

RegistryLike = Optional[AdapterRegistry]

_DEFAULT_REGISTRY: AdapterRegistry | None = None


def register_data_adapter(
    *,
    key: str,
    adapter: type[BaseDataAdapter] | AdapterFactory[BaseDataAdapter],
    registry: RegistryLike = None,
    config_model: type[BaseSettings] | None = None,
    entry_point: str | None = None,
    capabilities: Iterable[str] | None = None,
) -> AdapterRegistration:
    target = _resolve_registry(registry)
    return target.register_data(
        key,
        adapter,
        config_model=config_model,
        entry_point=entry_point,
        capabilities=capabilities,
    )


def register_memory_provider(
    *,
    key: str,
    provider: type[BaseMemoryProvider],
    registry: RegistryLike = None,
    config_model: type[BaseSettings] | None = None,
    entry_point: str | None = None,
    capabilities: Iterable[str] | None = None,
) -> AdapterRegistration:
    target = _resolve_registry(registry)
    return target.register_memory(
        key,
        provider,
        config_model=config_model,
        entry_point=entry_point,
        capabilities=capabilities,
    )


def register_csv_loader(*, key: str, registry: RegistryLike = None) -> AdapterRegistration:
    return register_data_adapter(
        key=key,
        adapter=CSVDataAdapter,
        registry=registry,
        config_model=CSVAdapterSettings,
        capabilities={"filesystem"},
    )


def register_http_loader(*, key: str, registry: RegistryLike = None) -> AdapterRegistration:
    return register_data_adapter(
        key=key,
        adapter=HttpJSONAdapter,
        registry=registry,
        config_model=HttpAdapterSettings,
        capabilities={"http"},
    )


def register_static_memory_provider(
    *, key: str, registry: RegistryLike = None
) -> AdapterRegistration:
    return register_memory_provider(
        key=key,
        provider=StaticMemoryProvider,
        registry=registry,
        config_model=StaticMemorySettings,
        capabilities={"static"},
    )


def register_vector_memory_provider(
    *, key: str, registry: RegistryLike = None
) -> AdapterRegistration:
    return register_memory_provider(
        key=key,
        provider=VectorMemoryProvider,
        registry=registry,
        config_model=VectorMemorySettings,
        capabilities={"vector"},
    )


def list_data_adapters(*, registry: RegistryLike = None) -> tuple[str, ...]:
    target = _resolve_registry(registry)
    return tuple(sorted(target.available_data_keys()))


def list_memory_providers(*, registry: RegistryLike = None) -> tuple[str, ...]:
    target = _resolve_registry(registry)
    return tuple(sorted(target.available_memory_keys()))


def _resolve_registry(registry: RegistryLike) -> AdapterRegistry:
    global _DEFAULT_REGISTRY
    if registry is not None:
        return registry
    if _DEFAULT_REGISTRY is None:
        _DEFAULT_REGISTRY = AdapterRegistry()
    return _DEFAULT_REGISTRY


__all__ = [
    "AdapterRegistry",
    "register_csv_loader",
    "register_data_adapter",
    "register_http_loader",
    "register_memory_provider",
    "register_static_memory_provider",
    "register_vector_memory_provider",
    "list_data_adapters",
    "list_memory_providers",
]
