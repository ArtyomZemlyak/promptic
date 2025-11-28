"""Unit tests for versioning configuration models.

Tests for:
- ClassifierConfig validation (T005)
- VersioningConfig validation (T006)
- VersioningSettings environment variable resolution (T007)
"""

from __future__ import annotations

import os
from unittest import mock

import pytest
from pydantic import ValidationError


class TestClassifierConfig:
    """Test ClassifierConfig validation (T005)."""

    def test_valid_classifier_config(self) -> None:
        """Valid classifier config should be accepted."""
        from promptic.versioning.config import ClassifierConfig

        config = ClassifierConfig(name="lang", values=["en", "ru", "de"], default="en")

        assert config.name == "lang"
        assert config.values == ["en", "ru", "de"]
        assert config.default == "en"

    def test_default_must_be_in_values(self) -> None:
        """Default value must be present in allowed values."""
        from promptic.versioning.config import ClassifierConfig

        with pytest.raises(ValidationError) as exc_info:
            ClassifierConfig(name="lang", values=["en", "ru"], default="de")

        assert "default" in str(exc_info.value).lower()

    def test_empty_values_rejected(self) -> None:
        """Empty values list should be rejected."""
        from promptic.versioning.config import ClassifierConfig

        with pytest.raises(ValidationError):
            ClassifierConfig(name="lang", values=[], default="en")

    def test_empty_name_rejected(self) -> None:
        """Empty classifier name should be rejected."""
        from promptic.versioning.config import ClassifierConfig

        with pytest.raises(ValidationError):
            ClassifierConfig(name="", values=["en"], default="en")

    def test_classifier_config_is_frozen(self) -> None:
        """ClassifierConfig should be immutable (frozen)."""
        from promptic.versioning.config import ClassifierConfig

        config = ClassifierConfig(name="lang", values=["en", "ru"], default="en")

        with pytest.raises(ValidationError):
            config.name = "other"  # type: ignore[misc]

    def test_duplicate_values_allowed(self) -> None:
        """Duplicate values in list should be allowed (pydantic default behavior)."""
        from promptic.versioning.config import ClassifierConfig

        # Not strictly forbidden, but typically undesirable
        config = ClassifierConfig(name="lang", values=["en", "en", "ru"], default="en")
        assert config.values == ["en", "en", "ru"]


