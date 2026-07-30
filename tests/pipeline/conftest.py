"""Pipeline DB E2E fixtures (T-002 s02).

Session-scoped TimescaleDB via testcontainers, alembic upgrade head,
async engine/session, autouse truncate, writer_tcp harness on ephemeral port.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
from collections.abc import AsyncIterator, Iterator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

from apps.edge.storage.events_repo import EventsRepo
from apps.edge.storage.samples_repo import SamplesRepo
from apps.edge.storage.writer import WriterService


def _docker_available() -> bool:
    """Return True if docker CLI and daemon are reachable."""
    if shutil.which("docker") is None:
        return False
    try:
        subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
            timeout=5,
        )
        return True
    except Exception:
        return False


def _skip_if_no_docker() -> None:
    if not _docker_available():
        pytest.skip("Docker required for pipeline DB E2E")


@pytest.fixture(scope="session")
def timescale_url() -> Iterator[str]:
    """Session-scoped TimescaleDB container. Returns asyncpg URL.

    Uses image timescale/timescaledb:2.14.2-pg16 (matches compose).
    Env: POSTGRES_USER/PASSWORD/DB=shipsense.
    Waits for pg_isready via container health.
    """
    _skip_if_no_docker()

    container = (
        DockerContainer("timescale/timescaledb:2.14.2-pg16")
        .with_env("POSTGRES_USER", "shipsense")
        .with_env("POSTGRES_PASSWORD", "shipsense")
        .with_env("POSTGRES_DB", "shipsense")
        .with_exposed_ports(5432)
        # Match compose shm_size to prevent postgres OOM/crash on init.
        # DockerContainer has no with_shm_size; pass via with_kwargs to docker run.
        .with_kwargs(shm_size=512 * 1024 * 1024)  # 512MB, match compose shm_size
    )
    container.start()

    # Wait for readiness. The log message "database system is ready to accept connections"
    # can appear during transient init/shutdown cycles inside the entrypoint.
    # We must poll with pg_isready (or direct connect) until the server actually accepts connections.
    # Use a bounded poll loop; fail fast with clear error if it never stabilizes.
    import time as _time

    host = container.get_container_host_ip()
    port = container.get_exposed_port(5432)
    deadline = _time.time() + 90.0
    last_err: Exception | None = None
    while _time.time() < deadline:
        try:
            # Prefer pg_isready inside the container (matches compose healthcheck)
            result = container.exec(["pg_isready", "-U", "shipsense", "-h", "127.0.0.1", "-p", "5432"])
            # exec returns (exit_code, output) or similar; treat non-zero as not ready
            if getattr(result, "exit_code", None) in (None, 0):
                # Some versions return (rc, (stdout, stderr)) tuple
                rc = result[0] if isinstance(result, (list, tuple)) else getattr(result, "exit_code", 0)
                if rc in (None, 0):
                    break
        except Exception as exc:
            last_err = exc
        _time.sleep(0.5)
    else:
        # Did not become ready in time
        raise RuntimeError(
            f"timescale container did not become ready within 90s; last error: {last_err}"
        )

    host = container.get_container_host_ip()
    port = container.get_exposed_port(5432)
    url = f"postgresql+asyncpg://shipsense:shipsense@{host}:{port}/shipsense"

    try:
        yield url
    finally:
        container.stop()


@pytest.fixture(scope="session")
def _alembic_migrated(timescale_url: str) -> Iterator[str]:
    """Run alembic upgrade head once per session against the container URL.

    Uses sync psycopg URL via migration_database_url pattern.
    Fails the session if alembic fails (no silent swallow).
    """
    # Convert asyncpg URL to sync psycopg for alembic
    sync_url = timescale_url.replace("+asyncpg", "+psycopg")

    # Build PYTHONPATH for the alembic subprocess so that env.py can import
    # apps.edge.storage.schemas without relying on pytest's internal sys.path
    # augmentation (which does not propagate to child processes).
    root = os.getcwd()
    collector_src = os.path.join(root, "apps/edge/collector/src")
    emulator_src = os.path.join(root, "apps/edge/emulator/src")
    pp_parts = [root, collector_src, emulator_src]
    existing_pp = os.environ.get("PYTHONPATH", "")
    if existing_pp:
        pp_parts.append(existing_pp)
    subprocess_pythonpath = ":".join(pp_parts)

    # Run alembic from repo root with DATABASE_URL override + explicit PYTHONPATH.
    # IMPORTANT: use the venv's alembic binary explicitly; system pyenv shims may
    # resolve to a Python that lacks psycopg and project PYTHONPATH.
    alembic_bin = os.path.join(root, ".venv", "bin", "alembic")
    if not os.path.exists(alembic_bin):
        # Fallback to PATH resolution if venv layout differs
        alembic_bin = "alembic"

    env = {
        **os.environ,
        "DATABASE_URL": sync_url,
        "PYTHONPATH": subprocess_pythonpath,
    }
    result = subprocess.run(
        [alembic_bin, "upgrade", "head"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"alembic upgrade head failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    yield timescale_url


@pytest_asyncio.fixture()
async def db_engine(_alembic_migrated: str):
    """Async engine bound to the migrated test DB (module/function scope)."""
    engine = create_async_engine(_alembic_migrated, echo=False, future=True)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture()
async def db_session(db_engine) -> AsyncIterator[AsyncSession]:
    """AsyncSession with autouse truncate of samples/events between tests."""
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        try:
            yield session
        finally:
            # Truncate dependent tables in reverse FK order; cascade to be safe
            await session.execute(
                text("TRUNCATE TABLE events, samples RESTART IDENTITY CASCADE")
            )
            await session.commit()


@pytest_asyncio.fixture()
async def writer_endpoint(db_session) -> AsyncIterator[tuple[str, int]]:
    """WriterService on ephemeral TCP port + background writer_loop.

    Yields (host, port). On teardown: shutdown + cancel loop task.
    Does NOT call __main__; uses WriterService directly.
    """
    samples_repo = SamplesRepo(db_session)
    events_repo = EventsRepo(db_session)
    service = WriterService(
        session=db_session,
        samples_repo=samples_repo,
        events_repo=events_repo,
        flush_interval_ms=50,
    )

    host, port = await service.start_tcp("127.0.0.1", 0)
    assert port > 0, "expected ephemeral port > 0"

    queue: asyncio.Queue = asyncio.Queue()
    loop_task = asyncio.create_task(service.writer_loop())

    try:
        yield (host, port)
    finally:
        await service.shutdown()
        loop_task.cancel()
        try:
            await loop_task
        except asyncio.CancelledError:
            pass


@pytest.fixture(scope="module")
def mqtt_broker() -> tuple[str, int]:
    """Start an ephemeral Mosquitto broker for MQTT pipeline integration tests (T-002 s04).

    Local wrap of collector pattern to avoid importing collector test package quirks.
    """
    try:
        from testcontainers.community.mqtt import MosquittoContainer
    except ImportError:  # pragma: no cover - integration dependency
        pytest.skip("testcontainers mqtt extra not installed")
    try:
        import aiomqtt  # noqa: F401
    except ImportError:  # pragma: no cover - integration dependency
        pytest.skip("aiomqtt not installed")

    import concurrent.futures

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(
                lambda: MosquittoContainer("eclipse-mosquitto:2").start()
            )
            broker = future.result(timeout=60)
    except concurrent.futures.TimeoutError:
        pytest.fail("MosquittoContainer.start timed out after 60s")
    except Exception as exc:
        pytest.skip(f"Mosquitto container is unavailable: {exc}")
    try:
        host = broker.get_container_host_ip()
        port = int(broker.get_exposed_port(1883))
        yield host, port
    finally:
        broker.stop()
