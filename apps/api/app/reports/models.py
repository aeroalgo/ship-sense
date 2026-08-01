from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Index, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ReportRun(Base):
    __tablename__ = "report_runs"
    __table_args__ = (Index("report_runs_type_generated", "type", "generated_at"),)

    report_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    period_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_to: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    boundary_rule: Mapped[str] = mapped_column(String(32), nullable=False)
    asset_scope: Mapped[str | None] = mapped_column(Text)
    formulas_version: Mapped[str] = mapped_column(String(64), nullable=False)
    data_watermark: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    initiated_by: Mapped[str | None] = mapped_column(Text)
    body_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    body_html: Mapped[str | None] = mapped_column(Text)
    provenance: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
