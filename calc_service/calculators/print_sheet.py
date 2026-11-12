"""
Калькулятор ЦИФРОВОЙ ЛИСТОВОЙ ПЕЧАТИ.

Считает листовую продукцию (листовки, визитки и т.п.): материал, печать, опционально ламинация,
опционально постпечать: нумерация, штрихкод, переменные данные, скругление углов, пробивка отверстий, биговка.
Резка в расчёт входит по умолчанию, в описаниях не упоминается.

Использовать, когда менеджер просит: «листовки», «листовки с ламинацией», «визитки с ламинацией»
и т.п. — печать (с опциональной ламинацией), а не только отдельную ламинацию.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Optional

from calculators.base import BaseCalculator, ProductionMode
from calculators.cut_guillotine import CutGuillotineCalculator
from calculators.lamination import LaminationCalculator, LAMINATOR_CODE
from calculators.print_inkjet import PrintInkjetCalculator
from common.helpers import calc_weight
from common.layout import layout_on_sheet
from common.process_tools import calc_crease, calc_punching, calc_rounding
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
# Струйные принтеры — как switch в js_legacy/calc/calcPrintSheet.js (строки 83–97).
INKJET_PRINTERS = frozenset({"EPSONWF7610", "DTFTransfer"})
# Качество по умолчанию: EPSONWF7610 → 1, DTFTransfer → 0.
_INKJET_DEFAULT_QUALITY = {"EPSONWF7610": 1, "DTFTransfer": 0}

# Доп. опции постпечати — как в js_legacy/calc/calcPrintSheet.js (costOptions).
# Фиксированные надбавки за шт. (себестоимость / цена до marginPrintSheet).
_OPTION_NUMBERING_COST_PER_UNIT = 0.75
_OPTION_NUMBERING_PRICE_PER_UNIT = 1.0
_OPTION_NUMBERING_TIME_H = 0.05
_OPTION_BARCODE_COST_PER_UNIT = 1.0
_OPTION_BARCODE_PRICE_PER_UNIT = 2.0
_OPTION_BARCODE_TIME_H = 0.1
_OPTION_VARIABLE_DATA_COST_PER_UNIT = 3.0
_OPTION_VARIABLE_DATA_PRICE_PER_UNIT = 5.0
_OPTION_VARIABLE_DATA_TIME_H = 0.1

_MAX_HOLES_PER_ITEM = 50
_MAX_CREASE_LINES = 20


def _coerce_bool(v: Any) -> bool:
    if v is True:
        return True
    if v is False or v is None:
        return False
    if isinstance(v, (int, float)):
        return v != 0
    if isinstance(v, str):
        return v.strip().lower() in ("1", "true", "yes", "да", "on")
    return False


def _coerce_nonneg_int(v: Any, default: int = 0) -> int:
    try:
        n = int(v)
        return max(0, n)
    except (TypeError, ValueError):
        return default


def _print_sheet_extra_options(
    params: Mapping[str, Any],
    quantity: int,
    size: List[float],
    material_id: str,
    mode_value: int,
) -> tuple[float, float, float]:
    """
    Доп. опции постпечати (как costOptions в calcPrintSheet.js).

    Возвращает (себестоимость опций, цена-вклад до marginPrintSheet, время, ч).
    """
    opt_cost = 0.0
    opt_price = 0.0
    opt_time = 0.0

    if _coerce_bool(params.get("option_numbering")) or _coerce_bool(params.get("is_number")):
        opt_cost += _OPTION_NUMBERING_COST_PER_UNIT * quantity
        opt_price += _OPTION_NUMBERING_PRICE_PER_UNIT * quantity
        opt_time += _OPTION_NUMBERING_TIME_H

    if _coerce_bool(params.get("option_barcode")) or _coerce_bool(params.get("is_barcode")):
        opt_cost += _OPTION_BARCODE_COST_PER_UNIT * quantity
        opt_price += _OPTION_BARCODE_PRICE_PER_UNIT * quantity
        opt_time += _OPTION_BARCODE_TIME_H

    if _coerce_bool(params.get("option_variable_data")) or _coerce_bool(params.get("is_variables")):
        opt_cost += _OPTION_VARIABLE_DATA_COST_PER_UNIT * quantity
        opt_price += _OPTION_VARIABLE_DATA_PRICE_PER_UNIT * quantity
        opt_time += _OPTION_VARIABLE_DATA_TIME_H

    if _coerce_bool(params.get("option_rounding")) or _coerce_bool(params.get("is_rounding")):
        r = calc_rounding(quantity, material_id, mode_value)
        opt_cost += r.cost
        opt_price += r.price
        opt_time += r.time_hours

    holes = _coerce_nonneg_int(
        params.get("holes_per_item", params.get("is_hole")),
        0,
    )
    if holes > 0:
        holes = min(holes, _MAX_HOLES_PER_ITEM)
        r = calc_punching(quantity * holes, material_id, mode_value)
        opt_cost += r.cost
        opt_price += r.price
        opt_time += r.time_hours

    crease = _coerce_nonneg_int(
        params.get("crease_lines_per_item", params.get("is_crease")),
        0,
    )
    if crease > 0:
        crease = min(crease, _MAX_CREASE_LINES)
        try:
            r = calc_crease(quantity, crease, size, material_id, mode_value)
            opt_cost += r.cost
            opt_price += r.price
            opt_time += r.time_hours
        except ValueError:
            raise ValueError(
                "Биговка: размер изделия не помещается в допустимый формат для оборудования. "
                "Уменьшите размер или отключите опцию crease_lines_per_item."
            ) from None

    opt_time = math.ceil(opt_time * 100) / 100.0
    return opt_cost, opt_price, opt_time


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
    """Листовая цифровая печать: материал, печать, опционально ламинация."""

    slug = "print_sheet"
    name = "Печать листовая"
    description = (
        "Расчёт листовой печати (листовки, визитки и т.п.): материал, печать, опционально ламинация, "
        "опции: нумерация, штрихкод, переменные данные, скругление, пробивка отверстий (число на изделие), биговка. "
        "Использовать, когда нужна печать продукции, в том числе «листовки с ламинацией»."
    )
    def get_param_schema(self) -> Dict[str, Any]:
        """
        Детальная схема параметров для листовой печати.

        Используется агентом и UI для построения формы и валидации.
        """
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
                    "name": "width_mm",
                    "type": "number",
                    "required": True,
                    "title": "Ширина (мм)",
                    "description": "Ширина изделия",
                    "validation": {"min": 10, "max": 1300},
                    "unit": "мм",
                },
                {
                    "name": "height_mm",
                    "type": "number",
                    "required": True,
                    "title": "Высота (мм)",
                    "description": "Высота изделия",
                    "validation": {"min": 10, "max": 900},
                    "unit": "мм",
                },
                {
                    "name": "material",
                    "type": "enum_cascading",
                    "required": True,
                    "title": "Бумага",
                    "description": "Тип бумаги, вариант и плотность",
                    "choices": {
                        "source": "materials:sheet",
                        "cascade_levels": ["type", "variant", "thickness"],
                    },
                },
                {
                    "name": "color",
                    "type": "enum",
                    "required": True,
                    "default": "4+0",
                    "title": "Цветность",
                    "description": "Схема печати: 1+0, 4+0, 1+1, 4+1, 4+4",
                    "choices": {
                        "inline": [
                            {"id": "1+0", "title": "1+0", "description": "Ч/б с одной стороны"},
                            {"id": "4+0", "title": "4+0", "description": "Цвет с одной стороны"},
                            {"id": "1+1", "title": "1+1", "description": "Ч/б с двух сторон"},
                            {"id": "4+1", "title": "4+1", "description": "Цвет + ч/б с оборота"},
                            {"id": "4+4", "title": "4+4", "description": "Цвет с двух сторон"},
                        ]
                    },
                },
                {
                    "name": "lamination",
                    "type": "enum",
                    "required": False,
                    "title": "Ламинация",
                    "description": "Плёнка для ламинации (по умолчанию без ламинации)",
                    "choices": {
                        "source": "materials:laminat",
                    },
                },
                {
                    "name": "lamination_double_side",
                    "type": "boolean",
                    "required": False,
                    "default": True,
                    "title": "Двусторонняя ламинация",
                    "description": "Если включено — ламинация с двух сторон",
                },
                {
                    "name": "mode",
                    "type": "enum",
                    "required": False,
                    "default": int(ProductionMode.STANDARD),
                    "title": "Режим",
                    "description": "Срочность изготовления заказа",
                    "choices": {
                        "inline": [
                            {"id": int(ProductionMode.ECONOMY), "title": "Эконом", "description": "3 рабочих дня"},
                            {"id": int(ProductionMode.STANDARD), "title": "Стандарт", "description": "1 рабочий день"},
                            {"id": int(ProductionMode.EXPRESS), "title": "Экспресс", "description": "4 часа"},
                        ]
                    },
                },
                {
                    "name": "quality",
                    "type": "enum",
                    "required": False,
                    "default": 1,
                    "title": "Качество печати",
                    "description": "Для струйных принтеров: 0=стандарт, 1=высокое, 2=фото. EPSONWF7610 по умолчанию 1, DTFTransfer — 0.",
                    "choices": {
                        "inline": [
                            {"id": 0, "title": "Стандарт"},
                            {"id": 1, "title": "Высокое"},
                            {"id": 2, "title": "Фото"},
                        ]
                    },
                },
                {
                    "name": "option_numbering",
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "title": "Нумерация",
                    "description": "Последовательная нумерация экземпляров (как isNumber в JS).",
                },
                {
                    "name": "option_barcode",
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "title": "Штрихкод",
                    "description": "Добавить штрихкод на каждое изделие (isBarcode).",
                },
                {
                    "name": "option_variable_data",
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "title": "Переменные данные",
                    "description": "Персонализация / переменные поля в макете (isVariables).",
                },
                {
                    "name": "option_rounding",
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "title": "Скругление углов",
                    "description": "Скругление углов заготовки после печати (isRounding).",
                },
                {
                    "name": "holes_per_item",
                    "type": "integer",
                    "required": False,
                    "default": 0,
                    "title": "Отверстий на изделие",
                    "description": "Пробивка: количество отверстий на одно изделие; 0 — без пробивки (аналог isHole в JS).",
                    "validation": {"min": 0, "max": _MAX_HOLES_PER_ITEM},
                },
                {
                    "name": "crease_lines_per_item",
                    "type": "integer",
                    "required": False,
                    "default": 0,
                    "title": "Линий биговки на изделие",
                    "description": "Биговка/перфорация: число линий на одно изделие; 0 — без биговки (isCrease).",
                    "validation": {"min": 0, "max": _MAX_CREASE_LINES},
                },
            ],
            "param_groups": {
                "main": ["quantity", "width_mm", "height_mm"],
                "material": ["material"],
                "processing": ["color", "quality", "lamination", "lamination_double_side"],
                "extras": [
                    "option_numbering",
                    "option_barcode",
                    "option_variable_data",
                    "option_rounding",
                    "holes_per_item",
                    "crease_lines_per_item",
                ],
                "mode": ["mode"],
            },
        }

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
            "qualities": [
                {"value": 0, "label": "Стандарт"},
                {"value": 1, "label": "Высокое"},
                {"value": 2, "label": "Фото"},
            ],
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
                    "quality": {
                        "type": "integer",
                        "enum": [0, 1, 2],
                        "default": 1,
                        "description": "Качество струйной печати: 0=стандарт, 1=высокое, 2=фото. Для EPSONWF7610 по умолчанию 1, для DTFTransfer — 0.",
                    },
                    "lamination_id": {
                        "type": "string",
                        "description": "Код плёнки ламинации (из каталога laminat). Пусто — без ламинации.",
                    },
                    "lamination_double_side": {
                        "type": "boolean",
                        "description": "Двусторонняя ламинация (как в JS calcPrintSheet, по умолчанию true).",
                    },
                    "no_cut": {
                        "type": "boolean",
                        "description": "Без резки (для бейджей — печать без гильотинной резки).",
                        "default": False,
                    },
                    "option_numbering": {
                        "type": "boolean",
                        "default": False,
                        "description": "Нумерация экземпляров (постпечать).",
                    },
                    "option_barcode": {
                        "type": "boolean",
                        "default": False,
                        "description": "Штрихкод на каждое изделие.",
                    },
                    "option_variable_data": {
                        "type": "boolean",
                        "default": False,
                        "description": "Переменные данные / персонализация в макете.",
                    },
                    "option_rounding": {
                        "type": "boolean",
                        "default": False,
                        "description": "Скругление углов после печати.",
                    },
                    "holes_per_item": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": _MAX_HOLES_PER_ITEM,
                        "default": 0,
                        "description": "Число пробиваемых отверстий на одно изделие; 0 — не считать пробивку.",
                    },
                    "crease_lines_per_item": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": _MAX_CREASE_LINES,
                        "default": 0,
                        "description": "Число линий биговки на одно изделие; 0 — не считать биговку.",
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
        # JS calcPrintSheet.js:48-49: при margins == -1 поля принтера не прибавляются.
        skip_printer_margins = margins_param == -1
        if margins_param is not None and not skip_printer_margins:
            sum_margins = list(margins_param) if isinstance(margins_param, (list, tuple)) else [0, 0, 0, 0]
        else:
            sum_margins = [0, 0, 0, 0]
        interval = float(params.get("interval", 0) or 0)
        material_id = str(params.get("material_id", "") or "").strip()
        printer_code = str(params.get("printer_code", "") or PRINTER_CODE).strip() or PRINTER_CODE
        lamination_id = str(params.get("lamination_id", "") or "").strip()
        lamination_double_side = bool(params.get("lamination_double_side", True))
        mode = ProductionMode(int(params.get("mode", 1)))
        # Качество струйной печати: явное или по умолчанию как в calcPrintSheet.
        if "quality" in params and params.get("quality") is not None:
            quality = int(params.get("quality"))
        else:
            quality = int(_INKJET_DEFAULT_QUALITY.get(printer_code, 1))

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
        if color != "0+0" and sum_margins and not skip_printer_margins:
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

        is_inkjet = printer_code in INKJET_PRINTERS
        print_weight_kg: Optional[float] = None

        if is_inkjet:
            # Как calcPrintSheet: EPSONWF7610 / DTFTransfer → calcPrintInkJet (порт PrintInkjetCalculator).
            # defectsPrinter для материала — без mode-надбавки (её применяет сам inkjet).
            defects_printer = printer.get_defect_rate(float(num_sheet_to_print))
            inkjet_result = PrintInkjetCalculator().calculate(
                {
                    "num_sheet": int(num_sheet_to_print),
                    "width": float(size_sheet[0]),
                    "height": float(size_sheet[1]),
                    "quality": quality,
                    "color": color,
                    "material_id": material_id,
                    "printer_code": printer_code,
                    "mode": mode.value,
                }
            )
            cost_print_total = float(inkjet_result.get("cost", 0.0))
            price_print = float(inkjet_result.get("price", 0.0))
            time_print = float(inkjet_result.get("time_hours", 0.0))
            print_time_ready = float(inkjet_result.get("time_ready", 0.0))
            print_weight_kg = float(inkjet_result.get("weight_kg", 0.0))
        else:
            # Печать (лазерная логика как в calcPrintLaser).
            defects_printer = printer.get_defect_rate(float(num_sheet_to_print))
            if mode.value >= 2:
                defects_printer += defects_printer * (mode.value - 1)
            # JS: time — ceil(n*(1+d)); cost расходников — n*(1+d) без ceil.
            sheets_with_defects = num_sheet_to_print * (1 + defects_printer)
            sheets_for_time = math.ceil(sheets_with_defects)

            coeff_size = 1.0
            half_sheet = [max_printer[0], max_printer[1] / 2.0]
            layout_half = layout_on_sheet(size_sheet, half_sheet, None, 0.0)
            if layout_half["num"] > 0:
                coeff_size = 0.5
            sheets_per_hour = printer.get_sheets_per_hour(getattr(material, "density", 80) or 80)
            if sheets_per_hour <= 0:
                sheets_per_hour = 250.0
            double_side = 2 if color in ("1+1", "4+1", "4+4") else 1
            # JS calcPrintLaser: timePrepare * modeProduction (без max(1, …))
            time_prepare = (printer.time_prepare or 0.1) * mode.value
            time_print_raw = (
                sheets_for_time / sheets_per_hour * coeff_size * double_side + time_prepare
            )
            time_operator = time_print_raw * 0.5 * (1 + defects_printer) + time_prepare

            cost_print_sheet_list = getattr(printer, "cost_print_sheet", None) or [4.0, 12.0]
            cost_per_sheet_val = _cost_per_sheet_laser(color, cost_print_sheet_list)
            # JS: себестоимость от сырого timePrint
            cost_depreciation = printer.depreciation_per_hour * time_print_raw
            cost_consumables = cost_per_sheet_val * coeff_size * sheets_with_defects
            cost_print = cost_depreciation + cost_consumables
            cost_operator = time_operator * printer.operator_cost_per_hour
            cost_print_total = cost_print + cost_operator
            margin_print_laser = get_margin("marginPrintLaser")
            price_print = cost_print * (1 + MARGIN_MATERIAL + margin_print_laser) + cost_operator * (
                1 + MARGIN_OPERATION + margin_print_laser
            )
            # JS: Math.ceil(timePrint * 100) / 100 до timeReady / вклада в сумму
            time_print = math.ceil(time_print_raw * 100) / 100.0
            # JS calcPrintLaser: timeReady = time + baseTimeReady принтера (не листа)
            printer_base_list = printer.base_time_ready or get_time_ready("baseTimeReady")
            idx_printer = max(0, min(len(printer_base_list) - 1, int(math.ceil(mode.value))))
            print_time_ready = time_print + float(printer_base_list[idx_printer])

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

        no_cut = bool(params.get("no_cut", False))

        if not no_cut:
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

        opt_cost, opt_price, opt_time = _print_sheet_extra_options(
            params, quantity, size, material_id, mode.value
        )

        cost = (
            cost_material
            + cost_cut
            + cost_print_total
            + cost_lamination
            + cost_cut_guillotine
            + opt_cost
        )
        # JS: result.price = (costMaterial*(1+marginMaterial) + costCut.price + costPrint.price + …) * (1+marginPrintSheet)
        # price_print уже посчитан выше (лазер / inkjet).
        price_material = cost_material * (1 + MARGIN_MATERIAL)
        margin_print_sheet = get_margin("marginPrintSheet")
        # JS calcPrintSheet: без Math.ceil на price (лазер и струйная).
        price = (
            price_material
            + price_print
            + price_cut_guillotine
            + price_lamination
            + opt_price
        ) * (1 + margin_print_sheet)

        time_total = time_print + time_cut + time_lamination + time_cut_guillotine + opt_time
        # В JS: result.time = Math.ceil((costCut.time+costPrint.time+…)*100)/100
        time_hours = math.ceil(time_total * 100) / 100.0
        base_time_ready_list = get_time_ready("baseTimeReadyPrintSheet")
        idx = max(0, min(len(base_time_ready_list) - 1, mode.value))
        base_ready = float(base_time_ready_list[idx])
        # JS: result.timeReady = result.time + Math.max(baseTimeReady, costPrint.timeReady)
        if print_time_ready is None:
            print_time_ready = time_print + base_ready
        time_ready = time_hours + max(base_ready, print_time_ready)

        # Лазер: вес по тиражу и размеру изделия. Решение человека 11.11.2026: это верный вес.
        # JS calcPrintSheet → calcPrintLaser считает calcWeight(numSheet, sizeSheet) —
        # весь лист, включая обрезь, поэтому JS тяжелее (вымпел 50×80×120: JS 0.1328, Python 0.1052).
        # Струй: вес из calcPrintInkJet + ламинация.
        weight_kg = 0.0
        if is_inkjet and print_weight_kg is not None:
            weight_kg = float(print_weight_kg)
        else:
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

        # Размер листа из каталога (как material.size в JS calcPrintSheet).
        catalog_size = material.sizes[0] if material.sizes else size_sheet
        materials_out: List[Dict[str, Any]] = [
            {
                "code": material.code,
                "name": material.description,
                "title": material.title,
                "quantity": num_sheets_physical,
                "unit": "лист",
                "size_mm": [float(catalog_size[0]), float(catalog_size[1])],
            }
        ]
        if lamination_result:
            for m in lamination_result.get("materials") or []:
                materials_out.append(m)

        # JS: price без округления до рубля (и лазер, и струйная).
        return {
            "cost": float(cost),
            "price": float(price),
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
