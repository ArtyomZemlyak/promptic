#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Example: Custom version patterns.

This script demonstrates how to use custom regex patterns for version detection:
- Non-standard versioning like _rev42, _build123
- Custom patterns must use named capture groups
- Pattern validation and error handling

Usage:
    python demo_custom_patterns.py
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
    """Demonstrate custom version patterns."""
    print("=" * 60)
    print("Example 9: Custom Version Patterns")
    print("=" * 60)

    prompts_dir = script_dir / "prompts_custom_pattern"

    print(f"\nDirectory: {prompts_dir}")
    print("Files:")
    print("  - task_rev1.md (revision 1)")
    print("  - task_rev2.md (revision 2)")
    print("  - task_rev42.md (revision 42)")

    # 1. Custom pattern for revision-based versioning
    print("\n" + "-" * 60)
    print("1. Revision-Based Versioning Pattern")
    print("-" * 60)

    # Pattern explanation:
    # _rev(?P<major>\d+) matches:
    # - _rev - literal text
    # - (?P<major>\d+) - named capture group "major" for the revision number
    config = VersioningConfig(version_pattern=r"_rev(?P<major>\d+)")

    content = render(prompts_dir, version="latest", versioning_config=config)
    print("Pattern: r'_rev(?P<major>\\d+)'")
    print("Requested: version='latest'")
    print(f"\nResult (rev42 - highest number):\n{content}")

    # 2. How version detection works
    print("\n" + "-" * 60)
    print("2. How Custom Pattern Detection Works")
    print("-" * 60)

    print("\nThe custom pattern extracts version components from filenames:")
    print("  - task_rev1.md  → major=1  → v1.0.0")
    print("  - task_rev2.md  → major=2  → v2.0.0")
    print("  - task_rev42.md → major=42 → v42.0.0")
    print("\nThe 'latest' version resolves to v42.0.0 (highest major).")
    print("\nNote: Specific version requests (e.g., 'rev2') still use semver format.")
    print("To load rev2, use version='v2' or version='v2.0.0'.")

    # 3. Load specific revision using semver format
    print("\n" + "-" * 60)
    print("3. Load Specific Revision (using semver)")
    print("-" * 60)

    content = render(prompts_dir, version="v2", versioning_config=config)
    print("Pattern maps rev2 → v2.0.0")
    print("Requested: version='v2'")
    print(f"\nResult:\n{content}")

    # 4. Pattern requirements
    print("\n" + "-" * 60)
    print("4. Pattern Requirements")
    print("-" * 60)

    print("\nCustom patterns MUST use named capture groups:")
    print("  ✓ (?P<major>\\d+) - required, captures major version")
    print("  ✓ (?P<minor>\\d+) - optional")
    print("  ✓ (?P<patch>\\d+) - optional")
    print("  ✓ (?P<prerelease>[a-zA-Z0-9.]+) - optional")
    print("\nExamples:")
    print("  r'_v(?P<major>\\d+)' - simple major version")
    print("  r'_v(?P<major>\\d+)\\.(?P<minor>\\d+)' - major.minor")
    print("  r'_build(?P<major>\\d+)' - build numbers")
    print("  r'_rev(?P<major>\\d+)' - revision numbers")

    # 5. Invalid pattern (demonstration)
    print("\n" + "-" * 60)
    print("5. Invalid Pattern Detection")
    print("-" * 60)

    print("\nPatterns without named groups are rejected:")
    print("  ✗ r'_v(\\d+)' - missing (?P<major>...)")
    print("\nAttempting to create invalid config...")

    try:
        # This will raise a validation error
        _invalid_config = VersioningConfig(version_pattern=r"_v(\d+)")
        print("ERROR: Should have raised an exception!")
    except ValueError as e:
        print(f"✓ Correctly rejected: {e}")

    print("\n" + "=" * 60)
    print("✓ All custom pattern examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
