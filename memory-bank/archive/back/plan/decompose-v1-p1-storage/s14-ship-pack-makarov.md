# Шаг s14: ship-pack/makarov (vessel, assets, tag_map, native_stub, timezone)
**Plan ID:** v1-p1-storage
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** no
**AC:** AC-STO-S14 (из плана §214–222, §677–777: ~586 KKS, full hierarchy, stub native, TZ config, validated by loader)
**code_surface:** infra

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`

## Цель
Создать минимальный production-ready ship-pack для «Адмирал Макаров»: vessel.yaml, assets.yaml (NDO/GDU с механизмами), tag_map.yaml (~586 entries с label/unit/source/range/setpoints), native_map_stub.yaml (synthetic до Ф0), timezone.yaml (Asia/Vladivostok + rules). Структура валидна под loader s12.

## Контекст
- **Consumes:** план §678–777 (примеры YAML), s12 loader validation.
- **Produces:** ship-pack/makarov/*.yaml
- **Downstream:** s12 load, s13 engine, s14 is the data; T-001 stub native, emulator.
- **План:** §216 (tree 586), §218 (stub), §661 (TZ).

## Файлы
- `ship-pack/makarov/vessel.yaml` (Создание)
- `ship-pack/makarov/assets.yaml` (Создание — полная иерархия)
- `ship-pack/makarov/tag_map.yaml` (Создание — ~586 tags; в реальности будет от консультанта; здесь representative + count_expected)
- `ship-pack/makarov/native_map_stub.yaml` (Создание — synthetic mappings)
- `ship-pack/makarov/timezone.yaml` (Создание)

## Интерфейсы (lean — без кода)
- YAML контракты как в план §680 (vessel), §698 (assets), §736 (tag_map), §761 (native_stub), §662 (timezone).
- tag_count_expected: 482 aps + 104 skt = 586.
- approved: true в stub.

## TDD
- **Нет:** данные + структура.
- **Верификация:** loader s12 на этом pack → no error, 586 unique tags, tree ok, checksum.
- В s18: fixture minimal + full pack load.

## Подробный процесс выполнения
1. Скопировать/адаптировать примеры из плана.
2. Для tag_map: сгенерировать representative (несколько десятков реальных + заглушки для 586) с корректными KKS (TAI*, PAL*, SKT*).
3. native_stub: MODBUS/OPC примеры + synthetic.
4. TZ: Asia/Vladivostok, prefer_source=true, thresholds из плана.
5. Убедиться, что assets покрывают все tags из tag_map (валидация в loader).

## Верификация
- `python -m semantic.loader ship-pack/makarov` → success, tag count 586.
- diff stub → quarantine empty если approved.
- Блокер: s12 (loader).

## Блокеры / CREATIVE
Ф0 native map позже (stub ok).
