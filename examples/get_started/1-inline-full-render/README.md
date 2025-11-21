# Example 1: Inline Full Render Mode

This is the simplest example showing how to use promptic with **full render mode** - where all file references are inlined into a single output.

## Files

- `main.md` - Main markdown file that references another file
- `greeting.md` - Included markdown file with greeting text
- `render.py` - Python script that loads and renders the main file

## File Structure

```
main.md
  └─ [Greeting](greeting.md)
```

The `main.md` file contains a markdown link to `greeting.md`.

## Running the Example

```bash
cd examples/get_started/1-inline-full-render
python render.py
```

## What This Shows

- **Loading**: How to load a markdown file with `load_node_network()`
- **Full Render Mode**: How to use `render_mode="full"` to inline all referenced content
- **Reference Resolution**: The link `[Greeting](greeting.md)` is replaced with the actual content of `greeting.md`
- **Minimal Setup**: Just ~30 lines of Python code to get started

## Output

The script will render `main.md` showing how the content from `greeting.md` is inlined at the location of the reference:

**Original `main.md`:**
```markdown
# Welcome

[Greeting](greeting.md)
```

**Rendered output (full mode):**
```markdown
# Welcome

Hello! This is a greeting from the included file.
```

The link is replaced with the actual content!

## Key Concepts

- **Full Render Mode** (`render_mode="full"`) - Inlines all references into a single output
- **Reference Syntax** - `[label](path)` in markdown
- **Recursive Resolution** - Works for nested references too

## Next Steps

- Try **Example 2** to see file-first mode (preserving links)
- Try **Example 3** to see multiple root files
- Try **Example 4** to see different file formats
