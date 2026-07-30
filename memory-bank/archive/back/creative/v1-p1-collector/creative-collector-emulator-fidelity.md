# CR-COL-03 — Универсальная fidelity-архитектура промышленного эмулятора

**Creative ID:** CR-COL-03  
**Decompose step:** [s15-emulator-tag-model.md](../../plan/decompose-v1-p1-collector/s15-emulator-tag-model.md)  
**Зависимые шаги:** [s16-emulator-modbus-server.md](../../plan/decompose-v1-p1-collector/s16-emulator-modbus-server.md), [s17-emulator-opcua-server.md](../../plan/decompose-v1-p1-collector/s17-emulator-opcua-server.md), [s18-emulator-dirt.md](../../plan/decompose-v1-p1-collector/s18-emulator-dirt.md)  
**Plan:** [plan-v1-p1-collector.md](../../plan/plan-v1-p1-collector.md) (§6.1, §10, AC-I3-01..16)  
**Дата:** 2026-07-27  
**Режим:** BACK CREATIVE  
**Уровень:** L4 (T-001)  
**Статус:** approved by user; selected universal design

## 1. Решение

Нужна не «модель АПС на 586 тегов», а **универсальное ядро эмулятора промышленных сигналов**, которое в первом профиле описывает АПС/СКТ ГЭУ.

Выбранная архитектура:

```text
Profile YAML (catalog + dynamics + scenarios)
                    |
                    v
             SignalModel / TagGenerator
                    |
          one immutable tick snapshot
             /                    \
    Modbus adapter           OPC UA adapter

ScenarioRunner -> model snapshot / adapter transport hooks
```

- По умолчанию оба протокола работают **в одном процессе** и используют один `TagGenerator`.
- Протоколы не импортируются в domain/model: они являются отдельными адаптерами.
- Профиль оборудования задаётся YAML; Python-код содержит универсальные генераторы и registry, а не список корабельных тегов.
- `tags_stub.yaml` содержит 586 сигналов текущего профиля, но формат не привязан к судну.
- Внешние реальные профили Ф2.5 и Ф0 заменяют YAML-данные, не меняя ядро.

Это сохраняет выбранное ранее преимущество одного процесса — общий snapshot и отсутствие IPC — и одновременно не превращает ship-specific assumptions в архитектурный контракт.

## 2. Критерии универсальности

Решение считается пригодным для следующего промышленного оборудования, если новый профиль можно добавить без:

- изменения `TagGenerator`;
- импорта нового оборудования в physics-код;
- копирования Modbus/OPC UA логики;
- изменения seed-контракта;
- изменения `ScenarioRunner` для уже поддержанных типов dirt.

Новый protocol adapter или новый generator kind может добавляться как отдельный extension, но профиль существующих протоколов остаётся совместимым.

## 3. Архитектурные варианты

### 3.1 Топология запуска

#### Вариант A — один процесс, общая модель и два адаптера (выбран)

**Плюсы:**

- один источник истины для обоих протоколов;
- одинаковые значения при чтении Modbus и OPC UA;
- единый seed и единый tick index;
- сценарий применяется согласованно;
- простая локальная интеграция и меньше инфраструктуры.

**Минусы:**

- ошибка в общем core потенциально влияет на оба адаптера;
- независимое масштабирование протоколов не является целью dev-режима.

#### Вариант B — два процесса с общей конфигурацией и seed

**Плюсы:**

- сильная изоляция отказов;
- ближе к deployment, где протоколы могут быть на разных endpoint.

**Минусы:**

- требуется IPC или независимое воспроизведение потока;
- легко получить разные значения из-за рассинхронизации tick;
- сложнее локальный запуск и тесты.

#### Вариант C — всегда два процесса плюс replay-файл

**Плюсы:**

- максимально близко к capture/replay стенду;
- можно разнести нагрузку.

**Минусы:**

- premature для профиля без реального capture;
- инфраструктурный overhead не улучшает текущий AC-I3-03.

**Рекомендация:** A по умолчанию. Core и adapters должны иметь такой контракт, чтобы B можно было добавить позднее без переписывания модели: sidecar получает тот же snapshot или replay stream.

### 3.2 Представление сигнала

#### Вариант A — ship-specific список тегов в Python

Отклонён: не переносится на другое оборудование и ломает замену карты после Ф0.

