# Tutorial Examples

These examples provide comprehensive, step-by-step tutorials for using promptic in real-world scenarios.

## Examples

### 1. Complete End-to-End (`complete/`)

A full demonstration of all library functionality covering the entire workflow.

**What you'll learn:**
- Complete blueprint authoring workflow
- Adapter registration and configuration
- Preview generation (inline and file-first modes)
- Render for LLM
- Instruction rendering
- Fallback handling

**Run it:**
```bash
python examples/tutorials/complete/end_to_end.py
```

### 2. Adapter Registration (`us2-adapters/`)

Learn how to register and swap data/memory adapters without modifying blueprint code.

**What you'll learn:**
- Registering CSV and memory adapters
- Swapping adapters transparently
- Using adapters with both inline and file-first rendering modes

**Run it:**
```bash
python examples/tutorials/us2-adapters/swap_adapters.py
```

### 3. File-First Examples (`file-first-examples/`)

Comprehensive examples demonstrating file-first prompt hierarchy with real-world use cases.

**Examples included:**
- **Code Review** (`code-review/`) - Systematic code analysis workflow
- **Data Analysis** (`data-analysis/`) - Complete data processing pipeline
- **Content Generation** (`content-generation/`) - Multi-stage content creation
- **Decision Making** (`decision-making/`) - Strategic decision-making process

**What you'll learn:**
- Organizing complex workflows hierarchically
- Creating compact prompts with file references
- Reducing token usage while maintaining completeness
- Memory channels and format definitions

**Run any example:**
```bash
from promptic.sdk.blueprints import preview_blueprint

result = preview_blueprint(
    "examples/tutorials/file-first-examples/code-review/code_review_workflow.yaml",
    render_mode="file_first",
    base_url="https://kb.example.com"
)
print(result.markdown)
```

See `file-first-examples/README.md` for detailed documentation on each example.

## Learning Path

1. Start with **Get Started** examples (`../get_started/`) if you're new to promptic
2. Work through these tutorials to understand advanced features
3. Explore **Advanced** examples (`../advanced/`) for low-level customization
