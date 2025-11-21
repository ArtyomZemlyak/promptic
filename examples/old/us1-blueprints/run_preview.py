#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Example: Blueprint authoring and preview (User Story 1).

Minimal API usage - just blueprint.yaml file and a few lines of code:
1. Load blueprint (settings are in blueprint.yaml)
2. Preview (formatted output) - inline mode
3. File-first rendering (compact prompts with file references)
4. Render for LLM (plain text)
"""

from pathlib import Path

from promptic.adapters.registry import AdapterRegistry
from promptic.sdk import adapters as sdk_adapters
from promptic.sdk.api import build_materializer, load_blueprint, render_for_llm, render_preview
from promptic.sdk.blueprints import preview_blueprint
from promptic.settings.base import ContextEngineSettings

# Register adapters (optional - not needed for this simple example)
registry = AdapterRegistry()

# Minimal API: Load blueprint (auto-discovers paths and settings from blueprint.yaml)
blueprint_path = Path(__file__).parent / "simple_blueprint.yaml"

# Create settings - instruction_root will be resolved relative to blueprint file
settings = ContextEngineSettings()
blueprint_dir = blueprint_path.parent.resolve()
if (blueprint_dir / "instructions").exists():
    settings.instruction_root = blueprint_dir / "instructions"

# Create materializer with registry and settings
materializer = build_materializer(settings=settings, registry=registry)

# Load blueprint
blueprint = load_blueprint(blueprint_path, settings=settings)

# Preview (formatted terminal output with Rich) - inline mode
print("=== Inline Preview ===")
render_preview(blueprint, materializer=materializer, settings=settings)

# File-first rendering (compact prompts with file references)
print("\n=== File-First Rendering ===")
file_first_result = preview_blueprint(
    blueprint_id=str(blueprint_path),
    settings=settings,
    materializer=materializer,
    render_mode="file_first",
    print_to_console=True,
)
if file_first_result.markdown:
    print(f"\n[OK] File-first markdown ({len(file_first_result.markdown)} chars)")
    print(
        file_first_result.markdown[:500] + "..."
        if len(file_first_result.markdown) > 500
        else file_first_result.markdown
    )

# Render for LLM (plain text ready for LLM input)
print("\n=== Render for LLM ===")
llm_text = render_for_llm(blueprint, materializer=materializer, settings=settings)
print(f"[OK] LLM-ready text ({len(llm_text)} chars): {llm_text[:200]}...")
