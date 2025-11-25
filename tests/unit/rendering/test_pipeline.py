"""Unit tests for rendering pipeline (T058).

# AICODE-NOTE: Tests for the composable rendering pipeline pattern.
# Each test focuses on a specific aspect of pipeline functionality.
"""

import pytest

from promptic.context.nodes.models import ContextNode, NodeNetwork
from promptic.rendering.pipeline import (
    ContentExtractorStage,
    FormatConverterStage,
    PipelineBuilder,
    PipelineStage,
    ReferenceInliningStage,
    RenderContext,
    RenderingPipeline,
)

pytestmark = pytest.mark.unit


class TestRenderContext:
    """Test RenderContext dataclass."""

    def test_context_creation(self):
        """Test creating a render context."""
        node = ContextNode(
            id="test",
            content={"raw_content": "Hello"},
            format="markdown",
        )
        network = NodeNetwork(root=node, nodes={"test": node}, total_size=1, depth=1)

        context = RenderContext(
            node=node,
            network=network,
            target_format="markdown",
        )

        assert context.node == node
        assert context.network == network
        assert context.target_format == "markdown"
        assert context.content is None
        assert context.metadata == {}

    def test_with_content_creates_new_context(self):
        """Test that with_content creates a new context."""
        node = ContextNode(id="test", content={}, format="markdown")
        network = NodeNetwork(root=node, nodes={"test": node}, total_size=1, depth=1)

        context = RenderContext(node=node, network=network, target_format="markdown")
        new_context = context.with_content("new content")

        assert context.content is None  # Original unchanged
        assert new_context.content == "new content"
        assert new_context.node == context.node


class TestContentExtractorStage:
    """Test ContentExtractorStage."""

    def test_extracts_raw_content(self):
        """Test extracting raw_content from text nodes."""
        node = ContextNode(
            id="test",
            content={"raw_content": "# Hello World"},
            format="markdown",
        )
        network = NodeNetwork(root=node, nodes={"test": node}, total_size=1, depth=1)

        stage = ContentExtractorStage()
        context = RenderContext(node=node, network=network, target_format="markdown")

        result = stage.process(context)

        assert result.content == "# Hello World"

    def test_extracts_structured_content(self):
        """Test extracting structured content from YAML/JSON nodes."""
        node = ContextNode(
            id="test",
            content={"key": "value", "nested": {"a": 1}},
            format="yaml",
        )
        network = NodeNetwork(root=node, nodes={"test": node}, total_size=1, depth=1)

        stage = ContentExtractorStage()
        context = RenderContext(node=node, network=network, target_format="yaml")

        result = stage.process(context)

        assert result.content == {"key": "value", "nested": {"a": 1}}

    def test_stage_name(self):
        """Test stage name property."""
        stage = ContentExtractorStage()
        assert stage.name == "content_extractor"


class TestFormatConverterStage:
    """Test FormatConverterStage."""

    def test_no_conversion_same_format(self):
        """Test that no conversion happens for same format."""
        node = ContextNode(id="test", content={}, format="markdown")
        network = NodeNetwork(root=node, nodes={"test": node}, total_size=1, depth=1)

        stage = FormatConverterStage()
        context = RenderContext(
            node=node, network=network, target_format="markdown", content="# Hello"
        )

        result = stage.process(context)

        assert result.content == "# Hello"

    def test_yaml_to_markdown_conversion(self):
        """Test YAML to markdown conversion wraps in code block."""
        node = ContextNode(id="test", content={}, format="yaml")
        network = NodeNetwork(root=node, nodes={"test": node}, total_size=1, depth=1)

        stage = FormatConverterStage()
        context = RenderContext(
            node=node, network=network, target_format="markdown", content={"key": "value"}
        )

        result = stage.process(context)

        assert "```yaml" in result.content
        assert "key: value" in result.content

    def test_json_to_markdown_conversion(self):
        """Test JSON to markdown conversion wraps in code block."""
        node = ContextNode(id="test", content={}, format="json")
        network = NodeNetwork(root=node, nodes={"test": node}, total_size=1, depth=1)

        stage = FormatConverterStage()
        context = RenderContext(
            node=node, network=network, target_format="markdown", content={"key": "value"}
        )

        result = stage.process(context)

        assert "```json" in result.content
        assert '"key"' in result.content

    def test_stage_name(self):
        """Test stage name property."""
        stage = FormatConverterStage()
        assert stage.name == "format_converter"


class TestReferenceInliningStage:
    """Test ReferenceInliningStage."""

    def test_stage_name(self):
        """Test stage name property."""
        stage = ReferenceInliningStage()
        assert stage.name == "reference_inlining"

    def test_inlines_content(self):
        """Test that stage inlines references."""
        node = ContextNode(
            id="test",
            content={"raw_content": "Hello"},
            format="markdown",
        )
        network = NodeNetwork(root=node, nodes={"test": node}, total_size=1, depth=1)

        stage = ReferenceInliningStage()
        context = RenderContext(node=node, network=network, target_format="markdown")

        result = stage.process(context)

        # Content should be processed (even if no refs to inline)
        assert result.content is not None


