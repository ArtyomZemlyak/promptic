from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AdapterRegistrySettings(BaseModel):
    """Configuration for auto-loading adapter modules and entry points."""

    module_paths: List[str] = Field(
        default_factory=list,
        description="Import paths (e.g., promptic.adapters.data.filesystem) auto-imported at startup.",
    )
    entry_point_group: str = Field(
        default="promptic.adapters",
        description="Entry-point group for discovering third-party adapters.",
    )
    refresh_on_startup: bool = Field(
        default=True,
        description="Whether to rebuild the adapter registry cache each time settings load.",
    )


class SizeBudgetSettings(BaseModel):
    """Defines context-size guardrails and blueprint limits."""

    max_context_chars: int = Field(
        default=16000,
        ge=1024,
        description="Maximum characters allowed in a rendered context payload.",
    )
    max_step_depth: int = Field(
        default=5,
        ge=1,
        description="Maximum depth of nested blueprint steps before validation fails.",
    )
    per_step_budget_chars: int = Field(
        default=4000,
        ge=512,
        description="Recommended character budget per pipeline step.",
    )


class ContextEngineSettings(BaseSettings):
    """
    Shared configuration for the Context Engineering library.

    # AICODE-NOTE: These defaults prioritize local development (relative paths, eager discovery).
    Downstream projects should override via environment variables or `.env` files.
    """

    model_config = SettingsConfigDict(env_prefix="PROMPTIC_", env_file=".env", extra="ignore")

    blueprint_root: Path = Field(
        default_factory=lambda: Path("blueprints"),
        description="Location where blueprint YAML/JSON definitions are stored.",
    )
    instruction_root: Path = Field(
        default_factory=lambda: Path("instructions"),
        description="Filesystem location of instruction assets (markdown, templates, etc.).",
    )
    log_root: Path = Field(
        default_factory=lambda: Path("logs"),
        description="Directory for execution/event logs when running pipelines.",
    )
    adapter_registry: AdapterRegistrySettings = Field(
        default_factory=AdapterRegistrySettings,
        description="Controls adapter discovery/registration behavior.",
    )
    size_budget: SizeBudgetSettings = Field(
        default_factory=SizeBudgetSettings,
        description="Guardrails for preview/execution text budgets and nesting depth.",
    )

    def ensure_directories(self) -> None:
        """Create directories that must exist before interacting with the filesystem."""

        for path in (self.blueprint_root, self.instruction_root, self.log_root):
            resolved = path.expanduser()
            resolved.mkdir(parents=True, exist_ok=True)

    def resolved_instruction_root(self) -> Path:
        """Return an absolute path to the instruction root, ensuring it exists."""

        root = self.instruction_root.expanduser()
        root.mkdir(parents=True, exist_ok=True)
        return root
