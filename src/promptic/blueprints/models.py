from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Literal, Optional, Set
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from promptic.pipeline.context_materializer import ContextMaterializer
    from promptic.settings.base import ContextEngineSettings

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


class InstructionFallbackPolicy(str, Enum):
    ERROR = "error"
    WARN = "warn"
    NOOP = "noop"


class InstructionFallbackConfig(BaseModel):
    """Configuration describing how to degrade when an instruction cannot load."""

    mode: InstructionFallbackPolicy = Field(default=InstructionFallbackPolicy.ERROR)
    placeholder: Optional[str] = Field(default=None, max_length=512)
    log_key: Optional[str] = Field(
        default=None, min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_\-]+$"
    )

    @model_validator(mode="after")
    def _validate_placeholder(self) -> "InstructionFallbackConfig":
        if self.mode in {InstructionFallbackPolicy.WARN, InstructionFallbackPolicy.NOOP}:
            if not self.placeholder:
                raise ValueError("placeholder is required when warn/noop fallback is used.")
        return self


class InstructionNodeRef(BaseModel):
    """Reference to an instruction asset by identifier/version."""

    instruction_id: str = Field(..., min_length=1, pattern=r"^[a-zA-Z0-9_\-./]+$")
    version: Optional[str] = Field(default=None, min_length=1)
    fallback: Optional[InstructionFallbackConfig] = None


class InstructionNode(BaseModel):
    """Instruction metadata derived from instruction stores."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    instruction_id: str = Field(..., min_length=1, pattern=r"^[a-zA-Z0-9_\-./]+$")
    source_uri: AnyUrl | FilePath | str
    format: Literal["md", "txt", "jinja", "yaml", "yml"]
    checksum: str = Field(..., min_length=32, max_length=64)
    locale: str = Field(default="en-US", min_length=2, max_length=16)
    version: str = Field(default="0.0.1", min_length=1, max_length=32)
    provider_key: str = Field(default="filesystem_default", min_length=1, max_length=64)
    fallback_policy: InstructionFallbackPolicy = Field(default=InstructionFallbackPolicy.ERROR)
    placeholder_template: Optional[str] = Field(default=None, max_length=512)
    pattern: Optional[str] = Field(
        default=None,
        description="Regex pattern for custom placeholder substitution (required group 'placeholder').",
    )


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
    fallback_policies: Set[str] = Field(default_factory=set)


class ExecutionLogEntry(BaseModel):
    """Structured JSONL log payload emitted by the executor.

    # AICODE-NOTE: Schema matches clarified logging format with timestamp, level,
    #              event_type, blueprint_id, step_id, asset_id, and metadata fields
    #              for structured querying and audit trails.
    """

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    event_type: Literal[
        "instruction_accessed",
        "instruction_loaded",
        "instruction_fallback",
        "adapter_resolved",
        "fallback_applied",
        "data_resolved",
        "memory_resolved",
        "size_warning",
        "error",
    ]
    blueprint_id: Optional[str] = Field(default=None, min_length=1)
    step_id: str = Field(..., min_length=1)
    asset_id: Optional[str] = Field(default=None, min_length=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    # Legacy fields for backward compatibility
    payload: Dict[str, Any] = Field(default_factory=dict)
    reference_ids: List[str] = Field(default_factory=list)


class FallbackEvent(BaseModel):
    """Structured representation of an instruction fallback that callers can inspect."""

    instruction_id: str = Field(..., min_length=1, pattern=r"^[a-zA-Z0-9_\-./]+$")
    mode: InstructionFallbackPolicy
    message: str = Field(..., min_length=1)
    placeholder_used: Optional[str] = Field(default=None, max_length=512)
    log_key: Optional[str] = Field(
        default=None, min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_\-]+$"
    )


class BlueprintSettings(BaseModel):
    """Blueprint-specific settings for paths and adapters."""

    instruction_root: Optional[str] = Field(
        default=None,
        description="Relative path to instructions directory (default: 'instructions' relative to blueprint file)",
    )
    adapter_defaults: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Default configuration for adapters (e.g., {'csv_loader': {'path': 'data/sources.csv'}})",
    )
    max_context_chars: Optional[int] = Field(
        default=None,
        ge=1024,
        description="Maximum characters allowed in rendered context (default: 16000)",
    )
    max_step_depth: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum depth of nested steps (default: 5)",
    )
    per_step_budget_chars: Optional[int] = Field(
        default=None,
        ge=512,
        description="Recommended character budget per step (default: 4000)",
    )


class ContextBlueprint(BaseModel):
    """
    Core blueprint describing prompt, instructions, data slots, and steps.

    # AICODE-NOTE: ContextBlueprint enforces uniqueness constraints eagerly so
    #              downstream builders can assume canonicalized structures.
    #              Settings are embedded in blueprint to avoid external configuration files.
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
    settings: BlueprintSettings = Field(
        default_factory=BlueprintSettings,
        description="Blueprint-specific settings for paths and adapters",
    )

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

    def render_instruction(
        self,
        instruction_id: str,
        *,
        settings: ContextEngineSettings | None = None,
        materializer: ContextMaterializer | None = None,
    ) -> str:
        """
        Render a specific instruction by ID from this blueprint.

        # AICODE-NOTE: This method provides convenient access to individual
        #              instructions without requiring external SDK functions.
        """
        from promptic.sdk.api import render_instruction

        return render_instruction(
            self, instruction_id=instruction_id, settings=settings, materializer=materializer
        )

    @staticmethod
    def _assert_unique(values: Iterable[str], label: str) -> None:
        seen: Set[str] = set()
        for value in values:
            if value in seen:
                raise ValueError(f"Duplicate {label} detected: '{value}'.")
            seen.add(value)


