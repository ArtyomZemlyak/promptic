"""Tests for classifier-based version filtering.

Tests for:
- Classifier extraction from filename (T049)
- Classifier filtering logic (T050)
- ClassifierNotFoundError (T051)
- Multi-classifier scenarios (T052)
- Classifier fallback (T053)
"""

from __future__ import annotations

from pathlib import Path

import pytest


class TestClassifierExtraction:
    """Test classifier extraction from filename (T049)."""

    def test_single_classifier_extraction(self, tmp_path: Path) -> None:
        """Extract single classifier from filename."""
        from promptic.versioning.adapters.scanner import VersionedFileScanner
        from promptic.versioning.config import ClassifierConfig, VersioningConfig

        (tmp_path / "prompt_en_v1.md").write_text("English v1")
        (tmp_path / "prompt_ru_v1.md").write_text("Russian v1")

        config = VersioningConfig(
            classifiers={
                "lang": ClassifierConfig(name="lang", values=["en", "ru"], default="en"),
            }
        )
        scanner = VersionedFileScanner(config=config)

        files = scanner.scan_directory(str(tmp_path))
        versioned = [f for f in files if f.is_versioned]

        # Should have both files with classifiers
        assert len(versioned) == 2
        # Classifier extraction will be implemented in scanner

    def test_multiple_classifiers_extraction(self, tmp_path: Path) -> None:
        """Extract multiple classifiers from filename."""
        from promptic.versioning.adapters.scanner import VersionedFileScanner
        from promptic.versioning.config import ClassifierConfig, VersioningConfig

        # Format: prompt_{lang}_{tone}_v{version}.md
        (tmp_path / "prompt_en_formal_v1.md").write_text("English formal v1")
        (tmp_path / "prompt_ru_casual_v1.md").write_text("Russian casual v1")

        config = VersioningConfig(
            classifiers={
                "lang": ClassifierConfig(name="lang", values=["en", "ru"], default="en"),
                "tone": ClassifierConfig(
                    name="tone", values=["formal", "casual"], default="formal"
                ),
            }
        )
        scanner = VersionedFileScanner(config=config)

        files = scanner.scan_directory(str(tmp_path))
        assert len([f for f in files if f.is_versioned]) == 2

    def test_no_classifier_in_filename(self, tmp_path: Path) -> None:
        """File without classifier should work with default."""
        from promptic.versioning.adapters.scanner import VersionedFileScanner
        from promptic.versioning.config import ClassifierConfig, VersioningConfig

        (tmp_path / "prompt_v1.md").write_text("No classifier")

        config = VersioningConfig(
            classifiers={
                "lang": ClassifierConfig(name="lang", values=["en", "ru"], default="en"),
            }
        )
        scanner = VersionedFileScanner(config=config)

        files = scanner.scan_directory(str(tmp_path))
        versioned = [f for f in files if f.is_versioned]

        assert len(versioned) == 1


