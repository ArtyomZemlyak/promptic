from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Literal, Optional, Set
from uuid import UUID, uuid4

from pydantic import (
    UUID4,
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    FilePath,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings

Slug = Field(min_length=1, pattern=r"^[a-zA-Z0-9_\-]+$")
PathLikeSlug = Field(min_length=1, pattern=r"^[a-zA-Z0-9_\-/\.]+$")


class Condition(BaseModel):
    """Represents a branch predicate for blueprint steps."""

    expression: str = Field(..., min_length=3)
    description: Optional[str] = Field(default=None, max_length=160)


class InstructionNodeRef(BaseModel):
    """Reference to an instruction asset by identifier/version."""

    instruction_id: str = Field(..., min_length=1, pattern=r"^[a-zA-Z0-9_\-./]+$")
    version: Optional[str] = Field(default=None, min_length=1)


class InstructionNode(BaseModel):
    """Instruction metadata derived from instruction stores."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    instruction_id: str = Field(..., min_length=1, pattern=r"^[a-zA-Z0-9_\-./]+$")
    source_uri: AnyUrl | FilePath | str
    format: Literal["md", "txt", "jinja"]
    checksum: str = Field(..., min_length=32, max_length=64)
    locale: str = Field(default="en-US", min_length=2, max_length=16)
    version: str = Field(default="0.0.1", min_length=1, max_length=32)


class DataSlot(BaseModel):
    """Required data inputs resolved by adapters."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., min_length=1, pattern=r"^[a-z0-9_\-]+$")
    schema_definition: Dict[str, Any] = Field(default_factory=dict, alias="schema")
    adapter_key: str = Field(..., min_length=1, pattern=r"^[a-z0-9_\-\.]+$")
    cardinality: Literal["single", "list"] = Field(default="single")
    ttl_seconds: Optional[int] = Field(default=None, ge=0)


class MemorySlot(BaseModel):
    """Memory providers used during context rendering or pipeline execution."""

    name: str = Field(..., min_length=1, pattern=r"^[a-z0-9_\-]+$")
    provider_key: str = Field(..., min_length=1, pattern=r"^[a-z0-9_\-\.]+$")
    scope: Literal["conversation", "project", "global"] = Field(default="conversation")
    fallback: Optional[Literal["warn", "noop", "error"]] = Field(default="warn")


class BlueprintStep(BaseModel):
    """Ordered pipeline step that may contain children."""

    model_config = ConfigDict(use_enum_values=True)

    step_id: str = Field(..., min_length=1, pattern=r"^[a-z0-9_\-]+$")
    title: str = Field(..., min_length=3, max_length=60)
    kind: Literal["sequence", "loop", "branch"] = Field(default="sequence")
    instruction_refs: List[InstructionNodeRef] = Field(default_factory=list)
    children: List["BlueprintStep"] = Field(default_factory=list)
    loop_slot: Optional[str] = Field(default=None, min_length=1)
    conditions: Optional[List[Condition]] = None

    @model_validator(mode="after")
    def _validate_constraints(self) -> "BlueprintStep":
        if self.kind == "loop" and not self.loop_slot:
            raise ValueError("loop_slot must be provided for loop steps.")
        if self.kind != "branch" and self.conditions:
            raise ValueError("conditions are only valid for branch steps.")
        return self


class AdapterRegistration(BaseModel):
    """Registration metadata stored alongside adapter factory references."""

    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    key: str = Field(..., min_length=1, pattern=r"^[a-z0-9_\-\.]+$")
    adapter_type: Literal["data", "memory"] = Field(alias="type")
    entry_point: Optional[str] = None
    config_model: Optional[type[BaseSettings]] = None
    capabilities: Set[str] = Field(default_factory=set)


class ExecutionLogEntry(BaseModel):
    """Structured JSONL log payload emitted by the executor."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    step_id: str = Field(..., min_length=1)
    event_type: Literal[
        "instruction_loaded",
        "data_resolved",
        "memory_resolved",
        "size_warning",
        "error",
    ]
    payload: Dict[str, Any] = Field(default_factory=dict)
    reference_ids: List[str] = Field(default_factory=list)


class ContextBlueprint(BaseModel):
    """
    Core blueprint describing prompt, instructions, data slots, and steps.

    # AICODE-NOTE: ContextBlueprint enforces uniqueness constraints eagerly so
    #              downstream builders can assume canonicalized structures.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    id: UUID4 = Field(default_factory=uuid4)
    name: str = Field(..., min_length=3, max_length=80)
    prompt_template: str = Field(..., min_length=1)
    global_instructions: List[InstructionNodeRef] = Field(default_factory=list)
    steps: List[BlueprintStep]
    data_slots: List[DataSlot] = Field(default_factory=list)
    memory_slots: List[MemorySlot] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_uniqueness(self) -> "ContextBlueprint":
        if not self.steps:
            raise ValueError("Blueprint must contain at least one step.")
        self._assert_unique([slot.name for slot in self.data_slots], "data slot")
        self._assert_unique([slot.name for slot in self.memory_slots], "memory slot")
        self._assert_unique(self._collect_step_ids(self.steps), "step")
        self._assert_unique(
            [ref.instruction_id for ref in self.global_instructions],
            "global instruction",
        )
        return self

    def get_data_slot(self, name: str) -> DataSlot:
        for slot in self.data_slots:
            if slot.name == name:
                return slot
        raise KeyError(f"Data slot '{name}' not defined.")

    def get_memory_slot(self, name: str) -> MemorySlot:
        for slot in self.memory_slots:
            if slot.name == name:
                return slot
        raise KeyError(f"Memory slot '{name}' not defined.")

    @staticmethod
    def _collect_step_ids(steps: Iterable[BlueprintStep]) -> List[str]:
        ids: List[str] = []
        for step in steps:
            ids.append(step.step_id)
            ids.extend(ContextBlueprint._collect_step_ids(step.children))
        return ids

    @staticmethod
    def _assert_unique(values: Iterable[str], label: str) -> None:
        seen: Set[str] = set()
        for value in values:
            if value in seen:
                raise ValueError(f"Duplicate {label} detected: '{value}'.")
            seen.add(value)


__all__ = [
    "AdapterRegistration",
    "BlueprintStep",
    "Condition",
    "ContextBlueprint",
    "DataSlot",
    "ExecutionLogEntry",
    "InstructionNode",
    "InstructionNodeRef",
    "MemorySlot",
]
