#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Example: Render agent prompt with file_first mode.

This script demonstrates how to render a prompt for one of the agents
using file_first rendering mode, which produces compact prompts with
file references instead of full instruction content.

Usage:
    python render_agent_prompt.py note_creation
    python render_agent_prompt.py media_processing
    python render_agent_prompt.py git_operations
"""

import sys
from pathlib import Path

from promptic.adapters.registry import AdapterRegistry
from promptic.sdk.api import build_materializer
from promptic.sdk.blueprints import preview_blueprint
from promptic.settings.base import ContextEngineSettings

# AICODE-NOTE: This example demonstrates the tg-note multi-agent use case
#              where multiple agents share common instructions while each
#              has its own root prompt and specific instructions.


def render_agent_prompt(agent_name: str) -> None:
    """Render agent prompt with file_first mode.

    Args:
        agent_name: Name of the agent (note_creation, media_processing, git_operations)
    """
    # Determine blueprint path
    script_dir = Path(__file__).parent.resolve()
    blueprint_path = script_dir / "agents" / f"{agent_name}.yaml"

    if not blueprint_path.exists():
        print(f"Error: Blueprint not found: {blueprint_path}")
        print(f"Available agents: note_creation, media_processing, git_operations")
        sys.exit(1)

    # Create settings
    settings = ContextEngineSettings()
    blueprint_dir = blueprint_path.parent.parent.resolve()
    instructions_dir = blueprint_dir / "instructions"
    if instructions_dir.exists():
        settings.instruction_root = instructions_dir

    # Build materializer with settings
    registry = AdapterRegistry()
    materializer = build_materializer(settings=settings, registry=registry)

    # Render with file_first mode
    print(f"=== Rendering {agent_name} agent prompt (file_first mode) ===\n")
    result = preview_blueprint(
        blueprint_id=str(blueprint_path.resolve()),
        settings=settings,
        materializer=materializer,
        render_mode="file_first",
        print_to_console=False,
    )

    if result.markdown:
        print("=== File-First Markdown Output ===\n")
        print(result.markdown)
        print("\n" + "=" * 60 + "\n")

        # Print metadata if available
        if result.metadata:
            print("=== Metadata ===")
            metrics = result.metadata.get("metrics", {})
            if metrics:
                print(f"Token reduction: {metrics.get('token_reduction_percent', 0):.1f}%")
                print(f"References: {metrics.get('reference_count', 0)}")
                print(f"Before tokens: {metrics.get('before_tokens', 0)}")
                print(f"After tokens: {metrics.get('after_tokens', 0)}")
            print("\n" + "=" * 60 + "\n")

        print(f"[OK] File-first markdown rendered ({len(result.markdown)} chars)")
    else:
        print("[ERROR] Failed to render file-first markdown")
        if result.warnings:
            print("Warnings:")
            for warning in result.warnings:
                print(f"  - {warning}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python render_agent_prompt.py <agent_name>")
        print("Available agents: note_creation, media_processing, git_operations")
        sys.exit(1)

    agent_name = sys.argv[1]
    render_agent_prompt(agent_name)
