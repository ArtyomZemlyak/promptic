#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Example 5: Load and render specific versions of prompts using render().

This script demonstrates how to work with versioned prompts using the render() function.
The render() function automatically resolves versioned hierarchies and their references.

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

    # Method 1: Using render() with version - returns rendered string
    print("\n" + "=" * 60)
    print("Method 1: Using render() with version - Returns String")
    print("=" * 60)

    # Render latest version
    print("\n--- Rendering LATEST version ---\n")
    latest_content = render(prompts_dir, version="latest")
    print(latest_content)
    print(f"\n[OK] Rendered latest version ({len(latest_content)} chars)")

    # Render specific version v1.0.0
    print("\n--- Rendering version v1.0.0 ---\n")
    v1_content = render(prompts_dir, version="v1.0.0")
    print(v1_content)
    print(f"\n[OK] Rendered v1.0.0 ({len(v1_content)} chars)")

    # Render with partial version (v2 resolves to v2.0.0)
    print("\n--- Rendering version v2 (resolves to v2.0.0) ---\n")
    v2_content = render(prompts_dir, version="v2")
    print(v2_content)
    print(f"\n[OK] Rendered v2 ({len(v2_content)} chars)")

    # Method 2: Using render() with variables
    print("\n" + "=" * 60)
    print("Method 2: Using render() with version and variables")
    print("=" * 60)

    print("\n--- Rendering v1.0.0 with variables ---\n")
    v1_with_vars = render(
        prompts_dir, version="v1.0.0", vars={"task_id": "12345", "priority": "high"}
    )
    print(v1_with_vars[:300] + "..." if len(v1_with_vars) > 300 else v1_with_vars)
    print(f"\n[OK] Rendered v1.0.0 with variables ({len(v1_with_vars)} chars)")

    # Method 3: Using render() with export_to to save files
    print("\n" + "=" * 60)
    print("Method 3: Using render() with export_to - Export Files")
    print("=" * 60)

    print("\n--- Exporting v2.0.0 to directory ---\n")
    export_dir = script_dir / "temp_export"

    result = render(prompts_dir, version="v2.0.0", export_to=export_dir, overwrite=True)
    print(f"✓ Exported {len(result.exported_files)} files to: {export_dir}")
    print(f"  Files: {', '.join([Path(f).name for f in result.exported_files])}")

    # Clean up export directory
    import shutil

    shutil.rmtree(export_dir)

    # Optional: load_prompt() for simple file loading (no references resolved)
    print("\n" + "=" * 60)
    print("Optional: load_prompt() for simple file loading")
    print("=" * 60)
    print("\n--- Using load_prompt() (raw file, references not resolved) ---\n")
    raw_content = load_prompt(prompts_dir, version="v1.0.0")
    print(raw_content[:200] + "...")
    print(f"\n[OK] Loaded raw file ({len(raw_content)} chars)")
    print("Note: load_prompt() returns the raw file without resolving references")

    print("\n" + "=" * 60)
    print("✓ All versions rendered successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
