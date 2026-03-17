"""
Калькулятор ХОЛСТОВ.

Мигрировано из js_legacy/calc/calcCanvas.js.
Печать на холсте + опциональный подрамник (багет) + натяжка на раму.
Использует print_roll для печати, профиль для подрамника, SetCanvasFrame для натяжки.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping

from calculators.base import BaseCalculator, ProductionMode
from calculators.print_roll import PrintRollCalculator
from common.helpers import calc_weight
from common.markups import (
    BASE_TIME_READY,
    MARGIN_MATERIAL,
    MARGIN_OPERATION,
    get_margin,
)
from common.process_tools import calc_cut_profile, calc_set_canvas_frame
from materials import profile as profile_catalog, roll as roll_catalog

DEFAULT_PRINTER = "HPLatex335"
DEFAULT_MATERIAL = "CanvasDLCNM320"
DEFAULT_FRAME = "CanvasFrame4520"
CUT_TOOL = "DWE713XPS"


def _min_profiles(len_profile: float, segments: List[List[float]]) -> int:
    """Минимальное кол-во палок профиля для нарезки сегментов."""
    sort_segments = [list(s) for s in segments]
    sort_segments.sort(key=lambda x: x[0], reverse=True)
    count = 0
    count_profile = 1
    index = 0
    len_remain = len_profile
    count_segments = sum(int(s[1]) for s in sort_segments)

    while count < count_segments:
        if len_remain >= sort_segments[index][0] and sort_segments[index][1] > 0:
            len_remain -= sort_segments[index][0]
            sort_segments[index][1] -= 1
            count += 1
        else:
            index += 1
            if index >= len(sort_segments):
                index = 0
                len_remain = len_profile
                count_profile += 1
    return count_profile


class CanvasCalculator(BaseCalculator):
    """Холсты: широкоформатная печать на холсте + подрамник + натяжка."""

    slug = "canvas"
    name = "Холсты"
    description = "Расчёт стоимости печати на холсте с подрамником и натяжкой на раму."

    def get_options(self) -> Dict[str, Any]:
        materials = roll_catalog.list_for_frontend()
        profiles = profile_catalog.list_for_frontend()
        return {
            "materials": materials,
            "profiles": profiles,
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
                    "quantity": {"type": "integer", "minimum": 1, "description": "Количество изделий"},
                    "width": {"type": "number", "minimum": 1, "description": "Ширина изделия, мм"},
                    "height": {"type": "number", "minimum": 1, "description": "Высота изделия, мм"},
                    "material_id": {"type": "string", "description": "Код материала холста"},
                    "printer_code": {"type": "string"},
                    "is_frame": {"type": "boolean", "default": True, "description": "Подрамник (багет)"},
                    "frame_id": {"type": "string", "description": "Код профиля подрамника"},
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["quantity", "width", "height"],
            },
        }

    def get_param_schema(self) -> Dict[str, Any]:
        return {
            "slug": self.slug,
            "title": self.name,
            "params": [
                {"name": "quantity", "type": "integer", "required": True, "title": "Тираж", "validation": {"min": 1}},
                {"name": "width", "type": "number", "required": True, "title": "Ширина (мм)", "unit": "мм"},
                {"name": "height", "type": "number", "required": True, "title": "Высота (мм)", "unit": "мм"},
                {"name": "material_id", "type": "enum_cascading", "required": False, "title": "Материал холста", "default": DEFAULT_MATERIAL, "choices": {"source": "materials:roll"}},
                {"name": "printer_code", "type": "enum", "required": False, "title": "Принтер", "default": DEFAULT_PRINTER},
                {"name": "is_frame", "type": "boolean", "required": False, "default": True, "title": "Подрамник"},
                {"name": "frame_id", "type": "enum", "required": False, "title": "Профиль подрамника", "default": DEFAULT_FRAME, "choices": {"source": "materials:profile"}},
                {"name": "mode", "type": "enum", "required": False, "default": 1, "title": "Режим",
                 "choices": {"inline": [{"id": 0, "title": "Эконом"}, {"id": 1, "title": "Стандарт"}, {"id": 2, "title": "Экспресс"}]}},
            ],
            "param_groups": {
                "main": ["quantity", "width", "height"],
                "material": ["material_id"],
                "options": ["is_frame", "frame_id"],
                "mode": ["mode"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        n = int(params.get("quantity", 1))
        width = float(params.get("width", 0))
        height = float(params.get("height", 0))
        size = [width, height]
        material_id = str(params.get("material_id", "") or DEFAULT_MATERIAL).strip() or DEFAULT_MATERIAL
        printer_code = str(params.get("printer_code", "") or DEFAULT_PRINTER).strip() or DEFAULT_PRINTER
        is_frame = bool(params.get("is_frame", True))
        frame_id = str(params.get("frame_id", "") or DEFAULT_FRAME).strip() or DEFAULT_FRAME
        mode = ProductionMode(int(params.get("mode", 1)))

        if width <= 0 or height <= 0:
            raise ValueError("Ширина и высота должны быть положительными")

        # 1. Печать на холсте (print_roll)
        print_calc = PrintRollCalculator()
        print_params = {
            "quantity": n,
            "width": width,
            "height": height,
            "material_id": material_id,
            "printer_code": printer_code,
            "mode": mode.value,
        }
        cost_print = print_calc.calculate(print_params)

        cost_total = float(cost_print.get("cost", 0))
        price_total = float(cost_print.get("price", 0))
        time_total = float(cost_print.get("time_hours", 0))
        time_ready_max = float(cost_print.get("time_ready", 0))
        weight_total = float(cost_print.get("weight_kg", 0))
        materials_out: List[Dict[str, Any]] = list(cost_print.get("materials", []))

        # 2. Подрамник (багет) + натяжка
        cost_frame = 0.0
        price_frame = 0.0
        time_frame = 0.0
        time_ready_frame = 0.0
        weight_frame = 0.0

        if is_frame:
            try:
                profile_spec = profile_catalog.get(frame_id)
            except KeyError:
                profile_spec = profile_catalog.get(DEFAULT_FRAME)

            profile_len = float(getattr(profile_spec, "len", 3050) or 3050)
            profile_cost_unit = float(profile_spec.cost or 0)
            profile_weight = float(getattr(profile_spec, "weight", 0.5) or 0.5)

            segments = [[size[0], 2], [size[1], 2]]
            n_segments = [[s[0], s[1] * n] for s in segments]
            num_profile = _min_profiles(profile_len, n_segments)
            len_profile_mm = sum(s[0] * s[1] for s in n_segments)
            num_corners = n * 4

            cost_material_frame = num_profile * profile_cost_unit
            cut_result = calc_cut_profile(n, segments, CUT_TOOL, mode.value)
            time_assembly = (num_corners / 2 * 480) / 3600
            from common.markups import COST_OPERATOR
            cost_assembly = time_assembly * COST_OPERATOR
            price_assembly = cost_assembly * (1 + MARGIN_OPERATION)

            cost_frame = cost_material_frame + cut_result.cost + cost_assembly
            price_frame = (
                cost_material_frame * (1 + MARGIN_MATERIAL)
                + cut_result.price
                + price_assembly
            )
            time_frame = cut_result.time_hours + time_assembly
            weight_frame = profile_weight * len_profile_mm / 1000

            set_canvas = calc_set_canvas_frame(n, size, mode.value)
            cost_frame += set_canvas.cost
            price_frame += set_canvas.price
            time_frame += set_canvas.time_hours

            cost_total += cost_frame
            price_total += price_frame
            time_total += time_frame
            weight_total += weight_frame
            time_ready_frame = time_frame + float(BASE_TIME_READY[min(mode.value, len(BASE_TIME_READY) - 1)])
            time_ready_max = max(time_ready_max, time_ready_frame)

            materials_out.append({
                "code": frame_id,
                "name": profile_spec.description,
                "title": profile_spec.title,
                "quantity": num_profile,
                "unit": "шт",
            })

        margin_canvas = get_margin("marginCanvas")
        price_total = price_total * (1 + margin_canvas)
        time_hours = math.ceil(time_total * 100) / 100.0
        time_ready = max(time_ready_max, time_hours + float(BASE_TIME_READY[min(mode.value, len(BASE_TIME_READY) - 1)]))

        return {
            "cost": float(math.ceil(cost_total)),
            "price": float(math.ceil(price_total)),
            "unit_price": round(float(price_total) / max(1, n), 2),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": round(weight_total, 2),
            "materials": materials_out,
        }
