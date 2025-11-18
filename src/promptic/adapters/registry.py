from __future__ import annotations

import inspect
from dataclasses import dataclass
from importlib import import_module
from importlib.metadata import EntryPoint, entry_points
from threading import RLock
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    Literal,
    Mapping,
    MutableMapping,
    Optional,
    TypeVar,
    cast,
)

from pydantic_settings import BaseSettings

from promptic.blueprints.models import AdapterRegistration, DataSlot, MemorySlot
from promptic.context.errors import AdapterNotRegisteredError, AdapterRegistrationError

TAdapter = TypeVar("TAdapter", bound="BaseAdapter")
AdapterFactory = Callable[[Optional[BaseSettings]], TAdapter]


class BaseAdapter:
    """Base class shared by data and memory adapters."""

    def __init__(self, settings: BaseSettings | None = None) -> None:
        self.settings = settings


class BaseDataAdapter(BaseAdapter):
    """Adapter that produces data slot payloads."""

    def fetch(self, slot: DataSlot) -> Any:  # pragma: no cover - interface
        raise NotImplementedError


class BaseMemoryProvider(BaseAdapter):
    """Adapter that resolves memory slot payloads."""

    def load(self, slot: MemorySlot) -> Any:  # pragma: no cover - interface
        raise NotImplementedError


@dataclass
class RegistryEntry(Generic[TAdapter]):
    registration: AdapterRegistration
    factory: AdapterFactory[TAdapter]


