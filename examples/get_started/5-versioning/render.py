#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Example 5: Load and render specific versions of prompts.

This script demonstrates how to load and render specific versions of prompts from a
hierarchical directory structure with versioned markdown files.

You can use either load_prompt() for simple loading or render() for full rendering
with variable substitution and format conversion.

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

from promptic import load_prompt, render


def main():
    """Load and render different versions of the prompt."""
    script_dir = Path(__file__).parent.resolve()
    prompts_dir = script_dir / "prompts"

    if not prompts_dir.exists():
        print(f"Error: prompts directory not found: {prompts_dir}")
        sys.exit(1)

    print("=" * 60)
    print("Example 5: Versioned Prompt Loading and Rendering")
    print("=" * 60)

    # Method 1: Using load_prompt() for simple loading
    print("\n" + "=" * 60)
    print("Method 1: Using load_prompt() - Simple Loading")
    print("=" * 60)

    # Load latest version (v2.0.0)
    print("\n--- Loading LATEST version ---\n")
    latest_content = load_prompt(prompts_dir, version="latest")
    print(latest_content)
    print(f"\n[OK] Loaded latest version ({len(latest_content)} chars)")

    # Load specific version v1.0.0
    print("\n--- Loading version v1.0.0 ---\n")
    v1_content = load_prompt(prompts_dir, version="v1.0.0")
    print(v1_content)
    print(f"\n[OK] Loaded v1.0.0 ({len(v1_content)} chars)")

    # Method 2: Using render() for full rendering with version support
    print("\n" + "=" * 60)
    print("Method 2: Using render() - Full Rendering")
    print("=" * 60)

    # Render latest version
    print("\n--- Rendering LATEST version ---\n")
    latest_rendered = render(prompts_dir, version="latest")
    print(latest_rendered)
    print(f"\n[OK] Rendered latest version ({len(latest_rendered)} chars)")

    # Render specific version v1.0.0
    print("\n--- Rendering version v1.0.0 ---\n")
    v1_rendered = render(prompts_dir, version="v1.0.0")
    print(v1_rendered)
    print(f"\n[OK] Rendered v1.0.0 ({len(v1_rendered)} chars)")

    # Render with partial version (v2 resolves to v2.0.0)
    print("\n--- Rendering version v2 (resolves to v2.0.0) ---\n")
    v2_rendered = render(prompts_dir, version="v2")
    print(v2_rendered)
    print(f"\n[OK] Rendered v2 ({len(v2_rendered)} chars)")

    # Render with version and format conversion
    print("\n--- Rendering v1.0.0 as YAML ---\n")
    v1_yaml = render(prompts_dir, version="v1.0.0", target_format="yaml")
    print(v1_yaml[:300] + "..." if len(v1_yaml) > 300 else v1_yaml)
    print(f"\n[OK] Rendered v1.0.0 as YAML ({len(v1_yaml)} chars)")

    print("\n" + "=" * 60)
    print("✓ All versions loaded and rendered successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