class TestRenderingPipeline:
    """Test RenderingPipeline composition."""

    def test_empty_pipeline(self):
        """Test pipeline with no stages returns None."""
        node = ContextNode(id="test", content={"raw_content": "Hello"}, format="markdown")
        network = NodeNetwork(root=node, nodes={"test": node}, total_size=1, depth=1)

        pipeline = RenderingPipeline()
        result = pipeline.execute(node, network, "markdown")

        assert result is None  # No stages processed content

    def test_single_stage_pipeline(self):
        """Test pipeline with single stage."""
        node = ContextNode(id="test", content={"raw_content": "Hello"}, format="markdown")
        network = NodeNetwork(root=node, nodes={"test": node}, total_size=1, depth=1)

        pipeline = RenderingPipeline()
        pipeline.add_stage(ContentExtractorStage())

        result = pipeline.execute(node, network, "markdown")

        assert result == "Hello"

    def test_multi_stage_pipeline(self):
        """Test pipeline with multiple stages."""
        node = ContextNode(id="test", content={"raw_content": "Hello"}, format="markdown")
        network = NodeNetwork(root=node, nodes={"test": node}, total_size=1, depth=1)

        pipeline = RenderingPipeline()
        pipeline.add_stage(ContentExtractorStage())
        pipeline.add_stage(FormatConverterStage())

        result = pipeline.execute(node, network, "markdown")

        assert result == "Hello"  # No conversion needed for same format

    def test_method_chaining(self):
        """Test that add_stage returns self for chaining."""
        pipeline = RenderingPipeline()
        result = pipeline.add_stage(ContentExtractorStage()).add_stage(FormatConverterStage())

        assert result is pipeline
        assert len(pipeline.stages) == 2

    def test_default_pipeline(self):
        """Test default pipeline creation."""
        pipeline = RenderingPipeline.default()

        assert len(pipeline.stages) == 3
        assert pipeline.stages[0].name == "content_extractor"
        assert pipeline.stages[1].name == "reference_inlining"
        assert pipeline.stages[2].name == "format_converter"

    def test_insert_stage(self):
        """Test inserting stage at specific position."""
        pipeline = RenderingPipeline()
        pipeline.add_stage(ContentExtractorStage())
        pipeline.add_stage(FormatConverterStage())
        pipeline.insert_stage(1, ReferenceInliningStage())

        assert len(pipeline.stages) == 3
        assert pipeline.stages[1].name == "reference_inlining"

    def test_remove_stage(self):
        """Test removing stage by name."""
        pipeline = RenderingPipeline.default()
        pipeline.remove_stage("format_converter")

        assert len(pipeline.stages) == 2
        assert all(s.name != "format_converter" for s in pipeline.stages)


class TestPipelineBuilder:
    """Test PipelineBuilder fluent API."""

    def test_builder_creates_empty_pipeline(self):
        """Test builder creates pipeline with no stages by default."""
        pipeline = RenderingPipeline.builder().build()

        assert len(pipeline.stages) == 0

    def test_builder_with_content_extraction(self):
        """Test adding content extraction stage."""
        pipeline = RenderingPipeline.builder().with_content_extraction().build()

        assert len(pipeline.stages) == 1
        assert pipeline.stages[0].name == "content_extractor"

    def test_builder_with_reference_inlining(self):
        """Test adding reference inlining stage."""
        pipeline = RenderingPipeline.builder().with_reference_inlining().build()

        assert len(pipeline.stages) == 1
        assert pipeline.stages[0].name == "reference_inlining"

    def test_builder_with_format_conversion(self):
        """Test adding format conversion stage."""
        pipeline = RenderingPipeline.builder().with_format_conversion().build()

        assert len(pipeline.stages) == 1
        assert pipeline.stages[0].name == "format_converter"

    def test_builder_chaining(self):
        """Test builder method chaining."""
        pipeline = (
            RenderingPipeline.builder()
            .with_content_extraction()
            .with_reference_inlining()
            .with_format_conversion()
            .build()
        )

        assert len(pipeline.stages) == 3

    def test_builder_with_custom_stage(self):
        """Test adding custom stage via builder."""

        class CustomStage(PipelineStage):
            @property
            def name(self) -> str:
                return "custom"

            def process(self, context: RenderContext) -> RenderContext:
                return context.with_content("custom output")

        pipeline = (
            RenderingPipeline.builder()
            .with_content_extraction()
            .with_custom_stage(CustomStage())
            .build()
        )

        assert len(pipeline.stages) == 2
        assert pipeline.stages[1].name == "custom"


class TestPipelineIntegration:
    """Integration tests for pipeline with real content."""

    def test_full_pipeline_markdown_to_markdown(self):
        """Test full pipeline with markdown content."""
        node = ContextNode(
            id="root",
            content={"raw_content": "# Title\n\nSome content here."},
            format="markdown",
        )
        network = NodeNetwork(root=node, nodes={"root": node}, total_size=1, depth=1)

        pipeline = RenderingPipeline.default()
        result = pipeline.execute(node, network, "markdown")

        assert "# Title" in result
        assert "Some content here" in result

    def test_full_pipeline_yaml_to_markdown(self):
        """Test full pipeline converting YAML to markdown."""
        node = ContextNode(
            id="root",
            content={"name": "test", "value": 42},
            format="yaml",
        )
        network = NodeNetwork(root=node, nodes={"root": node}, total_size=1, depth=1)

        pipeline = RenderingPipeline.default()
        result = pipeline.execute(node, network, "markdown")

        assert "```yaml" in result
        assert "name: test" in result
