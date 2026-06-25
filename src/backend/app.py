from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from src.backend.api.routes import api_router, ws_router
from src.backend.config import Settings, get_settings
from src.backend.errors import (
    ApiError,
    api_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from src.backend.response import new_request_id
from src.backend.services.board_program_runner import ProgramRunner
from src.backend.services.camera_service import CameraBackend
from src.backend.services.container import create_services


def create_app(
    settings: Settings | None = None,
    program_runner: ProgramRunner | None = None,
    camera_backend: CameraBackend | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(
        title="AtlasSmartArm API",
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.state.services = create_services(settings, program_runner, camera_backend)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request.state.request_id = request.headers.get("X-Request-ID", new_request_id())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
    app.include_router(api_router)
    app.include_router(ws_router)
    return app


app = create_app()
