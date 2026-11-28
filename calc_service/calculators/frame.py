"""
Рамка стенда из профиля и подвесы.

Порт insaincalc.calcFrame из js_legacy/calc/calcTablets.js.
Подвес isHanger входит в эту функцию, как в JS: без рамки calcTablets его не вызывает.
Цена рамки без marginTablets — эту наценку добавляет calcTablets.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Sequence

from calculators.base import BaseCalculator, material_line, parse_mode
from common.markups import (
    BASE_TIME_READY,
    COST_OPERATOR,
    MARGIN_MATERIAL,
    MARGIN_OPERATION,
)
from common.process_tools import calc_cut_profile, calc_set_profile
from materials import profile as profile_catalog

CUT_TOOL = "DWE713XPS"
DEFAULT_PROFILE = "AluFrame2Plus"


def _min_profiles(len_profile: float, segments: List[List[float]]) -> int:
    """Минимальное число хлыстов. Раскладка как minProfiles в calcFrame."""
    sort_segments = [list(s) for s in segments]
    sort_segments.sort(key=lambda x: x[0], reverse=True)
    if any(float(s[0]) > len_profile for s in sort_segments):
        raise ValueError("Отрезок профиля длиннее хлыста")
    count = 0
    count_profile = 1
    index = 0
    len_remain = len_profile
    count_segments = sum(int(s[1]) for s in sort_segments)
    guard = 0
    while count < count_segments:
        guard += 1
        if guard > 100000:
            raise ValueError("Не удалось разложить профиль по хлыстам")
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


def _hanger_part(n: int, raw: Mapping[str, Any]) -> Dict[str, Any]:
    """Установка подвесов. numHanger в JS уже умножается на число рам."""
    hanger_id = str(raw.get("hanger_id") or raw.get("hangerID") or "").strip()
    if not hanger_id or hanger_id in ("no", "0", "No"):
        return {"cost": 0.0, "price": 0.0, "time_hours": 0.0, "weight_kg": 0.0, "materials": []}
    num_hanger = float(raw.get("num_hanger") if raw.get("num_hanger") is not None else raw.get("numHanger") or 0)
    num_hanger *= n
    spec = profile_catalog.get(hanger_id)
    weight_unit = float(spec.weight_per_unit or 0)
    time_hours = (num_hanger * 10) / 3600
    cost_operator = time_hours * COST_OPERATOR
    cost_material = num_hanger * float(spec.cost or 0)
    size = spec.sizes[0] if spec.sizes else [0, 0]
    return {
        "cost": cost_material + cost_operator,
        "price": (
            cost_material * (1 + MARGIN_MATERIAL)
            + cost_operator * (1 + MARGIN_OPERATION)
        ),
        "time_hours": time_hours,
        "weight_kg": weight_unit * num_hanger / 1000,
        "materials": [material_line(
            code=hanger_id,
            name=spec.description,
            title=spec.title,
            quantity=num_hanger,
            unit="шт",
            size_mm=[float(size[0]), float(size[1])],
        )],
    }


class FrameCalculator(BaseCalculator):
    """Нарезка и установка алюминиевого профиля, опционально подвесы."""

    slug = "frame"
    name = "Рамка"
    description = "Рамка стенда из профиля: хлысты, нарезка, сборка, подвесы."
    is_public = False

    def get_options(self) -> Dict[str, Any]:
        return {"profiles": profile_catalog.list_for_frontend()}

    def get_tool_schema(self) -> Dict[str, Any]:
        return {
            "name": "calc_frame",
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "quantity": {"type": "integer", "minimum": 1},
                    "profile_id": {"type": "string"},
                    "segments": {"type": "array"},
                    "is_hanger": {"type": "object"},
                    "mode": {"type": "integer"},
                },
                "required": ["quantity", "profile_id", "segments"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        n = int(params.get("quantity", 1) or 0)
        if n < 1:
            raise ValueError("Количество рамок должно быть положительным")
        profile_id = str(params.get("profile_id") or params.get("profileID") or "").strip()
        if not profile_id:
            raise ValueError("Не выбран профиль рамки")
        raw_segments = params.get("segments")
        if not isinstance(raw_segments, (list, tuple)) or not raw_segments:
            raise ValueError("Не заданы отрезки рамки")
        segments = [[float(s[0]), int(s[1])] for s in raw_segments if len(s) >= 2]
        if not segments:
            raise ValueError("Не заданы отрезки рамки")
        mode = int(parse_mode(params.get("mode", 1)))

        profile = profile_catalog.get(profile_id)
        len_stick = 3050.0
        from common.process_tools import _get_raw_material

        profile_raw = _get_raw_material("profile", profile_id)
        if profile_raw.get("len"):
            len_stick = float(profile_raw["len"])
        n_segments = [[s[0], s[1] * n] for s in segments]
        num_profile = _min_profiles(len_stick, n_segments)
        len_profile = sum(s[0] * s[1] for s in n_segments)
        cost_material = num_profile * float(profile.cost or 0)
        weight_unit = float(profile_raw.get("weight") or profile.weight_per_unit or 0)

        cut = calc_cut_profile(n, segments, CUT_TOOL, mode)
        mounted = calc_set_profile(n, segments, profile_id, mode)
        hanger_raw = params.get("is_hanger") or params.get("isHanger") or {}
        hanger = _hanger_part(n, hanger_raw if isinstance(hanger_raw, Mapping) else {})

        cost = cost_material + cut.cost + mounted.cost + hanger["cost"]
        price = (
            cost_material * (1 + MARGIN_MATERIAL)
            + cut.price
            + mounted.price
            + hanger["price"]
        )
        time_hours = cut.time_hours + mounted.time_hours + hanger["time_hours"]
        weight_kg = weight_unit * len_profile / 1000 + mounted.weight_kg + hanger["weight_kg"]
        idx = max(0, min(len(BASE_TIME_READY) - 1, math.ceil(mode)))
        time_ready = time_hours + float(BASE_TIME_READY[idx])
        profile_size = profile.sizes[0] if profile.sizes else [0, 0]
        materials: List[Dict[str, Any]] = [
            material_line(
                code=profile_id,
                name=profile.description,
                title=profile.title,
                quantity=num_profile,
                unit="шт",
                size_mm=[float(profile_size[0]), float(profile_size[1])],
            ),
            *list(mounted.materials or []),
            *hanger["materials"],
        ]
        return {
            "cost": float(cost),
            "price": float(price),
            "unit_price": round(float(price) / n, 2),
            "time_hours": float(time_hours),
            "time_ready": float(time_ready),
            "weight_kg": float(weight_kg),
            "materials": materials,
        }
