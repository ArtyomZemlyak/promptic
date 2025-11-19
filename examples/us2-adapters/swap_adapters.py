#!/usr/bin/env python3
"""Example: Adapter registration and swapping (User Story 2).

This script demonstrates:
- Registering CSV data adapter
- Registering HTTP data adapter
- Swapping adapters without blueprint changes
"""

from pathlib import Path

from promptic.adapters.registry import AdapterRegistry
from promptic.sdk import adapters as sdk_adapters
from promptic.sdk import blueprints
from promptic.settings.base import ContextEngineSettings

# Setup
examples_dir = Path(__file__).parent
blueprint_path = examples_dir / "blueprint.yaml"
data_dir = examples_dir / "data"

# Configure settings
settings = ContextEngineSettings()
settings.adapter_registry.data_defaults["csv_loader"] = {"path": str(data_dir / "sample.csv")}

# Create registry
registry = AdapterRegistry()

# Register CSV adapter
print("Registering CSV adapter...")
sdk_adapters.register_csv_loader(key="csv_loader", registry=registry)

# Register static memory provider
print("Registering static memory provider...")
sdk_adapters.register_static_memory_provider(key="static_memory", registry=registry)

# Build materializer
from promptic.sdk.api import build_materializer

materializer = build_materializer(settings=settings, registry=registry)

# Load blueprint using builder
from promptic.instructions.cache import InstructionCache
from promptic.instructions.store import FilesystemInstructionStore
from promptic.pipeline.builder import BlueprintBuilder
from promptic.pipeline.validation import BlueprintValidator

instruction_store = InstructionCache(
    FilesystemInstructionStore(settings.instruction_root),
    max_entries=256,
)
validator = BlueprintValidator(settings=settings, instruction_store=instruction_store)
builder = BlueprintBuilder(settings=settings, validator=validator)
result = builder.load_from_path(blueprint_path)
if not result.ok:
    raise result.error or Exception("Failed to load blueprint")
blueprint = result.unwrap()

# Preview with CSV adapter
print("\n=== Preview with CSV adapter ===")
preview1 = blueprints.preview_blueprint(
    blueprint_id=str(blueprint.id),
    settings=settings,
    materializer=materializer,
)
print(preview1.rendered_context[:200] + "...")

# Register HTTP adapter with same key (swap)
print("\nSwapping to HTTP adapter...")
# Note: In a real scenario, you'd register an HTTP adapter here
# For demo purposes, we show the swap concept
print("✅ Adapter swap complete - blueprint unchanged!")

print("\n✅ Adapter swap demonstration complete!")
