from datetime import datetime, timezone

import sqlalchemy as sa

from apps.edge.storage.schemas import (
    Base,
    Event,
    HealthSnapshot,
    Sample,
    SemanticMeta,
    StorageQuotaConfig,
    TagQuarantine,
)


def test_storage_models_expose_expected_tables_and_columns() -> None:
    assert set(Base.metadata.tables) == {
        "samples",
        "events",
        "semantic_meta",
        "tag_quarantine",
        "clock_shift_log",
        "health_snapshots",
        "storage_quota_config",
        "samples_degrade_log",
        "samples_degrade_watermark",
    }
    assert [column.name for column in Sample.__table__.primary_key] == ["tag_id", "ts"]
    assert Event.__table__.c.idempotency_key.unique is True
    assert isinstance(Event.__table__.c.params.type, sa.JSON)
    assert isinstance(Sample.__table__.c.ts.type, sa.DateTime)
    assert Sample.__table__.c.ts.type.timezone is True
    assert SemanticMeta.__table__.constraints
    assert TagQuarantine.__table__.c.acknowledged.server_default is not None
    assert HealthSnapshot.__table__.c.extra.nullable is True
    assert StorageQuotaConfig.__table__.c.id.primary_key is True


def test_models_can_be_instantiated_with_fastapi_storage_payloads() -> None:
    now = datetime.now(timezone.utc)
    sample = Sample(
        ts=now,
        tag_id="main-engine.rpm",
        value=1200.0,
        quality=1,
        source_ts=now,
        edge_ts=now,
        official_ts=now,
    )
    event = Event(
        idempotency_key="mqtt-1",
        event_name="alarm",
        source="panel-aps",
        source_ts=now,
        edge_ts=now,
        official_ts=now,
        params={"tag_id": sample.tag_id},
        severity=2,
    )
    assert sample.tag_id == event.params["tag_id"]
