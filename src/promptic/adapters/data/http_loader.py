from __future__ import annotations

import json
from typing import Any, List
from urllib import error, request

from pydantic import AnyUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from promptic.adapters.registry import BaseDataAdapter
from promptic.blueprints.models import DataSlot
from promptic.context.errors import AdapterExecutionError


class HttpAdapterSettings(BaseSettings):
    """Simple HTTP JSON adapter configuration."""

    model_config = SettingsConfigDict(env_prefix="PROMPTIC_HTTP_ADAPTER_", extra="ignore")

    endpoint: AnyUrl
    timeout: float = 5.0


class HttpJSONAdapter(BaseDataAdapter):
    """Fetches JSON documents from an HTTP endpoint."""

    def __init__(self, settings: HttpAdapterSettings | None = None) -> None:
        super().__init__(settings)
        self._settings = settings or HttpAdapterSettings()

    def fetch(self, slot: DataSlot) -> List[Any]:
        try:
            with request.urlopen(
                str(self._settings.endpoint),
                timeout=self._settings.timeout,
            ) as response:
                payload = response.read().decode("utf-8")
        except error.URLError as exc:  # pragma: no cover - network specific
            raise AdapterExecutionError(str(exc)) from exc
        data = json.loads(payload)
        if isinstance(data, list):
            return data
        return [data]


__all__ = ["HttpAdapterSettings", "HttpJSONAdapter"]
