# File-First Renderer Architecture

This document describes how the file-first renderer fits into the Clean Architecture layers (Entities → Use Cases → Interface Adapters) and documents the dependency flow to ensure all dependencies point inward.

## Architecture Overview

The file-first renderer follows Clean Architecture principles, organizing code into distinct layers with clear boundaries and dependency rules:

```
┌─────────────────────────────────────────────────────────────┐
│                    Interface Adapters                        │
│  FileSummaryService, ReferenceFormatter, ReferenceTreeBuilder│
│  (Adapt domain models to rendering needs)                   │
└───────────────────────┬─────────────────────────────────────┘
                        │ depends on
┌───────────────────────▼─────────────────────────────────────┐
│                      Use Cases                               │
│              FileFirstRenderer.render()                      │
│        (Orchestrates file-first rendering workflow)          │
└───────────────────────┬─────────────────────────────────────┘
                        │ depends on
┌───────────────────────▼─────────────────────────────────────┐
│                      Entities (Domain)                       │
│  PromptHierarchyBlueprint, InstructionReference,            │
│  MemoryChannel, RenderMetrics, ContextBlueprint             │
└───────────────────────┬─────────────────────────────────────┘
                        │ depends on
┌───────────────────────▼─────────────────────────────────────┐
│              ContextMaterializer (Interface)                 │
│  (Abstraction for instruction/data/memory access)            │
└─────────────────────────────────────────────────────────────┘
```

## Layer Breakdown

### Entities (Domain Layer)

**Location**: `src/promptic/blueprints/models.py`

Entities are pure domain objects with no dependencies on external frameworks or infrastructure. They represent core business concepts:

- **`PromptHierarchyBlueprint`**: Root entity containing persona, objectives, steps (as `InstructionReference` trees), memory channels, and render metrics. This is the primary output of file-first rendering.

- **`InstructionReference`**: Represents a reference to an instruction file with metadata (ID, title, summary, path, token estimate). Supports nested children for hierarchical structures.

- **`MemoryChannel`**: Describes memory/logging locations with format descriptors and retention policies.

- **`RenderMetrics`**: Captures token counts (before/after rendering) and reference statistics to prove token reduction.

- **`ContextBlueprint`**: Input entity representing the full blueprint structure with steps, data slots, and memory slots.

**Key Properties**:
- Entities contain no business logic beyond validation
- Entities have no knowledge of rendering, file I/O, or adapters
- Entities are serializable (Pydantic models) for persistence and API contracts

### Use Cases (Application Layer)

**Location**: `src/promptic/pipeline/format_renderers/file_first.py`

Use cases orchestrate the rendering workflow by coordinating entities and adapters:

- **`FileFirstRenderer.render()`**: Primary use case that:
  1. Extracts metadata from `ContextBlueprint` (persona, objectives, summary overrides)
  2. Creates adapter services (`FileSummaryService`, `ReferenceFormatter`, `ReferenceTreeBuilder`)
  3. Builds reference tree from blueprint steps
  4. Constructs `PromptHierarchyBlueprint` entity
  5. Renders markdown output
  6. Calculates and attaches `RenderMetrics`

**Dependency Rule**: Use cases depend on entities and interface adapters, but never on concrete infrastructure implementations. The `FileFirstRenderer` receives a `ContextMaterializer` (interface) rather than directly accessing filesystem or adapter registries.

**Registration**: The renderer is registered in `TemplateRenderer` (located in `src/promptic/pipeline/template_renderer.py`) via `_register_file_first_strategy()`, allowing callers to request `render_mode="file_first"` without coupling to the implementation.

### Interface Adapters

**Location**: `src/promptic/pipeline/format_renderers/file_first.py`

Adapters translate between domain entities and external concerns (file I/O, formatting, tree building):

#### `FileSummaryService`
- **Responsibility**: Summarizes instruction files to ≤120 tokens for compact references
- **SOLID Principles**:
  - **SRP**: Single responsibility—summarization only
  - **OCP**: Extensible via `overrides` parameter (open for extension, closed for modification)
  - **DIP**: Depends on `ContextMaterializer` abstraction, not concrete filesystem
- **Dependencies**: `ContextMaterializer` (interface), `InstructionNode` (entity)

#### `ReferenceFormatter`
- **Responsibility**: Formats relative paths into absolute URLs when `base_url` is provided
- **SOLID Principles**:
  - **SRP**: Formatting paths/hints only
  - **DIP**: Depends on `base_url` abstraction (can be None for relative paths)
- **Dependencies**: None (pure formatting logic)

#### `ReferenceTreeBuilder`
- **Responsibility**: Builds nested `InstructionReference` trees from `BlueprintStep` hierarchies with cycle detection and depth limiting
- **SOLID Principles**:
  - **SRP**: Tree construction only
  - **ISP**: Minimal public interface (`build()` method)
  - **DIP**: Depends on `FileSummaryService` and `ReferenceFormatter` abstractions
- **Dependencies**: `ContextBlueprint` (entity), `FileSummaryService` (adapter), `ReferenceFormatter` (adapter)

#### `RenderMetricsBuilder`
- **Responsibility**: Calculates token deltas and reference counts
- **SOLID Principles**:
  - **SRP**: Metrics calculation only
