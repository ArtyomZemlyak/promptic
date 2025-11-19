# Integration Analysis: Context Engine and Instruction Templating

**Created**: 2025-01-28  
**Purpose**: Analyze changes made in context engine (001-context-engine) and how they relate to instruction templating (001-instruction-templating) to identify conflicts, overlaps, and integration points.

## Executive Summary

The context engine (001-context-engine) is **implemented** and uses Jinja2 for rendering blueprint `prompt_template` fields. Instruction templating (001-instruction-templating) is now **implemented** with dedicated format renderers, hierarchy parsing, and loop-aware contexts. Key outcomes:

- ✅ **TemplateRenderer integration**: `ContextPreviewer` now routes every instruction through the dispatcher, applying `InstructionFallbackPolicy` semantics automatically.
- ✅ **Namespaced context variables**: `InstructionRenderContext` exposes `data.*`, `memory.*`, `step.*` (including `step.loop_item`), and `blueprint.*`. Documentation lives in `docs_site/context-engineering/template-context-variables.md`.
- ✅ **Separate instruction Jinja2 environment**: `Jinja2FormatRenderer` lazily instantiates its own environment with instruction-specific filters/globals (`format_step`, `get_parent_step`) while keeping base config aligned with prompt rendering.
- ✅ **Markdown hierarchy parsing**: `MarkdownHierarchyParser` powers conditional sections and heading metadata so purely Markdown instructions can express lightweight logic.
- ✅ **Loop iteration support**: `build_instruction_context()` accepts a `loop_item` parameter and the new integration test `tests/integration/test_loop_iteration_templating.py` verifies each iteration receives a unique context.
- ⚠️ **Future work**: Continue expanding contract coverage (`tests/contract/test_template_context_contract.py`) and polish performance benchmarks.

---

## 1. Context Engine Implementation Status

### 1.1 What Was Implemented

**Location**: `src/promptic/context/rendering.py`

- **Jinja2 for prompt templates**: The `_render_prompt()` function uses Jinja2 to render `blueprint.prompt_template` with context variables
- **Template context structure**: Built in `ContextPreviewer.preview()` (lines 114-121):
  ```python
  template_context = {
      "blueprint": blueprint.model_dump(),
      "data": data_values,
      "memory": memory_values,
      "sample_data": data_values or sample_data,  # Back-compat
      "sample_memory": memory_values or sample_memory,  # Back-compat
  }
  ```
- **Jinja2 environment**: Uses `StrictUndefined` with fallback to `DebugUndefined` on errors
- **Error handling**: Template errors are captured as warnings, rendering continues with fallback

**Location**: `src/promptic/blueprints/models.py`

- **InstructionNode.format field**: Already exists with values `"md"`, `"txt"`, `"jinja"` (line 73)
- **Format detection**: Implemented in `FilesystemInstructionStore` based on file extension

**Location**: `src/promptic/pipeline/previewer.py`

- **Instruction loading**: `_resolve_instruction_text()` loads instructions as **plain text** (no templating)
- **Instruction content**: Currently returned as raw strings without any data injection

### 1.2 Current Instruction Flow

```
Blueprint → InstructionNodeRef → ContextMaterializer.resolve_instruction_refs()
  → InstructionStore.load_content() → Returns raw string → Passed to rendering
```

**Key observation**: Instructions are loaded as plain text and passed directly to rendering functions without any template processing.

---

## 2. Instruction Templating Requirements

### 2.1 What the Spec Requires

From `specs/001-instruction-templating/spec.md`:

- **FR-001**: Markdown instructions with `{}` placeholders (Python string format syntax)
- **FR-002**: Jinja2 templating for `.jinja` instruction files
- **FR-003**: Custom pattern templating for YAML instructions
- **FR-006**: Blueprint context (data slots, memory slots, step hierarchy, step_id) available during template rendering
- **FR-008**: Nested dictionary access in Markdown (`{user.profile.name}`)

### 2.2 Architecture Requirements

