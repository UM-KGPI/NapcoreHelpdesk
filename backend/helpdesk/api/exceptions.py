from __future__ import annotations

from uuid import uuid4

from rest_framework import status
from rest_framework.views import exception_handler as drf_exception_handler


def _request_id(request) -> str:
    # Generate a fallback ID when requests are missing X-Request-Id.
    if request is None:
        return f"req-{uuid4().hex[:12]}"
    return request.headers.get("X-Request-Id") or f"req-{uuid4().hex[:12]}"


def _code_from_status(status_code: int) -> str:
    # Map HTTP status to stable error codes expected by API consumers.
    mapping = {
        status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
        status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
        status.HTTP_403_FORBIDDEN: "FORBIDDEN",
        status.HTTP_404_NOT_FOUND: "NOT_FOUND",
        status.HTTP_405_METHOD_NOT_ALLOWED: "METHOD_NOT_ALLOWED",
        status.HTTP_409_CONFLICT: "CONFLICT",
        status.HTTP_422_UNPROCESSABLE_ENTITY: "UNPROCESSABLE_ENTITY",
    }
    return mapping.get(status_code, "INTERNAL_ERROR")


def custom_exception_handler(exc, context):
    # Start with DRF default handling and then reshape into OpenAPI ErrorResponse.
    response = drf_exception_handler(exc, context)
    if response is None:
        return response

    request = context.get("request")
    request_id = _request_id(request)
    code = _code_from_status(response.status_code)

    message = "Request failed."
    # Prefer DRF's explicit detail when available; otherwise provide normalized defaults.
    detail = response.data.get("detail") if isinstance(response.data, dict) else None
    if isinstance(detail, str) and detail.strip():
        message = detail
    elif response.status_code == status.HTTP_400_BAD_REQUEST:
        message = "Invalid request payload."
    elif response.status_code == status.HTTP_401_UNAUTHORIZED:
        message = "Authentication credentials were missing or invalid."
    elif response.status_code == status.HTTP_403_FORBIDDEN:
        message = "You do not have permission to perform this action."

    response.data = {
        "error": {
            "code": code,
            "message": message,
            "requestId": request_id,
        }
    }
    return response
