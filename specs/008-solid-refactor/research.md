# Research: SOLID Refactoring - Code Analysis

**Branch**: `008-solid-refactor` | **Date**: 2025-11-25

## Code Duplication Analysis

### Primary Target: `sdk/nodes.py` - `render_node_network`

#### Quantitative Analysis

| Metric | Value |
|--------|-------|
| Total function lines | ~750 |
| `process_node_content` definitions | 4 |
| `replace_jinja2_ref` definitions | 4 |
| `replace_markdown_ref` definitions | 4 |
| `replace_refs_in_dict` definitions | 4 |
| Pattern matches for duplicates | 25 |
| Estimated duplication | ~70% |

#### Code Blocks Identified for Extraction

**Block 1: Jinja2 Reference Processing (lines ~369-397, ~492-510, ~556-581, etc.)**

```python
# Pattern repeated 4+ times
jinja2_ref_pattern = re.compile(r"\{\#\s*ref:\s*([^\#]+)\s*\#\}", re.IGNORECASE)

def replace_jinja2_ref(match: re.Match[str]) -> str:
    path = match.group(1).strip()
    child = None
    for node_id, n in network.nodes.items():
        if (
            path == str(node_id)
            or path in str(node_id)
            or str(node_id).endswith(path)
        ):
            child = n
            break
    if child:
        child_content = process_node_content(child)
        if isinstance(child_content, str):
            return child_content
        else:
            return yaml.dump(child_content, default_flow_style=False, sort_keys=False).strip()
    return match.group(0)
```

**Block 2: Markdown Link Processing (lines ~401-431, ~513-535, ~584-609, etc.)**

```python
# Pattern repeated 4+ times
markdown_ref_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

def replace_markdown_ref(match: re.Match[str]) -> str:
    path = match.group(2)
    if path.startswith(("http://", "https://", "mailto:")):
        return match.group(0)
    child = None
    for node_id, n in network.nodes.items():
        if (
            path == str(node_id)
            or path in str(node_id)
            or str(node_id).endswith(path)
        ):
            child = n
            break
    if child:
        child_content = process_node_content(child)
        if isinstance(child_content, str):
            return child_content
        else:
            return yaml.dump(child_content, default_flow_style=False, sort_keys=False).strip()
    return match.group(0)
```

**Block 3: Structured Ref Processing ($ref in YAML/JSON) (lines ~435-474, ~613-651, etc.)**

```python
# Pattern repeated 4+ times
def replace_refs_in_dict(data: dict[str, Any]) -> dict[str, Any]:
    result = {}
    for key, value in data.items():
        if isinstance(value, dict):
            if "$ref" in value:
                ref_path = value["$ref"]
                if isinstance(ref_path, str):
                    child = None
                    for node_id, n in network.nodes.items():
                        if (
                            ref_path == str(node_id)
                            or ref_path in str(node_id)
                            or str(node_id).endswith(ref_path)
                        ):
                            child = n
                            break
                    if child:
                        child_content = process_node_content(child)
                        result[key] = child_content
                    else:
                        result[key] = value
                else:
                    result[key] = value
            else:
                result[key] = replace_refs_in_dict(value)
        elif isinstance(value, list):
            result[key] = [
                replace_refs_in_dict(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value
    return result
```

**Block 4: Node Lookup Logic (repeated in all blocks)**

```python
# This exact pattern appears 12+ times
child = None
for node_id, n in network.nodes.items():
    if (
        path == str(node_id)
        or path in str(node_id)
        or str(node_id).endswith(path)
    ):
        child = n
        break
```

### Secondary Target: `versioning/domain/exporter.py` - `export_version`

#### Quantitative Analysis

| Metric | Value |
|--------|-------|
| Total function lines | ~230 |
| Nested function definitions | 3 |
| Distinct responsibilities | 5+ |
| Cyclomatic complexity | High |

#### Responsibilities Mixed in Single Function

1. **Validation**: `validate_export_target()`
2. **Version Resolution**: `resolve_version()` call
3. **File Discovery**: `discover_versioned_files()`, `discover_referenced_files()`
4. **File Mapping**: Building `file_mapping` dict
5. **Content Processing**: `content_processor` nested function
6. **Export Execution**: `export_files()` call
7. **Result Handling**: Building `ExportResult`

