# Implementation Plan: SOLID Refactoring - Code Deduplication & Clean Architecture

**Branch**: `008-solid-refactor` | **Date**: 2025-11-25 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/008-solid-refactor/spec.md`

**Note**: This plan aligns with the `promptic Constitution` (clean architecture, SOLID, tests, docs, readability).

## Summary

This refactoring eliminates massive code duplication in `render_node_network` (750+ lines with 25 occurrences of duplicate patterns) by extracting dedicated service classes following SOLID principles. The primary approach is:

1. Extract `ReferenceInliner` service to consolidate duplicate `process_node_content` implementations
2. Implement Strategy pattern for reference types (MarkdownLink, Jinja2Ref, StructuredRef)
3. Simplify `VersionExporter.export_version` by extracting helper methods

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: pydantic (models), pyyaml, jinja2  
**Storage**: Filesystem (prompt files)  
**Testing**: pytest (unit, integration, contract tests)  
**Target Platform**: Cross-platform Python library  
**Project Type**: Single Python library  
**Performance Goals**: No regression in rendering performance  
**Constraints**: 100% backward compatibility for public API  
**Scale/Scope**: ~1200 lines of code to refactor, ~200 lines of new abstractions

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Architecture

**Current State (violations):**
```
sdk/nodes.py (render_node_network: 750+ lines)
├── process_node_content (defined 4+ times)
├── replace_jinja2_ref (duplicated)
├── replace_markdown_ref (duplicated)
└── replace_refs_in_dict (duplicated)
```

**Target State (clean architecture):**
```
Entities (unchanged):
├── ContextNode, NodeNetwork, NodeReference

Use Cases (new):
├── ReferenceInliner
│   └── inline_references(node, network, format) -> content
└── NodeContentProcessor
    └── process_content(node, strategies) -> content

Interface Adapters (new strategies):
├── ReferenceStrategy (ABC)
│   ├── MarkdownLinkStrategy
│   ├── Jinja2RefStrategy
│   └── StructuredRefStrategy

Dependency Flow: Adapters → Use Cases → Entities
```

**SOLID Trade-offs:**
- Strategy pattern adds abstraction overhead but eliminates 4x code duplication
- New classes increase file count but reduce cyclomatic complexity by 70%+

### Testing Evidence

| Requirement | Test Type | Test Location |
|-------------|-----------|---------------|
| FR-001: Identical behavior | Regression | `tests/integration/test_render_api.py` |
| FR-002: Single ReferenceInliner | Unit | `tests/unit/rendering/test_reference_inliner.py` (new) |
| FR-003: Strategy classes | Unit | `tests/unit/rendering/test_strategies.py` (new) |
| FR-004: Function size <100 | Static | Pre-commit hook + manual review |
| FR-006: No regression | Integration | All existing tests pass |
| FR-007: API compatibility | Contract | `tests/contract/test_public_api.py` |

### Quality Gates

- [x] Black formatter (line-length=100)
- [x] isort (profile=black)
- [x] `pre-commit run --all-files`
- [ ] mypy type checking (existing setup)
- [ ] pytest --cov (90%+ coverage for new code)

### Documentation & Traceability

| Update Required | Location |
|-----------------|----------|
| Architecture diagram | `docs_site/architecture/` |
| API reference | Docstrings in new classes |
| AICODE-NOTE comments | All new modules |
| Migration notes | `docs_site/development/` |

### Readability & DX

- Maximum function size: 50 lines (enforced by review)
- Naming: `{Action}{Target}Strategy` pattern (e.g., `MarkdownLinkStrategy`)
- File organization: One class per file for strategies
- No nested functions beyond 1 level deep

## Project Structure

### Documentation (this feature)

```text
specs/008-solid-refactor/
├── spec.md              # Feature specification (created)
├── plan.md              # This file
├── research.md          # Phase 0 output (below)
├── data-model.md        # Phase 1 output (below)
├── contracts/           # Phase 1 output (below)
│   ├── reference_strategy.py
│   └── reference_inliner.py
├── checklists/          # Quality tracking
│   └── requirements.md  # Spec validation (created)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/promptic/
├── context/
│   └── nodes/
│       └── models.py         # ContextNode, NodeNetwork (unchanged)
├── rendering/                 # NEW MODULE
│   ├── __init__.py
│   ├── inliner.py            # ReferenceInliner service
│   ├── processor.py          # NodeContentProcessor
│   └── strategies/
│       ├── __init__.py
│       ├── base.py           # ReferenceStrategy ABC
│       ├── markdown_link.py  # MarkdownLinkStrategy
│       ├── jinja2_ref.py     # Jinja2RefStrategy
│       └── structured_ref.py # StructuredRefStrategy
├── sdk/
│   └── nodes.py              # Refactored (750 → <100 lines)
└── versioning/
    └── domain/
        └── exporter.py       # Refactored (230 → <100 lines)

