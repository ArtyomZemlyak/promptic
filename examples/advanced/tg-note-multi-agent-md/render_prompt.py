#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimal example: Render agent prompt from markdown file.

This script demonstrates the simplest way to load and render a prompt
using the markdown-first approach where each file is a node.

Usage:
    python render_prompt.py note_creation.md
    python render_prompt.py media_processing.md
    python render_prompt.py git_operations.md
"""

import sys
from pathlib import Path

# AICODE-NOTE: Minimal import - only what's needed for loading and rendering
from promptic.sdk.nodes import load_node_network, render_node_network

# AICODE-NOTE: This example demonstrates the markdown-first approach where
#              each .md file is a node that can reference other .md files.
#              The structure is similar to tg-note where prompts are stored
#              as markdown files with links to other instructions.


def render_prompt(
    prompt_file: str, target_format: str = "markdown", render_mode: str = "file_first"
) -> None:
    """Load and render a prompt from markdown file.

    Args:
        prompt_file: Path to the root markdown prompt file
        target_format: Output format (markdown, yaml, json, jinja2)
        render_mode: Rendering mode (file_first or full)
    """
    script_dir = Path(__file__).parent.resolve()
    prompt_path = script_dir / prompt_file

    if not prompt_path.exists():
        print(f"Error: Prompt file not found: {prompt_path}")
        print(f"Available prompts: note_creation.md, media_processing.md, git_operations.md")
        sys.exit(1)

    # Load network from markdown file (minimal code - just load and render)
    network = load_node_network(prompt_path)

    # Render with specified format and mode
    # AICODE-NOTE: render_mode="file_first" preserves links, render_mode="full" inlines content
    #              target_format determines output format (markdown, yaml, json, jinja2)
    output = render_node_network(
        network,
        target_format=target_format,
        render_mode=render_mode,
    )

    print(f"=== Rendered prompt: {prompt_file} (format={target_format}, mode={render_mode}) ===\n")
    print(output)
    print(f"\n[OK] Prompt rendered ({len(output)} chars)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python render_prompt.py <prompt_file.md> [format] [mode]")
        print("Available prompts: note_creation.md, media_processing.md, git_operations.md")
        print("Formats: markdown, yaml, json, jinja2 (default: markdown)")
        print("Modes: file_first, full (default: file_first)")
        sys.exit(1)

    target_format = sys.argv[2] if len(sys.argv) > 2 else "markdown"
    render_mode = sys.argv[3] if len(sys.argv) > 3 else "file_first"

    render_prompt(sys.argv[1], target_format=target_format, render_mode=render_mode)
