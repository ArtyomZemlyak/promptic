from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, Iterable, Mapping, Optional, TypeVar


class PrompticError(Exception):
    """Base exception for the Promptic SDK."""

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        hint: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> None:
        text = message or self.__class__.__name__
        super().__init__(text)
        self.message = text
        self.code = code or self.__class__.__name__
        self.hint = hint
        self.context = dict(context or {})


class InstructionNotFoundError(PrompticError):
    """Raised when an instruction asset cannot be resolved."""

    def __init__(self, instruction_id: str) -> None:
        super().__init__(
            f"Instruction '{instruction_id}' could not be located.",
            code="INSTRUCTION_NOT_FOUND",
            hint="Ensure the instruction asset exists under the configured instruction_root.",
            context={"instruction_id": instruction_id},
        )
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
        super().__init__(
            message,
            code="ADAPTER_NOT_REGISTERED",
            hint="Register the adapter via promptic.sdk.adapters or update the slot configuration.",
            context={"adapter_key": key, "adapter_type": adapter_type},
        )
        self.key = key
        self.adapter_type = adapter_type


# Alias for consistency with spec terminology
AdapterNotFoundError = AdapterNotRegisteredError


class ContextSizeExceededError(PrompticError):
    """Raised when context size limits are exceeded."""

    def __init__(self, step_id: str, actual_size: int, limit: int) -> None:
        message = f"Step '{step_id}' exceeded context size limit ({actual_size} > {limit})."
        super().__init__(
            message,
            code="CONTEXT_SIZE_EXCEEDED",
            hint="Reduce step content or increase size_budget.per_step_budget_chars in settings.",
            context={"step_id": step_id, "actual_size": actual_size, "limit": limit},
        )
        self.step_id = step_id
        self.actual_size = actual_size
        self.limit = limit


class AdapterUnavailableError(PrompticError):
    """Raised when an adapter is unavailable after retries."""

    def __init__(self, key: str, adapter_type: str, reason: str) -> None:
        message = f"{adapter_type} adapter '{key}' is unavailable: {reason}."
        super().__init__(
            message,
            code="ADAPTER_UNAVAILABLE",
            hint="Check adapter configuration and network connectivity, or configure fallback policy.",
            context={"adapter_key": key, "adapter_type": adapter_type, "reason": reason},
        )
        self.key = key
        self.adapter_type = adapter_type
        self.reason = reason


class AdapterExecutionError(PrompticError):
    """Encapsulates runtime failures raised by adapters."""


class AdapterRetryError(AdapterExecutionError):
    """Raised when an adapter exhausts its retry budget."""

    def __init__(self, key: str, attempts: int, last_error: AdapterExecutionError) -> None:
        super().__init__(
            f"Adapter '{key}' failed after {attempts} attempts: {last_error}",
            code="ADAPTER_RETRY_EXHAUSTED",
            hint="Retry the adapter by increasing adapter_registry.max_retries or inspect adapter logs for permanent failures.",
            context={"adapter_key": key, "attempts": attempts},
        )
        self.key = key
        self.attempts = attempts
        self.last_error = last_error


class ContextMaterializationError(PrompticError):
    """Raised when blueprint data/memory/materialization cannot be fulfilled."""


class LoggingError(PrompticError):
    """Raised when the event logger fails to write artifacts."""


class TemplateRenderError(PrompticError):
    """Domain exception raised when template rendering fails."""

    def __init__(
        self,
        instruction_id: str,
        format: str,
        error_type: str,  # Literal["missing_placeholder", "syntax_error", "type_mismatch", "circular_reference"]
        message: str,
        line_number: int | None = None,
        placeholder: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> None:
        error_context = {
            "instruction_id": instruction_id,
            "format": format,
            "error_type": error_type,
            "line_number": line_number,
            "placeholder": placeholder,
        }
        if context:
            error_context.update(context)

        super().__init__(
            message,
            code="TEMPLATE_RENDER_ERROR",
            hint="Check the instruction content matches the expected template syntax and available data.",
            context=error_context,
        )
        self.instruction_id = instruction_id
        self.format = format
        self.error_type = error_type
        self.line_number = line_number
        self.placeholder = placeholder


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


@dataclass(frozen=True)
class ErrorDetail:
    code: str
    message: str
    hint: str | None = None
    context: dict[str, Any] = field(default_factory=dict)


def describe_error(error: PrompticError) -> ErrorDetail:
    """Return a structured description suitable for SDK surfaces."""

    hint = error.hint or _DEFAULT_HINTS.get(type(error))
    context = dict(error.context)
    if isinstance(error, AdapterRetryError):
        context.setdefault("last_error", str(error.last_error))
    return ErrorDetail(
        code=error.code,
        message=str(error),
        hint=hint,
        context=context,
    )


__all__ = [
    "AdapterExecutionError",
    "AdapterNotFoundError",
    "AdapterNotRegisteredError",
    "AdapterRegistrationError",
    "AdapterRetryError",
    "AdapterUnavailableError",
    "BlueprintLoadError",
    "BlueprintValidationError",
    "ContextMaterializationError",
    "ContextSizeExceededError",
    "ErrorDetail",
    "InstructionNotFoundError",
    "LoggingError",
    "OperationResult",
    "PrompticError",
    "describe_error",
]


_DEFAULT_HINTS: dict[type[PrompticError], str] = {
    InstructionNotFoundError: "Verify the blueprint references existing instruction files.",
    BlueprintValidationError: "Run BlueprintValidator to inspect structural issues.",
    BlueprintLoadError: "Ensure the blueprint file exists and is valid YAML/JSON.",
    AdapterNotRegisteredError: "Register the adapter or update the slot's adapter_key.",
    AdapterNotFoundError: "Register the adapter or update the slot's adapter_key.",
    AdapterRetryError: "Retry the adapter (increase adapter_registry.max_retries) or inspect adapter logs for permanent failures.",
    AdapterUnavailableError: "Check adapter configuration and network connectivity, or configure fallback policy.",
    ContextSizeExceededError: "Reduce step content or increase size_budget.per_step_budget_chars in settings.",
    ContextMaterializationError: "Check adapter outputs and overrides supplied to the SDK.",
    LoggingError: "Ensure the log directory is writable.",
}
