# syntax=docker/dockerfile:1
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY apps/edge/collector/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && addgroup --system shipsense \
    && adduser --system --ingroup shipsense shipsense
COPY apps/edge/gateway/ ./apps/edge/gateway/
COPY apps/__init__.py ./apps/__init__.py
COPY apps/edge/__init__.py ./apps/edge/__init__.py

ENV PYTHONPATH=/app
EXPOSE 5020
STOPSIGNAL SIGTERM
USER shipsense
ENTRYPOINT ["python", "-m", "apps.edge.gateway.main"]
