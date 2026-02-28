"""
Калькулятор фрезеровки.

Перенесено из js_legacy/calc/calcMilling.js.
Параметры: количество, размер изделия, материал (hardsheet), опции (резка, материал наш/заказчика).
Результат: себестоимость и цена с учётом материала, резки, доставки; мин. сумма 500 руб.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Mapping

import json5

from calculators.base import BaseCalculator, ProductionMode
from common.helpers import calc_weight, find_in_table
from common.layout import layout_on_sheet
from common.markups import (
    BASE_TIME_READY,
    MARGIN_MATERIAL,
    MARGIN_MIN,
    MARGIN_OPERATION,
    get_margin,
)
from equipment import milling as milling_catalog
from materials import get_material

MILLING_CODE = "MillingMachine"
DATA_EQUIPMENT = Path(__file__).resolve().parent.parent / "data" / "equipment"
MIN_COST = 500.0
INTERVAL_DEFAULT = 8.0


def _load_milling_raw() -> Dict[str, Any]:
    """Загрузить сырые данные milling.json для costCut, discountCostCut, costShipment."""
    path = DATA_EQUIPMENT / "milling.json"
    if not path.is_file():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json5.load(f)
        return data.get(MILLING_CODE, {}) or {}
    except Exception:
        return {}


def _cost_cut_per_meter(material_id: str, thickness_mm: float, raw: Dict[str, Any]) -> float:
    """Стоимость фрезеровки руб/м.п. по группе материала и толщине."""
    cost_cut = raw.get("costCut") or {}
    if not isinstance(cost_cut, dict):
        return 0.0
    for key, table in cost_cut.items():
        if material_id.startswith(key) and isinstance(table, (list, tuple)) and table:
            tiers = [(float(x[0]), float(x[1])) for x in table if len(x) >= 2]
            if tiers:
                return find_in_table(sorted(tiers, key=lambda p: p[0]), thickness_mm)
    return 0.0


def _discount_for_length(length_m: float, raw: Dict[str, Any]) -> float:
    """Скидка на резку от объёма (длина в м). Как в JS: findIndex(item[0] > len)-1 → значение для наибольшего порога <= length_m."""
    discount_table = raw.get("discountCostCut") or []
    if not isinstance(discount_table, (list, tuple)):
        return 0.0
    tiers = [(float(x[0]), float(x[1])) for x in discount_table if len(x) >= 2]
    if not tiers:
        return 0.0
    sorted_tiers = sorted(tiers, key=lambda p: p[0])
    discount = 0.0
    for threshold, val in sorted_tiers:
        if threshold <= length_m:
            discount = val
    return discount


def _cost_shipment(size: List[float], raw: Dict[str, Any]) -> float:
    """Стоимость доставки по габаритам: первый подходящий размер из costShipment."""
    shipment = raw.get("costShipment") or []
    if not isinstance(shipment, (list, tuple)):
        return 0.0
    for item in shipment:
        if not isinstance(item, (list, tuple)) or len(item) < 3:
            continue
        size_transport = [float(item[0]), float(item[1])]
        cost = float(item[2])
        layout = layout_on_sheet(size, size_transport)
        if layout.get("num", 0) > 0:
            return cost
    return 0.0


class MillingCalculator(BaseCalculator):
    """Фрезеровка: листовой жёсткий материал, резка по контуру."""

    slug = "milling"
    name = "Фрезеровка"
    description = "Расчёт стоимости фрезеровки (ПВХ, акрил, фанера, МДФ и др.)."

    def get_options(self) -> Dict[str, Any]:
        materials = []
        try:
            from materials import ALL_MATERIALS
            h = ALL_MATERIALS.get("hardsheet")
            if h:
                materials = h.list_for_frontend()
        except Exception:
            pass
        return {
            "materials": materials[:80],
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
                    "material_mode": {"type": "string", "enum": ["isMaterial", "isMaterialCustomer", "noMaterial"]},
                    "len_cut": {"type": "number"},
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
        material_mode = str(params.get("material_mode", "isMaterial") or "isMaterial")
        len_cut = float(params.get("len_cut", 0) or 0)
        mode = ProductionMode(int(params.get("mode", 1)))

        try:
            milling = milling_catalog.get(MILLING_CODE)
        except KeyError:
            return self._empty_result(mode)

        raw = _load_milling_raw()
        margins = list(milling.margins or [10, 10, 10, 10])
        if len(margins) < 4:
            margins = [10, 10, 10, 10]
        interval = INTERVAL_DEFAULT
        defects = milling.get_defect_rate(float(quantity))
        if mode.value >= 2:
            defects += defects * (mode.value - 1)

        cost_material = 0.0
        cost_cut = 0.0
        num_sheet = 0
        material = None
        time_cut = 0.0

        if material_id:
            try:
                material = get_material("hardsheet", material_id)
            except Exception:
                material = None
            if material:
                thickness_mm = float(material.thickness or 0 or 3)
                cost_cut_per_m = _cost_cut_per_meter(material_id, thickness_mm, raw)
                if cost_cut_per_m > 0 and len_cut > 0:
                    # В JS lenCut в мм: len = ceil(n * lenCut / 1000). Если len_cut < 100 — считаем в метрах (периметр 3 м → len_cut=3).
                    if 0 < len_cut <= 100:
                        length_m = math.ceil(quantity * len_cut)
                    else:
                        length_m = math.ceil(quantity * len_cut / 1000.0)
                    discount = _discount_for_length(length_m, raw)
                    cost_cut = length_m * cost_cut_per_m * (1 - discount)

                max_size = milling.max_size or [4000, 2000]
                layout_milling = layout_on_sheet(size, max_size, margins, interval)
                if layout_milling.get("num", 0) == 0:
                    return self._empty_result(mode)

                sizes = material.sizes or []
                if not sizes:
                    sizes = [[2100, 1400]]
                best_cost = None
                best_sheets = 0
                best_size_mat = None
                for sz in sizes:
                    if len(sz) < 2:
                        continue
                    sheet_w, sheet_h = sz[0], sz[1]
                    layout_sheet = layout_on_sheet(size, [sheet_w, sheet_h], margins, interval)
                    if layout_sheet.get("num", 0) == 0:
                        continue
                    n_sheet = quantity // layout_sheet["num"]
                    frac = quantity / layout_sheet["num"] - n_sheet
                    if frac > 0:
                        n_sheet += 1
                    cost_per_sheet = material.get_cost(n_sheet)
                    cost_mat = cost_per_sheet * n_sheet * (sheet_w * sheet_h) / 1_000_000.0
                    if best_cost is None or cost_mat < best_cost:
                        best_cost = cost_mat
                        best_sheets = n_sheet
                        best_size_mat = [sheet_w, sheet_h]

                if best_cost is not None and material_mode == "isMaterial":
                    cost_material = best_cost
                    num_sheet = best_sheets
                elif material_mode == "isMaterialCustomer":
                    cost_cut *= 1.25

        # В JS: timePrepare * modeProduction (0, 1, 2)
        time_prepare = (milling.time_prepare or 0.05) * mode.value
        time_hours = round((time_cut + time_prepare) * 100) / 100.0
        cost_operator = time_prepare * milling.operator_cost_per_hour
        cost_ship = _cost_shipment(size, raw)
        if mode.value == 0:
            cost_ship *= 0.5
        else:
            cost_ship *= max(1, mode.value)

        equipment_margin = float(raw.get("margin", 0) or 0)
        cost_total = (cost_cut + cost_material + cost_operator + cost_ship) * (1 + equipment_margin)
        # В JS: Math.round(n*(1+defects)) == n → учёт брака в цене. Python round(10.5)=10, JS Math.round(10.5)=11 → совпадаем через round half up.
        rounded_with_defects = int(quantity * (1 + defects) + 0.5)
        if rounded_with_defects == quantity and defects > 0:
            cost_total *= 1 + defects
        if cost_total < MIN_COST:
            cost_total = (MIN_COST + cost_ship) * (1 + equipment_margin)
            margin_extra = get_margin("marginMilling")
            price = math.ceil((MIN_COST + cost_ship) * (1 + MARGIN_OPERATION + margin_extra))
        else:
            margin_extra = get_margin("marginMilling")
            price = (
                cost_material * (1 + defects + MARGIN_MATERIAL)
                + (cost_cut + cost_ship + cost_operator) * (1 + defects + MARGIN_OPERATION + margin_extra)
            )
            price = max(price, cost_total * (1 + MARGIN_MIN))
            price = math.ceil(price)

        base_ready = milling.base_time_ready or BASE_TIME_READY
        idx = max(0, min(len(base_ready) - 1, mode.value))
        time_ready = time_hours + float(base_ready[idx])

        weight_kg = 0.0
        materials_out: List[Dict[str, Any]] = []
        if material and material_id and material_mode == "isMaterial":
            try:
                weight_kg = calc_weight(
                    quantity=quantity,
                    density=material.density or 0.0,
                    thickness=material.thickness or 0.0,
                    size=size,
                    density_unit=getattr(material, "density_unit", "гсм3") or "гсм3",
                )
            except Exception:
                pass
            materials_out = [
                {"code": material.code, "name": material.name, "quantity": num_sheet, "unit": "sheet"}
            ]

        return {
            "cost": float(cost_total),
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
