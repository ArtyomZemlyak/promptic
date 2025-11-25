#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Example 8: Export with variable substitution using render().

This script demonstrates how to use render() with export_to and variables
for exporting prompts with variable substitution at different scopes.

Usage:
    python export_demo.py
"""

import shutil
import sys
from pathlib import Path

# Add project root to path to import promptic
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent.parent
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

from promptic import render

# Setup paths
base_dir = Path(__file__).parent
export_dir = base_dir / "export_output"

# Clean previous export
if export_dir.exists():
    shutil.rmtree(export_dir)

# Variables with different scopes
variables = {
    # Simple (Global)
    "global_var": "I am global",
    "shared_var": "I am default shared",
    # Node Scoped
    "root.root_specific": "I am root specific",
    "child.child_specific": "I am child specific",
    # Path Scoped (overrides global/node)
    # Note: The path follows the reference graph, not just directory structure.
    # root.md references group/child.md directly, so the path is root.child
    "root.child.shared_var": "I am child shared (path scoped)",
    "root.child.path_only": "I am path only",
}

print("Exporting with variables using render()...")
result = render(
    base_dir / "root.md", version="latest", export_to=export_dir, vars=variables, overwrite=True
)

print("\nExport successful!")
print(f"Files exported: {len(result.exported_files)}")

print("\n--- content of export_output/root.md ---")
print((export_dir / "root.md").read_text())

print("\n--- content of export_output/group/child.md ---")
print((export_dir / "group/child.md").read_text())

# Cleanup
shutil.rmtree(export_dir)
