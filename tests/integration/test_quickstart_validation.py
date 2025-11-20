from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from promptic.adapters import AdapterRegistry
from promptic.sdk import adapters as sdk_adapters
from promptic.sdk import api
from promptic.settings.base import ContextEngineSettings


def _write_quickstart_assets(tmp_path: Path) -> tuple[ContextEngineSettings, str]:
    blueprint_root = tmp_path / "blueprints"
    instruction_root = tmp_path / "instructions"
    data_root = tmp_path / "data"
    log_root = tmp_path / "logs"
    blueprint_root.mkdir()
    instruction_root.mkdir()
    data_root.mkdir()
    log_root.mkdir()

    (instruction_root / "root_guidance.md").write_text("Root guidance", encoding="utf-8")
    (instruction_root / "collect_step.md").write_text(
        "Collecting {{ loop_item.title }}", encoding="utf-8"
    )
    (instruction_root / "summarize_step.md").write_text("Summaries go here.", encoding="utf-8")

    csv_path = data_root / "sources.csv"
    csv_path.write_text(
        "title,url\nDoc A,https://example/a\nDoc B,https://example/b\n", encoding="utf-8"
    )

    blueprint_root.joinpath("research-flow.yaml").write_text(
        dedent(
            """
            name: Research Flow
            prompt_template: |
              You are a structured research assistant.
            global_instructions:
              - instruction_id: root_guidance
            data_slots:
              - name: sources
                adapter_key: csv_loader
                schema:
                  type: array
                  items:
                    type: object
                    properties:
                      title: {type: string}
                      url: {type: string}
            memory_slots:
              - name: prior_findings
                provider_key: vector_db
            steps:
              - step_id: collect
                title: Collect Sources
                kind: loop
                loop_slot: sources
                instruction_refs:
                  - instruction_id: collect_step
                children:
                  - step_id: summarize
                    title: Summarize Source
                    kind: sequence
                    instruction_refs:
                      - instruction_id: summarize_step
            """
        ).strip(),
        encoding="utf-8",
    )

    settings = ContextEngineSettings(
        blueprint_root=blueprint_root,
        instruction_root=instruction_root,
        log_root=log_root,
    )
    settings.adapter_registry.data_defaults["csv_loader"] = {"path": csv_path}
    settings.adapter_registry.memory_defaults["vector_db"] = {"values": ["vector://finding-123"]}
    return settings, "research-flow"


def test_quickstart_instructions_execute_end_to_end(tmp_path: Path) -> None:
    settings, blueprint_id = _write_quickstart_assets(tmp_path)
    registry = AdapterRegistry()
    sdk_adapters.register_csv_loader(key="csv_loader", registry=registry)
    sdk_adapters.register_static_memory_provider(key="vector_db", registry=registry)

    runtime = api.bootstrap_runtime(settings=settings, registry=registry)

    preview = api.preview_blueprint(
        blueprint_id=blueprint_id,
        settings=settings,
        materializer=runtime.materializer,
    )

    assert "Doc A" in preview.rendered_context
    assert preview.instruction_ids
