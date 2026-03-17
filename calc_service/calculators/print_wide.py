"""
Калькулятор ШИРОКОФОРМАТНОЙ ПЕЧАТИ.

Мигрировано из js_legacy/calc/calcPrintWide.js.
Считает стоимость печати на рулонном широкоформатном принтере (баннер, плёнка, бумага).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping

from calculators.base import BaseCalculator, ProductionMode
from common.helpers import calc_weight
from common.markups import (
    BASE_TIME_READY,
    MARGIN_OPERATION,
    get_margin,
)
from equipment import printer as printer_catalog
from materials import roll as roll_catalog

DEFAULT_PRINTER = "Technojet160ECO"


class PrintWideCalculator(BaseCalculator):
    """Широкоформатная печать на рулонных материалах."""

    slug = "print_wide"
    name = "Широкоформатная печать"
    description = "Расчёт широкоформатной печати на баннере, плёнке, бумаге (рулон)."

    def get_options(self) -> Dict[str, Any]:
        materials = roll_catalog.list_for_frontend()
        printers = []
        try:
            for code, spec in printer_catalog._items.items():
                if spec.cost_print_m2 > 0 or spec.meter_per_hour > 0:
                    printers.append({"code": code, "name": spec.name})
        except Exception:
            printers = [{"code": DEFAULT_PRINTER, "name": "Широкоформатный принтер"}]
        return {
            "materials": materials,
            "printers": printers,
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
                    "width": {"type": "number", "minimum": 1, "description": "Ширина изделия, мм"},
                    "height": {"type": "number", "minimum": 1, "description": "Высота изделия, мм"},
                    "material_id": {"type": "string", "description": "Код материала (из каталога roll)"},
                    "printer_code": {"type": "string", "description": "Код принтера"},
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
                {"name": "width", "type": "number", "required": True, "title": "Ширина (мм)", "unit": "мм", "validation": {"min": 1, "max": 5000}},
                {"name": "height", "type": "number", "required": True, "title": "Высота (мм)", "unit": "мм", "validation": {"min": 1, "max": 50000}},
                {"name": "material_id", "type": "enum_cascading", "required": True, "title": "Материал", "choices": {"source": "materials:roll"}},
                {"name": "printer_code", "type": "enum", "required": False, "title": "Принтер", "default": DEFAULT_PRINTER},
                {"name": "mode", "type": "enum", "required": False, "default": 1, "title": "Режим",
                 "choices": {"inline": [
                     {"id": 0, "title": "Эконом"}, {"id": 1, "title": "Стандарт"}, {"id": 2, "title": "Экспресс"},
                 ]}},
            ],
            "param_groups": {"main": ["quantity", "width", "height"], "material": ["material_id"], "equipment": ["printer_code"], "mode": ["mode"]},
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        quantity = int(params.get("quantity", 1))
        width = float(params.get("width", 0))
        height = float(params.get("height", 0))
        size = [width, height]
        material_id = str(params.get("material_id", "")).strip()
        printer_code = str(params.get("printer_code", "") or DEFAULT_PRINTER).strip() or DEFAULT_PRINTER
        mode = ProductionMode(int(params.get("mode", 1)))

        printer = self._get_printer(printer_code)
        if not printer:
            return self._empty(mode)

        material = self._get_material(material_id)
        if not material:
            return self._empty(mode)

        base_time_ready = printer.base_time_ready or BASE_TIME_READY
        idx = max(0, min(len(base_time_ready) - 1, mode.value))
        base_ready = float(base_time_ready[idx])

        time_prepare = (printer.time_prepare or 0) * max(1, mode.value)
        min_vol = printer.min_vol_print

        defects = printer.get_defect_rate(float(quantity))
        if mode.value >= 2:
            defects += defects * (mode.value - 1)

        vol_print = size[0] * size[1] * (1 + defects) / 1_000_000  # м²
        if min_vol > 0 and vol_print < min_vol:
            vol_print = min_vol

        meter_per_hour = printer.meter_per_hour or 10.0
        time_print = vol_print / meter_per_hour + time_prepare
        time_operator = (time_print + time_prepare) * 0.5

        cost_print = printer.depreciation_per_hour * time_print + printer.cost_print_m2 * vol_print
        cost_operator = time_operator * printer.operator_cost_per_hour

        cost = math.ceil(cost_print + cost_operator)
        margin_wide = get_margin("marginPrintWide")
        price = math.ceil(cost * (1 + MARGIN_OPERATION + margin_wide))

        time_hours = math.ceil(time_print * 100) / 100.0
        time_ready = time_hours + base_ready

        roll_width_m = (material.sizes[0][0] if material.sizes else width) / 1000.0
        length_m = vol_print / roll_width_m if roll_width_m > 0 else 0

        weight_kg = 0.0
        try:
            weight_kg = calc_weight(
                quantity=quantity,
                density=getattr(material, "density", 0) or 0,
                thickness=getattr(material, "thickness", 0) or 0,
                size=size,
                density_unit=getattr(material, "density_unit", "гм2") or "гм2",
            )
        except Exception:
            pass

        materials_out: List[Dict[str, Any]] = [{
            "code": material.code,
            "name": material.description,
            "title": material.title,
            "quantity": round(length_m, 2),
            "unit": "м",
        }]

        return {
            "cost": float(cost),
            "price": float(price),
            "unit_price": float(price) / max(1, quantity),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": round(weight_kg, 3),
            "materials": materials_out,
        }

    # ── helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _get_printer(code: str):
        try:
            return printer_catalog.get(code)
        except KeyError:
            try:
                return printer_catalog.get(DEFAULT_PRINTER)
            except KeyError:
                return None

    @staticmethod
    def _get_material(material_id: str):
        try:
            return roll_catalog.get(material_id)
        except KeyError:
            return None

    def _empty(self, mode: ProductionMode) -> Dict[str, Any]:
        btr = BASE_TIME_READY
        idx = max(0, min(len(btr) - 1, mode.value))
        return {
            "cost": 0.0, "price": 0.0, "unit_price": 0.0,
            "time_hours": 0.0, "time_ready": float(btr[idx]),
            "weight_kg": 0.0, "materials": [],
        }
