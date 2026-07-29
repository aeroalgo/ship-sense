# syntax=docker/dockerfile:1
# Writer stub (T-002 day-1) — length-prefixed framing server, drain-only.
# Реальный writer — задача T-002; здесь контейнер-заглушка, чтобы IPC sink
# collector'а (AC-INT-01) имел живого peer'а в compose и не падал с SinkUnavailable.
# Build context: apps/edge/writer-stub
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY src/ ./src/

ENV PYTHONPATH=/app/src

EXPOSE 9009

STOPSIGNAL SIGTERM

ENTRYPOINT ["python", "-m", "writer_stub"]
CMD ["--host", "0.0.0.0", "--port", "9009"]
