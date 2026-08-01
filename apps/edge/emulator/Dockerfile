# syntax=docker/dockerfile:1
# I3 industrial emulator (T-001 test source).
# Build context: apps/edge/emulator
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && addgroup --system shipsense \
    && adduser --system --ingroup shipsense shipsense

COPY src/ ./src/
COPY config/ ./config/

ENV PYTHONPATH=/app/src

# Modbus TCP (5020) + OPC UA (4840). Порты задокументированы в README + compose.
EXPOSE 5020 5021 4840

STOPSIGNAL SIGTERM
USER shipsense

# host 0.0.0.0 — слушать во всех интерфейсах контейнера (dev default 127.0.0.1
# в контейнере не даст collector'у подключиться из соседнего сервиса).
ENTRYPOINT ["python", "-m", "emulator"]
CMD ["--host", "0.0.0.0", "--modbus-port", "5020", "--opcua-port", "4840"]