## Refactoring Patterns

### Strategy Pattern for Reference Types

**Problem**: Different reference types (jinja2, markdown, $ref) require different regex patterns and processing, but share common lookup logic.

**Solution**: Strategy pattern where each strategy:
- Defines its own detection pattern
- Implements processing specific to its format
- Delegates to shared node lookup service

```
┌──────────────────┐
│ ReferenceInliner │
├──────────────────┤
│ strategies[]     │──────┬────────────────────────────────┐
│ inline()         │      │                                │
└──────────────────┘      │                                │
                          ▼                                ▼
              ┌─────────────────────┐          ┌─────────────────────┐
              │ MarkdownLinkStrategy│          │ Jinja2RefStrategy   │
              ├─────────────────────┤          ├─────────────────────┤
              │ pattern: [text](p)  │          │ pattern: {# ref: #} │
              │ process()           │          │ process()           │
              └─────────────────────┘          └─────────────────────┘
                                                          │
                          ┌───────────────────────────────┘
                          ▼
              ┌─────────────────────┐
              │ StructuredRefStrategy│
              ├─────────────────────┤
              │ pattern: {"$ref": } │
              │ process()           │
              └─────────────────────┘
```

### Extract Method for VersionExporter

**Problem**: `export_version()` has too many responsibilities.

**Solution**: Extract private methods for each responsibility:

```python
class VersionExporter:
    def export_version(self, ...):
        self._validate_export(target_dir, overwrite)
        resolved_root = self._resolve_root_version(source_path, version_spec)
        file_mapping = self._build_file_mapping(source_base, target, version_spec)
        processor = self._create_content_processor(vars, hierarchical_paths)
        return self._execute_export(file_mapping, target, processor)
    
    def _validate_export(self, target_dir, overwrite): ...
    def _resolve_root_version(self, source_path, version_spec): ...
    def _build_file_mapping(self, source_base, target, version_spec): ...
    def _create_content_processor(self, vars, hierarchical_paths): ...
    def _execute_export(self, file_mapping, target, processor): ...
```

## Existing Patterns in Codebase

### Pattern Registry (format_parsers/registry.py)

The codebase already uses registry pattern for format parsers:

```python
class FormatParserRegistry:
    def register(self, format_name, parser, extensions): ...
    def get_parser(self, format_name): ...
```

**Applicability**: Could use similar pattern for strategy registration, but may be overkill. Simple list injection is sufficient.

### Abstract Base Classes (format_parsers/base.py)

```python
class FormatParser(ABC):
    @abstractmethod
    def detect(self, content, path): ...
    @abstractmethod
    def parse(self, content, path): ...
```

**Applicability**: Use same ABC pattern for `ReferenceStrategy`.

### Dependency Injection (pipeline/network/builder.py)

```python
class NodeNetworkBuilder:
    def __init__(self, resolver: NodeReferenceResolver | None = None):
        self.resolver = resolver or FilesystemReferenceResolver()
```

**Applicability**: Use same DI pattern for `ReferenceInliner` with strategies.

## Risk Analysis

### Breaking Changes Risk

| Component | Risk Level | Reason |
|-----------|------------|--------|
| Public API | Low | `render()`, `render_node_network()` signatures unchanged |
| Internal behavior | Medium | Edge cases in reference resolution |
| Performance | Low | Strategy overhead is minimal |

### Mitigation Strategy

1. **Snapshot Testing**: Capture current output for all example files
2. **A/B Comparison**: Run both implementations in parallel during development
3. **Incremental Refactoring**: Extract one strategy at a time, verify after each

## Conclusion

The refactoring is feasible with well-defined extraction points. Primary risk is regression in edge cases, mitigated by comprehensive testing before extraction begins.

**Recommended Approach**:
1. Write characterization tests capturing current behavior
2. Extract strategies one at a time
3. Create `ReferenceInliner` using extracted strategies
4. Swap implementation in `render_node_network`
5. Remove duplicate code
6. Repeat for `VersionExporter`

