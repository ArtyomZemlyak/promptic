#!/usr/bin/env python3
"""Example: Adapter registration and swapping (User Story 2).

This script demonstrates:
- Registering CSV data adapter
- Registering static memory provider
- Swapping adapters without blueprint changes
- Rendering contexts with different adapters (inline and file-first modes)
"""

from pathlib import Path

from promptic.adapters.registry import AdapterRegistry
from promptic.sdk import adapters as sdk_adapters
from promptic.sdk.api import build_materializer, load_blueprint, render_for_llm, render_preview
from promptic.sdk.blueprints import preview_blueprint
from promptic.settings.base import ContextEngineSettings

# Create registry and register adapters
registry = AdapterRegistry()
sdk_adapters.register_csv_loader(key="csv_loader", registry=registry)
sdk_adapters.register_static_memory_provider(key="static_memory", registry=registry)
print("✅ Adapters registered")

# Minimal API: Load blueprint (settings are in blueprint.yaml)
blueprint_path = Path(__file__).parent / "blueprint.yaml"

# Create settings - instruction_root will be resolved relative to blueprint file
settings = ContextEngineSettings()
blueprint_dir = blueprint_path.parent.resolve()
if (blueprint_dir / "instructions").exists():
    settings.instruction_root = blueprint_dir / "instructions"

# Configure adapter defaults for CSV loader
if (blueprint_dir / "data" / "sample.csv").exists():
    settings.adapter_registry.data_defaults["csv_loader"] = {
        "path": str(blueprint_dir / "data" / "sample.csv")
    }

# Create materializer with registry and settings
materializer = build_materializer(settings=settings, registry=registry)

# Load blueprint
blueprint = load_blueprint(blueprint_path, settings=settings)
print(f"✅ Blueprint loaded")

# Preview with CSV adapter (formatted terminal output) - inline mode
print("\n=== Preview with CSV adapter (inline mode) ===")
render_preview(blueprint, materializer=materializer, settings=settings)

# File-first rendering with CSV adapter
print("\n=== File-first rendering with CSV adapter ===")
file_first_result = preview_blueprint(
    blueprint_id=str(blueprint_path),
    settings=settings,
    materializer=materializer,
    render_mode="file_first",
    print_to_console=True,
)
if file_first_result.markdown:
    print(f"\n✅ File-first markdown ({len(file_first_result.markdown)} chars)")
    print(
        file_first_result.markdown[:300] + "..."
        if len(file_first_result.markdown) > 300
        else file_first_result.markdown
    )

# Render for LLM with CSV adapter
print("\n=== Render for LLM with CSV adapter ===")
llm_text = render_for_llm(blueprint, materializer=materializer, settings=settings)
print(f"✅ LLM-ready text ({len(llm_text)} chars): {llm_text[:200]}...")

# Note: In a real scenario, you would register an HTTP adapter here
# and swap it by registering with the same key or creating a new registry
print("\n=== Adapter Swap Note ===")
print("To swap adapters, you can:")
print("1. Register a new adapter with the same key (replaces existing)")
print("2. Create a new registry and materializer with different adapters")
print("3. The blueprint code remains unchanged - adapter swap is transparent")
print("✅ Adapter swap demonstration complete!")
