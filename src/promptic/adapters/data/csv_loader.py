from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable, List

from pydantic_settings import BaseSettings, SettingsConfigDict

from promptic.adapters.registry import BaseDataAdapter
from promptic.blueprints.models import DataSlot
from promptic.context.errors import AdapterExecutionError


class CSVAdapterSettings(BaseSettings):
    """Configuration for CSV-backed data adapters."""

    model_config = SettingsConfigDict(env_prefix="PROMPTIC_CSV_ADAPTER_", extra="ignore")

    path: Path
    encoding: str = "utf-8"
    delimiter: str = ","


class CSVDataAdapter(BaseDataAdapter):
    """Loads blueprint slot data from a CSV file."""

    def __init__(self, settings: CSVAdapterSettings | None = None) -> None:
        super().__init__(settings)
        self._settings = settings or CSVAdapterSettings()

    def fetch(self, slot: DataSlot) -> List[dict[str, Any]]:
        path = self._settings.path.expanduser()
        if not path.exists():
            raise AdapterExecutionError(f"CSV file '{path}' not found for slot '{slot.name}'.")
        with path.open(encoding=self._settings.encoding, newline="") as handle:
            reader = csv.DictReader(handle, delimiter=self._settings.delimiter)
            return [dict(row) for row in reader]


__all__ = ["CSVAdapterSettings", "CSVDataAdapter"]
