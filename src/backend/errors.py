from dataclasses import dataclass

from fastapi import Request
from fastapi.exceptions import RequestValidationError

from src.backend.response import fail


@dataclass
class ApiError(Exception):
    code: str
    message: str
    status_code: int = 400
    details: dict[str, object] | None = None


async def api_error_handler(request: Request, exc: ApiError):
    return fail(
        request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )


async def validation_error_handler(request: Request, exc: RequestValidationError):
    return fail(
        request,
        status_code=400,
        code="INVALID_ARGUMENT",
        message="Request validation failed.",
        details={"errors": exc.errors()},
    )


async def unhandled_error_handler(request: Request, exc: Exception):
    return fail(
        request,
        status_code=500,
        code="INTERNAL",
        message="Internal server error.",
        details={},
    )
