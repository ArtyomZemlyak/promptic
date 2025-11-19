#!/usr/bin/env python3
"""Complete end-to-end example demonstrating all library functionality.

This script shows:
- Blueprint authoring and loading
- Adapter registration
- Preview generation
- Pipeline execution
- Log analysis
- Fallback handling
"""

from pathlib import Path

from promptic.adapters.registry import AdapterRegistry
from promptic.instructions.cache import InstructionCache
from promptic.instructions.store import FilesystemInstructionStore
from promptic.pipeline.builder import BlueprintBuilder
from promptic.pipeline.validation import BlueprintValidator
from promptic.sdk import adapters as sdk_adapters
from promptic.sdk import blueprints, pipeline
from promptic.sdk.api import build_materializer
from promptic.settings.base import ContextEngineSettings

# Setup paths
examples_dir = Path(__file__).parent
blueprint_path = examples_dir / "research_flow.yaml"
instructions_dir = examples_dir / "instructions"
data_dir = examples_dir / "data"

# Configure settings
settings = ContextEngineSettings()
settings.instruction_root = instructions_dir
settings.blueprint_root = examples_dir
settings.adapter_registry.data_defaults["csv_loader"] = {"path": str(data_dir / "sources.csv")}

# Create registry and register adapters
print("=== Setting up adapters ===")
registry = AdapterRegistry()
sdk_adapters.register_csv_loader(key="csv_loader", registry=registry)
sdk_adapters.register_static_memory_provider(key="vector_db", registry=registry)
print("✅ Adapters registered")

# Build materializer
materializer = build_materializer(settings=settings, registry=registry)

# Load blueprint
print("\n=== Loading blueprint ===")
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
print(f"✅ Blueprint loaded: {blueprint.name}")

# Preview
print("\n=== Generating preview ===")
# Preview is automatically printed to console with Rich formatting (colors, styles)
preview = blueprints.preview_blueprint(
    blueprint_id=str(blueprint.id),
    settings=settings,
    materializer=materializer,
)
print("✅ Preview generated")
# rendered_context contains plain text version for programmatic use
print(f"Plain text preview length: {len(preview.rendered_context)} characters")

if preview.fallback_events:
    print(f"\n⚠️  {len(preview.fallback_events)} fallback events detected")

# Execute pipeline
print("\n=== Executing pipeline ===")
run = pipeline.run_pipeline(
    blueprint_id=str(blueprint.id),
    settings=settings,
    materializer=materializer,
)
print("✅ Pipeline executed")

# Analyze execution log
print("\n=== Execution Log Analysis ===")
print(f"Total events: {len(run.events)}")
for event in run.events[:5]:  # Show first 5 events
    print(f"  {event.event_type} @ {event.step_id}")

if run.fallback_events:
    print(f"\n⚠️  {len(run.fallback_events)} fallback events during execution")

print("\n✅ End-to-end demonstration complete!")
