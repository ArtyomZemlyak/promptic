# Adapter Integration Guide

Phase 1 establishes the adapter registry infrastructure so later stories can
swap data and memory sources without rewriting pipeline logic. This document
describes the base classes, registration API, plugin discovery, and how the
`ContextMaterializer` consumes adapters during preview/execution.

## Adapter Base Classes

All adapters inherit from `promptic.adapters.registry.BaseAdapter` which stores
an optional `pydantic-settings` configuration instance. Two concrete families
exist today:

- `BaseDataAdapter`: implementations must override `fetch(self, slot: DataSlot)`
  and return serializable data that matches the slot's JSON schema.
- `BaseMemoryProvider`: implementations override `load(self, slot: MemorySlot)`
  and return whatever structure downstream prompts expect (vector IDs, chat
  history, etc.).

Adapters are regular Python classes; async variants can still be wrapped by
returning `asyncio.run()` or exposing awaitables once we add async orchestration.

## Registration API

Use `promptic.adapters.AdapterRegistry` to register adapters at import time:

```python
from promptic.adapters import AdapterRegistry, BaseDataAdapter
from promptic.blueprints import DataSlot
from promptic.settings.base import ContextEngineSettings

registry = AdapterRegistry()

class CsvLoader(BaseDataAdapter):
    def fetch(self, slot: DataSlot):
        return [{"title": "Paper A"}]

registry.register_data("csv_loader", CsvLoader)
registry.register_memory("vector_db", MyVectorProvider)

materializer = promptic.sdk.build_materializer(
    settings=ContextEngineSettings(), registry=registry
)
```

Each registration stores an `AdapterRegistration` record (available via the
registry) so future diagnostics can report entry points, config models, and
capabilities. Passing a `config_model` ensures the registry instantiates the
adapter with strongly-typed settings whenever callers supply a plain dict.

## Plugin Discovery

`AdapterRegistry.auto_discover()` supports two discovery modes:

- Import modules declared in `ContextEngineSettings.adapter_registry.module_paths`
  so the modules can call `register_data`/`register_memory` on import.
- Load entry points (default group `promptic.adapters`) where each entry point
  may expose a subclass, a `(AdapterRegistration, factory)` tuple, or a
  callable that receives the registry and performs custom registrations.

This keeps the core library lean while enabling applications to ship adapters
in separate packages.

## Consumption via the Context Materializer

`ContextMaterializer.resolve_data()` and `resolve_memory()` request adapters by
key, instantiate them through the registry, and cache resolved values. When a
blueprint provides explicit overrides (e.g., sample data for previews) the
materializer short-circuits the registry but still records the result so
subsequent lookups avoid redundant work. Adapter failures are wrapped in
`AdapterExecutionError` and propagated via `OperationResult`, giving SDK callers
structured context for retries or rich error messaging.
