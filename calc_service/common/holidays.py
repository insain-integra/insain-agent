"""
Праздничные и рабочие дни из data/common.json.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, Set

import json5

_DATA_PATH = Path(__file__).parent.parent / "data" / "common.json"


def _load_calendar() -> Dict[str, Any]:
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        data = json5.load(f)
    return data.get("calendar", {}) or {}


_calendar_data: Dict[str, Any] = _load_calendar()

# В JSON даты в формате "день.месяц", например "3.1"
HOLIDAYS: Set[str] = set(_calendar_data.get("workingDays", []))
EXTRA_WORK_DAYS: Set[str] = set(_calendar_data.get("weekEnd", []))


def _fmt(d: date) -> str:
    """Преобразовать дату в ключ формата 'день.месяц'."""
    return f"{d.day}.{d.month}"


def is_holiday(d: date) -> bool:
    """
    True если:
      - дата в HOLIDAYS и не в EXTRA_WORK_DAYS, или
      - суббота/воскресенье,
    False если дата в EXTRA_WORK_DAYS (выходной стал рабочим).
    """
    key = _fmt(d)
    if key in EXTRA_WORK_DAYS:
        return False
    if key in HOLIDAYS:
        return True
    # 5 = суббота, 6 = воскресенье
    if d.weekday() >= 5:
        return True
    return False


def is_working_day(d: date) -> bool:
    """Обратная функция к is_holiday."""
    return not is_holiday(d)


def next_working_day(d: date) -> date:
    """Следующий рабочий день после d."""
    current = d + timedelta(days=1)
    while not is_working_day(current):
        current += timedelta(days=1)
    return current


def add_working_hours(start: date, hours: float, hours_per_day: float = 8.0) -> date:
    """
    Добавить рабочие часы к дате и вернуть дату готовности.

    Логика:
      - 0 или отрицательное количество часов → вернуть start;
      - каждое посещение рабочего дня вычитает hours_per_day из остатка;
      - считаем только полные рабочие дни, начиная со следующего календарного дня.
    """
    if hours <= 0:
        return start

    remaining = hours
    current = start

    while remaining > 0:
        current += timedelta(days=1)
        if is_working_day(current):
            remaining -= hours_per_day

    return current


def reload() -> None:
    """Перечитать раздел calendar из common.json."""
    global _calendar_data, HOLIDAYS, EXTRA_WORK_DAYS
    _calendar_data = _load_calendar()
    HOLIDAYS = set(_calendar_data.get("workingDays", []))
    EXTRA_WORK_DAYS = set(_calendar_data.get("weekEnd", []))

