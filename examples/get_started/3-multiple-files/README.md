# Example 3: Multiple Root Files with Shared Includes

This example demonstrates how to work with multiple root files that share common includes and have their own specific ones.

## Files

- `root-1.md` - First root file (scenario 1)
- `root-2.md` - Second root file (scenario 2)
- `common.md` - Common file used by both root files
- `specific-2.md` - Specific file used only by root-2.md
- `render.py` - Python script that renders both root files

## File Structure

```
root-1.md
  └─ [Common Content](common.md)

root-2.md
  ├─ [Common Content](common.md)
  └─ [Specific Content](specific-2.md)
```

## Running the Example

```bash
cd examples/get_started/3-multiple-files
python render.py
```

## What This Shows

### 1. Multiple Root Files
- How to load and render different root files independently
- Each root file creates its own network
- Networks can share common dependencies

### 2. Shared Includes
- `common.md` is referenced by both root files
- Loaded only once per network
- Content is consistent across both outputs

### 3. Specific Includes
- `specific-2.md` is used only by `root-2.md`
- Different root files can have different dependency trees
- Flexible file organization

### 4. Full Render Mode
- Both roots are rendered with all content inlined
- Each output is self-contained
- References are fully resolved

## Output

The script renders both root files:

**First Output (root-1.md):**
```markdown
# First Alternative

This is a common section that's shared.

This is root 1.
```

**Second Output (root-2.md):**
```markdown
# Second Alternative

This is a common section that's shared.

Content specific to alternative 2.

This is root 2.
```

## Use Cases

This pattern is useful for:

### 1. Multiple Scenarios/Variants
- Different AI prompts sharing common instructions
- Multiple documentation versions with shared sections
- Variant configurations with common base

### 2. Template Systems
- Base template (common.md)
- Specific implementations (root-1.md, root-2.md)
- Additional components (specific-2.md)

### 3. Modular Documentation
- Shared introduction/conclusion
- Different main content sections
- Reusable components

## Key Concepts

### Network Independence
Each root file creates an independent network:
- `root-1.md` network includes: root-1.md + common.md
- `root-2.md` network includes: root-2.md + common.md + specific-2.md

### Dependency Resolution
- References are resolved recursively
- Each network only includes what it needs
- No duplication - files loaded once per network

### Flexible Organization
- Organize files logically by purpose
- Share common content without duplication
- Add specific content where needed

## Next Steps

- Try **Example 4** to see different file formats (YAML, JSON, Jinja2)
- Explore **Advanced Examples** for real-world use cases
