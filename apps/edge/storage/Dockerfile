# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/app:/app/collector
WORKDIR /app

RUN pip install --no-cache-dir \
    alembic asyncpg "psycopg[binary]" pydantic PyYAML sqlalchemy

COPY apps/ ./apps/
COPY apps/edge/collector/src/ ./collector/
COPY migrations/ ./migrations/
COPY alembic.ini pyproject.toml ./
COPY ship-pack/ ./ship-pack/

EXPOSE 9009
STOPSIGNAL SIGTERM
ENTRYPOINT ["python", "-m", "apps.edge.storage"]
