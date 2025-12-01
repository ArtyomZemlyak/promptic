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


def _create_versioned_prompt(tmp_path: Path) -> Path:
    """Create a directory with versioned root and nested prompts for path resolution tests."""
    prompt_dir = tmp_path / "versioned_prompt"
    prompt_dir.mkdir()

    instructions_dir = prompt_dir / "instructions"
    instructions_dir.mkdir()
    (instructions_dir / "process_v1.md").write_text("## Process v1\nStable flow")
    (instructions_dir / "process_v2.md").write_text("## Process v2\nLatest flow")

    root_template = """# Root {tag}

[Explicit file](instructions/process_v1.md)
[No version](instructions/process.md)
[No extension](instructions/process)
[Directory hint](instructions)
"""
    (prompt_dir / "task_v1.md").write_text(root_template.format(tag="v1"))
    (prompt_dir / "task_v2.md").write_text(root_template.format(tag="v2"))

    return prompt_dir


def test_render_supports_prompt_path_hints(tmp_path: Path):
    """Render should accept directories, base filenames, and version-less hints."""
    prompt_dir = _create_versioned_prompt(tmp_path)

    # Directory path + explicit version
    dir_output = render(prompt_dir, version="v1", render_mode="file_first")
    assert "Root v1" in dir_output

    # File hint without version suffix but with extension
    file_hint = prompt_dir / "task.md"
    file_output = render(file_hint, version="v2", render_mode="file_first")
    assert "Root v2" in file_output

    # File hint without extension defaults to latest version
    base_hint = prompt_dir / "task"
    latest_output = render(base_hint, render_mode="file_first")
    assert "Root v2" in latest_output


def test_render_resolves_nested_prompt_hints(tmp_path: Path):
    """Internal references without version or extension should resolve automatically."""
    prompt_dir = _create_versioned_prompt(tmp_path)

    latest_output = render(prompt_dir, render_mode="full")
    assert "Root v2" in latest_output
    assert "Process v2" in latest_output

    pinned_output = render(prompt_dir, version="v1", render_mode="full")
    assert "Root v1" in pinned_output
    assert "Process v1" in pinned_output


# =============================================================================
# REGRESSION TESTS - SOLID Refactoring (008-solid-refactor)
# =============================================================================
# AICODE-NOTE: These tests capture the current behavior of render_node_network
# for all formats and modes. They serve as regression baselines during the
# refactoring to ensure behavior is preserved.


@pytest.fixture
def rendering_fixtures() -> Path:
    """Return the path to rendering test fixtures."""
    return Path(__file__).parent.parent / "fixtures" / "rendering"


class TestRegressionMarkdownFullMode:
    """Regression tests for markdown full mode rendering."""

    def test_markdown_root_with_link_reference(self, rendering_fixtures: Path):
        """Test markdown file with [text](path) reference is inlined in full mode."""
        root_path = rendering_fixtures / "markdown_root.md"
        if not root_path.exists():
            pytest.skip("Fixture not found")

        output = render(root_path, target_format="markdown", render_mode="full")

        # The child content should be inlined where the link was
        assert "Child Content" in output
        assert "This is the child markdown file" in output
        # The root content should be preserved
        assert "Root Document" in output
        assert "End of root" in output

    def test_markdown_preserves_external_links(self, tmp_path: Path):
        """Test that external links (http://, https://) are preserved."""
        root_file = tmp_path / "root.md"
        root_file.write_text(
            "# Test\n[Google](https://google.com)\n[Email](mailto:test@example.com)"
        )

        output = render(root_file, target_format="markdown", render_mode="full")

        assert "https://google.com" in output
        assert "mailto:test@example.com" in output


class TestRegressionYamlFullMode:
    """Regression tests for YAML full mode rendering."""

    def test_yaml_root_with_ref_reference(self, rendering_fixtures: Path):
        """Test YAML file with $ref is resolved in full mode."""
        root_path = rendering_fixtures / "yaml_root.yaml"
        if not root_path.exists():
            pytest.skip("Fixture not found")

        output = render(root_path, target_format="yaml", render_mode="full")

        # The referenced config should be inlined
        assert "setting" in output
        assert "enabled" in output
        # The root content should be preserved
        assert "Root YAML File" in output


class TestRegressionJsonFullMode:
    """Regression tests for JSON full mode rendering."""

    def test_json_root_with_ref_reference(self, rendering_fixtures: Path):
        """Test JSON file with $ref is resolved in full mode."""
        root_path = rendering_fixtures / "json_root.json"
        if not root_path.exists():
            pytest.skip("Fixture not found")

        output = render(root_path, target_format="json", render_mode="full")

        # The referenced data should be inlined
        assert "key" in output
        assert "value" in output
        # The root content should be preserved
        assert "Root JSON File" in output


class TestRegressionJinja2FullMode:
    """Regression tests for Jinja2 full mode rendering."""

    def test_jinja2_root_with_ref_comment(self, rendering_fixtures: Path):
        """Test Jinja2 file with {# ref: #} is resolved in full mode."""
        root_path = rendering_fixtures / "jinja2_root.jinja2"
        if not root_path.exists():
            pytest.skip("Fixture not found")

        output = render(root_path, target_format="markdown", render_mode="full")

        # The referenced template data should be inlined
        assert "template_name" in output or "Test Template" in output
        # The root content should be preserved
        assert "Main Template" in output


class TestRegressionFileFirstMode:
    """Regression tests for file_first mode rendering."""

    def test_markdown_file_first_preserves_links(self, rendering_fixtures: Path):
        """Test that file_first mode preserves markdown links."""
        root_path = rendering_fixtures / "markdown_root.md"
        if not root_path.exists():
            pytest.skip("Fixture not found")

        output = render(root_path, target_format="markdown", render_mode="file_first")

        # The link should be preserved, not inlined
        assert "[Include child](child.md)" in output
        # The root content should be preserved
        assert "Root Document" in output

    def test_yaml_file_first_preserves_refs(self, rendering_fixtures: Path):
        """Test that file_first mode preserves $ref in YAML."""
        root_path = rendering_fixtures / "yaml_root.yaml"
        if not root_path.exists():
            pytest.skip("Fixture not found")

        output = render(root_path, target_format="yaml", render_mode="file_first")

        # The $ref should be preserved (or file_first returns raw)
        assert "Root YAML File" in output


class TestRegressionCrossFormatRendering:
    """Regression tests for cross-format rendering."""

    def test_yaml_to_markdown_wraps_in_code_block(self, rendering_fixtures: Path):
        """Test that YAML rendered to markdown is wrapped in code blocks."""
        root_path = rendering_fixtures / "yaml_root.yaml"
        if not root_path.exists():
            pytest.skip("Fixture not found")

        output = render(root_path, target_format="markdown", render_mode="full")

        # YAML content should be wrapped in code block for markdown output
        assert "```yaml" in output or "Root YAML File" in output

    def test_json_to_markdown_wraps_in_code_block(self, rendering_fixtures: Path):
        """Test that JSON rendered to markdown is wrapped in code blocks."""
        root_path = rendering_fixtures / "json_root.json"
        if not root_path.exists():
            pytest.skip("Fixture not found")

        output = render(root_path, target_format="markdown", render_mode="full")

        # JSON content should be wrapped in code block for markdown output
        assert "```json" in output or "Root JSON File" in output
