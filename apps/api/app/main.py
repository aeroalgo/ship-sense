from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.api import api_router
from app.core.exceptions import http_exception_handler, validation_exception_handler
from app.core.middleware import RateLimitMiddleware, RequestContextMiddleware
from app.core.settings import settings
from app.stream.service import FanoutBridge


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    application.state.stream_bridge = FanoutBridge()
    yield
    application.state.stream_bridge = None


def create_app() -> FastAPI:
    application = FastAPI(
        title="ShipSense API",
        version="1.0.0",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )
    application.add_middleware(RequestContextMiddleware)
    application.add_middleware(RateLimitMiddleware)
    application.add_exception_handler(StarletteHTTPException, http_exception_handler)
    application.add_exception_handler(RequestValidationError, validation_exception_handler)
    application.include_router(api_router, prefix=settings.API_V1_STR)
    return application


app = create_app()
