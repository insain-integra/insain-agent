"""
Калькулятор СТРУЙНОЙ / СУБЛИМАЦИОННОЙ ПЕЧАТИ на листовом принтере.

Мигрировано из js_legacy/calc/calcPrintInkJet.js (calcPrintInkJet).
Считает печать на EPSON WF-7610, DTFTransfer и аналогичных листовых струйных принтерах.

Порт полный: calcLayoutOnSheet, calcWeight. Не перенесено: —
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
)
from equipment import printer as printer_catalog
from materials import sheet as sheet_catalog

DEFAULT_PRINTER = "EPSONWF7610"


def _cost_per_sheet(color: str, cost_list: List[float] | None) -> float:
    """Себестоимость расходников листа по цветности (как в JS)."""
    if not cost_list:
        raise ValueError("Не задана себестоимость печати листа")
    bw = cost_list[0]
    cl = cost_list[1] if len(cost_list) > 1 else cost_list[0]
    mapping = {
        "1+0": bw,
        "1+1": 2 * bw,
        "4+0": cl,
        "4+1": bw + cl,
        "4+4": 2 * cl,
    }
    if color not in mapping:
        raise ValueError("Не задана или неверно задана цветность печати")
    return mapping[color]


def _sheets_per_hour(printer: Any, quality: int) -> float:
    """
    Скорость листов/час: в JS printer.sheetsPerHour[quality] —
    плоский массив [стандарт, высокое, фото].
    """
    by_q = getattr(printer, "sheets_per_hour_by_quality", None) or None
    if by_q:
        idx = max(0, min(len(by_q) - 1, int(quality)))
        rate = float(by_q[idx])
        if rate > 0:
            return rate
    # Запас: таблица по плотности (лазерный формат) — не используется струйным JS
    sph_table = printer.sheets_per_hour_table
    if sph_table:
        idx = max(0, min(len(sph_table) - 1, int(quality)))
        rate = float(sph_table[idx][1])
        if rate > 0:
            return rate
    raise ValueError("Не задана скорость печати листов (sheetsPerHour)")


class PrintInkjetCalculator(BaseCalculator):
    """Струйная / сублимационная печать на листовом принтере."""

    slug = "print_inkjet"
    name = "Струйная печать"
    description = "Расчёт струйной (сублимационной) печати на листовом принтере."

    def get_options(self) -> Dict[str, Any]:
        materials = sheet_catalog.list_for_frontend()
        return {
            "materials": materials[:60],
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
                    "num_sheet": {"type": "integer", "minimum": 1, "description": "Кол-во листов"},
                    "width": {"type": "number", "minimum": 1, "description": "Ширина листа, мм"},
                    "height": {"type": "number", "minimum": 1, "description": "Высота листа, мм"},
                    "quality": {"type": "integer", "enum": [0, 1, 2], "default": 0, "description": "Качество: 0=стандарт, 1=высокое, 2=фото"},
                    "color": {"type": "string", "description": "Цветность: 1+0, 4+0, 1+1, 4+1, 4+4"},
                    "material_id": {"type": "string", "description": "Код бумаги (из каталога sheet)"},
                    "printer_code": {"type": "string"},
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["num_sheet", "width", "height", "material_id"],
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
                {"name": "quality", "type": "enum", "required": False, "default": 0, "title": "Качество",
                 "choices": {"inline": [{"id": 0, "title": "Стандарт"}, {"id": 1, "title": "Высокое"}, {"id": 2, "title": "Фото"}]}},
                {"name": "color", "type": "enum", "required": False, "default": "4+0", "title": "Цветность",
                 "choices": {"inline": [{"id": "1+0", "title": "1+0"}, {"id": "4+0", "title": "4+0"}, {"id": "1+1", "title": "1+1"}, {"id": "4+1", "title": "4+1"}, {"id": "4+4", "title": "4+4"}]}},
                {"name": "material_id", "type": "enum_cascading", "required": True, "title": "Бумага", "choices": {"source": "materials:sheet"}},
                {"name": "mode", "type": "enum", "required": False, "default": 1, "title": "Режим",
                 "choices": {"inline": [{"id": 0, "title": "Эконом"}, {"id": 1, "title": "Стандарт"}, {"id": 2, "title": "Экспресс"}]}},
            ],
            "param_groups": {"main": ["num_sheet", "width", "height"], "material": ["material_id"], "processing": ["quality", "color"], "mode": ["mode"]},
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        # Как calcPrintInkJet(numSheet, sizeSheet, quality, color, materialID, printerID, modeProduction)
        num_sheet = int(params.get("num_sheet", 1))
        width = float(params.get("width", 0))
        height = float(params.get("height", 0))
        size_sheet = [width, height]
        quality = int(params.get("quality", 0))
        color = str(params.get("color", "4+0") or "4+0").strip()
        material_id = str(params.get("material_id", "")).strip()
        printer_code = str(params.get("printer_code", "") or DEFAULT_PRINTER).strip() or DEFAULT_PRINTER
        mode = ProductionMode(int(params.get("mode", 1)))

        try:
            printer = printer_catalog.get(printer_code)
        except KeyError:
            printer = None
        if not printer:
            return self._empty(mode)

        try:
            material = sheet_catalog.get(material_id)
        except KeyError:
            material = None
        if not material:
            return self._empty(mode)

        # JS: baseTimeReady[Math.ceil(modeProduction)]
        base_time_ready = printer.base_time_ready or BASE_TIME_READY
        idx = max(0, min(len(base_time_ready) - 1, int(math.ceil(mode.value))))
        base_ready = float(base_time_ready[idx])
        # JS: timePrepare * modeProduction (без max(1, …))
        time_prepare = (printer.time_prepare or 0) * float(mode.value)

        max_printer = printer.max_size or [297, 420]
        layout_check = layout_on_sheet(size_sheet, max_printer, None, 0.0)
        if layout_check["num"] == 0:
            raise ValueError("Размер изделия больше допустимого")

        # Коэффициент SRA3 / половина (как layoutOnHalfSheet в JS)
        coeff_size = 1.0
        half = [max_printer[0], max_printer[1] / 2.0]
        if layout_on_sheet(size_sheet, half, None, 0.0)["num"] > 0:
            coeff_size = 0.5

        sheets_per_hour = _sheets_per_hour(printer, quality)

        defects = printer.get_defect_rate(float(num_sheet))
        # JS: defects += modeProduction > 1 ? defects*(modeProduction-1) : 0
        if mode.value > 1:
            defects += defects * (mode.value - 1)

        double_side = 1 if color in ("1+0", "4+0") else 2
        # JS: Math.ceil(numSheet*(1+defects))/sheetsPerHour*coeffSizeSheet*doubleSide+timePrepare
        time_print = (
            math.ceil(num_sheet * (1 + defects)) / sheets_per_hour * coeff_size * double_side
            + time_prepare
        )
        time_operator = time_print * 0.5 * (1 + defects) + time_prepare

        cost_per_sheet_val = _cost_per_sheet(color, printer.cost_print_sheet)
        cost_print = (
            printer.depreciation_per_hour * time_print
            + cost_per_sheet_val * coeff_size * num_sheet * (1 + defects)
        )
        cost_operator = time_operator * printer.operator_cost_per_hour

        cost = cost_print + cost_operator
        margin_extra = get_margin("marginPrintLaser")
        price = (
            cost_print * (1 + MARGIN_MATERIAL + margin_extra)
            + cost_operator * (1 + MARGIN_OPERATION + margin_extra)
        )

        time_hours = math.ceil(time_print * 100) / 100.0
        time_ready = time_hours + base_ready

        weight_kg = calc_weight(
            quantity=num_sheet,
            density=getattr(material, "density", 80) or 80,
            thickness=getattr(material, "thickness", 0) or 0,
            size=size_sheet,
            density_unit=getattr(material, "density_unit", "гм2") or "гм2",
        )

        num_with_defects = math.ceil(num_sheet * (1 + defects))
        materials_out: List[Dict[str, Any]] = [{
            "code": material.code,
            "name": material.description,
            "title": material.title,
            "quantity": num_with_defects,
            "unit": "лист",
        }]

        return {
            "cost": float(cost),
            "price": float(price),
            "unit_price": float(price) / max(1, num_sheet),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": float(weight_kg),
            "materials": materials_out,
        }

    def _empty(self, mode: ProductionMode) -> Dict[str, Any]:
        btr = BASE_TIME_READY
        idx = max(0, min(len(btr) - 1, int(math.ceil(mode.value))))
        return {
            "cost": 0.0, "price": 0.0, "unit_price": 0.0,
            "time_hours": 0.0, "time_ready": float(btr[idx]),
            "weight_kg": 0.0, "materials": [],
        }
