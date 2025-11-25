"""Test that examples 003-006 still work after blueprint/adapter/token removal.

This test verifies that the core functionality used in examples continues to work
after cleanup, ensuring no regressions were introduced.
"""

import subprocess
import sys
from pathlib import Path
from typing import Tuple


def get_examples_dir() -> Path:
    """Get the examples directory path."""
    # test file is at tests/integration/test_examples_after_cleanup.py
    # examples are at examples/get_started/
    test_dir = Path(__file__).parent
    project_root = test_dir.parent.parent
    return project_root / "examples" / "get_started"


def run_example(example_script: Path) -> Tuple[int, str, str]:
    """Run an example script and return exit code, stdout, stderr."""
    result = subprocess.run(
        [sys.executable, str(example_script)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.returncode, result.stdout, result.stderr


class TestExample003MultipleFiles:
    """Test that example 003 (multiple files) works after cleanup."""

    def test_example_003_runs_successfully(self):
        """Test that example 003 runs without errors."""
        examples_dir = get_examples_dir()
        example_script = examples_dir / "3-multiple-files" / "render.py"

        assert example_script.exists(), f"Example script not found: {example_script}"

        exit_code, stdout, stderr = run_example(example_script)

        assert exit_code == 0, (
            f"Example 003 failed with exit code {exit_code}\n"
            f"stdout: {stdout}\n"
            f"stderr: {stderr}"
        )

        # Verify output contains expected content
        assert "Rendering root-1.md" in stdout
        assert "Rendering root-2.md" in stdout
        assert "[OK] Rendered" in stdout


class TestExample004FileFormats:
    """Test that example 004 (file formats) works after cleanup."""

    def test_example_004_runs_successfully(self):
        """Test that example 004 runs without errors."""
        examples_dir = get_examples_dir()
        example_script = examples_dir / "4-file-formats" / "render.py"

        assert example_script.exists(), f"Example script not found: {example_script}"

        exit_code, stdout, stderr = run_example(example_script)

        assert exit_code == 0, (
            f"Example 004 failed with exit code {exit_code}\n"
            f"stdout: {stdout}\n"
            f"stderr: {stderr}"
        )

        # Verify output contains expected formats
        assert "Rendering to YAML format" in stdout
        assert "Rendering to MARKDOWN format" in stdout
        assert "Rendering to JSON format" in stdout
        assert "[OK] Rendered" in stdout


class TestExample005Versioning:
    """Test that example 005 (versioning) works after cleanup."""

    def test_example_005_runs_successfully(self):
        """Test that example 005 runs without errors."""
        examples_dir = get_examples_dir()
        example_script = examples_dir / "5-versioning" / "render.py"

        assert example_script.exists(), f"Example script not found: {example_script}"

        exit_code, stdout, stderr = run_example(example_script)

        assert exit_code == 0, (
            f"Example 005 failed with exit code {exit_code}\n"
            f"stdout: {stdout}\n"
            f"stderr: {stderr}"
        )

        # Verify output contains version rendering
        assert "Rendering LATEST version" in stdout
        assert "Rendering version v1.0.0" in stdout
        assert "Rendering version v2" in stdout
        assert "[OK] Rendered" in stdout


class TestExample006VersionExport:
    """Test that example 006 (version export) works after cleanup."""

    def test_example_006_runs_successfully(self):
        """Test that example 006 runs without errors."""
        examples_dir = get_examples_dir()
        example_script = examples_dir / "6-version-export" / "export_demo.py"

        assert example_script.exists(), f"Example script not found: {example_script}"

        exit_code, stdout, stderr = run_example(example_script)

        assert exit_code == 0, (
            f"Example 006 failed with exit code {exit_code}\n"
            f"stdout: {stdout}\n"
            f"stderr: {stderr}"
        )

        # Verify output contains export operations
        assert "Exporting version v1.0.0" in stdout
        assert "Exporting version v2.0.0" in stdout
        assert "Exported" in stdout
        assert "files to:" in stdout
