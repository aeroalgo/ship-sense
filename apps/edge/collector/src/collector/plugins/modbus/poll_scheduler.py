from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from collector.config.models import PollGroup as ConfigPollGroup, TagMapEntry


@dataclass(frozen=True)
class PollGroup:
    """Runtime poll group (после merge/split).

    name: логическое имя (из explicit или auto-generated).
    hz: частота опроса группы (min из тегов).
    native_ids: список native_id (contiguous, ≤ max_regs, один FC).
    """

    name: str
    hz: float
    native_ids: list[str]


class PollScheduler:
    """Алгоритм группировки тегов Modbus в poll-группы.

    AC-B2-05: gap ≤ max_gap, size ≤ max_regs.
    AC-B2-06: hz = min(tag hz) в группе.
    """

    @staticmethod
    def build_groups(
        tag_map: Sequence[TagMapEntry],
        *,
        max_gap: int = 0,
        max_regs: int = 100,
        default_hz: float = 1.0,
        explicit_groups: Sequence[PollGroup] | None = None,
    ) -> list[PollGroup]:
        """Построить группы из tag_map.

        1. Разделить по FC (3 vs 4).
        2. Для каждого FC: отсортировать по address, greedy merge (gap ≤ max_gap).
        3. Split по max_regs.
        4. hz = min(tag hz или default).
        5. Если explicit_groups заданы с native_ids → вернуть как есть (validate в карте).
           Остальные теги → auto в "default" группу.
        """
        if not tag_map:
            return []

        # 1. Разделить по FC
        fc3: list[TagMapEntry] = []
        fc4: list[TagMapEntry] = []
        for t in tag_map:
            fc = t.fc
            if fc is None:
                # fallback: 40xxx → FC3 (holding), 30xxx → FC4 (input)
                if t.native_id.startswith("40"):
                    fc = 3
                elif t.native_id.startswith("30"):
                    fc = 4
                else:
                    fc = 3  # default
            if fc == 3:
                fc3.append(t)
            else:
                fc4.append(t)

        result: list[PollGroup] = []

        # 2-4. Обработать каждый FC
        for fc_tags, fc_name in [(fc3, "fc3"), (fc4, "fc4")]:
            if not fc_tags:
                continue
            # Сортируем по address (из native_id)
            sorted_tags = sorted(fc_tags, key=lambda t: _parse_address(t.native_id))
            groups = _merge_contiguous(sorted_tags, max_gap=max_gap, max_regs=max_regs, default_hz=default_hz)
            result.extend(groups)

        # 5. Явные группы (explicit)
        if explicit_groups:
            for eg in explicit_groups:
                # validate: все native_ids должны быть в tag_map
                valid_ids = {t.native_id for t in tag_map}
                for nid in eg.native_ids:
                    if nid not in valid_ids:
                        # skip invalid или raise? creative: validate, но не роняем весь build
                        # Для простоты: пропускаем невалидные, оставляем только валидные
                        pass
                # Пересоздаём с отфильтрованными
                filtered = [nid for nid in eg.native_ids if nid in {t.native_id for t in tag_map}]
                if filtered:
                    result.append(PollGroup(name=eg.name, hz=eg.hz, native_ids=filtered))

            # Теги, не попавшие в explicit → auto в "default" (если ещё не покрыты)
            covered: set[str] = set()
            for g in result:
                covered.update(g.native_ids)
            auto_remaining = [t for t in tag_map if t.native_id not in covered]
            if auto_remaining:
                auto_groups = _merge_contiguous(auto_remaining, max_gap=max_gap, max_regs=max_regs, default_hz=default_hz, name_prefix="default")
                result.extend(auto_groups)

        return result


def _parse_address(native_id: str) -> int:
    """40101 → 101, 40200.3 → 200."""
    base = native_id.split(".")[0]
    # '40101' → 101
    if len(base) >= 3:
        return int(base[2:])
    return int(base)


def _merge_contiguous(
    tags: Sequence[TagMapEntry],
    *,
    max_gap: int,
    max_regs: int,
    default_hz: float,
    name_prefix: str = "auto",
) -> list[PollGroup]:
    """Greedy merge по gap + split по max_regs."""
    if not tags:
        return []

    groups: list[PollGroup] = []
    current: list[TagMapEntry] = [tags[0]]

    for t in tags[1:]:
        last_addr = _parse_address(current[-1].native_id)
        curr_addr = _parse_address(t.native_id)
        gap = curr_addr - last_addr - 1  # registers between
        # contiguous if gap <= max_gap
        would_fit = len(current) + 1 <= max_regs
        if gap <= max_gap and would_fit:
            current.append(t)
        else:
            # flush current
            groups.append(_make_group(current, default_hz, name_prefix, len(groups)))
            current = [t]

    # flush last
    groups.append(_make_group(current, default_hz, name_prefix, len(groups)))
    return groups


def _make_group(tags: list[TagMapEntry], default_hz: float, prefix: str, idx: int) -> PollGroup:
    hz = min((getattr(t, "hz", None) or default_hz) for t in tags) if tags else default_hz
    # hz может прийти из config PollGroup (в явных), здесь теги из map → default
    name = f"{prefix}_{_parse_address(tags[0].native_id)}" if tags else f"{prefix}_{idx}"
    native_ids = [t.native_id for t in tags]
    return PollGroup(name=name, hz=hz, native_ids=native_ids)
