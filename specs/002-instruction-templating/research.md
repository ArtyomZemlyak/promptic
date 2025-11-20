# Research: Instruction Data Insertion with Multiple Templating Formats

## Template Renderer Architecture

- **Decision**: Introduce `TemplateRenderer` abstraction in use-case layer that dispatches to format-specific renderers based on `InstructionNode.format` field. Format renderers implement `FormatRenderer` interface following dependency inversion.
- **Rationale**: Clean architecture separation keeps domain entities (`InstructionNode`) unaware of rendering details. Interface-based design enables swapping implementations and testing without modifying use cases. Format detection already exists in `InstructionNode.format`, so dispatcher leverages existing infrastructure.
- **Alternatives considered**:
  - Monolithic renderer handling all formats: violates SRP, makes format-specific optimizations difficult, harder to test individual formats.
  - Format detection in domain layer: violates clean architecture by mixing rendering concerns with domain entities.

## Markdown Format Rendering

- **Decision**: Use Python string format syntax (`{}` placeholders) with support for nested dictionary access via dot notation (`{user.profile.name}`). Implement custom parser that handles escaping (`{{` → `{`), nested access, and preserves formatting.
- **Rationale**: Python string format is familiar to Python developers, simple for common use cases, and doesn't require learning new syntax. Nested access enables rich data structures without flattening. Escaping preserves literal braces in instructions.
- **Alternatives considered**:
  - Jinja2 for Markdown: Overkill for simple substitution, adds dependency complexity, conflicts with `.jinja` format distinction.
  - Custom DSL: Requires parser maintenance, steeper learning curve, harder to debug.

## Jinja2 Environment Configuration

- **Decision**: Use separate Jinja2 environment for instruction rendering with shared base configuration managed through settings. Instruction-specific filters and globals are added to instruction environment without affecting prompt rendering environment.
- **Rationale**: Separation enables instruction-specific helpers (e.g., `format_step()`, `get_parent_step()`) without risk to prompt templates. Shared base configuration ensures consistency (autoescape, undefined handling) while allowing format-specific customization. Aligns with clean architecture by isolating concerns.
- **Alternatives considered**:
  - Shared environment: Couples instruction and prompt rendering, makes it impossible to add instruction-specific helpers safely.
  - Completely separate configuration: Duplicates base settings, harder to maintain consistency.

## Context Variable Namespacing

- **Decision**: Provide namespaced context variables (`data.*`, `memory.*`, `step.*`) to avoid conflicts with user-provided data keys. Global context (data slots, memory slots, blueprint metadata) and step-specific context (step_id, title, kind, hierarchy, loop_item) are both available.
- **Rationale**: Namespacing prevents variable name collisions between blueprint context and user data. Both global and step-specific context enable step-aware instructions while maintaining access to all blueprint data. Clear namespace boundaries make template authoring predictable.
- **Alternatives considered**:
  - Flat context with prefix conventions: Less explicit, higher collision risk, harder to document.
  - Step-only context: Loses access to global data slots/memory, limiting instruction flexibility.

## Error Handling with InstructionFallbackPolicy

- **Decision**: Template rendering errors are handled according to `InstructionFallbackPolicy` configured for the instruction. `error` policy raises `TemplateRenderError`, `warn` policy emits structured warnings and continues with placeholder substitution, `noop` policy suppresses content and continues with empty string.
- **Rationale**: Aligns with existing fallback semantics used for instruction loading failures, providing consistent error handling across the library. Enables graceful degradation for optional instructions while maintaining strict validation for required ones.
- **Alternatives considered**:
  - Always fail on template errors: Too rigid, prevents graceful degradation for optional instructions.
  - Always continue with warnings: Loses strict validation for required instructions, makes debugging harder.

## Per-Iteration Loop Context

- **Decision**: For loop steps, each iteration renders instructions with per-iteration context including `step.loop_item` containing the current iteration item. Instructions are rendered once per iteration, not once per step.
- **Rationale**: Enables instructions like "Process source: {{ step.loop_item.title }}" for each loop iteration, aligning with the hierarchical/iterative nature of blueprints. Agent systems can call rendering function multiple times with different loop_item values, or library can provide iteration support.
- **Alternatives considered**:
  - Single rendering per step: Loses per-iteration context, makes loop-aware instructions impossible.
  - Library handles iteration internally: Couples library to execution semantics, violates separation of concerns (library is for context construction, not execution).

## YAML Custom Pattern Configuration

- **Decision**: Custom placeholder patterns for YAML instructions are specified in instruction metadata (`InstructionNode.pattern` field) or instruction provider configuration. Patterns are validated as regex or safe string replacement semantics.
- **Rationale**: YAML format is flexible and teams may have existing conventions. Configurable patterns enable adaptation to specific use cases without hardcoding syntax. Validation ensures patterns are safe and don't conflict with literal text.
- **Alternatives considered**:
  - Hardcoded YAML pattern: Inflexible, doesn't support team conventions.
  - Pattern in blueprint: Couples blueprint to instruction format details, violates separation of concerns.

## Markdown Hierarchy Parsing (P3)

- **Decision**: Markdown hierarchy parsing extracts hierarchical structure from heading levels and conditional markers (`<!-- if:condition -->`). Parser runs during instruction loading, producing structured metadata that informs rendering decisions without altering instruction content.
- **Rationale**: Enables hierarchical logic in Markdown files, reducing reliance on YAML blueprints for simple scenarios. Parsing during loading separates concerns (parsing vs rendering) and produces metadata that can be used for conditional rendering.
- **Alternatives considered**:
  - Runtime parsing during rendering: Duplicates parsing work, harder to cache metadata.
  - Embedded in instruction content: Alters instruction content, makes it harder to extract structure.

## Integration with Context Engine

- **Decision**: Template rendering is integrated into `ContextPreviewer._resolve_instruction_text()` by modifying it to accept template context and route through `TemplateRenderer`. Existing instruction loading flows remain unchanged; rendering happens after content is loaded.
- **Rationale**: Minimal changes to existing codebase, maintains clean architecture boundaries, leverages existing instruction loading infrastructure. Template rendering is a use-case concern, so integration in previewer (use-case layer) is appropriate.
- **Alternatives considered**:
  - Separate rendering step in SDK: Adds complexity, duplicates context building logic.
  - Rendering in instruction store: Violates clean architecture by mixing storage and rendering concerns.

## Format Detection and Override

- **Decision**: Format detection uses existing `InstructionNode.format` field (derived from file extension). Override mechanism allows explicit format specification when file extension doesn't match content or for edge cases.
- **Rationale**: Leverages existing format detection infrastructure, maintains consistency with context engine. Override mechanism handles edge cases (e.g., `.md` file with Jinja2 syntax) without breaking normal workflows.
- **Alternatives considered**:
  - Content-based auto-detection: Unreliable, adds complexity, may misidentify formats.
  - No override mechanism: Inflexible, doesn't handle edge cases.
