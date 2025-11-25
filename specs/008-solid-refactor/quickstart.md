# Quickstart: SOLID Refactoring Implementation

**Branch**: `008-solid-refactor` | **Date**: 2025-11-25

## Overview

This guide provides step-by-step instructions for implementing the SOLID refactoring of the promptic library.

## Prerequisites

```bash
# Ensure you're on the correct branch
git checkout 008-solid-refactor

# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Verify tests pass before starting
pytest tests/ -v
```

## Implementation Order

### Step 1: Create Module Structure (5 min)

```bash
# Create the rendering module
mkdir -p src/promptic/rendering/strategies
touch src/promptic/rendering/__init__.py
touch src/promptic/rendering/strategies/__init__.py
touch src/promptic/rendering/strategies/base.py
touch src/promptic/rendering/strategies/markdown_link.py
touch src/promptic/rendering/strategies/jinja2_ref.py
touch src/promptic/rendering/strategies/structured_ref.py
touch src/promptic/rendering/inliner.py

# Create test module
mkdir -p tests/unit/rendering
touch tests/unit/rendering/__init__.py
touch tests/unit/rendering/test_strategies.py
touch tests/unit/rendering/test_reference_inliner.py
```

### Step 2: Implement ReferenceStrategy Base (15 min)

Copy the interface from `specs/008-solid-refactor/data-model.md`:

```python
# src/promptic/rendering/strategies/base.py
from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

class ReferenceStrategy(ABC):
    """Abstract base class for reference resolution strategies."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    def can_process(self, content: Any) -> bool:
        pass
    
    @abstractmethod
    def process_string(
        self,
        content: str,
        node_lookup: Callable[[str], Optional[Any]],
        content_renderer: Callable[[Any, str], str],
        target_format: str,
    ) -> str:
        pass
    
    @abstractmethod
    def process_structure(
        self,
        content: dict[str, Any],
        node_lookup: Callable[[str], Optional[Any]],
        content_renderer: Callable[[Any, str], Any],
        target_format: str,
    ) -> dict[str, Any]:
        pass
```

### Step 3: Extract MarkdownLinkStrategy (30 min)

1. Copy the pattern from `sdk/nodes.py` line ~513-535
2. Implement in `strategies/markdown_link.py`
3. Write unit tests

```python
# Test first
def test_markdown_link_replaces_local_ref():
    strategy = MarkdownLinkStrategy()
    content = "[Instructions](instructions.md)"
    node_lookup = lambda p: MockNode(content="Hello World") if p == "instructions.md" else None
    renderer = lambda n, f: n.content
    
    result = strategy.process_string(content, node_lookup, renderer, "markdown")
    
    assert result == "Hello World"

def test_markdown_link_preserves_external():
    strategy = MarkdownLinkStrategy()
    content = "[Google](https://google.com)"
    
    result = strategy.process_string(content, lambda p: None, lambda n, f: "", "markdown")
    
    assert result == "[Google](https://google.com)"
```

### Step 4: Extract Jinja2RefStrategy (30 min)

1. Copy the pattern from `sdk/nodes.py` line ~369-397
2. Implement in `strategies/jinja2_ref.py`
3. Write unit tests

### Step 5: Extract StructuredRefStrategy (30 min)

1. Copy the pattern from `sdk/nodes.py` line ~435-474
2. Implement in `strategies/structured_ref.py`
3. Write unit tests

### Step 6: Implement ReferenceInliner (45 min)

1. Create `rendering/inliner.py`
2. Compose strategies
3. Implement `inline_references()` method
4. Write integration tests

```python
# Test with real network
def test_inliner_produces_same_output():
    # Load test fixture
    network = load_node_network("tests/fixtures/multi_ref.md")
    
    # Get baseline from current implementation
    baseline = render_node_network(network, "markdown", render_mode="full")
    
    # Get new implementation result
    inliner = ReferenceInliner()
    result = inliner.inline_references(network.root, network, "markdown")
    
    assert result == baseline
```

### Step 7: Refactor render_node_network (1 hour)

1. Import `ReferenceInliner`
2. Replace duplicate code blocks with `inliner.inline_references()`
3. Run full test suite after each replacement
4. Remove unused nested functions

```python
# Before: ~750 lines with duplicates
# After: ~50-100 lines using ReferenceInliner
```

### Step 8: Simplify VersionExporter (45 min)

Extract private methods:

```python
# Extract these from export_version():
def _validate_and_prepare(self, target_dir, overwrite): ...
def _resolve_root_path(self, source_path, version_spec): ...
def _build_file_mapping(self, source_base, target, version_spec): ...
def _create_content_processor(self, vars, hierarchical_paths): ...
```

### Step 9: Final Verification (30 min)

```bash
# Run all tests
pytest tests/ -v

# Check coverage
pytest tests/ --cov=src/promptic/rendering --cov-report=html

# Run pre-commit
pre-commit run --all-files

# Verify line counts
wc -l src/promptic/sdk/nodes.py
# Should be <200 lines (was ~1200)

wc -l src/promptic/versioning/domain/exporter.py
# Should be <200 lines (was ~525)
```

## Verification Checklist

- [ ] All existing tests pass
- [ ] New unit tests for strategies pass
- [ ] New unit tests for ReferenceInliner pass
- [ ] Integration tests comparing output pass
- [ ] `render_node_network` < 100 lines
- [ ] `export_version` < 100 lines
- [ ] Coverage > 90% for new code
- [ ] pre-commit passes
- [ ] No duplicate code blocks remain

## Rollback Plan

If issues are discovered:

```bash
# Revert to main branch
git checkout main

# Or revert specific commits
git revert HEAD~N
```

## Files Modified

| File | Action | Lines Before | Lines After |
|------|--------|--------------|-------------|
| `src/promptic/sdk/nodes.py` | Refactor | ~1200 | ~200 |
| `src/promptic/versioning/domain/exporter.py` | Refactor | ~525 | ~300 |
| `src/promptic/rendering/__init__.py` | New | 0 | ~20 |
| `src/promptic/rendering/inliner.py` | New | 0 | ~100 |
| `src/promptic/rendering/strategies/base.py` | New | 0 | ~50 |
| `src/promptic/rendering/strategies/markdown_link.py` | New | 0 | ~60 |
| `src/promptic/rendering/strategies/jinja2_ref.py` | New | 0 | ~50 |
| `src/promptic/rendering/strategies/structured_ref.py` | New | 0 | ~80 |
| `tests/unit/rendering/test_strategies.py` | New | 0 | ~150 |
| `tests/unit/rendering/test_reference_inliner.py` | New | 0 | ~100 |

## Common Issues

### Issue: Tests fail after extraction

**Solution**: Ensure node lookup logic matches exactly. The current implementation uses:
```python
path == str(node_id) or path in str(node_id) or str(node_id).endswith(path)
```

### Issue: Format conversion differs

**Solution**: Check that YAML/JSON wrapping in markdown code blocks is preserved:
```python
if target_format == "markdown" and node.format in ("yaml", "json"):
    return f"```{node.format}\n{content}\n```"
```

### Issue: Circular import

**Solution**: Use TYPE_CHECKING imports:
```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from promptic.context.nodes.models import ContextNode
```

