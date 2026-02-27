"""
Наценки и общие параметры из data/common.json.
См. docs/common-json-reference.md.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List

import json5

_DATA_PATH = Path(__file__).parent.parent / "data" / "common.json"


def _load_data() -> Dict[str, Any]:
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        return json5.load(f)


_data: Dict[str, Any] = _load_data()

# Базовые константы
COST_OPERATOR: float = float(_data.get("costOperator", 1400))
MARGIN_MATERIAL: float = float(_data.get("marginMaterial", 0.6))
MARGIN_OPERATION: float = float(_data.get("marginOperation", 0.55))
MARGIN_MIN: float = float(_data.get("marginMin", 0.25))

BASE_TIME_READY: List[float] = list(_data.get("baseTimeReady", [24, 8, 1]))
BASE_TIME_READY_PRINT_SHEET: List[float] = list(
    _data.get("baseTimeReadyPrintSheet", BASE_TIME_READY)
)
BASE_TIME_READY_PRINT_OFFSET_PROMO: List[float] = list(
    _data.get("baseTimeReadyPrintOffsetPromo", BASE_TIME_READY)
)


def get_margin(key: str) -> float:
    """
    Вернуть значение наценки по ключу, например get_margin(\"marginLaser\").
    Если ключа нет — вернуть 0.0.
    """
    try:
        return float(_data.get(key, 0.0))
    except (TypeError, ValueError):
        return 0.0


def get_time_ready(key: str) -> List[float]:
    """
    Вернуть массив сроков по ключу (например, \"baseTimeReadyPrintSheet\").
    Если ключ отсутствует — вернуть BASE_TIME_READY.
    """
    value = _data.get(key)
    if isinstance(value, Iterable):
        return list(value)
    return list(BASE_TIME_READY)


def get_all_margins() -> Dict[str, Any]:
    """
    Вернуть словарь всех полей, начинающихся с \"margin\" (для отладки).
    """
    return {k: v for k, v in _data.items() if k.startswith("margin")}


def reload() -> None:
    """
    Перечитать common.json и обновить все константы.
    """
    global _data
    global COST_OPERATOR, MARGIN_MATERIAL, MARGIN_OPERATION, MARGIN_MIN
    global BASE_TIME_READY, BASE_TIME_READY_PRINT_SHEET, BASE_TIME_READY_PRINT_OFFSET_PROMO

    _data = _load_data()

    COST_OPERATOR = float(_data.get("costOperator", 1400))
    MARGIN_MATERIAL = float(_data.get("marginMaterial", 0.6))
    MARGIN_OPERATION = float(_data.get("marginOperation", 0.55))
    MARGIN_MIN = float(_data.get("marginMin", 0.25))

    BASE_TIME_READY = list(_data.get("baseTimeReady", [24, 8, 1]))
    BASE_TIME_READY_PRINT_SHEET = list(
        _data.get("baseTimeReadyPrintSheet", BASE_TIME_READY)
    )
    BASE_TIME_READY_PRINT_OFFSET_PROMO = list(
        _data.get("baseTimeReadyPrintOffsetPromo", BASE_TIME_READY)
    )

