from __future__ import annotations

import json
from pathlib import Path

from promptic.blueprints import ExecutionLogEntry
from promptic.context import JsonlEventLogger


def test_jsonl_logger_writes_entries(tmp_path: Path) -> None:
    logger = JsonlEventLogger(tmp_path, blueprint_id="demo", run_id="run-1")
    entry = ExecutionLogEntry(
        step_id="collect",
        event_type="data_resolved",
        payload={"adapter": "csv"},
        reference_ids=["sources"],
    )

    log_path = logger.log(entry)

    assert log_path.exists()
    data = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(data) == 1
    parsed = json.loads(data[0])
    assert parsed["step_id"] == "collect"
    assert parsed["payload"]["adapter"] == "csv"
