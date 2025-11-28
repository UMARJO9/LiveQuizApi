from typing import Any, Iterable, Optional

from rest_framework import status
from rest_framework.response import Response


def _extract_message(data: Any, success: bool) -> str:
    """
    Try to pull a readable message out of DRF payloads (including validation errors).
    Falls back to generic success/error labels.
    """
    if isinstance(data, dict):
        for key in ("message", "detail", "error"):
            if key in data:
                value = data[key]
                if isinstance(value, str):
                    return value
                if isinstance(value, Iterable):
                    items = list(value)
                    if items and isinstance(items[0], str):
                        return items[0]
        if not data:
            return "Success" if success else "Error"

    if isinstance(data, list) and data and isinstance(data[0], str):
        return data[0]

    return "Success" if success else "Error"


def build_api_response(
    data: Any = None,
    *,
    status_code: int = status.HTTP_200_OK,
    message: Optional[str] = None,
    success: Optional[bool] = None,
) -> dict:
    success = bool(success) if success is not None else status.is_success(status_code)
    message = message or _extract_message(data, success)

    return {
        "success": success,
        "code": status_code,
        "message": message,
        "result": data,
    }


class StandardResponseMixin:
    """
    Wrap every DRF Response in a unified envelope:
    {success: bool, code: int, message: str, result: data}
    """

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)

        if isinstance(response, Response) and not getattr(response, "_already_standardized", False):
            data = response.data
            message_override = None
            # If view already returned only a message field, treat it as top-level message, not result payload.
            if isinstance(data, dict) and set(data.keys()) == {"message"}:
                message_override = data.get("message")
                data = None

            payload = build_api_response(
                data=data,
                status_code=response.status_code,
                success=status.is_success(response.status_code),
                message=message_override,
            )
            response.data = payload
            response._already_standardized = True

        return response
