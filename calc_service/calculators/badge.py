"""
Калькулятор бейджей.

Мигрировано из js_legacy/calc/calcBadge.js.
Упрощённая версия: печать + лазерная резка + опционально УФ-печать + крепление + упаковка.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping

from calculators.base import BaseCalculator, ProductionMode
from calculators.print_sheet import PrintSheetCalculator
from calculators.laser import LaserCalculator
from calculators.uv_print import UVPrintCalculator
from common.helpers import calc_weight
from common.layout import layout_on_sheet
from common.markups import BASE_TIME_READY, MARGIN_MATERIAL, MARGIN_OPERATION, get_margin, get_time_ready
from common.process_tools import calc_attachment, calc_packing
from equipment import laminator as laminator_catalog
from materials import hardsheet as hardsheet_catalog, sheet as sheet_catalog

DEFAULT_PRINT_MATERIAL = "RaflatacMW"
DEFAULT_LAMINATION = "Laminat32G"
SIZE_SHEET_BADGE = [320, 450]
LAMINATOR_CODE = "FGKFM360"


def _calc_lamination_roll(num_sheet: int, size_sheet: List[float], mode: int) -> Dict[str, Any]:
    """
    Накатка отпечатанных листов на основу (аналог calcLaminationRoll из JS).
    """
    try:
        laminator = laminator_catalog.get(LAMINATOR_CODE)
    except KeyError:
        return {"cost": 0.0, "price": 0.0, "time_hours": 0.0, "time_ready": 0.0}

    defects = laminator.get_defect_rate(float(num_sheet))
    if mode > 1:
        defects += defects * (mode - 1)
    num_with_defects = math.ceil(num_sheet * (1 + defects))

    meter_per_hour = 25.0
    from common.layout import layout_on_roll
    layout = layout_on_roll(1, size_sheet, laminator.max_size or [330, 0], 0)
    length_m = (layout.get("length", 1000) or 1000) / 1000.0
    if length_m <= 0:
        length_m = 0.5
    sheet_per_hour = max(1, meter_per_hour / length_m)

    time_prepare = (laminator.time_prepare or 0.1) * mode
    time_roll = num_with_defects / sheet_per_hour + time_prepare
    cost_roll = laminator.depreciation_per_hour * time_roll
    cost_operator = time_roll * laminator.operator_cost_per_hour

    cost = cost_roll + cost_operator
    margin_lam = get_margin("marginLamination") or 0
    price = (cost_roll + cost_operator) * (1 + MARGIN_OPERATION + margin_lam)

    return {
        "cost": cost,
        "price": price,
        "time_hours": math.ceil(time_roll * 100) / 100,
        "time_ready": time_roll,
    }


class BadgeCalculator(BaseCalculator):
    """Бейджи: печать + лазерная резка + опционально УФ-печать + крепление + упаковка."""

    slug = "badge"
    name = "Бейджи"
    description = "Расчёт стоимости бейджей: печать, лазерная резка, опционально УФ-печать, крепление, упаковка."

    def get_param_schema(self) -> Dict[str, Any]:
        return {
            "slug": self.slug,
            "title": self.name,
            "params": [
                {"name": "quantity", "type": "integer", "required": True, "title": "Тираж", "validation": {"min": 1}},
                {"name": "width", "type": "number", "required": True, "title": "Ширина (мм)", "unit": "мм"},
                {"name": "height", "type": "number", "required": True, "title": "Высота (мм)", "unit": "мм"},
                {"name": "difficulty", "type": "number", "required": False, "default": 1.0, "title": "Сложность формы"},
                {"name": "material_id", "type": "string", "required": True, "title": "Материал основы (hardsheet)"},
                {"name": "is_print", "type": "boolean", "required": False, "default": True, "title": "Печать"},
                {"name": "color", "type": "string", "required": False, "default": "4+0", "title": "Цветность печати"},
                {"name": "is_uv_print", "type": "boolean", "required": False, "default": False, "title": "УФ-печать"},
                {"name": "attachment_id", "type": "string", "required": False, "title": "Крепление"},
                {"name": "packing_id", "type": "string", "required": False, "title": "Упаковка"},
                {"name": "mode", "type": "integer", "required": False, "default": 1, "title": "Режим"},
            ],
            "param_groups": {
                "main": ["quantity", "width", "height"],
                "material": ["material_id"],
                "processing": ["is_print", "color", "is_uv_print", "attachment_id", "packing_id"],
                "mode": ["mode"],
            },
        }

    def get_options(self) -> Dict[str, Any]:
        materials = hardsheet_catalog.list_for_frontend()
        attachments = []
        try:
            from materials import attachment
            attachments = [{"code": m["code"], "name": m.get("title", m.get("name", ""))} for m in attachment.list_for_frontend()]
        except Exception:
            pass
        return {
            "materials": materials[:50],
            "attachments": attachments[:20],
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
                    "width": {"type": "number", "minimum": 1, "description": "Ширина, мм"},
                    "height": {"type": "number", "minimum": 1, "description": "Высота, мм"},
                    "difficulty": {"type": "number", "default": 1.0, "description": "Сложность формы"},
                    "material_id": {"type": "string", "description": "Код материала из hardsheet"},
                    "is_print": {"type": "boolean", "default": True, "description": "Печать"},
                    "color": {"type": "string", "default": "4+0", "description": "Цветность"},
                    "is_uv_print": {"type": "boolean", "default": False, "description": "УФ-печать"},
                    "attachment_id": {"type": "string", "description": "Код крепления"},
                    "packing_id": {"type": "string", "description": "Код упаковки"},
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["quantity", "width", "height", "material_id"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        n = int(params.get("quantity", 1))
        width = float(params.get("width", 0))
        height = float(params.get("height", 0))
        size = [width, height]
        difficulty = float(params.get("difficulty", 1.0) or 1.0)
        material_id = str(params.get("material_id", "") or "").strip()
        is_print = bool(params.get("is_print", True))
        color = str(params.get("color", "4+0") or "4+0").strip()
        is_uv_print = bool(params.get("is_uv_print", False))
        attachment_id = str(params.get("attachment_id", "") or "").strip()
        packing_id = str(params.get("packing_id", "") or "").strip()
        mode = ProductionMode(int(params.get("mode", 1)))

        if not material_id:
            raise ValueError("material_id обязателен")

        material = hardsheet_catalog.get(material_id)

        cost_print = 0.0
        price_print = 0.0
        time_print = 0.0
        time_ready_print = 0.0
        weight_print = 0.0
        cost_laser1 = 0.0
        price_laser1 = 0.0
        time_laser1 = 0.0
        time_ready_laser1 = 0.0
        weight_laser1 = 0.0
        cost_roll = 0.0
        price_roll = 0.0
        time_roll = 0.0
        n_items = n
        num_sheet = 0

        materials_out: List[Dict[str, Any]] = []

        if is_print:
            # Печать (без резки — no_cut)
            print_calc = PrintSheetCalculator()
            print_params = {
                "quantity": n,
                "width": size[0],
                "height": size[1],
                "color": color,
                "margins": [2, 2, 2, 2],
                "interval": 4,
                "material_id": DEFAULT_PRINT_MATERIAL,
                "lamination_id": DEFAULT_LAMINATION,
                "no_cut": True,
                "mode": mode.value,
            }
            try:
                sheet_mat = sheet_catalog.get(DEFAULT_PRINT_MATERIAL)
            except KeyError:
                sheet_mat = None
            if sheet_mat:
                print_result = print_calc.calculate(print_params)
                cost_print = float(print_result.get("cost", 0))
                price_print = float(print_result.get("price", 0))
                time_print = float(print_result.get("time_hours", 0))
                time_ready_print = float(print_result.get("time_ready", 0))
                weight_print = float(print_result.get("weight_kg", 0))
                materials_out.extend(print_result.get("materials") or [])

            # Лазерная резка основы (листы 320x450)
            layout = layout_on_sheet(size, SIZE_SHEET_BADGE, [5, 5, 5, 5], 4)
            if layout["num"] == 0:
                raise ValueError("Размер изделия больше допустимого")
            num_sheet = math.ceil(n / layout["num"])

            laser_calc = LaserCalculator()
            laser_params1 = {
                "quantity": num_sheet,
                "width": SIZE_SHEET_BADGE[0],
                "height": SIZE_SHEET_BADGE[1],
                "material_id": material_id,
                "is_cut_laser": {"size_item": size[0] * size[1], "density": 0, "difficulty": 1, "len_cut": 0},
                "mode": mode.value,
            }
            laser_result1 = laser_calc.calculate(laser_params1)
            cost_laser1 = float(laser_result1.get("cost", 0))
            price_laser1 = float(laser_result1.get("price", 0))
            time_laser1 = float(laser_result1.get("time_hours", 0))
            time_ready_laser1 = float(laser_result1.get("time_ready", 0))
            weight_laser1 = float(laser_result1.get("weight_kg", 0))
            materials_out.extend(laser_result1.get("materials") or [])

            # Накатка
            roll_result = _calc_lamination_roll(num_sheet, SIZE_SHEET_BADGE, mode.value)
            cost_roll = roll_result["cost"]
            price_roll = roll_result["price"]
            time_roll = roll_result["time_hours"]

        # Лазерная резка изделий
        laser_calc = LaserCalculator()
        laser_params2 = {
            "quantity": n_items,
            "width": size[0],
            "height": size[1],
            "material_id": material_id,
            "is_cut_laser": {"size_item": size[0] * size[1], "density": 0, "difficulty": difficulty, "len_cut": 0},
            "mode": mode.value,
        }
        if is_print:
            laser_params2["material_mode"] = "noMaterial"
        laser_result2 = laser_calc.calculate(laser_params2)
        cost_laser2 = float(laser_result2.get("cost", 0))
        price_laser2 = float(laser_result2.get("price", 0))
        time_laser2 = float(laser_result2.get("time_hours", 0))
        time_ready_laser2 = float(laser_result2.get("time_ready", 0))
        weight_laser2 = float(laser_result2.get("weight_kg", 0))
        if not is_print:
            materials_out.extend(laser_result2.get("materials") or [])

        # УФ-печать
        cost_uv = 0.0
        price_uv = 0.0
        time_uv = 0.0
        time_ready_uv = 0.0
        if is_uv_print:
            uv_calc = UVPrintCalculator()
            uv_params = {
                "quantity": n,
                "width": size[0],
                "height": size[1],
                "item_width": size[0],
                "item_height": size[1],
                "resolution": 2,
                "color": "4+0",
                "surface": "plain",
                "mode": mode.value,
            }
            uv_result = uv_calc.calculate(uv_params)
            cost_uv = float(uv_result.get("cost", 0))
            price_uv = float(uv_result.get("price", 0))
            time_uv = float(uv_result.get("time_hours", 0))
            time_ready_uv = float(uv_result.get("time_ready", 0))
            materials_out.extend(uv_result.get("materials") or [])

        # Крепление
        cost_attach = 0.0
        price_attach = 0.0
        time_attach = 0.0
        weight_attach = 0.0
        if attachment_id:
            attach_result = calc_attachment(n, attachment_id, mode.value)
            cost_attach = attach_result.cost
            price_attach = attach_result.price
            time_attach = attach_result.time_hours
            weight_attach = attach_result.weight_kg
            materials_out.extend(attach_result.materials)

        # Упаковка
        cost_pack = 0.0
        price_pack = 0.0
        time_pack = 0.0
        weight_pack = 0.0
        if packing_id:
            pack_result = calc_packing(n, [size[0], size[1], 5], {"isPacking": packing_id}, mode.value)
            cost_pack = pack_result.cost
            price_pack = pack_result.price
            time_pack = pack_result.time_hours
            weight_pack = pack_result.weight_kg
            materials_out.extend(pack_result.materials)

        # Итог
        cost_total = cost_print + cost_laser1 + cost_roll + cost_laser2 + cost_uv + cost_attach + cost_pack
        price_total = price_print + price_laser1 + price_roll + price_laser2 + price_uv + price_attach + price_pack
        margin_badge = get_margin("marginBadge")
        price_total = math.ceil(price_total * (1 + margin_badge))

        time_hours = time_print + time_laser1 + time_roll + time_laser2 + time_uv + time_attach + time_pack
        time_hours = math.ceil(time_hours * 100) / 100.0

        time_ready_list = [
            time_ready_print, time_ready_laser1, time_ready_laser2, time_ready_uv,
        ]
        base_ready = get_time_ready("baseTimeReady")
        idx = max(0, min(len(base_ready) - 1, mode.value))
        ready_vals = [t for t in time_ready_list if t > 0] or [time_hours + float(base_ready[idx])]
        time_ready = max(ready_vals)

        weight_kg = weight_print + weight_laser1 + weight_laser2 + weight_attach + weight_pack
        weight_kg = math.ceil(weight_kg * 100) / 100.0

        return {
            "cost": float(cost_total),
            "price": int(price_total),
            "unit_price": float(price_total) / max(1, n),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": weight_kg,
            "materials": materials_out,
        }
