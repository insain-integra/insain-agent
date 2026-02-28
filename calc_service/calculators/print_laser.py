"""
Калькулятор лазерной печати на листах.

Перенесено из js_legacy/calc/calcPrintLaser.js.
Вход: количество листов, размер листа, цветность (4+0, 1+0, …), материал, принтер, режим.
Выход: себестоимость и цена печати, время, срок готовности, вес, материалы.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Optional

from calculators.base import BaseCalculator, ProductionMode
from common.helpers import calc_weight
from common.layout import layout_on_sheet
from common.markups import (
    MARGIN_MATERIAL,
    MARGIN_MIN,
    MARGIN_OPERATION,
    get_margin,
)
from equipment import printer as printer_catalog
from materials import sheet as sheet_catalog

PRINTER_CODE = "KMBizhubC220"

# Цветность: 1+0, 4+0 — односторонние; 1+1, 4+1, 4+4 — двухсторонние (double_side=2)


def _cost_per_sheet(color: str, cost_list: List[float]) -> float:
    """Себестоимость одного листа по цветности (JS: costPrintSheet)."""
    if not cost_list:
        return 0.0
    bw = cost_list[0] if len(cost_list) > 0 else 0.0
    color_cost = cost_list[1] if len(cost_list) > 1 else bw
    if color == "1+0":
        return bw
    if color == "1+1":
        return 2 * bw
    if color == "4+0":
        return color_cost
    if color == "4+1":
        return bw + color_cost
    if color == "4+4":
        return 2 * color_cost
    return color_cost


class PrintLaserCalculator(BaseCalculator):
    """Лазерная печать: листовой материал, цветность 1+0 / 4+0 / 1+1 / 4+1 / 4+4."""

    slug = "print_laser"
    name = "Лазерная печать"
    description = "Расчёт стоимости лазерной печати на листовом материале (принтер Konica Minolta и др.)."

    def get_options(self) -> Dict[str, Any]:
        materials = sheet_catalog.list_for_frontend()
        try:
            printers = [
                {"code": code, "name": spec.name}
                for code, spec in printer_catalog._items.items()
            ]
        except Exception:
            printers = [{"code": PRINTER_CODE, "name": "Принтер лазерный"}]
        return {
            "materials": materials[:60],
            "printers": printers,
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
                    "num_sheet": {"type": "integer", "minimum": 1, "description": "Количество листов печати"},
                    "width": {"type": "number", "minimum": 1, "description": "Ширина листа, мм"},
                    "height": {"type": "number", "minimum": 1, "description": "Высота листа, мм"},
                    "color": {"type": "string", "description": "Цветность: 1+0, 4+0, 1+1, 4+1, 4+4"},
                    "material_id": {"type": "string", "description": "Код материала из sheet (бумага)"},
                    "printer_code": {"type": "string", "description": "Код принтера"},
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["num_sheet", "width", "height", "material_id"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        num_sheet = int(params.get("num_sheet", 1))
        width = float(params.get("width", 0))
        height = float(params.get("height", 0))
        size_sheet = [width, height]
        color = str(params.get("color", "4+0") or "4+0").strip()
        material_id = str(params.get("material_id", "") or "").strip()
        printer_code = str(params.get("printer_code", "") or PRINTER_CODE).strip() or PRINTER_CODE
        mode = ProductionMode(int(params.get("mode", 1)))

        if color == "0+0":
            return self._empty_result(size_sheet, num_sheet, mode)

        try:
            printer = printer_catalog.get(printer_code)
        except KeyError:
            printer = printer_catalog.get(PRINTER_CODE) if printer_catalog._items else None
        if not printer:
            # TODO: оборудование не найдено
            return self._empty_result(size_sheet, num_sheet, mode)

        material = None
        if material_id:
            try:
                material = sheet_catalog.get(material_id)
            except KeyError:
                pass
        if not material:
            # TODO: материал не найден
            return self._empty_result(size_sheet, num_sheet, mode)

        max_printer = printer.max_size or [320, 450]
        layout_printer = layout_on_sheet(size_sheet, max_printer, None, 0.0)
        if layout_printer["num"] == 0:
            return self._empty_result(size_sheet, num_sheet, mode)

        # Коэффициент размера: половинный лист SRA (JS: layoutOnHalfSheet)
        coeff_size = 1.0
        half_sheet = [max_printer[0], max_printer[1] / 2.0]
        layout_half = layout_on_sheet(size_sheet, half_sheet, None, 0.0)
        if layout_half["num"] > 0:
            coeff_size = 0.5

        sheets_per_hour = printer.get_sheets_per_hour(getattr(material, "density", 80) or 80)
        if sheets_per_hour <= 0:
            sheets_per_hour = 250.0

        defects = printer.get_defect_rate(float(num_sheet))
        if mode.value >= 2:
            defects += defects * (mode.value - 1)
        num_with_defects = math.ceil(num_sheet * (1 + defects))

        double_side = 2 if color in ("1+1", "4+1", "4+4") else 1
        time_prepare = (printer.time_prepare or 0.1) * max(1, mode.value)
        time_print = (
            num_with_defects / sheets_per_hour * coeff_size * double_side + time_prepare
        )
        time_operator = time_print * 0.5 * (1 + defects) + time_prepare

        cost_print_sheet_list = getattr(printer, "cost_print_sheet", None) or [4.0, 12.0]
        cost_per_sheet_val = _cost_per_sheet(color, cost_print_sheet_list)

        cost_depreciation = printer.depreciation_per_hour * time_print
        cost_consumables = cost_per_sheet_val * coeff_size * num_with_defects
        cost_print = cost_depreciation + cost_consumables
        cost_operator = time_operator * printer.operator_cost_per_hour

        cost = cost_print + cost_operator
        margin_extra = get_margin("marginPrintLaser")
        effective_margin = max(MARGIN_OPERATION + margin_extra, MARGIN_MIN)
        # JS: result.price = costPrint * (1 + marginMaterial + marginPrintLaser) + costOperator * (1 + marginOperation + marginPrintLaser)
        price_print = cost_print * (1 + MARGIN_MATERIAL + margin_extra)
        price_operator = cost_operator * (1 + MARGIN_OPERATION + margin_extra)
        price = math.ceil(price_print + price_operator)

        time_hours = round(time_print * 100) / 100.0
        base_ready = printer.base_time_ready or [16, 8, 1]
        idx = max(0, min(len(base_ready) - 1, mode.value))
        time_ready = time_hours + float(base_ready[idx])

        weight_kg = 0.0
        try:
            weight_kg = calc_weight(
                quantity=num_sheet,
                density=getattr(material, "density", 80) or 80,
                thickness=getattr(material, "thickness", 0) or 0,
                size=size_sheet,
                density_unit=getattr(material, "density_unit", "гсм3") or "гсм3",
            )
        except Exception:
            pass

        materials_out: List[Dict[str, Any]] = []

        return {
            "cost": float(cost),
            "price": int(price),
            "unit_price": float(price) / max(1, num_sheet),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": weight_kg,
            "materials": materials_out,
        }

    def _empty_result(
        self, size_sheet: List[float], num_sheet: int, mode: ProductionMode
    ) -> Dict[str, Any]:
        from common.markups import BASE_TIME_READY

        base = BASE_TIME_READY
        idx = max(0, min(len(base) - 1, mode.value))
        return {
            "cost": 0.0,
            "price": 0,
            "unit_price": 0.0,
            "time_hours": 0.0,
            "time_ready": float(base[idx]),
            "weight_kg": 0.0,
            "materials": [],
        }
