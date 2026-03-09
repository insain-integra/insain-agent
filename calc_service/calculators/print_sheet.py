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
from calculators.cut_guillotine import CutGuillotineCalculator
from calculators.lamination import LaminationCalculator, LAMINATOR_CODE
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
from equipment import laminator as laminator_catalog
from materials import sheet as sheet_catalog
from materials import get_material as get_material_any

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
                    "lamination_id": {
                        "type": "string",
                        "description": "Код плёнки ламинации (из каталога laminat). Пусто — без ламинации.",
                    },
                    "lamination_double_side": {
                        "type": "boolean",
                        "description": "Двусторонняя ламинация (как в JS calcPrintSheet, по умолчанию true).",
                    },
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
        lamination_id = str(params.get("lamination_id", "") or "").strip()
        lamination_double_side = bool(params.get("lamination_double_side", True))
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
        # Если есть ламинация, сначала учитываем брак ламинатора, как в JS calcPrintSheet:
        # defectsLaminator → numSheetToPrint = ceil(numSheetToPrint * (1 + defectsLaminator)).
        if lamination_id:
            try:
                laminator = laminator_catalog.get(LAMINATOR_CODE)
            except Exception:
                laminator = None
            if laminator:
                try:
                    defects_laminator = laminator.get_defect_rate(float(num_sheet))
                    num_sheet_to_print = math.ceil(num_sheet_to_print * (1 + defects_laminator))
                except Exception:
                    pass

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
        price_cut_guillotine = 0.0
        price_lamination = 0.0
        time_cut = 0.0
        time_lamination = 0.0
        time_cut_guillotine = 0.0

        try:
            cut_calc = CutGuillotineCalculator()
            cut_params = {
                "num_sheet": num_sheet,
                "width": size[0],
                "height": size[1],
                "sheet_width": size_sheet[0],
                "sheet_height": size_sheet[1],
                "material_id": material_id,
                "material_category": "sheet",
                "margins": list(sum_margins),
                "interval": interval,
                "mode": mode.value,
            }
            cut_result = cut_calc.calculate(cut_params)
            cost_cut_guillotine = float(cut_result.get("cost", 0))
            time_cut_guillotine = float(cut_result.get("time_hours", 0))
            price_cut_guillotine = float(cut_result.get("price", 0))
        except Exception:
            pass

        # Ламинация (как в JS calcPrintSheet: по плёнке laminat, с выбором по размеру плёнки)
        lamination_result: Optional[Dict[str, Any]] = None
        if lamination_id:
            try:
                lam_material = get_material_any("laminat", lamination_id)
            except Exception:
                lam_material = None
            try:
                lam_calc = LaminationCalculator()
                if lam_material and getattr(lam_material, "sizes", None):
                    first_size = lam_material.sizes[0]
                    lam_w = float(first_size[0]) if len(first_size) > 0 else 0.0
                    lam_h = float(first_size[1]) if len(first_size) > 1 else 0.0
                else:
                    lam_w = lam_h = 0.0

                # JS: если laminat.size[1] == 0 → считаем по листам (numSheet, sizeSheet),
                # иначе по изделиям (n, size).
                if lam_h == 0:
                    # JS: calcLamination(numSheet, sizeSheet, ...)
                    lam_quantity = num_sheet
                    lam_width, lam_height = size_sheet[0], size_sheet[1]
                else:
                    lam_quantity = quantity
                    lam_width, lam_height = size[0], size[1]

                lam_params = {
                    "quantity": int(lam_quantity),
                    "width": float(lam_width),
                    "height": float(lam_height),
                    "material_id": lamination_id,
                    "double_side": bool(lamination_double_side),
                    "mode": mode.value,
                }
                lamination_result = lam_calc.calculate(lam_params)
                cost_lamination = float(lamination_result.get("cost", 0.0))
                time_lamination = float(lamination_result.get("time_hours", 0.0))
                price_lamination = float(lamination_result.get("price", 0.0))
            except Exception:
                lamination_result = None

        cost = cost_material + cost_cut + cost_print_total + cost_lamination + cost_cut_guillotine
        # JS: result.price = (costMaterial*(1+marginMaterial) + costCut.price + costPrint.price + costLamination.price + costCutGuillotine.price + costOptions.price) * (1+marginPrintSheet)
        # costPrint.price (calcPrintLaser): costPrint*(1+marginMaterial+marginPrintLaser) + costOperator*(1+marginOperation+marginPrintLaser)
        price_material = cost_material * (1 + MARGIN_MATERIAL)
        margin_print_laser = get_margin("marginPrintLaser")
        price_print = cost_print * (1 + MARGIN_MATERIAL + margin_print_laser) + cost_operator * (
            1 + MARGIN_OPERATION + margin_print_laser
        )
        margin_print_sheet = get_margin("marginPrintSheet")
        price = (price_material + price_print + price_cut_guillotine + price_lamination) * (1 + margin_print_sheet)
        price = math.ceil(price)

        time_total = time_print + time_cut + time_lamination + time_cut_guillotine
        # В JS: result.time = Math.ceil((costCut.time+costPrint.time+costLamination.time+costCutGuillotine.time+costOptions.time)*100)/100
        # Используем такое же округление вверх до сотых.
        time_hours = math.ceil(time_total * 100) / 100.0
        base_time_ready_list = get_time_ready("baseTimeReadyPrintSheet")
        idx = max(0, min(len(base_time_ready_list) - 1, mode.value))
        base_ready = float(base_time_ready_list[idx])
        # JS: result.timeReady = result.time + Math.max(baseTimeReady, costPrint.timeReady); costPrint.timeReady = timePrint + baseTimeReady
        print_time_ready = time_print + base_ready
        time_ready = time_hours + max(base_ready, print_time_ready)

        # Вес по количеству выдаваемой продукции (тираж × размер изделия), не по листам с браком.
        # Плюс вес плёнки ламинации, если она есть.
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
        if lamination_result:
            try:
                weight_kg += float(lamination_result.get("weight_kg", 0.0))
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
        if lamination_result:
            for m in lamination_result.get("materials") or []:
                materials_out.append(m)

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
