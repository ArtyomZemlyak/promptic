# Memory Format for Data Analysis

Structure for storing analysis history and feature registry.

## Analysis History Format

Store completed analyses in `memory/analyses/` directory:

```markdown
# Analysis: {dataset_name} - {date}

- Dataset: {name}
- Date: YYYY-MM-DD
- Analyst: {name}
- Key Findings: {summary}
- Recommendations: {list}
- Files: {links}
```

## Feature Registry Format

Store feature definitions in `memory/features/` directory:

```markdown
# Feature: {feature_name}

- Type: {numeric|categorical|datetime}
- Source: {original|derived}
- Transformation: {method}
- Validation: {status}
- Usage: {analysis_types}
```

## Retention Policy

- Analysis history: Keep for 2 years, then archive
- Feature registry: Keep indefinitely, update as needed
- Intermediate results: Keep for 6 months
