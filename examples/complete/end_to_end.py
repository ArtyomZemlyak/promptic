#!/usr/bin/env python3
"""Complete end-to-end example demonstrating all library functionality.

This script shows:
- Blueprint authoring and loading (settings in blueprint.yaml)
- Adapter registration
- Preview generation (formatted terminal output)
- Render for LLM (plain text ready for LLM input)
- Instruction rendering
- Fallback handling

Note: This library focuses on context construction only. Pipeline execution
is handled by external agent frameworks.
"""

from pathlib import Path

from promptic.adapters.registry import AdapterRegistry
from promptic.sdk import adapters as sdk_adapters
from promptic.sdk.api import (
    _create_settings_from_blueprint,
    build_materializer,
    load_blueprint,
    render_for_llm,
    render_instruction,
    render_preview,
)

# Create registry and register adapters
print("=== Setting up adapters ===")
registry = AdapterRegistry()
sdk_adapters.register_csv_loader(key="csv_loader", registry=registry)
sdk_adapters.register_static_memory_provider(key="vector_db", registry=registry)
print("✅ Adapters registered")

# Minimal API: Load blueprint (settings are in blueprint.yaml)
print("\n=== Loading blueprint ===")
blueprint = load_blueprint(Path(__file__).parent / "research_flow.yaml")
print(f"✅ Blueprint loaded: {blueprint.name}")
print(f"   Steps: {len(blueprint.steps)}")
print(f"   Data slots: {len(blueprint.data_slots)}")
print(f"   Memory slots: {len(blueprint.memory_slots)}")

# Create materializer with registry and settings from blueprint
settings = _create_settings_from_blueprint(blueprint)
materializer = build_materializer(settings=settings, registry=registry)

# Preview (formatted terminal output with Rich)
print("\n=== Generating preview (formatted) ===")
render_preview(blueprint, materializer=materializer)
print(f"✅ Preview generated")

# Render for LLM (plain text ready for LLM input)
print("\n=== Rendering for LLM (plain text) ===")
llm_text = render_for_llm(blueprint, materializer=materializer)
print(f"✅ LLM-ready text generated")
print(f"   Text length: {len(llm_text)} characters")
print(f"   First 200 chars: {llm_text[:200]}...")

# Render specific instruction
if blueprint.steps:
    first_step = blueprint.steps[0]
    if first_step.instruction_refs:
        instruction_id = first_step.instruction_refs[0].instruction_id
        print(f"\n=== Rendering instruction: {instruction_id} ===")
        instruction_text = render_instruction(
            blueprint=blueprint,
            instruction_id=instruction_id,
            step_id=first_step.step_id,
            materializer=materializer,
        )
        print(f"✅ Instruction rendered")
        print(f"   Length: {len(instruction_text)} characters")
        print(f"   Preview: {instruction_text[:150]}...")

print("\n✅ End-to-end demonstration complete!")
print("\nNote: This library constructs contexts for LLM input.")
print("      Pipeline execution is handled by external agent frameworks.")
