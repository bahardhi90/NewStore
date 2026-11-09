"""Custom exception handler: every error is returned as {detail, code, errors}."""

import logging
from typing import Any

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.fields import get_error_detail
from rest_framework.response import Response
from rest_framework.views import exception_handler

from . import messages as msg

logger = logging.getLogger(__name__)


class StoreError(exceptions.APIException):
    """Business error with a stable code, a Persian message and optional field errors."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = msg.VALIDATION_ERROR
    default_code = "store_error"

    def __init__(
        self,
        detail: str,
        code: str,
        *,
        status_code: int = 400,
        errors: dict[str, list[str]] | None = None,
    ) -> None:
        super().__init__(detail=detail, code=code)
        self.status_code = status_code
        self.error_code = code
        self.field_errors = errors or {}


def _flatten(data: Any) -> dict[str, list[str]]:
    """Turn DRF validation data into {field: [messages]}."""
    if isinstance(data, list):
        return {"non_field_errors": [str(item) for item in _messages(data)]}
    if isinstance(data, dict):
        out: dict[str, list[str]] = {}
        for key, value in data.items():
            out[str(key)] = [str(item) for item in _messages(value)]
        return out
    return {"non_field_errors": [str(data)]}


def _messages(value: Any) -> list[str]:
    if isinstance(value, dict):
        result: list[str] = []
        for sub in value.values():
            result.extend(_messages(sub))
        return result
    if isinstance(value, (list, tuple)):
        result = []
        for sub in value:
            result.extend(_messages(sub))
        return result
    return [str(value)]


_STATUS_DEFAULTS: dict[int, tuple[str, str]] = {
    401: ("not_authenticated", msg.NOT_AUTHENTICATED),
    403: ("permission_denied", msg.PERMISSION_DENIED),
    404: ("not_found", msg.NOT_FOUND),
    405: ("method_not_allowed", msg.METHOD_NOT_ALLOWED),
    415: ("unsupported_media_type", msg.UNSUPPORTED_MEDIA),
}


def custom_exception_handler(exc: Exception, context: dict) -> Response | None:
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, DjangoPermissionDenied):
        exc = exceptions.PermissionDenied()
    elif isinstance(exc, DjangoValidationError):
        exc = exceptions.ValidationError(get_error_detail(exc))

    response = exception_handler(exc, context)

    if response is None:
        logger.exception("Unhandled API error", exc_info=exc)
        return Response(
            {"detail": msg.SERVER_ERROR, "code": "server_error", "errors": {}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if isinstance(exc, StoreError):
        payload = {"detail": str(exc.detail), "code": exc.error_code, "errors": exc.field_errors}
    elif isinstance(exc, exceptions.ValidationError):
        payload = {"detail": msg.VALIDATION_ERROR, "code": "validation_error", "errors": _flatten(response.data)}
    elif isinstance(exc, exceptions.Throttled):
        wait = int(exc.wait or 60)
        payload = {
            "detail": msg.THROTTLED.format(seconds=wait),
            "code": "throttled",
            "errors": {"retry_after": [str(wait)]},
        }
    elif isinstance(exc, exceptions.ParseError):
        payload = {"detail": msg.PARSE_ERROR, "code": "parse_error", "errors": {}}
    else:
        code, detail = _STATUS_DEFAULTS.get(response.status_code, ("error", str(getattr(exc, "detail", exc))))
        payload = {"detail": detail, "code": code, "errors": {}}

    response.data = payload
    return response
