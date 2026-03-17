"""
Калькулятор БЛОКНОТОВ.

Мигрировано из js_legacy/calc/calcNotebook.js.
Обложка (печать) + внутренний блок (печать) + переплёт (пружина или скобы).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping

from calculators.base import BaseCalculator, ProductionMode
from calculators.print_sheet import PrintSheetCalculator
from calculators.print_offset import PrintOffsetCalculator
from common.helpers import calc_weight
from common.layout import layout_on_sheet
from common.markups import get_margin, get_time_ready
from common.process_tools import calc_binding, calc_set_staples
from materials import sheet as sheet_catalog

# Размер A4 для расчёта раскладки внутреннего блока
SIZE_A4 = [320, 225]


def _merge_materials(a: List[Dict[str, Any]], b: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Объединить списки материалов (суммировать quantity по code)."""
    by_code: Dict[str, Dict[str, Any]] = {}
    for m in a + b:
        code = m.get("code", "")
        if code in by_code:
            q = by_code[code].get("quantity", 0)
            by_code[code]["quantity"] = q + m.get("quantity", 0)
        else:
            by_code[code] = dict(m)
    return list(by_code.values())


class NotebookCalculator(BaseCalculator):
    """Блокноты: обложка + внутренний блок + переплёт."""

    slug = "notebook"
    name = "Блокноты"
    description = "Расчёт блокнотов: печать обложки и внутреннего блока, переплёт на пружину или скобами."

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
                    "description": "Количество блокнотов",
                    "validation": {"min": 1, "max": 10000},
                },
                {
                    "name": "width_mm",
                    "type": "number",
                    "required": True,
                    "title": "Ширина (мм)",
                    "description": "Ширина изделия",
                    "validation": {"min": 50, "max": 400},
                    "unit": "мм",
                },
                {
                    "name": "height_mm",
                    "type": "number",
                    "required": True,
                    "title": "Высота (мм)",
                    "description": "Высота изделия",
                    "validation": {"min": 50, "max": 400},
                    "unit": "мм",
                },
                {
                    "name": "cover_material_id",
                    "type": "string",
                    "required": True,
                    "title": "Материал обложки",
                    "description": "Код бумаги для обложки (sheet)",
                },
                {
                    "name": "cover_color",
                    "type": "string",
                    "required": False,
                    "default": "4+0",
                    "title": "Цветность обложки",
                    "choices": {"inline": [
                        {"id": "1+0", "title": "1+0"}, {"id": "4+0", "title": "4+0"},
                        {"id": "1+1", "title": "1+1"}, {"id": "4+1", "title": "4+1"}, {"id": "4+4", "title": "4+4"},
                    ]},
                },
                {
                    "name": "cover_lamination_id",
                    "type": "string",
                    "required": False,
                    "title": "Ламинация обложки",
                },
                {
                    "name": "inner_material_id",
                    "type": "string",
                    "required": True,
                    "title": "Материал блока",
                    "description": "Код бумаги для внутреннего блока",
                },
                {
                    "name": "inner_num_sheet",
                    "type": "integer",
                    "required": True,
                    "title": "Листов в блоке",
                    "validation": {"min": 1, "max": 200},
                },
                {
                    "name": "inner_color",
                    "type": "string",
                    "required": False,
                    "default": "1+0",
                    "title": "Цветность блока",
                },
                {
                    "name": "binding_type",
                    "type": "string",
                    "required": False,
                    "default": "spring",
                    "title": "Тип переплёта",
                    "choices": {"inline": [
                        {"id": "spring", "title": "Пружина"},
                        {"id": "staples", "title": "Скобы"},
                    ]},
                },
                {
                    "name": "binding_edge",
                    "type": "string",
                    "required": False,
                    "default": "long",
                    "title": "Сторона переплёта",
                    "choices": {"inline": [
                        {"id": "short", "title": "По короткой стороне"},
                        {"id": "long", "title": "По длинной стороне"},
                    ]},
                },
                {
                    "name": "mode",
                    "type": "integer",
                    "required": False,
                    "default": int(ProductionMode.STANDARD),
                    "title": "Режим",
                },
            ],
            "param_groups": {
                "main": ["quantity", "width_mm", "height_mm"],
                "cover": ["cover_material_id", "cover_color", "cover_lamination_id"],
                "inner": ["inner_material_id", "inner_num_sheet", "inner_color"],
                "binding": ["binding_type", "binding_edge"],
                "mode": ["mode"],
            },
        }

    def get_options(self) -> Dict[str, Any]:
        materials = sheet_catalog.list_for_frontend()
        return {
            "materials": materials[:60],
            "colors": ["1+0", "4+0", "1+1", "4+1", "4+4"],
            "binding_types": ["spring", "staples"],
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
                    "quantity": {"type": "integer", "minimum": 1, "description": "Тираж блокнотов"},
                    "width_mm": {"type": "number", "minimum": 50, "description": "Ширина, мм"},
                    "height_mm": {"type": "number", "minimum": 50, "description": "Высота, мм"},
                    "cover_material_id": {"type": "string", "description": "Код бумаги обложки"},
                    "cover_color": {"type": "string", "default": "4+0"},
                    "cover_lamination_id": {"type": "string"},
                    "inner_material_id": {"type": "string", "description": "Код бумаги блока"},
                    "inner_num_sheet": {"type": "integer", "minimum": 1, "description": "Листов в блоке"},
                    "inner_color": {"type": "string", "default": "1+0"},
                    "binding_type": {"type": "string", "enum": ["spring", "staples"], "default": "spring"},
                    "binding_edge": {"type": "string", "enum": ["short", "long"], "default": "long"},
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["quantity", "width_mm", "height_mm", "cover_material_id", "inner_material_id", "inner_num_sheet"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        n = int(params.get("quantity", 1))
        width = float(params.get("width_mm", 0))
        height = float(params.get("height_mm", 0))
        size = [width, height]
        mode = ProductionMode(int(params.get("mode", 1)))

        cover_material_id = str(params.get("cover_material_id", "") or "").strip()
        cover_color = str(params.get("cover_color", "4+0") or "4+0").strip()
        cover_lamination_id = str(params.get("cover_lamination_id", "") or "").strip()
        inner_material_id = str(params.get("inner_material_id", "") or "").strip()
        inner_num_sheet = int(params.get("inner_num_sheet", 1))
        inner_color = str(params.get("inner_color", "1+0") or "1+0").strip()
        binding_type = str(params.get("binding_type", "spring") or "spring").strip()
        binding_edge = str(params.get("binding_edge", "long") or "long").strip()

        if not cover_material_id or not inner_material_id:
            raise ValueError("Укажите материал обложки и блока")

        num_with_defects = n
        margins = [2, 2, 2, 2]
        interval = 4

        # Обложка: лицевая и задняя — одна печать 2*n если одинаковые
        print_sheet = PrintSheetCalculator()
        cover_params = {
            "quantity": 2 * num_with_defects,
            "width": size[0],
            "height": size[1],
            "color": cover_color,
            "margins": margins,
            "interval": interval,
            "material_id": cover_material_id,
            "lamination_id": cover_lamination_id if cover_lamination_id else None,
            "lamination_double_side": True,
            "mode": mode.value,
        }
        cost_covers = print_sheet.calculate(cover_params)

        # Внутренний блок
        layout_a4 = layout_on_sheet(size, SIZE_A4, None, 0.0)
        num_sheet_a4 = math.ceil(num_with_defects * inner_num_sheet / layout_a4["num"]) if layout_a4["num"] > 0 else 0

        use_offset = (
            layout_a4["num"] > 0
            and num_sheet_a4 >= 1000
            and not params.get("is_print_laser")
            and not (inner_color == "0+0" and math.ceil(num_with_defects / layout_a4["num"]) <= 200)
        )

        cost_inners: Dict[str, Any] = {"cost": 0.0, "price": 0.0, "time_hours": 0.0, "time_ready": 0.0, "weight_kg": 0.0, "materials": []}
        is_offset = False

        if use_offset:
            print_offset = PrintOffsetCalculator()
            offset_params = {
                "num_sheet": num_with_defects * inner_num_sheet,
                "width": size[0],
                "height": size[1],
                "color": inner_color,
                "material_id": inner_material_id,
                "mode": mode.value,
            }
            inner_result = print_offset.calculate(offset_params)
            cost_inners = inner_result
            if num_sheet_a4 > 2500:
                is_offset = True
        else:
            margins_inner = [2, 2, 2, 2]
            interval_inner = 4
            if inner_material_id == "VHI80":
                margins_inner = [-1, -1, -1, -1]
                interval_inner = 0
            inner_params = {
                "quantity": num_with_defects * inner_num_sheet,
                "width": size[0],
                "height": size[1],
                "color": inner_color,
                "margins": margins_inner,
                "interval": interval_inner,
                "material_id": inner_material_id,
                "lamination_id": None,
                "lamination_double_side": True,
                "mode": mode.value,
            }
            inner_result = print_sheet.calculate(inner_params)
            cost_inners = inner_result

        # Переплёт
        cover = {
            "cover": {"materialID": cover_material_id, "laminatID": cover_lamination_id or "", "color": cover_color},
            "backing": {"materialID": cover_material_id, "laminatID": cover_lamination_id or "", "color": cover_color},
        }
        inner = [{"materialID": inner_material_id, "numSheet": inner_num_sheet, "color": inner_color}]
        binding = {"edge": binding_edge}
        options_binding = {"bindingID": "BindOffset" if is_offset else "BindRenzSRW"}

        if binding_type == "staples":
            cost_binding = calc_set_staples(n, None, mode.value)
        else:
            cost_binding = calc_binding(n, size, cover, inner, binding, options_binding, mode.value)

        # Итог
        cost_total = cost_covers["cost"] + cost_inners["cost"] + cost_binding.cost
        price_total = cost_covers["price"] + cost_inners["price"] + cost_binding.price
        margin_notebook = get_margin("marginNotebook")
        price = (price_total) * (1 + margin_notebook)
        price = math.ceil(price)

        time_hours = math.ceil((cost_covers["time_hours"] + cost_inners["time_hours"] + cost_binding.time_hours) * 100) / 100
        time_ready = time_hours + max(
            cost_covers.get("time_ready", 0),
            cost_inners.get("time_ready", 0),
            cost_binding.time_ready,
        )
        weight_kg = cost_covers.get("weight_kg", 0) + cost_inners.get("weight_kg", 0) + cost_binding.weight_kg

        materials_out = _merge_materials(
            cost_covers.get("materials", []),
            cost_inners.get("materials", []),
        )
        materials_out = _merge_materials(materials_out, cost_binding.materials)

        return {
            "cost": float(cost_total),
            "price": int(price),
            "unit_price": float(price) / max(1, n),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": round(weight_kg, 2),
            "materials": materials_out,
        }
