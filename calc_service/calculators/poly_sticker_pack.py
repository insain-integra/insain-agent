"""
Калькулятор СТИКЕРПАКОВ С ПОЛИМЕРНОЙ ЗАЛИВКОЙ.

Мигрировано из js_legacy/calc/calcPolySticker.js (функция calcPolyStickerPack, строки 51-133).
Комбинирует: наклейка (sticker) + нарезка на паки (cut_saber) + эпоксидная заливка.

Для LLM/агента массив stickers упрощён до трёх скалярных параметров:
  num_stickers, sticker_size, sticker_difficulty.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping

from calculators.base import BaseCalculator, ProductionMode
from calculators.sticker import StickerCalculator
from common.markups import BASE_TIME_READY, get_margin
from common.process_tools import calc_cut_saber, calc_epoxy
from equipment import tools as tools_catalog


CUTTER_ID = "Ideal1046"
CUT_MARGINS = [2, 2, 2, 2]
CUT_INTERVAL = 4


class PolyStickerPackCalculator(BaseCalculator):
    """Стикерпаки с полимерной заливкой."""

    slug = "poly_sticker_pack"
    name = "Стикерпаки с полимерной заливкой"
    description = "Расчёт стоимости стикерпаков (наборов наклеек на листе) с эпоксидной заливкой."
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
                    "quantity": {"type": "integer", "minimum": 1, "description": "Тираж стикерпаков, шт."},
                    "width": {"type": "number", "minimum": 1, "description": "Ширина стикерпака, мм"},
                    "height": {"type": "number", "minimum": 1, "description": "Высота стикерпака, мм"},
                    "material_id": {"type": "string", "description": "Код материала"},
                    "num_stickers": {"type": "integer", "minimum": 1, "default": 5, "description": "Кол-во наклеек в стикерпаке"},
                    "sticker_size": {"type": "number", "minimum": 1, "default": 30, "description": "Средний размер наклейки, мм"},
                    "sticker_difficulty": {"type": "number", "default": 1.0, "description": "Средняя сложность формы наклеек: 1..2"},
                    "is_background": {"type": "boolean", "default": False, "description": "Фон остаётся (уменьшает размер элементов для резки)"},
                    "print_method": {
                        "type": "string",
                        "enum": ["No", "KMBizhubC220", "Technojet160ECO", "HPLatex335"],
                        "default": "KMBizhubC220",
                        "description": "Способ печати",
                    },
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
                {"name": "quantity", "type": "integer", "required": True, "title": "Тираж стикерпаков", "validation": {"min": 1}},
                {"name": "width", "type": "number", "required": True, "title": "Ширина стикерпака (мм)", "unit": "мм"},
                {"name": "height", "type": "number", "required": True, "title": "Высота стикерпака (мм)", "unit": "мм"},
                {"name": "material_id", "type": "enum_cascading", "required": True, "title": "Материал", "choices": {"source": "materials:sheet"}},
                {"name": "num_stickers", "type": "integer", "required": False, "default": 5, "title": "Наклеек в стикерпаке", "validation": {"min": 1, "max": 50}},
                {"name": "sticker_size", "type": "number", "required": False, "default": 30, "title": "Средний размер наклейки (мм)", "unit": "мм", "validation": {"min": 5, "max": 200}},
                {"name": "sticker_difficulty", "type": "number", "required": False, "default": 1.0, "title": "Сложность формы наклеек", "validation": {"min": 1, "max": 2}},
                {"name": "is_background", "type": "boolean", "required": False, "default": False, "title": "Фон остаётся"},
                {"name": "print_method", "type": "enum", "required": False, "default": "KMBizhubC220", "title": "Способ печати",
                 "choices": {"inline": [
                     {"id": "No", "title": "Без печати"},
                     {"id": "KMBizhubC220", "title": "Лазерная печать"},
                     {"id": "Technojet160ECO", "title": "УФ-печать Technojet"},
                     {"id": "HPLatex335", "title": "Латексная печать HP"},
                 ]}},
                {"name": "mode", "type": "enum", "required": False, "default": 1, "title": "Режим",
                 "choices": {"inline": [{"id": 0, "title": "Эконом"}, {"id": 1, "title": "Стандарт"}, {"id": 2, "title": "Экспресс"}]}},
            ],
            "param_groups": {
                "main": ["quantity", "width", "height"],
                "stickers": ["num_stickers", "sticker_size", "sticker_difficulty", "is_background"],
                "processing": ["print_method"],
                "material": ["material_id"],
                "mode": ["mode"],
            },
        }

    def get_llm_prompt(self) -> str:
        return ""

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        n = int(params.get("quantity", 1))
        width = float(params.get("width", 0))
        height = float(params.get("height", 0))
        size = [width, height]
        material_id = str(params.get("material_id", "")).strip()
        mode = ProductionMode(int(params.get("mode", 1)))

        num_stickers = int(params.get("num_stickers", 5) or 5)
        sticker_size = float(params.get("sticker_size", 30) or 30)
        sticker_difficulty = float(params.get("sticker_difficulty", 1.0) or 1.0)
        is_background = bool(params.get("is_background", False))
        print_method = str(params.get("print_method", "KMBizhubC220") or "KMBizhubC220").strip()

        # --- Агрегированные метрики наклеек (аналог JS-цикла по stickers[]) ---
        # sizeItem — средний размер элемента для резки
        size_item = sticker_size
        if is_background:
            size_item /= 3

        # difficulty — средняя сложность, делённая на 1.1 (стикерпак сложнее одиночной наклейки)
        difficulty = sticker_difficulty / 1.1

        # areaItem — средняя площадь одной наклейки
        area_item = sticker_size * sticker_size

        # density — плотность заполнения: суммарная площадь наклеек / площадь стикерпака
        pack_area = width * height
        if pack_area <= 0:
            raise ValueError("Размер стикерпака должен быть > 0")
        density = min(1.0, (num_stickers * area_item) / pack_area)

        # --- Брак эпоксидной заливки ---
        try:
            epoxy_tool = tools_catalog.get("EpoxyCoating")
            defects = epoxy_tool.get_defect_rate(float(n))
        except Exception:
            defects = 0.05
        if mode.value > 1:
            defects += defects * (mode.value - 1)
        n_stickers = math.ceil(n * (1 + defects))

        # base_time_ready из EpoxyCoating
        base_time_ready = BASE_TIME_READY
        try:
            epoxy_tool = tools_catalog.get("EpoxyCoating")
            if epoxy_tool.base_time_ready:
                base_time_ready = epoxy_tool.base_time_ready
        except Exception:
            pass
        idx = max(0, min(len(base_time_ready) - 1, mode.value))
        base_ready = float(base_time_ready[idx])

        # --- 1. Расчёт наклейки (с учётом брака заливки) ---
        sticker_calc = StickerCalculator()
        color = "4+0" if print_method != "No" else ""
        sticker_params: Dict[str, Any] = {
            "quantity": n_stickers,
            "width": width,
            "height": height,
            "size_item": size_item,
            "density": density,
            "difficulty": difficulty,
            "material_id": material_id,
            "color": color,
            "printer_code": print_method if print_method != "No" else "",
            "mode": mode.value,
        }
        sticker_result = sticker_calc.calculate(sticker_params)

        # --- 2. Нарезка на отдельные стикерпаки (сабельный резак) ---
        sticker_materials = sticker_result.get("materials", [])
        num_sheet = 1
        size_sheet = [320, 450]
        for m in sticker_materials:
            if m.get("code") == material_id:
                qty = m.get("quantity", 0)
                unit = m.get("unit", "")
                if unit == "sheet":
                    num_sheet = int(qty)
                size_mm = m.get("size_mm")
                if size_mm and isinstance(size_mm, (list, tuple)) and len(size_mm) >= 2:
                    size_sheet = [float(size_mm[0]), float(size_mm[1])]
                break

        cut_result = calc_cut_saber(
            num_sheet=num_sheet,
            size=size,
            size_sheet=size_sheet,
            material_id=material_id,
            cutter_id=CUTTER_ID,
            margins=CUT_MARGINS,
            interval=CUT_INTERVAL,
            mode=mode.value,
        )

        # --- 3. Эпоксидная заливка (для каждой наклейки на каждом стикерпаке) ---
        epoxy_side = math.sqrt(area_item)
        epoxy_result = calc_epoxy(
            n=n * num_stickers,
            size=[epoxy_side, epoxy_side],
            difficulty=difficulty,
            mode=mode.value,
        )

        # --- 4. Итого ---
        cost = math.ceil(
            float(sticker_result.get("cost", 0))
            + epoxy_result.cost
            + cut_result.cost
        )
        margin_poly = get_margin("marginStickerPoly")
        price = math.ceil(
            float(sticker_result.get("price", 0))
            + epoxy_result.price
            + cut_result.price
        ) * (1 + margin_poly)

        time_hours = math.ceil(
            (
                float(sticker_result.get("time_hours", 0))
                + epoxy_result.time_hours
                + cut_result.time_hours
            ) * 100
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
