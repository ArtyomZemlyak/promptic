# Data Model: SOLID Refactoring

**Branch**: `008-solid-refactor` | **Date**: 2025-11-25

## New Entities

### ReferenceStrategy (Abstract Base Class)

```python
from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

class ReferenceStrategy(ABC):
    """Abstract base class for reference resolution strategies.
    
    # AICODE-NOTE: Each strategy handles one type of reference pattern:
    # - MarkdownLinkStrategy: [text](path)
    # - Jinja2RefStrategy: {# ref: path #}
    # - StructuredRefStrategy: {"$ref": "path"}
    
    The strategy pattern allows adding new reference types without modifying
    existing code (Open/Closed Principle).
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name for debugging and logging."""
        pass
    
    @abstractmethod
    def can_process(self, content: Any) -> bool:
        """Check if this strategy can process the given content.
        
        Args:
            content: Content to check (string or dict)
            
        Returns:
            True if this strategy should process the content
        """
        pass
    
    @abstractmethod
    def process_string(
        self,
        content: str,
        node_lookup: Callable[[str], Optional[Any]],
        content_renderer: Callable[[Any, str], str],
        target_format: str,
    ) -> str:
        """Process string content and replace references.
        
        Args:
            content: String content with potential references
            node_lookup: Function(path) -> ContextNode or None
            content_renderer: Function(node, format) -> rendered string
            target_format: Target output format (yaml, json, markdown)
            
        Returns:
            Content with references replaced by resolved content
        """
        pass
    
    @abstractmethod
    def process_structure(
        self,
        content: dict[str, Any],
        node_lookup: Callable[[str], Optional[Any]],
        content_renderer: Callable[[Any, str], Any],
        target_format: str,
    ) -> dict[str, Any]:
        """Process structured content (dict) and replace references.
        
        Args:
            content: Dict content with potential $ref entries
            node_lookup: Function(path) -> ContextNode or None
            content_renderer: Function(node, format) -> rendered content
            target_format: Target output format
            
        Returns:
            Content with $ref entries replaced by resolved content
        """
        pass
```

### MarkdownLinkStrategy

```python
import re
from typing import Any, Callable, Optional

class MarkdownLinkStrategy(ReferenceStrategy):
    """Strategy for processing markdown link references [text](path).
    
    # AICODE-NOTE: This strategy handles markdown-style links that reference
    # other files in the node network. External URLs (http://, https://, mailto:)
    # are preserved unchanged.
    
    Pattern: \[([^\]]+)\]\(([^)]+)\)
    Example: [Instructions](instructions.md) -> content of instructions.md
    """
    
    LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "#")
    
    @property
    def name(self) -> str:
        return "markdown_link"
    
    def can_process(self, content: Any) -> bool:
        if isinstance(content, str):
            return bool(self.LINK_PATTERN.search(content))
        return False
    
    def process_string(
        self,
        content: str,
        node_lookup: Callable[[str], Optional[Any]],
        content_renderer: Callable[[Any, str], str],
        target_format: str,
    ) -> str:
        def replace_link(match: re.Match[str]) -> str:
            path = match.group(2)
            
            # Preserve external links
            if path.startswith(self.EXTERNAL_PREFIXES):
                return match.group(0)
            
            node = node_lookup(path)
            if node:
                return content_renderer(node, target_format)
            return match.group(0)
        
        return self.LINK_PATTERN.sub(replace_link, content)
    
    def process_structure(
        self,
        content: dict[str, Any],
        node_lookup: Callable[[str], Optional[Any]],
        content_renderer: Callable[[Any, str], Any],
        target_format: str,
    ) -> dict[str, Any]:
        # Markdown links don't appear in structured content
        return content
```

### Jinja2RefStrategy

```python
import re
from typing import Any, Callable, Optional

class Jinja2RefStrategy(ReferenceStrategy):
    """Strategy for processing Jinja2-style reference comments.
    
    # AICODE-NOTE: This strategy handles Jinja2 comment-style references
    # used for including external files in templates.
    
    Pattern: \{\#\s*ref:\s*([^\#]+)\s*\#\}
    Example: {# ref: data.yaml #} -> content of data.yaml
    """
    
    REF_PATTERN = re.compile(r"\{\#\s*ref:\s*([^\#]+)\s*\#\}", re.IGNORECASE)
    
    @property
    def name(self) -> str:
        return "jinja2_ref"
    
    def can_process(self, content: Any) -> bool:
        if isinstance(content, str):
            return bool(self.REF_PATTERN.search(content))
        return False
    
    def process_string(
        self,
        content: str,
        node_lookup: Callable[[str], Optional[Any]],
        content_renderer: Callable[[Any, str], str],
        target_format: str,
    ) -> str:
        def replace_ref(match: re.Match[str]) -> str:
            path = match.group(1).strip()
            node = node_lookup(path)
            if node:
                return content_renderer(node, target_format)
            return match.group(0)
        
        return self.REF_PATTERN.sub(replace_ref, content)
    
    def process_structure(
        self,
        content: dict[str, Any],
        node_lookup: Callable[[str], Optional[Any]],
        content_renderer: Callable[[Any, str], Any],
        target_format: str,
    ) -> dict[str, Any]:
        # Jinja2 refs are string-based, not in structured content
        return content
```

