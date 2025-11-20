# Data Model: Instruction Data Insertion with Multiple Templating Formats

All models will be implemented as `pydantic.BaseModel` subclasses (domain layer) or protocol/ABC interfaces (use-case layer) to guarantee validation, serialization, and compatibility with `pydantic-settings`.

## TemplateRenderer

**Layer**: Use-case layer  
**Location**: `src/promptic/pipeline/template_renderer.py`

Abstraction that coordinates format-specific rendering. Dispatches to format-specific renderers based on instruction format.

| Method | Signature | Description |
|--------|-----------|-------------|
| `render` | `(instruction_node: InstructionNode, content: str, context: InstructionRenderContext) -> str` | Renders instruction content with template context, routing to appropriate format renderer based on `instruction_node.format` |

## FormatRenderer (Interface)

**Layer**: Use-case layer (interface)  
**Location**: `src/promptic/pipeline/format_renderers/base.py`

Interface for format-specific rendering implementations. Each format renderer implements this interface.

| Method | Signature | Description |
|--------|-----------|-------------|
| `render` | `(content: str, context: InstructionRenderContext) -> str` | Renders content with template context using format-specific syntax |
| `supports_format` | `(format: str) -> bool` | Returns True if this renderer supports the given format |

**Implementations**:
- `MarkdownFormatRenderer`: Handles `"md"` format with `{}` placeholders
- `Jinja2FormatRenderer`: Handles `"jinja"` format with Jinja2 syntax
- `YamlFormatRenderer`: Handles `"yaml"`/`"yml"` format with custom patterns

## InstructionRenderContext

**Layer**: Use-case layer  
**Location**: `src/promptic/context/template_context.py`

Context object passed to renderers containing blueprint data, step information, and template variables.

| Field | Type | Description |
|-------|------|-------------|
| `data` | `Dict[str, Any]` | Data slot values (namespaced as `data.*` in templates) |
| `memory` | `Dict[str, Any]` | Memory slot values (namespaced as `memory.*` in templates) |
| `step` | `Optional[StepContext]` | Step-specific information (namespaced as `step.*` in templates) |
| `blueprint` | `Dict[str, Any]` | Blueprint metadata (full blueprint dump) |

**StepContext** (nested):

| Field | Type | Description |
|-------|------|-------------|
| `step_id` | `str` | Current step identifier |
| `title` | `str` | Step title |
| `kind` | `str` | Step kind (`sequence`, `loop`, `branch`) |
| `hierarchy` | `List[str]` | Parent step IDs (hierarchical position) |
| `loop_item` | `Optional[Any]` | Current loop iteration item (for loop steps) |

**Context Variable Namespacing**:
- `data.*`: Access to data slot values (e.g., `data.sources`, `data.user.name`)
- `memory.*`: Access to memory slot values (e.g., `memory.prior_findings`)
- `step.*`: Access to step-specific information (e.g., `step.step_id`, `step.loop_item.title`)
- `blueprint.*`: Access to blueprint metadata (e.g., `blueprint.name`, `blueprint.id`)

## TemplateRenderError

**Layer**: Domain layer  
**Location**: `src/promptic/context/errors.py` (extends existing error types)

Domain exception raised when template rendering fails.

| Field | Type | Description |
|-------|------|-------------|
| `instruction_id` | `str` | Instruction that failed to render |
| `format` | `str` | Instruction format |
| `error_type` | `Literal["missing_placeholder", "syntax_error", "type_mismatch", "circular_reference"]` | Type of rendering error |
| `message` | `str` | Descriptive error message |
| `line_number` | `Optional[int]` | Line number where error occurred (if applicable) |
| `placeholder` | `Optional[str]` | Placeholder that caused error (if applicable) |

## InstructionNode (Extended)

**Layer**: Domain layer  
**Location**: `src/promptic/blueprints/models.py` (existing entity)

Existing entity extended with optional pattern field for YAML custom patterns.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `format` | `Literal["md", "txt", "jinja"]` | Instruction format (existing) | Must match file extension or override |
| `pattern` | `Optional[str]` | Custom placeholder pattern for YAML format | Valid regex or safe string replacement; required when format is `yaml`/`yml` and custom pattern used |

**Note**: `InstructionNode` already exists in context engine. This feature adds optional `pattern` field for YAML custom patterns. Format detection and validation remain unchanged.

## MarkdownHierarchyParser (P3 - Optional)

**Layer**: Use-case layer  
**Location**: `src/promptic/pipeline/format_renderers/markdown_hierarchy.py`

Optional parser that extracts hierarchical structure from Markdown instruction files.

| Method | Signature | Description |
|--------|-----------|-------------|
| `parse` | `(content: str) -> MarkdownHierarchy` | Extracts hierarchical structure from Markdown content |
| `extract_conditionals` | `(content: str) -> List[ConditionalSection]` | Extracts conditional markers (`<!-- if:condition -->`) |

**MarkdownHierarchy**:

| Field | Type | Description |
|-------|------|-------------|
| `sections` | `List[Section]` | Hierarchical sections extracted from headings |
| `conditionals` | `List[ConditionalSection]` | Conditional sections with markers |

**Section**:

| Field | Type | Description |
|-------|------|-------------|
| `level` | `int` | Heading level (1-6) |
| `title` | `str` | Section title |
| `content` | `str` | Section content |
| `children` | `List[Section]` | Nested child sections |

**ConditionalSection**:

| Field | Type | Description |
|-------|------|-------------|
| `condition` | `str` | Condition expression |
| `content` | `str` | Conditional content |
| `start_line` | `int` | Starting line number |
| `end_line` | `int` | Ending line number |

## Relationships

- `TemplateRenderer` uses `FormatRenderer` implementations (dependency inversion)
- `FormatRenderer` implementations use `InstructionRenderContext` for template variables
- `InstructionRenderContext` references `ContextBlueprint` and `BlueprintStep` (domain entities)
- `TemplateRenderError` is raised by format renderers and handled according to `InstructionFallbackPolicy`
- `InstructionNode.format` drives format renderer selection
- `InstructionNode.pattern` (optional) configures YAML custom pattern rendering
