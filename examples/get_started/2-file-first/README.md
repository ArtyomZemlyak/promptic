# Example 2: File-First Render Mode

This example shows how to use promptic with **file-first render mode** - where file references are preserved as links instead of being inlined.

## Files

- `main.md` - Main markdown file that references another file
- `greeting.md` - Included markdown file with greeting text
- `render.py` - Python script that loads and renders in file-first mode

## File Structure

```
main.md
  └─ [Greeting](greeting.md)
```

The `main.md` file contains a markdown link to `greeting.md`.

## Running the Example

```bash
cd examples/get_started/2-file-first
python render.py
```

## What This Shows

- **File-First Mode**: How to use `render_mode="file_first"` to preserve file references
- **Link Preservation**: The link `[Greeting](greeting.md)` stays as a link in the output
- **Comparison**: The difference between file-first and full render modes

## Output

The script renders both modes for comparison:

**File-First Mode Output:**
```markdown
# Welcome

[Greeting](greeting.md)
```
The link is preserved as-is.

**Full Mode Output (for comparison):**
```markdown
# Welcome

Hello! This is a greeting from the included file.
```
The link is replaced with content.

## Key Concepts

### File-First Mode (`render_mode="file_first"`)
- Preserves file references as links
- Useful when you want to keep the structure
- Good for documentation that should reference external files
- Files are still loaded and validated, but not inlined

### Full Mode (`render_mode="full"`)
- Inlines all referenced content
- Creates a single self-contained output
- Good for AI prompts or consolidated documents

## When to Use Each Mode

**Use File-First when:**
- You want to preserve the file structure
- References should stay as clickable links
- Building navigation or indexes
- Creating documentation with external references

**Use Full Mode when:**
- You need a single self-contained document
- Building AI prompts that need all context
- Merging multiple files into one output
- Creating exports or snapshots

## Next Steps

- Try **Example 3** to see multiple root files
- Try **Example 4** to see different file formats
