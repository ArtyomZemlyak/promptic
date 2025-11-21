from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

from promptic.context.errors import BlueprintLoadError, OperationResult
from promptic.context.nodes.errors import (
    NodeNetworkDepthExceededError,
    NodeNetworkValidationError,
    NodeReferenceNotFoundError,
    NodeResourceLimitExceededError,
)
from promptic.context.nodes.models import NetworkConfig, NodeNetwork
from promptic.pipeline.network.builder import NodeNetworkBuilder
from promptic.settings.base import ContextEngineSettings


class BlueprintBuilder:
    """Loads and validates blueprints stored on disk using unified node network architecture.

    # AICODE-NOTE: This class has been migrated to use NodeNetworkBuilder instead of
    #              ContextBlueprint. It now loads blueprints as NodeNetwork instances
    #              using the unified context node architecture.
    """

    def __init__(
        self,
        *,
        settings: ContextEngineSettings,
        validator: None = None,  # Validator no longer needed, validation handled by NodeNetworkBuilder
    ) -> None:
        self.settings = settings
        self._network_builder = NodeNetworkBuilder()

    def list_blueprints(self) -> Sequence[str]:
        root = self.settings.blueprint_root.expanduser()
        if not root.exists():
            return tuple()
        results: set[str] = set()
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in {
                ".yaml",
                ".yml",
                ".json",
                ".md",
                ".jinja",
                ".jinja2",
            }:
                relative = path.relative_to(root)
                results.add(relative.with_suffix("").as_posix())
        return tuple(sorted(results))

    def load(self, blueprint_id: str) -> OperationResult[NodeNetwork]:
        try:
            path = self._resolve_path(blueprint_id)
        except FileNotFoundError as exc:
            return OperationResult.failure(
                BlueprintLoadError(f"Blueprint '{blueprint_id}' not found."),
            )
        return self.load_from_path(path)

    def load_from_path(
        self, path: Path | str, config: NetworkConfig | None = None
    ) -> OperationResult[NodeNetwork]:
        target = Path(path)
        if not target.exists():
            return OperationResult.failure(
                BlueprintLoadError(f"Blueprint file '{target}' does not exist."),
            )
        try:
            network = self._network_builder.build_network(target, config)
            return OperationResult.success(network)
        except (
            NodeNetworkValidationError,
            NodeNetworkDepthExceededError,
            NodeReferenceNotFoundError,
            NodeResourceLimitExceededError,
        ) as exc:
            return OperationResult.failure(BlueprintLoadError(str(exc)))
        except Exception as exc:  # pragma: no cover - edge cases
            return OperationResult.failure(BlueprintLoadError(str(exc)))

    def _resolve_path(self, blueprint_id: str) -> Path:
        root = self.settings.blueprint_root.expanduser()
        explicit = root / blueprint_id
        candidates = list(self._candidate_paths(explicit))
        for candidate in candidates:
            if candidate.exists():
                return candidate
        raise FileNotFoundError(blueprint_id)

    @staticmethod
    def _candidate_paths(explicit: Path) -> Iterable[Path]:
        if explicit.suffix:
            yield explicit
            return
        for suffix in (".yaml", ".yml", ".json"):
            yield explicit.with_suffix(suffix)


__all__ = ["BlueprintBuilder"]
