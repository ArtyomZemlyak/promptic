#!/usr/bin/env python3
"""Example: Blueprint authoring and preview (User Story 1).

This script demonstrates:
- Loading a blueprint from YAML
- Previewing the merged context
- Showing all referenced instructions
"""

from pathlib import Path

from promptic.adapters.registry import AdapterRegistry
from promptic.instructions.cache import InstructionCache
from promptic.instructions.store import FilesystemInstructionStore
from promptic.pipeline.builder import BlueprintBuilder
from promptic.pipeline.validation import BlueprintValidator
from promptic.sdk import adapters as sdk_adapters
from promptic.sdk import blueprints
from promptic.sdk.api import build_materializer
from promptic.settings.base import ContextEngineSettings

# Setup
examples_dir = Path(__file__).parent
blueprint_path = examples_dir / "simple_blueprint.yaml"
settings_path = examples_dir / "settings.yaml"

# Load settings from YAML file
settings = ContextEngineSettings.from_yaml(settings_path)

# Create registry and register adapters
registry = AdapterRegistry()
sdk_adapters.register_csv_loader(key="csv_loader", registry=registry)
sdk_adapters.register_static_memory_provider(key="vector_db", registry=registry)

# Build materializer with registry
materializer = build_materializer(settings=settings, registry=registry)

# Build builder to load blueprint from path
instruction_store = InstructionCache(
    FilesystemInstructionStore(settings.instruction_root),
    max_entries=256,
)
validator = BlueprintValidator(settings=settings, instruction_store=instruction_store)
builder = BlueprintBuilder(settings=settings, validator=validator)

# Load blueprint from path
print("Loading blueprint from:", blueprint_path)
result = builder.load_from_path(blueprint_path)
if not result.ok:
    raise result.error or Exception("Failed to load blueprint")
blueprint = result.unwrap()

# Calculate relative path from blueprint_root for preview
print("\nPreviewing blueprint context...")
# Preview is automatically printed to console with Rich formatting (colors, styles)
# rendered_context contains plain text version for programmatic use
preview = blueprints.preview_blueprint(
    blueprint_id="simple_blueprint",
    settings=settings,
    materializer=materializer,
)

if preview.fallback_events:
    print("\n=== Fallback Events ===")
    for event in preview.fallback_events:
        print(f"- {event.mode}: {event.instruction_id}")

print("\n✅ Blueprint preview complete!")
