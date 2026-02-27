from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import json5

from common.currencies import parse_currency
from .base import EquipmentCatalog, EquipmentSpec, LaserSpec


DATA_DIR = Path(__file__).parent.parent / "data" / "equipment"


def _load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json5.load(f)


def _parse_time_load(value: Any) -> float:
    """
    Преобразовать timeLoad в одно число (часы).

    - число → float
    - [0.02, 0.05] → берём максимум (худший случай)
    - иначе → 0.0
    """
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, (list, tuple)) and value:
        try:
            return float(max(value))
        except TypeError:
            return 0.0
    return 0.0


def _parse_pairs(value: Any) -> Optional[List[Tuple[float, float]]]:
    """
    Преобразовать массив [[x, y], ...] в список пар (float, float).
    Если формат не массив пар — вернуть None.
    """
    if not isinstance(value, (list, tuple)) or not value:
        return None
    first = value[0]
    if not isinstance(first, (list, tuple)) or len(first) < 2:
        return None
    pairs: List[Tuple[float, float]] = []
    for item in value:
        if not isinstance(item, (list, tuple)) or len(item) < 2:
            continue
        pairs.append((float(item[0]), float(item[1])))
    return pairs or None


def load_laser_catalog() -> EquipmentCatalog:
    """
    Загрузить каталог лазеров из data/equipment/laser.json.
    """
    path = DATA_DIR / "laser.json"
    data = _load_json(path)

    catalog = EquipmentCatalog(category="laser")

    for code, raw in data.items():
        if not isinstance(raw, dict):
            continue

        defects = _parse_pairs(raw.get("defects"))
        cut_table = _parse_pairs(raw.get("cutPerHour"))
        grave_raw = raw.get("gravePerHour") or []
        grave_table: List[float] = [float(x) for x in grave_raw]

        # Стоимость оборудования и трубки могут быть в валюте
        raw_cost = raw.get("cost")
        if isinstance(raw_cost, (int, float, str)):
            purchase_cost = parse_currency(raw_cost)
        else:
            purchase_cost = 0.0

        raw_tube_cost = raw.get("costLaserTube")
        if isinstance(raw_tube_cost, (int, float, str)):
            laser_tube_cost = parse_currency(raw_tube_cost)
        else:
            laser_tube_cost = 0.0

        spec = LaserSpec(
            code=code,
            name=raw.get("name", code),
            category="laser",
            max_size=raw.get("maxSize"),
            margins=raw.get("margins"),
            purchase_cost=purchase_cost,
            depreciation_years=raw.get("timeDepreciation", 10.0),
            work_days_year=raw.get("workDay", 250),
            hours_per_day=raw.get("hoursDay", 4.0),
            cost_operator=raw.get("costOperator", 0.0),
            time_prepare=raw.get("timePrepare", 0.0),
            time_load=_parse_time_load(raw.get("timeLoad")),
            base_time_ready=raw.get("baseTimeReady"),
            defect_table=defects,
            cut_speed_table=cut_table or [],
            grave_speed_table=grave_table,
            laser_tube_cost=laser_tube_cost,
            laser_tube_life_hours=raw.get("lifeLaserTube", 1.0),
            power_cost_per_kwh=raw.get("costPower", 0.0),
            power_consumption_kwh=raw.get("powerPerHour", 0.0),
        )

        catalog.add(spec)

    return catalog


def load_generic_catalog(filename: str) -> EquipmentCatalog:
    """
    Загрузить каталог произвольного оборудования из data/equipment/{filename}.
    Использует базовую модель EquipmentSpec.
    """
    path = DATA_DIR / filename
    data = _load_json(path)

    category = path.stem
    catalog = EquipmentCatalog(category=category)

    for code, raw in data.items():
        if not isinstance(raw, dict):
            continue

        defects = _parse_pairs(raw.get("defects"))

        raw_cost = raw.get("cost")
        if isinstance(raw_cost, (int, float, str)):
            purchase_cost = parse_currency(raw_cost)
        else:
            purchase_cost = 0.0

        spec = EquipmentSpec(
            code=code,
            name=raw.get("name", code),
            category=category,
            max_size=raw.get("maxSize"),
            margins=raw.get("margins"),
            purchase_cost=purchase_cost,
            depreciation_years=raw.get("timeDepreciation", 10.0),
            work_days_year=raw.get("workDay", 250),
            hours_per_day=raw.get("hoursDay", 4.0),
            cost_operator=raw.get("costOperator", 0.0),
            time_prepare=raw.get("timePrepare", 0.0),
            time_load=_parse_time_load(raw.get("timeLoad")),
            base_time_ready=raw.get("baseTimeReady"),
            defect_table=defects,
            available=bool(raw.get("available", True)),
        )

        catalog.add(spec)

    return catalog

