"""
Калькулятор тиснения (горячее тиснение).

Перенесено из js_legacy/calc/calcEmbossing.js.
Тиснение блинтовое или фольгой: клише (опционально) + стоимость тиснения по тиражу + доставка.
"""

from __future__ import annotations

import json5
import math
from pathlib import Path
from typing import Any, Dict, List, Mapping

from calculators.base import BaseCalculator, ProductionMode
from common.markups import (
    BASE_TIME_READY,
    COST_OPERATOR,
    MARGIN_MATERIAL,
    MARGIN_OPERATION,
    get_margin,
)
from common.process_tools import calc_shipment

_TOOLS_JSON = Path(__file__).parent.parent / "data" / "equipment" / "tools.json"


def _load_tools_raw() -> Dict[str, Any]:
    with open(_TOOLS_JSON, "r", encoding="utf-8") as f:
        return json5.load(f)


def _find_cost_for_quantity(cost_table: List[List[float]], n: int) -> float:
    """Найти стоимость за штуку по таблице [[порог, руб/шт], ...]."""
    if not cost_table:
        return 0.0
    for threshold, cost_per_unit in sorted(cost_table, key=lambda x: x[0]):
        if n <= threshold:
            return float(cost_per_unit)
    return float(cost_table[-1][1]) if cost_table else 0.0


def _calc_cliche(size: List[float], mode: int) -> Dict[str, Any]:
    """
    Расчёт стоимости изготовления клише.
    size: [ширина, высота] в мм
    """
    raw = _load_tools_raw()
    tool = raw.get("Cliche")
    if not tool:
        return {"cost": 0.0, "price": 0.0, "time": 0.0, "time_ready": 0.0, "weight": 0.0, "materials": []}

    cost_per_cm2 = float(tool.get("cost", 50))
    min_cost = float(tool.get("minCostCliche", 1100))
    time_prepare = float(tool.get("timePrepare", 0.25)) * mode
    weight_per_cm2 = float(tool.get("weight", 1.0))  # гр/см2

    area_cm2 = size[0] * size[1] / 100.0
    cost_material = max(cost_per_cm2 * area_cm2, min_cost)
    cost_operator = time_prepare * COST_OPERATOR
    weight_kg = weight_per_cm2 * area_cm2 / 1000.0

    size_3d = [size[0], size[1], 20]
    cost_ship = calc_shipment(1, size_3d, weight_kg, "Own")

    cost = cost_material + cost_ship.cost + cost_operator
    price = (
        cost_ship.price
        + cost_material * (1 + MARGIN_MATERIAL)
        + cost_operator * (1 + MARGIN_OPERATION)
    )

    base_time_ready = tool.get("baseTimeReady") or BASE_TIME_READY
    idx = max(0, min(len(base_time_ready) - 1, math.ceil(mode)))
    time_ready = time_prepare + float(base_time_ready[idx])

    materials = [
        {
            "code": "cliche",
            "name": "Клише",
            "title": "Клише",
            "size_mm": size,
            "quantity": 1,
            "unit": "шт",
        }
    ]

    return {
        "cost": cost,
        "price": price,
        "time": time_prepare,
        "time_ready": time_ready,
        "weight": weight_kg,
        "materials": materials,
    }


