#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple example: Render markdown file with includes.

This script demonstrates the simplest way to load and render a markdown file
that includes other markdown files using file-first rendering.

Usage:
    python render.py
"""

import sys
from pathlib import Path

# Add project root to path to import promptic
# render.py is at examples/get_started/simple-include/render.py
# So we need to go up 4 levels to reach project root
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent.parent
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

from promptic import render


def main():
    """Load and render main.md with file-first rendering."""
    script_dir = Path(__file__).parent.resolve()
    main_path = script_dir / "main.md"

    if not main_path.exists():
        print(f"Error: main.md not found: {main_path}")
        sys.exit(1)

    # Render with file-first mode (preserves links to other files)
    output = render(main_path, render_mode="file_first")

    print("=== Rendered Output (file-first mode) ===\n")
    print(output)
    print(f"\n[OK] Rendered successfully ({len(output)} chars)")


if __name__ == "__main__":
    main()
