"""
Раскладка изделий на листе и рулоне.

Формулы адаптированы из js_legacy/calc/calcLayout.js.
Размеры — в миллиметрах.
"""

from __future__ import annotations

import math
from typing import Dict, Sequence


def _normalize_margins(margins: Sequence[float] | None) -> tuple[float, float, float, float]:
    """
    margins: [top, right, bottom, left] в мм.
    По умолчанию все отступы равны 0.
    """
    if margins is None:
        return 0.0, 0.0, 0.0, 0.0
    if len(margins) != 4:
        raise ValueError("margins must be [top, right, bottom, left]")
    top, right, bottom, left = margins
    return float(top), float(right), float(bottom), float(left)


def _pack_on_sheet(
    area_width: float,
    area_height: float,
    item_width: float,
    item_height: float,
    gap: float,
) -> tuple[int, int, int]:
    """
    Вспомогательная функция: раскладка в конкретной ориентации.
    Возвращает (num, cols, rows).
    """
    if area_width <= 0 or area_height <= 0:
        return 0, 0, 0

    step_w = item_width + gap
    step_h = item_height + gap
    if step_w <= 0 or step_h <= 0:
        return 0, 0, 0

    cols = int((area_width + gap) // step_w)
    rows = int((area_height + gap) // step_h)

    if cols <= 0 or rows <= 0:
        return 0, 0, 0

    num = cols * rows
    return num, cols, rows


def layout_on_sheet(
    item_size: Sequence[float],
    sheet_size: Sequence[float],
    margins: Sequence[float] | None = None,
    gap: float = 0.0,
) -> Dict[str, int]:
    """
    Оптимальная раскладка изделий на листе.

    item_size: [width, height] изделия в мм.
    sheet_size: [width, height] листа в мм.
    margins: [top, right, bottom, left] в мм.
    gap: расстояние между изделиями в мм.

    Пробует два варианта — без поворота и с поворотом изделия на 90°.
    Возвращает лучший: {"num": количество, "cols": столбцов, "rows": строк}.
    """
    if len(item_size) != 2 or len(sheet_size) != 2:
        raise ValueError("item_size and sheet_size must be [width, height]")

    item_w, item_h = map(float, item_size)
    sheet_w, sheet_h = map(float, sheet_size)
    gap = float(gap)

    top, right, bottom, left = _normalize_margins(margins)

    area_w = sheet_w - left - right
    area_h = sheet_h - top - bottom

    if area_w <= 0 or area_h <= 0:
        return {"num": 0, "cols": 0, "rows": 0}

    # Вариант 1: без поворота
    num1, cols1, rows1 = _pack_on_sheet(area_w, area_h, item_w, item_h, gap)
    # Вариант 2: с поворотом
    num2, cols2, rows2 = _pack_on_sheet(area_w, area_h, item_h, item_w, gap)

    if num2 > num1:
        return {"num": num2, "cols": cols2, "rows": rows2}

    return {"num": num1, "cols": cols1, "rows": rows1}


def layout_on_roll(
    quantity: int,
    item_size: Sequence[float],
    roll_size: Sequence[float],
    gap: float = 0.0,
) -> Dict[str, float]:
    """
    Оптимальная раскладка изделий на рулоне.

    quantity: нужное количество изделий.
    item_size: [width, height] изделия в мм.
    roll_size: [width, 0] рулона (height=0 означает рулон).
    gap: расстояние между изделиями в мм.

    Если изделие не помещается по ширине — пробует повернуть на 90°.
    Возвращает: {"num": фактическое количество, "length": длина отреза в мм}.
    """
    if len(item_size) != 2 or len(roll_size) != 2:
        raise ValueError("item_size and roll_size must be [width, height]")

    if quantity <= 0:
        return {"num": 0, "length": 0.0}

    item_w, item_h = map(float, item_size)
    roll_w = float(roll_size[0])
    gap = float(gap)

    if roll_w <= 0:
        return {"num": 0, "length": 0.0}

    def _variant(width_item: float, height_item: float) -> float | None:
        # Если вообще не помещается по ширине
        if width_item > roll_w:
            return None
        step_w = width_item + gap
        if step_w <= 0:
            return None
        cols = int((roll_w + gap) // step_w)
        if cols <= 0:
            return None
        rows = int(math.ceil(quantity / cols))
        length = rows * height_item + max(0, rows - 1) * gap
        return length

    # Вариант 1: без поворота
    length1 = _variant(item_w, item_h)
    # Вариант 2: с поворотом
    length2 = _variant(item_h, item_w)

    best_length: float | None

    if length1 is None and length2 is None:
        return {"num": 0, "length": 0.0}
    elif length1 is None:
        best_length = length2
    elif length2 is None:
        best_length = length1
    else:
        best_length = min(length1, length2)

    return {"num": int(quantity), "length": float(best_length)}

