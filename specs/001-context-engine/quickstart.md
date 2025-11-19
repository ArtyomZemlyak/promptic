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

## 4. Configure Instruction Fallbacks
Optional instructions (e.g., experimental guidance hosted in a remote store) can now declare fallback policies directly in the blueprint so adapter swaps never require core code edits. Extend the YAML from step 2:
```yaml
global_instructions:
  - instruction_id: root_guidance
    fallback:
      mode: warn
      placeholder: "[root guidance temporarily unavailable]"
steps:
  - step_id: collect
    instruction_refs:
      - instruction_id: collect_step
        fallback:
          mode: noop
          log_key: collect_step_missing
```
Register providers with their supported modes:
```python
sdk_adapters.register_http_instruction_store(
    key="remote_store",
    registry=registry,
    fallback_policies={"error", "warn"},
)
```
If the HTTP store goes down, rendering emits a `fallback_event`, inject the placeholder (for `warn`) or empty string (for `noop`), and continue so long as the policy allows it. All events are returned in response objects via `InstructionFallbackPolicy` diagnostics.

## 5. Load & Render (Minimal API)
The simplest usage requires just 3 lines of Python code:
```python
from promptic.sdk import load_blueprint, render_preview, render_for_llm

# Load blueprint (auto-discovers instructions and adapters)
blueprint = load_blueprint("research-flow")

# Preview in terminal (Rich formatting)
render_preview(blueprint)

# Get text for LLM
text = render_for_llm(blueprint)
```

All dependencies (instructions, adapters) are resolved automatically under the hood. The `load_blueprint()` function supports three variants:
- Auto-discovery by name: `load_blueprint("research-flow")`
- Explicit file path: `load_blueprint("path/to/blueprint.yaml")`
- With optional settings: `load_blueprint("research-flow", settings=...)`

## 6. Advanced Usage
For more control, you can use the detailed API:
```python
from promptic.sdk import blueprints
from promptic.sdk.api import build_materializer

materializer = build_materializer(settings=settings, registry=registry)
preview = blueprints.preview_blueprint(
    blueprint_id="research-flow",
    settings=settings,
    materializer=materializer,
)
print(preview.rendered_context)
for event in preview.fallback_events:
    print("fallback:", event.mode, event.instruction_id)
```

Rendering functions resolve data/memory via the injected `ContextMaterializer`, so adapters remain encapsulated. Preview rendering highlights unresolved placeholders. To swap sources, register a different adapter under the same key (e.g., `sdk_adapters.register_http_loader("csv_loader", registry=AdapterRegistry())`) and provide new defaults—no blueprint changes required.

`preview.fallback_events` expose structured diagnostics for each degraded instruction. Every event includes the `instruction_id`, fallback `mode`, `message`, and the placeholder text that was rendered (warn) or recorded (noop).

## 7. Render Specific Instructions
You can render specific instructions in multiple ways:
```python
# Render single instruction by ID
text = render_instruction(blueprint, "collect_step")

# Render all instructions for a step
text = render_instruction(blueprint, step_id="collect")

# Or use method on blueprint object
text = blueprint.render_instruction("collect_step")
```

## 8. Iterate
- Update YAML/Markdown assets; no Python edits required unless adding adapters.
- Re-run tests: `pytest tests -m "unit or integration or contract"`.
- Run `pre-commit run --all-files` before pushing.
- Validation evidence for this flow lives in `docs_site/context-engineering/quickstart-validation.md`.
