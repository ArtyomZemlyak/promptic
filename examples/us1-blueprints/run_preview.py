#!/usr/bin/env python3
"""Example: Blueprint authoring and preview (User Story 1).

This script demonstrates:
- Loading a blueprint from YAML
- Previewing the merged context
- Showing all referenced instructions
"""

from pathlib import Path

from promptic.instructions.cache import InstructionCache
from promptic.instructions.store import FilesystemInstructionStore
from promptic.pipeline.builder import BlueprintBuilder
from promptic.pipeline.validation import BlueprintValidator
from promptic.sdk import blueprints
from promptic.sdk.api import build_materializer
from promptic.settings.base import ContextEngineSettings

# Setup
examples_dir = Path(__file__).parent
blueprint_path = examples_dir / "simple_blueprint.yaml"
instructions_dir = examples_dir / "instructions"

# Configure settings
settings = ContextEngineSettings()
settings.instruction_root = instructions_dir
settings.blueprint_root = examples_dir

# Build materializer
materializer = build_materializer(settings=settings)

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

print("\nPreviewing blueprint context...")
preview = blueprints.preview_blueprint(
    blueprint_id=str(blueprint.id),
    settings=settings,
    materializer=materializer,
)

print("\n=== Preview Output ===")
print(preview.rendered_context)

if preview.fallback_events:
    print("\n=== Fallback Events ===")
    for event in preview.fallback_events:
        print(f"- {event.mode}: {event.instruction_id}")

print("\n✅ Blueprint preview complete!")
