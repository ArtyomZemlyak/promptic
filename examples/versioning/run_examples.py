import os
import sys
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).parents[2].resolve()
sys.path.insert(0, str(root_dir / "src"))

from promptic import load_blueprint, load_prompt
from promptic.versioning import cleanup_exported_version, export_version


def main():
    base_dir = Path(__file__).parent
    prompts_dir = base_dir / "prompts/task"
    export_dir = base_dir / "export"

    print(f"Running examples from: {base_dir}")

    # 1. Load latest version
    print("\n--- 1. Load Latest Version ---")
    content = load_prompt(prompts_dir, version="latest")
    print(f"Loaded content length: {len(content)}")
    print(f"Content preview: {content[:50]}...")

    # 2. Load specific version
    print("\n--- 2. Load v1.0.0 ---")
    content_v1 = load_prompt(prompts_dir, version="v1.0.0")
    print(f"Loaded content length: {len(content_v1)}")
    print(f"Content starts with: {content_v1[:50]}...")

    # 3. Hierarchical Versioning
    print("\n--- 3. Hierarchical Versioning ---")
    # Root v1, Process v2
    version_spec = {"root": "v1.0.0", "instructions/process": "v2.0.0"}
    # Use load_blueprint to verify hierarchical resolution (resolves includes)
    network = load_blueprint(prompts_dir, version=version_spec)
    print(f"Loaded network root: {network.root.id}")

    # Check referenced node version (implicitly via content)
    from promptic.sdk.nodes import render_node_network

    rendered = render_node_network(network, "markdown", render_mode="full")
    if "Process Instruction (v2.0.0)" in rendered:
        print("Verified: Contains Process Instruction v2.0.0")
    else:
        print("FAILED: Did not find Process Instruction v2.0.0")
        print(f"Rendered content:\n{rendered}")

    # 4. Export Version
    print("\n--- 4. Export Version ---")
    target_dir = export_dir / "task_v2"
    print(f"Exporting v2.0.0 to {target_dir}...")

    try:
        result = export_version(
            source_path=str(prompts_dir),
            version_spec="v2.0.0",
            target_dir=str(target_dir),
            overwrite=True,
        )
        print(f"Export successful!")
        print(f"Exported files: {len(result.exported_files)}")
        print(f"Root prompt content starts with: {result.root_prompt_content[:50]}...")

        # Verify file structure
        if (target_dir / "root_prompt.md").exists():
            print("Verified: root_prompt.md exists")
        if (target_dir / "instructions/process.md").exists():
            print("Verified: instructions/process.md exists")

    except Exception as e:
        print(f"Export failed: {e}")

    # 5. Cleanup
    print("\n--- 5. Cleanup ---")
    print(f"Cleaning up {target_dir}...")
    try:
        cleanup_exported_version(str(target_dir))
        if not target_dir.exists():
            print("Cleanup successful: Directory removed")
        else:
            print("Cleanup failed: Directory still exists")
    except Exception as e:
        print(f"Cleanup failed: {e}")


if __name__ == "__main__":
    main()