### StructuredRefStrategy

```python
from typing import Any, Callable, Optional

class StructuredRefStrategy(ReferenceStrategy):
    """Strategy for processing JSON Schema-style $ref references.
    
    # AICODE-NOTE: This strategy handles $ref objects in YAML/JSON content,
    # following the JSON Schema $ref convention.
    
    Pattern: {"$ref": "path/to/file"}
    Example: {"data": {"$ref": "config.yaml"}} -> {"data": <config content>}
    """
    
    @property
    def name(self) -> str:
        return "structured_ref"
    
    def can_process(self, content: Any) -> bool:
        if isinstance(content, dict):
            return self._has_ref(content)
        return False
    
    def _has_ref(self, data: dict[str, Any]) -> bool:
        """Recursively check if dict contains $ref."""
        for value in data.values():
            if isinstance(value, dict):
                if "$ref" in value:
                    return True
                if self._has_ref(value):
                    return True
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and self._has_ref(item):
                        return True
        return False
    
    def process_string(
        self,
        content: str,
        node_lookup: Callable[[str], Optional[Any]],
        content_renderer: Callable[[Any, str], str],
        target_format: str,
    ) -> str:
        # $ref is structure-based, not string-based
        return content
    
    def process_structure(
        self,
        content: dict[str, Any],
        node_lookup: Callable[[str], Optional[Any]],
        content_renderer: Callable[[Any, str], Any],
        target_format: str,
    ) -> dict[str, Any]:
        return self._replace_refs(content, node_lookup, content_renderer, target_format)
    
    def _replace_refs(
        self,
        data: dict[str, Any],
        node_lookup: Callable[[str], Optional[Any]],
        content_renderer: Callable[[Any, str], Any],
        target_format: str,
    ) -> dict[str, Any]:
        """Recursively replace $ref objects with resolved content."""
        result = {}
        for key, value in data.items():
            if isinstance(value, dict):
                if "$ref" in value and isinstance(value["$ref"], str):
                    ref_path = value["$ref"]
                    node = node_lookup(ref_path)
                    if node:
                        result[key] = content_renderer(node, target_format)
                    else:
                        result[key] = value
                else:
                    result[key] = self._replace_refs(
                        value, node_lookup, content_renderer, target_format
                    )
            elif isinstance(value, list):
                result[key] = [
                    self._replace_refs(item, node_lookup, content_renderer, target_format)
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        return result
```

### ReferenceInliner

```python
from typing import Any, Optional
from promptic.context.nodes.models import ContextNode, NodeNetwork

class ReferenceInliner:
    """Service for inlining referenced content into nodes.
    
    # AICODE-NOTE: This class consolidates all duplicate process_node_content
    # implementations from the original render_node_network function.
    # It orchestrates multiple strategies to handle different reference types.
    
    Usage:
        inliner = ReferenceInliner()
        content = inliner.inline_references(node, network, "markdown")
    """
    
    def __init__(self, strategies: list[ReferenceStrategy] | None = None):
        """Initialize with reference strategies.
        
        Args:
            strategies: List of strategies to use. Defaults to all built-in strategies.
        """
        self.strategies = strategies or self._default_strategies()
    
    def _default_strategies(self) -> list[ReferenceStrategy]:
        """Get default strategy instances."""
        return [
            Jinja2RefStrategy(),
            MarkdownLinkStrategy(),
            StructuredRefStrategy(),
        ]
    
    def inline_references(
        self,
        node: ContextNode,
        network: NodeNetwork,
        target_format: str,
    ) -> str | dict[str, Any]:
        """Inline all references in node content.
        
        Args:
            node: Node to process
            network: Network containing all nodes for lookup
            target_format: Target output format (yaml, json, markdown, jinja2)
            
        Returns:
            Content with references inlined (string for text formats, dict for structured)
        """
        content = node.content.copy()
        
        # Create lookup function
        def node_lookup(path: str) -> Optional[ContextNode]:
            return self._find_node(path, network)
        
        # Create content renderer
        def content_renderer(child_node: ContextNode, fmt: str) -> Any:
            # Recursively process child nodes
            return self.inline_references(child_node, network, fmt)
        
        # Process based on content type
        if "raw_content" in content and isinstance(content["raw_content"], str):
            # Text content (markdown, jinja2)
            processed = content["raw_content"]
            for strategy in self.strategies:
                if strategy.can_process(processed):
                    processed = strategy.process_string(
                        processed, node_lookup, content_renderer, target_format
                    )
            return processed
        else:
            # Structured content (yaml, json)
            processed = content
            for strategy in self.strategies:
                if strategy.can_process(processed):
                    processed = strategy.process_structure(
                        processed, node_lookup, content_renderer, target_format
                    )
            return processed
    
    def _find_node(self, path: str, network: NodeNetwork) -> Optional[ContextNode]:
        """Find node in network by path.
        
        # AICODE-NOTE: This consolidates the duplicate node lookup logic
        # that was repeated 12+ times in render_node_network.
        """
        for node_id, node in network.nodes.items():
            if (
                path == str(node_id)
                or path in str(node_id)
                or str(node_id).endswith(path)
            ):
                return node
        return None
```

