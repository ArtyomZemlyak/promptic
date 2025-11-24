"""Contract test for promptic public API.

This test verifies that the public API exports only the expected functions
after cleanup, and that removed functions are no longer accessible.
"""

import promptic


def test_public_api_exports_only_expected_functions():
    """Test that __all__ contains only expected exports after cleanup."""
    expected_exports = {
        "__version__",
        "load_prompt",
        "export_version",
        "cleanup_exported_version",
    }

    actual_exports = set(promptic.__all__)

    # Verify only expected exports are present
    assert actual_exports == expected_exports, (
        f"Public API exports do not match expected.\n"
        f"Expected: {sorted(expected_exports)}\n"
        f"Actual: {sorted(actual_exports)}\n"
        f"Missing: {sorted(expected_exports - actual_exports)}\n"
        f"Extra: {sorted(actual_exports - expected_exports)}"
    )


def test_removed_blueprint_functions_not_exported():
    """Test that blueprint-related functions are not in __all__."""
    removed_blueprint_functions = {
        "bootstrap_runtime",
        "load_blueprint",
        "preview_blueprint",
        "render_for_llm",
        "render_instruction",
        "render_preview",
    }

    actual_exports = set(promptic.__all__)

    for func_name in removed_blueprint_functions:
        assert (
            func_name not in actual_exports
        ), f"Removed blueprint function '{func_name}' should not be in __all__"


def test_expected_functions_are_accessible():
    """Test that all expected functions can be accessed from promptic module."""
    # Test that expected functions exist and are callable
    assert hasattr(promptic, "__version__")
    assert isinstance(promptic.__version__, str)

    assert hasattr(promptic, "load_prompt")
    assert callable(promptic.load_prompt)

    assert hasattr(promptic, "export_version")
    assert callable(promptic.export_version)

    assert hasattr(promptic, "cleanup_exported_version")
    assert callable(promptic.cleanup_exported_version)


def test_removed_functions_not_accessible():
    """Test that removed blueprint functions are not accessible from promptic."""
    removed_functions = [
        "bootstrap_runtime",
        "load_blueprint",
        "preview_blueprint",
        "render_for_llm",
        "render_instruction",
        "render_preview",
    ]

    for func_name in removed_functions:
        assert not hasattr(
            promptic, func_name
        ), f"Removed function '{func_name}' should not be accessible from promptic"
