#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Example 7: Variable insertion with hierarchical scope.

This example demonstrates all three variable scoping methods:
- Simple scope: {"var": "value"} - applies globally
- Node scope: {"node.var": "value"} - applies to specific node names
- Path scope: {"root.group.node.var": "value"} - applies at specific hierarchy path

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

from promptic import render


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def main():
    """Demonstrate variable insertion with all three scoping methods."""
    script_dir = Path(__file__).parent.resolve()
    root_path = script_dir / "root.md"

    if not root_path.exists():
        print(f"Error: root.md not found: {root_path}")
        sys.exit(1)

    print("=" * 70)
    print("  Example 7: Variable Insertion with Hierarchical Scope")
    print("=" * 70)

    # Scenario 1: Simple variables only
    print_section("Scenario 1: Simple Variables (Global Scope)")
    print("Variables:")
    print('  - user_name: "Alice"')
    print('  - task_type: "analysis"')

    simple_vars = {
        "user_name": "Alice",
        "task_type": "analysis",
    }

    output1 = render(root_path, vars=simple_vars)
    print("\nRendered output:")
    print(output1)
    print(f"\n[OK] Simple variables applied ({len(output1)} chars)")

    # Scenario 2: Node-scoped variables
    print_section("Scenario 2: Node-Scoped Variables")
    print("Variables:")
    print('  - user_name: "Bob"')
    print('  - task_type: "review"')
    print('  - instructions.format: "detailed"')
    print('  - details.level: "advanced"')

    node_vars = {
        "user_name": "Bob",
        "task_type": "review",
        "instructions.format": "detailed",
        "details.level": "advanced",
    }

    output2 = render(root_path, vars=node_vars)
    print("\nRendered output:")
    print(output2)
    print(f"\n[OK] Node-scoped variables applied ({len(output2)} chars)")

    # Scenario 3: Path-scoped variables (maximum precision)
    print_section("Scenario 3: Path-Scoped Variables (Full Hierarchy)")
    print("Variables:")
    print('  - user_name: "Charlie"')
    print('  - task_type: "design"')
    print('  - instructions.format: "concise"')
    print('  - details.level: "intermediate"')
    print('  - root.group.instructions.style: "technical"')
    print('  - root.templates.details.verbosity: "high"')

    path_vars = {
        "user_name": "Charlie",
        "task_type": "design",
        "instructions.format": "concise",
        "details.level": "intermediate",
        "root.group.instructions.style": "technical",
        "root.templates.details.verbosity": "high",
    }

    output3 = render(root_path, vars=path_vars)
    print("\nRendered output:")
    print(output3)
    print(f"\n[OK] Path-scoped variables applied ({len(output3)} chars)")

    # Scenario 4: File-first mode with variables
    print_section("Scenario 4: File-First Mode with Variables")
    print("Variables:")
    print('  - user_name: "Diana"')
    print('  - task_type: "implementation"')

    file_first_vars = {
        "user_name": "Diana",
        "task_type": "implementation",
    }

    output4 = render(root_path, render_mode="file_first", vars=file_first_vars)
    print("\nRendered output (file-first mode, references preserved):")
    print(output4)
    print(f"\n[OK] File-first with variables applied ({len(output4)} chars)")

    print("\n" + "=" * 70)
    print("  All scenarios completed successfully!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
