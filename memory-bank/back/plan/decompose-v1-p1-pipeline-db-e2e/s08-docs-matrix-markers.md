# Шаг s08: матрица доказательств + pyproject markers/testpaths
**Plan ID:** v1-p1-pipeline-db-e2e
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** no
**AC:** AC-PIPE-09, AC-PIPE-10
**code_surface:** infra

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`

## Цель
Зафиксировать runner contract и матрицу «что доказывает pytest L0/L1 / compose L2 / nightly load». `pyproject.toml`: `testpaths` включает `tests/pipeline`; marker `e2e` (optional) зарегистрирован. README команды smoke + expected SQL. Регрессия соседних suite не сломана.

## Контекст
- **Consumes:** s01–s07 артефакты; plan §2.1 / §11 matrix.
- **Produces:** docs fragment + pyproject markers; AC-PIPE-10 verify командой.

## Файлы
- `pyproject.toml` (Модификация — testpaths, markers)
- `apps/edge/collector/README.md` и/или `infra/timescale/README.md` (Модификация — L2 smoke команды)
- `tests/conftest.py` (Модификация — register `e2e` если нужно)

## Интерфейсы (lean — без кода)
- Документ-матрица (таблица): Layer | Tool | Markers | Assert | CI/manual.
- Команды: `.venv/bin/pytest tests/pipeline …`; `scripts/smoke-pipeline-db.sh [default|mqtt]`.
- Marker `e2e` description в `[tool.pytest.ini_options] markers`.
- n/a runtime API.

## TDD (нет)
- **Причина:** docs + config markers.
- **Верификация:**
  - `grep`/чтение pyproject — `tests/pipeline` в testpaths; marker объявлен.
  - Регрессия: `.venv/bin/pytest tests/storage apps/edge/collector/tests apps/edge/emulator/tests -q` (parent) — без новых fail.
  - `pytest --markers` показывает `e2e` если добавлен.

## Подробный процесс выполнения
1. Дописать README § Pipeline DB E2E (команды + expected COUNT).
2. pyproject: testpaths + marker.
3. Прогнать regression (parent).
4. Не менять load 586 suite scope.

## Чекпоинт верификации
- AC-PIPE-09: матрица в README/implement.
- AC-PIPE-10: storage + mqtt e2e + emulator mqtt — green.
- DoD plan §1 пункты 6–7.

## Зависимости
- s01–s07 желательно done; markers можно частично раньше — этот шаг финализирует.

## Frontend
N/A.

## Следующий шаг
→ BACK QA `v1-p1-pipeline-db-e2e` (L2 + regression + FR-7 hardening по желанию).
