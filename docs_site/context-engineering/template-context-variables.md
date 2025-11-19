# Template Context Variables

Template renderers receive a namespaced context object so instructions can
reference blueprint data, memory, and step metadata without collisions.

## Namespaces

| Namespace | Description | Examples |
|-----------|-------------|----------|
| `data.*` | Values supplied by data slots or manual overrides. | `data.item_name`, `data.sources[0].url` |
| `memory.*` | Memory providers or cached findings. | `memory.prior_findings`, `memory.owner` |
| `step.*` | Metadata about the current step. Available keys: `step_id`, `title`, `kind`, `hierarchy`, `loop_item`. | `step.title`, `step.hierarchy`, `step.loop_item.url` |
| `blueprint.*` | Blueprint metadata serialized via `ContextBlueprint.model_dump()`. | `blueprint.name`, `blueprint.id` |

## Loop iterations

When rendering instructions inside a loop step, the per-iteration item is
available at `step.loop_item`. The integration test
`tests/integration/test_loop_iteration_templating.py` demonstrates the pattern:

```markdown
Processing: {step.loop_item.title}
URL: {step.loop_item.url}
```

Construct the context by passing `loop_item` to
`build_instruction_context(..., step_id="loop_step", loop_item=item)`.

## Access rules

- Dot notation works for dicts or objects (e.g., `{data.user.profile.name}`).
- Missing keys raise `TemplateRenderError` with the placeholder path.
- Use the same expressions in Markdown conditionals (`<!-- if:data.flag -->`)
  and in Jinja2 templates (`{{ step.loop_item.title }}`).

For additional examples, see:

- `docs_site/context-engineering/markdown-templating.md`
- `docs_site/context-engineering/jinja2-templating.md`
- `docs_site/context-engineering/hierarchical-markdown.md`
