"""HTTP error envelope used by the public API."""

from collections.abc import Mapping
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Any = None

    model_config = ConfigDict(extra="forbid")


class ErrorEnvelope(BaseModel):
    error: ErrorBody


def error_response(
    *,
    code: str,
    message: str,
    details: Any = None,
    status_code: int,
) -> JSONResponse:
    body = ErrorEnvelope(error=ErrorBody(code=code, message=message, details=details))
    return JSONResponse(status_code=status_code, content=body.model_dump())


async def http_exception_handler(
    _: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    code = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
    message = str(exc.detail)
    details: Any = None
    if isinstance(exc.detail, Mapping):
        message = str(exc.detail.get("message", message))
        details = exc.detail.get("details")
        code = str(exc.detail.get("code", code))
    return error_response(
        code=code,
        message=message,
        details=details,
        status_code=exc.status_code,
    )


async def validation_exception_handler(
    _: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return error_response(
        code="VALIDATION_ERROR",
        message="Request validation failed",
        details=exc.errors(),
        status_code=422,
    )
