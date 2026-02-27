from __future__ import annotations

from typing import Dict

from .base import EquipmentCatalog, EquipmentSpec
from .loader import load_generic_catalog, load_laser_catalog


def _safe_load_generic(filename: str) -> EquipmentCatalog:
    """
    Загрузить каталог оборудования, отлавливая ошибки формата JSON.

    Если загрузка/валидация падает — выводит предупреждение и
    возвращает пустой каталог нужной категории.
    """
    category = filename.rsplit(".", 1)[0]
    try:
        return load_generic_catalog(filename)
    except Exception as exc:  # noqa: BLE001
        print(f"[equipment] warning: failed to load {filename}: {exc}")
        return EquipmentCatalog(category=category)


# Лазеры — отдельная функция загрузчика
try:
    laser: EquipmentCatalog = load_laser_catalog()
except Exception as exc:  # noqa: BLE001
    print(f"[equipment] warning: failed to load laser.json: {exc}")
    laser = EquipmentCatalog(category="laser")


printer: EquipmentCatalog = _safe_load_generic("printer.json")
plotter: EquipmentCatalog = _safe_load_generic("plotter.json")
cutter: EquipmentCatalog = _safe_load_generic("cutter.json")
laminator: EquipmentCatalog = _safe_load_generic("laminator.json")
milling: EquipmentCatalog = _safe_load_generic("milling.json")
heatpress: EquipmentCatalog = _safe_load_generic("heatpress.json")
cards: EquipmentCatalog = _safe_load_generic("cards.json")
metalpins: EquipmentCatalog = _safe_load_generic("metalpins.json")
design: EquipmentCatalog = _safe_load_generic("design.json")
tools: EquipmentCatalog = _safe_load_generic("tools.json")


ALL_EQUIPMENT: Dict[str, EquipmentCatalog] = {
    "laser": laser,
    "printer": printer,
    "plotter": plotter,
    "cutter": cutter,
    "laminator": laminator,
    "milling": milling,
    "heatpress": heatpress,
    "cards": cards,
    "metalpins": metalpins,
    "design": design,
    "tools": tools,
}


def get_equipment(category: str, code: str) -> EquipmentSpec:
    """
    Получить оборудование по категории и коду.

    Пример:
        get_equipment("laser", "Qualitech11G1290")
    """
    try:
        catalog = ALL_EQUIPMENT[category]
    except KeyError as exc:
        raise KeyError(f"Unknown equipment category: {category!r}") from exc
    return catalog.get(code)


def get_all_equipment_options() -> Dict[str, Dict[str, str]]:
    """
    Все оборудование для отладки / API.

    Формат:
        {
            "laser": {"Qualitech11G1290": "Лазер ...", ...},
            "printer": {...},
            ...
        }
    """
    result: Dict[str, Dict[str, str]] = {}
    for category, catalog in ALL_EQUIPMENT.items():
        # Используем внутреннее хранилище каталога
        mapping: Dict[str, str] = {}
        for code, spec in catalog._items.items():  # type: ignore[attr-defined]
            mapping[code] = spec.name
        result[category] = mapping
    return result

