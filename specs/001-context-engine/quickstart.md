# Quickstart: Context Engineering Library

## 1. Install & Configure
```bash
pip install -e .[cli,adapters]
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
Implement adapters (or reuse built-ins) and register them in `settings.adapters`:
```python
from promptic.adapters import registry
from my_project.adapters import CsvSource, QdrantMemory

registry.register_data("csv_loader", CsvSource)
registry.register_memory("vector_db", QdrantMemory)
```
Adapters inherit from `BaseAdapter`/`BaseMemoryProvider` and accept `BaseSettings` configs. Registration can run at import time or via plugin entry points.

## 4. Preview & Execute
```bash
promptic blueprint preview research-flow --sample samples/research.json
promptic pipeline run research-flow --data sources=samples/research.csv
```
Preview renders merged context and highlights unresolved placeholders. Execution logs every instruction/data/memory lookup to `logs/research-flow.jsonl`.

## 5. Audit Outputs
- Inspect `logs/*.jsonl` for `size_warning` or `error` events.
- Use `promptic pipeline trace research-flow --step summarize --item 2` to replay nested instructions for a specific item.

## 6. Iterate
- Update YAML/Markdown assets; no Python edits required unless adding adapters.
- Re-run tests: `pytest tests -m "unit or integration or contract"`.
- Run `pre-commit run --all-files` before pushing.
