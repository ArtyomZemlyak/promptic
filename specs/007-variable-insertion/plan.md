# Implementation Plan: Variable Insertion

**Branch**: `007-variable-insertion` | **Date**: 2025-11-25 | **Spec**: [spec.md](./spec.md)

## Summary

Implement variable insertion functionality for prompts, enabling users to pass runtime values that get substituted into prompt content. Supports three scoping levels: simple (global), node-scoped, and full-path. Works across all file formats with format-specific handling for Jinja2 (native templating) and others ({{var}} markers).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pydantic>=2.6, pyyaml>=6.0, jinja2>=3.1, orjson>=3.9  
**Storage**: Filesystem-based prompt files  
**Testing**: pytest with unit, integration, and contract tests  
**Target Platform**: Linux/macOS/Windows (Python cross-platform)  
**Project Type**: Single project (src/, tests/ at root)  
**Performance Goals**: Variable substitution <100ms for 100-node hierarchies with 50 variables  
**Constraints**: Must not break existing format parsing, preserve YAML/JSON validity  
**Scale/Scope**: Support hierarchies up to 10 nesting levels, 1000+ nodes

## Constitution Check

- **Architecture**: `VariableSubstitutor` service in domain layer (`src/promptic/context/variables/`), format-specific adapters remain in `src/promptic/format_parsers/`. Rendering functions in SDK layer accept `vars` parameter and delegate to substitutor. Dependencies flow: SDK → Domain (substitutor) → Adapters (parsers). No outward dependencies from domain.

- **Testing Evidence**: Unit tests for scope matching (`tests/unit/variables/test_scope_resolution.py`), substitution logic (`test_substitutor.py`), integration tests for hierarchies (`tests/integration/test_variable_insertion.py`), contract tests for substitution interface (`tests/contract/test_variable_interface.py`).

- **Quality Gates**: Black formatting (`black --line-length=100`), isort (`--profile=black`), pre-commit hooks (YAML/JSON validation, trailing whitespace), pytest coverage >85% for new code.

- **Documentation & Traceability**: Create `docs_site/variables/insertion-guide.md`, update `README.md` examples, add docstrings to all new classes/functions, use `AICODE-NOTE` for substitution strategy and scope precedence rules.

- **Readability & DX**: Keep substitution functions <80 lines, use clear names (`resolve_scoped_variable`, `substitute_in_content`), avoid complex regex (use simple patterns with comments), separate parsing from substitution logic.

## Project Structure

### Documentation (this feature)

```text
specs/007-variable-insertion/
├── spec.md                     # Feature specification (completed)
├── plan.md                     # This file
├── tasks.md                    # Task breakdown (next)
├── data-model.md              # Variable scope model
└── contracts/
    └── variable-substitution.yaml  # Contract definitions
```

### Source Code (repository root)

```text
src/promptic/
├── context/
│   ├── variables/              # NEW: Variable substitution domain logic
│   │   ├── __init__.py
│   │   ├── models.py          # VariableScope, SubstitutionContext
│   │   ├── substitutor.py     # VariableSubstitutor service
│   │   └── resolver.py        # Scope resolution logic
│   └── nodes/
│       └── models.py          # Update ContextNode (optional context field)
├── format_parsers/
│   ├── jinja2_parser.py       # Update: Jinja2 variable rendering
│   └── base.py                # Update: Variable marker handling
└── sdk/
    ├── nodes.py               # Update: Add vars param to render_node_network
    └── api.py                 # Update: Add vars param to export_version

tests/
├── unit/
│   └── variables/             # NEW: Unit tests for variables
│       ├── test_substitutor.py
│       ├── test_scope_resolution.py
│       └── test_jinja2_variables.py
├── integration/
│   └── test_variable_insertion.py  # NEW: Integration tests
└── contract/
    └── test_variable_contract.py   # NEW: Contract tests

examples/get_started/
└── 7-variable-insertion/      # NEW: Example 7
    ├── README.md
    ├── render.py
    ├── root.md
    ├── group/
    │   └── instructions.md
    └── templates/
        └── details.md
```

## Complexity Tracking

No violations anticipated. Feature adds new domain services without changing existing architecture boundaries.

## Implementation Phases

### Phase 1: Domain Layer - Variable Substitution Core

1. Create `src/promptic/context/variables/models.py` with `VariableScope` and `SubstitutionContext` models
2. Create `src/promptic/context/variables/resolver.py` with scope matching logic
3. Create `src/promptic/context/variables/substitutor.py` with `VariableSubstitutor` service
4. Write unit tests for scope resolution and substitution logic

### Phase 2: Format Parser Updates

1. Update `base.py` to define variable marker pattern `{{var}}`
2. Update `markdown_parser.py` to preserve variable markers during parsing
3. Update `yaml_parser.py` to handle variables in YAML values
4. Update `json_parser.py` to handle variables in JSON strings
5. Update `jinja2_parser.py` to use native Jinja2 rendering for variables
6. Write unit tests for each parser with variables

### Phase 3: SDK Layer Integration

1. Update `render_node_network()` in `sdk/nodes.py` to accept `vars` parameter
2. Update `export_version()` in `sdk/api.py` to accept `vars` parameter
3. Integrate `VariableSubstitutor` into rendering pipeline (after reference resolution)
4. Write integration tests for render and export with variables

### Phase 4: Example and Documentation

1. Create example 7 with hierarchical structure and all three variable scoping methods
2. Write `docs_site/variables/insertion-guide.md` with comprehensive examples
3. Update `README.md` with variable insertion quick start
4. Add inline docstrings and `AICODE-NOTE` comments

### Phase 5: Testing and Quality

1. Run full test suite (`pytest tests/ -v`)
2. Verify coverage >85% for variable code (`pytest --cov=promptic.context.variables`)
3. Run pre-commit hooks (`pre-commit run --all-files`)
4. Fix any linting/formatting issues

## Data Model

### VariableScope

```python
class VariableScope(str, Enum):
    """Variable resolution scope levels."""
    SIMPLE = "simple"        # Global: {"var": "value"}
    NODE = "node"           # Node-scoped: {"node.var": "value"}
    PATH = "path"           # Full-path: {"root.group.node.var": "value"}
```

### SubstitutionContext

```python
@dataclass
class SubstitutionContext:
    """Context for variable substitution in a node."""
    node_id: str             # Node identifier
    hierarchical_path: str   # Full path in hierarchy (e.g., "root.group.node")
    content: str             # Content to substitute variables in
    format: str              # File format (affects substitution strategy)
```

### Variable Resolution Precedence

1. **Full-path match** (most specific): `"root.group.node.var"` matches only nodes at exact path
2. **Node-scoped match**: `"node_name.var"` matches all nodes with matching name
3. **Simple match** (global): `"var"` matches in all nodes

## Risk Mitigation

- **Risk**: Variable syntax conflicts with existing content (e.g., literal `{{text}}` in prompts)
  - **Mitigation**: Document escape mechanism, provide clear error messages, validate variable names
  
- **Risk**: Performance degradation with many variables in large hierarchies
  - **Mitigation**: Compile variable patterns once, use efficient string methods, benchmark with 1000-node hierarchies
  
- **Risk**: Jinja2 variable syntax differs from custom markers, causing confusion
  - **Mitigation**: Clear documentation showing Jinja2 uses native `{{ var }}`, others use `{{var}}`, provide examples for each

- **Risk**: Type preservation in YAML/JSON (integer/boolean values)
  - **Mitigation**: Document that string substitution is used (types not preserved), suggest using Jinja2 for type-aware substitution if needed
