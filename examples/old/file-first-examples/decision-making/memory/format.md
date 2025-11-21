# Memory Format for Decision Making

Structure for storing decision history and decision framework.

## Decision History Format

Store completed decisions in `memory/decisions/` directory:

```markdown
# Decision: {decision_name} - {date}

- Problem: {description}
- Date: YYYY-MM-DD
- Decision Maker: {name}
- Options Considered: {count}
- Chosen Option: {name}
- Rationale: {summary}
- Outcome: {result}
- Lessons Learned: {notes}
```

## Decision Framework Format

Store decision frameworks in `memory/frameworks/` directory:

- `evaluation_criteria.md`: Standard criteria for evaluation
- `risk_assessment.md`: Risk assessment methodology
- `stakeholder_analysis.md`: Stakeholder mapping approach
- `implementation_templates.md`: Implementation planning templates

## Retention Policy

- Decision history: Keep for 5 years, then archive
- Decision frameworks: Keep indefinitely, update annually
- Lessons learned: Keep indefinitely, review quarterly
