from __future__ import annotations

from typing import Dict

from .base import MaterialCatalog, MaterialSpec
from .loader import load_catalog

# Загружаем все каталоги материалов при импорте модуля.
hardsheet: MaterialCatalog = load_catalog("hardsheet.json")
roll: MaterialCatalog = load_catalog("roll.json")
sheet: MaterialCatalog = load_catalog("sheet.json")
offset_promo: MaterialCatalog = load_catalog("offset_promo.json")
laminat: MaterialCatalog = load_catalog("laminat.json")
profile: MaterialCatalog = load_catalog("profile.json")
presswall: MaterialCatalog = load_catalog("presswall.json")
calendar: MaterialCatalog = load_catalog("calendar.json")
magnet: MaterialCatalog = load_catalog("magnet.json")
keychain: MaterialCatalog = load_catalog("keychain.json")
mug: MaterialCatalog = load_catalog("mug.json")
misc: MaterialCatalog = load_catalog("misc.json")
epoxy: MaterialCatalog = load_catalog("epoxy.json")
attachment: MaterialCatalog = load_catalog("attachment.json")
pack: MaterialCatalog = load_catalog("pack.json")
pocket: MaterialCatalog = load_catalog("pocket.json")
flag: MaterialCatalog = load_catalog("flag.json")
pins: MaterialCatalog = load_catalog("pins.json")
tape: MaterialCatalog = load_catalog("tape.json")
plaque: MaterialCatalog = load_catalog("plaque.json")
puzzle: MaterialCatalog = load_catalog("puzzle.json")
pennant: MaterialCatalog = load_catalog("pennant.json")


ALL_MATERIALS: Dict[str, MaterialCatalog] = {
    "hardsheet": hardsheet,
    "roll": roll,
    "sheet": sheet,
    "offset_promo": offset_promo,
    "laminat": laminat,
    "profile": profile,
    "presswall": presswall,
    "calendar": calendar,
    "magnet": magnet,
    "keychain": keychain,
    "mug": mug,
    "misc": misc,
    "epoxy": epoxy,
    "attachment": attachment,
    "pack": pack,
    "pocket": pocket,
    "flag": flag,
    "pins": pins,
    "tape": tape,
    "plaque": plaque,
    "puzzle": puzzle,
    "pennant": pennant,
}


def get_material(category: str, code: str) -> MaterialSpec:
    """
    Получить материал по категории и коду.

    Пример:
        get_material("hardsheet", "PVC3")
    """
    try:
        catalog = ALL_MATERIALS[category]
    except KeyError as exc:
        raise KeyError(f"Unknown material category: {category!r}") from exc
    return catalog.get(code)


def get_all_options() -> Dict[str, list[dict]]:
    """
    Все материалы для выпадающих списков на сайте / в API.

    Формат:
        {
            "hardsheet": [...],
            "roll": [...],
            ...
        }
    где значение — результат catalog.list_for_frontend().
    """
    return {name: catalog.list_for_frontend() for name, catalog in ALL_MATERIALS.items()}