## Class Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         <<interface>>                           │
│                       ReferenceStrategy                         │
├─────────────────────────────────────────────────────────────────┤
│ + name: str                                                     │
│ + can_process(content: Any) -> bool                             │
│ + process_string(content, lookup, renderer, format) -> str      │
│ + process_structure(content, lookup, renderer, format) -> dict  │
└─────────────────────────────────────────────────────────────────┘
                              △
                              │
           ┌──────────────────┼──────────────────┐
           │                  │                  │
           ▼                  ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│MarkdownLink    │ │ Jinja2Ref      │ │ StructuredRef       │
│Strategy        │ │ Strategy       │ │ Strategy            │
├─────────────────┤ ├─────────────────┤ ├─────────────────────┤
│ LINK_PATTERN   │ │ REF_PATTERN    │ │ _has_ref()          │
│ EXTERNAL_PREFIX│ │                │ │ _replace_refs()     │
└─────────────────┘ └─────────────────┘ └─────────────────────┘
                              △
                              │ uses
                              │
              ┌───────────────────────────────┐
              │       ReferenceInliner        │
              ├───────────────────────────────┤
              │ - strategies: list[Strategy]  │
              ├───────────────────────────────┤
              │ + inline_references()         │
              │ - _find_node()                │
              │ - _default_strategies()       │
              └───────────────────────────────┘
                              △
                              │ uses
                              │
              ┌───────────────────────────────┐
              │     render_node_network()     │
              │        (sdk/nodes.py)         │
              └───────────────────────────────┘
```

## Existing Entities (Unchanged)

### ContextNode

```python
class ContextNode(BaseModel):
    id: str | UUID
    content: dict[str, Any]
    format: Literal["yaml", "jinja2", "markdown", "json"]
    semantic_type: Optional[Literal["blueprint", "instruction", "data", "memory"]]
    version: Optional[str]
    references: list[NodeReference]
    children: list[ContextNode]
    metadata: dict[str, Any]
```

### NodeNetwork

```python
class NodeNetwork(BaseModel):
    root: ContextNode
    nodes: dict[str, ContextNode]
    total_size: int
    depth: int
```

### NodeReference

```python
class NodeReference(BaseModel):
    path: str
    type: Literal["file", "id", "uri"]
    label: Optional[str]
```

## Integration Points

### sdk/nodes.py - render_node_network (After Refactoring)

```python
def render_node_network(
    network: NodeNetwork,
    target_format: Literal["yaml", "markdown", "json", "jinja2"],
    render_mode: Literal["full", "file_first"] = "file_first",
    vars: dict[str, Any] | None = None,
) -> str:
    """Render a NodeNetwork to target format."""
    # Apply variables if provided
    if vars:
        network = network.model_copy(deep=True)
        _apply_variables_to_network(network, vars)
    
    # Fast path: file_first mode with same format
    if render_mode == "file_first" and network.root.format == target_format:
        if "raw_content" in network.root.content:
            return str(network.root.content["raw_content"])
    
    # Full mode: use ReferenceInliner
    if render_mode == "full" and network.root.references:
        inliner = ReferenceInliner()
        inlined_content = inliner.inline_references(
            network.root, network, target_format
        )
        return _format_output(inlined_content, target_format, network.root.format)
    
    # Default: render root node
    return render_node(network.root, target_format)
```

This reduces the function from ~750 lines to ~30 lines.

