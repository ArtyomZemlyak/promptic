#!/usr/bin/env python3
"""Example: Adapter registration and swapping (User Story 2).

This script demonstrates:
- Registering CSV data adapter
- Registering static memory provider
- Swapping adapters without blueprint changes
- Rendering contexts with different adapters
"""

from pathlib import Path

from promptic.adapters.registry import AdapterRegistry
from promptic.sdk import adapters as sdk_adapters
from promptic.sdk.api import (
    _create_settings_from_blueprint,
    build_materializer,
    load_blueprint,
    render_for_llm,
    render_preview,
)

# Create registry and register adapters
registry = AdapterRegistry()
sdk_adapters.register_csv_loader(key="csv_loader", registry=registry)
sdk_adapters.register_static_memory_provider(key="static_memory", registry=registry)
print("✅ Adapters registered")

# Minimal API: Load blueprint (settings are in blueprint.yaml)
blueprint = load_blueprint(Path(__file__).parent / "blueprint.yaml")
print(f"✅ Blueprint loaded: {blueprint.name}")

# Create materializer with registry and settings from blueprint
settings = _create_settings_from_blueprint(blueprint)
materializer = build_materializer(settings=settings, registry=registry)

# Preview with CSV adapter (formatted terminal output)
print("\n=== Preview with CSV adapter ===")
render_preview(blueprint, materializer=materializer)

# Render for LLM with CSV adapter
print("\n=== Render for LLM with CSV adapter ===")
llm_text = render_for_llm(blueprint, materializer=materializer)
print(f"✅ LLM-ready text ({len(llm_text)} chars): {llm_text[:200]}...")

# Note: In a real scenario, you would register an HTTP adapter here
# and swap it by registering with the same key or creating a new registry
print("\n=== Adapter Swap Note ===")
print("To swap adapters, you can:")
print("1. Register a new adapter with the same key (replaces existing)")
print("2. Create a new registry and materializer with different adapters")
print("3. The blueprint code remains unchanged - adapter swap is transparent")
print("✅ Adapter swap demonstration complete!")
