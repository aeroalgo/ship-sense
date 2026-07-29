# Шаг s06: Modbus decoder: float32/int/bitfield/endianness
**Plan ID:** v1-p1-collector
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-B2-02, AC-B2-03, AC-B2-04, AC-B2-12

**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
Modbus decoder: float32/int/bitfield/endianness — один атомарный IMPLEMENT-заход с проверяемым deliverable.

## Контекст
- **Consumes:** plan §12.3–12.4 golden cases
- **Produces:** decoder.py pure functions + golden unit tests

## Файлы
- `apps/edge/collector/src/collector/plugins/modbus/decoder.py` (Создание)
- `apps/edge/collector/tests/unit/test_decoder_float32.py` (Создание)
- `apps/edge/collector/tests/unit/test_bitfield.py` (Создание)

## Интерфейсы (lean — без кода)
- fn: `decode_float32(regs, word_order, byte_order) → float`
- fn: `decode_int(regs, datatype, endian) → int`
- fn: `extract_bit(register, bit_index) → bool` — native_id `40200.3`

## TDD (красная → зелёная)
1. **Тест:** `test_decoder_float32.py`, `test_bitfield.py`
2. **Запуск:** тесты падают (реализации нет).
3. **Реализация:** минимальный код по интерфейсам и процессу ниже.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. TDD: сначала golden vectors ABCD/CDAB/BADC/DCBA для float32.
2. int16/32 uint16/32; bitfield extract.
3. Без сетевого I/O.

## Чекпоинт верификации
- все golden float32 green
- bit 40200.3 корректно
- невалидная длина regs → явная ошибка
