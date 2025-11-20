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

## SDK Helper Functions & Sample Adapters

`promptic.sdk.adapters` exposes convenience wrappers so applications can register
adapters without importing the registry directly. The helpers also ship reference
implementations that cover common bootstrap scenarios:

```python
from promptic.adapters import AdapterRegistry
from promptic.sdk import adapters as sdk_adapters
from promptic.settings import ContextEngineSettings

registry = AdapterRegistry()

sko = sdk_adapters.register_csv_loader(key="research_sources", registry=registry)
sko = sdk_adapters.register_http_loader(key="research_sources_http", registry=registry)
sdk_adapters.register_static_memory_provider(key="research_memory", registry=registry)

settings = ContextEngineSettings()
settings.adapter_registry.data_defaults["research_sources"] = {"path": "data/sources.csv"}
settings.adapter_registry.data_defaults["research_sources_http"] = {"endpoint": "https://api.example/data"}
settings.adapter_registry.memory_defaults["research_memory"] = {"values": ["seed"]}
```

Two data adapters are bundled today:

- `CSVDataAdapter`: reads CSV files via `CSVAdapterSettings` (path, delimiter, encoding)
  and returns a list of dictionaries suitable for JSON serialization.
- `HttpJSONAdapter`: performs a GET request using Python's standard library and returns
  parsed JSON (lists or single documents).

On the memory side we ship:

- `StaticMemoryProvider`: returns a preconfigured list of records (e.g., canned history snippets).
- `VectorMemoryProvider`: slices a configured record set to simulate retrieving the top-N embeddings.

Applications can still subclass the base adapters when they need custom logic; the helpers
simply reduce boilerplate for the common cases outlined in the spec.

## Instruction Provider Fallback Policies

Instruction providers (filesystem stores, HTTP loaders, vector-backed instruction hubs) must now declare the fallback behaviors they support so blueprints can degrade predictably without editing core modules. Each `AdapterRegistration` may include a `fallback_policies` set describing which `InstructionFallbackPolicy` modes it honors:

```python
sdk_adapters.register_http_instruction_store(
    key="remote_store",
    registry=registry,
    fallback_policies={"error", "warn"},
)
```

Blueprint authors (or SDK helpers) attach fallback configs per instruction reference:

```yaml
instruction_refs:
  - instruction_id: summarize_step
    fallback:
      mode: warn
      placeholder: "[summaries delayed]"
```

During preview/execution the `ContextMaterializer` invokes the provider. If the provider fails and the blueprint allows `warn`/`noop`, the materializer records an `instruction_fallback` event, injects the placeholder (or empty string), and continues orchestration. Providers that only support `error` preserve fail-fast semantics. This keeps SRP intact—use cases never import adapters directly, and swapping providers simply means registering a new implementation that advertises the same fallback modes.

SDK responses now surface these degradations explicitly:

- `PreviewResponse.fallback_events` contains `instruction_id`, `mode`, `message`, and the rendered placeholder so clients can render UI notices or audits.
- When building custom executors, mirror the preview logging format so `instruction_fallback` entries remain machine-readable across JSONL streams and analytics pipelines.

## Consumption via the Context Materializer

`ContextMaterializer.resolve_data()` and `resolve_memory()` request adapters by
key, instantiate them through the registry, and cache resolved values. When a
blueprint provides explicit overrides (e.g., sample data for previews) the
materializer short-circuits the registry but still records the result so
subsequent lookups avoid redundant work. Adapter failures are wrapped in
`AdapterExecutionError` and propagated via `OperationResult`, giving SDK callers
structured context for retries or rich error messaging.

Phase 2 extends the materializer with TTL-aware caches (respecting `DataSlot.ttl_seconds`)
and configurable retries (`ContextEngineSettings.adapter_registry.max_retries`). Default
configuration payloads for each adapter key live under
`ContextEngineSettings.adapter_registry.{data_defaults,memory_defaults}` so projects can
lean on `pydantic-settings` rather than hardcoding parameters in code.

## Batching, Reuse & Telemetry

During the Polish phase the materializer learned how to batch adapter usage per
configuration. Instances are now cached per adapter key + config fingerprint, which
means running both preview and pipeline flows only instantiates each adapter once.
The new `MaterializerStats` dataclass exposes cache hits, misses, and adapter
instantiation counts so performance regressions surface immediately:

```python
stats = materializer.snapshot_stats()
print("Data hits:", stats.data_cache_hits, "adapter instances:", stats.data_adapter_instances)
```

These stats are what power the new integration benchmark (`tests/integration/test_performance.py`)
and the quickstart validation doc, giving adapter owners concrete evidence that their
connectors behave within the promised latency budget.