class TestClassifierFiltering:
    """Test classifier filtering logic (T050)."""

    def test_filter_by_single_classifier(self, tmp_path: Path) -> None:
        """Filter files by single classifier value."""
        from promptic.versioning.adapters.scanner import VersionedFileScanner
        from promptic.versioning.config import ClassifierConfig, VersioningConfig

        (tmp_path / "prompt_en_v1.md").write_text("English v1")
        (tmp_path / "prompt_ru_v1.md").write_text("Russian v1")
        (tmp_path / "prompt_en_v2.md").write_text("English v2")

        config = VersioningConfig(
            classifiers={
                "lang": ClassifierConfig(name="lang", values=["en", "ru"], default="en"),
            }
        )
        scanner = VersionedFileScanner(config=config)

        # Resolve with classifier filter - will be implemented
        resolved = scanner.resolve_version(str(tmp_path), "latest", classifier={"lang": "ru"})

        assert "ru" in resolved or "prompt_ru_v1.md" in resolved

    def test_filter_by_multiple_classifiers(self, tmp_path: Path) -> None:
        """Filter files by multiple classifier values."""
        from promptic.versioning.adapters.scanner import VersionedFileScanner
        from promptic.versioning.config import ClassifierConfig, VersioningConfig

        (tmp_path / "prompt_en_formal_v1.md").write_text("English formal")
        (tmp_path / "prompt_en_casual_v1.md").write_text("English casual")
        (tmp_path / "prompt_ru_formal_v1.md").write_text("Russian formal")

        config = VersioningConfig(
            classifiers={
                "lang": ClassifierConfig(name="lang", values=["en", "ru"], default="en"),
                "tone": ClassifierConfig(
                    name="tone", values=["formal", "casual"], default="formal"
                ),
            }
        )
        scanner = VersionedFileScanner(config=config)

        resolved = scanner.resolve_version(
            str(tmp_path), "latest", classifier={"lang": "en", "tone": "casual"}
        )

        assert "casual" in resolved

    def test_default_classifier_used_when_not_specified(self, tmp_path: Path) -> None:
        """Default classifier should be used when not specified."""
        from promptic.versioning.adapters.scanner import VersionedFileScanner
        from promptic.versioning.config import ClassifierConfig, VersioningConfig

        (tmp_path / "prompt_en_v1.md").write_text("English v1")
        (tmp_path / "prompt_ru_v1.md").write_text("Russian v1")

        config = VersioningConfig(
            classifiers={
                "lang": ClassifierConfig(name="lang", values=["en", "ru"], default="en"),
            }
        )
        scanner = VersionedFileScanner(config=config)

        # Without classifier, should use default (en)
        resolved = scanner.resolve_version(str(tmp_path), "latest")

        # Should prefer English (default)
        assert "prompt_en_v1.md" in resolved or "en" in resolved


class TestClassifierNotFoundError:
    """Test ClassifierNotFoundError (T051)."""

    def test_error_on_invalid_classifier_value(self, tmp_path: Path) -> None:
        """Raise error when classifier value doesn't exist in any file."""
        from promptic.versioning import ClassifierNotFoundError
        from promptic.versioning.adapters.scanner import VersionedFileScanner
        from promptic.versioning.config import ClassifierConfig, VersioningConfig

        (tmp_path / "prompt_en_v1.md").write_text("English")
        (tmp_path / "prompt_ru_v1.md").write_text("Russian")

        config = VersioningConfig(
            classifiers={
                "lang": ClassifierConfig(name="lang", values=["en", "ru", "de"], default="en"),
            }
        )
        scanner = VersionedFileScanner(config=config)

        # German (de) doesn't exist in any file
        with pytest.raises(ClassifierNotFoundError) as exc_info:
            scanner.resolve_version(str(tmp_path), "latest", classifier={"lang": "de"})

        assert exc_info.value.classifier_name == "lang"
        assert exc_info.value.requested_value == "de"
        assert "en" in exc_info.value.available_values
        assert "ru" in exc_info.value.available_values

    def test_error_message_lists_available_values(self) -> None:
        """Error message should list available classifier values."""
        from promptic.versioning import ClassifierNotFoundError

        error = ClassifierNotFoundError(
            classifier_name="lang",
            requested_value="es",
            available_values=["en", "ru", "de"],
        )

        message = str(error)
        assert "lang" in message
        assert "es" in message
        assert "en" in message or "Available" in message


