"""Integration tests for node networks."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from promptic.context.nodes.models import NetworkConfig
from promptic.sdk.nodes import load_node_network, render_node_network


def test_build_three_level_deep_node_network_mixed_formats():
    """Test building 3-level deep node network with mixed formats."""
    # This test will fail until network building is implemented
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create root node (YAML blueprint)
        root_yaml = root / "root.yaml"
        root_yaml.write_text(
            """name: Root Blueprint
steps:
  - step_id: step1
    instruction_refs:
      - $ref: instructions/step1.md
"""
        )

        # Create instruction node (Markdown)
        instructions_dir = root / "instructions"
        instructions_dir.mkdir()
        step1_md = instructions_dir / "step1.md"
        step1_md.write_text(
            """# Step 1 Instruction

This is step 1.

See [data guide](data/guide.json) for details.
"""
        )

        # Create data node (JSON)
        data_dir = root / "data"
        data_dir.mkdir()
        guide_json = data_dir / "guide.json"
        guide_json.write_text(
            """{
  "format": "guide",
  "content": "Data guide content"
}
"""
        )

        # Load network
        config = NetworkConfig(max_depth=10)
        network = load_node_network(root_path=root_yaml, config=config)

        # Verify network structure
        assert network.root is not None
        assert len(network.nodes) >= 3  # root + step1 + guide
        assert network.depth == 3

        # TODO: Implement network building and update this test
        pass


def test_network_loading_performance():
    """Test network loading performance (<2 seconds for <50 nodes)."""
    # This test will fail until network building is implemented
    import time

    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create a network with ~30 nodes
        # (Simplified for test - in practice would create more complex structure)
        root_yaml = root / "root.yaml"
        root_yaml.write_text("name: Performance Test\n")

        # Load network and measure time
        config = NetworkConfig(max_depth=10)
        start_time = time.time()
        network = load_node_network(root_path=root_yaml, config=config)
        elapsed = time.time() - start_time

        # Should complete in <2 seconds
        assert elapsed < 2.0

        # TODO: Implement network building and update this test
        pass


def test_network_rendering_all_formats():
    """Test network rendering across all formats."""
    # This test will fail until network rendering is implemented
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create simple network
        root_yaml = root / "root.yaml"
        root_yaml.write_text("name: Render Test\n")

        # Load network
        config = NetworkConfig(max_depth=10)
        network = load_node_network(root_path=root_yaml, config=config)

        # Render to all formats
        yaml_output = render_node_network(network, target_format="yaml")
        markdown_output = render_node_network(network, target_format="markdown")
        json_output = render_node_network(network, target_format="json")
        file_first_output = render_node_network(
            network, target_format="yaml", render_mode="file_first"
        )

        # All outputs should be non-empty strings
        assert len(yaml_output) > 0
        assert len(markdown_output) > 0
        assert len(json_output) > 0
        assert len(file_first_output) > 0

        # TODO: Implement network rendering and update this test
        pass


# AICODE-NOTE: test_token_counting_on_final_rendered_content removed
# Token counting feature removed in spec 006-remove-unused-code
