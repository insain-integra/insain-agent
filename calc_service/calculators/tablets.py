"""
Калькулятор ТАБЛИЧЕК.

Мигрировано из js_legacy/calc/calcTablets.js (упрощённая версия).
Информационные таблички: база (hardsheet) + печать (UV/лазер) + карманы + рамка из профиля.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping

from calculators.base import BaseCalculator, ProductionMode
from calculators.laser import LaserCalculator
from calculators.uv_print import UVPrintCalculator
from common.helpers import calc_weight
from common.layout import layout_on_sheet
from common.markups import (
    BASE_TIME_READY,
    MARGIN_MATERIAL,
    MARGIN_OPERATION,
    get_margin,
)
from common.process_tools import calc_cut_profile, calc_pocket, calc_set_profile
from materials import hardsheet as hardsheet_catalog, pocket as pocket_catalog, profile as profile_catalog

DEFAULT_PROFILE = "AluFrame2Plus"
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


class TabletsCalculator(BaseCalculator):
    """Таблички: база + печать + карманы + рамка."""

    slug = "tablets"
    name = "Таблички"
    description = "Расчёт стоимости информационных табличек: база, печать, карманы, рамка."

    def get_options(self) -> Dict[str, Any]:
        materials = hardsheet_catalog.list_for_frontend()
        pockets = pocket_catalog.list_for_frontend()
        profiles = profile_catalog.list_for_frontend()
        return {
            "materials": materials,
            "pockets": pockets,
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
                    "width": {"type": "number", "minimum": 1, "description": "Ширина, мм"},
                    "height": {"type": "number", "minimum": 1, "description": "Высота, мм"},
                    "material_id": {"type": "string", "description": "Код материала hardsheet"},
                    "print_method": {"type": "string", "enum": ["uv", "laser", "none"], "default": "uv", "description": "Способ нанесения"},
                    "pocket_id": {"type": "string", "description": "Код кармана (опционально)"},
                    "pocket_count": {"type": "integer", "default": 1, "description": "Кол-во карманов на изделие"},
                    "is_frame": {"type": "boolean", "default": False, "description": "Рамка из профиля"},
                    "frame_profile_id": {"type": "string", "description": "Код профиля рамки"},
                    "frame_segments": {"type": "array", "description": "Сегменты рамки [[длина, кол-во], ...]"},
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["quantity", "width", "height", "material_id"],
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
                {"name": "material_id", "type": "enum_cascading", "required": True, "title": "Материал", "choices": {"source": "materials:hardsheet"}},
                {"name": "print_method", "type": "enum", "required": False, "default": "uv", "title": "Печать",
                 "choices": {"inline": [{"id": "uv", "title": "УФ"}, {"id": "laser", "title": "Лазер"}, {"id": "none", "title": "Без печати"}]}},
                {"name": "pocket_id", "type": "enum", "required": False, "title": "Карман", "choices": {"source": "materials:pocket"}},
                {"name": "pocket_count", "type": "integer", "required": False, "default": 1, "title": "Карманов на изделие"},
                {"name": "is_frame", "type": "boolean", "required": False, "default": False, "title": "Рамка"},
                {"name": "frame_profile_id", "type": "enum", "required": False, "title": "Профиль рамки", "default": DEFAULT_PROFILE, "choices": {"source": "materials:profile"}},
                {"name": "mode", "type": "enum", "required": False, "default": 1, "title": "Режим",
                 "choices": {"inline": [{"id": 0, "title": "Эконом"}, {"id": 1, "title": "Стандарт"}, {"id": 2, "title": "Экспресс"}]}},
            ],
            "param_groups": {
                "main": ["quantity", "width", "height"],
                "material": ["material_id"],
                "print": ["print_method"],
                "options": ["pocket_id", "pocket_count", "is_frame", "frame_profile_id"],
                "mode": ["mode"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        n = int(params.get("quantity", 1))
        width = float(params.get("width", 0))
        height = float(params.get("height", 0))
        size = [width, height]
        material_id = str(params.get("material_id", "")).strip()
        print_method = str(params.get("print_method", "uv") or "uv").strip().lower()
        pocket_id = params.get("pocket_id")
        pocket_count = int(params.get("pocket_count", 1) or 1)
        is_frame = bool(params.get("is_frame", False))
        frame_profile_id = str(params.get("frame_profile_id", "") or DEFAULT_PROFILE).strip() or DEFAULT_PROFILE
        mode = ProductionMode(int(params.get("mode", 1)))

        if width <= 0 or height <= 0:
            raise ValueError("Ширина и высота должны быть положительными")
        if not material_id:
            raise ValueError("material_id обязателен")

        material = hardsheet_catalog.get(material_id)
        cost_total = 0.0
        price_total = 0.0
        time_total = 0.0
        time_ready_list: List[float] = []
        weight_total = 0.0
        materials_out: List[Dict[str, Any]] = []

        # 1. База: лазерная резка материала (или только материал при print_method=uv)
        if print_method == "laser":
            laser_calc = LaserCalculator()
            laser_params = {
                "quantity": n,
                "width": width,
                "height": height,
                "material_id": material_id,
                "mode": mode.value,
                "is_cut_laser": {"len_cut": (width + height) * 2, "size_item": width * height, "density": 0, "difficulty": 1},
            }
            laser_res = laser_calc.calculate(laser_params)
            cost_total += laser_res["cost"]
            price_total += laser_res["price"]
            time_total += laser_res["time_hours"]
            time_ready_list.append(laser_res["time_ready"])
            weight_total += laser_res["weight_kg"]
            materials_out.extend(laser_res.get("materials", []))
        else:
            # База: стоимость материала + резка (упрощённо — через layout)
            sizes = material.sizes or [[3050, 2050]]
            size_sheet = sizes[0] if sizes else [3050, 2050]
            if isinstance(size_sheet[0], (list, tuple)):
                size_sheet = size_sheet[0]
            layout = layout_on_sheet(size, size_sheet, [0, 0, 0, 0], 5)
            if layout["num"] == 0:
                raise ValueError("Изделие не помещается на материал")
            num_sheet = math.ceil(n / layout["num"])
            cost_mat = float(material.cost or 0) * num_sheet
            cost_total += cost_mat
            price_total += cost_mat * (1 + MARGIN_MATERIAL)
            area_m2 = n * width * height / 1_000_000
            weight_total += calc_weight(
                quantity=n,
                density=material.density or 0,
                thickness=material.thickness or 0,
                size=size,
                density_unit=getattr(material, "density_unit", "гм2") or "гм2",
            )
            materials_out.append({
                "code": material_id,
                "name": material.description,
                "title": material.title,
                "quantity": num_sheet,
                "unit": "лист",
            })

        # 2. Печать: UV или лазер (лазер уже в п.1)
        if print_method == "uv":
            uv_calc = UVPrintCalculator()
            uv_params = {
                "quantity": n,
                "width": width,
                "height": height,
                "item_width": width,
                "item_height": height,
                "mode": mode.value,
            }
            uv_res = uv_calc.calculate(uv_params)
            cost_total += uv_res["cost"]
            price_total += uv_res["price"]
            time_total += uv_res["time_hours"]
            time_ready_list.append(uv_res["time_ready"])

        # 3. Карманы
        if pocket_id:
            pocket_res = calc_pocket(n * pocket_count, pocket_id, mode.value)
            cost_total += pocket_res.cost
            price_total += pocket_res.price
            time_total += pocket_res.time_hours
            weight_total += pocket_res.weight_kg
            materials_out.extend(pocket_res.materials)

        # 4. Рамка из профиля
        if is_frame:
            profile_spec = profile_catalog.get(frame_profile_id)
            profile_len = float(getattr(profile_spec, "len", 3050) or 3050)
            profile_cost_unit = float(profile_spec.cost or 0)
            profile_weight = float(getattr(profile_spec, "weight", 0.5) or 0.5)

            frame_segments = params.get("frame_segments")
            if frame_segments and isinstance(frame_segments, (list, tuple)):
                segments = [[float(s[0]), int(s[1])] for s in frame_segments if len(s) >= 2]
            else:
                segments = [[size[0], 2], [size[1], 2]]

            n_segments = [[s[0], s[1] * n] for s in segments]
            num_profile = _min_profiles(profile_len, n_segments)
            len_profile_mm = sum(s[0] * s[1] for s in n_segments)

            cost_mat_frame = num_profile * profile_cost_unit
            cut_res = calc_cut_profile(n, segments, CUT_TOOL, mode.value)
            set_res = calc_set_profile(n, segments, frame_profile_id, mode.value)

            cost_frame = cost_mat_frame + cut_res.cost + set_res.cost
            price_frame = (
                cost_mat_frame * (1 + MARGIN_MATERIAL)
                + cut_res.price
                + set_res.price
            )
            time_frame = cut_res.time_hours + set_res.time_hours
            weight_frame = profile_weight * len_profile_mm / 1000 + set_res.weight_kg

            cost_total += cost_frame
            price_total += price_frame
            time_total += time_frame
            weight_total += weight_frame
            time_ready_list.append(time_frame + float(BASE_TIME_READY[min(mode.value, len(BASE_TIME_READY) - 1)]))

            materials_out.append({
                "code": frame_profile_id,
                "name": profile_spec.description,
                "title": profile_spec.title,
                "quantity": num_profile,
                "unit": "шт",
            })
            materials_out.extend(set_res.materials)

        margin_tablet = get_margin("marginTablets")
        price_total = price_total * (1 + margin_tablet)
        time_hours = math.ceil(time_total * 100) / 100.0
        time_ready = max(time_ready_list) if time_ready_list else time_hours + float(BASE_TIME_READY[min(mode.value, len(BASE_TIME_READY) - 1)])

        return {
            "cost": float(math.ceil(cost_total)),
            "price": float(math.ceil(price_total)),
            "unit_price": round(float(price_total) / max(1, n), 2),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": round(weight_total, 2),
            "materials": materials_out,
        }
