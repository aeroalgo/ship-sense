from __future__ import annotations

import asyncio
import os
import subprocess
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.edge.semantic.engine import SemanticEngine
from apps.edge.storage.events_repo import EventsRepo
from apps.edge.storage.samples_repo import SamplesRepo
from apps.edge.storage.writer import WriterService


def migration_database_url(database_url: str) -> str:
    return database_url.replace("+asyncpg", "+psycopg")


async def main() -> None:
    database_url = os.environ.get(
        "DATABASE_URL", "postgresql+asyncpg://shipsense:shipsense@db:5432/shipsense"
    )
    migration_url = os.environ.get(
        "DATABASE_MIGRATION_URL", migration_database_url(database_url)
    )
    subprocess.run(
        ["alembic", "upgrade", "head"],
        check=True,
        env={**os.environ, "DATABASE_URL": migration_url},
    )
    engine = create_async_engine(database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    semantic = SemanticEngine()
    pack_dir = Path(os.environ.get("SHIPSSENSE_PACK_DIR", "/app/ship-pack/makarov"))
    if pack_dir.exists():
        semantic.load(pack_dir)

    async with session_factory() as session:
        service = WriterService(
            session=session,
            samples_repo=SamplesRepo(session),
            events_repo=EventsRepo(session),
            quarantined_tags=lambda: semantic.quarantined_tags,
        )
        await service.run_tcp(
            os.environ.get("SHIPSSENSE_WRITER_HOST", "0.0.0.0"),
            int(os.environ.get("SHIPSSENSE_WRITER_PORT", "9009")),
        )
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
