"""Strategy for processing JSON Schema-style $ref references.

# AICODE-NOTE: This strategy handles $ref objects in YAML/JSON content,
# following the JSON Schema $ref convention. It recursively processes
# nested dicts and lists to find all $ref entries.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from promptic.rendering.strategies.base import ReferenceStrategy


class StructuredRefStrategy(ReferenceStrategy):
    """Strategy for processing JSON Schema-style $ref references.

    Pattern: {"$ref": "path/to/file"}
    Example: {"data": {"$ref": "config.yaml"}} -> {"data": <config content>}

    This strategy recursively processes nested dicts and lists to find
    all $ref entries and replace them with the referenced content.
    """

    @property
    def name(self) -> str:
        return "structured_ref"

    def can_process(self, content: Any) -> bool:
        """Check if content contains $ref entries."""
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
                    if isinstance(item, dict):
                        # Check if the list item itself is a $ref
                        if "$ref" in item:
                            return True
                        # Or if it contains nested $refs
                        if self._has_ref(item):
                            return True
        return False

    def process_string(
        self,
        content: str,
        node_lookup: Callable[[str], Optional[Any]],
        content_renderer: Callable[[Any, str], str],
        target_format: str,
    ) -> str:
        """$ref is structure-based, not string-based, return as-is."""
        return content

    def process_structure(
        self,
        content: dict[str, Any],
        node_lookup: Callable[[str], Optional[Any]],
        content_renderer: Callable[[Any, str], Any],
        target_format: str,
    ) -> dict[str, Any]:
        """Process structured content and replace $ref objects with resolved content."""
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
                new_list = []
                for item in value:
                    if isinstance(item, dict):
                        # Check if list item is a $ref
                        if "$ref" in item and isinstance(item["$ref"], str):
                            ref_path = item["$ref"]
                            node = node_lookup(ref_path)
                            if node:
                                new_list.append(content_renderer(node, target_format))
                            else:
                                new_list.append(item)
                        else:
                            # Recursively process nested dict
                            new_list.append(
                                self._replace_refs(
                                    item, node_lookup, content_renderer, target_format
                                )
                            )
                    else:
                        new_list.append(item)
                result[key] = new_list
            else:
                result[key] = value
        return result
