"""Test that no token-related code remains after token counting removal.

This test verifies that all token counting references have been removed from
the codebase after cleanup, except for comments explaining the removal.
"""

import ast
import re
from pathlib import Path
from typing import List, Tuple


def get_project_root() -> Path:
    """Get the project root directory."""
    # test file is at tests/integration/test_no_token_references.py
    # project root is two levels up
    test_dir = Path(__file__).parent
    return test_dir.parent.parent


def find_python_files(root: Path) -> List[Path]:
    """Find all Python files in src/promptic directory."""
    src_dir = root / "src" / "promptic"
    if not src_dir.exists():
        return []
    return list(src_dir.rglob("*.py"))


def scan_file_for_token_references(file_path: Path) -> List[Tuple[int, str]]:
    """
    Scan a file for token-related references.

    Returns list of (line_number, line_content) tuples with token references.
    Ignores comments and docstrings.
    """
    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    references = []

    # Token-related patterns to check
    token_patterns = [
        r"\btoken_counter\b",
        r"\bTokenCounter\b",
        r"\btiktoken\b",
        r"\bmax_tokens_per_node\b",
        r"\bmax_tokens_per_network\b",
        r"\btoken_model\b",
        r"\btotal_tokens\b",
        r"\bnode_tokens\b",
        r"\bcount_tokens\b",
        r"\bTokenCountingError\b",
        r"from promptic\.token_counting",
        r"import.*token_counting",
    ]

    for line_num, line in enumerate(lines, start=1):
        # Skip comment-only lines
        stripped = line.strip()
        if stripped.startswith("#"):
            continue

        # Check for token references (case-sensitive)
        for pattern in token_patterns:
            if re.search(pattern, line):
                references.append((line_num, line))
                break

    return references


def test_no_token_counting_references_in_source():
    """Test that no token counting references remain in source code."""
    project_root = get_project_root()
    python_files = find_python_files(project_root)

    assert len(python_files) > 0, "No Python files found in src/promptic"

    files_with_references = {}
    for file_path in python_files:
        references = scan_file_for_token_references(file_path)
        if references:
            rel_path = file_path.relative_to(project_root)
            files_with_references[str(rel_path)] = references

    if files_with_references:
        error_msg = "Token counting references found in source code:\n"
        for file_path, references in files_with_references.items():
            error_msg += f"\n{file_path}:\n"
            for line_num, line_content in references:
                error_msg += f"  Line {line_num}: {line_content.strip()}\n"
        error_msg += "\nAll token counting references should be removed after cleanup."

        # Fail the test
        assert False, error_msg


def test_tiktoken_dependency_removed_from_pyproject():
    """Test that tiktoken dependency is removed from pyproject.toml."""
    project_root = get_project_root()
    pyproject_path = project_root / "pyproject.toml"

    assert pyproject_path.exists(), "pyproject.toml not found"

    content = pyproject_path.read_text(encoding="utf-8")

    # Check for tiktoken in actual dependencies (not in comments)
    # Look for lines that contain tiktoken but are not comments
    lines = content.splitlines()
    dependency_lines_with_tiktoken = [
        line for line in lines if "tiktoken" in line and not line.strip().startswith("#")
    ]

    assert not dependency_lines_with_tiktoken, (
        f"tiktoken dependency found in pyproject.toml:\n"
        f"{chr(10).join(dependency_lines_with_tiktoken)}\n"
        "tiktoken should be removed from dependencies (comments are okay)"
    )


def test_no_token_counting_imports():
    """Test that no imports reference promptic.token_counting."""
    project_root = get_project_root()
    python_files = find_python_files(project_root)

    files_with_imports = []
    for file_path in python_files:
        lines = file_path.read_text(encoding="utf-8").splitlines()

        # Check for token_counting imports (ignore comment-only lines)
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "from promptic.token_counting" in line or "import promptic.token_counting" in line:
                rel_path = file_path.relative_to(project_root)
                files_with_imports.append(str(rel_path))
                break

    assert not files_with_imports, (
        f"Files with token_counting imports found: {files_with_imports}\n"
        "All token_counting imports should be removed after cleanup (comments are okay)."
    )
