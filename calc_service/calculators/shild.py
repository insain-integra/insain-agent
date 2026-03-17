"""
Калькулятор ЩИТОВ / ШИЛЬДОВ.

Мигрировано из js_legacy/calc/calcShild.js (упрощённая версия).
Щиты/шильды: материал (hardsheet) + широкоформатная/УФ печать + монтаж.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping

from calculators.base import BaseCalculator, ProductionMode
from calculators.print_wide import PrintWideCalculator
from calculators.uv_print import UVPrintCalculator
from common.helpers import calc_weight
from common.layout import layout_on_sheet
from common.markups import (
    BASE_TIME_READY,
    MARGIN_MATERIAL,
    get_margin,
)
from common.process_tools import calc_packing
from materials import hardsheet as hardsheet_catalog, roll as roll_catalog

DEFAULT_PRINTER = "Technojet160ECO"
DEFAULT_UV_PRINTER = "RimalSuvUV"


class ShildCalculator(BaseCalculator):
    """Щиты/шильды: hardsheet + печать + опциональная упаковка."""

    slug = "shild"
    name = "Щиты"
    description = "Расчёт стоимости щитов и шильдов: материал, широкоформатная или УФ печать, упаковка."

    def get_options(self) -> Dict[str, Any]:
        materials = hardsheet_catalog.list_for_frontend()
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
                    "quantity": {"type": "integer", "minimum": 1, "description": "Количество изделий"},
                    "width": {"type": "number", "minimum": 1, "description": "Ширина, мм"},
                    "height": {"type": "number", "minimum": 1, "description": "Высота, мм"},
                    "material_id": {"type": "string", "description": "Код материала hardsheet"},
                    "print_method": {"type": "string", "enum": ["wide", "uv"], "default": "uv", "description": "Печать: wide=широкоформатная, uv=УФ"},
                    "printer_code": {"type": "string"},
                    "is_packing": {"type": "boolean", "default": False, "description": "Упаковка в зиплок"},
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["quantity", "width", "height", "material_id"],
            },
        }

    def get_param_schema(self) -> Dict[str, Any]:
        return {
            "slug": self.slug,
            "title": self.name,
            "params": [
                {"name": "quantity", "type": "integer", "required": True, "title": "Тираж", "validation": {"min": 1}},
                {"name": "width", "type": "number", "required": True, "title": "Ширина (мм)", "unit": "мм"},
                {"name": "height", "type": "number", "required": True, "title": "Высота (мм)", "unit": "мм"},
                {"name": "material_id", "type": "enum_cascading", "required": True, "title": "Материал", "choices": {"source": "materials:hardsheet"}},
                {"name": "print_method", "type": "enum", "required": False, "default": "uv", "title": "Печать",
                 "choices": {"inline": [{"id": "wide", "title": "Широкоформатная"}, {"id": "uv", "title": "УФ"}]}},
                {"name": "printer_code", "type": "string", "required": False, "title": "Принтер"},
                {"name": "is_packing", "type": "boolean", "required": False, "default": False, "title": "Упаковка"},
                {"name": "mode", "type": "enum", "required": False, "default": 1, "title": "Режим",
                 "choices": {"inline": [{"id": 0, "title": "Эконом"}, {"id": 1, "title": "Стандарт"}, {"id": 2, "title": "Экспресс"}]}},
            ],
            "param_groups": {
                "main": ["quantity", "width", "height"],
                "material": ["material_id"],
                "print": ["print_method", "printer_code"],
                "options": ["is_packing"],
                "mode": ["mode"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        n = int(params.get("quantity", 1))
        width = float(params.get("width", 0))
        height = float(params.get("height", 0))
        size = [width, height]
        material_id = str(params.get("material_id", "")).strip()
        print_method = str(params.get("print_method", "uv") or "uv").strip().lower()
        printer_code = str(params.get("printer_code", "") or (DEFAULT_UV_PRINTER if print_method == "uv" else DEFAULT_PRINTER)).strip()
        is_packing = bool(params.get("is_packing", False))
        mode = ProductionMode(int(params.get("mode", 1)))

        if width <= 0 or height <= 0:
            raise ValueError("Ширина и высота должны быть положительными")
        if not material_id:
            raise ValueError("material_id обязателен")

        material = hardsheet_catalog.get(material_id)
        cost_total = 0.0
        price_total = 0.0
        time_total = 0.0
        time_ready_max = 0.0
        weight_total = 0.0
        materials_out: List[Dict[str, Any]] = []

        # 1. База: материал (резка — упрощённо через стоимость листов)
        sizes = material.sizes or [[3050, 2050]]
        size_sheet = sizes[0] if sizes else [3050, 2050]
        if isinstance(size_sheet[0], (list, tuple)):
            size_sheet = size_sheet[0]
        layout = layout_on_sheet(size, size_sheet, [0, 0, 0, 0], 5)
        if layout["num"] == 0:
            raise ValueError("Изделие не помещается на материал")
        num_sheet = math.ceil(n / layout["num"])
        cost_mat = float(material.cost or 0) * num_sheet
        cost_total += cost_mat
        price_total += cost_mat * (1 + MARGIN_MATERIAL)
        weight_total += calc_weight(
            quantity=n,
            density=material.density or 0,
            thickness=material.thickness or 0,
            size=size,
            density_unit=getattr(material, "density_unit", "гм2") or "гм2",
        )
        materials_out.append({
            "code": material_id,
            "name": material.description,
            "title": material.title,
            "quantity": num_sheet,
            "unit": "лист",
        })

        # 2. Печать
        if print_method == "uv":
            uv_calc = UVPrintCalculator()
            uv_params = {
                "quantity": n,
                "width": width,
                "height": height,
                "item_width": width,
                "item_height": height,
                "printer_code": printer_code or DEFAULT_UV_PRINTER,
                "mode": mode.value,
            }
            uv_res = uv_calc.calculate(uv_params)
            cost_total += uv_res["cost"]
            price_total += uv_res["price"]
            time_total += uv_res["time_hours"]
            time_ready_max = max(time_ready_max, uv_res["time_ready"])
        else:
            # Широкоформатная печать — нужен рулонный материал. Для щитов используем плёнку ORAJET3640
            film_id = "ORAJET3640"
            try:
                film = roll_catalog.get(film_id)
            except KeyError:
                film = None
            if film:
                wide_calc = PrintWideCalculator()
                wide_params = {
                    "quantity": n,
                    "width": width,
                    "height": height,
                    "material_id": film_id,
                    "printer_code": printer_code or DEFAULT_PRINTER,
                    "mode": mode.value,
                }
                wide_res = wide_calc.calculate(wide_params)
                cost_total += wide_res["cost"]
                price_total += wide_res["price"]
                time_total += wide_res["time_hours"]
                time_ready_max = max(time_ready_max, wide_res["time_ready"])
                materials_out.extend(wide_res.get("materials", []))
            else:
                # Fallback: УФ печать
                uv_calc = UVPrintCalculator()
                uv_params = {
                    "quantity": n,
                    "width": width,
                    "height": height,
                    "item_width": width,
                    "item_height": height,
                    "printer_code": DEFAULT_UV_PRINTER,
                    "mode": mode.value,
                }
                uv_res = uv_calc.calculate(uv_params)
                cost_total += uv_res["cost"]
                price_total += uv_res["price"]
                time_total += uv_res["time_hours"]
                time_ready_max = max(time_ready_max, uv_res["time_ready"])

        # 3. Упаковка
        if is_packing:
            pack_options = {"isPacking": True}
            pack_res = calc_packing(n, [width, height, float(material.thickness or 3)], pack_options, mode.value)
            cost_total += pack_res.cost
            price_total += pack_res.price
            time_total += pack_res.time_hours
            weight_total += pack_res.weight_kg
            materials_out.extend(pack_res.materials)

        margin_shild = get_margin("marginShild")
        price_total = price_total * (1 + margin_shild)
        time_hours = math.ceil(time_total * 100) / 100.0
        time_ready = max(time_ready_max, time_hours + float(BASE_TIME_READY[min(mode.value, len(BASE_TIME_READY) - 1)]))

        return {
            "cost": float(math.ceil(cost_total)),
            "price": float(math.ceil(price_total)),
            "unit_price": round(float(price_total) / max(1, n), 2),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": round(weight_total, 2),
            "materials": materials_out,
        }
