"""SQLAlchemy models for the edge storage schema (storage plan §236 ERD)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Interval,
    JSON,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    false,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


Timestamp = DateTime(timezone=True)


class Sample(Base):
    __tablename__ = "samples"
    __table_args__ = (
        CheckConstraint("quality BETWEEN 0 AND 5", name="samples_quality_chk"),
        Index("idx_samples_tag_ts_desc", "tag_id", text("ts DESC")),
        Index("idx_samples_official_ts", text("official_ts DESC")),
        Index("idx_samples_edge_ts", text("edge_ts DESC")),
    )

    tag_id: Mapped[str] = mapped_column(Text, primary_key=True)
    ts: Mapped[datetime] = mapped_column(Timestamp, primary_key=True)
    value: Mapped[float | None] = mapped_column(Float)
    quality: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")
    source_ts: Mapped[datetime] = mapped_column(Timestamp, nullable=False)
    edge_ts: Mapped[datetime] = mapped_column(Timestamp, nullable=False)
    official_ts: Mapped[datetime] = mapped_column(Timestamp, nullable=False)


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint(
            "severity IS NULL OR severity BETWEEN 0 AND 4",
            name="events_severity_chk",
        ),
        Index("idx_events_official_ts", text("official_ts DESC"), "event_id"),
        Index("idx_events_name_ts", "event_name", text("official_ts DESC")),
        Index("idx_events_source_ts", "source", text("official_ts DESC")),
    )

    event_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    event_name: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    source_ts: Mapped[datetime] = mapped_column(Timestamp, nullable=False)
    edge_ts: Mapped[datetime] = mapped_column(Timestamp, nullable=False)
    official_ts: Mapped[datetime] = mapped_column(Timestamp, nullable=False)
    params: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, server_default="{}")
    severity: Mapped[int | None] = mapped_column(SmallInteger)
    reconstructed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())
    ingested_at: Mapped[datetime] = mapped_column(Timestamp, nullable=False, server_default=func.now())


class ClockShiftLog(Base):
    __tablename__ = "clock_shift_log"
    __table_args__ = (
        CheckConstraint("detected_on IN ('edge', 'source')", name="clock_shift_detected_on_chk"),
        Index("idx_clock_shift_detected", text("detected_at DESC")),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    detected_at: Mapped[datetime] = mapped_column(Timestamp, nullable=False, server_default=func.now())
    detected_on: Mapped[str] = mapped_column(Text, nullable=False)
    delta: Mapped[Any] = mapped_column(Interval, nullable=False)
    prev_ts: Mapped[datetime] = mapped_column(Timestamp, nullable=False)
    new_ts: Mapped[datetime] = mapped_column(Timestamp, nullable=False)
    linked_event_id: Mapped[UUID | None] = mapped_column(ForeignKey("events.event_id"))


class SemanticMeta(Base):
    __tablename__ = "semantic_meta"
    __table_args__ = (UniqueConstraint("pack_name", "version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pack_name: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(Text, nullable=False)
    approved_at: Mapped[datetime] = mapped_column(Timestamp, nullable=False, server_default=func.now())
    checksum: Mapped[str] = mapped_column(Text, nullable=False)
    manifest: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class TagQuarantine(Base):
    __tablename__ = "tag_quarantine"
    __table_args__ = (Index("idx_tag_quarantine_since", text('"since" DESC')),)

    tag_id: Mapped[str] = mapped_column(Text, primary_key=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    since: Mapped[datetime] = mapped_column(Timestamp, nullable=False, server_default=func.now())
    native_id_hint: Mapped[str | None] = mapped_column(Text)
    acknowledged: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())


class HealthSnapshot(Base):
    __tablename__ = "health_snapshots"
    __table_args__ = (Index("idx_health_snapshots_at", text("captured_at DESC")),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    captured_at: Mapped[datetime] = mapped_column(Timestamp, nullable=False, server_default=func.now())
    disk_total_gb: Mapped[float | None] = mapped_column(Float)
    disk_used_gb: Mapped[float | None] = mapped_column(Float)
    disk_pct: Mapped[float | None] = mapped_column(Float)
    ram_pct: Mapped[float | None] = mapped_column(Float)
    cpu_pct: Mapped[float | None] = mapped_column(Float)
    pg_size_mb: Mapped[float | None] = mapped_column(Float)
    queue_depth: Mapped[int | None] = mapped_column(Integer)
    extra: Mapped[dict[str, Any] | None] = mapped_column(JSON, server_default="{}")


class StorageQuotaConfig(Base):
    __tablename__ = "storage_quota_config"
    __table_args__ = (CheckConstraint("id = 1", name="storage_quota_config_id_chk"),)

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, server_default="1")
    disk_total_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    alert_pct: Mapped[float] = mapped_column(Float, nullable=False, server_default="80.0")
    samples_quota_pct: Mapped[float] = mapped_column(Float, nullable=False, server_default="85.0")
    events_quota_pct: Mapped[float] = mapped_column(Float, nullable=False, server_default="10.0")
    headroom_pct: Mapped[float] = mapped_column(Float, nullable=False, server_default="5.0")
    updated_at: Mapped[datetime] = mapped_column(Timestamp, nullable=False, server_default=func.now())


class SamplesDegradeLog(Base):
    __tablename__ = "samples_degrade_log"
    __table_args__ = (Index("idx_samples_degrade_log_at", text("degraded_at DESC")),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    degraded_at: Mapped[datetime] = mapped_column(Timestamp, nullable=False, server_default=func.now())
    chunk_start: Mapped[datetime] = mapped_column(Timestamp, nullable=False)
    chunk_end: Mapped[datetime] = mapped_column(Timestamp, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    rows_estimate: Mapped[int | None] = mapped_column(BigInteger)


class SamplesDegradeWatermark(Base):
    __tablename__ = "samples_degrade_watermark"
    __table_args__ = (CheckConstraint("id = 1", name="samples_degrade_watermark_id_chk"),)

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, server_default="1")
    oldest_sample_ts: Mapped[datetime | None] = mapped_column(Timestamp)
    updated_at: Mapped[datetime] = mapped_column(Timestamp, nullable=False, server_default=func.now())
