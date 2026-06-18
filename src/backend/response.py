from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse


def new_request_id() -> str:
    return f"req_{uuid4().hex[:16]}"


def request_id_from(request: Request) -> str:
    return getattr(request.state, "request_id", new_request_id())


def ok(request: Request, data: object, status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "request_id": request_id_from(request),
            "success": True,
            "data": data,
            "error": None,
        },
    )


def fail(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, object] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "request_id": request_id_from(request),
            "success": False,
            "data": None,
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            },
        },
    )
