"""FastAPI dependency providers for API layers."""

from collections.abc import AsyncIterator

from app.core.database.session import get_session
from app.core.settings import settings
from app.semantic.engine import SemanticEngine
from app.session.service import SessionService
from app.telemetry.service import get_latest_value_cache
from app.vessel.service import VesselStateService
from app.vessel.store import InMemoryOverrideStore

_vessel_override_store = InMemoryOverrideStore()

def get_vessel_service() -> VesselStateService:
    return VesselStateService(settings.SHIP_PACK_PATH, get_latest_value_cache(), _vessel_override_store)


_semantic_engine = SemanticEngine()
_session_service = SessionService(settings.SHIP_PACK_PATH)


async def get_db() -> AsyncIterator:
    """Yield the shared database session dependency."""
    async for session in get_session():
        yield session


def get_semantic_engine() -> SemanticEngine:
    return _semantic_engine


def get_session_service() -> SessionService:
    return _session_service
