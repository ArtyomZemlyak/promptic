# Example 5: Versioned Prompt Loading

This example demonstrates how to load specific versions of prompts using the versioning system with hierarchical markdown files.

## Files

```
prompts/
  ├── main_v1.0.0.md                    # Main prompt version 1.0.0
  ├── main_v2.0.0.md                    # Main prompt version 2.0.0
  ├── instructions/
  │   ├── process_v1.0.0.md            # Instructions version 1.0.0
  │   └── process_v2.0.0.md            # Instructions version 2.0.0
  └── context/
      ├── details_v1.0.0.md            # Context details version 1.0.0
      └── details_v2.0.0.md            # Context details version 2.0.0
render.py                               # Script demonstrating version loading
```

## File Structure

The prompt hierarchy has multiple versions:

```
prompts/
  └─ main_v1.0.0.md / main_v2.0.0.md
      ├─ [instructions/process.md] → resolves to process_v1.0.0.md or process_v2.0.0.md
      └─ [context/details.md] → resolves to details_v1.0.0.md or details_v2.0.0.md
```

When you load version `v1.0.0`, the system automatically resolves:
- `main.md` → `main_v1.0.0.md`
- `instructions/process.md` → `instructions/process_v1.0.0.md`
- `context/details.md` → `context/details_v1.0.0.md`

## Running the Example

```bash
cd examples/get_started/5-versioning
python render.py
```

## What This Shows

- **Semantic Versioning**: Files are versioned using `_vX.Y.Z` suffix (e.g., `main_v1.0.0.md`)
- **Version Resolution**: Load specific versions with `load_prompt(path, version="v1.0.0")`
- **Latest Version**: Use `version="latest"` to load the most recent version
- **Partial Versions**: Use `version="v2"` to automatically resolve to `v2.0.0`
- **Hierarchical References**: Referenced files are resolved to matching versions automatically
- **Directory Structure**: Versions are preserved across subdirectories

## Version Specifications

You can specify versions in different ways:

```python
# Load latest version (highest version number)
content = load_prompt(prompts_dir, version="latest")

# Load specific full version
content = load_prompt(prompts_dir, version="v1.0.0")

# Load with partial version (resolves to v2.0.0)
content = load_prompt(prompts_dir, version="v2")

# Load with major.minor version
content = load_prompt(prompts_dir, version="v1.0")
```

## Key Concepts

- **Semantic Versioning** - Files use `_vX.Y.Z` suffix pattern
- **Automatic Resolution** - Referenced files resolve to same version
- **Version Compatibility** - Load any version without modifying files
- **Hierarchical Support** - Works with nested directory structures

## Output

The script will load and display different versions:

**Version 1.0.0:**
```markdown
# Task Processing v1.0.0

Welcome to version 1.0.0 of the task processor.
...
```

**Version 2.0.0:**
```markdown
# Task Processing v2.0.0

Welcome to version 2.0.0 with enhanced features!
...
```

## Next Steps

- Try **Example 6** to see how to export specific versions
- Modify version numbers in filenames to create new versions
- Add more nested subdirectories with versioned files
