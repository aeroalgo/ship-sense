"""OPC UA browse helpers.

AC-B3-03: browse адресного пространства → RawTagDescriptor list.
AC-B3-07: EUInformation → unit (verify vs map).
AC-B3-08: browse diff vs map → сигнал изменений (hook для B8/T7).
"""

from __future__ import annotations

import logging
from typing import Any

from asyncua import Client, ua
from asyncua.common import node

from collector.config.models import TagMapEntry
from collector.domain.models import RawTagDescriptor

logger = logging.getLogger(__name__)


async def browse_nodes(client: Client, root_node_id: Any = ua.ObjectIds.ObjectsFolder) -> list[RawTagDescriptor]:
    """
    Рекурсивный browse адресного пространства (ограниченная глубина для dev).

    Возвращает список RawTagDescriptor с native_id (NodeId строкой).
    Для production: ограничить depth / whitelist namespace.

    Args:
        client: подключённый asyncua Client.
        root_node_id: стартовая точка (по умолчанию ObjectsFolder).

    Returns:
        Список дескрипторов (native_id, name, datatype, unit, description).
    """
    root = client.get_node(root_node_id)
    descriptors: list[RawTagDescriptor] = []

    async def _walk(n: node.Node, depth: int = 0, max_depth: int = 3) -> None:
        if depth > max_depth:
            return
        try:
            children = await n.get_children()
            for child in children:
                try:
                    browse_name = await child.read_browse_name()
                    node_class = await child.read_node_class()
                    # Интересуют только Variable (теги данных)
                    if node_class != ua.NodeClass.Variable:
                        # Продолжаем рекурсию по объектам/папкам
                        await _walk(child, depth + 1, max_depth)
                        continue

                    native_id = str(child.nodeid)
                    name = browse_name.Name if browse_name else None

                    # datatype (локальное имя типа, если возможно)
                    datatype: str | None = None
                    try:
                        dt = await child.read_data_type_as_variant_type()
                        datatype = str(dt) if dt else None
                    except Exception:  # noqa: BLE001
                        pass

                    # unit из EUInformation (если есть)
                    unit: str | None = None
                    try:
                        eu = await child.read_attribute(ua.AttributeIds.EURange)  # type: ignore[attr-defined]
                        # EURange не даёт unit; ищем EUInformation в description или property
                        # Простейший путь: читаем EUInformation property если есть
                        eu_info = await _read_eu_information(child)
                        if eu_info and getattr(eu_info, "DisplayName", None):
                            unit = getattr(eu_info.DisplayName, "Text", None)
                    except Exception:  # noqa: BLE001, S110
                        pass

                    desc = await child.read_description()
                    description = getattr(desc, "Text", None) if desc else None

                    descriptors.append(
                        RawTagDescriptor(
                            native_id=native_id,
                            name=name,
                            unit=unit,
                            datatype=datatype,
                            description=description,
                        )
                    )
                except Exception:  # noqa: BLE001, S110
                    # Один узел не должен ронять весь browse
                    logger.debug("skip node during browse: %s", child, exc_info=True)
                    continue
        except Exception:  # noqa: BLE001, S110
            logger.debug("browse walk error at depth %s", depth, exc_info=True)

    await _walk(root)
    return descriptors


async def _read_eu_information(n: node.Node) -> Any | None:
    """Попытка прочитать EUInformation property узла (если сервер отдаёт)."""
    try:
        # Ищем property EngineeringUnits (стандарт OPC UA)
        eu_prop = await n.get_child("2:EngineeringUnits")
        if eu_prop:
            val = await eu_prop.read_value()
            return val
    except Exception:  # noqa: BLE001, S110
        pass
    return None


def browse_diff(
    discovered: list[RawTagDescriptor], tag_map: list[TagMapEntry]
) -> tuple[list[str], list[str]]:
    """
    Сравнить discovered (из browse) с tag_map (из конфига).

    Returns:
        (added, removed) — списки native_id (node_id).
    """
    discovered_ids = {d.native_id for d in discovered}
    mapped_ids = {e.node_id or e.native_id for e in tag_map}

    added = sorted(discovered_ids - mapped_ids)
    removed = sorted(mapped_ids - discovered_ids)
    return added, removed
