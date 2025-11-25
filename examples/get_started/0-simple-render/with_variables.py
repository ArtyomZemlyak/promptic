#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Example: Using render() with variable substitution.

This example demonstrates how to pass variables to render() for dynamic content.

Usage:
    python with_variables.py
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


def main():
    """Demonstrate render() with variable substitution."""
    script_dir = Path(__file__).parent.resolve()
    task_path = script_dir / "task.md"

    print("=== Example 0: Render with Variables ===\n")
    print("This example shows how to use variables with render().\n")

    # Render with variables
    # Variables use {{variable_name}} syntax in markdown files
    output = render(
        task_path,
        vars={
            "task_name": "Code Review",
            "user_name": "Alice",
            "priority": "High",
        },
    )

    print("=== Rendered Output (with variables) ===\n")
    print(output)
    print(f"\n[OK] Rendered successfully ({len(output)} chars)")

    # Render with different variables (reusable)
    print("\n=== Second Render (different variables) ===\n")
    output2 = render(
        task_path,
        vars={
            "task_name": "Bug Fix",
            "user_name": "Bob",
            "priority": "Urgent",
        },
    )
    print(output2)
    print(f"\n[OK] Rendered successfully ({len(output2)} chars)")


if __name__ == "__main__":
    main()
