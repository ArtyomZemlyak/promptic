import os
import sys
from pathlib import Path

# Add src to path to import promptic
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from promptic import load_prompt
from promptic.versioning import cleanup_exported_version, export_version


def run_examples():
    print("--- Basic Versioning ---")
    # Load latest version
    basic_path = Path(__file__).parent / "basic"
    prompt_content = load_prompt(basic_path, version="latest")
    print(f"Loaded latest: {prompt_content.strip()}")

    # Load specific version
    prompt_v1_content = load_prompt(basic_path, version="v1")
    print(f"Loaded v1: {prompt_v1_content.strip()}")

    print("\n--- Hierarchical Versioning ---")
    # Load hierarchical
    hier_path = Path(__file__).parent / "hierarchical"
    # Even though root_v1 refers to instructions/context.md, it resolves to instructions/context_v1.md
    prompt_h_content = load_prompt(hier_path, version="v1")
    print(f"Loaded hierarchical root v1:\n{prompt_h_content.strip()}")

    print("\n--- Export ---")
    export_dir = Path(__file__).parent / "export_output"
    print(f"Exporting v1 to {export_dir}...")

    try:
        result = export_version(
            source_path=hier_path, version_spec="v1", target_dir=export_dir, overwrite=True
        )
        print(f"Exported {len(result.exported_files)} files.")
        print(f"Root content:\n{result.root_prompt_content.strip()}")

        print(f"\nExported directory structure:")
        for root, dirs, files in os.walk(export_dir):
            level = root.replace(str(export_dir), "").count(os.sep)
            indent = " " * 4 * (level)
            print(f"{indent}{os.path.basename(root)}/")
            subindent = " " * 4 * (level + 1)
            for f in files:
                print(f"{subindent}{f}")

    except Exception as e:
        print(f"Export failed: {e}")

    print("\n--- Cleanup ---")
    print(f"Cleaning up {export_dir}...")
    try:
        cleanup_exported_version(export_dir)
        print("Cleanup successful.")
    except Exception as e:
        print(f"Cleanup failed: {e}")


if __name__ == "__main__":
    run_examples()
