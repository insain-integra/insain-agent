"""
Калькулятор цифровой листовой печати (принтер + опционально ламинация и резка).

Перенесено из js_legacy/calc/calcPrintSheet.js.
Вход: тираж, размер изделия, цветность, отступы, материал, принтер, опции (ламинация, резка), режим.
Выход: себестоимость и цена, время, срок готовности (baseTimeReadyPrintSheet [24, 8, 1]), вес, материалы.
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
    get_time_ready,
)
from equipment import printer as printer_catalog
from materials import sheet as sheet_catalog

PRINTER_CODE = "KMBizhubC220"


def _cost_per_sheet_laser(color: str, cost_list: Optional[List[float]]) -> float:
    """Себестоимость одного листа печати по цветности."""
    if not cost_list:
        return 12.0
    bw, cl = cost_list[0], cost_list[1] if len(cost_list) > 1 else cost_list[0]
    if color == "1+0":
        return bw
    if color == "1+1":
        return 2 * bw
    if color == "4+0":
        return cl
    if color == "4+1":
        return bw + cl
    if color == "4+4":
        return 2 * cl
    return cl


class PrintSheetCalculator(BaseCalculator):
    """Цифровая листовая печать: раскладка на листе, печать (лазер), опционально ламинация и резка."""

    slug = "print_sheet"
    name = "Печать листовая"
    description = "Расчёт стоимости цифровой листовой печати (лазер/струйный принтер, материал, опции)."

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
                    "quantity": {"type": "integer", "minimum": 1, "description": "Тираж, шт."},
                    "width": {"type": "number", "minimum": 1},
                    "height": {"type": "number", "minimum": 1},
                    "color": {"type": "string", "description": "Цветность: 1+0, 4+0, 1+1, 4+1, 4+4"},
                    "margins": {"type": "array", "items": {"type": "number"}, "description": "Вылеты [top, right, bottom, left] мм"},
                    "interval": {"type": "number", "description": "Отступ между изделиями, мм"},
                    "material_id": {"type": "string"},
                    "printer_code": {"type": "string"},
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["quantity", "width", "height", "material_id"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        quantity = int(params.get("quantity", 1))
        width = float(params.get("width", 0))
        height = float(params.get("height", 0))
        size = [width, height]
        color = str(params.get("color", "4+0") or "4+0").strip()
        margins_param = params.get("margins")
        if margins_param is not None and margins_param != -1:
            sum_margins = list(margins_param) if isinstance(margins_param, (list, tuple)) else [0, 0, 0, 0]
        else:
            sum_margins = [0, 0, 0, 0]
        interval = float(params.get("interval", 0) or 0)
        material_id = str(params.get("material_id", "") or "").strip()
        printer_code = str(params.get("printer_code", "") or PRINTER_CODE).strip() or PRINTER_CODE
        mode = ProductionMode(int(params.get("mode", 1)))

        if color == "0+0":
            return self._empty_result(size, quantity, mode)

        try:
            printer = printer_catalog.get(printer_code)
        except KeyError:
            printer = printer_catalog.get(PRINTER_CODE) if printer_catalog._items else None
        if not printer:
            # TODO: оборудование не найдено
            return self._empty_result(size, quantity, mode)

        material = None
        if material_id:
            try:
                material = sheet_catalog.get(material_id)
            except KeyError:
                pass
        if not material:
            # TODO: материал не найден
            return self._empty_result(size, quantity, mode)

        size_sheet = material.sizes[0] if material.sizes else [320, 450]
        size_sheet = [float(size_sheet[0]), float(size_sheet[1])]
        max_printer = printer.max_size or [320, 450]
        printer_margins = list(printer.margins or [3, 3, 3, 3])
        if len(printer_margins) < 4:
            printer_margins = [3, 3, 3, 3]
        if color != "0+0" and sum_margins:
            sum_margins = [
                sum_margins[i] + printer_margins[i]
                for i in range(min(4, len(sum_margins)))
            ]
        if len(sum_margins) < 4:
            sum_margins = sum_margins + [0] * (4 - len(sum_margins))

        layout_on_printer = layout_on_sheet(size_sheet, max_printer, None, 0.0)
        if layout_on_printer["num"] == 0:
            size_sheet = list(max_printer)
            layout_on_material = layout_on_sheet(size_sheet, size_sheet, None, 0.0)
            layout_sheet = layout_on_sheet(size, size_sheet, sum_margins, interval)
            if layout_sheet["num"] == 0:
                return self._empty_result(size, quantity, mode)
            num_sheet = math.ceil(quantity / layout_sheet["num"])
            # TODO: доп. резка (гильотина/роликовый) — не реализовано
        else:
            layout_sheet = layout_on_sheet(size, size_sheet, sum_margins, interval)
            if layout_sheet["num"] == 0:
                return self._empty_result(size, quantity, mode)
            num_sheet = math.ceil(quantity / layout_sheet["num"])
            layout_on_material = {"num": 1}

        num_sheet_to_print = num_sheet
        # TODO: ламинация — defectsLaminator, num_sheet_to_print = ceil(num_sheet_to_print * (1 + defectsLaminator))
        defects_printer = printer.get_defect_rate(float(num_sheet_to_print))
        if mode.value >= 2:
            defects_printer += defects_printer * (mode.value - 1)
        num_with_defects = math.ceil(num_sheet_to_print * (1 + defects_printer))

        # Печать (лазерная логика как в calcPrintLaser)
        coeff_size = 1.0
        half_sheet = [max_printer[0], max_printer[1] / 2.0]
        layout_half = layout_on_sheet(size_sheet, half_sheet, None, 0.0)
        if layout_half["num"] > 0:
            coeff_size = 0.5
        sheets_per_hour = printer.get_sheets_per_hour(getattr(material, "density", 80) or 80)
        if sheets_per_hour <= 0:
            sheets_per_hour = 250.0
        double_side = 2 if color in ("1+1", "4+1", "4+4") else 1
        time_prepare = (printer.time_prepare or 0.1) * max(1, mode.value)
        time_print = num_with_defects / sheets_per_hour * coeff_size * double_side + time_prepare
        time_operator = time_print * 0.5 * (1 + defects_printer) + time_prepare

        cost_print_sheet_list = getattr(printer, "cost_print_sheet", None) or [4.0, 12.0]
        cost_per_sheet_val = _cost_per_sheet_laser(color, cost_print_sheet_list)
        cost_depreciation = printer.depreciation_per_hour * time_print
        cost_consumables = cost_per_sheet_val * coeff_size * num_with_defects
        cost_print = cost_depreciation + cost_consumables
        cost_operator = time_operator * printer.operator_cost_per_hour
        cost_print_total = cost_print + cost_operator

        # Материал: costMaterial = material.cost * ceil(numSheetToPrint*(1+defectsPrinter)) / layoutOnMaterial.num
        layout_num = max(1, layout_on_material.get("num", 1))
        num_sheets_physical = math.ceil(num_sheet_to_print * (1 + defects_printer) / layout_num)
        cost_material = float(material.get_cost(1)) * num_sheets_physical

        cost_cut = 0.0
        cost_lamination = 0.0
        cost_cut_guillotine = 0.0
        time_cut = 0.0
        time_lamination = 0.0
        time_cut_guillotine = 0.0
        # TODO: costCut, costLamination, costCutGuillotine из соответствующих калькуляторов

        cost = cost_material + cost_cut + cost_print_total + cost_lamination + cost_cut_guillotine
        price_material = cost_material * (1 + MARGIN_MATERIAL)
        margin_extra = get_margin("marginPrintSheet")
        effective_margin = max(MARGIN_OPERATION + margin_extra, MARGIN_MIN)
        price_operations = (cost_print_total + cost_cut + cost_lamination + cost_cut_guillotine) * (1 + effective_margin)
        price = math.ceil(price_material + price_operations)

        time_total = time_print + time_cut + time_lamination + time_cut_guillotine
        time_hours = round(time_total * 100) / 100.0
        base_time_ready_list = get_time_ready("baseTimeReadyPrintSheet")
        idx = max(0, min(len(base_time_ready_list) - 1, mode.value))
        base_ready = base_time_ready_list[idx]
        printer_ready = printer.base_time_ready or [24, 8, 1]
        idx_p = max(0, min(len(printer_ready) - 1, mode.value))
        time_ready = time_hours + max(float(base_ready), float(printer_ready[idx_p]))

        weight_kg = 0.0
        try:
            weight_kg = calc_weight(
                quantity=quantity,
                density=getattr(material, "density", 80) or 80,
                thickness=getattr(material, "thickness", 0) or 0,
                size=size,
                density_unit=getattr(material, "density_unit", "гм2") or "гм2",
            )
        except Exception:
            pass

        materials_out: List[Dict[str, Any]] = [
            {
                "code": material.code,
                "name": material.name,
                "quantity": num_sheets_physical,
                "unit": "sheet",
            }
        ]

        return {
            "cost": float(cost),
            "price": int(price),
            "unit_price": float(price) / max(1, quantity),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": weight_kg,
            "materials": materials_out,
        }

    def _empty_result(
        self, size: List[float], quantity: int, mode: ProductionMode
    ) -> Dict[str, Any]:
        base_list = get_time_ready("baseTimeReadyPrintSheet")
        idx = max(0, min(len(base_list) - 1, mode.value))
        return {
            "cost": 0.0,
            "price": 0,
            "unit_price": 0.0,
            "time_hours": 0.0,
            "time_ready": float(base_list[idx]),
            "weight_kg": 0.0,
            "materials": [],
        }