- **TemplateRenderer**: Abstraction in use-case layer for format-specific rendering
- **FormatRenderer**: Interface for format-specific implementations
- **InstructionRenderContext**: Context object with blueprint data, step info, hierarchical position

---

## 3. Integration Points Analysis

### 3.1 ✅ No Conflicts: Jinja2 Usage

**Context Engine**: Uses Jinja2 for `prompt_template` rendering  
**Instruction Templating**: Will use Jinja2 for `.jinja` instruction files

**Analysis**: These are separate concerns:
- Prompt templates are rendered once per blueprint preview/execution
- Instruction templates are rendered per instruction file, potentially multiple times per blueprint

**Recommendation**: ✅ No conflict. Consider separate Jinja2 environments if different configurations are needed (filters, globals, etc.).

### 3.2 ✅ Alignment: Format Field

**Context Engine**: `InstructionNode.format` field exists with `"md"`, `"txt"`, `"jinja"`  
**Instruction Templating**: Spec relies on `format` field to route to appropriate renderer

**Analysis**: Perfect alignment. The format field is already implemented and will drive template renderer selection.

**Recommendation**: ✅ No changes needed. Format field is ready for templating implementation.

### 3.3 ⚠️ Integration Point: Instruction Rendering Flow

**Current Flow** (from `previewer.py`):
```python
def _resolve_instruction_text(self, refs, instruction_ids):
    result = self._materializer.resolve_instruction_refs(refs)
    # ... error handling ...
    payloads = []
    for node, content in result.unwrap():
        instruction_ids.append(node.instruction_id)
        payloads.append(content)  # ← Raw content, no templating
    return payloads, warnings, None
```

**Required Flow** (per templating spec):
```python
def _resolve_instruction_text(self, refs, instruction_ids, template_context):
    result = self._materializer.resolve_instruction_refs(refs)
    # ... error handling ...
    payloads = []
    for node, content in result.unwrap():
        instruction_ids.append(node.instruction_id)
        # ← Need to render content with template_context
        rendered = template_renderer.render(node, content, template_context)
        payloads.append(rendered)
    return payloads, warnings, None
```

**Analysis**: The instruction resolution flow needs modification to:
1. Accept template context (data slots, memory slots, step info)
2. Route through template renderer based on `node.format`
3. Return rendered content instead of raw content

**Recommendation**: ⚠️ **Modify `ContextPreviewer._resolve_instruction_text()`** to accept template context and call template renderer. This is a **breaking change** to the internal API but maintains external API compatibility.

### 3.4 ⚠️ Integration Point: Context Variable Scope

**Context Engine**: `template_context` includes:
- `blueprint`: Full blueprint dump
- `data`: Resolved data slot values
- `memory`: Resolved memory slot values
- `sample_data`, `sample_memory`: Back-compat aliases

**Instruction Templating Spec (FR-006)**: Requires:
- Data slots
- Memory slots
- Step hierarchy
- `step_id` (current step)

**Analysis**: Current `template_context` has data/memory but lacks:
- Step-specific context (`step_id`, step hierarchy position)
- Step-level data (for loop steps, the current iteration item)

**Recommendation**: ⚠️ **Clarification needed**: Should instruction templates have access to:
1. **Global context only** (all data/memory slots, blueprint metadata)?
2. **Step-specific context** (current step_id, loop iteration item, parent steps)?
3. **Both** (with clear precedence rules)?

**Suggested approach**: Provide both global and step-specific context:
```python
instruction_context = {
    **template_context,  # Global: blueprint, data, memory
    "step": {
        "step_id": current_step.step_id,
        "title": current_step.title,
        "kind": current_step.kind,
        "hierarchy": [...],  # Parent steps
        "loop_item": current_loop_item,  # For loop steps
    }
}
```

### 3.5 ⚠️ Integration Point: Jinja2 Environment Configuration

**Context Engine**: Uses default Jinja2 environment:
```python
env = Environment(autoescape=False, undefined=StrictUndefined)
```

**Instruction Templating Spec**: Mentions "Jinja2 environment configuration (filters, globals) is managed through settings"

