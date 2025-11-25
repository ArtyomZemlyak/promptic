"""Reference resolution strategy implementations.

# AICODE-NOTE: This package implements the Strategy pattern for different
# reference types (markdown links, jinja2 refs, $ref). Each strategy handles
# one specific reference format, following the Single Responsibility Principle.

Strategies:
- MarkdownLinkStrategy: [text](path) references
- Jinja2RefStrategy: {# ref: path #} references
- StructuredRefStrategy: {"$ref": "path"} references
"""

from promptic.rendering.strategies.base import ReferenceStrategy
from promptic.rendering.strategies.jinja2_ref import Jinja2RefStrategy
from promptic.rendering.strategies.markdown_link import MarkdownLinkStrategy
from promptic.rendering.strategies.structured_ref import StructuredRefStrategy

__all__ = [
    "ReferenceStrategy",
    "MarkdownLinkStrategy",
    "Jinja2RefStrategy",
    "StructuredRefStrategy",
]
