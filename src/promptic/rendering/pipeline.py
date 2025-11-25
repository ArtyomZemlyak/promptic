"""Rendering pipeline for composable content processing.

# AICODE-NOTE: This module implements the Pipeline pattern for rendering operations.
# The pipeline allows composing multiple processing stages (strategies, transformers)
# into a single configurable rendering flow. This enables:
# - Easy addition of new processing stages
# - Configurable order of operations
# - Testable individual stages
# - Separation of concerns between different rendering aspects
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, TypeVar

from promptic.context.nodes.models import ContextNode, NodeNetwork

T = TypeVar("T")


@dataclass
class RenderContext:
    """
    Context object passed through the rendering pipeline.

    # AICODE-NOTE: The context carries all information needed by pipeline stages:
    # - The node being processed
    # - The full network for reference resolution
    # - Target output format
    # - Accumulated processed content
    # - Metadata for inter-stage communication

    Attributes:
        node: The context node being rendered
        network: The full node network for lookups
        target_format: Target output format (markdown, yaml, json, jinja2)
        content: Current processed content (mutated by stages)
        metadata: Additional data for inter-stage communication
    """

    node: ContextNode
    network: NodeNetwork
    target_format: str
    content: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def with_content(self, new_content: Any) -> "RenderContext":
        """Create new context with updated content."""
        return RenderContext(
            node=self.node,
            network=self.network,
            target_format=self.target_format,
            content=new_content,
            metadata=self.metadata.copy(),
        )


class PipelineStage(ABC):
    """
    Abstract base class for pipeline processing stages.

    # AICODE-NOTE: Each stage implements a single responsibility in the rendering
    # pipeline. Stages receive a RenderContext and return a modified context.
    # This follows the Chain of Responsibility pattern.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Stage name for debugging and logging."""
        pass

    @abstractmethod
    def process(self, context: RenderContext) -> RenderContext:
        """
        Process the render context and return updated context.

        Args:
            context: Current render context

        Returns:
            Updated render context with processed content
        """
        pass


class ContentExtractorStage(PipelineStage):
    """
    Pipeline stage that extracts initial content from node.

    # AICODE-NOTE: This is typically the first stage in a pipeline.
    # It extracts raw_content from text nodes or the full content dict
    # from structured nodes.
    """

    @property
    def name(self) -> str:
        return "content_extractor"

    def process(self, context: RenderContext) -> RenderContext:
        node = context.node
        if "raw_content" in node.content:
            return context.with_content(node.content["raw_content"])
        return context.with_content(node.content.copy())


class ReferenceInliningStage(PipelineStage):
    """
    Pipeline stage that inlines references using ReferenceInliner.

    # AICODE-NOTE: This stage uses the existing ReferenceInliner to resolve
    # and inline all references (markdown links, jinja2 refs, $ref) in the content.
    """

    def __init__(self):
        from promptic.rendering.inliner import ReferenceInliner

        self.inliner = ReferenceInliner()

    @property
    def name(self) -> str:
        return "reference_inlining"

    def process(self, context: RenderContext) -> RenderContext:
        inlined = self.inliner.inline_references(
            context.node, context.network, context.target_format
        )
        return context.with_content(inlined)


class FormatConverterStage(PipelineStage):
    """
    Pipeline stage that converts content to target format.

    # AICODE-NOTE: This stage handles format conversion (e.g., YAML to markdown).
    # It wraps structured content in code blocks when converting to markdown.
    """

    @property
    def name(self) -> str:
        return "format_converter"

    def process(self, context: RenderContext) -> RenderContext:
        content = context.content
        source_format = context.node.format
        target_format = context.target_format

        # No conversion needed for same format
        if source_format == target_format:
            return context

        # Convert structured content to string for markdown output
        if target_format == "markdown" and isinstance(content, dict):
            import json

            import yaml

            if source_format == "yaml":
                formatted = yaml.dump(content, default_flow_style=False, sort_keys=False)
                new_content = f"```yaml\n{formatted}```"
            elif source_format == "json":
                formatted = json.dumps(content, indent=2)
                new_content = f"```json\n{formatted}\n```"
            else:
                new_content = str(content)
            return context.with_content(new_content)

        return context


