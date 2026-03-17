"""
Калькулятор кружек с сублимационной печатью.

Перенесено из js_legacy/calc/calcMug.js.
Использует calcHeatPress (сублимация) + заготовки кружек.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Mapping

import json5

from calculators.base import BaseCalculator, ProductionMode
from calculators.print_sheet import PrintSheetCalculator
from common.markups import (
    COST_OPERATOR,
    MARGIN_MATERIAL,
    MARGIN_OPERATION,
    get_margin,
)

HEATPRESS_JSON = Path(__file__).parent.parent / "data" / "equipment" / "heatpress.json"
MUG_PRINT_SIZE = [214, 82]  # размер нанесения для кружки, мм
SUBLIMATION_MATERIAL = "PaperSublimation128"
SUBLIMATION_PRINTER = "EPSONWF7610"


def _load_heatpress_raw(code: str = "EconopressMUGH") -> Dict[str, Any]:
    """Загрузить сырые данные термопресса для кружек."""
    with open(HEATPRESS_JSON, "r", encoding="utf-8") as f:
        data = json5.load(f)
    return data.get(code, {})


def _calc_heatpress_sublimation(
    n: int,
    size: List[float],
    mode: int,
    heatpress_raw: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Упрощённый расчёт термопереноса сублимацией.
    Аналог calcHeatPress(transferID='sublimation', itemID='mug').
    """
    from equipment import heatpress as heatpress_catalog

    heatpress = heatpress_catalog.get("EconopressMUGH")

    defects = heatpress.get_defect_rate(float(n))
    if mode > 1:
        defects += defects * (mode - 1)
    num_with_defects = int(round(n * (1 + defects)))

    # Печать трансфера через PrintSheetCalculator
    print_calc = PrintSheetCalculator()
    print_params = {
        "quantity": num_with_defects,
        "width": size[0],
        "height": size[1],
        "material_id": SUBLIMATION_MATERIAL,
        "color": "4+0",
        "margins": [0, 0, 0, 0],
        "interval": 2,
        "printer_code": SUBLIMATION_PRINTER,
        "mode": mode,
    }
    cost_transfer_result = print_calc.calculate(print_params)

    cost_transfer = float(cost_transfer_result.get("cost", 0))
    price_transfer = float(cost_transfer_result.get("price", 0))
    time_transfer = float(cost_transfer_result.get("time_hours", 0))
    weight_transfer = float(cost_transfer_result.get("weight_kg", 0))
    time_ready_transfer = float(cost_transfer_result.get("time_ready", 0))
    materials_transfer = cost_transfer_result.get("materials", [])

    # Время переноса: 35 сек на изделие
    time_press_per_item = 35 / 3600.0
    time_load_arr = heatpress_raw.get("timeLoad", [0.02, 0.05])
    time_load = float(time_load_arr[0]) if time_load_arr else 0.02
    time_press_total = (time_press_per_item + time_load) * num_with_defects
    time_prepare = float(heatpress_raw.get("timePrepare", 0.05)) * max(1, mode)
    time_operator = time_press_total + time_prepare

    cost_depreciation_hour = heatpress.depreciation_per_hour
    cost_power = float(heatpress_raw.get("costPower", 5.0))
    power_per_hour = float(heatpress_raw.get("powerPerHour", 0.45))
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

    base_time_ready = heatpress_raw.get("baseTimeReady", [16, 8, 1])
    idx = min(max(0, mode), len(base_time_ready) - 1)
    time_ready = time_operator + time_transfer + float(base_time_ready[idx])

    return {
        "cost": cost_total,
        "price": price_total,
        "time_hours": time_operator + time_transfer,
        "time_ready": time_ready,
        "weight_kg": weight_transfer,
        "materials": materials_transfer,
    }


