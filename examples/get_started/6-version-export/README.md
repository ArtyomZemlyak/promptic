# Example 6: Version Export

This example demonstrates how to export specific versions of prompts from a hierarchical structure, preserving directory structure and removing version suffixes from filenames.

## Files

```
prompts/
  ├── workflow_v1.0.0.md                # Main workflow version 1.0.0
  ├── workflow_v2.0.0.md                # Main workflow version 2.0.0
  ├── tasks/
  │   ├── definition_v1.0.0.md         # Task definition version 1.0.0
  │   └── definition_v2.0.0.md         # Task definition version 2.0.0
  ├── steps/
  │   ├── process_v1.0.0.md            # Processing steps version 1.0.0
  │   └── process_v2.0.0.md            # Processing steps version 2.0.0
  ├── output/
  │   ├── format_v1.0.0.md             # Output format version 1.0.0
  │   └── format_v2.0.0.md             # Output format version 2.0.0
  └── quality/
      └── checks_v2.0.0.md             # Quality checks (v2.0.0 only)
export_demo.py                          # Script demonstrating version export
```

## Running the Example

```bash
cd examples/get_started/6-version-export
python export_demo.py
```

## What This Shows

- **Version Export**: Export complete version snapshots with `export_version()`
- **Structure Preservation**: Exported files maintain the original directory hierarchy
- **Version Suffix Removal**: Exported files have version suffixes removed (e.g., `workflow_v1.0.0.md` → `workflow.md`)
- **Explicit Version References**: Files can explicitly reference specific versions (e.g., `format_v1.0.0.md`)
- **Smart Version Resolution**: When explicit version reference exists, automatic version resolution is skipped
- **Path Resolution**: References in files are resolved to work in exported structure
- **Atomic Export**: All files are exported together (all or nothing)
- **Multiple Versions**: Export different versions to different directories

## Export Behavior

When you export version `v1.0.0`:

**Original Structure:**
```
prompts/
  ├── workflow_v1.0.0.md
  └── tasks/
      └── definition_v1.0.0.md
```

**Exported Structure:**
```
exported/workflow_v1/
  ├── workflow.md                      # Version suffix removed!
  └── tasks/
      └── definition.md                # Version suffix removed!
```

The exported files are ready to use without any modifications!

## Explicit Version References

This example demonstrates an important feature: **explicit version references**.

In `workflow_v2.0.0.md`, the output format explicitly references v1.0.0:

```markdown
## Output Format

[Output Format](output/format_v1.0.0.md)
```

This means:
- v2.0.0 workflow uses the v1.0.0 output format (perhaps for backward compatibility)
- When exporting v2.0.0, the system detects this explicit reference
- The file is exported as `output/format_v1.0.0.md` (keeping the version suffix)
- The automatic resolution of `output/format_v2.0.0.md` is skipped to avoid conflicts

**Without explicit reference** (like in v1.0.0):
```markdown
[Output Format](output/format.md)  → resolves to format_v1.0.0.md → exports as format.md
```

**With explicit reference** (like in v2.0.0):
```markdown
[Output Format](output/format_v1.0.0.md)  → exports as format_v1.0.0.md (version kept!)
```

This allows you to:
- Mix different versions of components in a single workflow
- Maintain backward compatibility with older formats
- Explicitly control which version of each component is used
- Avoid automatic version resolution when you need specific versions

## Export API

```python
from promptic import export_version

# Export specific version
result = export_version(
    source_path="prompts/",           # Source directory
    version_spec="v1.0.0",            # Version to export
    target_dir="exported/v1/",        # Target export directory
    overwrite=True                     # Overwrite if exists
)

# Access export results
print(f"Exported {len(result.exported_files)} files")
print(f"Root content: {result.root_prompt_content}")
print(f"Structure preserved: {result.structure_preserved}")
```

## Export Result

The `export_version()` function returns an `ExportResult` object with:

- `root_prompt_content`: The content of the root prompt with resolved paths
- `exported_files`: List of all exported file paths
- `structure_preserved`: Whether directory structure was preserved (always `True`)

## Version Differences

**v1.0.0 exports:**
- workflow.md
- tasks/definition.md
- steps/process.md
- output/format.md (automatically resolved from format_v1.0.0.md, suffix removed)

**v2.0.0 exports:**
- workflow.md (with "Quality Checks" section)
- tasks/definition.md (enhanced)
- steps/process.md (5 steps instead of 3)
- output/format_v1.0.0.md (**explicit reference**, suffix kept!)
- quality/checks.md (new file!)

**Note:** v2.0.0 explicitly references `output/format_v1.0.0.md` in the workflow file. When a file explicitly references a specific version, the export preserves the version suffix to maintain the explicit reference.

## Use Cases

Export is useful for:

1. **Deployment**: Export specific version for production
2. **Distribution**: Share a clean version without all variants
3. **Testing**: Create isolated test environments
4. **Archiving**: Preserve version snapshots
5. **Integration**: Export for use with other tools

## Key Concepts

- **Atomic Export** - All files export successfully or nothing is exported
- **Structure Preservation** - Directory hierarchy is maintained
- **Version Suffix Removal** - Files are renamed to be version-agnostic
- **Path Resolution** - References work correctly in exported structure
- **Hierarchical Discovery** - All referenced files are included

## Cleanup

To clean up exported directories safely:

```python
from promptic import cleanup_exported_version

cleanup_exported_version("exported/workflow_v1/")
```

The cleanup function includes safety checks to prevent accidental deletion of source directories.

## Next Steps

- Modify the export script to export to different locations
- Try exporting with `version="latest"` to export the newest version
- Combine with Example 5 to load and export versions programmatically
- Use exported versions in your production applications
