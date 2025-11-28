#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Example: Pre-release version handling.

This script demonstrates how pre-release versions work:
- Pre-releases (-alpha, -beta, -rc) are excluded from "latest" by default
- include_prerelease=True includes them in resolution
- Explicit version requests always work
- Pre-release ordering: alpha < beta < rc < release

Usage:
    python demo_prereleases.py
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
    """Demonstrate pre-release version handling."""
    print("=" * 60)
    print("Example 9: Pre-release Version Handling")
    print("=" * 60)

    prompts_dir = script_dir / "prompts_prerelease"

    print(f"\nDirectory: {prompts_dir}")
    print("Files:")
    print("  - task_v1.0.0.md (release)")
    print("  - task_v1.1.0-alpha.md (prerelease)")
    print("  - task_v1.1.0-beta.md (prerelease)")
    print("  - task_v1.1.0-rc.1.md (prerelease)")
    print("  - task_v1.1.0.md (release)")
    print("  - task_v2.0.0-alpha.md (prerelease)")

    # 1. Default behavior: prereleases excluded
    print("\n" + "-" * 60)
    print("1. Default Behavior (prereleases EXCLUDED)")
    print("-" * 60)

    # Use render for version-aware loading
    content = render(prompts_dir, version="latest")
    print("Config: default (include_prerelease=False)")
    print("Requested: version='latest'")
    print("\nNote: By default, 'latest' returns the highest version found.")
    print("Pre-release exclusion depends on the scanner implementation.")
    print(f"\nResult:\n{content}")

    # 2. Include prereleases
    print("\n" + "-" * 60)
    print("2. Include Pre-releases")
    print("-" * 60)

    config = VersioningConfig(include_prerelease=True)
    content = render(prompts_dir, version="latest", versioning_config=config)
    print("Config: VersioningConfig(include_prerelease=True)")
    print("Requested: version='latest'")
    print(f"\nResult:\n{content}")

    # 3. Explicit prerelease request
    print("\n" + "-" * 60)
    print("3. Explicit Pre-release Request")
    print("-" * 60)

    content = render(prompts_dir, version="v1.1.0-beta")
    print("Requested: version='v1.1.0-beta' (explicit)")
    print(f"\nResult:\n{content}")

    # 4. Request alpha of v2
    print("\n" + "-" * 60)
    print("4. Request v2.0.0-alpha Explicitly")
    print("-" * 60)

    content = render(prompts_dir, version="v2.0.0-alpha")
    print("Requested: version='v2.0.0-alpha' (explicit)")
    print(f"\nResult:\n{content}")

    # 5. Pre-release ordering
    print("\n" + "-" * 60)
    print("5. Pre-release Ordering")
    print("-" * 60)

    print("\nDefault ordering: alpha < beta < rc < release")
    print("\nFor version v1.1.0:")
    print("  v1.1.0-alpha < v1.1.0-beta < v1.1.0-rc.1 < v1.1.0")
    print("\nCustom ordering example:")
    print("  config = VersioningConfig(prerelease_order=['dev', 'alpha', 'beta', 'rc'])")
    print("  This would make 'dev' the earliest prerelease type.")

    # 6. Load v1.0.0 (stable)
    print("\n" + "-" * 60)
    print("6. Load Specific Stable Version")
    print("-" * 60)

    content = render(prompts_dir, version="v1.0.0")
    print("Requested: version='v1.0.0'")
    print(f"\nResult:\n{content}")

    # 7. Load v1.1.0 (stable release)
    print("\n" + "-" * 60)
    print("7. Load v1.1.0 (Stable Release)")
    print("-" * 60)

    content = render(prompts_dir, version="v1.1.0")
    print("Requested: version='v1.1.0'")
    print(f"\nResult:\n{content}")

    print("\n" + "=" * 60)
    print("✓ All pre-release examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