class RenderMetrics(BaseModel):
    """Token/validation statistics recorded by file-first renders."""

    tokens_before: int = Field(default=0, ge=0)
    tokens_after: int = Field(default=0, ge=0)
    reference_count: int = Field(default=0, ge=0)
    missing_paths: List[str] = Field(default_factory=list)


class MemoryChannel(BaseModel):
    """Memory/log destinations surfaced in file-first prompts."""

    location: str = Field(..., min_length=1)
    expected_format: str = Field(..., min_length=1)
    format_descriptor_path: Optional[str] = Field(default=None, min_length=1)
    retention_policy: Optional[str] = Field(default=None, max_length=512)
    usage_examples: List[str] = Field(default_factory=list, max_length=10)


class InstructionReference(BaseModel):
    """Represents a single referenced instruction file."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=80)
    summary: str = Field(..., min_length=1)
    reference_path: str = Field(..., min_length=1)
    detail_hint: str = Field(..., min_length=1)
    token_estimate: int = Field(default=0, ge=0)
    children: List["InstructionReference"] = Field(default_factory=list)


class PromptHierarchyBlueprint(BaseModel):
    """Top-level persona/goals plus reference tree for file-first renders."""

    model_config = ConfigDict(str_strip_whitespace=True)

    blueprint_id: str = Field(..., min_length=1)
    persona: str = Field(..., min_length=1)
    objectives: List[str] = Field(default_factory=list, max_length=8)
    steps: List[InstructionReference] = Field(default_factory=list)
    memory_channels: List[MemoryChannel] = Field(default_factory=list)
    metrics: Optional[RenderMetrics] = None


InstructionReference.model_rebuild()


__all__ = [
    "AdapterRegistration",
    "BlueprintSettings",
    "BlueprintStep",
    "Condition",
    "ContextBlueprint",
    "DataSlot",
    "ExecutionLogEntry",
    "FallbackEvent",
    "InstructionFallbackConfig",
    "InstructionFallbackPolicy",
    "InstructionNode",
    "InstructionNodeRef",
    "InstructionReference",
    "MemoryChannel",
    "MemorySlot",
    "PromptHierarchyBlueprint",
    "RenderMetrics",
]
