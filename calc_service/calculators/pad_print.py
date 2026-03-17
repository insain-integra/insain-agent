"""
Калькулятор тампопечати.

Перенесено из js_legacy/calc/calcPadPrint.js.
Тампопечать на изделиях: клише + краски + тампоны + УФ-сушка.
"""

from __future__ import annotations

import json5
import math
from pathlib import Path
from typing import Any, Dict, List, Mapping

from calculators.base import BaseCalculator, ProductionMode
from common.currencies import parse_currency, usd_to_rub
from common.markups import COST_OPERATOR, MARGIN_MATERIAL, MARGIN_OPERATION, get_margin

_TOOLS_JSON = Path(__file__).parent.parent / "data" / "equipment" / "tools.json"


def _load_tools_raw() -> Dict[str, Any]:
    with open(_TOOLS_JSON, "r", encoding="utf-8") as f:
        return json5.load(f)


def _find_defect(defects_table: List[List[float]], n: int) -> float:
    """Найти процент брака по таблице [[порог, доля], ...]."""
    if not defects_table:
        return 0.0
    for threshold, rate in sorted(defects_table, key=lambda x: x[0]):
        if n <= threshold:
            return float(rate)
    return float(defects_table[-1][1]) if defects_table else 0.0


class PadPrintCalculator(BaseCalculator):
    """Тампопечать на изделиях."""

    slug = "pad_print"
    name = "Тампопечать"
    description = "Расчёт стоимости тампопечати на пластике, металле, стекле и др."

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
                    "description": "Количество изделий",
                    "validation": {"min": 1, "max": 100000},
                },
                {
                    "name": "size_item",
                    "type": "string",
                    "required": False,
                    "default": "isSmallItems",
                    "title": "Размер изделия",
                    "description": "Малые или крупные изделия (влияет на скорость)",
                    "choices": {
                        "inline": [
                            {"id": "isSmallItems", "title": "Малые (до 50 мм)"},
                            {"id": "isLargeItems", "title": "Крупные (более 50 мм)"},
                        ]
                    },
                },
                {
                    "name": "width_mm",
                    "type": "number",
                    "required": False,
                    "title": "Ширина (мм)",
                    "description": "Ширина области печати (если задан массив — макс. размер)",
                    "unit": "мм",
                },
                {
                    "name": "height_mm",
                    "type": "number",
                    "required": False,
                    "title": "Высота (мм)",
                    "unit": "мм",
                },
                {
                    "name": "depth_mm",
                    "type": "number",
                    "required": False,
                    "title": "Глубина (мм)",
                    "unit": "мм",
                },
                {
                    "name": "color",
                    "type": "integer",
                    "required": True,
                    "default": 1,
                    "title": "Количество цветов",
                    "description": "1 или 2",
                    "validation": {"min": 1, "max": 2},
                },
                {
                    "name": "is_pantone",
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "title": "Пантон",
                    "description": "Смешивание краски по пантону",
                },
                {
                    "name": "is_packing",
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "title": "Упаковка",
                    "description": "Распаковка и упаковка изделий",
                },
                {
                    "name": "material_mode",
                    "type": "string",
                    "required": False,
                    "default": "isMaterial",
                    "title": "Материал",
                    "description": "Наш материал или заказчика",
                    "choices": {
                        "inline": [
                            {"id": "isMaterial", "title": "Наш материал"},
                            {"id": "isMaterialCustomer", "title": "Материал заказчика"},
                        ]
                    },
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
                "main": ["quantity", "color"],
                "options": ["size_item", "is_pantone", "is_packing", "material_mode"],
                "mode": ["mode"],
            },
        }

    def get_options(self) -> Dict[str, Any]:
        return {
            "size_items": [
                {"id": "isSmallItems", "title": "Малые (до 50 мм)"},
                {"id": "isLargeItems", "title": "Крупные (более 50 мм)"},
            ],
            "colors": [1, 2],
            "modes": [
                {"value": 0, "label": "Экономичный"},
                {"value": 1, "label": "Стандартный"},
                {"value": 2, "label": "Экспресс"},
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
                    "size_item": {
                        "type": "string",
                        "enum": ["isSmallItems", "isLargeItems"],
                        "description": "Размер изделия",
                    },
                    "width_mm": {"type": "number", "description": "Ширина области печати, мм"},
                    "height_mm": {"type": "number", "description": "Высота, мм"},
                    "depth_mm": {"type": "number", "description": "Глубина, мм"},
                    "color": {"type": "integer", "minimum": 1, "maximum": 2, "description": "Количество цветов"},
                    "is_pantone": {"type": "boolean", "description": "Смешивание по пантону"},
                    "is_packing": {"type": "boolean", "description": "Упаковка"},
                    "material_mode": {
                        "type": "string",
                        "enum": ["isMaterial", "isMaterialCustomer"],
                        "description": "Материал: наш или заказчика",
                    },
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["quantity", "color"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        quantity = int(params.get("quantity", 1))
        size_item = str(params.get("size_item", "isSmallItems") or "isSmallItems").strip()
        width = float(params.get("width_mm", 0) or params.get("width", 0))
        height = float(params.get("height_mm", 0) or params.get("height", 0))
        depth = float(params.get("depth_mm", 0) or params.get("depth", 0))
        color = int(params.get("color", 1) or 1)
        is_pantone = bool(params.get("is_pantone", False))
        is_packing = bool(params.get("is_packing", False))
        material_mode = str(params.get("material_mode", "isMaterial") or "isMaterial").strip()
        mode = ProductionMode(int(params.get("mode", 1)))

        raw = _load_tools_raw()
        tool = raw.get("TIC177")
        camera = raw.get("TICUV300")
        if not tool or not camera:
            raise ValueError("Не обнаружены данные для оборудования тампопечати в tools.json")

        base_time_ready = tool.get("baseTimeReady") or [24, 8, 1]
        idx = max(0, min(len(base_time_ready) - 1, math.ceil(mode.value)))
        base_ready = float(base_time_ready[idx])

        diff_print = 0
        if width > 0 and height > 0 and depth > 0:
            if max(width, height, depth) > 50:
                diff_print = 1
        else:
            diff_print = 1 if size_item == "isLargeItems" else 0

        process_per_hour_arr = tool.get("processPerHour", [300, 100])
        process_per_hour = float(
            process_per_hour_arr[diff_print]
            if isinstance(process_per_hour_arr, (list, tuple)) and len(process_per_hour_arr) > diff_print
            else process_per_hour_arr[0] if isinstance(process_per_hour_arr, (list, tuple)) else 300
        )

        defects_table = tool.get("defects", [[10000000, 0.01]])
        defects = _find_defect(defects_table, quantity)
        if mode.value > 1:
            defects += defects * (mode.value - 1)

        cost_cliche_usd = float(tool.get("costCliche", 5.0))
        cost_small = tool.get("costSmallTampon", [15, 0.00001, 0.01])
        cost_large = tool.get("costLargeTampon", [30, 0.00001, 0.02])
        cost_paint = tool.get("costPaint", [100, 0.013, 0.001])
        cost_solvent = tool.get("costSolvent", [28, 0.004, 0.001])
        cost_cleaner = tool.get("costCleaner", [52, 0.0025, 0.0])
        cost_film = tool.get("costFilm", [15, 0.01, 0.0])

        def _material_cost(arr: List[float]) -> float:
            price_usd = float(arr[0]) if arr else 0
            min_use = float(arr[1]) if len(arr) > 1 else 0
            per_100 = float(arr[2]) if len(arr) > 2 else 0
            return price_usd * (min_use + per_100 * (math.ceil(quantity / 100) - 1))

        cost_material_usd = 0.0
        cost_material_usd += _material_cost(cost_paint)
        cost_material_usd += _material_cost(cost_solvent)
        cost_material_usd += _material_cost(cost_cleaner)
        cost_material_usd += _material_cost(cost_film)
        if diff_print == 0:
            cost_material_usd += _material_cost(cost_small)
        else:
            cost_material_usd += _material_cost(cost_large)
        cost_material_usd *= color
        cost_material_usd += cost_cliche_usd * (1 + diff_print * (color - 1))
        cost_material = cost_material_usd * usd_to_rub(1.0)

        time_prepare_cliche = 0.25 * (1 + diff_print * (color - 1))
        time_prepare_paint = 0.02 * color
        if is_pantone:
            time_prepare_paint += 0.2 * color
        time_packing = 0.003 * quantity if is_packing else 0.0

        time_prepare = float(tool.get("timePrepare", 0.15)) * max(1, mode.value)
        time_print = (quantity / process_per_hour + time_prepare) * color + time_packing

        tool_cost = parse_currency(tool.get("cost", "$1400") or "$1400")
        tool_depr = float(tool.get("timeDepreciation", 10)) * 250 * float(tool.get("hoursDay", 2))
        cost_depr_hour = tool_cost / tool_depr if tool_depr > 0 else 0
        cost_print = cost_depr_hour * time_print

        cam_cost = parse_currency(camera.get("cost", "$1000") or "$1000")
        cam_depr = float(camera.get("timeDepreciation", 10)) * 250 * float(camera.get("hoursDay", 2))
        cost_dry_hour = cam_cost / cam_depr if cam_depr > 0 else 0
        time_dry = 0.5
        cost_dry = cost_dry_hour * time_dry

        cost_process = cost_print + cost_dry
        time_operator = time_prepare_cliche + time_prepare_paint + time_print
        cost_operator = time_operator * COST_OPERATOR

        if material_mode == "isMaterialCustomer":
            defects += 0.25

        cost_total = math.ceil((cost_material + cost_process + cost_operator) * (1 + defects))
        margin_pad = get_margin("marginPadPrint")
        price_total = math.ceil(
            (cost_process + cost_operator) * (1 + defects + MARGIN_OPERATION + margin_pad)
            + cost_material * (1 + defects + MARGIN_MATERIAL + margin_pad)
        )

        time_hours = math.ceil((time_operator + time_dry) * 100) / 100.0
        time_ready = time_hours + base_ready

        return {
            "cost": float(cost_total),
            "price": int(price_total),
            "unit_price": float(price_total) / max(1, quantity),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": 0.0,
            "materials": [],
        }


