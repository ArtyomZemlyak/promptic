"""Integration tests for instruction file migration to unified context node architecture.

These tests verify that all existing instruction files load correctly
with the new node system, ensuring file format compatibility.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from promptic.context.nodes.models import ContextNode
from promptic.sdk.nodes import load_node


def test_existing_instruction_markdown_files_load():
    """Test that all existing instruction Markdown files load correctly.

    After migration, existing instruction Markdown files should load as
    ContextNode instances while maintaining compatibility.
    """
    # TODO: Implement after T089-T090 migration
    # This test should:
    # 1. Load existing instruction .md files from examples/
    # 2. Verify they load as ContextNode
    # 3. Verify content is preserved correctly
    pass


def test_existing_instruction_yaml_files_load():
    """Test that all existing instruction YAML files load correctly.

    After migration, existing instruction YAML files should load as
    ContextNode instances while maintaining compatibility.
    """
    # TODO: Implement after T089-T090 migration
    # This test should:
    # 1. Load existing instruction .yaml files
    # 2. Verify they load as ContextNode
    # 3. Verify content is preserved correctly
    pass


def test_existing_instruction_jinja2_files_load():
    """Test that all existing instruction Jinja2 files load correctly.

    After migration, existing instruction Jinja2 template files should
    load as ContextNode instances while maintaining compatibility.
    """
    # TODO: Implement after T089-T090 migration
    # This test should:
    # 1. Load existing instruction .jinja/.jinja2 files
    # 2. Verify they load as ContextNode
    # 3. Verify template syntax is preserved
    pass


def test_instruction_content_preserved():
    """Test that instruction content is preserved during migration.

    The migration should preserve all instruction content, metadata,
    and structure while using ContextNode internally.
    """
    # TODO: Implement after T089-T090 migration
    # This test verifies:
    # 1. Instruction text/content preserved
    # 2. Metadata preserved (version, locale, etc.)
    # 3. Format information preserved
    # 4. References preserved
    pass


def test_examples_directory_instructions_load():
    """Test that all instruction files in examples/ directory load correctly.

    This comprehensive test loads all instruction files from the
    examples directory to verify migration compatibility.
    """
    # TODO: Implement after T089-T090 migration
    # This test should:
    # 1. Find all instruction files (.md, .yaml, .jinja, .jinja2) in examples/
    # 2. Load each using load_node() or equivalent
    # 3. Verify they all load successfully
    # 4. Verify they can be rendered
    examples_dir = Path(__file__).parent.parent.parent / "examples"
    # instruction_files = list(examples_dir.rglob("instructions/*.md"))
    # instruction_files.extend(examples_dir.rglob("instructions/*.yaml"))
    # instruction_files.extend(examples_dir.rglob("instructions/*.jinja*"))
    # for instruction_file in instruction_files:
    #     node = load_node(str(instruction_file))
    #     assert node is not None
    #     assert isinstance(node, ContextNode)
    pass
