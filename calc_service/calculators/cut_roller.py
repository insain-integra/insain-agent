"""
Калькулятор рулонной резки на роликовом резаке.

Перенесено из js_legacy/calc/calcCutRoller.js.
Параметры: количество, размер изделия, материал, резак, material_mode.

Логика по умолчанию (как в JS):
  - По умолчанию материал в цену не включаем (material_mode=noMaterial).
  - isMaterial — в себестоимость и цену входит материал, в ответе список materials.
  - noMaterial — только резка, стоимость материала не считаем.
  - isMaterialCustomer — только резка, стоимость резки увеличиваем на 25% (наценка).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Optional, Sequence

from calculators.base import BaseCalculator, ProductionMode
from common.helpers import calc_weight
from common.layout import layout_on_roll, layout_on_sheet
from common.markups import (
    BASE_TIME_READY,
    MARGIN_MATERIAL,
    MARGIN_MIN,
    MARGIN_OPERATION,
    get_margin,
)
from equipment import cutter as cutter_catalog
from materials import get_material

CUTTER_CODE = "KWTrio3026"
MATERIAL_CATEGORIES = ("sheet", "roll", "hardsheet")


def _find_material(material_code: str):
    """Найти материал в sheet, roll или hardsheet."""
    for cat in MATERIAL_CATEGORIES:
        try:
            return get_material(cat, material_code)
        except Exception:
            continue
    return None


class CutRollerCalculator(BaseCalculator):
    """Рулонная/листовая резка на роликовом резаке."""

    slug = "cut_roller"
    name = "Рулонная резка"
    description = "Расчёт стоимости раскроя на роликовом резаке (листы или рулон)."

    def get_options(self) -> Dict[str, Any]:
        materials = []
        try:
            from materials import ALL_MATERIALS
            for cat in MATERIAL_CATEGORIES:
                c = ALL_MATERIALS.get(cat)
                if c:
                    materials.extend(c.list_for_frontend())
        except Exception:
            pass
        cutters = []
        try:
            from equipment import get_all_equipment_options
            cut_opts = get_all_equipment_options().get("cutter", {})
            cutters = [{"code": c, "name": cut_opts.get(c, c)} for c in cut_opts]
        except Exception:
            pass
        if not cutters:
            cutters = [{"code": CUTTER_CODE, "name": "Резак"}]
        return {
            "materials": materials[:80],
            "cutters": cutters,
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
                    "quantity": {"type": "integer", "minimum": 1, "description": "Количество листов/изделий"},
                    "width_mm": {"type": "number", "minimum": 1},
                    "height_mm": {"type": "number", "minimum": 1},
                    "material_code": {"type": "string"},
                    "material_category": {"type": "string", "enum": list(MATERIAL_CATEGORIES)},
                    "cutter_code": {"type": "string"},
                    "material_mode": {"type": "string", "enum": ["isMaterial", "isMaterialCustomer", "noMaterial"]},
                    "mode": {"type": "integer", "enum": [0, 1, 2]},
                },
                "required": ["quantity", "width_mm", "height_mm", "material_code"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        quantity = int(params.get("quantity", 1))
        size = [float(params.get("width_mm", 0)), float(params.get("height_mm", 0))]
        material_code = str(params.get("material_code", "") or "").strip()
        material_category = str(params.get("material_category", "sheet") or "sheet")
        cutter_code = str(params.get("cutter_code", "") or CUTTER_CODE).strip() or CUTTER_CODE
        # По умолчанию материал в цену не включаем (как в JS: isMaterial = 'noMaterial').
        material_mode = str(params.get("material_mode", "noMaterial") or "noMaterial")
        mode = ProductionMode(int(params.get("mode", ProductionMode.STANDARD)))

        if size[0] <= 0 or size[1] <= 0:
            raise ValueError("width_mm и height_mm должны быть положительными")
        if not material_code:
            raise ValueError("material_code обязателен")

        material = _find_material(material_code)
        if material is None:
            raise ValueError("Параметры материала не найдены")

        try:
            cutter = cutter_catalog.get(cutter_code)
        except Exception:
            cutter = cutter_catalog.get(CUTTER_CODE)

        sizes_material = material.sizes or []
        if not sizes_material:
            raise ValueError("У материала не заданы размеры")
        if isinstance(sizes_material[0], (int, float)):
            sizes_material = [sizes_material]

        interval = 0.0
        min_cost = None
        best_size = None
        best_num_sheet = 0.0
        best_len = 0.0
        best_num_cut = 0.0

        thickness = getattr(material, "thickness", None) or 0.0

        for sz in sizes_material:
            size_w, size_h = float(sz[0]), float(sz[1])
            cutter_max_w = (cutter.max_size or [1520, 0])[0] if cutter.max_size else 1520

            if min(size_w, size_h) > cutter_max_w:
                continue

            cost_mat = 0.0
            num_cut = 0
            num_sheet = 0.0
            len_mat = 0.0

            if size_h == 0:
                layout = layout_on_roll(quantity, size, [size_w, size_h], interval)
                if layout["num"] == 0:
                    continue
                len_mat = layout["length"]
                min_side = min(size[0], size[1])
                step = min_side + interval if interval else min_side
                num_wide = int((size_w + interval) // step) if step > 0 else 1
                num_far = math.ceil(quantity / num_wide) if num_wide > 0 else quantity
                num_cut = num_far + 1 + num_far * (num_wide + 1) - (num_wide * num_far - quantity)
                base_cost = material.get_cost(len_mat / 1000.0)
                if getattr(material, "length_min", None) and material.length_min > 0:
                    cost_mat = base_cost * math.ceil(len_mat / material.length_min) * material.length_min / 1e6 * size_w
                else:
                    cost_mat = base_cost * len_mat * size_w / 1e6
            else:
                layout = layout_on_sheet(size, [size_w, size_h], [0, 0, 0, 0], interval)
                if layout["num"] == 0:
                    continue
                num_cut_1 = (layout.get("cols", 1) or 1) + (layout.get("cols", 1) or 1) * (layout.get("rows", 1) or 1)
                num_cut_2 = (layout.get("rows", 1) or 1) + (layout.get("rows", 1) or 1) * (layout.get("cols", 1) or 1)
                if max(size_w, size_h) > cutter_max_w:
                    num_cut = num_cut_2
                else:
                    num_cut = min(num_cut_1, num_cut_2)
                num_cut = math.ceil(num_cut * quantity / layout["num"])
                layout_min = layout_on_sheet(material.min_size or [size[0], size[1]], [size_w, size_h]) if getattr(material, "min_size", None) else layout
                layout_min_num = max(1, (layout_min.get("num") or 1))
                num_sheet = math.ceil(quantity / layout["num"] * layout_min_num) / layout_min_num
                cost_mat = material.get_cost(num_sheet) * num_sheet * size_w * size_h / 1e6

            if thickness > 0:
                num_cut = num_cut * 2 * math.ceil(size[0] / 1000) * math.ceil(size[1] / 1000)
            else:
                num_cut = num_cut * math.ceil(size[0] / 1500) * math.ceil(size[1] / 1500)

            # При материале заказчика — наценка на резку 25% (как в JS).
            if material_mode == "isMaterialCustomer":
                num_cut = int(num_cut * 1.25)

            if material_mode != "isMaterial":
                cost_mat = 0.0

            if min_cost is None or cost_mat + 1 < min_cost:
                min_cost = cost_mat
                best_size = [size_w, size_h]
                best_num_sheet = num_sheet
                best_len = len_mat
                best_num_cut = num_cut

        if min_cost is None:
            raise ValueError("Изделие не помещается на материал")

        cost_material = min_cost
        num_cut = best_num_cut
        time_prepare = (cutter.time_prepare or 0) * mode.value
        cuts_per_hour = cutter.cuts_per_hour or 120.0
        time_cut = num_cut / cuts_per_hour + time_prepare
        cost_dep = cutter.depreciation_per_hour * time_cut
        cost_process = num_cut * (cutter.cost_process or 0.04)
        cost_operator = time_cut * cutter.operator_cost_per_hour
        cost = math.ceil(cost_material + cost_dep + cost_process + cost_operator)

        margin_extra = get_margin("marginCutRoller")
        effective_margin = max(MARGIN_OPERATION + margin_extra, MARGIN_MIN)
        price = math.ceil(
            cost_material * (1 + MARGIN_MATERIAL)
            + (cost_dep + cost_process + cost_operator) * (1 + effective_margin)
        )

        time_hours = math.ceil(time_cut * 100) / 100.0
        base_ready = cutter.base_time_ready if cutter.base_time_ready else BASE_TIME_READY
        idx = max(0, min(len(base_ready) - 1, int(mode.value)))
        time_ready = time_hours + float(base_ready[idx])

        weight_kg = calc_weight(
            quantity=quantity,
            density=material.density or 0.0,
            thickness=material.thickness or 0.0,
            size=size,
            density_unit=getattr(material, "density_unit", "гсм3"),
        )

        materials_out: List[Dict[str, Any]] = []
        if material_mode == "isMaterial" and best_size is not None:
            qty = best_len / 1000.0 if best_size[1] == 0 else best_num_sheet
            unit = "mm" if best_size[1] == 0 else "sheet"
            materials_out.append({
                "code": material_code,
                "name": material.name,
                "size_mm": best_size,
                "quantity": qty,
                "unit": unit,
            })

        return {
            "cost": float(cost),
            "price": float(price),
            "unit_price": float(price) / max(1, quantity),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": float(weight_kg),
            "materials": materials_out,
        }