class AdapterRegistry:
    """Thread-safe registry for adapter factories and plugin discovery."""

    def __init__(self) -> None:
        self._data: Dict[str, RegistryEntry[BaseDataAdapter]] = {}
        self._memory: Dict[str, RegistryEntry[BaseMemoryProvider]] = {}
        self._lock = RLock()

    def register_data(
        self,
        key: str,
        adapter: type[BaseDataAdapter] | AdapterFactory[BaseDataAdapter],
        *,
        config_model: type[BaseSettings] | None = None,
        entry_point: str | None = None,
        capabilities: Iterable[str] | None = None,
    ) -> AdapterRegistration:
        return self._register(
            bucket=self._data,
            key=key,
            adapter=adapter,
            adapter_type="data",
            config_model=config_model,
            entry_point=entry_point,
            capabilities=capabilities,
        )

    def register_memory(
        self,
        key: str,
        provider: type[BaseMemoryProvider] | AdapterFactory[BaseMemoryProvider],
        *,
        config_model: type[BaseSettings] | None = None,
        entry_point: str | None = None,
        capabilities: Iterable[str] | None = None,
    ) -> AdapterRegistration:
        return self._register(
            bucket=self._memory,
            key=key,
            adapter=provider,
            adapter_type="memory",
            config_model=config_model,
            entry_point=entry_point,
            capabilities=capabilities,
        )

    def create_data_adapter(
        self, key: str, *, config: BaseSettings | Mapping[str, Any] | None = None
    ) -> BaseDataAdapter:
        entry = self._get_entry(self._data, key, adapter_type="data")
        settings = self._prepare_settings(config, entry.registration.config_model)
        return self._instantiate(entry.factory, settings)

    def create_memory_provider(
        self, key: str, *, config: BaseSettings | Mapping[str, Any] | None = None
    ) -> BaseMemoryProvider:
        entry = self._get_entry(self._memory, key, adapter_type="memory")
        settings = self._prepare_settings(config, entry.registration.config_model)
        return self._instantiate(entry.factory, settings)

    def available_data_keys(self) -> Iterable[str]:
        with self._lock:
            return tuple(sorted(self._data.keys()))

    def available_memory_keys(self) -> Iterable[str]:
        with self._lock:
            return tuple(sorted(self._memory.keys()))

    def auto_discover(
        self,
        *,
        module_paths: Iterable[str] | None = None,
        entry_point_group: str | None = None,
    ) -> int:
        """Import modules and entry points declared by settings."""

        discovered = 0
        if module_paths:
            for module_path in module_paths:
                import_module(module_path)
        if entry_point_group:
            discovered += self.load_entry_points(entry_point_group)
        return discovered

    def load_entry_points(self, group: str) -> int:
        count = 0
        for ep in _iter_entry_points(group):
            payload = ep.load()
            self._register_from_plugin(ep.name, payload)
            count += 1
        return count

    def _register(
        self,
        *,
        bucket: MutableMapping[str, RegistryEntry[Any]],
        key: str,
        adapter: type[TAdapter] | AdapterFactory[TAdapter],
        adapter_type: Literal["data", "memory"],
        config_model: type[BaseSettings] | None,
        entry_point: str | None,
        capabilities: Iterable[str] | None,
    ) -> AdapterRegistration:
        with self._lock:
            if key in bucket:
                raise AdapterRegistrationError(
                    f"{adapter_type} adapter '{key}' already registered."
                )
            factory = self._normalize_factory(adapter)
            registration = AdapterRegistration(
                key=key,
                adapter_type=adapter_type,
                entry_point=entry_point,
                config_model=config_model,
                capabilities=set(capabilities or set()),
            )
            bucket[key] = RegistryEntry(registration=registration, factory=factory)
        return registration

    def _get_entry(
        self,
        bucket: Mapping[str, RegistryEntry[TAdapter]],
        key: str,
        *,
        adapter_type: str,
    ) -> RegistryEntry[TAdapter]:
        with self._lock:
            try:
                return bucket[key]
            except KeyError as exc:  # pragma: no cover - defensive
                raise AdapterNotRegisteredError(key, adapter_type) from exc

    def _prepare_settings(
        self,
        config: BaseSettings | Mapping[str, Any] | None,
        config_model: type[BaseSettings] | None,
    ) -> BaseSettings | None:
        if config is None:
            return config_model() if config_model else None
        if isinstance(config, BaseSettings):
            return config
        if not config_model:
            raise AdapterRegistrationError(
                "Dictionary configuration provided but adapter lacks a config_model."
            )
        return config_model(**config)

    @staticmethod
    def _instantiate(factory: AdapterFactory[TAdapter], settings: BaseSettings | None) -> TAdapter:
        return factory(settings)

    @staticmethod
    def _normalize_factory(
        adapter: type[TAdapter] | AdapterFactory[TAdapter],
    ) -> AdapterFactory[TAdapter]:
        if inspect.isclass(adapter):
            return cast(AdapterFactory[TAdapter], adapter)
        return adapter

    def _register_from_plugin(self, name: str, payload: Any) -> None:
        if (
            isinstance(payload, tuple)
            and len(payload) == 2
            and isinstance(payload[0], AdapterRegistration)
        ):
            registration, factory = payload
            target_bucket: MutableMapping[str, RegistryEntry[Any]]
            if registration.adapter_type == "data":
                target_bucket = cast(MutableMapping[str, RegistryEntry[Any]], self._data)
            else:
                target_bucket = cast(MutableMapping[str, RegistryEntry[Any]], self._memory)
            self._register(
                bucket=target_bucket,
                key=registration.key,
                adapter=factory,
                adapter_type=registration.adapter_type,
                config_model=registration.config_model,
                entry_point=registration.entry_point or name,
                capabilities=registration.capabilities,
            )
            return

        if inspect.isclass(payload):
            if issubclass(payload, BaseDataAdapter):
                self.register_data(name, payload)
                return
            if issubclass(payload, BaseMemoryProvider):
                self.register_memory(name, payload)
                return

        if callable(payload):
            payload(self)
            return

        raise AdapterRegistrationError(
            f"Unsupported entry point payload '{payload}' for adapter '{name}'."
        )


def _iter_entry_points(group: str) -> Iterable[EntryPoint]:
    eps = entry_points()
    if hasattr(eps, "select"):
        select = getattr(eps, "select")
        return tuple(select(group=group))
    if isinstance(eps, dict):
        legacy = eps.get(group, ())
        return tuple(legacy)
    return tuple(ep for ep in eps if getattr(ep, "group", None) == group)


__all__ = [
    "AdapterRegistry",
    "BaseAdapter",
    "BaseDataAdapter",
    "BaseMemoryProvider",
]
