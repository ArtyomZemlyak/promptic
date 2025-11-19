# Hierarchical Markdown Instructions

User Story 4 introduces a lightweight hierarchy parser that lets designers
structure Markdown instructions with heading levels and optional conditional
sections—no YAML blueprint edits required.

## Syntax overview

- Use Markdown headings (`##`, `###`, etc.) to express parent/child sections.
- Gate a block of Markdown with `<!-- if:expression --> ... <!-- endif -->`
  where `expression` references a namespaced context variable such as
  `data.show_details` or `memory.has_incident`.
- Placeholders inside the block continue to use the standard `{}` syntax.

## Example

```markdown
## Research Summary
Always visible content.

<!-- if:data.show_details -->
### Detailed Notes
- Risks: {data.risks}
- Next Steps: {data.next_steps}
<!-- endif -->
```

Rendering with `data.show_details=True` includes the `Detailed Notes` section;
setting it to `False` removes the block entirely.

## Integration details

1. `MarkdownHierarchyParser` (use-case layer) parses headings plus conditional
   markers and produces a `MarkdownHierarchy` object.
2. `MarkdownFormatRenderer` calls the parser prior to placeholder expansion,
   evaluates each conditional expression against the namespaced template
   context, and removes sections that evaluate to `False`.
3. Errors resolving conditional expressions raise `TemplateRenderError` with
   the offending placeholder for easy debugging.

## Testing & examples

- Unit tests in `tests/unit/pipeline/test_template_renderer_markdown.py`
  validate hierarchy parsing and conditional extraction.
- Integration test `tests/integration/test_instruction_templating.py::
  test_markdown_hierarchy_conditionals` demonstrates end-to-end rendering.
- Example project: `examples/us4-hierarchical-markdown/`.

## Authoring tips

- Prefer heading levels `##` and deeper to avoid colliding with blueprint-wide
  headings.
- Keep conditional expressions simple (dot-delimited lookups). They share the
  same resolution rules as `{}` placeholders.
- Use Rich preview (`promptic.sdk.api.preview_blueprint`) to verify which
  sections were included along with any fallback warnings.
