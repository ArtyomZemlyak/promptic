#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Example 6: Export specific versions of prompts.

This script demonstrates how to export specific versions of prompts from a
hierarchical directory structure, preserving the directory structure and
removing version suffixes from filenames.

Usage:
    python export_demo.py
"""

import os
import shutil
import sys
from pathlib import Path

# Add project root to path to import promptic
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent.parent
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

from promptic import cleanup_exported_version, export_version


def print_directory_tree(
    directory: Path, prefix: str = "", max_depth: int = 5, current_depth: int = 0
):
    """Print directory tree structure."""
    if current_depth >= max_depth:
        return

    if not directory.exists():
        return

    entries = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name))

    for i, entry in enumerate(entries):
        is_last = i == len(entries) - 1
        connector = "└── " if is_last else "├── "
        print(f"{prefix}{connector}{entry.name}")

        if entry.is_dir():
            extension = "    " if is_last else "│   "
            print_directory_tree(entry, prefix + extension, max_depth, current_depth + 1)


def main():
    """Export and display different versions of the workflow."""
    script_dir = Path(__file__).parent.resolve()
    prompts_dir = script_dir / "prompts"
    export_base = script_dir / "exported"

    if not prompts_dir.exists():
        print(f"Error: prompts directory not found: {prompts_dir}")
        sys.exit(1)

    # Clean up previous exports
    if export_base.exists():
        print(f"Cleaning up previous exports: {export_base}")
        shutil.rmtree(export_base)

    export_base.mkdir(exist_ok=True)

    print("=" * 70)
    print("Example 6: Version Export")
    print("=" * 70)

    # Export version 1.0.0
    print("\n--- Exporting version v1.0.0 ---\n")
    export_v1_dir = export_base / "workflow_v1"

    result_v1 = export_version(
        source_path=prompts_dir, version_spec="v1.0.0", target_dir=export_v1_dir, overwrite=True
    )

    print(f"✓ Exported {len(result_v1.exported_files)} files to: {export_v1_dir}")
    print(f"  Structure preserved: {result_v1.structure_preserved}")
    print(f"\n  Exported files:")
    for file in result_v1.exported_files:
        rel_path = Path(file).relative_to(export_v1_dir)
        print(f"    - {rel_path}")

    print(f"\n  Directory structure:")
    print_directory_tree(export_v1_dir, "    ")

    print(f"\n  Root prompt content preview:")
    preview = result_v1.root_prompt_content[:300]
    print("    " + "\n    ".join(preview.split("\n")))
    if len(result_v1.root_prompt_content) > 300:
        print("    ...")

    # Export version 2.0.0
    print("\n" + "=" * 70)
    print("\n--- Exporting version v2.0.0 ---\n")
    export_v2_dir = export_base / "workflow_v2"

    result_v2 = export_version(
        source_path=prompts_dir, version_spec="v2.0.0", target_dir=export_v2_dir, overwrite=True
    )

    print(f"✓ Exported {len(result_v2.exported_files)} files to: {export_v2_dir}")
    print(f"  Structure preserved: {result_v2.structure_preserved}")
    print(f"\n  Exported files:")
    for file in result_v2.exported_files:
        rel_path = Path(file).relative_to(export_v2_dir)
        print(f"    - {rel_path}")

    print(f"\n  Directory structure:")
    print_directory_tree(export_v2_dir, "    ")

    print(f"\n  Root prompt content preview:")
    preview = result_v2.root_prompt_content[:300]
    print("    " + "\n    ".join(preview.split("\n")))
    if len(result_v2.root_prompt_content) > 300:
        print("    ...")

    # Compare versions
    print("\n" + "=" * 70)
    print("\n--- Version Comparison ---\n")
    print(f"v1.0.0: {len(result_v1.exported_files)} files")
    print(f"v2.0.0: {len(result_v2.exported_files)} files")
    print(f"\nNote: v2.0.0 includes additional quality/checks.md file")

    # Show how exported files have version suffixes removed
    print("\n" + "=" * 70)
    print("\n--- Version Suffix Removal ---\n")
    print("Original files have version suffixes:")
    print("  - workflow_v1.0.0.md → exported as workflow.md")
    print("  - workflow_v2.0.0.md → exported as workflow.md")
    print("  - tasks/definition_v1.0.0.md → exported as tasks/definition.md")
    print("\nThis allows exported versions to be used directly without modifications!")

    # Explain explicit version references
    print("\n" + "=" * 70)
    print("\n--- Explicit Version References ---\n")
    print("v2.0.0 demonstrates explicit version references:")
    print("  - workflow_v2.0.0.md explicitly references output/format_v1.0.0.md")
    print("  - This means v2.0.0 uses v1.0.0 output format (backward compatibility)")
    print("  - The file is exported as 'output/format_v1.0.0.md' (version suffix kept!)")
    print("  - Automatic resolution of format_v2.0.0.md is skipped to avoid conflicts")
    print("\nThis allows mixing different versions of components in a single workflow!")

    print("\n" + "=" * 70)
    print("✓ All versions exported successfully!")
    print("=" * 70)

    print(f"\nExported directories are located at:")
    print(f"  - {export_v1_dir}")
    print(f"  - {export_v2_dir}")

    print("\nYou can now use these exported versions directly in your application!")


if __name__ == "__main__":
    main()
