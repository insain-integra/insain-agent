"""
Калькулятор БУМАЖНЫХ ВЫМПЕЛОВ.

Мигрировано из js_legacy/calc/calcPennant.js.
Вымпелы: листовая печать + пробивка отверстий (2 на изделие) + установка шнура.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping

from calculators.base import BaseCalculator, ProductionMode
from calculators.print_sheet import PrintSheetCalculator
from common.markups import get_margin, get_time_ready
from materials import sheet as sheet_catalog
from common.process_tools import calc_punching, calc_set_rope

DEFAULT_ROPE_ID = "RopeForPack"
NUM_HOLES_PER_ITEM = 2  # как в JS: isHole = 2


class PennantCalculator(BaseCalculator):
    """Бумажные вымпелы: печать + пробивка отверстий + шнур."""

    slug = "pennant"
    name = "Вымпелы"
    description = (
        "Расчёт бумажных вымпелов: листовая печать, "
        "пробивка отверстий для шнура, установка шнура."
    )

    def get_param_schema(self) -> Dict[str, Any]:
        return {
            "slug": self.slug,
            "title": self.name,
            "params": [
                {
                    "name": "quantity",
                    "type": "integer",
                    "required": True,
                    "title": "Тираж",
                    "description": "Количество вымпелов",
                    "validation": {"min": 1, "max": 100000},
                },
                {
                    "name": "width_mm",
                    "type": "number",
                    "required": True,
                    "title": "Ширина (мм)",
                    "description": "Ширина вымпела",
                    "validation": {"min": 10, "max": 450},
                    "unit": "мм",
                },
                {
                    "name": "height_mm",
                    "type": "number",
                    "required": True,
                    "title": "Высота (мм)",
                    "description": "Высота вымпела",
                    "validation": {"min": 10, "max": 450},
                    "unit": "мм",
                },
                {
                    "name": "material",
                    "type": "enum_cascading",
                    "required": True,
                    "title": "Бумага",
                    "description": "Тип бумаги для печати",
                    "choices": {"source": "materials:sheet"},
                },
                {
                    "name": "color",
                    "type": "enum",
                    "required": True,
                    "default": "4+0",
                    "title": "Цветность",
                    "choices": {
                        "inline": [
                            {"id": "1+0", "title": "1+0"},
                            {"id": "4+0", "title": "4+0"},
                            {"id": "1+1", "title": "1+1"},
                            {"id": "4+1", "title": "4+1"},
                            {"id": "4+4", "title": "4+4"},
                        ]
                    },
                },
                {
                    "name": "lamination",
                    "type": "enum",
                    "required": False,
                    "title": "Ламинация",
                    "choices": {"source": "materials:laminat"},
                },
                {
                    "name": "mode",
                    "type": "enum",
                    "required": False,
                    "default": int(ProductionMode.STANDARD),
                    "title": "Режим",
                    "choices": {
                        "inline": [
                            {"id": 0, "title": "Эконом"},
                            {"id": 1, "title": "Стандарт"},
                            {"id": 2, "title": "Экспресс"},
                        ]
                    },
                },
            ],
            "param_groups": {
                "main": ["quantity", "width_mm", "height_mm"],
                "material": ["material"],
                "processing": ["color", "lamination"],
                "mode": ["mode"],
            },
        }

    def get_options(self) -> Dict[str, Any]:
        materials = sheet_catalog.list_for_frontend()
        return {
            "materials": materials[:60],
            "colors": ["1+0", "4+0", "1+1", "4+1", "4+4"],
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
                    "quantity": {"type": "integer", "minimum": 1, "description": "Тираж, шт."},
                    "width_mm": {"type": "number", "minimum": 1, "description": "Ширина вымпела, мм"},
                    "height_mm": {"type": "number", "minimum": 1, "description": "Высота вымпела, мм"},
                    "material_id": {"type": "string", "description": "Код бумаги (sheet)"},
                    "color": {"type": "string", "description": "Цветность: 1+0, 4+0, 1+1, 4+1, 4+4"},
                    "lamination_id": {"type": "string", "description": "Код плёнки ламинации (пусто — без ламинации)"},
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["quantity", "width_mm", "height_mm", "material_id"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        n = int(params.get("quantity", 1))
        width = float(params.get("width_mm", params.get("width", 0)))
        height = float(params.get("height_mm", params.get("height", 0)))
        size = [width, height]
        material_id = str(params.get("material_id") or params.get("material") or "").strip()
        color = str(params.get("color", "4+0") or "4+0").strip()
        lamination_id = str(params.get("lamination_id") or params.get("lamination", "") or "").strip()
        mode = ProductionMode(int(params.get("mode", 1)))
        rope_id = str(params.get("rope_id", DEFAULT_ROPE_ID) or DEFAULT_ROPE_ID).strip() or DEFAULT_ROPE_ID

        if n < 1:
            return self._empty_result(mode)

        # 1. Печать (calcPrintSheet)
        print_calc = PrintSheetCalculator()
        print_params = {
            "quantity": n,
            "width": width,
            "height": height,
            "material_id": material_id,
            "color": color,
            "mode": mode.value,
        }
        if lamination_id:
            print_params["lamination_id"] = lamination_id
        try:
            cost_print = print_calc.calculate(print_params)
        except (KeyError, ValueError):
            return self._empty_result(mode)

        # 2. Пробивка отверстий (2 на изделие, как в JS isHole=2)
        cost_punching = calc_punching(n * NUM_HOLES_PER_ITEM, material_id, mode.value)

        # 3. Установка шнура (calcSetRope)
        cost_rope = calc_set_rope(n, rope_id, mode.value)

        # Итог (как в JS)
        cost = cost_print["cost"] + cost_punching.cost + cost_rope.cost
        price_sum = cost_print["price"] + cost_punching.price + cost_rope.price
        margin_pennant = get_margin("marginPennantPaper")
        price = math.ceil(price_sum * (1 + margin_pennant))

        time_hours = math.ceil(
            (cost_print["time_hours"] + cost_punching.time_hours + cost_rope.time_hours) * 100
        ) / 100.0
        time_ready = time_hours + max(
            cost_print.get("time_ready", 0),
            cost_punching.time_ready,
            cost_rope.time_ready,
        )

        weight_kg = cost_print.get("weight_kg", 0) + cost_rope.weight_kg

        materials_out: List[Dict[str, Any]] = []
        for m in cost_print.get("materials", []):
            materials_out.append({
                "code": m.get("code", ""),
                "name": m.get("name", ""),
                "title": m.get("title", ""),
                "quantity": m.get("quantity", 0),
                "unit": m.get("unit", "sheet"),
            })
        for m in cost_rope.materials:
            materials_out.append({
                "code": m.get("code", ""),
                "name": m.get("name", ""),
                "title": m.get("title", ""),
                "quantity": m.get("quantity", 0),
                "unit": m.get("unit", "шт"),
            })

        return {
            "cost": float(cost),
            "price": int(price),
            "unit_price": float(price) / max(1, n),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": weight_kg,
            "materials": materials_out,
        }

    def _empty_result(self, mode: ProductionMode) -> Dict[str, Any]:
        btr = get_time_ready("baseTimeReadyPrintSheet")
        idx = max(0, min(len(btr) - 1, mode.value))
        return {
            "cost": 0.0,
            "price": 0,
            "unit_price": 0.0,
            "time_hours": 0.0,
            "time_ready": float(btr[idx]),
            "weight_kg": 0.0,
            "materials": [],
        }
