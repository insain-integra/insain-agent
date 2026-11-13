"""
Калькулятор ШИРОКОФОРМАТНОЙ ЛАМИНАЦИИ.

Перенесено из js_legacy/calc/calcLamination.js (calcLaminationWide).
Рулонная ламинация отпечатков на широкоформатном ламинаторе LaminatorWide
плёнкой LaminatDLCLAM (как в JS, плёнка не выбирается). Минимальный объём — 1 м².

Отличия от JS:
- timeReady в JS не задаётся (0); здесь time_hours + базовый срок ламинатора (common.baseTimeReady).
- Расход в materials — метры плёнки по её ширине (в JS — площадь, делённая на ширину в мм).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Mapping

import json5

from calculators.base import BaseCalculator, ProductionMode, material_line
from common.markups import (
    BASE_TIME_READY,
    MARGIN_MATERIAL,
    MARGIN_MIN,
    MARGIN_OPERATION,
    get_margin,
)
from equipment import laminator as laminator_catalog
from materials import get_material

LAMINATOR_CODE = "LaminatorWide"
LAMINAT_ID = "LaminatDLCLAM"
WEIGHT_LAMINAT = 0.0011  # кг / (мкм·м²) плёнки
LAMINATOR_JSON = Path(__file__).parent.parent / "data" / "equipment" / "laminator.json"


def _laminator_cost_operation(code: str) -> float:
    """Себестоимость ламинации за м² (costOperation) — поля нет в EquipmentSpec."""
    with open(LAMINATOR_JSON, "r", encoding="utf-8") as f:
        data = json5.load(f)
    return float((data.get(code) or {}).get("costOperation", 0) or 0)


class LaminationWideCalculator(BaseCalculator):
    """Широкоформатная рулонная ламинация отпечатков."""

    slug = "lamination_wide"
    name = "Широкоформатная ламинация"
    description = (
        "Расчёт рулонной ламинации широкоформатных отпечатков (плёнка 1,52 м). "
        "Минимальный объём — 1 м²."
    )

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
                    "name": "width",
                    "type": "number",
                    "required": True,
                    "title": "Ширина (мм)",
                    "description": "Ширина изделия",
                    "validation": {"min": 1, "max": 5000},
                    "unit": "мм",
                },
                {
                    "name": "height",
                    "type": "number",
                    "required": True,
                    "title": "Высота (мм)",
                    "description": "Высота изделия (0 — минимальный объём 1 м²)",
                    "validation": {"min": 0, "max": 50000},
                    "unit": "мм",
                },
                {
                    "name": "mode",
                    "type": "integer",
                    "required": False,
                    "default": int(ProductionMode.STANDARD),
                    "title": "Режим",
                    "description": "0=эконом, 1=стандарт, 2=экспресс",
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
                "main": ["quantity", "width", "height"],
                "mode": ["mode"],
            },
        }

    def get_options(self) -> Dict[str, Any]:
        return {
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
                    "width": {"type": "number", "minimum": 1, "description": "Ширина изделия, мм"},
                    "height": {"type": "number", "minimum": 0, "description": "Высота изделия, мм"},
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["quantity", "width", "height"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        quantity = int(params.get("quantity", 1))
        w = float(params.get("width", 0) or 0)
        h = float(params.get("height", 0) or 0)
        mode = ProductionMode(int(params.get("mode", ProductionMode.STANDARD)))
        if quantity < 1:
            raise ValueError("Тираж должен быть не меньше 1")
        if w <= 0 or h < 0:
            raise ValueError("Размер изделия должен быть положительным")

        laminator = laminator_catalog.get(LAMINATOR_CODE)
        laminat = get_material("laminat", LAMINAT_ID)
        laminat_width = float(laminat.sizes[0][0])

        defects = laminator.get_defect_rate(float(quantity))
        if mode.value > 1:
            defects += defects * (mode.value - 1)

        vol_material = quantity * w * h * (1 + defects) / 1_000_000  # м²
        if vol_material < 1:
            vol_material = 1.0

        time_prepare = float(laminator.time_prepare or 0) * mode.value
        time_process = vol_material / float(laminator.meter_per_hour) + time_prepare
        time_operator = time_process

        cost_material = float(laminat.cost or 0) * vol_material
        cost_lamination = (
            laminator.depreciation_per_hour * time_process
            + vol_material * _laminator_cost_operation(LAMINATOR_CODE)
        )
        cost_operator = time_operator * laminator.operator_cost_per_hour

        cost = cost_material + cost_lamination + cost_operator
        margin_operation = max(MARGIN_OPERATION + get_margin("marginLaminationWide"), MARGIN_MIN)
        price = (
            cost_material * (1 + MARGIN_MATERIAL)
            + (cost_lamination + cost_operator) * (1 + margin_operation)
        )

        time_hours = math.ceil(time_process * 100) / 100.0
        base_ready = laminator.base_time_ready or BASE_TIME_READY
        idx = max(0, min(len(base_ready) - 1, mode.value))
        time_ready = time_hours + float(base_ready[idx])

        weight_kg = math.ceil(vol_material * float(laminat.density or 0) * WEIGHT_LAMINAT * 100) / 100.0

        materials_out: List[Dict[str, Any]] = [
            material_line(
                code=laminat.code,
                name=laminat.description,
                title=laminat.title,
                quantity=round(vol_material / (laminat_width / 1000.0), 4),
                unit="м",
                size_mm=[laminat_width, 0.0],
            )
        ]

        return {
            "cost": float(cost),
            "price": float(price),
            "unit_price": float(price) / max(1, quantity),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": weight_kg,
            "materials": materials_out,
        }
