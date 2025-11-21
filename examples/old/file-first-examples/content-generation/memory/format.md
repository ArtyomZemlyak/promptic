# Memory Format for Content Generation

Structure for storing content library, brand guidelines, and style guide.

## Content Library Format

Store published content in `memory/content/` directory:

```markdown
# Content: {title}

- Type: {blog|article|social|email}
- Date: YYYY-MM-DD
- Author: {name}
- Audience: {description}
- Key Messages: {list}
- Performance: {metrics}
- Files: {links}
```

## Brand Guidelines Format

Store brand guidelines in `memory/brand/` directory:

- `voice.md`: Brand voice and tone
- `style.md`: Visual and design guidelines
- `messaging.md`: Core brand messages
- `examples.md`: Example content pieces

## Style Guide Format

Store style guide in `memory/style/` directory:

- `grammar.md`: Grammar and punctuation rules
- `terminology.md`: Approved terms and phrases
- `formatting.md`: Formatting standards
- `citations.md`: Citation and attribution rules

## Retention Policy

- Content library: Keep indefinitely, archive after 2 years
- Brand guidelines: Keep indefinitely, update quarterly
- Style guide: Keep indefinitely, update as needed
