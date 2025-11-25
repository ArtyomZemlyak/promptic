import shutil
from pathlib import Path

from promptic.sdk.api import export_version

# Setup paths
base_dir = Path(__file__).parent
export_dir = base_dir / "export_output"

# Clean previous export
if export_dir.exists():
    shutil.rmtree(export_dir)

# Variables with different scopes
variables = {
    # Simple (Global)
    "global_var": "I am global",
    "shared_var": "I am default shared",
    # Node Scoped
    "root.root_specific": "I am root specific",
    "child.child_specific": "I am child specific",
    # Path Scoped (overrides global/node)
    # Note: The path follows the reference graph, not just directory structure.
    # root.md references group/child.md directly, so the path is root.child
    "root.child.shared_var": "I am child shared (path scoped)",
    "root.child.path_only": "I am path only",
}

print("Exporting with variables...")
result = export_version(
    source_path=base_dir / "root.md", version_spec="latest", target_dir=export_dir, vars=variables
)

print("\nExport successful!")
print(f"Files exported: {len(result.exported_files)}")

print("\n--- content of export_output/root.md ---")
print((export_dir / "root.md").read_text())

print("\n--- content of export_output/group/child.md ---")
print((export_dir / "group/child.md").read_text())

# Cleanup
shutil.rmtree(export_dir)
