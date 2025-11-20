# Quickstart: Instruction Templating

This guide demonstrates how to use instruction templating to insert dynamic data into instruction files.

## 1. Markdown Format with Placeholders (User Story 1)

Create a Markdown instruction file `instructions/process_item.md`:

```markdown
# Process Item

Process the item: {item_name}

User details:
- Name: {user.name}
- Email: {user.email}
- Role: {user.role}
```

Render it with data:

```python
from promptic.sdk.api import load_blueprint, render_for_llm
from promptic.pipeline.template_renderer import TemplateRenderer
from promptic.context.template_context import InstructionRenderContext

# Load blueprint (instructions are referenced in blueprint)
blueprint = load_blueprint("my_blueprint")

# Create template context with data
context = InstructionRenderContext(
    data={"item_name": "Task 1", "user": {"name": "Alice", "email": "alice@example.com", "role": "admin"}},
    memory={},
    step=None,
    blueprint=blueprint.model_dump()
)

# Render instruction (normally done automatically during blueprint rendering)
from promptic.instructions.store import FilesystemInstructionStore
from promptic.pipeline.template_renderer import TemplateRenderer

store = FilesystemInstructionStore("instructions/")
renderer = TemplateRenderer()
node = store.get_node("process_item")
content = store.load_content("process_item")
rendered = renderer.render(node, content, context)

print(rendered)
# Output:
# # Process Item
#
# Process the item: Task 1
#
# User details:
# - Name: Alice
# - Email: alice@example.com
# - Role: admin
```

## 2. Jinja2 Format with Conditionals (User Story 2)

Create a Jinja2 instruction file `instructions/conditional_step.jinja`:

```jinja
{% if step.kind == "loop" %}
Process each item in the loop:
{% for item in step.loop_item %}
- {{ item.title }}
{% endfor %}
{% else %}
Process single item: {{ data.item_name }}
{% endif %}

Memory context: {{ memory.prior_findings | join(", ") }}
```

Render it with context:

```python
context = InstructionRenderContext(
    data={"item_name": "Task 1"},
    memory={"prior_findings": ["finding1", "finding2"]},
    step=StepContext(
        step_id="process",
        title="Process Items",
        kind="sequence",
        hierarchy=[],
        loop_item=None
    ),
    blueprint=blueprint.model_dump()
)

node = store.get_node("conditional_step")
content = store.load_content("conditional_step")
rendered = renderer.render(node, content, context)
```

## 3. Loop Step with Per-Iteration Context (Clarification 4)

For loop steps, each iteration renders with different `step.loop_item`:

```python
# Blueprint has loop step that processes sources
sources = [
    {"title": "Source 1", "url": "https://example.com/1"},
    {"title": "Source 2", "url": "https://example.com/2"}
]

# Render instruction for each iteration
for source in sources:
    context = InstructionRenderContext(
        data={},
        memory={},
        step=StepContext(
            step_id="process_source",
            title="Process Source",
            kind="loop",
            hierarchy=["collect"],
            loop_item=source  # Different for each iteration
        ),
        blueprint=blueprint.model_dump()
    )

    node = store.get_node("process_source")
    content = store.load_content("process_source")
    rendered = renderer.render(node, content, context)
    print(f"Rendered for {source['title']}: {rendered}")
```

Instruction file `instructions/process_source.md`:

```markdown
Process source: {step.loop_item.title}
URL: {step.loop_item.url}
```

## 4. Context Variable Namespacing (Clarification 1)

Context variables are namespaced to avoid conflicts:

```markdown
# Instruction: process_data.md

Data slot value: {data.item_name}
Memory slot value: {memory.prior_findings}
Step ID: {step.step_id}
Blueprint name: {blueprint.name}
```

**Important**: Use namespaced access (`data.*`, `memory.*`, `step.*`) to avoid conflicts with user-provided data keys.

## 5. Error Handling with InstructionFallbackPolicy (Clarification 3)

Template rendering errors are handled according to `InstructionFallbackPolicy`:

```python
# Instruction with missing placeholder
instruction_content = "Process: {missing_var}"

# With error policy (default)
try:
    rendered = renderer.render(node, instruction_content, context)
except TemplateRenderError as e:
    print(f"Error: {e.message}")  # Raises exception

# With warn policy
node.fallback_policy = InstructionFallbackPolicy.WARN
rendered = renderer.render(node, instruction_content, context)
# Emits warning, continues with placeholder substitution

# With noop policy
node.fallback_policy = InstructionFallbackPolicy.NOOP
rendered = renderer.render(node, instruction_content, context)
# Returns empty string, continues silently
```

## 6. Integration with Blueprint Rendering

Template rendering is automatically integrated into blueprint rendering:

```python
from promptic.sdk.api import load_blueprint, render_for_llm

# Load blueprint with instructions that have placeholders
blueprint = load_blueprint("my_blueprint")

# Render for LLM (instructions are automatically templated)
context_text = render_for_llm(blueprint)
# Instructions are rendered with data/memory/step context automatically
```

## 7. Format Detection

Format is automatically detected from file extension:

- `.md` → Markdown format (`{}` placeholders)
- `.jinja` → Jinja2 format (Jinja2 syntax)
- `.yaml`/`.yml` → YAML format (custom patterns)

Override format if needed:

```python
# Override format in InstructionNode
node = InstructionNode(
    instruction_id="custom",
    format="jinja",  # Explicitly set format
    # ... other fields
)
```

## Next Steps

- See `docs_site/context-engineering/markdown-templating.md` for Markdown format details
- See `docs_site/context-engineering/jinja2-templating.md` for Jinja2 syntax and filters
- See `docs_site/context-engineering/template-context-variables.md` for complete context variable reference
- See examples in `examples/markdown-templating/`, `examples/jinja2-templating/`, etc.
