"""
Калькулятор НАСТОЛЬНЫХ ФЛАЖКОВ.

Мигрировано из js_legacy/calc/calcFlag.js.
Флажки: листовая печать на бумаге + скрепление скобами + установка на пластиковую палочку.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping

from calculators.base import BaseCalculator, ProductionMode
from calculators.print_sheet import PrintSheetCalculator
from common.markups import get_margin, get_time_ready
from materials import sheet as sheet_catalog
from common.process_tools import calc_set_staples, calc_set_shaft

DEFAULT_SHAFT_ID = "PlasticShaft380"


class FlagCalculator(BaseCalculator):
    """Настольные флажки: печать + скрепки + палочка."""

    slug = "flag"
    name = "Флажки"
    description = (
        "Расчёт настольных флажков: листовая печать на бумаге, "
        "скрепление скобами, установка на пластиковую палочку."
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
                    "description": "Количество флажков",
                    "validation": {"min": 1, "max": 100000},
                },
                {
                    "name": "width_mm",
                    "type": "number",
                    "required": True,
                    "title": "Ширина (мм)",
                    "description": "Ширина флажка",
                    "validation": {"min": 10, "max": 450},
                    "unit": "мм",
                },
                {
                    "name": "height_mm",
                    "type": "number",
                    "required": True,
                    "title": "Высота (мм)",
                    "description": "Высота флажка",
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
                    "width_mm": {"type": "number", "minimum": 1, "description": "Ширина флажка, мм"},
                    "height_mm": {"type": "number", "minimum": 1, "description": "Высота флажка, мм"},
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
        lamination_id = str(params.get("lamination_id", params.get("lamination", "")) or "").strip()
        mode = ProductionMode(int(params.get("mode", 1)))
        shaft_id = str(params.get("shaft_id", DEFAULT_SHAFT_ID) or DEFAULT_SHAFT_ID).strip() or DEFAULT_SHAFT_ID

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

        # 2. Скрепки (calcSetStaples)
        cost_staples = calc_set_staples(n, None, mode.value)

        # 3. Палочка (calcSetShaft)
        cost_shaft = calc_set_shaft(n, shaft_id, mode.value)

        # Итог (как в JS)
        cost = cost_print["cost"] + cost_staples.cost + cost_shaft.cost
        price_sum = cost_print["price"] + cost_staples.price + cost_shaft.price
        margin_flag = get_margin("marginFlag")
        price = math.ceil(price_sum * (1 + margin_flag))

        time_hours = math.ceil(
            (cost_print["time_hours"] + cost_staples.time_hours + cost_shaft.time_hours) * 100
        ) / 100.0
        time_ready = time_hours + max(
            cost_print.get("time_ready", 0),
            cost_staples.time_ready,
            cost_shaft.time_ready,
        )

        weight_kg = cost_print.get("weight_kg", 0) + cost_shaft.weight_kg

        materials_out: List[Dict[str, Any]] = []
        for m in cost_print.get("materials", []):
            materials_out.append({
                "code": m.get("code", ""),
                "name": m.get("name", ""),
                "title": m.get("title", ""),
                "quantity": m.get("quantity", 0),
                "unit": m.get("unit", "sheet"),
            })
        for m in cost_staples.materials:
            materials_out.append({
                "code": m.get("code", ""),
                "name": m.get("name", ""),
                "title": m.get("title", ""),
                "quantity": m.get("quantity", 0),
                "unit": m.get("unit", "шт"),
            })
        for m in cost_shaft.materials:
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