- **Dependencies**: `InstructionReference` (entity), token estimation utilities

### ContextMaterializer (Interface Abstraction)

**Location**: `src/promptic/pipeline/context_materializer.py`

`ContextMaterializer` is the **sole gateway** to instruction stores, data adapters, and memory providers. It enforces dependency inversion by:

1. **Encapsulating adapter registries**: Preview/executor flows never access `AdapterRegistry` directly
2. **Providing caching**: LRU caches for instructions, data, and memory to avoid redundant I/O
3. **Resolving instructions**: `resolve_instruction()` returns `OperationResult[Tuple[InstructionNode, str]]` with error handling

**Why This Matters**: The file-first renderer depends on `ContextMaterializer` (interface), not on concrete filesystem stores or adapter implementations. This allows:
- Swapping instruction stores (filesystem → S3 → database) without changing renderer code
- Testing renderer with mock materializers
- Maintaining clean layer boundaries

## Dependency Flow

All dependencies point **inward** (toward domain entities):

```
External Infrastructure (Filesystem, Adapters)
         ↑
         │ implements
         │
ContextMaterializer (Interface)
         ↑
         │ depends on
         │
Interface Adapters (FileSummaryService, etc.)
         ↑
         │ depends on
         │
Use Cases (FileFirstRenderer)
         ↑
         │ depends on
         │
Entities (PromptHierarchyBlueprint, etc.)
```

**Key Rules**:
1. ✅ Entities have **zero** dependencies on other layers
2. ✅ Use cases depend on entities and adapters, **never** on infrastructure
3. ✅ Adapters depend on entities and interfaces, **never** on concrete implementations
4. ✅ Infrastructure (filesystem, adapters) implements interfaces defined in domain/use case layers

## Integration Points

### TemplateRenderer Registration

The file-first renderer is registered in `TemplateRenderer._register_file_first_strategy()`:

```python
# src/promptic/pipeline/template_renderer.py
def _register_file_first_strategy(self) -> None:
    from promptic.pipeline.format_renderers.file_first import FileFirstRenderer
    self._strategies["file_first"] = FileFirstRenderer()
```

This allows callers to use:
```python
template_renderer.render_file_first(
    blueprint=blueprint,
    materializer=materializer,  # Interface, not concrete implementation
    base_url="https://kb.example.com",
)
```

### SDK Integration

The SDK (`src/promptic/sdk/blueprints.py`) wires the renderer through `TemplateRenderer`, ensuring:
- Materializer is injected (dependency injection)
- Settings flow through materializer, not directly to renderer
- Errors are surfaced as `PrompticError` subclasses

## SOLID Principles in Practice

### Single Responsibility Principle (SRP)
- `FileSummaryService`: Summarization only
- `ReferenceFormatter`: Path formatting only
- `ReferenceTreeBuilder`: Tree construction only
- `RenderMetricsBuilder`: Metrics calculation only

### Open/Closed Principle (OCP)
- `FileSummaryService` accepts `overrides` parameter for extension without modification
- `ReferenceFormatter` supports optional `base_url` without changing core logic
- New render strategies can be added via `TemplateRenderer.register_renderer()` without modifying existing code

### Liskov Substitution Principle (LSP)
- Any `ContextMaterializer` implementation can be used (filesystem, mock, remote store)
- `InstructionReference` trees can be extended with new metadata without breaking existing code

### Interface Segregation Principle (ISP)
- `ContextMaterializer` provides focused methods (`resolve_instruction`, `resolve_data`, `resolve_memory`)
- Adapters expose minimal public interfaces

### Dependency Inversion Principle (DIP)
- `FileFirstRenderer` depends on `ContextMaterializer` (interface), not concrete stores
- Adapters depend on entity abstractions, not concrete implementations
- All dependencies point toward domain entities

## Testing Implications

The architecture enables clean testing:

1. **Unit Tests**: Test adapters with mock entities and materializers
2. **Integration Tests**: Test use cases with real materializers but mock adapters
3. **Contract Tests**: Verify entity serialization and API contracts

Example test structure:
```python
# Unit test: FileSummaryService with mock materializer
def test_summarize_truncates_content():
    mock_materializer = MockMaterializer()
    service = FileSummaryService(materializer=mock_materializer)
    # Test summarization logic in isolation

# Integration test: FileFirstRenderer with real materializer
def test_render_produces_hierarchy():
    materializer = build_materializer(settings)
    renderer = FileFirstRenderer()
    result = renderer.render(blueprint=blueprint, materializer=materializer)
    # Verify PromptHierarchyBlueprint structure
```

## Future Extensibility

The architecture supports future enhancements without breaking existing code:

- **New render strategies**: Register via `TemplateRenderer` without modifying file-first renderer
- **New instruction stores**: Implement `InstructionResolver` interface, inject via `ContextMaterializer`
- **New metrics**: Extend `RenderMetrics` entity, update `RenderMetricsBuilder` adapter
- **New reference formats**: Extend `ReferenceFormatter` or create new formatter adapters

All extensions maintain the dependency rule: **dependencies point inward toward domain entities**.
