from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

from pydantic import ValidationError

from promptic.blueprints.models import ContextBlueprint
from promptic.blueprints.serialization import load_blueprint
from promptic.context.errors import BlueprintLoadError, BlueprintValidationError, OperationResult
from promptic.pipeline.validation import BlueprintValidator
from promptic.settings.base import ContextEngineSettings


class BlueprintBuilder:
    """Loads and validates blueprints stored on disk."""

    def __init__(
        self,
        *,
        settings: ContextEngineSettings,
        validator: BlueprintValidator,
    ) -> None:
        self.settings = settings
        self._validator = validator

    def list_blueprints(self) -> Sequence[str]:
        root = self.settings.blueprint_root.expanduser()
        if not root.exists():
            return tuple()
        results: set[str] = set()
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in {".yaml", ".yml", ".json"}:
                relative = path.relative_to(root)
                results.add(relative.with_suffix("").as_posix())
        return tuple(sorted(results))

    def load(self, blueprint_id: str) -> OperationResult[ContextBlueprint]:
        try:
            path = self._resolve_path(blueprint_id)
        except FileNotFoundError as exc:
            return OperationResult.failure(
                BlueprintLoadError(f"Blueprint '{blueprint_id}' not found."),
            )
        return self.load_from_path(path)

    def load_from_path(self, path: Path | str) -> OperationResult[ContextBlueprint]:
        target = Path(path)
        if not target.exists():
            return OperationResult.failure(
                BlueprintLoadError(f"Blueprint file '{target}' does not exist."),
            )
        try:
            blueprint = load_blueprint(target)
        except ValidationError as exc:
            return OperationResult.failure(BlueprintValidationError(str(exc)))
        except Exception as exc:  # pragma: no cover - yaml edge cases
            return OperationResult.failure(BlueprintLoadError(str(exc)))
        validation = self._validator.validate(blueprint)
        if not validation.ok:
            error = validation.error or BlueprintValidationError("Blueprint validation failed.")
            return OperationResult.failure(error, warnings=validation.warnings)
        validated = validation.unwrap()
        return OperationResult.success(validated, warnings=validation.warnings)

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
