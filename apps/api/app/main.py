from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.api.v1.api import api_router
from app.core.settings import settings


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield


def create_app() -> FastAPI:
    application = FastAPI(title="ShipSense API", lifespan=lifespan)
    application.include_router(api_router, prefix=settings.API_V1_STR)
    return application


app = create_app()
