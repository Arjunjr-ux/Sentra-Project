"""Wrap DRF's exception handler so every error response carries a stable
``detail`` string (SENTRA_BUILD_SPEC.md §4), without discarding the per-field
validation errors DRF already produced."""

from __future__ import annotations

from rest_framework.views import exception_handler as drf_exception_handler


def _first_message(value) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key, nested in value.items():
            msg = _first_message(nested)
            if msg:
                return msg if key in {"detail", "non_field_errors"} else f"{key}: {msg}"
        return None
    if isinstance(value, (list, tuple)):
        for item in value:
            msg = _first_message(item)
            if msg:
                return msg
        return None
    return None


def sentra_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    data = response.data
    if isinstance(data, dict):
        if "detail" not in data:
            data["detail"] = _first_message(data) or "Request failed."
    elif isinstance(data, list):
        response.data = {
            "detail": _first_message(data) or "Request failed.",
            "errors": data,
        }
    return response
