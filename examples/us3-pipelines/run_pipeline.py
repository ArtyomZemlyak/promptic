#!/usr/bin/env python3
"""Example: Pipeline execution (User Story 3).

This script demonstrates:
- Running a 5-step hierarchical pipeline
- Step 3 loops over items
- Fetches instruction for each item
- Execution log shows instruction IDs per item
"""

from pathlib import Path

from promptic.adapters.registry import AdapterRegistry
from promptic.instructions.cache import InstructionCache
from promptic.instructions.store import FilesystemInstructionStore
from promptic.pipeline.builder import BlueprintBuilder
from promptic.pipeline.validation import BlueprintValidator
from promptic.sdk import blueprints, pipeline
from promptic.sdk.api import build_materializer
from promptic.settings.base import ContextEngineSettings

# Setup
examples_dir = Path(__file__).parent
blueprint_path = examples_dir / "hierarchical_blueprint.yaml"

# Configure settings
settings = ContextEngineSettings()
settings.blueprint_root = examples_dir

# Create registry and materializer
registry = AdapterRegistry()
materializer = build_materializer(settings=settings, registry=registry)

# Load blueprint
print("Loading blueprint...")
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

# Execute pipeline
print("\nExecuting pipeline...")
run = pipeline.run_pipeline(
    blueprint_id=str(blueprint.id),
    settings=settings,
    materializer=materializer,
)

# Display execution log
print("\n=== Execution Log ===")
for event in run.events:
    print(f"{event.event_type}: {event.step_id}")
    if hasattr(event, "instruction_id"):
        print(f"  Instruction: {event.instruction_id}")

print("\n✅ Pipeline execution complete!")
