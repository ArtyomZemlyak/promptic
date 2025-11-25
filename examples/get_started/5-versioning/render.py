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

    # Method 2: Using render() with export_to for version export
    print("\n" + "=" * 60)
    print("Method 2: Using render() with export_to - Version Export")
    print("=" * 60)

    # AICODE-NOTE: For versioned prompt hierarchies with references, use render()
    # with export_to parameter. This exports the entire hierarchy with resolved
    # references and variable substitution.

    # Export latest version
    print("\n--- Exporting LATEST version ---\n")
    export_dir = script_dir / "temp_export"
    if export_dir.exists():
        import shutil

        shutil.rmtree(export_dir)

    latest_exported = render(prompts_dir, version="latest", export_to=export_dir, overwrite=True)
    print(f"✓ Exported {len(latest_exported.exported_files)} files")
    print(f"Root content preview:\n{latest_exported.root_prompt_content[:200]}...")
    print(f"\n[OK] Exported latest version")

    # Clean up export directory
    import shutil

    shutil.rmtree(export_dir)

    # Show that load_prompt() is still useful for simple loading
    print("\n" + "=" * 60)
    print("Note: For simple loading without references, use load_prompt()")
    print("=" * 60)

    print("\n" + "=" * 60)
    print("✓ All versions loaded and rendered successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
