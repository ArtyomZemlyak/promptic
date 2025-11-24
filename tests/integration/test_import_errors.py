"""Test that removed modules cannot be imported after cleanup.

This test file verifies that blueprint, adapter, and token counting modules
raise ImportError after they are removed from the codebase.
"""

import pytest


class TestBlueprintImportErrors:
    """Test that blueprint imports raise ImportError after removal."""

    def test_import_load_blueprint_from_main_module_raises_error(self):
        """Test that importing load_blueprint from promptic raises ImportError."""
        with pytest.raises(ImportError):
            from promptic import load_blueprint  # noqa: F401

    def test_import_blueprint_package_raises_error(self):
        """Test that importing promptic.blueprints raises ImportError."""
        with pytest.raises(ImportError):
            import promptic.blueprints  # noqa: F401

    def test_import_blueprint_models_raises_error(self):
        """Test that importing blueprint models raises ImportError."""
        with pytest.raises(ImportError):
            from promptic.blueprints import ContextBlueprint  # noqa: F401

    def test_import_sdk_blueprints_raises_error(self):
        """Test that importing sdk.blueprints module raises ImportError."""
        with pytest.raises(ImportError):
            import promptic.sdk.blueprints  # noqa: F401

    def test_import_bootstrap_runtime_raises_error(self):
        """Test that importing bootstrap_runtime raises ImportError."""
        with pytest.raises(ImportError):
            from promptic import bootstrap_runtime  # noqa: F401

    def test_import_preview_blueprint_raises_error(self):
        """Test that importing preview_blueprint raises ImportError."""
        with pytest.raises(ImportError):
            from promptic import preview_blueprint  # noqa: F401

    def test_import_render_for_llm_raises_error(self):
        """Test that importing render_for_llm raises ImportError."""
        with pytest.raises(ImportError):
            from promptic import render_for_llm  # noqa: F401

    def test_import_render_instruction_raises_error(self):
        """Test that importing render_instruction raises ImportError."""
        with pytest.raises(ImportError):
            from promptic import render_instruction  # noqa: F401

    def test_import_render_preview_raises_error(self):
        """Test that importing render_preview raises ImportError."""
        with pytest.raises(ImportError):
            from promptic import render_preview  # noqa: F401


class TestAdapterImportErrors:
    """Test that adapter imports raise ImportError after removal."""

    def test_import_adapter_registry_raises_error(self):
        """Test that importing AdapterRegistry raises ImportError."""
        with pytest.raises(ImportError):
            from promptic.adapters import AdapterRegistry  # noqa: F401

    def test_import_adapter_package_raises_error(self):
        """Test that importing promptic.adapters raises ImportError."""
        with pytest.raises(ImportError):
            import promptic.adapters  # noqa: F401

    def test_import_sdk_adapters_raises_error(self):
        """Test that importing sdk.adapters module raises ImportError."""
        with pytest.raises(ImportError):
            import promptic.sdk.adapters  # noqa: F401


class TestTokenCountingImportErrors:
    """Test that token counting imports raise ImportError after removal."""

    def test_import_token_counter_raises_error(self):
        """Test that importing TokenCounter raises ImportError."""
        with pytest.raises(ImportError):
            from promptic.token_counting import TokenCounter  # noqa: F401

    def test_import_token_counting_package_raises_error(self):
        """Test that importing promptic.token_counting raises ImportError."""
        with pytest.raises(ImportError):
            import promptic.token_counting  # noqa: F401


class TestSettingsImportErrors:
    """Test that settings imports raise ImportError after removal."""

    def test_import_settings_raises_error(self):
        """Test that importing promptic.settings raises ImportError."""
        with pytest.raises(ImportError):
            import promptic.settings  # noqa: F401

    def test_import_context_engine_settings_raises_error(self):
        """Test that importing ContextEngineSettings raises ImportError."""
        with pytest.raises(ImportError):
            from promptic.settings.base import ContextEngineSettings  # noqa: F401


class TestInstructionsImportErrors:
    """Test that instructions imports raise ImportError after removal."""

    def test_import_instructions_raises_error(self):
        """Test that importing promptic.instructions raises ImportError."""
        with pytest.raises(ImportError):
            import promptic.instructions  # noqa: F401

    def test_import_instruction_store_raises_error(self):
        """Test that importing instruction store raises ImportError."""
        with pytest.raises(ImportError):
            from promptic.instructions.store import FilesystemInstructionStore  # noqa: F401
