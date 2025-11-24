from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml
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
    data_defaults: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional default configuration payloads per data adapter key.",
    )
    memory_defaults: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional default configuration payloads per memory provider key.",
    )
    max_retries: int = Field(
        default=1,
        ge=0,
        description="Number of retry attempts when adapters raise recoverable errors.",
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
    log_level: str = Field(
        default="INFO",
        description="Logging level for versioning operations (DEBUG, INFO, WARNING, ERROR).",
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

    @classmethod
    def from_yaml(cls, yaml_path: Path | str) -> ContextEngineSettings:
        """
        Load settings from a YAML configuration file.

        # AICODE-NOTE: This method allows loading settings from YAML files instead of
        programmatically setting them. Relative paths in the YAML are resolved relative to
        the YAML file's directory.

        Args:
            yaml_path: Path to the YAML configuration file

        Returns:
            ContextEngineSettings instance loaded from the YAML file

        Example:
            ```yaml
            blueprint_root: blueprints
            instruction_root: instructions
            log_root: logs
            adapter_registry:
              data_defaults:
                csv_loader:
                  path: data/sources.csv
            ```
        """
        yaml_path = Path(yaml_path).resolve()
        if not yaml_path.exists():
            raise FileNotFoundError(f"Settings YAML file not found: {yaml_path}")

        yaml_dir = yaml_path.parent

        with yaml_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        # Convert string paths to Path objects and resolve relative paths
        for path_field in ("blueprint_root", "instruction_root", "log_root"):
            if path_field in data:
                path_value = data[path_field]
                if isinstance(path_value, str):
                    path_obj = Path(path_value)
                    if not path_obj.is_absolute():
                        path_obj = (yaml_dir / path_obj).resolve()
                    data[path_field] = path_obj

        # Resolve relative paths in adapter registry data_defaults
        if "adapter_registry" in data and isinstance(data["adapter_registry"], dict):
            adapter_registry = data["adapter_registry"]
            if "data_defaults" in adapter_registry:
                for adapter_key, adapter_config in adapter_registry["data_defaults"].items():
                    if isinstance(adapter_config, dict) and "path" in adapter_config:
                        path_value = adapter_config["path"]
                        if isinstance(path_value, str):
                            path_obj = Path(path_value)
                            if not path_obj.is_absolute():
                                path_obj = (yaml_dir / path_obj).resolve()
                            adapter_config["path"] = str(path_obj)

        return cls(**data)