class RenderingPipeline:
    """
    Composable rendering pipeline for processing node content.

    # AICODE-NOTE: The pipeline composes multiple PipelineStage instances
    # and executes them in order. This allows:
    # - Flexible configuration of rendering stages
    # - Easy addition of custom processing steps
    # - Testable individual stages
    # - Clear separation of rendering concerns

    Usage:
        pipeline = RenderingPipeline()
        pipeline.add_stage(ContentExtractorStage())
        pipeline.add_stage(ReferenceInliningStage())
        pipeline.add_stage(FormatConverterStage())

        result = pipeline.execute(node, network, "markdown")

    Or use the builder pattern:
        pipeline = (
            RenderingPipeline.builder()
            .with_content_extraction()
            .with_reference_inlining()
            .with_format_conversion()
            .build()
        )
    """

    def __init__(self, stages: list[PipelineStage] | None = None):
        """
        Initialize pipeline with optional stages.

        Args:
            stages: Initial list of pipeline stages
        """
        self._stages: list[PipelineStage] = stages or []

    def add_stage(self, stage: PipelineStage) -> "RenderingPipeline":
        """
        Add a stage to the pipeline.

        Args:
            stage: Pipeline stage to add

        Returns:
            Self for method chaining
        """
        self._stages.append(stage)
        return self

    def insert_stage(self, index: int, stage: PipelineStage) -> "RenderingPipeline":
        """
        Insert a stage at specific position.

        Args:
            index: Position to insert at
            stage: Pipeline stage to insert

        Returns:
            Self for method chaining
        """
        self._stages.insert(index, stage)
        return self

    def remove_stage(self, name: str) -> "RenderingPipeline":
        """
        Remove a stage by name.

        Args:
            name: Name of stage to remove

        Returns:
            Self for method chaining
        """
        self._stages = [s for s in self._stages if s.name != name]
        return self

    @property
    def stages(self) -> list[PipelineStage]:
        """Get list of pipeline stages."""
        return self._stages.copy()

    def execute(
        self,
        node: ContextNode,
        network: NodeNetwork,
        target_format: str,
    ) -> Any:
        """
        Execute the pipeline on a node.

        Args:
            node: Node to process
            network: Full node network for reference resolution
            target_format: Target output format

        Returns:
            Processed content
        """
        context = RenderContext(
            node=node,
            network=network,
            target_format=target_format,
        )

        for stage in self._stages:
            context = stage.process(context)

        return context.content

    @classmethod
    def default(cls) -> "RenderingPipeline":
        """
        Create a pipeline with default stages.

        Returns:
            Pipeline with content extraction, reference inlining, and format conversion
        """
        return cls(
            stages=[
                ContentExtractorStage(),
                ReferenceInliningStage(),
                FormatConverterStage(),
            ]
        )

    @classmethod
    def builder(cls) -> "PipelineBuilder":
        """
        Get a builder for constructing pipelines.

        Returns:
            PipelineBuilder instance
        """
        return PipelineBuilder()


class PipelineBuilder:
    """
    Builder for constructing rendering pipelines.

    # AICODE-NOTE: The builder provides a fluent API for constructing pipelines
    # with common stage configurations. This improves readability and makes
    # pipeline construction self-documenting.
    """

    def __init__(self):
        self._stages: list[PipelineStage] = []

    def with_content_extraction(self) -> "PipelineBuilder":
        """Add content extraction stage."""
        self._stages.append(ContentExtractorStage())
        return self

    def with_reference_inlining(self) -> "PipelineBuilder":
        """Add reference inlining stage."""
        self._stages.append(ReferenceInliningStage())
        return self

    def with_format_conversion(self) -> "PipelineBuilder":
        """Add format conversion stage."""
        self._stages.append(FormatConverterStage())
        return self

    def with_custom_stage(self, stage: PipelineStage) -> "PipelineBuilder":
        """Add a custom pipeline stage."""
        self._stages.append(stage)
        return self

    def build(self) -> RenderingPipeline:
        """Build the configured pipeline."""
        return RenderingPipeline(stages=self._stages)