class TestVersioningConfig:
    """Test VersioningConfig validation (T006)."""

    def test_default_config(self) -> None:
        """Default configuration should have sensible defaults."""
        from promptic.versioning.config import VersioningConfig

        config = VersioningConfig()

        assert config.delimiter == "_"
        assert config.delimiters is None
        assert config.version_pattern is None
        assert config.include_prerelease is False
        assert config.prerelease_order == ["alpha", "beta", "rc"]
        assert config.classifiers is None

    def test_valid_delimiter_underscore(self) -> None:
        """Underscore delimiter should be accepted."""
        from promptic.versioning.config import VersioningConfig

        config = VersioningConfig(delimiter="_")
        assert config.delimiter == "_"

    def test_valid_delimiter_dot(self) -> None:
        """Dot delimiter should be accepted."""
        from promptic.versioning.config import VersioningConfig

        config = VersioningConfig(delimiter=".")
        assert config.delimiter == "."

    def test_valid_delimiter_hyphen(self) -> None:
        """Hyphen delimiter should be accepted."""
        from promptic.versioning.config import VersioningConfig

        config = VersioningConfig(delimiter="-")
        assert config.delimiter == "-"

    def test_invalid_delimiter_rejected(self) -> None:
        """Invalid delimiter should be rejected."""
        from promptic.versioning.config import VersioningConfig

        with pytest.raises(ValidationError) as exc_info:
            VersioningConfig(delimiter="@")

        assert "delimiter" in str(exc_info.value).lower()

    def test_valid_delimiters_list(self) -> None:
        """Valid delimiters list should be accepted."""
        from promptic.versioning.config import VersioningConfig

        config = VersioningConfig(delimiters=["_", "-"])
        assert config.delimiters == ["_", "-"]

    def test_invalid_delimiters_list_rejected(self) -> None:
        """Invalid delimiter in list should be rejected."""
        from promptic.versioning.config import VersioningConfig

        with pytest.raises(ValidationError):
            VersioningConfig(delimiters=["_", "@"])

    def test_valid_version_pattern(self) -> None:
        """Valid version pattern with named groups should be accepted."""
        from promptic.versioning.config import VersioningConfig

        config = VersioningConfig(version_pattern=r"_rev(?P<major>\d+)")
        assert config.version_pattern == r"_rev(?P<major>\d+)"

    def test_invalid_version_pattern_no_major_group(self) -> None:
        """Pattern without major named group should be rejected."""
        from promptic.versioning.config import VersioningConfig

        with pytest.raises(ValidationError) as exc_info:
            VersioningConfig(version_pattern=r"_rev(\d+)")

        assert "major" in str(exc_info.value).lower()

    def test_invalid_version_pattern_bad_regex(self) -> None:
        """Invalid regex pattern should be rejected."""
        from promptic.versioning.config import VersioningConfig

        with pytest.raises(ValidationError):
            VersioningConfig(version_pattern=r"[invalid(regex")

    def test_config_with_classifiers(self) -> None:
        """Config with classifiers should be valid."""
        from promptic.versioning.config import ClassifierConfig, VersioningConfig

        config = VersioningConfig(
            delimiter="-",
            classifiers={
                "lang": ClassifierConfig(name="lang", values=["en", "ru"], default="en"),
            },
        )

        assert config.classifiers is not None
        assert "lang" in config.classifiers
        assert config.classifiers["lang"].default == "en"

    def test_config_is_frozen(self) -> None:
        """VersioningConfig should be immutable (frozen)."""
        from promptic.versioning.config import VersioningConfig

        config = VersioningConfig()

        with pytest.raises(ValidationError):
            config.delimiter = "-"  # type: ignore[misc]

    def test_custom_prerelease_order(self) -> None:
        """Custom prerelease order should be accepted."""
        from promptic.versioning.config import VersioningConfig

        config = VersioningConfig(prerelease_order=["dev", "alpha", "beta", "rc", "preview"])
        assert config.prerelease_order == ["dev", "alpha", "beta", "rc", "preview"]


class TestVersioningSettings:
    """Test VersioningSettings env var resolution (T007)."""

    def test_settings_loads_from_env(self) -> None:
        """Settings should load values from environment variables."""
        from promptic.versioning.config import VersioningSettings

        with mock.patch.dict(
            os.environ,
            {
                "PROMPTIC_DELIMITER": "-",
                "PROMPTIC_INCLUDE_PRERELEASE": "true",
            },
        ):
            settings = VersioningSettings()

            assert settings.delimiter == "-"
            assert settings.include_prerelease is True

    def test_settings_default_when_no_env(self) -> None:
        """Settings should use defaults when no env vars set."""
        from promptic.versioning.config import VersioningSettings

        # Clear any existing PROMPTIC_ env vars
        env_copy = {k: v for k, v in os.environ.items() if not k.startswith("PROMPTIC_")}

        with mock.patch.dict(os.environ, env_copy, clear=True):
            settings = VersioningSettings()

            assert settings.delimiter == "_"
            assert settings.include_prerelease is False

    def test_settings_env_prefix(self) -> None:
        """Settings should use PROMPTIC_ prefix for env vars."""
        from promptic.versioning.config import VersioningSettings

        # Test that OTHER_DELIMITER is ignored
        with mock.patch.dict(
            os.environ,
            {
                "OTHER_DELIMITER": "-",
                "DELIMITER": ".",
            },
        ):
            settings = VersioningSettings()
            # Should use default, not the env vars without PROMPTIC_ prefix
            assert settings.delimiter == "_"

    def test_settings_inherits_from_versioning_config(self) -> None:
        """VersioningSettings should inherit all VersioningConfig fields."""
        from promptic.versioning.config import VersioningConfig, VersioningSettings

        # Check that all VersioningConfig fields are present in VersioningSettings
        config_fields = set(VersioningConfig.model_fields.keys())
        settings_fields = set(VersioningSettings.model_fields.keys())

        assert config_fields.issubset(settings_fields)

    def test_settings_validates_delimiter_from_env(self) -> None:
        """Settings should validate delimiter even when from env."""
        from promptic.versioning.config import VersioningSettings

        with mock.patch.dict(os.environ, {"PROMPTIC_DELIMITER": "@"}):
            with pytest.raises(ValidationError):
                VersioningSettings()
