# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/app/apps/api
WORKDIR /app

RUN pip install --no-cache-dir \
    fastapi uvicorn[standard] pydantic-settings sqlalchemy asyncpg PyYAML \
    && addgroup --system shipsense \
    && adduser --system --ingroup shipsense shipsense

COPY apps/api/ ./apps/api/
COPY ship-pack/ ./ship-pack/

EXPOSE 8000
STOPSIGNAL SIGTERM
USER shipsense
ENTRYPOINT ["uvicorn", "app.main:app"]
CMD ["--host", "0.0.0.0", "--port", "8000"]
