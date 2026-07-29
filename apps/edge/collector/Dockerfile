# syntax=docker/dockerfile:1
# Collector — edge telemetry collector (T-001).
# Build context: apps/edge/collector
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps: libc для asyncua/pymodbus ничего сверх slim не требуют.
# gcc нужен только если wheel'ов под целевую платформу нет (например cryptography).
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# App source (src layout). PYTHONPATH=src — соответствует dev-запуску.
COPY pyproject.toml ./
COPY src/ ./src/
COPY config/ ./config/
COPY maps/ ./maps/

ENV PYTHONPATH=/app/src

# Health snapshot volume (sources.dev.yaml → /var/lib/shipsense/health).
RUN mkdir -p /var/lib/shipsense/health
VOLUME ["/var/lib/shipsense/health"]

# 9009 — sink IPC framing collector → writer (AC-INT-01, README §framing).
EXPOSE 9009

# SIGTERM → CollectorApp.request_stop → exit 0 (AC-HLT-05).
STOPSIGNAL SIGTERM

ENTRYPOINT ["python", "-m", "collector"]
CMD ["--snapshot", "/var/lib/shipsense/health/collector.json"]
