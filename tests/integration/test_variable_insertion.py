"""Integration tests for variable insertion across node networks."""

from pathlib import Path

from promptic.sdk.nodes import load_node_network, render_node_network


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_render_node_network_applies_all_scopes(tmp_path):
    """Ensure simple, node, and path scoped variables substitute correctly."""
    root = tmp_path / "root.md"
    instructions = tmp_path / "group" / "instructions.md"
    templates = tmp_path / "templates" / "details.md"

    _write_file(
        root,
        """# Task Prompt for {{user_name}}

Welcome {{user_name}}!

## Steps
- Follow the [instructions](group/instructions.md)
- Review the [template](templates/details.md)
""",
    )

    _write_file(
        instructions,
        """# Instructions for {{user_name}}

Format: {{format}}
Style: {{style}}
""",
    )

    _write_file(
        templates,
        """# Template Details

Level: {{level}}
Verbosity: {{verbosity}}
Style echo: {{style}}
""",
    )

    network = load_node_network(root)
    rendered = render_node_network(
        network,
        target_format="markdown",
        render_mode="full",
        vars={
            "user_name": "Alice",
            "instructions.format": "detailed",
            "details.level": "advanced",
            "root.group.instructions.style": "technical",
            "root.templates.details.verbosity": "high",
        },
    )

    assert "Task Prompt for Alice" in rendered
    assert "Instructions for Alice" in rendered
    assert "Format: detailed" in rendered
    assert "Style: technical" in rendered
    assert "Level: advanced" in rendered
    assert "Verbosity: high" in rendered
    # Style in template remains unresolved because no applicable variable
    assert "Style echo: {{style}}" in rendered


def test_render_node_network_does_not_mutate_network(tmp_path):
    """Rendering with variables should not mutate the original network."""
    root = tmp_path / "root.md"
    _write_file(
        root,
        """# Greeting

Hello {{user_name}}!
""",
    )

    network = load_node_network(root)

    first = render_node_network(
        network, target_format="markdown", render_mode="full", vars={"user_name": "Alice"}
    )
    second = render_node_network(
        network, target_format="markdown", render_mode="full", vars={"user_name": "Bob"}
    )

    assert "Alice" in first
    assert "Bob" in second
