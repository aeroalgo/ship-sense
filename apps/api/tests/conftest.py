"""Shared fixtures for API tests."""

from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.core.database.session import engine
from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def database_schema() -> AsyncIterator[None]:
    async with engine.begin() as connection:
        await connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS access_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts DATETIME NOT NULL,
                    person_id TEXT,
                    session_id TEXT,
                    action TEXT NOT NULL,
                    source_ip TEXT,
                    details TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
        )
    yield
    async with engine.begin() as connection:
        await connection.execute(text("DELETE FROM access_audit"))


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client
