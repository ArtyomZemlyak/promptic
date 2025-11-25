#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple example: Using render() function for one-step rendering.

This is the simplest and recommended way to use promptic.
Just call render() with a file path and get the rendered output.

Usage:
    python simple_render.py
"""

import sys
from pathlib import Path

# Add project root to path to import promptic
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent.parent
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

from promptic import render


def main():
    """Demonstrate simple usage of render() function."""
    script_dir = Path(__file__).parent.resolve()
    task_path = script_dir / "task.md"

    print("=== Example 0: Simple Render ===\n")
    print("This example shows the simplest way to use promptic.\n")

    # Simple render: load and render in one call
    # By default, render() uses:
    #   - target_format="markdown" (output format)
    #   - render_mode="full" (inline all references)
    output = render(task_path)

    print("=== Rendered Output ===\n")
    print(output)
    print(f"\n[OK] Rendered successfully ({len(output)} chars)")

    # You can also convert to different formats
    print("\n=== Convert to YAML ===\n")
    yaml_output = render(task_path, target_format="yaml")
    print(yaml_output[:300] + "..." if len(yaml_output) > 300 else yaml_output)


if __name__ == "__main__":
    main()
