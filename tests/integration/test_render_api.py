"""Integration tests for the render() API function.

This module tests the main render() function that combines load_node_network
and render_node_network for convenient one-step rendering.
"""

from pathlib import Path

import pytest

from promptic import render


@pytest.fixture
def example_dir() -> Path:
    """Return the path to example files."""
    return Path(__file__).parent.parent.parent / "examples" / "get_started"


def test_render_simple_markdown(example_dir: Path):
    """Test render() with simple markdown file."""
    main_path = example_dir / "1-inline-full-render" / "main.md"

    # Render with default settings (full mode, markdown)
    output = render(main_path)

    assert isinstance(output, str)
    assert len(output) > 0
    assert "Hello" in output or "greeting" in output.lower()


def test_render_with_target_format(example_dir: Path):
    """Test render() with different target formats."""
    main_path = example_dir / "1-inline-full-render" / "main.md"

    # Test markdown format (default)
    md_output = render(main_path, target_format="markdown")
    assert isinstance(md_output, str)

    # Test YAML format
    yaml_output = render(main_path, target_format="yaml")
    assert isinstance(yaml_output, str)

    # Test JSON format
    json_output = render(main_path, target_format="json")
    assert isinstance(json_output, str)


def test_render_with_render_mode(example_dir: Path):
    """Test render() with different render modes."""
    main_path = example_dir / "2-file-first" / "main.md"

    # Full mode: inlines all content
    full_output = render(main_path, render_mode="full")
    assert isinstance(full_output, str)

    # File-first mode: preserves links
    file_first_output = render(main_path, render_mode="file_first")
    assert isinstance(file_first_output, str)

    # Full mode should be longer (includes inlined content)
    # File-first mode should contain markdown links
    assert len(full_output) >= len(file_first_output) or "[" in file_first_output


def test_render_with_variables(tmp_path: Path):
    """Test render() with variable substitution."""
    # Create a test file with variables
    test_file = tmp_path / "test.md"
    test_file.write_text("Hello, {{user_name}}! Task: {{task_type}}")

    # Render with variables
    output = render(test_file, vars={"user_name": "Alice", "task_type": "analysis"})

    assert "Alice" in output
    assert "analysis" in output
    assert "{{user_name}}" not in output
    assert "{{task_type}}" not in output


def test_render_file_not_found():
    """Test render() with non-existent file."""
    with pytest.raises(FileNotFoundError):
        render("non_existent_file.md")


def test_render_multiple_files(example_dir: Path):
    """Test render() with files that reference other files."""
    main_path = example_dir / "3-multiple-files" / "root-1.md"

    # Render with full mode (should inline all references)
    output = render(main_path, render_mode="full")

    assert isinstance(output, str)
    assert len(output) > 0


def test_render_different_formats(example_dir: Path):
    """Test render() with different file formats."""
    formats_dir = example_dir / "4-file-formats"

    # Test YAML file
    yaml_path = formats_dir / "root.yaml"
    if yaml_path.exists():
        output = render(yaml_path, target_format="markdown")
        assert isinstance(output, str)

    # Test JSON file
    json_path = formats_dir / "file.json"
    if json_path.exists():
        output = render(json_path, target_format="markdown")
        assert isinstance(output, str)

    # Test Markdown file
    md_path = formats_dir / "file.md"
    if md_path.exists():
        output = render(md_path, target_format="yaml")
        assert isinstance(output, str)


def test_render_returns_string():
    """Test that render() always returns a string."""
    # Create a minimal test file
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test\n\nThis is a test.")
        temp_path = Path(f.name)

    try:
        output = render(temp_path)
        assert isinstance(output, str)
        assert len(output) > 0
    finally:
        temp_path.unlink()


def test_render_with_config(tmp_path: Path):
    """Test render() with custom NetworkConfig."""
    from promptic.context.nodes.models import NetworkConfig

    test_file = tmp_path / "test.md"
    test_file.write_text("# Test\n\nThis is a test.")

    # Render with custom config
    config = NetworkConfig(max_depth=5)
    output = render(test_file, config=config)

    assert isinstance(output, str)
    assert len(output) > 0


def test_render_reusable_with_variables(tmp_path: Path):
    """Test that render() can be called multiple times with different variables."""
    test_file = tmp_path / "test.md"
    test_file.write_text("User: {{name}}, Role: {{role}}")

    # First render
    output1 = render(test_file, vars={"name": "Alice", "role": "admin"})
    assert "Alice" in output1
    assert "admin" in output1

    # Second render with different variables
    output2 = render(test_file, vars={"name": "Bob", "role": "user"})
    assert "Bob" in output2
    assert "user" in output2

    # Outputs should be different
    assert output1 != output2
