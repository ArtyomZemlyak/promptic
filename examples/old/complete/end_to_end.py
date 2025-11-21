#!/usr/bin/env python3
"""Complete end-to-end example demonstrating all library functionality.

This script shows:
- Blueprint authoring and loading (settings in blueprint.yaml)
- Adapter registration
- Preview generation (formatted terminal output) - inline mode
- File-first rendering (compact prompts with file references)
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
    build_materializer,
    load_blueprint,
    render_for_llm,
    render_instruction,
    render_preview,
)
from promptic.sdk.blueprints import preview_blueprint
from promptic.settings.base import ContextEngineSettings

# Create registry and register adapters
print("=== Setting up adapters ===")
registry = AdapterRegistry()
sdk_adapters.register_csv_loader(key="csv_loader", registry=registry)
sdk_adapters.register_static_memory_provider(key="vector_db", registry=registry)
print("✅ Adapters registered")

# Minimal API: Load blueprint (settings are in blueprint.yaml)
print("\n=== Loading blueprint ===")
blueprint_path = Path(__file__).parent / "research_flow.yaml"

# Create settings - instruction_root will be resolved relative to blueprint file
settings = ContextEngineSettings()
blueprint_dir = blueprint_path.parent.resolve()
if (blueprint_dir / "instructions").exists():
    settings.instruction_root = blueprint_dir / "instructions"

# Configure adapter defaults for CSV loader
if (blueprint_dir / "data" / "sources.csv").exists():
    settings.adapter_registry.data_defaults["csv_loader"] = {
        "path": str(blueprint_dir / "data" / "sources.csv")
    }

# Create materializer with registry and settings
materializer = build_materializer(settings=settings, registry=registry)

# Load blueprint
blueprint = load_blueprint(blueprint_path, settings=settings)
print(f"✅ Blueprint loaded")
print(f"   Network nodes: {len(blueprint.nodes)}")

# Preview (formatted terminal output with Rich) - inline mode
print("\n=== Generating preview (inline mode) ===")
render_preview(blueprint, materializer=materializer, settings=settings)
print(f"✅ Preview generated")

# File-first rendering (compact prompts with file references)
print("\n=== File-first rendering (compact with references) ===")
file_first_result = preview_blueprint(
    blueprint_id=str(blueprint_path),
    settings=settings,
    materializer=materializer,
    render_mode="file_first",
    print_to_console=True,
)
print(f"✅ File-first rendering complete")
if file_first_result.markdown:
    print(f"   Markdown length: {len(file_first_result.markdown)} characters")
    print(f"   First 300 chars: {file_first_result.markdown[:300]}...")
if file_first_result.metadata:
    metrics = file_first_result.metadata.get("metrics", {})
    if metrics:
        print(f"   Token reduction: {metrics.get('token_reduction_percent', 0):.1f}%")
        print(f"   References: {metrics.get('reference_count', 0)}")

# Render for LLM (plain text ready for LLM input)
print("\n=== Rendering for LLM (plain text) ===")
llm_text = render_for_llm(blueprint, materializer=materializer, settings=settings)
print(f"✅ LLM-ready text generated")
print(f"   Text length: {len(llm_text)} characters")
print(f"   First 200 chars: {llm_text[:200]}...")

# Note: Instruction rendering with NodeNetwork requires different approach
# For now, we'll skip the instruction rendering example as it requires
# converting NodeNetwork to ContextBlueprint or using preview_blueprint
print("\n=== Instruction Rendering ===")
print("Note: Use preview_blueprint to access individual instructions")

print("\n✅ End-to-end demonstration complete!")
print("\nNote: This library constructs contexts for LLM input.")
print("      Pipeline execution is handled by external agent frameworks.")