#### Вариант B — универсальный config-driven catalog (выбран)

**Плюсы:**

- тип, единицы, диапазон, protocol IDs и динамика — данные;
- один формат для APS, SKT GEU, насоса, компрессора или турбины;
- startup validation ловит дубли и неверные диапазоны;
- representative subset и stub-расширение живут в одном формате.

**Минусы:**

- нужен явный schema/versioning;
- YAML менее удобен для очень больших профилей, поэтому позднее возможен generated YAML/JSON без смены domain API.

#### Вариант C — универсальная конфигурация + database catalog

Отклонён для s15: база добавляет I/O и миграции, хотя профиль нужен локальному эмулятору и должен запускаться в тестах без инфраструктуры.

**Рекомендация:** B; YAML — portable source format, Pydantic/dataclass validation на startup.

### 3.3 Динамика сигнала

#### Вариант A — независимый random walk

Отклонён как default: не даёт физически полезных корреляций.

#### Вариант B — driver/dependency graph (выбран)

Каждый signal может быть:

- `constant`;
- `random_walk`;
- `periodic`;
- `discrete`;
- `correlated`, ссылающийся на один или несколько drivers;
- позднее `replay`.

Зависимости описываются data-only графом. Для текущего профиля драйвер `MAIN_ENGINE_RPM` питает temperature/pressure, но core не знает слова «engine».

**Плюсы:**

- переносится на любое оборудование;
- коэффициенты и диапазоны меняются в профиле;
- можно валидировать неизвестные drivers и циклы;
- корреляции проверяются отдельно от транспорта.

**Минусы:**

- требуется topological ordering;
- сложнее независимого шума.

#### Вариант C — replay реальных временных рядов как основной режим

Отклонён как baseline: capture Ф2.5 ещё нет, а генератор должен работать в чистом dev/CI окружении. Replay будет предусмотренным будущим `generator.kind`, но не реализуется в s15.

**Рекомендация:** B сейчас, replay как совместимое расширение.

### 3.4 Seed strategy

#### Вариант A — один mutable `random.Random` на все теги

Отклонён: добавление/удаление тега или изменение порядка YAML сдвигает случайный поток всех остальных тегов.

#### Вариант B — независимые детерминированные substreams (выбран)

Поток сигнала выводится из:

```text
(seed, profile_id, signal_id, tick_index, stream_name) -> deterministic noise
```

Внутри можно использовать стабильный hash (не Python `hash()`, который рандомизирован между процессами) и локальный PRNG для каждого сигнала/driver. Порядок YAML не является частью результата.

**Плюсы:**

- изменение одного сигнала не ломает остальные golden streams;
- один seed воспроизводим между процессами;
- можно параллельно вычислять группы в будущем;
- сценарии получают отдельные stream names.

**Минусы:**

- нужен явно зафиксированный stable-hash алгоритм;
- stateful random walk требует хранить предыдущее состояние driver, но шум каждого шага остаётся адресуемым.

#### Вариант C — только seed + mutable PRNG sequence

Проще, но непереносимо для evolving catalogs и параллельных адаптеров. Не выбираем.

**Рекомендация:** B. Детерминизм означает идентичность по `(profile, seed, tick_index)`, а не зависимость от wall clock или порядка словаря.

### 3.5 Суточные и режимные паттерны

#### Вариант A — hard-coded sinusoid

Отклонён: промышленное оборудование имеет сменные профили нагрузки, а не одну «судовую» синусоиду.

#### Вариант B — composable profile functions из YAML (выбран)

`daily_patterns.py` предоставляет чистый UTC-профиль, а конфигурация выбирает:

- период;
- амплитуду;
- фазу;
- baseline;
- режимы (`stopped`, `running`, `maintenance`) и переходы.

В s15 достаточно реализовать bounded periodic profile и базовые driver correlations; registry оставляет место для state profile без импорта транспорта.

#### Вариант C — внешний скрипт/DSL в YAML

Отклонён: код в конфигурации создаёт проблемы безопасности, тестирования и воспроизводимости.

**Рекомендация:** B, только whitelisted generator kinds, никаких `eval`/вызываемых объектов из YAML.

## 4. Универсальный контракт профиля

Минимальная запись сигнала:

