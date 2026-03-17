"""
Калькулятор ПОЛИМЕРНЫХ НАКЛЕЕК (с эпоксидной заливкой).

Мигрировано из js_legacy/calc/calcPolySticker.js.
Комбинирует: наклейка (sticker) + эпоксидная заливка.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping

from calculators.base import BaseCalculator, ProductionMode
from calculators.sticker import StickerCalculator
from common.markups import BASE_TIME_READY, get_margin
from common.process_tools import calc_epoxy
from equipment import tools as tools_catalog


class PolyStickerCalculator(BaseCalculator):
    """Полимерные наклейки с эпоксидной заливкой."""

    slug = "poly_sticker"
    name = "Полимерные наклейки"
    description = "Расчёт полимерных наклеек (стикеров) с эпоксидной заливкой."

    def get_options(self) -> Dict[str, Any]:
        sticker_calc = StickerCalculator()
        return sticker_calc.get_options()

    def get_tool_schema(self) -> Dict[str, Any]:
        return {
            "name": "calc_" + self.slug,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "quantity": {"type": "integer", "minimum": 1, "description": "Тираж, шт."},
                    "width": {"type": "number", "minimum": 1, "description": "Ширина, мм"},
                    "height": {"type": "number", "minimum": 1, "description": "Высота, мм"},
                    "difficulty": {"type": "number", "default": 1.0, "description": "Сложность формы: 1..2"},
                    "material_id": {"type": "string", "description": "Код материала"},
                    "color": {"type": "string", "description": "Цветность печати"},
                    "lamination_id": {"type": "string", "description": "Код ламинации"},
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["quantity", "width", "height", "material_id"],
            },
        }

    def get_param_schema(self) -> Dict[str, Any]:
        return {
            "slug": self.slug, "title": self.name,
            "params": [
                {"name": "quantity", "type": "integer", "required": True, "title": "Тираж", "validation": {"min": 1}},
                {"name": "width", "type": "number", "required": True, "title": "Ширина (мм)", "unit": "мм"},
                {"name": "height", "type": "number", "required": True, "title": "Высота (мм)", "unit": "мм"},
                {"name": "difficulty", "type": "number", "required": False, "default": 1.0, "title": "Сложность формы"},
                {"name": "material_id", "type": "enum_cascading", "required": True, "title": "Материал", "choices": {"source": "materials:sheet"}},
                {"name": "color", "type": "enum", "required": False, "title": "Цветность",
                 "choices": {"inline": [{"id": "1+0", "title": "1+0"}, {"id": "4+0", "title": "4+0"}, {"id": "1+1", "title": "1+1"}, {"id": "4+1", "title": "4+1"}, {"id": "4+4", "title": "4+4"}]}},
                {"name": "mode", "type": "enum", "required": False, "default": 1, "title": "Режим",
                 "choices": {"inline": [{"id": 0, "title": "Эконом"}, {"id": 1, "title": "Стандарт"}, {"id": 2, "title": "Экспресс"}]}},
            ],
            "param_groups": {"main": ["quantity", "width", "height"], "processing": ["difficulty", "color"], "material": ["material_id"], "mode": ["mode"]},
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        n = int(params.get("quantity", 1))
        width = float(params.get("width", 0))
        height = float(params.get("height", 0))
        size = [width, height]
        difficulty = float(params.get("difficulty", 1.0) or 1.0)
        material_id = str(params.get("material_id", "")).strip()
        mode = ProductionMode(int(params.get("mode", 1)))

        # Брак эпоксидной заливки
        try:
            epoxy_tool = tools_catalog.get("EpoxyCoating")
            defects = epoxy_tool.get_defect_rate(float(n))
        except Exception:
            defects = 0.05
        if mode.value >= 2:
            defects += defects * (mode.value - 1)
        n_stickers = math.ceil(n * (1 + defects))

        base_time_ready = BASE_TIME_READY
        try:
            epoxy_tool = tools_catalog.get("EpoxyCoating")
            if epoxy_tool.base_time_ready:
                base_time_ready = epoxy_tool.base_time_ready
        except Exception:
            pass
        idx = max(0, min(len(base_time_ready) - 1, mode.value))
        base_ready = float(base_time_ready[idx])

        # Расчёт наклейки (с учётом брака заливки)
        sticker_calc = StickerCalculator()
        sticker_params = dict(params)
        sticker_params["quantity"] = n_stickers
        sticker_params["size_item"] = width
        sticker_params["density"] = 0
        sticker_result = sticker_calc.calculate(sticker_params)

        # Расчёт эпоксидной заливки
        epoxy_result = calc_epoxy(n, size, difficulty, mode=mode.value)

        # Итого
        cost = math.ceil(
            float(sticker_result.get("cost", 0))
            + epoxy_result.cost
        )
        margin_poly = get_margin("marginStickerPoly")
        price = math.ceil(
            float(sticker_result.get("price", 0))
            + epoxy_result.price
        ) * (1 + margin_poly)

        time_hours = math.ceil(
            (float(sticker_result.get("time_hours", 0)) + epoxy_result.time_hours) * 100
        ) / 100.0
        time_ready = time_hours + base_ready

        weight_kg = math.ceil(
            (float(sticker_result.get("weight_kg", 0)) + epoxy_result.weight_kg) * 100
        ) / 100.0

        materials_out: List[Dict[str, Any]] = list(sticker_result.get("materials", []))
        materials_out.extend(epoxy_result.materials)

        return {
            "cost": float(cost),
            "price": float(price),
            "unit_price": float(price) / max(1, n),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": weight_kg,
            "materials": materials_out,
        }
