"""
Калькулятор УФ-ПЕЧАТИ (планшетной и круговой).

Мигрировано из js_legacy/calc/calcUVPrint.js.
Печать на УФ-принтере (RimalSuvUV или PrintUV) с опциями:
нумерация, штрихкод, переменные данные, материал заказчика.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping

from calculators.base import BaseCalculator, ProductionMode
from common.layout import layout_on_sheet
from common.markups import (
    BASE_TIME_READY,
    MARGIN_OPERATION,
    get_margin,
)
from equipment import printer as printer_catalog

DEFAULT_PRINTER = "RimalSuvUV"


class UVPrintCalculator(BaseCalculator):
    """УФ-печать: планшетная или круговая."""

    slug = "uv_print"
    name = "УФ-печать"
    description = "Расчёт УФ-печати на плоских или цилиндрических изделиях."

    def get_options(self) -> Dict[str, Any]:
        printers = []
        try:
            for code, spec in printer_catalog._items.items():
                if spec.cost_process > 0:
                    printers.append({"code": code, "name": spec.name})
        except Exception:
            printers = [{"code": DEFAULT_PRINTER, "name": "УФ-принтер"}]
        return {
            "printers": printers,
            "colors": ["4+0", "1+0", "4+1", "4+2"],
            "surfaces": ["plain", "round"],
            "resolutions": [
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
                    "quantity": {"type": "integer", "minimum": 1, "description": "Тираж"},
                    "width": {"type": "number", "minimum": 1, "description": "Ширина области печати, мм"},
                    "height": {"type": "number", "minimum": 1, "description": "Высота области печати, мм"},
                    "item_width": {"type": "number", "description": "Ширина изделия, мм"},
                    "item_height": {"type": "number", "description": "Высота изделия, мм"},
                    "resolution": {"type": "integer", "enum": [0, 1, 2], "default": 0, "description": "Качество: 0=стандарт, 1=высокое, 2=фото"},
                    "color": {"type": "string", "default": "4+0", "description": "Цветность: 4+0, 1+0, 4+1, 4+2"},
                    "surface": {"type": "string", "enum": ["plain", "round"], "default": "plain", "description": "Вид: plain=плоская, round=круговая"},
                    "double_application": {"type": "boolean", "default": False, "description": "Двойное нанесение"},
                    "is_customer_material": {"type": "boolean", "default": False, "description": "Материал заказчика (наценка 25%)"},
                    "printer_code": {"type": "string"},
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["quantity", "width", "height"],
            },
        }

    def get_param_schema(self) -> Dict[str, Any]:
        return {
            "slug": self.slug, "title": self.name,
            "params": [
                {"name": "quantity", "type": "integer", "required": True, "title": "Тираж", "validation": {"min": 1}},
                {"name": "width", "type": "number", "required": True, "title": "Ширина печати (мм)", "unit": "мм"},
                {"name": "height", "type": "number", "required": True, "title": "Высота печати (мм)", "unit": "мм"},
                {"name": "item_width", "type": "number", "required": False, "title": "Ширина изделия (мм)", "unit": "мм"},
                {"name": "item_height", "type": "number", "required": False, "title": "Высота изделия (мм)", "unit": "мм"},
                {"name": "resolution", "type": "enum", "required": False, "default": 0, "title": "Качество",
                 "choices": {"inline": [{"id": 0, "title": "Стандарт"}, {"id": 1, "title": "Высокое"}, {"id": 2, "title": "Фото"}]}},
                {"name": "color", "type": "enum", "required": False, "default": "4+0", "title": "Цветность",
                 "choices": {"inline": [{"id": "4+0", "title": "4+0"}, {"id": "1+0", "title": "1+0"}, {"id": "4+1", "title": "4+1"}, {"id": "4+2", "title": "4+2"}]}},
                {"name": "surface", "type": "enum", "required": False, "default": "plain", "title": "Поверхность",
                 "choices": {"inline": [{"id": "plain", "title": "Плоская"}, {"id": "round", "title": "Круговая"}]}},
                {"name": "mode", "type": "enum", "required": False, "default": 1, "title": "Режим",
                 "choices": {"inline": [{"id": 0, "title": "Эконом"}, {"id": 1, "title": "Стандарт"}, {"id": 2, "title": "Экспресс"}]}},
            ],
            "param_groups": {"main": ["quantity", "width", "height", "item_width", "item_height"], "processing": ["resolution", "color", "surface"], "mode": ["mode"]},
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        n = int(params.get("quantity", 1))
        width = float(params.get("width", 0))
        height = float(params.get("height", 0))
        size = [width, height]  # область печати
        item_width = float(params.get("item_width", 0) or width)
        item_height = float(params.get("item_height", 0) or height)
        size_item = [item_width, item_height]
        resolution = int(params.get("resolution", 0))
        color = str(params.get("color", "4+0") or "4+0").strip()
        surface = str(params.get("surface", "plain") or "plain").strip()
        double_app = 2 if params.get("double_application") else 1
        is_customer_material = bool(params.get("is_customer_material", False))
        printer_code = str(params.get("printer_code", "") or DEFAULT_PRINTER).strip() or DEFAULT_PRINTER
        mode = ProductionMode(int(params.get("mode", 1)))

        try:
            printer = printer_catalog.get(printer_code)
        except KeyError:
            try:
                printer = printer_catalog.get(DEFAULT_PRINTER)
            except KeyError:
                return self._empty(mode)

        base_time_ready = printer.base_time_ready or BASE_TIME_READY
        idx = max(0, min(len(base_time_ready) - 1, mode.value))
        base_ready = float(base_time_ready[idx])

        margins_printer = list(printer.margins or [25, 25, 25, 25])
        if len(margins_printer) < 4:
            margins_printer = [25, 25, 25, 25]

        defects = printer.get_defect_rate(float(n))
        if mode.value >= 2:
            defects += defects * (mode.value - 1)

        max_size = printer.max_size or [600, 800]
        interval = 5
        layout = layout_on_sheet(size_item, max_size, margins_printer, float(interval))
        if layout["num"] == 0:
            raise ValueError("Размер изделия больше допустимого для принтера")

        # Объёмы печати
        if surface == "plain":
            items_per_load = max(1, layout["num"])
            num_loads = math.ceil(n / items_per_load)
            vol_print = size[0] * size[1] * n / 1_000_000  # м²
            vol_material = size[0] * size[1] * n * (1 + defects) / 1_000_000
            time_prepare = (printer.time_prepare or 0.2) * max(1, mode.value)
        else:
            num_loads = math.ceil(n * (1 + defects))
            vol_material = size[0] * size[1] * num_loads / 1_000_000
            vol_print = vol_material
            time_load_each = getattr(printer, "time_prepare", 0.05)
            time_prepare = time_load_each * max(1, mode.value)

        vol_print *= double_app
        num_loads *= double_app

        # Скорость
        raw_mph = printer.meter_per_hour
        if printer.meter_per_hour_table and resolution < len(printer.meter_per_hour_table):
            meter_per_hour = printer.meter_per_hour_table[resolution][1]
        elif raw_mph > 0:
            meter_per_hour = raw_mph
        else:
            meter_per_hour = 1.0

        # Коэффициент цветности
        coeff = 1
        if color == "4+1":
            coeff = 2
        elif color == "4+2":
            coeff = 3
        meter_per_hour /= coeff

        time_load_total = (printer.time_load or 0) * num_loads
        time_prepare += time_load_total
        time_print = vol_print * (1 + defects) / meter_per_hour + time_prepare
        time_operator = 0.5 * (time_print + time_prepare)

        # Скидка от объёма (discount table)
        discount = 0.0

        # Стоимость печати по цветности
        cost_process_list = []
        if printer.cost_process > 0:
            cost_process_list = [printer.cost_process, printer.cost_process, printer.cost_process]
        else:
            cost_process_list = [950, 950, 950]

        cost_per_m2 = 0.0
        if color in ("4+0", "1+0"):
            cost_per_m2 = cost_process_list[0]
        elif color == "4+1":
            cost_per_m2 = cost_process_list[0] + (cost_process_list[1] if len(cost_process_list) > 1 else 0)
        elif color == "4+2":
            cost_per_m2 = sum(cost_process_list[:3])
        if cost_per_m2 == 0:
            cost_per_m2 = cost_process_list[0]

        cost_print = printer.depreciation_per_hour * time_print + cost_per_m2 * (1 - discount) * vol_print
        cost_operator = time_operator * printer.operator_cost_per_hour

        coeff_customer = 1.25 if is_customer_material else 1.0
        cost = math.ceil(cost_print + cost_operator) * coeff_customer

        margin_uv = get_margin("marginUVPrint")
        price = math.ceil(cost * (1 + MARGIN_OPERATION + margin_uv))

        time_hours = math.ceil(time_print * 100) / 100.0
        time_ready = time_hours + base_ready

        return {
            "cost": float(cost),
            "price": float(price),
            "unit_price": float(price) / max(1, n),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": 0.0,
            "materials": [],
        }

    def _empty(self, mode: ProductionMode) -> Dict[str, Any]:
        btr = BASE_TIME_READY
        idx = max(0, min(len(btr) - 1, mode.value))
        return {
            "cost": 0.0, "price": 0.0, "unit_price": 0.0,
            "time_hours": 0.0, "time_ready": float(btr[idx]),
            "weight_kg": 0.0, "materials": [],
        }
