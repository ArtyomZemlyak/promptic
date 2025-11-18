from __future__ import annotations

from pathlib import Path
from threading import RLock
from typing import Iterable, cast

import orjson

from promptic.blueprints.models import ExecutionLogEntry
from promptic.context.errors import LoggingError


class JsonlEventLogger:
    """
    Append-only JSONL logger capturing execution events.

    # AICODE-NOTE: JSONL keeps logs grep-able while remaining friendly to BI tooling.
    """

    def __init__(
        self, log_root: Path | str, *, blueprint_id: str, run_id: str | None = None
    ) -> None:
        self.log_root = Path(log_root).expanduser()
        self.log_root.mkdir(parents=True, exist_ok=True)
        stem = blueprint_id.replace("/", "_")
        if run_id:
            stem = f"{stem}-{run_id}"
        self.path = self.log_root / f"{stem}.jsonl"
        self._lock = RLock()

    def log(self, entry: ExecutionLogEntry) -> Path:
        return self.log_many([entry])

    def log_many(self, entries: Iterable[ExecutionLogEntry]) -> Path:
        payload = b"".join(self._serialize(entry) for entry in entries)
        with self._lock:
            try:
                with self.path.open("ab") as handle:
                    handle.write(payload)
            except OSError as exc:  # pragma: no cover - filesystem specific
                raise LoggingError(str(exc)) from exc
        return self.path

    @staticmethod
    def _serialize(entry: ExecutionLogEntry) -> bytes:
        data = entry.model_dump(mode="json")
        payload = cast(bytes, orjson.dumps(data))
        return payload + b"\n"


__all__ = ["JsonlEventLogger"]