class TestMultiClassifierScenarios:
    """Integration tests for multi-classifier scenarios (T052)."""

    def test_three_classifiers(self, tmp_path: Path) -> None:
        """Handle three classifiers in filename."""
        from promptic.versioning.adapters.scanner import VersionedFileScanner
        from promptic.versioning.config import ClassifierConfig, VersioningConfig

        # Format: prompt_{lang}_{tone}_{env}_v{version}.md
        (tmp_path / "prompt_en_formal_prod_v1.md").write_text("EN formal prod")
        (tmp_path / "prompt_en_casual_dev_v1.md").write_text("EN casual dev")

        config = VersioningConfig(
            classifiers={
                "lang": ClassifierConfig(name="lang", values=["en", "ru"], default="en"),
                "tone": ClassifierConfig(
                    name="tone", values=["formal", "casual"], default="formal"
                ),
                "env": ClassifierConfig(name="env", values=["prod", "dev"], default="prod"),
            }
        )
        scanner = VersionedFileScanner(config=config)

        resolved = scanner.resolve_version(
            str(tmp_path), "latest", classifier={"lang": "en", "tone": "casual", "env": "dev"}
        )

        assert "casual" in resolved and "dev" in resolved

    def test_partial_classifier_match(self, tmp_path: Path) -> None:
        """Match files with partial classifier specification."""
        from promptic.versioning.adapters.scanner import VersionedFileScanner
        from promptic.versioning.config import ClassifierConfig, VersioningConfig

        (tmp_path / "prompt_en_formal_v1.md").write_text("EN formal")
        (tmp_path / "prompt_en_casual_v1.md").write_text("EN casual")
        (tmp_path / "prompt_ru_formal_v1.md").write_text("RU formal")

        config = VersioningConfig(
            classifiers={
                "lang": ClassifierConfig(name="lang", values=["en", "ru"], default="en"),
                "tone": ClassifierConfig(
                    name="tone", values=["formal", "casual"], default="formal"
                ),
            }
        )
        scanner = VersionedFileScanner(config=config)

        # Only specify lang, use default for tone (formal)
        resolved = scanner.resolve_version(str(tmp_path), "latest", classifier={"lang": "ru"})

        # Should get Russian formal (default tone)
        assert "ru" in resolved


class TestClassifierFallback:
    """Integration tests for classifier fallback behavior (T053)."""

    def test_fallback_to_latest_version_with_classifier(self, tmp_path: Path) -> None:
        """Return latest version that HAS the requested classifier."""
        from promptic.versioning.adapters.scanner import VersionedFileScanner
        from promptic.versioning.config import ClassifierConfig, VersioningConfig

        # Russian exists in v1 but not v2
        (tmp_path / "prompt_en_v1.md").write_text("EN v1")
        (tmp_path / "prompt_ru_v1.md").write_text("RU v1")
        (tmp_path / "prompt_en_v2.md").write_text("EN v2")
        # No prompt_ru_v2.md!

        config = VersioningConfig(
            classifiers={
                "lang": ClassifierConfig(name="lang", values=["en", "ru"], default="en"),
            }
        )
        scanner = VersionedFileScanner(config=config)

        # Request Russian latest - should get v1 (latest with RU)
        resolved = scanner.resolve_version(str(tmp_path), "latest", classifier={"lang": "ru"})

        assert "prompt_ru_v1.md" in resolved

    def test_no_fallback_for_specific_version(self, tmp_path: Path) -> None:
        """Specific version + classifier must match exactly or raise error."""
        from promptic.versioning import VersionNotFoundError
        from promptic.versioning.adapters.scanner import VersionedFileScanner
        from promptic.versioning.config import ClassifierConfig, VersioningConfig

        (tmp_path / "prompt_en_v1.md").write_text("EN v1")
        (tmp_path / "prompt_ru_v1.md").write_text("RU v1")
        (tmp_path / "prompt_en_v2.md").write_text("EN v2")
        # No prompt_ru_v2.md!

        config = VersioningConfig(
            classifiers={
                "lang": ClassifierConfig(name="lang", values=["en", "ru"], default="en"),
            }
        )
        scanner = VersionedFileScanner(config=config)

        # Request specific v2 with Russian - should raise error
        with pytest.raises(VersionNotFoundError):
            scanner.resolve_version(str(tmp_path), "v2", classifier={"lang": "ru"})

    def test_default_classifier_used_in_fallback(self, tmp_path: Path) -> None:
        """Default classifier should not affect fallback behavior."""
        from promptic.versioning.adapters.scanner import VersionedFileScanner
        from promptic.versioning.config import ClassifierConfig, VersioningConfig

        (tmp_path / "prompt_en_v1.md").write_text("EN v1")
        (tmp_path / "prompt_en_v2.md").write_text("EN v2")
        (tmp_path / "prompt_ru_v1.md").write_text("RU v1")

        config = VersioningConfig(
            classifiers={
                "lang": ClassifierConfig(name="lang", values=["en", "ru"], default="en"),
            }
        )
        scanner = VersionedFileScanner(config=config)

        # Without classifier, should get latest English (default)
        resolved = scanner.resolve_version(str(tmp_path), "latest")

        assert "prompt_en_v2.md" in resolved
