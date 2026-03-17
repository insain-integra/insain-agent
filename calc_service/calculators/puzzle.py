"""
Калькулятор ПАЗЛОВ.

Мигрировано из js_legacy/calc/calcPuzzle.js.
Пазлы с сублимационной печатью: заготовка + печать на сублимационной бумаге + термоперенос.
В текущей версии puzzle.json содержит только пазлы с applicationID=isSublimation.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Mapping

import json5

from calculators.base import BaseCalculator, ProductionMode
from calculators.print_sheet import PrintSheetCalculator
from common.markups import BASE_TIME_READY, COST_OPERATOR, MARGIN_MATERIAL, MARGIN_OPERATION, get_margin
from materials import puzzle as puzzle_catalog

PUZZLE_JSON = Path(__file__).parent.parent / "data" / "materials" / "puzzle.json"
SUBLIMATION_PAPER = "PaperSublimation128"
TIME_PRESS_PER_ITEM = 35 / 3600  # 35 сек в часах


def _load_puzzle_raw() -> Dict[str, Any]:
    """Загрузить сырые данные пазлов (sizePrint, applicationID)."""
    with open(PUZZLE_JSON, "r", encoding="utf-8") as f:
        return json5.load(f)


def _get_puzzle_config(puzzle_id: str) -> Dict[str, Any]:
    """Получить конфиг пазла по коду (size, sizePrint, applicationID, cost, weight)."""
    data = _load_puzzle_raw()
    for group_id, group_data in data.items():
        if not isinstance(group_data, dict):
            continue
        default = group_data.get("Default", {}) or {}
        for code, raw in group_data.items():
            if code == "Default":
                continue
            if code == puzzle_id:
                merged = dict(default)
                merged.update(raw)
                merged["_group"] = group_id
                return merged
    raise KeyError(f"Пазл {puzzle_id!r} не найден")


class PuzzleCalculator(BaseCalculator):
    """Пазлы с сублимационной печатью."""

    slug = "puzzle"
    name = "Пазлы"
    description = "Расчёт пазлов с сублимационной печатью: заготовка + печать + термоперенос."

    def get_options(self) -> Dict[str, Any]:
        materials = puzzle_catalog.list_for_frontend()
        return {
            "materials": materials,
            "modes": [
                {"value": ProductionMode.ECONOMY, "label": "Экономичный"},
                {"value": ProductionMode.STANDARD, "label": "Стандартный"},
                {"value": ProductionMode.EXPRESS, "label": "Экспресс"},
            ],
        }

    def get_tool_schema(self) -> Dict[str, Any]:
        return {
            "name": "calc_" + self.slug,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "quantity": {"type": "integer", "minimum": 1, "description": "Тираж"},
                    "puzzle_id": {"type": "string", "description": "Код пазла (Puzzle300420, Puzzle208298, Puzzle159215)"},
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["quantity", "puzzle_id"],
            },
        }

    def get_param_schema(self) -> Dict[str, Any]:
        return {
            "slug": self.slug,
            "title": self.name,
            "params": [
                {"name": "quantity", "type": "integer", "required": True, "title": "Тираж", "validation": {"min": 1}},
                {"name": "puzzle_id", "type": "enum_cascading", "required": True, "title": "Тип пазла", "choices": {"source": "materials:puzzle"}},
                {"name": "mode", "type": "enum", "required": False, "default": 1, "title": "Режим",
                 "choices": {"inline": [{"id": 0, "title": "Эконом"}, {"id": 1, "title": "Стандарт"}, {"id": 2, "title": "Экспресс"}]}},
            ],
            "param_groups": {"main": ["quantity", "puzzle_id"], "mode": ["mode"]},
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        n = int(params.get("quantity", 1))
        puzzle_id = str(params.get("puzzle_id", "")).strip()
        mode = ProductionMode(int(params.get("mode", 1)))

        if not puzzle_id:
            raise ValueError("Не указан тип пазла (puzzle_id)")

        config = _get_puzzle_config(puzzle_id)
        application_id = config.get("applicationID", "")

        if application_id != "isSublimation":
            raise ValueError(
                f"Пазл {puzzle_id!r}: поддерживается только сублимационная печать (isSublimation). "
                "UV-печать и гравировка будут добавлены после миграции calcTablets."
            )

        puzzle_cost = float(config.get("cost", 0))
        puzzle_weight = float(config.get("weight", 0))
        size = config.get("size", [0, 0])
        size_print = config.get("sizePrint", size)

        try:
            material = puzzle_catalog.get(puzzle_id)
        except KeyError:
            raise ValueError(f"Пазл {puzzle_id!r} не найден в каталоге")

        # Стоимость заготовок
        cost_puzzle = puzzle_cost * n
        price_puzzle = cost_puzzle * (1 + MARGIN_MATERIAL)
        weight_kg = puzzle_weight * n

        materials_out: List[Dict[str, Any]] = [{
            "code": puzzle_id,
            "name": material.description,
            "title": material.title,
            "quantity": n,
            "unit": "шт",
            "size_mm": size,
        }]

        # Упаковка: 0.006 ч на изделие
        time_packing = 0.006 * n
        cost_packing = time_packing * COST_OPERATOR
        price_packing = cost_packing * (1 + MARGIN_OPERATION)

        # Сублимация: печать на бумаге + термоперенос
        print_calc = PrintSheetCalculator()
        print_result = print_calc.calculate({
            "quantity": n,
            "width": size_print[0],
            "height": size_print[1],
            "material_id": SUBLIMATION_PAPER,
            "color": "4+0",
            "lamination_id": "",
            "mode": mode.value,
        })

        cost_application = float(print_result.get("cost", 0))
        price_application = float(print_result.get("price", 0))
        time_application = float(print_result.get("time_hours", 0))
        time_ready_application = float(print_result.get("time_ready", 0))

        # Время термопереноса: 35 сек на изделие
        time_press = n * TIME_PRESS_PER_ITEM
        cost_press = time_press * COST_OPERATOR
        price_press = cost_press * (1 + get_margin("marginHeatPress"))
        cost_application += cost_press
        price_application += price_press
        time_application += time_press

        materials_out.extend(print_result.get("materials", []))

        # Итог
        cost = cost_puzzle + cost_packing + cost_application
        price = (price_puzzle + price_packing + price_application) * (1 + get_margin("marginPuzzle"))
        time_hours = time_packing + time_application
        time_ready = time_hours + max(time_ready_application, float(BASE_TIME_READY[min(mode.value, len(BASE_TIME_READY) - 1)]))

        return {
            "cost": math.ceil(cost),
            "price": math.ceil(price),
            "unit_price": math.ceil(price) / max(1, n),
            "time_hours": math.ceil(time_hours * 100) / 100,
            "time_ready": time_ready,
            "weight_kg": round(weight_kg, 2),
            "materials": materials_out,
        }
