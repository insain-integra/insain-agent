from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import json5

from .base import MaterialCatalog, MaterialSpec


DATA_DIR = Path(__file__).parent.parent / "data" / "materials"


def normalize_sizes(size_data: Any) -> List[List[float]]:
    """
    Нормализовать поле size из JSON в список размеров.

    [] → []
    [3050, 2050] → [[3050, 2050]]
    [[3050, 2050], [2050, 1525]] → как есть
    [620, 0] → [[620, 0]]
    150 → [[150, 0]]  (специальный случай для ригелей и подобного)
    """
    if size_data is None or size_data == []:
        return []

    # Специальный случай: скалярная длина (например, Rigel: size = 150)
    if isinstance(size_data, (int, float)):
        return [[float(size_data), 0.0]]

    # Ожидаем список / кортеж
    if not isinstance(size_data, (list, tuple)):
        raise TypeError("size должен быть списком, кортежем или числом")

    if not size_data:
        return []

    first = size_data[0]

    # Формат [w, h]
    if isinstance(first, (int, float)):
        if len(size_data) < 2:
            raise ValueError("size должен содержать [width, height]")
        return [[float(size_data[0]), float(size_data[1])]]

    # Формат [[w, h], [w2, h2], ...]
    result: List[List[float]] = []
    for pair in size_data:
        if not isinstance(pair, (list, tuple)) or len(pair) < 2:
            raise ValueError("каждый элемент size должен быть [width, height]")
        result.append([float(pair[0]), float(pair[1])])
    return result


def parse_cost(raw_cost: Any) -> Tuple[Optional[float], Optional[List[Tuple[float, float]]]]:
    """
    Разобрать поле cost из JSON.

    750 → (750.0, None)
    [[10, 800], [50, 700]] → (None, [(10.0, 800.0), (50.0, 700.0)])
    """
    if raw_cost is None:
        return None, None

    # Фиксированная цена
    if isinstance(raw_cost, (int, float)):
        return float(raw_cost), None

    # Градированная цена
    if isinstance(raw_cost, (list, tuple)):
        tiers: List[Tuple[float, float]] = []
        for item in raw_cost:
            if not isinstance(item, (list, tuple)) or len(item) < 2:
                raise ValueError("каждая градация цены должна быть [threshold, value]")
            threshold, value = item[0], item[1]
            tiers.append((float(threshold), float(value)))
        return None, tiers

    raise TypeError("cost должен быть числом или списком [threshold, value]")


def load_catalog(filename: str) -> MaterialCatalog:
    """
    Загрузить каталог материалов из файла data/materials/{filename}.
    """
    path = DATA_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(path)

    with open(path, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = json5.load(f)

    # Имя категории — имя JSON-файла без расширения
    category = path.stem
    catalog = MaterialCatalog(category=category)

    for group_id, group_data in data.items():
        if not isinstance(group_data, dict):
            continue

        default = group_data.get("Default", {}) or {}

        for code, raw_spec in group_data.items():
            if code == "Default":
                continue
            if not isinstance(raw_spec, dict):
                continue

            merged: Dict[str, Any] = dict(default)
            merged.update(raw_spec)

            sizes = normalize_sizes(merged.get("size", []))
            min_size = merged.get("minSize")

            cost, cost_tiers = parse_cost(merged.get("cost"))

            is_roll = False
            if sizes:
                is_roll = any(sz[1] == 0 for sz in sizes)

            # roll_width: можно явно задать в JSON, иначе берём ширину первого размера для рулона
            roll_width: Optional[float] = merged.get("rollWidth")
            if roll_width is None and is_roll and sizes:
                roll_width = float(sizes[0][0])

            spec = MaterialSpec(
                code=code,
                group=group_id,
                name=merged.get("name", code),
                category=category,
                cost=cost,
                cost_tiers=cost_tiers,
                sizes=sizes,
                min_size=min_size,
                is_roll=is_roll,
                roll_width=roll_width,
                length_min=merged.get("lengthMin"),
                thickness=merged.get("thickness"),
                density=merged.get("density"),
                density_unit=merged.get("unitDensity", "гсм3"),
                weight_per_unit=merged.get("weightPerUnit"),
                available=bool(merged.get("available", True)),
            )

            catalog.add(spec)

    return catalog

