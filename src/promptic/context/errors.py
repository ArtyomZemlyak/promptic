from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, Iterable, Optional, TypeVar


class PrompticError(Exception):
    """Base exception for the Promptic SDK."""


class InstructionNotFoundError(PrompticError):
    """Raised when an instruction asset cannot be resolved."""

    def __init__(self, instruction_id: str) -> None:
        super().__init__(f"Instruction '{instruction_id}' could not be located.")
        self.instruction_id = instruction_id


class BlueprintValidationError(PrompticError):
    """Represents structural or logical blueprint problems."""


class BlueprintLoadError(PrompticError):
    """Raised when a blueprint file cannot be located or parsed."""


class AdapterRegistrationError(PrompticError):
    """Raised when adapter registration metadata is invalid."""


class AdapterNotRegisteredError(PrompticError):
    """Raised when an adapter key is not present in the registry."""

    def __init__(self, key: str, adapter_type: str) -> None:
        message = f"No {adapter_type} adapter registered for key '{key}'."
        super().__init__(message)
        self.key = key
        self.adapter_type = adapter_type


class AdapterExecutionError(PrompticError):
    """Encapsulates runtime failures raised by adapters."""


class AdapterRetryError(AdapterExecutionError):
    """Raised when an adapter exhausts its retry budget."""

    def __init__(self, key: str, attempts: int, last_error: AdapterExecutionError) -> None:
        super().__init__(f"Adapter '{key}' failed after {attempts} attempts: {last_error}")
        self.key = key
        self.attempts = attempts
        self.last_error = last_error


class ContextMaterializationError(PrompticError):
    """Raised when blueprint data/memory/materialization cannot be fulfilled."""


class LoggingError(PrompticError):
    """Raised when the event logger fails to write artifacts."""


T = TypeVar("T")


@dataclass
class OperationResult(Generic[T]):
    """
    Small helper representing success/failure with optional warnings.

    # AICODE-NOTE: Terse result objects keep future CLI/SDK layers agnostic of the
    #              underlying exception hierarchy while still surfacing warnings.
    """

    ok: bool
    value: Optional[T] = None
    error: Optional[PrompticError] = None
    warnings: list[str] = field(default_factory=list)

    @classmethod
    def success(cls, value: T, *, warnings: Iterable[str] | None = None) -> "OperationResult[T]":
        return cls(ok=True, value=value, warnings=list(warnings or []))

    @classmethod
    def failure(
        cls, error: PrompticError, *, warnings: Iterable[str] | None = None
    ) -> "OperationResult[T]":
        return cls(ok=False, error=error, warnings=list(warnings or []))

    def unwrap(self) -> T:
        if not self.ok or self.value is None:
            raise self.error or PrompticError("Operation did not produce a value.")
        return self.value


__all__ = [
    "AdapterExecutionError",
    "AdapterNotRegisteredError",
    "AdapterRegistrationError",
    "AdapterRetryError",
    "BlueprintLoadError",
    "BlueprintValidationError",
    "ContextMaterializationError",
    "InstructionNotFoundError",
    "LoggingError",
    "OperationResult",
    "PrompticError",
]
