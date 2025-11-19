from __future__ import annotations

from typing import Any, List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from promptic.adapters.registry import BaseMemoryProvider
from promptic.blueprints.models import MemorySlot


class StaticMemorySettings(BaseSettings):
    """Configuration for returning static memory payloads."""

    model_config = SettingsConfigDict(env_prefix="PROMPTIC_MEMORY_STATIC_", extra="ignore")

    values: List[Any] = Field(default_factory=list)


class StaticMemoryProvider(BaseMemoryProvider):
    """Returns preconfigured memory payloads."""

    def __init__(self, settings: StaticMemorySettings | None = None) -> None:
        super().__init__(settings)
        self._settings = settings or StaticMemorySettings()

    def load(self, slot: MemorySlot) -> List[Any]:
        return list(self._settings.values)


__all__ = ["StaticMemoryProvider", "StaticMemorySettings"]
