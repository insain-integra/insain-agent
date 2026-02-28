"""
Калькулятор плоттерной резки.

Перенесено из js_legacy/calc/calcCutPlotter.js.
Параметры: количество, размер изделия, материал (sheet/roll), плоттер, опции (интервал, метки, облой).
Результат: себестоимость и цена резки; расход материала в materials.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Optional

from calculators.base import BaseCalculator, ProductionMode
from common.layout import layout_on_roll, layout_on_roll_with_orientation, layout_on_sheet
from common.markups import (
    BASE_TIME_READY,
    MARGIN_MIN,
    MARGIN_OPERATION,
    get_margin,
)
from equipment import plotter as plotter_catalog

PLOTTER_CODE = "GraphtecCE5000-60"
SHEET_CATEGORIES = ("sheet", "roll")
INTERVAL_DEFAULT = 4.0


def _find_material(material_code: str):
    """Найти материал в sheet или roll."""
    from materials import get_material
    for cat in SHEET_CATEGORIES:
        try:
            return get_material(cat, material_code)
        except Exception:
            continue
    return None


class CutPlotterCalculator(BaseCalculator):
    """Плоттерная резка: листовой или рулонный материал, резка по контуру."""

    slug = "cut_plotter"
    name = "Плоттерная резка"
    description = "Расчёт стоимости плоттерной резки (наклейки, плёнка, бумага)."

    def get_options(self) -> Dict[str, Any]:
        materials = []
        try:
            from materials import ALL_MATERIALS
            for cat in SHEET_CATEGORIES:
                c = ALL_MATERIALS.get(cat)
                if c:
                    materials.extend(c.list_for_frontend())
        except Exception:
            pass
        plotters = []
        try:
            from equipment import get_all_equipment_options
            opts = get_all_equipment_options().get("plotter", {})
            plotters = [{"code": k, "name": v} for k, v in opts.items()]
        except Exception:
            pass
        if not plotters:
            plotters = [{"code": PLOTTER_CODE, "name": "Плоттер"}]
        return {
            "materials": materials[:80],
            "plotters": plotters,
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
                    "width_mm": {"type": "number", "minimum": 1},
                    "height_mm": {"type": "number", "minimum": 1},
                    "material_code": {"type": "string"},
                    "plotter_code": {"type": "string"},
                    "interval": {"type": "number", "description": "Интервал между изделиями, мм"},
                    "is_find_mark": {"type": "boolean"},
                    "is_del_film": {"type": "boolean"},
                    "len_cut": {"type": "number", "description": "Длина реза одного элемента, м (0 = по размерам)"},
                    "density": {"type": "number"},
                    "difficulty": {"type": "number"},
                    "size_item": {"type": "number"},
                    "mode": {"type": "integer", "enum": [0, 1, 2]},
                },
                "required": ["quantity", "width_mm", "height_mm", "material_code"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        quantity = int(params.get("quantity", 1))
        w = float(params.get("width_mm", 0))
        h = float(params.get("height_mm", 0))
        size = [w, h]
        material_code = str(params.get("material_code", "") or "").strip()
        plotter_code = str(params.get("plotter_code", "") or PLOTTER_CODE).strip() or PLOTTER_CODE
        interval = float(params.get("interval", INTERVAL_DEFAULT) or INTERVAL_DEFAULT)
        is_find_mark = bool(params.get("is_find_mark", False))
        is_del_film = bool(params.get("is_del_film", True))
        len_cut_param = params.get("len_cut")
        len_cut = float(len_cut_param) if len_cut_param is not None else 0.0
        density = float(params.get("density", 0) or 0)
        difficulty = float(params.get("difficulty", 1) or 1)
        size_item = float(params.get("size_item", 0) or 0)
        mode = ProductionMode(int(params.get("mode", 1)))

        try:
            plotter = plotter_catalog.get(plotter_code)
        except KeyError:
            plotter = plotter_catalog.get(PLOTTER_CODE) if plotter_catalog._items else None
        if not plotter:
            return self._empty_result(size, quantity, mode)

        material = _find_material(material_code) if material_code else None
        margins = list(plotter.margins or [30, 10, 10, 10])
        if len(margins) < 4:
            margins = [30, 10, 10, 10]
        # TODO: marginsMark from plotter when is_find_mark
        defects = plotter.get_defect_rate(float(quantity))
        if mode.value >= 2:
            defects += defects * (mode.value - 1)
        num_with_defects = math.ceil(quantity * (1 + defects))

        thickness_um = 80.0
        if material:
            if getattr(material, "thickness", None) is not None and material.thickness:
                thickness_um = float(material.thickness)
                if thickness_um < 20:
                    thickness_um *= 1000
            elif getattr(material, "density", None) and material.density:
                thickness_um = material.density / 80.0 * 100.0

        process_per_hour = plotter.get_process_speed(thickness_um)
        if process_per_hour <= 0:
            process_per_hour = 120.0

        if len_cut <= 0:
            len_cut = (size[0] + size[1]) * 2.0 / 1000.0
            if density > 0 and size_item > 0:
                len_cut += 4.0 * size[0] * size[1] * density / size_item / 1000.0
            len_cut *= difficulty

        max_plotter = plotter.max_size or [603, 5000]
        is_roll = material and getattr(material, "is_roll", False)
        len_material_mm: Optional[float] = None

        if is_roll and material and material.sizes:
            # Рулон: как в JS — перебираем варианты раскроя, выбираем минимальный расход
            len_cut_with_defects = len_cut * num_with_defects
            min_size = min(size[0], size[1])
            max_size = max(size[0], size[1])
            roll_sizes = [s for s in material.sizes if s[1] == 0] or material.sizes
            len_material_mm = None
            num_sheet = None

            for roll_size in roll_sizes:
                roll_w = float(roll_size[0])
                # Полезная ширина рулона (JS: sizeMaterial[0] - margins[0] - margins[2])
                roll_eff = roll_w - margins[0] - margins[2]
                if roll_eff <= 0:
                    continue
                # Проверка: изделие помещается на плоттер (JS: layoutOnPlotter)
                layout_plotter_check = layout_on_roll(
                    num_with_defects, size, [max_plotter[0], 0.0], interval
                )
                if layout_plotter_check["length"] <= 0:
                    continue

                cur_len = 0.0
                cur_num_sheet = 0

                # Способ 1: поперёк рулона, короткой стороной по ширине (JS: if maxSize <= plotter.maxSize[0])
                if max_size <= max_plotter[0]:
                    length_way1 = layout_on_roll_with_orientation(
                        num_with_defects, size, roll_eff, interval, -1
                    )
                    if length_way1 > 0:
                        num_sheet_far = math.ceil(length_way1 / max_plotter[0])
                        l1 = length_way1 + num_sheet_far * (margins[1] + margins[3])
                        if cur_len == 0 or l1 < cur_len:
                            cur_len = l1
                            cur_num_sheet = num_sheet_far

                # Способ 2: поперёк рулона, длинной стороной по ширине
                length_way2 = layout_on_roll_with_orientation(
                    num_with_defects, size, roll_eff, interval, 1
                )
                if length_way2 > 0:
                    num_sheet_far = math.ceil(length_way2 / max_plotter[0])
                    l2 = length_way2 + num_sheet_far * (margins[1] + margins[3])
                    if cur_len == 0 or l2 < cur_len:
                        cur_len = l2
                        cur_num_sheet = num_sheet_far

                # Способ 3: вдоль рулона, короткой стороной вдоль
                w3 = math.floor(max_plotter[0] / min_size) * min_size + margins[1] + margins[3]
                num_sheet_wide3 = math.floor(roll_w / w3) if w3 > 0 else 0
                if num_sheet_wide3 > 0:
                    num_wide3 = num_sheet_wide3 * math.floor(max_plotter[0] / min_size)
                    w_rem = roll_w - w3 * num_sheet_wide3
                    if w_rem - margins[0] - margins[2] > min_size:
                        num_wide3 += math.floor((w_rem - margins[0] - margins[2]) / min_size)
                        num_sheet_wide3 += 1
                    l3_rows = math.ceil(num_with_defects / num_wide3) * max_size
                    num_sheet_far3 = math.ceil(l3_rows / max_plotter[1])
                    l3 = l3_rows + num_sheet_far3 * (margins[0] + margins[2])
                    if cur_len == 0 or l3 < cur_len:
                        cur_len = l3
                        cur_num_sheet = num_sheet_wide3 * num_sheet_far3

                # Способ 4: вдоль рулона, длинной стороной вдоль (JS: if maxSize < plotter.maxSize[0])
                if max_size < max_plotter[0]:
                    w4 = math.floor(max_plotter[0] / max_size) * max_size + margins[1] + margins[3]
                    num_sheet_wide4 = math.floor(roll_w / w4) if w4 > 0 else 0
                    if num_sheet_wide4 > 0:
                        num_wide4 = num_sheet_wide4 * math.floor(max_plotter[0] / max_size)
                        w_rem4 = roll_w - w4 * num_sheet_wide4
                        if w_rem4 - margins[0] - margins[2] > max_size:
                            num_wide4 += math.floor((w_rem4 - margins[0] - margins[2]) / max_size)
                            num_sheet_wide4 += 1
                        l4_rows = math.ceil(num_with_defects / num_wide4) * min_size
                        num_sheet_far4 = math.ceil(l4_rows / max_plotter[1])
                        l4 = l4_rows + num_sheet_far4 * (margins[0] + margins[2])
                        if cur_len == 0 or l4 < cur_len:
                            cur_len = l4
                            cur_num_sheet = num_sheet_wide4 * num_sheet_far4

                if cur_len > 0 and (len_material_mm is None or cur_len < len_material_mm):
                    len_material_mm = cur_len
                    num_sheet = cur_num_sheet

            if len_material_mm is None or len_material_mm <= 0:
                # Fallback: изделие не помещается ни одним способом — разбиваем на куски (JS: else)
                roll_eff = float(roll_sizes[0][0]) - margins[1] - margins[3]
                if roll_eff < max_plotter[0]:
                    num_bond_material = math.ceil(min_size / roll_eff)
                else:
                    num_bond_plotter = math.ceil(min_size / max_plotter[0])
                    num_bond_material = 1.0 / math.ceil(
                        roll_w / (min_size / num_bond_plotter + margins[1] + margins[3])
                    )
                num_sheet = math.ceil(
                    max_size * num_with_defects * (math.ceil(min_size / max_plotter[0]) if roll_eff >= max_plotter[0] else 1)
                    / min(max_plotter[1], max_size)
                )
                len_material_mm = (
                    max_size * num_with_defects * (math.ceil(min_size / max_plotter[0]) if roll_eff >= max_plotter[0] else 1)
                    + num_sheet * (margins[0] + margins[2])
                ) * (num_bond_material if roll_eff < max_plotter[0] else 1)

            if len_material_mm is None or len_material_mm <= 0:
                return self._empty_result(size, quantity, mode)
            if num_sheet is None:
                num_sheet = math.ceil(len_material_mm / max_plotter[0])
        else:
            layout_plotter = layout_on_sheet(size, max_plotter, margins, interval)
            if layout_plotter["num"] == 0:
                return self._empty_result(size, quantity, mode)
            num_sheet = math.ceil(num_with_defects / layout_plotter["num"])
            len_cut_with_defects = (
                len_cut * num_with_defects
                if num_sheet <= 1
                else len_cut * layout_plotter["num"] * num_sheet
            )

        # В JS: lenCut в метрах, timeCut = lenCutWithDefects/processPerHour (без /1000), costCut += lenCutWithDefects*costProcess
        time_prepare = (plotter.time_prepare or 0.05) * mode.value
        time_cut = len_cut_with_defects / process_per_hour + time_prepare
        time_load_sheet = getattr(plotter, "time_load_sheet", 0.01) or 0.01
        time_find_mark = getattr(plotter, "time_find_mark", 0.015) or 0.015
        time_cut += num_sheet * time_load_sheet
        if is_find_mark:
            time_cut += num_sheet * time_find_mark

        time_hours = round(time_cut * 100) / 100.0
        cost_depreciation = plotter.depreciation_per_hour * time_cut
        cost_process = len_cut_with_defects * (plotter.cost_process or 0.3)
        cost_operator = time_cut * plotter.operator_cost_per_hour
        cost = cost_depreciation + cost_process + cost_operator

        margin_extra = get_margin("marginPlotter")
        effective_margin = max(MARGIN_OPERATION + margin_extra, MARGIN_MIN)
        price = math.ceil(cost * (1 + effective_margin))

        base_ready = plotter.base_time_ready or BASE_TIME_READY
        idx = max(0, min(len(base_ready) - 1, mode.value))
        time_ready = time_hours + float(base_ready[idx])

        weight_kg = 0.0
        materials_out: List[Dict[str, Any]] = []
        if material and material_code:
            weight_kg = 0.0
            try:
                from common.helpers import calc_weight
                weight_kg = calc_weight(
                    quantity=quantity,
                    density=material.density or 0.0,
                    thickness=material.thickness or 0.0,
                    size=size,
                    density_unit=getattr(material, "density_unit", "гсм3") or "гсм3",
                )
            except Exception:
                pass
            if is_roll and len_material_mm is not None:
                # Рулон: расход в метрах, дробное значение
                materials_out = [
                    {
                        "code": material.code,
                        "name": material.name,
                        "quantity": round(len_material_mm / 1000.0, 2),
                        "unit": "m",
                    }
                ]
            else:
                materials_out = [
                    {
                        "code": material.code,
                        "name": material.name,
                        "quantity": num_sheet,
                        "unit": "sheet",
                    }
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

    def _empty_result(self, size: List[float], quantity: int, mode: ProductionMode) -> Dict[str, Any]:
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
