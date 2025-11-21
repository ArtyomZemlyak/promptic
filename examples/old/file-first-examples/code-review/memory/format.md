# Memory Format for Code Reviews

This document describes the structure for storing code review history and team standards.

## Review History Format

Store reviews in `memory/reviews/` directory as markdown files:

```markdown
# Review: PR-{number}

- Date: YYYY-MM-DD
- Reviewer: {name}
- Status: {approved|changes_requested|commented}
- Issues Found: {count}
- Categories: {list}
```

## Team Standards Format

Store team standards in `memory/standards/` directory:

- `coding_standards.md`: Code style and conventions
- `review_guidelines.md`: Review process and expectations
- `common_patterns.md`: Frequently used patterns and solutions

## Retention Policy

- Reviews: Keep for 6 months, then archive
- Standards: Keep indefinitely, update as needed
- Patterns: Keep for 1 year, refresh quarterly