tests/
├── unit/
│   └── rendering/             # NEW TEST MODULE
│       ├── __init__.py
│       ├── test_reference_inliner.py
│       └── test_strategies.py
├── integration/
│   └── test_render_api.py    # Extended with regression tests
└── contract/
    └── test_rendering_contracts.py  # NEW
```

**Structure Decision**: Single project layout maintained. New `rendering/` module follows existing patterns in `context/`, `versioning/`.

## Complexity Tracking

> No Constitution violations requiring justification. The refactoring reduces complexity.

## Phase 0: Research

### Current Code Analysis

#### Problem: `render_node_network` in `sdk/nodes.py`

**Metrics:**
- Total lines: ~750
- `process_node_content` definitions: 4+ (25 pattern matches)
- Cyclomatic complexity: Very high (nested conditionals, loops)
- Code duplication: 70%+ estimated

**Duplicate Patterns Identified:**

1. **Jinja2 Reference Pattern** (repeated 4 times):
```python
jinja2_ref_pattern = re.compile(r"\{\#\s*ref:\s*([^\#]+)\s*\#\}", re.IGNORECASE)
def replace_jinja2_ref(match: re.Match[str]) -> str:
    path = match.group(1).strip()
    child = None
    for node_id, n in network.nodes.items():
        if (path == str(node_id) or path in str(node_id) or str(node_id).endswith(path)):
            child = n
            break
    if child:
        # ... processing logic
    return match.group(0)
```

2. **Markdown Link Pattern** (repeated 4 times):
```python
markdown_ref_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
def replace_markdown_ref(match: re.Match[str]) -> str:
    path = match.group(2)
    if path.startswith(("http://", "https://", "mailto:")):
        return match.group(0)
    # ... similar lookup logic
```

3. **Structured Ref Pattern** (repeated 4 times):
```python
def replace_refs_in_dict(data: dict[str, Any]) -> dict[str, Any]:
    result = {}
    for key, value in data.items():
        if isinstance(value, dict) and "$ref" in value:
            # ... resolution logic
```

#### Problem: `export_version` in `versioning/domain/exporter.py`

**Metrics:**
- Total lines: ~230
- Nested functions: 3 (content_processor, _build_hierarchical_paths)
- Responsibilities: 5+ (validation, discovery, mapping, processing, export)

### Extraction Strategy

**Phase 1 (P1 items):**
1. Create `ReferenceStrategy` interface
2. Implement concrete strategies
3. Create `ReferenceInliner` using strategies
4. Refactor `render_node_network` to use `ReferenceInliner`

**Phase 2 (P2 items):**
5. Extract `VersionExporter` helper methods

**Phase 3 (P3 items):**
6. Optional: Pipeline pattern (defer if not needed)

## Phase 1: Design

### Data Model

See [data-model.md](./data-model.md) for detailed class diagrams.

**Core Abstractions:**

```python
# rendering/strategies/base.py
from abc import ABC, abstractmethod
from typing import Any, Callable

class ReferenceStrategy(ABC):
    """Strategy interface for reference resolution."""

    @abstractmethod
    def can_process(self, content: Any) -> bool:
        """Check if this strategy can process the content type."""
        pass

    @abstractmethod
    def process(
        self,
        content: str,
        node_lookup: Callable[[str], Any],
        format_renderer: Callable[[Any], str],
    ) -> str:
        """Process content and resolve references.

        Args:
            content: Content string to process
            node_lookup: Function to lookup nodes by path
            format_renderer: Function to render node content to string

        Returns:
            Processed content with references resolved
        """
        pass


# rendering/inliner.py
from promptic.context.nodes.models import ContextNode, NodeNetwork

