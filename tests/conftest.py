from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    tests_root = ROOT / "tests"
    for item in items:
        try:
            relative = Path(item.fspath).resolve().relative_to(tests_root)
        except ValueError:
            continue
        top_level = relative.parts[0]
        if top_level == "unit":
            item.add_marker("unit")
        elif top_level == "integration":
            item.add_marker("integration")
        elif top_level == "contract":
            item.add_marker("contract")
