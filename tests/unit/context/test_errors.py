from __future__ import annotations

from promptic.context.errors import (
    AdapterExecutionError,
    AdapterNotRegisteredError,
    AdapterRetryError,
    ErrorDetail,
    InstructionNotFoundError,
    PrompticError,
    describe_error,
)


def test_describe_error_includes_hint_and_context() -> None:
    error = InstructionNotFoundError("missing.md")

    detail = describe_error(error)

    assert isinstance(detail, ErrorDetail)
    assert detail.code == "INSTRUCTION_NOT_FOUND"
    assert "missing.md" in detail.message
    assert detail.context["instruction_id"] == "missing.md"
    assert "instruction" in (detail.hint or "")


def test_describe_error_handles_registry_failures() -> None:
    error = AdapterNotRegisteredError("csv_loader", "data")

    detail = describe_error(error)

    assert detail.code == "ADAPTER_NOT_REGISTERED"
    assert detail.context["adapter_key"] == "csv_loader"
    assert detail.context["adapter_type"] == "data"
    assert "register" in (detail.hint or "").lower()


def test_describe_error_falls_back_to_generic() -> None:
    class CustomError(PrompticError):
        pass

    detail = describe_error(CustomError("boom"))

    assert detail.code == "CustomError"
    assert detail.message == "boom"
    assert detail.hint is None
    assert detail.context == {}


def test_describe_error_surfaces_retry_metadata() -> None:
    last_error = AdapterExecutionError("timeout")
    error = AdapterRetryError("csv_loader", 3, last_error)

    detail = describe_error(error)

    assert detail.code == "ADAPTER_RETRY_EXHAUSTED"
    assert detail.context["adapter_key"] == "csv_loader"
    assert detail.context["attempts"] == 3
    assert "retry" in (detail.hint or "").lower()