**Analysis**: Potential conflict if:
- Different Jinja2 configurations needed for prompt vs instruction rendering
- Custom filters/globals for instructions that shouldn't affect prompts

**Recommendation**: ⚠️ **Clarification needed**: Should instruction Jinja2 rendering:
1. **Share the same environment** as prompt rendering (simpler, consistent)?
2. **Use a separate environment** (more flexible, isolated)?

**Suggested approach**: Separate environments with shared base configuration:
```python
# Base configuration in settings
jinja2_base_config = settings.jinja2_config

# Prompt rendering (existing)
prompt_env = Environment(**jinja2_base_config, undefined=StrictUndefined)

# Instruction rendering (new)
instruction_env = Environment(
    **jinja2_base_config,
    undefined=StrictUndefined,
    filters=instruction_specific_filters,
    globals=instruction_specific_globals,
)
```

### 3.6 ⚠️ Integration Point: Rendering Order

**Current Flow**:
1. Load blueprint
2. Resolve data/memory slots
3. Load instruction content (raw)
4. Build template_context
5. Render prompt template with context
6. Combine prompt + instructions (raw) for output

**Required Flow** (with templating):
1. Load blueprint
2. Resolve data/memory slots
3. Build template_context
4. Load instruction content
5. **Render instruction templates with context** ← NEW
6. Render prompt template with context
7. Combine prompt + rendered instructions for output

**Analysis**: Instruction templating must happen **after** data/memory resolution but **before** final context assembly. The current flow already supports this order.

**Recommendation**: ✅ **No conflict**. The flow order is compatible. Instruction rendering should be inserted between step 3 and 5.

---

## 4. Clarifications Needed

### 4.1 Context Variable Scope (HIGH PRIORITY)

**Question**: What context variables should be available in instruction templates?

**Options**:
- **A) Global only**: All data/memory slots, blueprint metadata (simpler, consistent across all instructions)
- **B) Step-specific**: Current step_id, loop item, hierarchy (more powerful, enables step-aware instructions)
- **C) Both with namespacing**: `data.*`, `memory.*`, `step.*` (most flexible, clearest separation)

**Recommendation**: **Option C** - Both with clear namespacing to avoid conflicts and enable step-aware instructions.

**Impact**: Affects template renderer interface and context building logic.

---

### 4.2 Jinja2 Environment Configuration (MEDIUM PRIORITY)

**Question**: Should instruction Jinja2 rendering use the same environment as prompt rendering?

**Options**:
- **A) Shared environment**: Same filters, globals, configuration (simpler, consistent)
- **B) Separate environment**: Different filters/globals for instructions (more flexible, isolated)

**Recommendation**: **Option B** - Separate environments with shared base config. Allows instruction-specific filters (e.g., `format_step()`, `get_parent_step()`) without affecting prompt rendering.

**Impact**: Affects template renderer implementation and settings structure.

---

### 4.3 Template Rendering Error Handling (MEDIUM PRIORITY)

**Question**: How should template rendering errors be handled in instructions?

**Context Engine**: Prompt template errors are captured as warnings, rendering continues with fallback.

**Options**:
- **A) Same as prompts**: Warnings, continue with fallback (consistent behavior)
- **B) Fail fast**: Raise exceptions for instruction template errors (stricter, fails early)
- **C) Configurable per instruction**: Use `InstructionFallbackPolicy` to control behavior (most flexible)

**Recommendation**: **Option C** - Use existing `InstructionFallbackPolicy` to control template rendering errors. Aligns with existing fallback semantics.

**Impact**: Affects template renderer error handling and integration with fallback system.

---

### 4.4 Instruction Template Context for Loop Steps (LOW PRIORITY)

**Question**: For loop steps, should each iteration render instructions with different context?

**Example**: Loop step processes `sources` array. Should instruction template have access to `step.loop_item` for current iteration?

**Options**:
- **A) No loop context**: Instructions rendered once per step, same context for all iterations (simpler)
- **B) Per-iteration context**: Instructions rendered per iteration with `step.loop_item` (more powerful)