class ReferenceInliner:
    """Service for inlining referenced content into nodes.

    # AICODE-NOTE: This class consolidates all duplicate process_node_content
    # implementations from render_node_network. It uses strategy pattern to
    # handle different reference types (markdown links, jinja2 refs, $ref).
    """

    def __init__(self, strategies: list[ReferenceStrategy] | None = None):
        self.strategies = strategies or self._default_strategies()

    def inline_references(
        self,
        node: ContextNode,
        network: NodeNetwork,
        target_format: str,
    ) -> str:
        """Inline all references in node content.

        Args:
            node: Node to process
            network: Network containing all nodes for lookup
            target_format: Target output format

        Returns:
            Content string with all references inlined
        """
        pass
```

### Contracts

See [contracts/](./contracts/) for interface definitions.

**Key Contracts:**

1. `ReferenceStrategy.process()` must be idempotent
2. `ReferenceInliner.inline_references()` must produce identical output to current implementation
3. Strategies must gracefully handle missing references (return original content)

## Implementation Phases

### Phase 1: Extract Strategy Classes (P1)

**Duration**: 2-3 hours

**Steps:**
1. Create `src/promptic/rendering/` module structure
2. Implement `ReferenceStrategy` ABC
3. Extract `MarkdownLinkStrategy` from duplicate code
4. Extract `Jinja2RefStrategy` from duplicate code
5. Extract `StructuredRefStrategy` from duplicate code
6. Write unit tests for each strategy

**Verification:**
- Each strategy passes isolated unit tests
- No changes to `render_node_network` yet

### Phase 2: Create ReferenceInliner (P1)

**Duration**: 2-3 hours

**Steps:**
1. Implement `ReferenceInliner` class
2. Integrate strategies via composition
3. Implement `inline_references()` method
4. Write unit tests
5. Write integration tests comparing output

**Verification:**
- `ReferenceInliner` produces identical output to current implementation
- All strategy combinations tested

### Phase 3: Refactor render_node_network (P1)

**Duration**: 2-3 hours

**Steps:**
1. Import `ReferenceInliner` in `sdk/nodes.py`
2. Replace duplicate `process_node_content` calls with `ReferenceInliner`
3. Remove duplicate pattern definitions
4. Simplify conditional branches
5. Run full test suite

**Verification:**
- `render_node_network` < 100 lines
- All existing tests pass
- New tests pass

### Phase 4: Simplify VersionExporter (P2)

**Duration**: 1-2 hours

**Steps:**
1. Extract `_build_file_mapping()` method
2. Extract `_create_content_processor()` method
3. Extract `_validate_and_prepare_export()` method
4. Update `export_version()` to use new methods
5. Run versioning tests

**Verification:**
- `export_version()` < 100 lines
- Each method has single responsibility
- All versioning tests pass

### Phase 5: Documentation & Cleanup (All)

**Duration**: 1 hour

**Steps:**
1. Add `AICODE-NOTE` comments to all new classes
2. Update docstrings
3. Run `pre-commit run --all-files`
4. Update `docs_site/` if architecture section exists
5. Final test run with coverage

**Verification:**
- 90%+ coverage on new code
- All quality gates pass
- No lint errors

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Regression in rendering output | Medium | High | Extensive regression tests before/after |
| Strategy ordering affects output | Low | Medium | Document order requirements, test all orderings |
| Performance degradation | Low | Low | Profile before/after, optimize if needed |
| Breaking internal consumers | Low | Medium | Search for all usages, ensure compatibility |

## Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| `render_node_network` lines | ~750 | <100 | `wc -l` |
| Duplicate code blocks | 4+ | 0 | Manual review |
| Test coverage (new code) | N/A | 90%+ | pytest-cov |
| Cyclomatic complexity | High | Reduced 50%+ | radon |
| Existing tests passing | 100% | 100% | pytest |

## Appendix: File Mapping

| Current Location | Action | New Location |
|------------------|--------|--------------|
| `sdk/nodes.py:353-1015` | Extract | `rendering/inliner.py` |
| `sdk/nodes.py` (jinja2 pattern) | Extract | `rendering/strategies/jinja2_ref.py` |
| `sdk/nodes.py` (markdown pattern) | Extract | `rendering/strategies/markdown_link.py` |
| `sdk/nodes.py` ($ref pattern) | Extract | `rendering/strategies/structured_ref.py` |
| `versioning/domain/exporter.py:68-327` | Refactor in place | Same file, new methods |
