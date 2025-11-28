#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Example: Custom version delimiters.

This script demonstrates how to use different delimiters for version detection:
- Underscore (_): task_v1.0.0.md (default)
- Hyphen (-): task-v1.0.0.md
- Dot (.): task.v1.0.0.md
- Multiple delimiters: mixed conventions in one directory

Usage:
    python demo_delimiters.py
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
from promptic.versioning import VersioningConfig


def main():
    """Demonstrate different version delimiters."""
    print("=" * 60)
    print("Example 9: Custom Version Delimiters")
    print("=" * 60)

    # 1. Default underscore delimiter
    print("\n" + "-" * 60)
    print("1. Underscore Delimiter (Default)")
    print("-" * 60)

    prompts_dir = script_dir / "prompts_underscore"
    # No config needed - underscore is the default
    content = render(prompts_dir, version="latest")
    print(f"Directory: {prompts_dir}")
    print(f"Files: task_v1.0.0.md, task_v2.0.0.md")
    print(f"\nLatest version content:\n{content}")

    # 2. Hyphen delimiter
    print("\n" + "-" * 60)
    print("2. Hyphen Delimiter")
    print("-" * 60)

    prompts_dir = script_dir / "prompts_hyphen"
    config = VersioningConfig(delimiter="-")
    content = render(prompts_dir, version="latest", versioning_config=config)
    print(f"Directory: {prompts_dir}")
    print(f"Files: task-v1.0.0.md, task-v2.0.0.md")
    print(f"Config: VersioningConfig(delimiter='-')")
    print(f"\nLatest version content:\n{content}")

    # 3. Dot delimiter
    print("\n" + "-" * 60)
    print("3. Dot Delimiter")
    print("-" * 60)

    prompts_dir = script_dir / "prompts_dot"
    config = VersioningConfig(delimiter=".")
    content = render(prompts_dir, version="latest", versioning_config=config)
    print(f"Directory: {prompts_dir}")
    print(f"Files: task.v1.0.0.md, task.v2.0.0.md")
    print(f"Config: VersioningConfig(delimiter='.')")
    print(f"\nLatest version content:\n{content}")

    # 4. Multiple delimiters (mixed naming)
    print("\n" + "-" * 60)
    print("4. Multiple Delimiters (Mixed Naming)")
    print("-" * 60)

    prompts_dir = script_dir / "prompts_mixed"
    config = VersioningConfig(delimiters=["_", "-"])
    content = render(prompts_dir, version="latest", versioning_config=config)
    print(f"Directory: {prompts_dir}")
    print(f"Files: task_v1.0.0.md (underscore), task-v2.0.0.md (hyphen)")
    print(f"Config: VersioningConfig(delimiters=['_', '-'])")
    print(f"\nLatest version content:\n{content}")

    # 5. Load specific version with different delimiter
    print("\n" + "-" * 60)
    print("5. Load Specific Version (v1)")
    print("-" * 60)

    config = VersioningConfig(delimiters=["_", "-"])
    content = render(prompts_dir, version="v1", versioning_config=config)
    print(f"Requested version: v1")
    print(f"\nVersion 1 content:\n{content}")

    print("\n" + "=" * 60)
    print("✓ All delimiter examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
