"""
Калькулятор ОФСЕТНОЙ ПЕЧАТИ.

Мигрировано из js_legacy/calc/calcPrintOffset.js.
Два режима: обычная офсетная печать и промо-тиражи (сборники).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping

from calculators.base import BaseCalculator, ProductionMode
from common.helpers import calc_weight
from common.layout import layout_on_sheet
from common.markups import (
    BASE_TIME_READY,
    MARGIN_MATERIAL,
    MARGIN_OPERATION,
    get_margin,
    get_time_ready,
)
from equipment import printer as printer_catalog
from materials import sheet as sheet_catalog

OFFSET_PRINTER_CODE = "OffsetPrint"


class PrintOffsetCalculator(BaseCalculator):
    """Офсетная печать (обычная + промо-тиражи)."""

    slug = "print_offset"
    name = "Офсетная печать"
    description = "Расчёт офсетной печати (от 500 экз.), включая стоимость форм, приладки и бумаги."

    def get_options(self) -> Dict[str, Any]:
        materials = sheet_catalog.list_for_frontend()
        return {
            "materials": materials[:60],
            "colors": ["0+0", "1+0", "4+0", "1+1", "4+1", "4+4"],
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
                    "num_sheet": {"type": "integer", "minimum": 1, "description": "Кол-во листов"},
                    "width": {"type": "number", "minimum": 1, "description": "Ширина листа, мм"},
                    "height": {"type": "number", "minimum": 1, "description": "Высота листа, мм"},
                    "color": {"type": "string", "description": "Цветность: 0+0, 1+0, 4+0, 1+1, 4+1, 4+4"},
                    "material_id": {"type": "string", "description": "Код бумаги (из каталога sheet)"},
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["num_sheet", "width", "height", "color", "material_id"],
            },
        }

    def get_param_schema(self) -> Dict[str, Any]:
        return {
            "slug": self.slug,
            "title": self.name,
            "params": [
                {"name": "num_sheet", "type": "integer", "required": True, "title": "Кол-во листов", "validation": {"min": 1}},
                {"name": "width", "type": "number", "required": True, "title": "Ширина (мм)", "unit": "мм"},
                {"name": "height", "type": "number", "required": True, "title": "Высота (мм)", "unit": "мм"},
                {"name": "color", "type": "enum", "required": True, "title": "Цветность",
                 "choices": {"inline": [
                     {"id": "0+0", "title": "0+0", "description": "Без печати"},
                     {"id": "1+0", "title": "1+0"}, {"id": "4+0", "title": "4+0"},
                     {"id": "1+1", "title": "1+1"}, {"id": "4+1", "title": "4+1"}, {"id": "4+4", "title": "4+4"},
                 ]}},
                {"name": "material_id", "type": "enum_cascading", "required": True, "title": "Бумага", "choices": {"source": "materials:sheet"}},
                {"name": "mode", "type": "enum", "required": False, "default": 1, "title": "Режим",
                 "choices": {"inline": [{"id": 0, "title": "Эконом"}, {"id": 1, "title": "Стандарт"}, {"id": 2, "title": "Экспресс"}]}},
            ],
            "param_groups": {"main": ["num_sheet", "width", "height"], "processing": ["color"], "material": ["material_id"], "mode": ["mode"]},
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        num_sheet = int(params.get("num_sheet", 1))
        width = float(params.get("width", 0))
        height = float(params.get("height", 0))
        size_sheet = [width, height]
        color = str(params.get("color", "4+0") or "4+0").strip()
        material_id = str(params.get("material_id", "")).strip()
        mode = ProductionMode(int(params.get("mode", 1)))

        try:
            printer = printer_catalog.get(OFFSET_PRINTER_CODE)
        except KeyError:
            return self._empty(mode)

        try:
            material = sheet_catalog.get(material_id)
        except KeyError:
            return self._empty(mode)

        base_time_ready = printer.base_time_ready or BASE_TIME_READY
        idx = max(0, min(len(base_time_ready) - 1, mode.value))
        base_ready = float(base_time_ready[idx])

        max_size = printer.max_size or [640, 450]

        # Раскладка на SRA2
        margins_print = [2, 2, 2, 2] if color != "0+0" else [0, 0, 0, 0]
        interval_print = 4 if color != "0+0" else 0
        layout_sra2 = layout_on_sheet(size_sheet, max_size, margins_print, float(interval_print))
        if layout_sra2["num"] == 0:
            raise ValueError("Размер листа не помещается на офсетный формат SRA2")
        num_sheet_sra2 = math.ceil(num_sheet / layout_sra2["num"])

        # Стоимость бумаги
        density = getattr(material, "density", 80) or 80
        cost_sheet, paper_name = self._find_paper_cost(printer, density)
        adjust_paper = printer.adjust_paper if color != "0+0" else 0
        cost_paper = (adjust_paper + num_sheet_sra2) * cost_sheet

        # Печать
        cost_offset_form = 0.0
        cost_prepare = 0.0
        cost_print = 0.0
        if color != "0+0":
            double_side = 2 if color in ("1+1", "4+1", "4+4") else 1
            cost_print = (
                printer.cost_adjust
                + (printer.cost_prepare_print + (printer.cost_print_m2 or 0.52) * num_sheet_sra2)
                * (1 + 0.66 * (double_side - 1))
            )
            cost_prepare = printer.cost_prepare_offset * double_side
            num_colors = int(color[0]) + int(color[2])
            cost_offset_form = printer.cost_offset_form * num_colors

        # Резка
        cost_cut = printer.cost_prepare_cut + math.ceil(num_sheet_sra2 / 900) * printer.cost_cut_offset

        # Время и оператор
        time_prepare = (printer.time_prepare or 0) * max(1, mode.value)
        time_operator = time_prepare
        cost_operator = time_operator * printer.operator_cost_per_hour

        # Итого
        cost = cost_operator + cost_paper + cost_offset_form + cost_prepare + cost_print + cost_cut
        margin_offset = get_margin("marginPrintOffset")
        price = (
            cost_operator * (1 + MARGIN_OPERATION + margin_offset)
            + (cost_paper + cost_offset_form + cost_prepare + cost_print + cost_cut)
            * (1 + MARGIN_MATERIAL + margin_offset)
        )

        time_hours = math.ceil(time_operator * 100) / 100.0
        time_ready = time_hours + base_ready

        weight_kg = calc_weight(
            quantity=num_sheet,
            density=density,
            thickness=getattr(material, "thickness", 0) or 0,
            size=size_sheet,
            density_unit=getattr(material, "density_unit", "гм2") or "гм2",
        )

        materials_out: List[Dict[str, Any]] = [{
            "code": "OffsetPaper",
            "name": paper_name,
            "title": paper_name,
            "quantity": adjust_paper + num_sheet_sra2,
            "unit": "sheet",
        }]

        return {
            "cost": float(cost),
            "price": float(price),
            "unit_price": float(price) / max(1, num_sheet),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": round(weight_kg, 3),
            "materials": materials_out,
        }

    @staticmethod
    def _find_paper_cost(printer, density: float) -> tuple[float, str]:
        """Найти стоимость и название бумаги по плотности из costPaper."""
        table = printer.cost_paper_table
        if not table:
            return 5.0, "Офсетная бумага SRA2"
        for name, d, cost in table:
            if d >= density:
                return cost, name
        last = table[-1]
        return last[2], last[0]

    def _empty(self, mode: ProductionMode) -> Dict[str, Any]:
        btr = BASE_TIME_READY
        idx = max(0, min(len(btr) - 1, mode.value))
        return {
            "cost": 0.0, "price": 0.0, "unit_price": 0.0,
            "time_hours": 0.0, "time_ready": float(btr[idx]),
            "weight_kg": 0.0, "materials": [],
        }
