"""
Калькулятор АКРИЛОВЫХ ПРИЗОВ.

Мигрировано из js_legacy/calc/calcAcrilycPrizes.js.
Слои акрила: лазерная резка/гравировка, УФ-печать, УФ-склейка лицевой части к основанию.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping

from calculators.base import BaseCalculator, ProductionMode
from calculators.laser import LaserCalculator
from calculators.uv_print import UVPrintCalculator
from common.markups import get_margin
from common.process_tools import calc_uv_gluing


def _merge_materials(a: List[Dict[str, Any]], b: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Объединить списки материалов."""
    by_code: Dict[str, Dict[str, Any]] = {}
    for m in a + b:
        code = m.get("code", "")
        if code in by_code:
            q = by_code[code].get("quantity", 0)
            by_code[code]["quantity"] = q + m.get("quantity", 0)
        else:
            by_code[code] = dict(m)
    return list(by_code.values())


class AcrylicPrizesCalculator(BaseCalculator):
    """Акриловые призы: лазерная резка, УФ-печать, склейка слоёв."""

    slug = "acrylic_prizes"
    name = "Акриловые призы"
    description = "Расчёт акриловых призов: лазерная резка/гравировка, УФ-печать, склейка слоёв."

    def get_param_schema(self) -> Dict[str, Any]:
        return {
            "slug": self.slug,
            "title": self.name,
            "params": [
                {
                    "name": "quantity",
                    "type": "integer",
                    "required": True,
                    "title": "Тираж",
                    "validation": {"min": 1, "max": 10000},
                },
                {
                    "name": "layers",
                    "type": "array",
                    "required": True,
                    "title": "Слои",
                    "description": "Список слоёв: [{materialID, size: [w,h], isTop, options: {isGrave, isCutLaser, isUVPrint}}]",
                },
                {
                    "name": "mode",
                    "type": "integer",
                    "required": False,
                    "default": int(ProductionMode.STANDARD),
                    "title": "Режим",
                },
            ],
            "param_groups": {"main": ["quantity"], "layers": ["layers"], "mode": ["mode"]},
        }

    def get_options(self) -> Dict[str, Any]:
        return {
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
                    "layers": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "materialID": {"type": "string", "description": "Код материала hardsheet"},
                                "size": {"type": "array", "items": {"type": "number"}, "description": "[ширина, высота] мм"},
                                "isTop": {"type": "boolean", "description": "Лицевой слой (склеивается с основанием)"},
                                "options": {
                                    "type": "object",
                                    "properties": {
                                        "isGrave": {"type": "integer"},
                                        "isCutLaser": {"type": "object"},
                                        "isUVPrint": {"type": "object", "description": "Область печати {size: [w,h]}"},
                                    },
                                },
                            },
                        },
                    },
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["quantity", "layers"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        n = int(params.get("quantity", 1))
        layers = params.get("layers", [])
        mode = ProductionMode(int(params.get("mode", 1)))

        if not layers:
            raise ValueError("Укажите хотя бы один слой")

        mode_laser = mode.value
        mode_uv = mode.value
        mode_gluing = mode.value

        max_size_base = [0.0, 0.0]
        for layer in layers:
            if not isinstance(layer, dict):
                continue
            if not layer.get("isTop", False):
                size = layer.get("size", [0, 0])
                if len(size) >= 2:
                    max_size_base[0] = max(max_size_base[0], float(size[0]))
                    max_size_base[1] = max(max_size_base[1], float(size[1]))

        cost_layers = 0.0
        price_layers = 0.0
        time_layers = 0.0
        weight_layers = 0.0
        time_ready_layers = 0.0
        materials_out: List[Dict[str, Any]] = []

        laser_calc = LaserCalculator()
        uv_calc = UVPrintCalculator()

        for layer in layers:
            if not isinstance(layer, dict):
                continue
            material_id = str(layer.get("materialID", "") or "")
            size = layer.get("size", [0, 0])
            if len(size) < 2:
                size = [0, 0]
            size = [float(size[0]), float(size[1])]
            is_top = bool(layer.get("isTop", False))
            options = layer.get("options", {}) or {}

            cost_layer = 0.0
            price_layer = 0.0
            time_layer = 0.0
            weight_layer = 0.0
            time_ready_layer = 0.0
            materials_layer: List[Dict[str, Any]] = []

            if options.get("isGrave") is not None or options.get("isCutLaser"):
                laser_params = {
                    "quantity": n,
                    "width": size[0],
                    "height": size[1],
                    "material_id": material_id or "PVC3",
                    "mode": mode_laser,
                }
                if options.get("isGrave") is not None:
                    laser_params["is_grave"] = options["isGrave"]
                    if "is_grave_fill" in options:
                        laser_params["is_grave_fill"] = options["is_grave_fill"]
                    if "is_grave_contur" in options:
                        laser_params["is_grave_contur"] = options["is_grave_contur"]
                if options.get("isCutLaser"):
                    laser_params["is_cut_laser"] = options["isCutLaser"] if isinstance(options["isCutLaser"], dict) else {}
                try:
                    laser_result = laser_calc.calculate(laser_params)
                    cost_layer += laser_result["cost"]
                    price_layer += laser_result["price"]
                    time_layer += laser_result["time_hours"]
                    weight_layer += laser_result.get("weight_kg", 0)
                    time_ready_layer = max(time_ready_layer, laser_result.get("time_ready", 0))
                    materials_layer = _merge_materials(materials_layer, laser_result.get("materials", []))
                    if mode_laser > 0:
                        mode_laser = 0
                except Exception:
                    pass

            if options.get("isUVPrint"):
                uv_opts = options["isUVPrint"]
                if isinstance(uv_opts, dict):
                    size_print = uv_opts.get("size", size)
                else:
                    size_print = size
                if len(size_print) < 2:
                    size_print = size
                uv_params = {
                    "quantity": n,
                    "width": size_print[0],
                    "height": size_print[1],
                    "item_width": size[0],
                    "item_height": size[1],
                    "resolution": uv_opts.get("resolution", 2) if isinstance(uv_opts, dict) else 2,
                    "color": uv_opts.get("color", "4+1") if isinstance(uv_opts, dict) else "4+1",
                    "surface": uv_opts.get("surface", "plain") if isinstance(uv_opts, dict) else "plain",
                    "mode": mode_uv,
                }
                try:
                    uv_result = uv_calc.calculate(uv_params)
                    cost_layer += uv_result["cost"]
                    price_layer += uv_result["price"]
                    time_layer += uv_result["time_hours"]
                    weight_layer += uv_result.get("weight_kg", 0)
                    time_ready_layer = max(time_ready_layer, uv_result.get("time_ready", 0))
                    materials_layer = _merge_materials(materials_layer, uv_result.get("materials", []))
                    if mode_uv > 0:
                        mode_uv = 0
                except Exception:
                    pass

            if is_top and max_size_base[0] > 0 and max_size_base[1] > 0:
                try:
                    gluing_result = calc_uv_gluing(n, max_size_base, mode_gluing)
                    cost_layer += gluing_result.cost
                    price_layer += gluing_result.price
                    time_layer += gluing_result.time_hours
                    weight_layer += gluing_result.weight_kg
                    time_ready_layer = max(time_ready_layer, gluing_result.time_ready)
                    materials_layer = _merge_materials(materials_layer, gluing_result.materials)
                    if mode_gluing > 0:
                        mode_gluing = 0
                except Exception:
                    pass

            cost_layers += cost_layer
            price_layers += price_layer
            time_layers += time_layer
            weight_layers += weight_layer
            time_ready_layers = max(time_ready_layers, time_ready_layer)
            materials_out = _merge_materials(materials_out, materials_layer)

        margin = get_margin("marginAcrilycPrizes")
        price = math.ceil((price_layers) * (1 + margin))
        time_hours = math.ceil(time_layers * 100) / 100
        time_ready = time_hours + time_ready_layers

        return {
            "cost": float(cost_layers),
            "price": int(price),
            "unit_price": float(price) / max(1, n),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": round(weight_layers, 2),
            "materials": materials_out,
        }
