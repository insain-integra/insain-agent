"""
Калькулятор ламинации.

Перенесено из js_legacy/calc/calcLamination.js.
Параметры: тираж, размер изделия, пленка (laminat), односторонняя/двусторонняя, режим.
Рулонная или пакетная ламинация в зависимости от размера пленки.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping

from calculators.base import BaseCalculator, ProductionMode
from common.layout import layout_on_roll
from common.markups import (
    BASE_TIME_READY,
    MARGIN_MATERIAL,
    MARGIN_MIN,
    MARGIN_OPERATION,
    get_margin,
)
from equipment import laminator as laminator_catalog
from materials import get_material

LAMINATOR_CODE = "FGKFM360"
WEIGHT_LAMINAT = 0.0011  # кг / (мкм·м²) пленки


class LaminationCalculator(BaseCalculator):
    """Ламинация: рулонная или пакетная пленка по размеру изделия."""

    slug = "lamination"
    name = "Ламинация"
    description = "Расчёт стоимости ламинации (рулонная или пакетная пленка)."

    def get_options(self) -> Dict[str, Any]:
        materials = []
        try:
            from materials import ALL_MATERIALS
            lam = ALL_MATERIALS.get("laminat")
            if lam:
                materials = lam.list_for_frontend()
        except Exception:
            pass
        return {
            "materials": materials[:50],
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
                    "quantity": {"type": "integer", "minimum": 1},
                    "width": {"type": "number", "minimum": 1},
                    "height": {"type": "number", "minimum": 1},
                    "material_id": {"type": "string"},
                    "double_side": {"type": "boolean"},
                    "mode": {"type": "integer", "enum": [0, 1, 2]},
                },
                "required": ["quantity", "width", "height", "material_id"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        quantity = int(params.get("quantity", 1))
        w = float(params.get("width", 0))
        h = float(params.get("height", 0))
        size = [w, h]
        material_id = str(params.get("material_id", "") or "").strip()
        double_side = bool(params.get("double_side", True))
        mode = ProductionMode(int(params.get("mode", 1)))
        laminator_code = str(params.get("laminator_code", "") or LAMINATOR_CODE).strip() or LAMINATOR_CODE

        try:
            laminator = laminator_catalog.get(laminator_code)
        except KeyError:
            return self._empty_result(mode)

        try:
            laminat = get_material("laminat", material_id)
        except Exception:
            return self._empty_result(mode)

        laminat_sizes = laminat.sizes or []
        if not laminat_sizes:
            return self._empty_result(mode)
        size_laminat = laminat_sizes[0]
        if len(size_laminat) < 2:
            return self._empty_result(mode)
        laminat_w, laminat_h = size_laminat[0], size_laminat[1]
        density_um = float(laminat.density or 0 or 32)
        cost_per_mp = float(laminat.cost or 0)

        defects = laminator.get_defect_rate(float(quantity))
        if mode.value >= 2:
            defects += defects * (mode.value - 1)

        meter_per_hour = laminator.get_meter_per_hour(density_um)
        if meter_per_hour <= 0:
            meter_per_hour = 50.0

        time_prepare = (laminator.time_prepare or 0.1) * mode.value
        deprec_hour = laminator.depreciation_per_hour
        cost_operator_hour = laminator.operator_cost_per_hour

        if laminat_h == 0:
            num = quantity if double_side else math.ceil(quantity / 2)
            layout_roll = layout_on_roll(1, size, [laminat_w, 0], 20)
            length_one_m = (layout_roll.get("length", 0) + 20) / 1000.0
            length_m = length_one_m * num * (1 + defects)
            time_lamination = length_m / meter_per_hour + time_prepare
            time_cut = 2 * num * (10 / 3600.0)
            time_operator = time_lamination + time_cut
            cost_material = cost_per_mp * 2 * length_m
            cost_lamination = deprec_hour * time_lamination
            cost_operator = time_operator * cost_operator_hour
            cost = cost_material + cost_lamination + cost_operator
            margin_extra = get_margin("marginLamination")
            price = (
                cost_material * (1 + MARGIN_MATERIAL + margin_extra)
                + (cost_lamination + cost_operator) * (1 + MARGIN_OPERATION + margin_extra)
            )
            time_hours = round(time_lamination * 100) / 100.0
            weight_kg = (
                quantity * (2 if double_side else 1) * density_um * w * h * WEIGHT_LAMINAT / 1_000_000.0
            )
            materials_out = [
                {
                    "code": laminat.code,
                    "name": laminat.name,
                    "quantity": round(2 * length_m, 4),
                    "unit": "m",
                }
            ]
        else:
            num = quantity
            num_with_defects = math.ceil(num * (1 + defects))
            layout_lam = layout_on_roll(1, [laminat_w, laminat_h], laminator.max_size or [330, 0], 0)
            layout_length_m = (layout_lam.get("length", 0) or 1) / 1000.0
            if layout_length_m <= 0:
                layout_length_m = 0.33
            sheet_per_hour = max(1, math.ceil(meter_per_hour / layout_length_m))
            time_packing = num_with_defects * (20 / 3600.0)
            time_lamination = num_with_defects / sheet_per_hour + time_prepare + time_packing
            cost_material = cost_per_mp * num_with_defects
            cost_lamination = deprec_hour * time_lamination
            cost_operator = time_lamination * cost_operator_hour
            cost = cost_material + cost_lamination + cost_operator
            margin_extra = get_margin("marginLamination")
            price = (
                cost_material * (1 + MARGIN_MATERIAL + margin_extra)
                + (cost_lamination + cost_operator) * (1 + MARGIN_OPERATION + margin_extra)
            )
            time_hours = round(time_lamination * 100) / 100.0
            weight_kg = (
                num * density_um * laminat_w * laminat_h * WEIGHT_LAMINAT / 1_000_000.0
            )
            materials_out = [
                {
                    "code": laminat.code,
                    "name": laminat.name,
                    "quantity": num_with_defects,
                    "unit": "sheet",
                }
            ]

        price = max(price, cost * (1 + MARGIN_MIN))
        price = math.ceil(price)

        base_ready = laminator.base_time_ready or BASE_TIME_READY
        idx = max(0, min(len(base_ready) - 1, mode.value))
        time_ready = time_hours + float(base_ready[idx])

        return {
            "cost": float(cost),
            "price": float(price),
            "unit_price": float(price) / max(1, quantity),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": weight_kg,
            "materials": materials_out,
        }

    def _empty_result(self, mode: ProductionMode) -> Dict[str, Any]:
        base = BASE_TIME_READY
        idx = max(0, min(len(base) - 1, mode.value))
        return {
            "cost": 0.0,
            "price": 0.0,
            "unit_price": 0.0,
            "time_hours": 0.0,
            "time_ready": float(base[idx]),
            "weight_kg": 0.0,
            "materials": [],
        }
