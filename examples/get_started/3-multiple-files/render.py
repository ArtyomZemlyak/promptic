#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Example: Render multiple root files with shared and specific includes.

This script demonstrates how to render different root files that share some
common includes and have specific ones.

Usage:
    python render.py
"""

import sys
from pathlib import Path

# Add project root to path to import promptic
# render.py is at examples/get_started/3-multiple-files/render.py
# So we need to go up 4 levels to reach project root
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent.parent
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

from promptic import render


def main():
    """Render both root files and print results."""
    script_dir = Path(__file__).parent.resolve()

    # Define both root files
    root1_path = script_dir / "root-1.md"
    root2_path = script_dir / "root-2.md"

    # Check if files exist
    if not root1_path.exists():
        print(f"Error: root-1.md not found: {root1_path}")
        sys.exit(1)
    if not root2_path.exists():
        print(f"Error: root-2.md not found: {root2_path}")
        sys.exit(1)

    # Render first root file
    print("=" * 60)
    print("Rendering root-1.md (with common.md)")
    print("=" * 60)
    output1 = render(root1_path)
    print(output1)
    print(f"\n[OK] Rendered root-1.md successfully ({len(output1)} chars)\n")

    # Render second root file
    print("=" * 60)
    print("Rendering root-2.md (with common.md and specific-2.md)")
    print("=" * 60)
    output2 = render(root2_path)
    print(output2)
    print(f"\n[OK] Rendered root-2.md successfully ({len(output2)} chars)\n")


if __name__ == "__main__":
    main()
