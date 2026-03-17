"""
Калькулятор термопереноса.

Мигрировано из js_legacy/calc/calcHeatPress.js.
Типы трансфера: сублимация, DTF, шелкотрансфер.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Mapping

import json5

from calculators.base import BaseCalculator, ProductionMode
from calculators.print_sheet import PrintSheetCalculator
from common.markups import MARGIN_MATERIAL, MARGIN_OPERATION, get_margin
from common.process_tools import calc_silk_print
from equipment import heatpress as heatpress_catalog

HEATPRESS_JSON = Path(__file__).parent.parent / "data" / "equipment" / "heatpress.json"
SUBLIMATION_MATERIAL = "PaperSublimation128"
SUBLIMATION_PRINTER = "EPSONWF7610"
DTF_MATERIAL = "PaperDTFTransfer"
DTF_PRINTER = "DTFTransfer"
ITEM_HEATPRESS_MAP = {
    "hat": "Grafalex",
    "mug": "EconopressMUGH",
    "tshirt": "SahokSH49BD",
    "clothes": "SahokSH49BD",
    "bag": "SahokSH49BD",
    "metal": "SahokSH49BD",
}
ITEM_DIFFICULTY = {"clothes": 1, "bag": 1}


def _load_heatpress_raw(code: str) -> Dict[str, Any]:
    with open(HEATPRESS_JSON, "r", encoding="utf-8") as f:
        data = json5.load(f)
    return data.get(code, {})


class HeatPressCalculator(BaseCalculator):
    """Термоперенос: сублимация, DTF, шелкотрансфер."""

    slug = "heat_press"
    name = "Термоперенос"
    description = "Расчёт термопереноса на ткани и изделия: сублимация, DTF, шелкотрансфер."

    def get_param_schema(self) -> Dict[str, Any]:
        return {
            "slug": self.slug,
            "title": self.name,
            "params": [
                {"name": "quantity", "type": "integer", "required": True, "title": "Тираж", "validation": {"min": 1}},
                {"name": "width", "type": "number", "required": True, "title": "Ширина нанесения (мм)", "unit": "мм"},
                {"name": "height", "type": "number", "required": True, "title": "Высота нанесения (мм)", "unit": "мм"},
                {"name": "transfer_type", "type": "enum", "required": True, "title": "Тип трансфера",
                 "choices": {"inline": [
                     {"id": "sublimation", "title": "Сублимация"},
                     {"id": "dtf", "title": "DTF"},
                     {"id": "silk", "title": "Шелкотрансфер"},
                 ]}},
                {"name": "item_type", "type": "enum", "required": False, "default": "tshirt", "title": "Тип изделия",
                 "choices": {"inline": [
                     {"id": "hat", "title": "Головной убор"},
                     {"id": "mug", "title": "Кружка"},
                     {"id": "tshirt", "title": "Футболка"},
                     {"id": "clothes", "title": "Плотная одежда"},
                     {"id": "bag", "title": "Сумка/рюкзак"},
                     {"id": "metal", "title": "Металл"},
                 ]}},
                {"name": "silk_colors", "type": "integer", "required": False, "default": 1, "title": "Кол-во цветов (шелк)"},
                {"name": "mode", "type": "integer", "required": False, "default": 1, "title": "Режим"},
            ],
            "param_groups": {
                "main": ["quantity", "width", "height"],
                "processing": ["transfer_type", "item_type", "silk_colors"],
                "mode": ["mode"],
            },
        }

    def get_options(self) -> Dict[str, Any]:
        heatpresses = []
        try:
            for code, spec in heatpress_catalog._items.items():
                heatpresses.append({"code": code, "name": spec.name})
        except Exception:
            pass
        return {
            "heatpresses": heatpresses,
            "transfer_types": ["sublimation", "dtf", "silk"],
            "item_types": list(ITEM_HEATPRESS_MAP.keys()),
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
                    "width": {"type": "number", "minimum": 1, "description": "Ширина нанесения, мм"},
                    "height": {"type": "number", "minimum": 1, "description": "Высота нанесения, мм"},
                    "transfer_type": {"type": "string", "enum": ["sublimation", "dtf", "silk"], "description": "Тип трансфера"},
                    "item_type": {"type": "string", "enum": list(ITEM_HEATPRESS_MAP.keys()), "default": "tshirt"},
                    "silk_colors": {"type": "integer", "default": 1, "description": "Кол-во цветов для шелка"},
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["quantity", "width", "height", "transfer_type"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        n = int(params.get("quantity", 1))
        width = float(params.get("width", 0))
        height = float(params.get("height", 0))
        size = [width, height]
        transfer_type = str(params.get("transfer_type", "sublimation")).strip().lower()
        item_type = str(params.get("item_type", "tshirt") or "tshirt").strip().lower()
        silk_colors = int(params.get("silk_colors", 1) or 1)
        mode = ProductionMode(int(params.get("mode", 1)))

        heatpress_code = ITEM_HEATPRESS_MAP.get(item_type, "SahokSH49BD")
        heatpress = heatpress_catalog.get(heatpress_code)
        heatpress_raw = _load_heatpress_raw(heatpress_code)

        defects = heatpress.get_defect_rate(float(n))
        if mode.value > 1:
            defects += defects * (mode.value - 1)
        num_with_defects = int(round(n * (1 + defects)))

        item_difficulty = ITEM_DIFFICULTY.get(item_type, 0)
        time_load_arr = heatpress_raw.get("timeLoad", [0.02, 0.05])
        time_load = float(time_load_arr[item_difficulty]) if item_difficulty < len(time_load_arr) else float(time_load_arr[0])
        base_time_ready = heatpress_raw.get("baseTimeReady", [16, 8, 1])
        idx = min(max(0, mode.value), len(base_time_ready) - 1)
        base_ready = float(base_time_ready[idx])

        cost_transfer = 0.0
        price_transfer = 0.0
        time_transfer = 0.0
        weight_transfer = 0.0
        materials_out: List[Dict[str, Any]] = []

        if transfer_type == "sublimation":
            print_calc = PrintSheetCalculator()
            print_params = {
                "quantity": num_with_defects,
                "width": size[0],
                "height": size[1],
                "color": "4+0",
                "margins": [0, 0, 0, 0],
                "interval": 2,
                "material_id": SUBLIMATION_MATERIAL,
                "printer_code": SUBLIMATION_PRINTER,
                "mode": mode.value,
            }
            print_result = print_calc.calculate(print_params)
            cost_transfer = float(print_result.get("cost", 0))
            price_transfer = float(print_result.get("price", 0))
            time_transfer = float(print_result.get("time_hours", 0))
            weight_transfer = float(print_result.get("weight_kg", 0))
            materials_out = list(print_result.get("materials") or [])
            time_press_per_item = 35 / 3600.0

        elif transfer_type == "dtf":
            print_calc = PrintSheetCalculator()
            print_params = {
                "quantity": num_with_defects,
                "width": size[0],
                "height": size[1],
                "color": "4+0",
                "margins": [2, 2, 2, 2],
                "interval": 2,
                "material_id": DTF_MATERIAL,
                "printer_code": DTF_PRINTER,
                "mode": mode.value,
            }
            try:
                print_result = print_calc.calculate(print_params)
                cost_transfer = float(print_result.get("cost", 0))
                price_transfer = float(print_result.get("price", 0))
                time_transfer = float(print_result.get("time_hours", 0))
                weight_transfer = float(print_result.get("weight_kg", 0))
                materials_out = list(print_result.get("materials") or [])
            except KeyError:
                pass
            time_press_per_item = 15 / 3600.0

        elif transfer_type == "silk":
            silk_result = calc_silk_print(
                num_with_defects,
                size,
                silk_colors,
                "transfer",
                mode=mode.value,
            )
            cost_transfer = silk_result.cost
            price_transfer = silk_result.price
            time_transfer = silk_result.time_hours
            materials_out = list(silk_result.materials)
            time_press_per_item = 10 / 3600.0

        else:
            raise ValueError(f"Неизвестный тип трансфера: {transfer_type!r}")

        time_press_total = (time_press_per_item + time_load) * num_with_defects
        time_prepare = float(heatpress_raw.get("timePrepare", 0.05)) * max(1, mode.value)
        time_operator = time_press_total + time_prepare

        cost_depreciation_hour = heatpress.depreciation_per_hour
        cost_power = float(heatpress_raw.get("costPower", 5.0))
        power_per_hour = float(heatpress_raw.get("powerPerHour", 2.0))
        cost_press_per_hour = cost_power * power_per_hour
        cost_press = cost_depreciation_hour * time_press_total + cost_press_per_hour * time_press_total
        cost_operator = time_operator * heatpress.operator_cost_per_hour

        cost_total = cost_operator + cost_press + cost_transfer
        margin_heatpress = get_margin("marginHeatPress")
        price_total = (
            cost_operator * (1 + MARGIN_OPERATION)
            + cost_press * (1 + MARGIN_MATERIAL)
            + price_transfer
        ) * (1 + margin_heatpress)

        time_hours = time_operator + time_transfer
        time_ready = time_hours + base_ready

        return {
            "cost": float(cost_total),
            "price": int(math.ceil(price_total)),
            "unit_price": float(price_total) / max(1, n),
            "time_hours": math.ceil(time_hours * 100) / 100,
            "time_ready": time_ready,
            "weight_kg": weight_transfer,
            "materials": materials_out,
        }