**Recommendation**: **Option B** - Per-iteration context enables instructions like "Process source: {{ step.loop_item.title }}". This aligns with the hierarchical/iterative nature of blueprints.

**Impact**: Affects instruction rendering in loop steps and context building logic.

---

## 5. Implementation Recommendations

### 5.1 Phase 1: Core Template Renderer (P1)

1. **Create `TemplateRenderer` abstraction** in `src/promptic/pipeline/template_renderer.py`
   - Interface: `render(instruction_node: InstructionNode, content: str, context: dict) -> str`
   - Format-specific renderers: `MarkdownFormatRenderer`, `Jinja2FormatRenderer`, `YamlFormatRenderer`

2. **Modify `ContextPreviewer._resolve_instruction_text()`**
   - Accept `template_context` parameter
   - Call template renderer for each instruction
   - Return rendered content

3. **Build instruction context**
   - Extend `template_context` with step-specific data
   - Provide namespaced access: `data.*`, `memory.*`, `step.*`

### 5.2 Phase 2: Format Support (P1-P2)

1. **Markdown format renderer** (P1)
   - Support `{}` placeholders with nested access
   - Handle escaping (`{{` → `{`)

2. **Jinja2 format renderer** (P2)
   - Separate Jinja2 environment configuration
   - Support conditionals, loops, filters

3. **YAML format renderer** (P3)
   - Custom pattern support
   - Pattern configuration in instruction metadata

### 5.3 Phase 3: Advanced Features (P3)

1. **Markdown hierarchy parsing** (P3)
   - Extract hierarchical structure from headings
   - Conditional markers support

2. **Loop iteration context** (P3)
   - Per-iteration instruction rendering
   - `step.loop_item` context variable

---

## 6. Summary of Findings

### ✅ No Conflicts

1. **Jinja2 usage**: Separate concerns (prompt vs instruction rendering)
2. **Format field**: Already implemented and aligned
3. **Rendering order**: Compatible flow

### ⚠️ Integration Points Requiring Changes

1. **Instruction rendering flow**: Modify `_resolve_instruction_text()` to support templating
2. **Context building**: Extend `template_context` with step-specific data
3. **Jinja2 environment**: Consider separate environment for instructions

### 📋 Clarifications Needed

1. **Context variable scope**: Global only, step-specific, or both? (Recommendation: Both with namespacing)
2. **Jinja2 environment**: Shared or separate? (Recommendation: Separate with shared base)
3. **Error handling**: How to handle template errors? (Recommendation: Use `InstructionFallbackPolicy`)
4. **Loop context**: Per-iteration rendering? (Recommendation: Yes, with `step.loop_item`)

---

### ✅ Resolved Clarifications (2025-11-19)

1. **Context scope**: Implemented both global and step namespaces with documentation plus tests covering `step.loop_item`.
2. **Jinja2 environment**: Instructions now use a dedicated environment with shared base config and instruction-specific helpers.
3. **Error handling**: `TemplateRenderer` enforces `InstructionFallbackPolicy` (`error`, `warn`, `noop`) with structured logging.
4. **Loop context**: `build_instruction_context()` accepts `loop_item` and integration tests confirm per-iteration rendering.

---

## 7. Next Steps

1. **Resolve clarifications** (Section 4) before implementation
2. **Update templating spec** with clarifications and integration details
3. **Create implementation plan** following the recommendations (Section 5)
4. **Update context engine documentation** to note instruction templating integration

---

## Appendix: Code References

### Context Engine Implementation

- Prompt template rendering: `src/promptic/context/rendering.py:161-173`
- Template context building: `src/promptic/pipeline/previewer.py:114-121`
- Instruction loading: `src/promptic/pipeline/previewer.py:183-199`
- Format field: `src/promptic/blueprints/models.py:73`
- Format detection: `src/promptic/instructions/store.py:11-16, 81`

### Instruction Templating Spec

- Specification: `specs/001-instruction-templating/spec.md`
- Requirements: Lines 99-115
- Architecture: Lines 116-127
