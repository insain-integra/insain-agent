"""
Калькулятор кружек с сублимационной печатью.

Перенесено из js_legacy/calc/calcMug.js.
Вызывает порт heat_press (сублимация, item_type=mug) + заготовки кружек.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping

from calculators.base import BaseCalculator, ProductionMode
from calculators.heat_press import HeatPressCalculator
from common.markups import (
    COST_OPERATOR,
    MARGIN_MATERIAL,
    MARGIN_OPERATION,
    get_margin,
)
from equipment import heatpress as heatpress_catalog

MUG_PRINT_SIZE = [214, 82]  # размер нанесения для кружки, мм
MUG_HEATPRESS_CODE = "EconopressMUGH"


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

        heatpress_result = HeatPressCalculator().calculate({
            "quantity": quantity,
            "width": MUG_PRINT_SIZE[0],
            "height": MUG_PRINT_SIZE[1],
            "transfer_type": "sublimation",
            "item_type": "mug",
            "mode": mode,
        })

        heatpress = heatpress_catalog.get(MUG_HEATPRESS_CODE)
        defects = heatpress.get_defect_rate(float(quantity))
        if mode > 1:
            defects += defects * (mode - 1)
        # JS Math.round: половина вверх
        num_with_defects = int(quantity * (1 + defects) + 0.5)

        cost_mug = float(mug.cost or 0) * num_with_defects
        weight_mug = float(mug_raw.get("weight", 0.41)) * quantity

        time_shipment = 16.0 if min_num > 0 else 0.0
        cost_shipment = 500.0 if min_num > 0 else 0.0

        time_packing = 0.006 * quantity if params.get("is_packing") else 0.0
        time_prepare_extra = (1 / 60) * quantity if params.get("is_different") else 0.0
        time_operator_extra = time_packing + time_prepare_extra
        cost_operator_extra = time_operator_extra * COST_OPERATOR

        cost = float(heatpress_result["cost"]) + cost_mug
        margin_mug = get_margin("marginMug")
        price = (
            float(heatpress_result["price"])
            + cost_mug * (1 + MARGIN_MATERIAL)
            + (cost_shipment + cost_operator_extra) * (1 + MARGIN_OPERATION)
        ) * (1 + margin_mug)

        time_hours = math.ceil(
            (time_operator_extra + float(heatpress_result["time_hours"])) * 100
        ) / 100
        weight_kg = math.ceil(
            (float(heatpress_result["weight_kg"]) + weight_mug) * 100
        ) / 100
        # JS: result.time + timeShipment + costHeatPress.timeReady
        time_ready = time_hours + time_shipment + float(heatpress_result["time_ready"])

        materials: List[Dict[str, Any]] = list(heatpress_result.get("materials") or [])
        materials.append({
            "code": mug_id,
            "name": mug.description,
            "title": mug.title,
            "quantity": num_with_defects,
            "unit": "шт",
        })

        return {
            "cost": float(cost),
            "price": float(price),
            "unit_price": float(price) / float(quantity),
            "time_hours": float(time_hours),
            "time_ready": float(time_ready),
            "weight_kg": float(weight_kg),
            "materials": materials,
        }