class EmbossingCalculator(BaseCalculator):
    """Тиснение блинтовое или фольгой."""

    slug = "embossing"
    name = "Тиснение"
    description = "Расчёт стоимости тиснения (блинт или фольга): клише + тиснение + доставка."

    def get_param_schema(self) -> Dict[str, Any]:
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
                    "name": "cliche_width_mm",
                    "type": "number",
                    "required": True,
                    "title": "Ширина клише (мм)",
                    "description": "Ширина области тиснения",
                    "validation": {"min": 1, "max": 500},
                    "unit": "мм",
                },
                {
                    "name": "cliche_height_mm",
                    "type": "number",
                    "required": True,
                    "title": "Высота клише (мм)",
                    "description": "Высота области тиснения",
                    "validation": {"min": 1, "max": 500},
                    "unit": "мм",
                },
                {
                    "name": "embossing_type",
                    "type": "enum",
                    "required": True,
                    "default": "foil",
                    "title": "Вид тиснения",
                    "description": "Блинт или фольга",
                    "choices": {
                        "inline": [
                            {"id": "blind", "title": "Блинтовое"},
                            {"id": "foil", "title": "Фольгой"},
                        ]
                    },
                },
                {
                    "name": "item_type",
                    "type": "enum",
                    "required": False,
                    "default": "other",
                    "title": "Тип изделия",
                    "description": "Для расчёта доставки",
                    "choices": {
                        "inline": [
                            {"id": "diary", "title": "Ежедневник"},
                            {"id": "planning", "title": "Планинг"},
                            {"id": "cardholder", "title": "Визитница"},
                            {"id": "other", "title": "Другое"},
                        ]
                    },
                },
                {
                    "name": "is_cliche",
                    "type": "boolean",
                    "required": False,
                    "default": True,
                    "title": "Изготовление клише",
                    "description": "Включить стоимость клише в расчёт",
                },
                {
                    "name": "mode",
                    "type": "enum",
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
            "param_groups": {
                "main": ["quantity", "cliche_width_mm", "cliche_height_mm"],
                "options": ["embossing_type", "item_type", "is_cliche"],
                "mode": ["mode"],
            },
        }

    def get_options(self) -> Dict[str, Any]:
        return {
            "embossing_types": [
                {"id": "blind", "title": "Блинтовое"},
                {"id": "foil", "title": "Фольгой"},
            ],
            "item_types": [
                {"id": "diary", "title": "Ежедневник"},
                {"id": "planning", "title": "Планинг"},
                {"id": "cardholder", "title": "Визитница"},
                {"id": "other", "title": "Другое"},
            ],
            "modes": [
                {"value": 0, "label": "Экономичный"},
                {"value": 1, "label": "Стандартный"},
                {"value": 2, "label": "Экспресс"},
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
                    "cliche_width_mm": {"type": "number", "minimum": 1, "description": "Ширина клише, мм"},
                    "cliche_height_mm": {"type": "number", "minimum": 1, "description": "Высота клише, мм"},
                    "embossing_type": {
                        "type": "string",
                        "enum": ["blind", "foil"],
                        "description": "Вид тиснения: blind — блинт, foil — фольгой",
                    },
                    "item_type": {
                        "type": "string",
                        "enum": ["diary", "planning", "cardholder", "other"],
                        "description": "Тип изделия для доставки",
                    },
                    "is_cliche": {"type": "boolean", "description": "Включить изготовление клише"},
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["quantity", "cliche_width_mm", "cliche_height_mm"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        quantity = int(params.get("quantity", 1))
        cliche_w = float(params.get("cliche_width_mm", 0) or params.get("cliche_width", 0))
        cliche_h = float(params.get("cliche_height_mm", 0) or params.get("cliche_height", 0))
        embossing_type = str(params.get("embossing_type", "foil") or "foil").strip().lower()
        item_type = str(params.get("item_type", "other") or "other").strip().lower()
        is_cliche = bool(params.get("is_cliche", True))
        mode = ProductionMode(int(params.get("mode", 1)))

        if cliche_w <= 0 or cliche_h <= 0:
            raise ValueError("Ширина и высота клише должны быть положительными")

        size_cliche = [cliche_w, cliche_h]
        raw = _load_tools_raw()
        tool_emb = raw.get("Embossing")
        if not tool_emb:
            raise ValueError("Не найдены данные оборудования тиснения в tools.json")

        cost_cliche = {"cost": 0.0, "price": 0.0, "time": 0.0, "time_ready": 0.0, "weight": 0.0, "materials": []}
        if is_cliche:
            cost_cliche = _calc_cliche(size_cliche, max(1, mode.value))

        emb_cost_data = tool_emb.get("cost", {}).get(embossing_type)
        if not emb_cost_data:
            emb_cost_data = tool_emb.get("cost", {}).get("foil", {})
        cost_table = emb_cost_data.get("cost", [[2000, 11.0]])
        min_cost = float(emb_cost_data.get("minCost", 2000))

        time_prepare = float(tool_emb.get("timePrepare", 0)) * max(1, mode.value)
        cost_operator = time_prepare * COST_OPERATOR

        cost_per_unit = _find_cost_for_quantity(cost_table, quantity)
        cost_embossing = max(min_cost, cost_per_unit * quantity) + cost_operator
        price_embossing = cost_embossing * (1 + MARGIN_MATERIAL) + cost_operator * (1 + MARGIN_OPERATION)

        item_sizes = {
            "diary": ([150, 210, 20], 0.1),
            "planning": ([210, 100, 10], 0.1),
            "cardholder": ([100, 100, 5], 0.02),
        }
        size_item, weight_item = item_sizes.get(item_type, ([100, 100, 10], 0.05))
        cost_ship = calc_shipment(quantity, size_item, weight_item, "Own")

        cost_total = cost_cliche["cost"] + cost_embossing + cost_ship.cost
        margin_emb = get_margin("marginEmbossing")
        price_total = (cost_cliche["price"] + price_embossing + cost_ship.price) * (1 + margin_emb)

        time_total = cost_cliche["time"] + time_prepare + cost_ship.time_hours
        base_time_ready = tool_emb.get("baseTimeReady") or BASE_TIME_READY
        idx = max(0, min(len(base_time_ready) - 1, math.ceil(mode.value)))
        time_ready = time_total + max(cost_cliche["time_ready"], float(base_time_ready[idx]))
        weight_kg = cost_cliche["weight"]

        materials: List[Dict[str, Any]] = list(cost_cliche.get("materials", []))

        return {
            "cost": float(cost_total),
            "price": math.ceil(price_total),
            "unit_price": math.ceil(price_total) / max(1, quantity),
            "time_hours": round(time_total, 2),
            "time_ready": time_ready,
            "weight_kg": weight_kg,
            "materials": materials,
        }
