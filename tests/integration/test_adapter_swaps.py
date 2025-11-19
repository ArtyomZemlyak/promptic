from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from promptic.adapters import AdapterRegistry
from promptic.sdk import adapters as sdk_adapters
from promptic.sdk import blueprints as sdk_blueprints
from promptic.sdk.api import build_materializer
from promptic.settings.base import AdapterRegistrySettings, ContextEngineSettings


def _write_blueprint(tmp_path: Path) -> ContextEngineSettings:
    blueprint_root = tmp_path / "blueprints"
    instruction_root = tmp_path / "instructions"
    blueprint_root.mkdir()
    instruction_root.mkdir()

    (instruction_root / "intro.md").write_text("Intro", encoding="utf-8")
    (instruction_root / "analyze.md").write_text("Analyze", encoding="utf-8")

    blueprint_root.joinpath("research.yaml").write_text(
        """
name: Research Flow
prompt_template: |
  Source: {{ data.records[0].title }}
  Memory count: {{ memory.history|length }}
global_instructions:
  - instruction_id: intro
steps:
  - step_id: analyze
    title: Analyze Data
    kind: sequence
    instruction_refs:
      - instruction_id: analyze
data_slots:
  - name: records
    adapter_key: research_sources
    schema:
      type: array
memory_slots:
  - name: history
    provider_key: research_memory
""",
        encoding="utf-8",
    )

    return ContextEngineSettings(
        blueprint_root=blueprint_root,
        instruction_root=instruction_root,
        log_root=tmp_path / "logs",
        adapter_registry=AdapterRegistrySettings(),
    )


def _make_csv(tmp_path: Path) -> Path:
    csv_path = tmp_path / "sources.csv"
    csv_path.write_text("title,url\nCSV Source,https://csv.example\n", encoding="utf-8")
    return csv_path


class _JSONHandler(BaseHTTPRequestHandler):
    payload: list[dict[str, Any]] = []

    def do_GET(self) -> None:  # pragma: no cover - exercised via integration test
        body = json.dumps(self.payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:  # pragma: no cover - noisy
        return


class _Server:
    def __init__(self, payload: list[dict[str, Any]]) -> None:
        self._handler = type("_Handler", (_JSONHandler,), {"payload": payload})
        self._server = HTTPServer(("127.0.0.1", 0), self._handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    def start(self) -> str:
        self._thread.start()
        host, port = self._server.server_address
        # server_address returns tuple[str, int] but host might be bytes
        host_str = host if isinstance(host, str) else host.decode("utf-8")
        return f"http://{host_str}:{port}"

    def stop(self) -> None:
        self._server.shutdown()
        self._thread.join(timeout=2)


def test_adapter_swap_via_sdk(tmp_path: Path) -> None:
    settings = _write_blueprint(tmp_path)
    csv_path = _make_csv(tmp_path)

    # First run: CSV adapter
    registry_csv = AdapterRegistry()
    sdk_adapters.register_csv_loader(key="research_sources", registry=registry_csv)
    sdk_adapters.register_static_memory_provider(key="research_memory", registry=registry_csv)
    settings_csv = settings.model_copy(deep=True)
    settings_csv.adapter_registry.data_defaults["research_sources"] = {"path": str(csv_path)}
    settings_csv.adapter_registry.memory_defaults["research_memory"] = {"values": ["csv-history"]}

    materializer_csv = build_materializer(settings=settings_csv, registry=registry_csv)
    csv_response = sdk_blueprints.preview_blueprint(
        blueprint_id="research",
        settings=settings_csv,
        materializer=materializer_csv,
    )

    assert "CSV Source" in csv_response.rendered_context
    assert "csv-history" in csv_response.rendered_context

    # Second run: HTTP adapter
    payload = [{"title": "HTTP Source", "url": "https://http.example"}]
    server = _Server(payload)
    endpoint = server.start()
    try:
        registry_http = AdapterRegistry()
        sdk_adapters.register_http_loader(key="research_sources", registry=registry_http)
        sdk_adapters.register_static_memory_provider(key="research_memory", registry=registry_http)
        settings_http = settings.model_copy(deep=True)
        settings_http.adapter_registry.data_defaults["research_sources"] = {"endpoint": endpoint}
        settings_http.adapter_registry.memory_defaults["research_memory"] = {
            "values": ["http-history"]
        }

        materializer_http = build_materializer(settings=settings_http, registry=registry_http)
        http_response = sdk_blueprints.preview_blueprint(
            blueprint_id="research",
            settings=settings_http,
            materializer=materializer_http,
        )
    finally:
        server.stop()

    assert "HTTP Source" in http_response.rendered_context
    assert "http-history" in http_response.rendered_context
    assert csv_response.rendered_context != http_response.rendered_context
