#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Example 5: Load specific versions of prompts.

This script demonstrates how to load specific versions of prompts from a
hierarchical directory structure with versioned markdown files.

Usage:
    python render.py
"""

import sys
from pathlib import Path

# Add project root to path to import promptic
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent.parent
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

from promptic import load_prompt


def main():
    """Load and display different versions of the prompt."""
    script_dir = Path(__file__).parent.resolve()
    prompts_dir = script_dir / "prompts"

    if not prompts_dir.exists():
        print(f"Error: prompts directory not found: {prompts_dir}")
        sys.exit(1)

    print("=" * 60)
    print("Example 5: Versioned Prompt Loading")
    print("=" * 60)

    # Load latest version (v2.0.0)
    print("\n--- Loading LATEST version ---\n")
    latest_content = load_prompt(prompts_dir, version="latest")
    print(latest_content)
    print(f"\n[OK] Loaded latest version ({len(latest_content)} chars)")

    # Load specific version v1.0.0
    print("\n" + "=" * 60)
    print("\n--- Loading version v1.0.0 ---\n")
    v1_content = load_prompt(prompts_dir, version="v1.0.0")
    print(v1_content)
    print(f"\n[OK] Loaded v1.0.0 ({len(v1_content)} chars)")

    # Load specific version v2.0.0
    print("\n" + "=" * 60)
    print("\n--- Loading version v2.0.0 ---\n")
    v2_content = load_prompt(prompts_dir, version="v2.0.0")
    print(v2_content)
    print(f"\n[OK] Loaded v2.0.0 ({len(v2_content)} chars)")

    # Load with partial version (v2 resolves to v2.0.0)
    print("\n" + "=" * 60)
    print("\n--- Loading version v2 (resolves to v2.0.0) ---\n")
    v2_short_content = load_prompt(prompts_dir, version="v2")
    print(v2_short_content)
    print(f"\n[OK] Loaded v2 ({len(v2_short_content)} chars)")

    print("\n" + "=" * 60)
    print("✓ All versions loaded successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
