# File-First Prompt Examples

This directory contains comprehensive examples demonstrating the file-first prompt hierarchy functionality. Each example showcases different use cases and patterns for organizing prompts as files that agents can reference on-demand.

## Overview

File-first prompts allow you to:
- Store detailed instructions in separate files
- Provide agents with compact root instructions
- Enable agents to fetch detailed context when needed
- Reduce token usage by up to 60% while maintaining completeness
- Organize complex workflows hierarchically

## Examples

### 1. Code Review Workflow (`code-review/`)

A comprehensive code review process demonstrating:
- Multi-level nested steps (analyze → check syntax/logic)
- Loop-based processing (review multiple issues)
- Memory channels for review history and team standards
- Complex workflow with 10+ instruction files

**Key Features:**
- Systematic code analysis
- Impact and risk assessment
- Structured feedback generation
- Issue categorization and fix suggestions

**Usage:**
```bash
promtic preview code-review/code_review_workflow.yaml --render-mode file_first
```

### 2. Data Analysis Pipeline (`data-analysis/`)

A complete data analysis workflow showing:
- Sequential data processing steps
- Feature engineering loops
- Pattern analysis and insights generation
- Memory channels for analysis history and feature registry

**Key Features:**
- Data loading and validation
- Exploratory data analysis
- Feature engineering
- Pattern identification
- Insight generation

**Usage:**
```bash
promtic preview data-analysis/data_analysis_pipeline.yaml --render-mode file_first
```

### 3. Content Generation Workflow (`content-generation/`)

A content creation process demonstrating:
- Multi-stage content development
- Loop-based section writing
- Multiple memory channels (content library, brand guidelines, style guide)
- Comprehensive quality checks

**Key Features:**
- Brief analysis and audience research
- Content planning and outlining
- Writing and refinement
- SEO optimization
- Quality review and proofreading

**Usage:**
```bash
promtic preview content-generation/content_generation_workflow.yaml --render-mode file_first
```

### 4. Decision Making Process (`decision-making/`)

A strategic decision-making workflow featuring:
- Branching logic based on feasibility and confidence
- Complex evaluation processes
- Multiple decision paths
- Comprehensive documentation

**Key Features:**
- Problem definition and stakeholder analysis
- Option generation and evaluation
- Risk assessment and comparison
- Decision documentation
- Implementation planning

**Usage:**
```bash
promtic preview decision-making/decision_making_process.yaml --render-mode file_first
```

## Structure

Each example follows this structure:

```
example-name/
├── example_name.yaml          # Blueprint definition
├── instructions/              # Instruction files referenced by blueprint
│   ├── principle.md          # Global principles
│   ├── step1_step.md         # Step-specific instructions
│   └── ...
├── memory/                    # Memory format definitions
│   └── format.md             # Memory structure documentation
├── data/                      # Sample data files (if applicable)
│   └── ...
└── README.md                 # Example-specific documentation (optional)
```

## Common Patterns

### Nested Steps

All examples demonstrate hierarchical step organization:
- Parent steps contain child steps
- Instructions cascade from parent to children
- Each level can have its own instruction files

### Loop Processing

Examples show loop-based processing:
- Code review: Loop through issues
- Data analysis: Loop through features
- Content generation: Loop through sections

### Branching Logic

Decision-making example demonstrates conditional branching:
- Different paths based on feasibility scores
- Alternative flows based on confidence levels
- Conditional step execution

### Memory Channels

All examples include memory channel definitions:
- Review history, analysis history, content library, decision history
- Format descriptors explaining memory structure
- Retention policies

## Running Examples

### Using CLI

```bash
# Basic preview
promtic preview <example-path>/<blueprint>.yaml --render-mode file_first

# With base URL for absolute links
promtic preview <example-path>/<blueprint>.yaml --render-mode file_first --base-url https://kb.example.com
```

### Using SDK

```python
from promptic.sdk.blueprints import BlueprintPreviewer

previewer = BlueprintPreviewer(
    render_mode="file_first",
    base_url="https://kb.example.com"
)

result = previewer.render("code-review/code_review_workflow.yaml")
print(result.markdown)
print(result.metadata["metrics"])
```

## Expected Output

When rendering in file-first mode, you'll see:

1. **Compact Root Instruction**:
   - Persona and goals (≤10 lines)
   - Ordered steps with summaries
   - File references (e.g., "See more: instructions/step.md")
   - Memory & logging block (if applicable)

2. **Structured Metadata**:
   - Steps array with summaries and references
   - Memory channels information
   - Render metrics (token reduction, reference counts)
   - Reference tree structure

3. **Token Reduction**:
   - Typically 60%+ reduction compared to full inline rendering
   - Detailed instructions remain in files for on-demand access

## Customization

### Adding New Examples

1. Create a new directory under `file-first-examples/`
2. Add blueprint YAML file
3. Create `instructions/` directory with instruction files
4. Add `memory/format.md` if using memory channels
5. Reference instruction files in blueprint `instruction_refs`

### Modifying Existing Examples

- Edit instruction files to change behavior
- Update blueprint YAML to modify structure
- Add new steps or modify existing ones
- Adjust memory format definitions

## Best Practices

1. **Organize Instructions Logically**:
   - Use descriptive file names
   - Group related instructions
   - Keep instructions focused and specific

2. **Maintain Hierarchy**:
   - Parent steps should provide context
   - Child steps should add detail
   - Avoid deep nesting (max 3-4 levels)

3. **Document Memory Formats**:
   - Clearly describe memory structure
   - Specify retention policies
   - Provide usage examples

4. **Test Renderings**:
   - Verify all file references resolve
   - Check token reduction metrics
   - Validate metadata structure
   - Test with different base URLs

## Troubleshooting

### Missing File Errors

If you see errors about missing instruction files:
- Check that all referenced files exist in `instructions/` directory
- Verify file names match exactly (case-sensitive)
- Ensure `instruction_root` setting is correct

### Token Reduction Not Achieved

If token reduction is less than expected:
- Check instruction file sizes (should be detailed)
- Verify summaries are being generated (≤120 tokens)
- Ensure full instructions aren't being inlined

### Reference Links Not Working

If reference links don't work:
- Provide `--base-url` for absolute links
- Check file paths are relative to instruction root
- Verify base URL format (include protocol)

## Related Documentation

- [File-First Architecture](../../docs_site/context-engineering/file-first-architecture.md)
- [Blueprint Guide](../../docs_site/context-engineering/blueprint-guide.md)
- [Quickstart Guide](../../specs/003-file-first-prompts/quickstart.md)
- [Specification](../../specs/003-file-first-prompts/spec.md)

## Contributing

When adding new examples:
1. Follow the existing structure
2. Include comprehensive instruction files
3. Add memory format documentation
4. Test with file-first render mode
5. Update this README