```yaml
profile:
  id: aps_stub
  version: 1
  tick_hz: 1.0
  signals:
    - signal_id: TAI4101
      native_ids:
        modbus: "40101"
        opcua: "ns=2;s=AI4101"
      value_type: float32
      unit: degC
      range: {min: -40, max: 120}
      generator:
        kind: correlated
        drivers: [MAIN_ENGINE_RPM]
        coefficients: [0.15]
        baseline: 70.0
        noise: 0.5
        daily_pattern: standard
```

Для обратной совместимости с plan допускаются aliases `tag_id`, `native_id_modbus`, `native_id_opcua`, `type`, но canonical internal model — `signal_id`, `native_ids`, `value_type`.

Обязательные invariants:

- `profile.id` и `version` заданы;
- `signal_id` уникален;
- native ID уникален внутри каждого protocol namespace;
- `range.min <= range.max`;
- generator kind известен registry;
- каждый driver существует;
- граф зависимостей ацикличен;
- значения соответствуют `value_type`.

Для текущего профиля:

- 482 APS + 104 SKT GEU;
- ровно 586 сигналов;
- `tags_stub.yaml` является адаптером этого универсального schema к текущему плану.

## 5. Универсальный tick/snapshot контракт

Публичный API остаётся совместимым с decompose:

```python
TagGenerator(seed=42, profile=profile).tick(t)
```

где `t` — целочисленный tick index, а результат — полный snapshot. Для adapter-neutral core рекомендуется внутренний typed snapshot с metadata:

```text
TickSnapshot:
  tick_index
  source_ts
  values: dict[native_id, scalar]
```

На границе s15 можно вернуть требуемый `dict[native_id, value]`; typed snapshot не должен протекать в Modbus/OPC API раньше необходимости.

Правила:

1. Сначала вычисляются drivers по dependency graph.
2. Затем correlated signals.
3. Затем daily/mode modifiers и deterministic noise.
4. Затем type/range validation модели.
5. Snapshot публикуется как единый результат для обоих адаптеров.

Wall-clock запрещён в расчёте значений. Pacing адаптера использует monotonic clock отдельно.

## 6. Correlations API

Вместо ship-specific функции как единственного механизма core предоставляет generic primitive:

```python
correlate(
    drivers: Mapping[str, float],
    coefficients: Mapping[str, float],
    baseline: float,
    noise: float,
    noise_sample: float,
) -> float
```

А требуемая функция s15 остаётся thin domain preset/helper:

```python
correlate_rpm_temp_pressure(...)
```

Она нужна для понятного AC-I3-03 теста, но делегирует generic primitive и не используется как архитектурный extension point.

Для temperature/pressure в APS профиль задаёт driver и коэффициенты. Для другого оборудования тот же алгоритм может описывать:

- pump speed → flow → pressure;
- compressor load → discharge temperature;
- turbine speed → bearing temperature/vibration;
- valve position → flow.

Не вводим отдельные Python-классы для каждого типа оборудования.

## 7. ScenarioRunner boundary

ScenarioRunner работает на уровне signal IDs и protocol hooks:

- value dirt (`out_of_range`, `stuck_value`, `nan_inf`, `signal_chatter`) изменяет snapshot или generator overlay;
- transport dirt (`connection_drop`, `modbus_bad_frame`) вызывается адаптером;
- metadata dirt (`tag_map_change`, `opc_bad_quality`, `time_jump`) изменяет protocol-facing envelope.

Это разделение обязательно для универсальности: например, MQTT/HTTP adapter сможет использовать value dirt, но не должен притворяться Modbus.

Порядок применения фиксирован:

```text
base model → value overlays → timestamp/quality overlays → transport hooks
```

Комбинации и seed описываются YAML. Инжектор не содержит APS-specific native IDs вне параметров профиля.

## 8. Performance и lifecycle

Целевой baseline сохраняется: 586 сигналов × 1 Hz, <30% одного CPU и <512 MB в dev. Универсальные меры:

- не создавать asyncio task на каждый сигнал;
- один tick loop на модель;
- один snapshot на tick;
- кэшировать compiled dependency order после startup;
- не делать YAML parsing в tick;
- не использовать глобальный random state.

При росте профиля сначала измерять; multiprocessing/parallel tick — отдельная оптимизация после profile-driven benchmark.

## 9. Тестовая стратегия

Обязательные example/property invariants для s15:

