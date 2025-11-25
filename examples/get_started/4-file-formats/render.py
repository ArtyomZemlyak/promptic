#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Example: Render file with all supported formats in full render mode.

This script demonstrates how to render a file network with all supported
target formats (yaml, markdown, json) in full render mode.

Usage:
    python render.py
"""

import sys
from pathlib import Path

# Add project root to path to import promptic
# render.py is at examples/get_started/4-file-formats/render.py
# So we need to go up 4 levels to reach project root
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent.parent
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

from promptic import render


def main():
    """Render root.yaml with all target formats in full render mode."""
    script_dir = Path(__file__).parent.resolve()
    root_path = script_dir / "root.yaml"

    # Check if file exists
    if not root_path.exists():
        print(f"Error: root.yaml not found: {root_path}")
        sys.exit(1)

    # Define all supported target formats
    target_formats = ["yaml", "markdown", "json"]

    # Render with each target format
    for target_format in target_formats:
        print("=" * 60)
        print(f"Rendering to {target_format.upper()} format (full mode)")
        print("=" * 60)
        output = render(root_path, target_format=target_format)
        print(output)
        print(f"\n[OK] Rendered to {target_format} successfully ({len(output)} chars)\n")


if __name__ == "__main__":
    main()
