from __future__ import annotations

from typing import Any, Dict, List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from promptic.adapters.registry import BaseMemoryProvider
from promptic.blueprints.models import MemorySlot


class VectorMemorySettings(BaseSettings):
    """Toy vector memory provider that slices a configured record set."""

    model_config = SettingsConfigDict(env_prefix="PROMPTIC_MEMORY_VECTOR_", extra="ignore")

    records: List[Dict[str, Any]] = Field(default_factory=list)
    limit: int = 5


class VectorMemoryProvider(BaseMemoryProvider):
    """Returns the top-N configured memory entries."""

    def __init__(self, settings: VectorMemorySettings | None = None) -> None:
        super().__init__(settings)
        self._settings = settings or VectorMemorySettings()

    def load(self, slot: MemorySlot) -> List[Dict[str, Any]]:
        return self._settings.records[: self._settings.limit]


__all__ = ["VectorMemoryProvider", "VectorMemorySettings"]