- один профиль → 586 сигналов;
- одинаковые `(profile, seed, N)` → идентичные N snapshots;
- изменение порядка записей YAML не меняет значения по `signal_id`;
- изменение одного сигнала не сдвигает noise stream несвязанных сигналов;
- все native IDs стабильны и уникальны по protocol;
- happy-path значения конечны и в диапазоне;
- dependency graph не допускает неизвестный driver и цикл;
- `daily_factor(t)` повторяется через период и не зависит от timezone/wall clock;
- generic correlation с положительным коэффициентом сохраняет положительный знак связи на выборке;
- Modbus и OPC adapters получают один и тот же snapshot (проверяется в s16/s17, не дублируется в s15).

Property-based тестирование применяется к чистым функциями и валидаторам; transport/integration тесты остаются example-based.

## 10. Решения для s15–s18

### s15 — TagGenerator

- создать universal signal model/loader в заявленных файлах;
- реализовать stable seed substreams;
- реализовать generic generators и driver graph минимум для `constant`, `random_walk`, `correlated`, `discrete`;
- реализовать bounded daily profile;
- поставлять `tags_stub.yaml` с 586 сигналами текущего профиля;
- не встраивать protocol server и dirt injector в model.

### s16 — ModbusServerAdapter

- один adapter instance получает общий `TagGenerator`/snapshot provider;
- native register mapping читается из profile;
- сервер read-only;
- транспортные сценарии вызываются через protocol hook.

### s17 — OpcUaServerAdapter

- тот же snapshot provider и тот же profile;
- NodeIds читаются из profile;
- сервер read-only;
- monitored item updates используют текущий snapshot.

### s18 — ScenarioRunner

- generic signal_id selectors;
- отдельные value/metadata/transport overlay interfaces;
- YAML сценарии не меняют core model;
- deterministic under the same profile + seed + scenario seed.

## 11. Что сознательно не делаем сейчас

- два процесса как обязательный режим;
- database-backed catalog;
- replay engine и хранение capture;
- пользовательский DSL или `eval` в YAML;
- отдельные классы `ShipTagGenerator`, `PumpTagGenerator`, `TurbineTagGenerator`;
- полноценную event engine;
- автоматическую калибровку по Ф2.5;
- hot reload профиля во время tick.

Это оставляет универсальную точку расширения, но не распыляет s15 и сохраняет атомарность шага.

## 12. Чекпоинт принятия CR-COL-03

- [x] Один процесс с общей моделью и двумя protocol adapters.
- [x] Архитектура profile-driven и equipment-neutral.
- [x] 586 — данные текущего APS profile, не ограничение core.
- [x] Generic dependency graph вместо hard-coded RPM/temp/pressure.
- [x] Stable per-signal deterministic substreams вместо одного глобального PRNG sequence.
- [x] Daily/mode patterns — composable pure functions.
- [x] Replay предусмотрен extension point, но не входит в s15.
- [x] Value dirt отделён от transport dirt.
- [x] Read-only protocol adapters.
- [x] Performance/lifecycle без task-per-signal.

## Rewire

- [x] s15: creative link, `needs_creative: no — closed`, Next Phase `BACK IMPLEMENT`.
- [x] s16: ссылка на общий snapshot/profile contract.
- [x] s17: ссылка на общий snapshot/profile contract.
- [x] s18: ссылка на ScenarioRunner boundary и dirt precedence.
- [x] decompose index: blocker CR-COL-03 закрыт, dependents cleared.

## Handoff

- **Done:** BACK CREATIVE CR-COL-03 — выбрана универсальная profile-driven архитектура промышленного эмулятора: один процесс, общий snapshot, protocol adapters, generic dependency graph, stable per-signal seed streams, composable patterns и разделение value/transport dirt.
- **Files:** `memory-bank/back/creative/v1-p1-collector/creative-collector-emulator-fidelity.md`; rewired `s15`, `s16`, `s17`, `s18` и decompose index.
- **Next:** `BACK IMPLEMENT s15` в новом чате — TDD TagGenerator, correlations, daily patterns и 586-signal APS stub profile.
- **Tool / model:** Claude Code + premium-coding для CREATIVE; Cursor + fast-editing для IMPLEMENT.
- **New chat:** yes — creative завершена, следующий шаг IMPLEMENT.
