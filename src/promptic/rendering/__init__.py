"""Rendering module for reference resolution and content inlining.

# AICODE-NOTE: This module consolidates duplicate reference processing code
# from sdk/nodes.py into reusable, testable components following SOLID principles.

Components:
- ReferenceInliner: Service for inlining referenced content into nodes
- ReferenceStrategy: Abstract base for reference resolution strategies
- RenderingPipeline: Composable pipeline for rendering operations

Usage:
    from promptic.rendering import ReferenceInliner

    inliner = ReferenceInliner()
    content = inliner.inline_references(node, network, "markdown")

    # Or use the pipeline pattern:
    from promptic.rendering import RenderingPipeline

    pipeline = RenderingPipeline.default()
    result = pipeline.execute(node, network, "markdown")
"""

from promptic.rendering.inliner import ReferenceInliner
from promptic.rendering.pipeline import (
    ContentExtractorStage,
    FormatConverterStage,
    PipelineBuilder,
    PipelineStage,
    ReferenceInliningStage,
    RenderContext,
    RenderingPipeline,
)
from promptic.rendering.strategies import (
    Jinja2RefStrategy,
    MarkdownLinkStrategy,
    ReferenceStrategy,
    StructuredRefStrategy,
)

__all__ = [
    # Inliner
    "ReferenceInliner",
    # Strategies
    "ReferenceStrategy",
    "MarkdownLinkStrategy",
    "Jinja2RefStrategy",
    "StructuredRefStrategy",
    # Pipeline
    "RenderingPipeline",
    "RenderContext",
    "PipelineStage",
    "PipelineBuilder",
    "ContentExtractorStage",
    "ReferenceInliningStage",
    "FormatConverterStage",
]
