#!/usr/bin/env python3
"""Example: Blueprint authoring and preview (User Story 1).

Minimal API usage - just blueprint.yaml file and 3 lines of code:
1. Load blueprint (settings are in blueprint.yaml)
2. Preview (formatted output)
3. Render for LLM (plain text)
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

# Register adapters
registry = AdapterRegistry()
sdk_adapters.register_csv_loader(key="csv_loader", registry=registry)
sdk_adapters.register_static_memory_provider(key="vector_db", registry=registry)

# Minimal API: Load blueprint (auto-discovers paths and settings from blueprint.yaml)
blueprint = load_blueprint(Path(__file__).parent / "simple_blueprint.yaml")

# Create materializer with registry and settings from blueprint
settings = _create_settings_from_blueprint(blueprint)
materializer = build_materializer(settings=settings, registry=registry)

# Preview (formatted terminal output with Rich)
render_preview(blueprint, materializer=materializer)

# Render for LLM (plain text ready for LLM input)
llm_text = render_for_llm(blueprint, materializer=materializer)
print(f"\n✅ LLM-ready text ({len(llm_text)} chars): {llm_text[:200]}...")
