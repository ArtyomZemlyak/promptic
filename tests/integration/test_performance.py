from __future__ import annotations

import time
from pathlib import Path
from textwrap import dedent

from promptic.adapters import AdapterRegistry, BaseDataAdapter, BaseMemoryProvider
from promptic.blueprints import DataSlot, MemorySlot
from promptic.sdk import api
from promptic.settings.base import ContextEngineSettings


class SlowDataAdapter(BaseDataAdapter):
    calls = 0

    def fetch(self, slot: DataSlot) -> list[dict[str, str]]:
        SlowDataAdapter.calls += 1
        time.sleep(0.01)
        return [
            {"title": f"item-{slot.name}-{index}", "url": f"https://example/{index}"}
            for index in range(5)
        ]


class CountingMemoryProvider(BaseMemoryProvider):
    calls = 0

    def load(self, slot: MemorySlot) -> list[str]:
        CountingMemoryProvider.calls += 1
        return [f"memory::{slot.name}"]


def _write_assets(tmp_path: Path) -> tuple[ContextEngineSettings, str]:
    blueprint_root = tmp_path / "blueprints"
    instruction_root = tmp_path / "instructions"
    log_root = tmp_path / "logs"
    blueprint_root.mkdir()
    instruction_root.mkdir()
    log_root.mkdir()

    for index in range(8):
        (instruction_root / f"instruction-{index}.md").write_text(
            f"Instruction {index}", encoding="utf-8"
        )

    blueprint_root.joinpath("benchmark-flow.yaml").write_text(
        dedent(
            """
            name: Benchmark Flow
            prompt_template: |
              You are a fast researcher. {{ data.sources | length }} sources loaded.
            global_instructions:
              - instruction_id: instruction-0
              - instruction_id: instruction-1
            steps:
              - step_id: collect
                title: Collect Sources
                kind: loop
                loop_slot: sources
                instruction_refs:
                  - instruction_id: instruction-2
                  - instruction_id: instruction-3
                children:
                  - step_id: summarize
                    title: Summarize
                    kind: sequence
                    instruction_refs:
                      - instruction_id: instruction-4
                      - instruction_id: instruction-5
            data_slots:
              - name: sources
                adapter_key: slow_sources
                schema:
                  type: array
                  items:
                    type: object
            memory_slots:
              - name: prior
                provider_key: static_memory
            """
        ).strip(),
        encoding="utf-8",
    )

    settings = ContextEngineSettings(
        blueprint_root=blueprint_root,
        instruction_root=instruction_root,
        log_root=log_root,
    )
    return settings, "benchmark-flow"


def test_materializer_caching_keeps_preview_and_pipeline_fast(tmp_path: Path) -> None:
    settings, blueprint_id = _write_assets(tmp_path)
    registry = AdapterRegistry()
    registry.register_data("slow_sources", SlowDataAdapter)
    registry.register_memory("static_memory", CountingMemoryProvider)

    runtime = api.bootstrap_runtime(settings=settings, registry=registry)
    materializer = runtime.materializer

    preview_start = time.perf_counter()
    preview = api.preview_blueprint(
        blueprint_id=blueprint_id,
        settings=settings,
        materializer=materializer,
    )
    preview_duration = time.perf_counter() - preview_start

    assert preview.rendered_context
    assert preview_duration < 0.5

    run_start = time.perf_counter()
    execution = api.run_pipeline(
        blueprint_id=blueprint_id,
        settings=settings,
        materializer=materializer,
    )
    run_duration = time.perf_counter() - run_start

    assert execution.run_id
    assert run_duration < 0.5

    stats = materializer.snapshot_stats()
    assert SlowDataAdapter.calls == 1
    assert CountingMemoryProvider.calls == 1
    assert stats.data_cache_hits >= 1
    assert stats.memory_cache_hits >= 1
    assert stats.instruction_hits >= 4
