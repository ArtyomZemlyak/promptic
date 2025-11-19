# Quickstart: Context Engineering Library

## 1. Install & Configure
```bash
pip install -e .[adapters]
cp .env.example .env
```
Populate `.env` with the `ContextEngineSettings` fields (filesystem root, default adapters, per-step size budgets). Settings are loaded via `pydantic-settings`, so environment variables beat `.env`.

## 2. Author a Blueprint
Create `blueprints/research_flow.yaml`:
```yaml
id: research-flow
name: Research Flow
prompt_template: >
  You are a structured research assistant...
global_instructions:
  - instruction_id: root_guidance
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
```

## 3. Register Adapters
Use the SDK helpers to register built-in adapters and configure defaults via settings:
```python
from promptic.adapters import AdapterRegistry
from promptic.sdk import adapters as sdk_adapters
from promptic.settings.base import ContextEngineSettings

registry = AdapterRegistry()
sdk_adapters.register_csv_loader("csv_loader", registry=registry)
sdk_adapters.register_static_memory_provider("vector_db", registry=registry)

settings = ContextEngineSettings()
settings.adapter_registry.data_defaults["csv_loader"] = {"path": "data/sources.csv"}
settings.adapter_registry.memory_defaults["vector_db"] = {"values": ["vector://finding-123"]}
```
Adapters inherit from `BaseAdapter`/`BaseMemoryProvider` and accept `BaseSettings` configs. Registration can run at import time or via plugin entry points.

## 4. Preview & Execute
```python
from promptic.sdk import blueprints, pipeline
from promptic.sdk.api import build_materializer

materializer = build_materializer(settings=settings, registry=registry)
preview = blueprints.preview_blueprint(
    blueprint_id="research-flow",
    settings=settings,
    materializer=materializer,
)
print(preview.rendered_context)

run = pipeline.run_pipeline(
    blueprint_id="research-flow",
    settings=settings,
    materializer=materializer,
)
for event in run.events:
    print(event.event_type, event.payload)
```
Both `blueprints.preview_blueprint` and `pipeline.run_pipeline` resolve data/memory via the injected `ContextMaterializer`, so adapters remain encapsulated even in US1. Preview rendering highlights unresolved placeholders, while execution logs every instruction/data/memory lookup to `logs/research-flow.jsonl`. To swap sources, register a different adapter under the same key (e.g., `sdk_adapters.register_http_loader("csv_loader", registry=AdapterRegistry())`) and provide new defaults—no blueprint changes required.

## 5. Audit Outputs
- Inspect `logs/*.jsonl` for `size_warning` or `error` events.
- Use `pipeline.trace_run(run_id, step_id="summarize", item_index=2)` (SDK helper) to replay nested instructions for a specific item.

## 6. Iterate
- Update YAML/Markdown assets; no Python edits required unless adding adapters.
- Re-run tests: `pytest tests -m "unit or integration or contract"`.
- Run `pre-commit run --all-files` before pushing.
