"""
Калькулятор УФ-БЕЙДЖЕЙ.

Мигрировано из js_legacy/calc/calcUVBadge.js.
Комбинирует: лазерная резка + УФ-печать + крепёж + карман + упаковка.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping

from calculators.base import BaseCalculator, ProductionMode
from calculators.laser import LaserCalculator
from calculators.uv_print import UVPrintCalculator
from common.markups import BASE_TIME_READY, get_margin
from common.process_tools import calc_attachment, calc_pocket, calc_packing
from equipment import printer as printer_catalog

UV_PRINTER_CODE = "RimalSuvUV"


class UVBadgeCalculator(BaseCalculator):
    """УФ-бейджи: лазерная резка + УФ-печать + крепёж."""

    slug = "uv_badge"
    name = "УФ-бейджи"
    description = "Расчёт бейджей с УФ-печатью: лазерная резка + печать + крепёж + упаковка."

    def get_options(self) -> Dict[str, Any]:
        from materials import hardsheet as hs
        materials = hs.list_for_frontend()
        return {
            "materials": materials[:40],
            "colors": ["4+0", "1+0", "4+1", "4+2"],
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
                    "quantity": {"type": "integer", "minimum": 1, "description": "Тираж"},
                    "width": {"type": "number", "minimum": 1, "description": "Ширина, мм"},
                    "height": {"type": "number", "minimum": 1, "description": "Высота, мм"},
                    "difficulty": {"type": "number", "default": 1.0, "description": "Сложность формы: 1..2"},
                    "color": {"type": "string", "default": "4+0", "description": "Цветность: 4+0, 1+0, 4+1, 4+2"},
                    "material_id": {"type": "string", "description": "Код материала (hardsheet)"},
                    "attachment_id": {"type": "string", "description": "Код крепежа (опционально)"},
                    "pocket_id": {"type": "string", "description": "Код кармана (опционально)"},
                    "is_packing": {"type": "boolean", "default": False, "description": "Индивидуальная упаковка"},
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
                {"name": "color", "type": "enum", "required": False, "default": "4+0", "title": "Цветность",
                 "choices": {"inline": [{"id": "4+0", "title": "4+0"}, {"id": "1+0", "title": "1+0"}, {"id": "4+1", "title": "4+1"}, {"id": "4+2", "title": "4+2"}]}},
                {"name": "material_id", "type": "enum_cascading", "required": True, "title": "Материал", "choices": {"source": "materials:hardsheet"}},
                {"name": "attachment_id", "type": "string", "required": False, "title": "Крепёж"},
                {"name": "pocket_id", "type": "string", "required": False, "title": "Карман"},
                {"name": "is_packing", "type": "boolean", "required": False, "default": False, "title": "Индивидуальная упаковка"},
                {"name": "mode", "type": "enum", "required": False, "default": 1, "title": "Режим",
                 "choices": {"inline": [{"id": 0, "title": "Эконом"}, {"id": 1, "title": "Стандарт"}, {"id": 2, "title": "Экспресс"}]}},
            ],
            "param_groups": {"main": ["quantity", "width", "height"], "processing": ["difficulty", "color"], "material": ["material_id"], "options": ["attachment_id", "pocket_id", "is_packing"], "mode": ["mode"]},
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        n = int(params.get("quantity", 1))
        width = float(params.get("width", 0))
        height = float(params.get("height", 0))
        size = [width, height]
        difficulty = float(params.get("difficulty", 1.0) or 1.0)
        color = str(params.get("color", "4+0") or "4+0").strip()
        material_id = str(params.get("material_id", "")).strip()
        attachment_id = str(params.get("attachment_id", "") or "").strip()
        pocket_id = str(params.get("pocket_id", "") or "").strip()
        is_packing = bool(params.get("is_packing", False))
        mode = ProductionMode(int(params.get("mode", 1)))

        try:
            printer = printer_catalog.get(UV_PRINTER_CODE)
        except KeyError:
            return self._empty(mode)

        base_time_ready = printer.base_time_ready or BASE_TIME_READY
        idx = max(0, min(len(base_time_ready) - 1, mode.value))
        base_ready = float(base_time_ready[idx])

        # Брак УФ-печати
        defects = printer.get_defect_rate(float(n))
        if mode.value >= 2:
            defects += defects * (mode.value - 1)
        n_items = math.ceil(n * (1 + defects))

        # Лазерная резка
        len_cut = (size[0] + size[1]) * 2 * difficulty / 1000.0  # в метрах
        if pocket_id:
            len_cut += 0.180  # ~180мм для окошка кармана

        laser_calc = LaserCalculator()
        laser_result = laser_calc.calculate({
            "quantity": n_items,
            "width": width,
            "height": height,
            "material_id": material_id,
            "cut_length_m": len_cut * n_items,
            "mode": mode.value,
        })

        # УФ-печать
        uv_calc = UVPrintCalculator()
        uv_result = uv_calc.calculate({
            "quantity": n,
            "width": width,
            "height": height,
            "item_width": width,
            "item_height": height,
            "resolution": 2,
            "color": color,
            "surface": "plain",
            "printer_code": UV_PRINTER_CODE,
            "mode": mode.value,
        })

        # Крепёж
        attach_result = {"cost": 0, "price": 0, "time": 0, "weight": 0, "materials": []}
        if attachment_id:
            try:
                attach_result = calc_attachment(n, attachment_id, mode.value)
            except Exception:
                pass

        # Карман
        pocket_result = {"cost": 0, "price": 0, "time": 0, "weight": 0, "materials": []}
        if pocket_id:
            try:
                pocket_result = calc_pocket(n, pocket_id, mode.value)
            except Exception:
                pass

        # Упаковка
        packing_result = {"cost": 0, "price": 0, "time": 0, "weight": 0, "materials": []}
        if is_packing:
            try:
                packing_result = calc_packing(n, [size[0], size[1], 5], mode=mode.value)
            except Exception:
                pass

        # Итого
        cost = math.ceil(
            float(uv_result.get("cost", 0))
            + float(laser_result.get("cost", 0))
            + float(attach_result.get("cost", 0))
            + float(pocket_result.get("cost", 0))
            + float(packing_result.get("cost", 0))
        )
        margin_badge = get_margin("marginBadge")
        price = math.ceil(
            float(uv_result.get("price", 0))
            + float(laser_result.get("price", 0))
            + float(attach_result.get("price", 0))
            + float(pocket_result.get("price", 0))
            + float(packing_result.get("price", 0))
        ) * (1 + margin_badge)

        time_hours = math.ceil((
            float(uv_result.get("time_hours", 0))
            + float(laser_result.get("time_hours", 0))
            + float(attach_result.get("time", 0))
            + float(pocket_result.get("time", 0))
            + float(packing_result.get("time", 0))
        ) * 100) / 100.0
        time_ready = time_hours + base_ready

        weight_kg = math.ceil((
            float(laser_result.get("weight_kg", 0))
            + float(pocket_result.get("weight", 0))
            + float(packing_result.get("weight", 0))
        ) * 100) / 100.0

        materials_out: List[Dict[str, Any]] = list(laser_result.get("materials", []))
        for r in (attach_result, pocket_result, packing_result):
            materials_out.extend(r.get("materials", []))

        return {
            "cost": float(cost),
            "price": float(price),
            "unit_price": float(price) / max(1, n),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": weight_kg,
            "materials": materials_out,
        }

    def _empty(self, mode: ProductionMode) -> Dict[str, Any]:
        btr = BASE_TIME_READY
        idx = max(0, min(len(btr) - 1, mode.value))
        return {
            "cost": 0.0, "price": 0.0, "unit_price": 0.0,
            "time_hours": 0.0, "time_ready": float(btr[idx]),
            "weight_kg": 0.0, "materials": [],
        }
