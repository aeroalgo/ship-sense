# [T-001 | s09 | opcua-security] IMPLEMENT
**Plan ID:** v1-p1-collector
**Decompose step:** [s09-opcua-security.md](../../plan/decompose-v1-p1-collector/s09-opcua-security.md)
**Implement index:** [index.md](index.md)
**Дата:** 2026-07-26
**Уровень:** L1 (security helpers, TDD)
**AC:** AC-B3-04, AC-B3-09, AC-B3-01 (readonly session prep)
**Статус:** done
Путь артефакта (epic): `memory-bank/back/implement/implement-v1-p1-collector/s09-opcua-security.md`

## Skills
- tdd, python-testing-patterns, modern-python (по workflow-implement)
- verification-before-completion (перед FINISH)

## Сделано
- Создан `plugins/opcua/security.py` — security helpers:
  - `build_client_security(config: SecurityConfig) → dict[str, Any]`:
    - Маппинг policy name → asyncua SecurityPolicy* (Basic256Sha256, Aes128..., None).
    - Маппинг mode name → ua.MessageSecurityMode (SignAndEncrypt, Sign, None_).
    - Для None/пустого policy или mode=None → возвращает `{}` (безопасность не применяется).
    - Если policy требует security, но cert_path/key_path отсутствуют → ConfigError с ясным сообщением.
    - Возвращает kwargs для `client.set_security(policy, certificate, private_key, mode=...)`.
  - `ensure_trust_store(path: str | Path) → Path`:
    - Создаёт директорию (mkdir -p, idempotent).
    - Для хранения доверенных server certs (offline-валидация, если потребуется в s10).
  - Инвариант в docstring: «публичный API НЕ экспортирует write paths» (AC-B3-01 prep).
- Создан `plugins/opcua/__init__.py` — экспорт `build_client_security`, `ensure_trust_store`.
- Тесты: `tests/unit/test_opcua_security.py` (TDD red→green):
  - `test_build_security_sign_and_encrypt_with_explicit_paths` — policy+mode+пути → args с policy/mode/cert/key.
  - `test_build_security_missing_cert_raises_config_error` — None cert/key → ConfigError.
  - `test_build_security_none_policy_returns_empty` — "None"/"" → {}.
  - `test_build_security_sign_mode_maps` — mode=Sign → MessageSecurityMode.Sign.
  - `test_ensure_trust_store_creates_dir` — создаёт nested dir, idempotent.
  - `test_build_security_unknown_policy_raises` — неизвестный policy → ConfigError.
- TDD: red (ModuleNotFoundError на import security) → реализация → 6 passed targeted.

## Файлы
- `apps/edge/collector/src/collector/plugins/opcua/security.py` (Создание)
- `apps/edge/collector/src/collector/plugins/opcua/__init__.py` (Создание)
- `apps/edge/collector/tests/unit/test_opcua_security.py` (Создание)

## Тесты
- **Runner note:** `PYTHONPATH=src .venv/bin/python -m pytest`. Async через `pytest.mark.asyncio`.
- red: `PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_opcua_security.py` → `ModuleNotFoundError: No module named 'collector.plugins.opcua.security'`.
- cmd targeted: `PYTHONPATH=src /home/aero/PyProject/ship-sense/.venv/bin/python -m pytest -q tests/unit/test_opcua_security.py`
- итог targeted: **6 passed in 0.45s**.
- cmd regression (plugin registry): `PYTHONPATH=src /home/aero/PyProject/ship-sense/.venv/bin/python -m pytest -q tests/unit/test_plugin_registry.py`
- итог regression: **12 passed** (не затронуты, opcua protocol уже был известен registry).

Покрытие (чекпоинты decompose s09):
- trust store configurable — green ✓ (`test_ensure_trust_store_creates_dir`)
- missing cert → понятная ошибка — green ✓ (`test_build_security_missing_cert_raises_config_error`)
- нет Write service в security helper API — green ✓ (grep + инвариант в docstring; публичные имена не содержат write_*)

## Integration check (§0.11)
- **SecurityConfig** (s02, models.py:31) → используется в `build_client_security(config)`.
- **ConfigError** (domain/errors.py) → raised для missing cert / unknown policy.
- **sources.dev.yaml** (config/) → содержит пример `security: {policy: Basic256Sha256, mode: SignAndEncrypt}` для aps_main_opcua.
- **validator.py** (config/) → уже знает protocol="opcua" + subscribe (не затронуто).
- **plugin registry** (s03) → opcua уже регистрируется как протокол (test_register_and_create_opcua); security не затрагивает registry.
- **asyncua Client.set_security** — контракт: `policy, certificate, private_key, mode=MessageSecurityMode` (server_certificate опционален, asyncua сам вытащит при connect).
- **Нет write путей** (AC-B3-01 prep): в security.py только чтение cert/key путей; публичный API (`build_client_security`, `ensure_trust_store`) не экспортирует write_*.
- §0.11: **PASS** (все внешние ссылки имеют существующие counterparts; wiring SecurityConfig → security helper → asyncua).
