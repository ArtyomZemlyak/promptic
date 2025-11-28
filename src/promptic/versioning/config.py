"""Versioning configuration models.

# AICODE-NOTE: This module contains pydantic models for versioning configuration.
# VersioningConfig is a BaseModel (not BaseSettings) intentionally to prevent
# auto-resolution conflicts when promptic is embedded in host applications.
# VersioningSettings extends BaseSettings for applications that want env var resolution.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

if TYPE_CHECKING:
    from typing import Self


class ClassifierConfig(BaseModel):
    """
    Configuration for a single classifier.

    # AICODE-NOTE: Classifiers create prompt variants within a version. For example,
    # language classifiers allow `prompt_en_v1.md` and `prompt_ru_v1.md`.

    Attributes:
        name: Classifier name (e.g., "lang", "tone")
        values: Allowed values (e.g., ["en", "ru", "de"])
        default: Default value (must be in values)

    Example:
        >>> ClassifierConfig(name="lang", values=["en", "ru", "de"], default="en")
        >>> ClassifierConfig(name="tone", values=["formal", "casual"], default="formal")
    """

    model_config = ConfigDict(frozen=True)

    name: str
    values: list[str]
    default: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate classifier name is non-empty."""
        if not v or not v.strip():
            raise ValueError("Classifier name must be non-empty")
        return v

    @field_validator("values")
    @classmethod
    def validate_values(cls, v: list[str]) -> list[str]:
        """Validate values list is non-empty."""
        if not v:
            raise ValueError("Classifier values must be non-empty list")
        return v

    @model_validator(mode="after")
    def validate_default_in_values(self) -> Self:
        """Validate that default value is present in allowed values."""
        if self.default not in self.values:
            raise ValueError(f"Default '{self.default}' must be in values: {self.values}")
        return self


class VersioningConfig(BaseModel):
    """
    Versioning configuration - NOT auto-resolved from environment variables.

    # AICODE-NOTE: This is a BaseModel (not BaseSettings) intentionally.
    # Host applications can embed this model in their own pydantic-settings
    # without conflicts from automatic environment variable resolution.

    Attributes:
        delimiter: Single delimiter for version detection (default: "_")
        delimiters: Multiple delimiters for mixed directories (overrides delimiter)
        version_pattern: Custom regex pattern (must use named capture groups)
        include_prerelease: Include prereleases in "latest" resolution
        prerelease_order: Order for prerelease comparison
        classifiers: Classifier definitions

    Example:
        >>> config = VersioningConfig(
        ...     delimiter="-",
        ...     include_prerelease=True,
        ...     classifiers={
        ...         "lang": ClassifierConfig(name="lang", values=["en", "ru"], default="en")
        ...     }
        ... )
    """

    model_config = ConfigDict(frozen=True)

    # Delimiter configuration
    delimiter: str = "_"
    delimiters: list[str] | None = None

    # Version pattern (optional custom regex)
    version_pattern: str | None = None

    # Prerelease handling
    include_prerelease: bool = False
    prerelease_order: list[str] = ["alpha", "beta", "rc"]

    # Classifiers
    classifiers: dict[str, ClassifierConfig] | None = None

    @field_validator("delimiter")
    @classmethod
    def validate_delimiter(cls, v: str) -> str:
        """Validate delimiter is one of the allowed values."""
        if v not in ("_", ".", "-"):
            raise ValueError(f"Invalid delimiter: {v}. Must be '_', '.', or '-'")
        return v

    @field_validator("delimiters")
    @classmethod
    def validate_delimiters(cls, v: list[str] | None) -> list[str] | None:
        """Validate all delimiters in list are valid."""
        if v is not None:
            for d in v:
                if d not in ("_", ".", "-"):
                    raise ValueError(f"Invalid delimiter in list: {d}. Must be '_', '.', or '-'")
        return v

    @field_validator("version_pattern")
    @classmethod
    def validate_pattern(cls, v: str | None) -> str | None:
        """Validate custom pattern is valid regex with required named groups."""
        if v is not None:
            try:
                compiled = re.compile(v)
                if "major" not in compiled.groupindex:
                    raise ValueError("Pattern must contain (?P<major>...) named group")
            except re.error as e:
                raise ValueError(f"Invalid regex pattern: {e}")
        return v


# Import pydantic-settings only when needed to avoid import errors
# if pydantic-settings is not installed
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict

    class VersioningSettings(VersioningConfig, BaseSettings):
        """
        Versioning configuration with environment variable resolution.

        # AICODE-NOTE: This class is opt-in. promptic itself never instantiates it.
        # Applications that want env var resolution can use this instead of
        # VersioningConfig.

        Uses PROMPTIC_ prefix for all environment variables.

        Environment variables:
            PROMPTIC_DELIMITER: "_" | "." | "-"
            PROMPTIC_INCLUDE_PRERELEASE: "true" | "false"
            PROMPTIC_PRERELEASE_ORDER: '["alpha", "beta", "rc"]' (JSON)

        Example:
            >>> # From environment
            >>> # export PROMPTIC_DELIMITER="-"
            >>> # export PROMPTIC_INCLUDE_PRERELEASE=true
            >>> settings = VersioningSettings()
            >>> assert settings.delimiter == "-"
            >>> assert settings.include_prerelease == True
        """

        model_config = SettingsConfigDict(
            env_prefix="PROMPTIC_",
            env_nested_delimiter="__",
        )

except ImportError:
    # pydantic-settings not installed, VersioningSettings not available
    VersioningSettings = None  # type: ignore[misc, assignment]
