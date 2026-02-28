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


def _first_process_per_hour(value: Any) -> float:
    """
    Из processPerHour (таблица [[толщина, скорость], ...] или число) вернуть скорость.
    """
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, (list, tuple)) and value:
        first = value[0]
        if isinstance(first, (list, tuple)) and len(first) >= 2:
            return float(first[1])
    return 0.0


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


def _to_float(value: Any, default: float = 0.0) -> float:
    """
    Преобразовать значение в float. Если список — взять первый элемент или default.
    (В printer.json/tools.json costProcess иногда массив, напр. [1300, 800, 800].)
    """
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, (list, tuple)) and value:
        try:
            return float(value[0])
        except (TypeError, ValueError):
            return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


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

        raw_defects = raw.get("defects")
        if isinstance(raw_defects, (int, float)):
            defects = [(0.0, float(raw_defects)), (1e9, float(raw_defects))]
        else:
            defects = _parse_pairs(raw_defects)

        raw_cost = raw.get("cost")
        if isinstance(raw_cost, (int, float, str)):
            purchase_cost = parse_currency(raw_cost)
        else:
            purchase_cost = 0.0

        raw_pph = raw.get("processPerHour")
        pph_table = _parse_pairs(raw_pph) if isinstance(raw_pph, (list, tuple)) and raw_pph and isinstance(raw_pph[0], (list, tuple)) else None
        raw_mph = raw.get("meterPerHour")
        mph_table = _parse_pairs(raw_mph) if isinstance(raw_mph, (list, tuple)) and raw_mph and isinstance(raw_mph[0], (list, tuple)) else None
        mph_single = float(raw_mph) if isinstance(raw_mph, (int, float)) else 0.0

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
            time_load_sheet=_to_float(raw.get("timeLoadSheet")),
            time_find_mark=_to_float(raw.get("timeFindMark")),
            base_time_ready=raw.get("baseTimeReady"),
            defect_table=defects,
            available=bool(raw.get("available", True)),
            cost_process=_to_float(raw.get("costProcess")),
            cuts_per_hour=_to_float(raw.get("cutsPerHour")),
            process_per_hour=_first_process_per_hour(raw_pph),
            process_per_hour_table=pph_table,
            max_sheet=int(raw.get("maxSheet", 0) or 0),
            meter_per_hour=mph_single,
            meter_per_hour_table=mph_table,
        )

        catalog.add(spec)

    return catalog