class MugCalculator(BaseCalculator):
    """Кружки с сублимационной печатью."""

    slug = "mug"
    name = "Кружки"
    description = "Расчёт кружек с сублимационной печатью."

    def get_param_schema(self) -> Dict[str, Any]:
        from materials import mug as mug_catalog

        mugs = mug_catalog.list_for_frontend()
        choices = [{"id": m["code"], "title": m.get("title", m.get("name", m["code"]))} for m in mugs]
        return {
            "slug": self.slug,
            "title": self.name,
            "params": [
                {
                    "name": "quantity",
                    "type": "integer",
                    "required": True,
                    "title": "Тираж",
                    "description": "Количество кружек",
                    "validation": {"min": 1, "max": 10000},
                },
                {
                    "name": "mug_id",
                    "type": "enum",
                    "required": True,
                    "title": "Вид кружки",
                    "description": "Тип заготовки кружки",
                    "choices": {"inline": choices},
                },
                {
                    "name": "is_packing",
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "title": "Упаковка",
                },
                {
                    "name": "is_different",
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "title": "Разные макеты",
                    "description": "Каждая кружка с уникальным дизайном",
                },
                {
                    "name": "mode",
                    "type": "integer",
                    "required": False,
                    "default": int(ProductionMode.STANDARD),
                    "title": "Режим",
                    "choices": {
                        "inline": [
                            {"id": 0, "title": "Эконом"},
                            {"id": 1, "title": "Стандарт"},
                            {"id": 2, "title": "Экспресс"},
                        ]
                    },
                },
            ],
            "param_groups": {"main": ["quantity", "mug_id"], "options": ["is_packing", "is_different"], "mode": ["mode"]},
        }

    def get_options(self) -> Dict[str, Any]:
        from materials import mug as mug_catalog

        return {
            "mugs": mug_catalog.list_for_frontend(),
            "modes": [
                {"value": 0, "label": "Экономичный"},
                {"value": 1, "label": "Стандартный"},
                {"value": 2, "label": "Экспресс"},
            ],
        }

    def get_tool_schema(self) -> Dict[str, Any]:
        return {
            "name": self.slug,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "quantity": {"type": "integer", "minimum": 1, "description": "Тираж, шт."},
                    "mug_id": {
                        "type": "string",
                        "description": "Код кружки: MugStandartWhite, MugColorBorderHandle и т.д.",
                    },
                    "is_packing": {"type": "boolean", "default": False},
                    "is_different": {"type": "boolean", "default": False},
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["quantity", "mug_id"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        from common.process_tools import _get_raw_material
        from materials import mug as mug_catalog

        quantity = int(params.get("quantity", 1))
        mug_id = str(params.get("mug_id", "") or "MugStandartWhite")
        mode = int(params.get("mode", ProductionMode.STANDARD))

        mug = mug_catalog.get(mug_id)
        try:
            mug_raw = _get_raw_material("mug", mug_id)
        except KeyError:
            mug_raw = {}
        min_num = int(mug_raw.get("minNum", 5))
        if quantity < min_num and min_num > 0:
            raise ValueError(f"Минимальный объём заказа данного вида кружек {min_num} шт")

        heatpress_raw = _load_heatpress_raw("EconopressMUGH")
        heatpress_result = _calc_heatpress_sublimation(
            quantity, MUG_PRINT_SIZE, mode, heatpress_raw
        )

        defects = 0.01  # из heatpress defects для кружек
        if mode > 1:
            defects += defects * (mode - 1)
        num_with_defects = int(round(quantity * (1 + defects)))

        cost_mug = float(mug.cost or 0) * num_with_defects
        weight_mug = float(mug_raw.get("weight", 0.41)) * quantity

        time_shipment = 16.0 if min_num > 0 else 0.0
        cost_shipment = 500.0 if min_num > 0 else 0.0

        time_packing = 0.006 * quantity if params.get("is_packing") else 0.0
        time_prepare_extra = (1 / 60) * quantity if params.get("is_different") else 0.0
        time_operator_extra = time_packing + time_prepare_extra
        cost_operator_extra = time_operator_extra * COST_OPERATOR

        cost = heatpress_result["cost"] + cost_mug
        margin_mug = get_margin("marginMug")
        price = (
            heatpress_result["price"]
            + cost_mug * (1 + MARGIN_MATERIAL)
            + (cost_shipment + cost_operator_extra) * (1 + MARGIN_OPERATION)
        ) * (1 + margin_mug)

        time_hours = math.ceil(
            (time_operator_extra + heatpress_result["time_hours"]) * 100
        ) / 100
        weight_kg = math.ceil(
            (heatpress_result["weight_kg"] + weight_mug) * 100
        ) / 100
        time_ready = time_hours + time_shipment + heatpress_result["time_ready"]

        materials: List[Dict[str, Any]] = list(heatpress_result.get("materials", []))
        materials.append({
            "code": mug_id,
            "name": mug.description,
            "title": mug.title,
            "quantity": num_with_defects,
            "unit": "шт",
        })

        return {
            "cost": float(math.ceil(cost)),
            "price": float(math.ceil(price)),
            "unit_price": float(math.ceil(price)) / float(quantity),
            "time_hours": float(time_hours),
            "time_ready": float(time_ready),
            "weight_kg": float(weight_kg),
            "materials": materials,
        }
