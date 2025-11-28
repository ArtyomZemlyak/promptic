#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Example: Configuration options overview.

This script demonstrates all configuration options:
- VersioningConfig (BaseModel, no auto-resolution)
- VersioningSettings (BaseSettings, env var resolution)
- Embedding config in host application settings

Usage:
    python demo_config.py
"""

import os
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
    """Demonstrate configuration options."""
    print("=" * 60)
    print("Example 9: Configuration Options")
    print("=" * 60)

    # 1. VersioningConfig (explicit, no auto-resolution)
    print("\n" + "-" * 60)
    print("1. VersioningConfig (BaseModel)")
    print("-" * 60)

    config = VersioningConfig(
        delimiter="-",
        include_prerelease=False,
        prerelease_order=["alpha", "beta", "rc"],
        classifiers={
            "lang": ClassifierConfig(
                name="lang",
                values=["en", "ru"],
                default="en",
            )
        },
    )

    print("VersioningConfig is a Pydantic BaseModel (NOT BaseSettings).")
    print("This means it does NOT auto-resolve from environment variables.")
    print("\nBenefit: No namespace conflicts when embedding in host apps.")
    print(f"\nConfig created:\n{config}")

    # 2. All configuration options
    print("\n" + "-" * 60)
    print("2. Available Configuration Options")
    print("-" * 60)

    print(
        """
VersioningConfig options:

  delimiter: str = "_"
      Single delimiter for version detection.
      Options: "_", ".", "-"

  delimiters: list[str] | None = None
      Multiple delimiters (overrides 'delimiter' when set).
      Example: ["_", "-"] for mixed naming conventions.

  version_pattern: str | None = None
      Custom regex pattern for version detection.
      Must use named capture groups: (?P<major>\\d+), etc.
      Example: r"_rev(?P<major>\\d+)"

  include_prerelease: bool = False
      Include pre-releases in "latest" resolution.
      Pre-releases: -alpha, -beta, -rc

  prerelease_order: list[str] = ["alpha", "beta", "rc"]
      Order for comparing pre-releases (earliest to latest).
      Customize for non-standard labels: ["dev", "alpha", "beta", "rc"]

  classifiers: dict[str, ClassifierConfig] | None = None
      Define variant classifiers (language, audience, etc.).
      Each classifier has: name, values, default.
"""
    )

    # 3. VersioningSettings (env var resolution)
    print("\n" + "-" * 60)
    print("3. VersioningSettings (BaseSettings)")
    print("-" * 60)

    print("VersioningSettings extends VersioningConfig with BaseSettings.")
    print("It reads from environment variables with PROMPTIC_ prefix:")
    print()
    print("  PROMPTIC_DELIMITER='_' | '.' | '-'")
    print("  PROMPTIC_INCLUDE_PRERELEASE='true' | 'false'")
    print('  PROMPTIC_PRERELEASE_ORDER=\'["alpha", "beta", "rc"]\'')
    print()
    print("Note: VersioningSettings requires pydantic-settings to be installed.")

    # Try to import VersioningSettings
    try:
        from promptic.versioning import VersioningSettings

        if VersioningSettings is not None:
            # Set env vars for demo
            os.environ["PROMPTIC_DELIMITER"] = "-"
            os.environ["PROMPTIC_INCLUDE_PRERELEASE"] = "true"

            settings = VersioningSettings()
            print(f"\nSettings from env vars:")
            print(f"  delimiter: {settings.delimiter}")
            print(f"  include_prerelease: {settings.include_prerelease}")

            # Clean up
            del os.environ["PROMPTIC_DELIMITER"]
            del os.environ["PROMPTIC_INCLUDE_PRERELEASE"]
        else:
            print("\n⚠ VersioningSettings is None (pydantic-settings not installed)")
    except ImportError:
        print("\n⚠ pydantic-settings not installed, VersioningSettings not available")

    # 4. Embedding in host application
    print("\n" + "-" * 60)
    print("4. Embedding in Host Application")
    print("-" * 60)

    print(
        """
For applications with their own pydantic-settings:

    from pydantic_settings import BaseSettings
    from promptic.versioning import VersioningConfig

    class MyAppSettings(BaseSettings):
        # Embed promptic config as nested model
        promptic: VersioningConfig = VersioningConfig()

        # Your app's settings
        api_key: str
        debug: bool = False

    # Usage
    settings = MyAppSettings()
    content = render("prompts/", versioning_config=settings.promptic)

Key benefit: VersioningConfig won't conflict with your app's
environment variable namespace because it's a BaseModel,
not a BaseSettings.
"""
    )

    # 5. Config validation
    print("\n" + "-" * 60)
    print("5. Configuration Validation")
    print("-" * 60)

    print("VersioningConfig validates all inputs at construction time.\n")

    # Invalid delimiter
    print("Invalid delimiter:")
    try:
        VersioningConfig(delimiter="@")
    except ValueError as e:
        print(f"  ✓ Rejected: {e}")

    # Invalid pattern
    print("\nInvalid pattern (missing named groups):")
    try:
        VersioningConfig(version_pattern=r"_v(\d+)")
    except ValueError as e:
        print(f"  ✓ Rejected: {e}")

    # Invalid classifier
    print("\nInvalid classifier (default not in values):")
    try:
        VersioningConfig(
            classifiers={
                "lang": ClassifierConfig(
                    name="lang",
                    values=["en", "ru"],
                    default="de",  # Not in values!
                )
            }
        )
    except ValueError as e:
        print(f"  ✓ Rejected: {e}")

    # 6. Using config with render()
    print("\n" + "-" * 60)
    print("6. Using Config with render()")
    print("-" * 60)

    prompts_dir = script_dir / "prompts_hyphen"
    config = VersioningConfig(delimiter="-")

    content = render(prompts_dir, version="latest", versioning_config=config)
    print(f"render('{prompts_dir}', version='latest', versioning_config=config)")
    print(f"\nResult:\n{content}")

    print("\n" + "=" * 60)
    print("✓ All configuration examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
