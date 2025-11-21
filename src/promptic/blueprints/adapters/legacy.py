"""Legacy adapters for converting NodeNetwork to ContextBlueprint during migration.

# AICODE-NOTE: These adapters are temporary during the migration from ContextBlueprint
#              to NodeNetwork. They extract blueprint structure from NodeNetwork.root.content
#              to maintain compatibility with existing code that expects ContextBlueprint.
#              Once migration is complete, these adapters will be removed.
"""

from __future__ import annotations

from typing import Any, Literal

from promptic.blueprints.models import (
    BlueprintStep,
    ContextBlueprint,
    DataSlot,
    InstructionFallbackPolicy,
    InstructionNode,
    InstructionNodeRef,
    MemorySlot,
)
from promptic.context.nodes.models import ContextNode, NodeNetwork


def network_to_blueprint(network: NodeNetwork) -> ContextBlueprint:
    """Convert NodeNetwork to ContextBlueprint for compatibility during migration.

    # AICODE-NOTE: This is a temporary adapter during migration. It extracts blueprint
    #              structure from the root node's content field, which should contain
    #              the parsed YAML structure with steps, global_instructions, etc.
    """
    root_content = network.root.content

    # Extract blueprint fields from root node content
    name = root_content.get("name", "Unnamed Blueprint")
    prompt_template = root_content.get("prompt_template", "")
    global_instructions = _extract_instruction_refs(root_content.get("global_instructions", []))
    steps = _extract_steps(root_content.get("steps", []))
    data_slots = _extract_data_slots(root_content.get("data_slots", []))
    memory_slots = _extract_memory_slots(root_content.get("memory_slots", []))
    metadata = root_content.get("metadata", {})

    # Create ContextBlueprint from extracted data
    # Generate UUID for id (ContextBlueprint requires UUID, not path string)
    from uuid import uuid4

    blueprint = ContextBlueprint(
        id=uuid4(),  # Generate new UUID (ContextBlueprint.id must be UUID, not path)
        name=name,
        prompt_template=prompt_template,
        global_instructions=global_instructions,
        steps=steps,
        data_slots=data_slots,
        memory_slots=memory_slots,
        metadata=metadata,
    )

    return blueprint


def _extract_instruction_refs(refs_data: list[dict[str, Any]]) -> list[InstructionNodeRef]:
    """Extract InstructionNodeRef list from raw data."""
    result = []
    for ref_data in refs_data:
        if isinstance(ref_data, dict):
            result.append(InstructionNodeRef(**ref_data))
        elif isinstance(ref_data, str):
            # Simple string reference
            result.append(InstructionNodeRef(instruction_id=ref_data))
    return result


def _extract_steps(steps_data: list[dict[str, Any]]) -> list[BlueprintStep]:
    """Extract BlueprintStep list from raw data."""
    result = []
    for step_data in steps_data:
        if isinstance(step_data, dict):
            # Recursively extract children
            if "children" in step_data:
                step_data["children"] = _extract_steps(step_data["children"])
            result.append(BlueprintStep(**step_data))
    return result


def _extract_data_slots(slots_data: list[dict[str, Any]]) -> list[DataSlot]:
    """Extract DataSlot list from raw data."""
    result = []
    for slot_data in slots_data:
        if isinstance(slot_data, dict):
            result.append(DataSlot(**slot_data))
    return result


def _extract_memory_slots(slots_data: list[dict[str, Any]]) -> list[MemorySlot]:
    """Extract MemorySlot list from raw data."""
    result = []
    for slot_data in slots_data:
        if isinstance(slot_data, dict):
            result.append(MemorySlot(**slot_data))
    return result


def node_to_instruction(node: ContextNode) -> InstructionNode:
    """Convert ContextNode to InstructionNode for compatibility during migration.

    # AICODE-NOTE: This is a temporary adapter during migration. It extracts instruction
    #              metadata from ContextNode to create an InstructionNode-like structure
    #              for compatibility with existing template rendering code.
    """
    node_id = str(node.id)
    content = node.content

    # Extract instruction metadata from node content or use defaults
    instruction_id = content.get("instruction_id", node_id)
    source_uri = content.get("source_uri", node_id)
    format_map = {
        "yaml": "yaml",
        "yml": "yml",
        "markdown": "md",
        "json": "txt",  # Default for JSON
        "jinja2": "jinja",
    }
    format_key = format_map.get(node.format, "md")
    checksum = content.get("checksum", "")
    locale = content.get("locale", "en-US")
    version = content.get("version", "0.0.1")
    provider_key = content.get("provider_key", "filesystem_default")
    fallback_policy_str = content.get("fallback_policy", "error")
    fallback_policy = (
        InstructionFallbackPolicy(fallback_policy_str)
        if fallback_policy_str
        else InstructionFallbackPolicy.ERROR
    )
    placeholder_template = content.get("placeholder_template")

    # Map format_key to InstructionNode format type
    instruction_format: Literal["md", "txt", "jinja", "yaml", "yml"] = "md"
    if format_key in ("md", "txt", "jinja", "yaml", "yml"):
        instruction_format = format_key  # type: ignore[assignment]

    return InstructionNode(
        instruction_id=instruction_id,
        source_uri=source_uri,
        format=instruction_format,
        checksum=checksum,
        locale=locale,
        version=version,
        provider_key=provider_key,
        fallback_policy=fallback_policy,
        placeholder_template=placeholder_template,
    )
