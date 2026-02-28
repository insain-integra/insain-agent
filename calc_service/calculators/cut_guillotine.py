"""
Калькулятор гильотинной резки.

Перенесено из js_legacy/calc/calcCutGuillotine.js.
Параметры: количество листов, размер изделия, размер листа, материал, отступы, интервал, режим.
Результат: себестоимость и цена резки (материал не входит в расчёт).
"""

from __future__ import annotations

import math
from typing import Any, Dict, Mapping

from calculators.base import BaseCalculator, ProductionMode
from common.layout import layout_on_sheet
from common.markups import (
    BASE_TIME_READY,
    MARGIN_MIN,
    MARGIN_OPERATION,
    get_margin,
)
from equipment import cutter as cutter_catalog
from materials import get_material

CUTTER_CODE = "KWTrio3971"


class CutGuillotineCalculator(BaseCalculator):
    """Гильотинная резка: листы заданного формата режут на изделия."""

    slug = "cut_guillotine"
    name = "Гильотинная резка"
    description = "Расчёт стоимости резки листов на гильотине (размер изделия, размер листа, материал)."

    def get_options(self) -> Dict[str, Any]:
        materials_sheet = []
        for cat in ("sheet", "roll", "hardsheet"):
            try:
                from materials import ALL_MATERIALS
                catalog = ALL_MATERIALS.get(cat)
                if catalog:
                    materials_sheet.extend(catalog.list_for_frontend())
            except Exception:
                pass
        return {
            "materials": materials_sheet[:50] if materials_sheet else [],
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
                    "num_sheet": {"type": "integer", "minimum": 1, "description": "Количество листов для резки"},
                    "width": {"type": "number", "minimum": 1, "description": "Ширина изделия, мм"},
                    "height": {"type": "number", "minimum": 1, "description": "Высота изделия, мм"},
                    "sheet_width": {"type": "number", "minimum": 1, "description": "Ширина листа, мм"},
                    "sheet_height": {"type": "number", "minimum": 1, "description": "Высота листа, мм"},
                    "material_id": {"type": "string", "description": "Код материала (sheet/roll/hardsheet)"},
                    "material_category": {"type": "string", "enum": ["sheet", "roll", "hardsheet"], "description": "Категория материала"},
                    "margins": {"type": "array", "items": {"type": "number"}, "description": "[top, right, bottom, left] мм"},
                    "interval": {"type": "number", "minimum": 0, "description": "Интервал между изделиями, мм"},
                    "mode": {"type": "integer", "enum": [0, 1, 2], "description": "Режим: 0 эконом, 1 стандарт, 2 экспресс"},
                },
                "required": ["num_sheet", "width", "height", "sheet_width", "sheet_height"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        num_sheet = int(params.get("num_sheet", 1))
        size = [float(params.get("width", 0)), float(params.get("height", 0))]
        size_sheet = [float(params.get("sheet_width", 0)), float(params.get("sheet_height", 0))]
        material_id = str(params.get("material_id", "") or "").strip()
        material_category = str(params.get("material_category", "sheet") or "sheet")
        margins = params.get("margins")
        if margins is None or not isinstance(margins, (list, tuple)) or len(margins) != 4:
            margins = [0.0, 0.0, 0.0, 0.0]
        margins = [float(m) for m in margins]
        interval = float(params.get("interval", 0))
        mode = ProductionMode(int(params.get("mode", ProductionMode.STANDARD)))

        if size[0] <= 0 or size[1] <= 0 or size_sheet[0] <= 0 or size_sheet[1] <= 0:
            raise ValueError("width, height, sheet_width, sheet_height должны быть положительными")

        cutter = cutter_catalog.get(CUTTER_CODE)
        cutter_max = (cutter.max_size or [475, 650])[:2]
        layout_cutter = layout_on_sheet(size_sheet, cutter_max, [0, 0, 0, 0], 0.0)
        if layout_cutter["num"] == 0:
            raise ValueError("Листы не помещаются в резак")

        layout_sheet = layout_on_sheet(size, size_sheet, margins, interval)
        if layout_sheet["num"] == 0:
            raise ValueError("Изделия не помещаются на листе")

        density = 80.0
        if material_id:
            try:
                mat = get_material(material_category, material_id)
                density = float(mat.density or 80) if hasattr(mat, "density") else 80.0
            except Exception:
                pass

        num_sheet_80 = math.ceil(num_sheet * density / 80.0)
        max_sheet = getattr(cutter, "max_sheet", None) or 500
        if max_sheet <= 0:
            max_sheet = 500
        num_stack = math.ceil(num_sheet_80 / max_sheet)
        num_sheet_80 = num_sheet_80 / num_stack

        cols = layout_sheet.get("cols", 1) or 1
        rows = layout_sheet.get("rows", 1) or 1
        num_along_long = max(cols, rows)
        num_along_short = min(cols, rows)

        def hevisaid(a: float) -> int:
            return 0 if a == 0 else 1

        margin = [
            hevisaid(margins[0] + margins[2] + abs(size_sheet[1] - size[1])),
            hevisaid(margins[1] + margins[3] + abs(size_sheet[0] - size[0])),
            hevisaid(hevisaid(margins[0]) * hevisaid(margins[2]) + interval),
            hevisaid(hevisaid(margins[1]) * hevisaid(margins[3]) + interval),
        ]
        num_stack_long = math.ceil(num_along_long / max(1, math.floor(max_sheet / num_sheet_80)))
        num_stack_short = math.ceil(num_along_short / max(1, math.floor(max_sheet / num_sheet_80)))
        num_cut_long = num_along_long - 1 + (0 if interval == 0 else num_stack_long - 1) + num_stack_long * (num_along_short - 1 + (0 if interval == 0 else num_stack_short - 1))
        num_cut_short = num_along_short - 1 + (0 if interval == 0 else num_stack_short - 1) + num_stack_short * (num_along_long - 1 + (0 if interval == 0 else num_stack_long - 1))
        num_cut = (margin[0] + margin[1] + margin[2] + margin[3]) + min(num_cut_long, num_cut_short)
        num_cut = num_cut * num_stack

        cuts_per_hour = cutter.cuts_per_hour or 120.0
        time_prepare = (cutter.time_prepare or 0) * mode.value
        time_cut = num_cut / cuts_per_hour + time_prepare
        cost_dep = cutter.depreciation_per_hour * time_cut
        cost_process = num_cut * (cutter.cost_process or 0.3)
        cost_operator = time_cut * cutter.operator_cost_per_hour
        cost = math.ceil(cost_dep + cost_process + cost_operator)

        margin_extra = get_margin("marginCutGuillotine")
        effective_margin = max(MARGIN_OPERATION + margin_extra, MARGIN_MIN)
        price = math.ceil(cost * (1 + effective_margin))

        time_hours = math.ceil(time_cut * 100) / 100.0
        base_ready = cutter.base_time_ready if cutter.base_time_ready else BASE_TIME_READY
        idx = max(0, min(len(base_ready) - 1, int(mode.value)))
        time_ready = time_hours + float(base_ready[idx])

        return {
            "cost": float(cost),
            "price": float(price),
            "unit_price": float(price) / max(1, num_sheet),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": 0.0,
            "materials": [],
        }
