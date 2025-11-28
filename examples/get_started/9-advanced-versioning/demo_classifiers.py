#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Example: Classifiers (language, audience, etc.).

This script demonstrates how classifiers create prompt variants:
- Define classifiers with allowed values and defaults
- Filter by classifier when loading
- Handle partial classifier coverage (not all versions have all classifiers)

Usage:
    python demo_classifiers.py
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
from promptic.versioning import ClassifierConfig, VersioningConfig


def main():
    """Demonstrate classifier-based prompt variants."""
    print("=" * 60)
    print("Example 9: Classifiers (Language Variants)")
    print("=" * 60)

    # Define language classifier
    config = VersioningConfig(
        classifiers={
            "lang": ClassifierConfig(
                name="lang",
                values=["en", "ru", "de"],
                default="en",
            )
        }
    )

    # 1. Full classifier coverage
    print("\n" + "-" * 60)
    print("1. Full Classifier Coverage")
    print("-" * 60)

    prompts_dir = script_dir / "prompts_classified"
    print(f"\nDirectory: {prompts_dir}")
    print("Files:")
    print("  - task_en_v1.0.0.md (English v1)")
    print("  - task_ru_v1.0.0.md (Russian v1)")
    print("  - task_en_v2.0.0.md (English v2)")
    print("  - task_ru_v2.0.0.md (Russian v2)")
    print("  - task_de_v2.0.0.md (German v2 only!)")

    # Default classifier (English) - use render with classifier parameter
    print("\n--- Default Classifier (English) ---")
    content = render(
        prompts_dir,
        version="latest",
        classifier={"lang": "en"},
        versioning_config=config,
    )
    print("Config: default classifier = 'en'")
    print("Requested: version='latest', classifier={'lang': 'en'}")
    print(f"\nResult (English v2):\n{content}")

    # Russian classifier
    print("\n--- Russian Classifier ---")
    content = render(
        prompts_dir,
        version="latest",
        classifier={"lang": "ru"},
        versioning_config=config,
    )
    print("Requested: version='latest', classifier={'lang': 'ru'}")
    print(f"\nResult (Russian v2):\n{content}")

    # German classifier
    print("\n--- German Classifier ---")
    content = render(
        prompts_dir,
        version="latest",
        classifier={"lang": "de"},
        versioning_config=config,
    )
    print("Requested: version='latest', classifier={'lang': 'de'}")
    print("Note: German only exists for v2.0.0")
    print(f"\nResult (German v2):\n{content}")

    # 2. Partial classifier coverage
    print("\n" + "-" * 60)
    print("2. Partial Classifier Coverage")
    print("-" * 60)

    prompts_dir = script_dir / "prompts_partial_classifier"
    print(f"\nDirectory: {prompts_dir}")
    print("Files:")
    print("  - task_en_v1.0.0.md (English v1)")
    print("  - task_ru_v1.0.0.md (Russian v1)")
    print("  - task_en_v2.0.0.md (English v2 - NO Russian v2!)")

    # English - has both v1 and v2
    print("\n--- English (has v1 and v2) ---")
    content = render(
        prompts_dir,
        version="latest",
        classifier={"lang": "en"},
        versioning_config=config,
    )
    print("Requested: version='latest', classifier={'lang': 'en'}")
    print(f"\nResult (English v2):\n{content}")

    # Russian - only has v1!
    print("\n--- Russian (only has v1!) ---")
    content = render(
        prompts_dir,
        version="latest",
        classifier={"lang": "ru"},
        versioning_config=config,
    )
    print("Requested: version='latest', classifier={'lang': 'ru'}")
    print("Note: Russian only exists for v1.0.0 - system returns latest WITH Russian")
    print(f"\nResult (Russian v1 - latest version with Russian):\n{content}")

    # 3. Specific version + classifier
    print("\n" + "-" * 60)
    print("3. Specific Version + Classifier")
    print("-" * 60)

    prompts_dir = script_dir / "prompts_classified"
    content = render(
        prompts_dir,
        version="v1",
        classifier={"lang": "ru"},
        versioning_config=config,
    )
    print("Requested: version='v1', classifier={'lang': 'ru'}")
    print(f"\nResult (Russian v1):\n{content}")

    print("\n" + "=" * 60)
    print("✓ All classifier examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
