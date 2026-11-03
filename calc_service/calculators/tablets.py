"""
Калькулятор ТАБЛИЧЕК.

Мигрировано из js_legacy/calc/calcTablets.js.
Информационные таблички: резка (лазер / металл), УФ, сублимация, карманы, рамка.

Перенесено (ветки плакеток): ручная резка металла, сублимация, лазерная резка
с гравировкой, УФ-печать; карманы и рамка — упрощённо через common/.

Список «не перенесено»: ручная резка роликом, фрезер, экосольвентная печать и плёнка,
фоновая плёнка, древко, клеевой слой, EVA-пена, подвесы; полные карманы и рамка
как в JS (см. scripts/js_port_gaps_allowed.txt, префикс calcTablets).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, MutableMapping, Sequence

from calculators.base import BaseCalculator, ProductionMode, material_line
from calculators.heat_press import HeatPressCalculator
from calculators.laser import LaserCalculator
from calculators.uv_print import UVPrintCalculator
from common.layout import layout_on_sheet
from common.markups import (
    BASE_TIME_READY,
    MARGIN_MATERIAL,
    get_margin,
)
from common.process_tools import calc_cut_profile, calc_cut_saber, calc_pocket, calc_set_profile
from materials import hardsheet as hardsheet_catalog, pocket as pocket_catalog, profile as profile_catalog

DEFAULT_PROFILE = "AluFrame2Plus"
CUT_TOOL = "DWE713XPS"
DEFAULT_UV_PRINTER = "RimalSuvUV"


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


def _pick(mapping: Mapping[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return default


def _normalize_surface(surface: Any) -> str:
    text = str(surface or "plain").strip()
    if text in ("isPlain", "plain"):
        return "plain"
    if text in ("isRound", "round"):
        return "round"
    return text


def _normalize_cut_laser(raw: Any) -> Dict[str, float]:
    if not isinstance(raw, Mapping):
        return {"len_cut": 0.0, "size_item": 0.0, "density": 0.0, "difficulty": 1.0}
    return {
        "len_cut": float(_pick(raw, "len_cut", "lenCut", default=0) or 0),
        "size_item": float(_pick(raw, "size_item", "sizeItem", default=0) or 0),
        "density": float(_pick(raw, "density", default=0) or 0),
        "difficulty": float(_pick(raw, "difficulty", default=1) or 1),
    }


def _from_process(res: Any) -> Dict[str, Any]:
    return {
        "cost": float(res.cost),
        "price": float(res.price),
        "time_hours": float(res.time_hours),
        "time_ready": float(res.time_ready),
        "weight_kg": float(res.weight_kg),
        "materials": list(res.materials or []),
    }


class TabletsCalculator(BaseCalculator):
    """Таблички: резка, УФ, сублимация, карманы, рамка."""

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
                    "is_cut_manual_metal": {
                        "type": "string",
                        "description": "Id резака для ручной резки металла (например AccusheadPro12)",
                    },
                    "is_sublimation": {"type": "boolean", "default": False, "description": "Сублимация через heat_press"},
                    "is_cut_laser": {
                        "type": "object",
                        "description": "Параметры лазерной резки (size_item/sizeItem, len_cut/lenCut, density, difficulty)",
                    },
                    "is_grave": {"type": "integer", "description": "Индекс детализации гравировки"},
                    "is_grave_fill": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 2,
                        "maxItems": 2,
                        "description": "Область сплошной гравировки [w, h], мм",
                    },
                    "is_uv_print": {
                        "type": "object",
                        "description": "УФ-печать: printer_id/printerID, resolution, surface, color, size",
                    },
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
                {"name": "is_cut_manual_metal", "type": "string", "required": False, "title": "Резак металла"},
                {"name": "is_sublimation", "type": "boolean", "required": False, "default": False, "title": "Сублимация"},
                {"name": "is_cut_laser", "type": "object", "required": False, "title": "Лазерная резка"},
                {"name": "is_grave", "type": "integer", "required": False, "title": "Гравировка (разрешение)"},
                {"name": "is_grave_fill", "type": "array", "required": False, "title": "Область гравировки"},
                {"name": "is_uv_print", "type": "object", "required": False, "title": "УФ-печать"},
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
                "cut": ["is_cut_manual_metal", "is_cut_laser", "is_grave", "is_grave_fill"],
                "print": ["is_uv_print", "is_sublimation"],
                "options": ["pocket_id", "pocket_count", "is_frame", "frame_profile_id"],
                "mode": ["mode"],
            },
        }

    def _cut_manual_metal(
        self,
        n: int,
        size: Sequence[float],
        material_id: str,
        cutter_id: str,
        mode: int,
    ) -> Dict[str, Any]:
        margins = [0.0, 0.0, 0.0, 0.0]
        interval = 1.0
        size_sheet: List[float] = [210.0, 297.0]
        layout = layout_on_sheet(size, size_sheet, margins, interval)
        if layout["num"] == 0:
            size_sheet = [420.0, 297.0]
            layout = layout_on_sheet(size, size_sheet, margins, interval)
            if layout["num"] == 0:
                raise ValueError("Изделие не помещается на материал")
        num_sheet = n / layout["num"]
        cut = calc_cut_saber(
            num_sheet=num_sheet,
            size=size,
            size_sheet=size_sheet,
            material_id=material_id,
            cutter_id=cutter_id,
            margins=margins,
            interval=interval,
            mode=mode,
        )
        material = hardsheet_catalog.get(material_id)
        sheet = material.sizes[0] if material.sizes else [3050.0, 2050.0]
        area_material = n * (size[0] + interval) * (size[1] + interval)
        num_material_sheet = area_material / (sheet[0] * sheet[1])
        cost = float(cut.cost) + num_material_sheet * float(material.cost or 0)
        price = float(cut.price) + num_material_sheet * float(material.cost or 0) * (1 + MARGIN_MATERIAL)
        weight = float(cut.weight_kg) + (
            area_material * float(material.thickness or 0) * float(material.density or 0) / 1_000_000.0
        )
        return {
            "cost": cost,
            "price": price,
            "time_hours": float(cut.time_hours),
            "time_ready": float(cut.time_ready),
            "weight_kg": weight,
            "materials": [
                material_line(
                    code=material_id,
                    name=material.description,
                    title=material.title,
                    quantity=num_material_sheet,
                    unit="лист",
                    size_mm=[float(sheet[0]), float(sheet[1])],
                )
            ],
        }

    def _sublimation(
        self,
        n: int,
        size: Sequence[float],
        mode: int,
    ) -> Dict[str, Any]:
        size_print: List[float] = [210.0, 297.0]
        margins = [5.0, 5.0, 5.0, 5.0]
        interval = 1.0
        layout = layout_on_sheet(size, size_print, margins, interval)
        if layout["num"] == 0:
            size_print = [420.0, 297.0]
            layout = layout_on_sheet(size, size_print, margins, interval)
            if layout["num"] == 0:
                raise ValueError("Изделие не помещается на материал")
        num_sheet = math.ceil(n / layout["num"])
        return HeatPressCalculator().calculate({
            "quantity": num_sheet,
            "width": size_print[0],
            "height": size_print[1],
            "transfer_type": "sublimation",
            "item_type": "metal",
            "mode": mode,
        })

    def _uv_print(
        self,
        n: int,
        size: Sequence[float],
        raw: Any,
        mode: int,
    ) -> Dict[str, Any]:
        opts: Mapping[str, Any] = raw if isinstance(raw, Mapping) else {}
        size_print_raw = _pick(opts, "size")
        if isinstance(size_print_raw, (list, tuple)) and len(size_print_raw) >= 2:
            size_print = [float(size_print_raw[0]), float(size_print_raw[1])]
        else:
            size_print = [float(size[0]), float(size[1])]
        printer = str(
            _pick(opts, "printer_id", "printerID", "printer_code", default=DEFAULT_UV_PRINTER)
            or DEFAULT_UV_PRINTER
        ).strip() or DEFAULT_UV_PRINTER
        return UVPrintCalculator().calculate({
            "quantity": n,
            "width": size_print[0],
            "height": size_print[1],
            "item_width": size_print[0],
            "item_height": size_print[1],
            "resolution": int(_pick(opts, "resolution", default=0) or 0),
            "color": str(_pick(opts, "color", default="4+0") or "4+0").strip(),
            "surface": _normalize_surface(_pick(opts, "surface", default="plain")),
            "printer_code": printer,
            "mode": mode,
        })

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        n = int(params.get("quantity", 1))
        width = float(params.get("width", 0))
        height = float(params.get("height", 0))
        size = [width, height]
        material_id = str(params.get("material_id", "")).strip()
        mode = ProductionMode(int(params.get("mode", 1)))

        is_cut_manual_metal = params.get("is_cut_manual_metal")
        is_sublimation = bool(params.get("is_sublimation", False))
        has_cut_laser = "is_cut_laser" in params and params.get("is_cut_laser") is not None
        is_grave = params.get("is_grave")
        is_grave_fill = params.get("is_grave_fill")
        has_uv = "is_uv_print" in params and params.get("is_uv_print") is not None

        pocket_id = params.get("pocket_id")
        pocket_count = int(params.get("pocket_count", 1) or 1)
        is_frame = bool(params.get("is_frame", False))
        frame_profile_id = str(params.get("frame_profile_id", "") or DEFAULT_PROFILE).strip() or DEFAULT_PROFILE

        if width <= 0 or height <= 0:
            raise ValueError("Ширина и высота должны быть положительными")
        if not material_id:
            raise ValueError("material_id обязателен")

        parts: List[Dict[str, Any]] = []

        # Ручная резка металла + материал (calcCutSaber + раскладка A4/A3)
        if is_cut_manual_metal:
            cutter_id = str(is_cut_manual_metal).strip()
            if cutter_id:
                parts.append(self._cut_manual_metal(n, size, material_id, cutter_id, mode.value))

        # Лазерная резка (+ гравировка)
        if has_cut_laser or is_grave is not None:
            laser_params: MutableMapping[str, Any] = {
                "quantity": n,
                "width": width,
                "height": height,
                "material_id": material_id,
                "mode": mode.value,
            }
            if has_cut_laser:
                laser_params["is_cut_laser"] = _normalize_cut_laser(params.get("is_cut_laser"))
            if is_grave is not None:
                laser_params["is_grave"] = int(is_grave)
            if is_grave_fill is not None:
                laser_params["is_grave_fill"] = is_grave_fill
            parts.append(LaserCalculator().calculate(laser_params))

        # Сублимация (calcHeatPress на раскладке A4/A3)
        if is_sublimation:
            parts.append(self._sublimation(n, size, mode.value))

        # УФ-печать поверх резки, не вместо
        if has_uv:
            parts.append(self._uv_print(n, size, params.get("is_uv_print"), mode.value))

        # Карманы (упрощённо; полный порт JS-карманов — не перенесён)
        if pocket_id:
            pocket_res = calc_pocket(n * pocket_count, str(pocket_id), mode.value)
            parts.append(_from_process(pocket_res))

        # Рамка из профиля (упрощённо; полный порт JS-рамки — не перенесён)
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

            frame_part = {
                "cost": cost_mat_frame + cut_res.cost + set_res.cost,
                "price": (
                    cost_mat_frame * (1 + MARGIN_MATERIAL)
                    + cut_res.price
                    + set_res.price
                ),
                "time_hours": cut_res.time_hours + set_res.time_hours,
                "time_ready": (
                    cut_res.time_hours
                    + set_res.time_hours
                    + float(BASE_TIME_READY[min(mode.value, len(BASE_TIME_READY) - 1)])
                ),
                "weight_kg": profile_weight * len_profile_mm / 1000 + set_res.weight_kg,
                "materials": [
                    {
                        "code": frame_profile_id,
                        "name": profile_spec.description,
                        "title": profile_spec.title,
                        "quantity": num_profile,
                        "unit": "шт",
                    },
                    *list(set_res.materials or []),
                ],
            }
            parts.append(frame_part)

        cost_total = sum(float(p["cost"]) for p in parts)
        price_parts = sum(float(p["price"]) for p in parts)
        time_total = sum(float(p["time_hours"]) for p in parts)
        weight_total = sum(float(p["weight_kg"]) for p in parts)
        time_ready_components = [float(p["time_ready"]) for p in parts]
        materials_out: List[Dict[str, Any]] = []
        for p in parts:
            materials_out.extend(p.get("materials") or [])

        margin_tablet = get_margin("marginTablets")
        price_total = price_parts * (1 + margin_tablet)
        time_hours = math.ceil(time_total * 100) / 100.0
        # Как в JS: result.time + Math.max(...component.timeReady)
        time_ready = time_hours + (max(time_ready_components) if time_ready_components else 0.0)
        weight_kg = math.ceil(weight_total * 100) / 100.0

        return {
            "cost": float(cost_total),
            "price": float(price_total),
            "unit_price": round(float(price_total) / max(1, n), 2),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": weight_kg,
            "materials": materials_out,
        }
