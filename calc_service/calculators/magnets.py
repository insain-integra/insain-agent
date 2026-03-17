"""
Калькулятор магнитов.

Перенесено из js_legacy/calc/calcMagnets.js.
Два типа: акриловые магниты (вставка + заготовка) и ламинированные (печать + ламинация + магнитный винил + резка).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping

from calculators.base import BaseCalculator, ProductionMode
from calculators.print_sheet import PrintSheetCalculator
from calculators.lamination import LaminationCalculator
from calculators.cut_guillotine import CutGuillotineCalculator
from common.markups import BASE_TIME_READY, MARGIN_MATERIAL, get_margin
from common.process_tools import calc_packing, calc_set_insert
from materials import magnet as magnet_catalog
from materials import get_material

DEFAULT_INSERT_MATERIAL = "PaperCoated115M"
DEFAULT_PRINT_MATERIAL = "RAFLACOAT"
ZIPLOCK_ACRYLIC = "ZipLockAcrylic"


class MagnetsCalculator(BaseCalculator):
    """Магниты: акриловые или ламинированные."""

    slug = "magnets"
    name = "Магниты"
    description = (
        "Расчёт магнитов: акриловые (заготовка + печать вставки) или "
        "ламинированные (печать + ламинация + магнитный винил + резка)."
    )

    def get_param_schema(self) -> Dict[str, Any]:
        magnets = magnet_catalog.list_for_frontend()
        choices = [{"id": m["code"], "title": m.get("title", m.get("name", m["code"]))} for m in magnets]
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
                    "name": "magnet_type",
                    "type": "enum",
                    "required": True,
                    "default": "acrylic",
                    "title": "Тип магнита",
                    "choices": {
                        "inline": [
                            {"id": "acrylic", "title": "Акриловые"},
                            {"id": "laminated", "title": "Ламинированные"},
                        ]
                    },
                },
                {
                    "name": "magnet_id",
                    "type": "enum",
                    "required": True,
                    "title": "Заготовка / материал",
                    "description": "Для акриловых — заготовка, для ламинированных — магнитный винил",
                    "choices": {"inline": choices},
                },
                {
                    "name": "width_mm",
                    "type": "number",
                    "required": False,
                    "title": "Ширина (мм)",
                    "description": "Для ламинированных",
                    "validation": {"min": 10, "max": 500},
                    "unit": "мм",
                },
                {
                    "name": "height_mm",
                    "type": "number",
                    "required": False,
                    "title": "Высота (мм)",
                    "description": "Для ламинированных",
                    "validation": {"min": 10, "max": 500},
                    "unit": "мм",
                },
                {
                    "name": "color",
                    "type": "integer",
                    "required": False,
                    "default": 1,
                    "title": "Печать",
                    "description": "1 — односторонняя, 2 — двухсторонняя",
                    "choices": {
                        "inline": [
                            {"id": 1, "title": "Односторонняя"},
                            {"id": 2, "title": "Двухсторонняя"},
                        ]
                    },
                },
                {
                    "name": "lamination_id",
                    "type": "string",
                    "required": False,
                    "title": "Ламинация",
                    "description": "Код плёнки для ламинированных (пусто — без ламинации)",
                },
                {
                    "name": "is_packing",
                    "type": "boolean",
                    "required": False,
                    "default": True,
                    "title": "Упаковка",
                },
                {
                    "name": "mode",
                    "type": "enum",
                    "required": False,
                    "default": int(ProductionMode.STANDARD),
                    "title": "Режим",
                    "choices": {
                        "inline": [
                            {"id": 0, "title": "Эконом"},
                            {"id": 1, "title": "Стандарт"},
                            {"id": 2, "title": "Экспресс"},
                        ]
                    },
                },
            ],
            "param_groups": {
                "main": ["quantity", "magnet_type", "magnet_id"],
                "size": ["width_mm", "height_mm"],
                "options": ["color", "lamination_id", "is_packing"],
                "mode": ["mode"],
            },
        }

    def get_options(self) -> Dict[str, Any]:
        return {
            "magnets": magnet_catalog.list_for_frontend(),
            "modes": [
                {"value": 0, "label": "Экономичный"},
                {"value": 1, "label": "Стандартный"},
                {"value": 2, "label": "Экспресс"},
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
                    "magnet_type": {
                        "type": "string",
                        "enum": ["acrylic", "laminated"],
                        "description": "Тип: acrylic — акриловые, laminated — ламинированные",
                    },
                    "magnet_id": {"type": "string", "description": "Код заготовки или магнитного винила"},
                    "width_mm": {"type": "number", "description": "Ширина (для ламинированных), мм"},
                    "height_mm": {"type": "number", "description": "Высота (для ламинированных), мм"},
                    "color": {"type": "integer", "minimum": 1, "maximum": 2, "description": "1 или 2 стороны печати"},
                    "lamination_id": {"type": "string", "description": "Плёнка ламинации (для ламинированных)"},
                    "is_packing": {"type": "boolean", "default": True},
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["quantity", "magnet_type", "magnet_id"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        magnet_type = str(params.get("magnet_type", "acrylic") or "acrylic").strip().lower()
        if magnet_type == "acrylic":
            return self._calc_acrylic(params)
        return self._calc_laminated(params)

    def _calc_acrylic(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        """Акриловые магниты: заготовка + печать вставки + установка вставки + упаковка."""
        from common.process_tools import _get_raw_material

        quantity = int(params.get("quantity", 1))
        magnet_id = str(params.get("magnet_id", "") or "MagnetAcrylic6565")
        color = int(params.get("color", 1) or 1)
        is_packing = bool(params.get("is_packing", True))
        mode = ProductionMode(int(params.get("mode", 1)))

        magnet = magnet_catalog.get(magnet_id)
        try:
            raw = _get_raw_material("magnet", magnet_id)
        except KeyError:
            raw = {}
        size = list(raw.get("size", magnet.sizes[0] if magnet.sizes else [65, 65]))
        size_insert = list(raw.get("sizeInsert", size))

        color_str = "4+4" if color >= 2 else "4+0"

        cost_blank = float(magnet.cost or 0) * quantity
        price_blank = cost_blank * (1 + MARGIN_MATERIAL)
        weight_blank = float(raw.get("weight", 20)) * quantity / 1000.0

        mat_blank = {
            "code": magnet_id,
            "name": magnet.description,
            "title": magnet.title,
            "quantity": quantity,
            "unit": "шт",
        }

        print_calc = PrintSheetCalculator()
        print_params = {
            "quantity": quantity,
            "width": size_insert[0],
            "height": size_insert[1],
            "material_id": DEFAULT_INSERT_MATERIAL,
            "color": color_str,
            "lamination_id": "",
            "mode": mode.value,
        }
        print_result = print_calc.calculate(print_params)
        cost_insert = float(print_result.get("cost", 0))
        price_insert = float(print_result.get("price", 0))
        time_insert = float(print_result.get("time_hours", 0))
        weight_insert = float(print_result.get("weight_kg", 0))
        time_ready_insert = float(print_result.get("time_ready", 0))
        materials_insert = print_result.get("materials", [])

        set_insert = calc_set_insert(quantity, mode.value)
        cost_set = set_insert.cost
        price_set = set_insert.price
        time_set = set_insert.time_hours
        time_ready_set = set_insert.time_ready

        cost_pack = 0.0
        price_pack = 0.0
        time_pack = 0.0
        time_ready_pack = 0.0
        weight_pack = 0.0
        materials_pack: List[Dict[str, Any]] = []
        if is_packing:
            pack_options = {"isPacking": ZIPLOCK_ACRYLIC}
            pack_size = [size[0], size[1], 5]
            pack_result = calc_packing(quantity, pack_size, pack_options, mode.value)
            cost_pack = pack_result.cost
            price_pack = pack_result.price
            time_pack = pack_result.time_hours
            time_ready_pack = pack_result.time_ready
            weight_pack = pack_result.weight_kg
            materials_pack = pack_result.materials

        margin = get_margin("marginMagnet") or get_margin("marginAcrylicKeychain")
        cost = cost_insert + cost_set + cost_blank + cost_pack
        price = (price_insert + price_set + price_blank + price_pack) * (1 + margin)

        time_hours = time_insert + time_set + time_pack
        time_ready = time_hours + max(time_ready_insert, time_ready_set, time_ready_pack)
        weight_kg = weight_insert + weight_blank + weight_pack

        materials: List[Dict[str, Any]] = [mat_blank] + materials_insert + materials_pack

        return {
            "cost": float(round(cost, 2)),
            "price": float(round(price, 2)),
            "unit_price": float(round(price, 2)) / max(1, quantity),
            "time_hours": float(round(time_hours, 2)),
            "time_ready": float(time_ready),
            "weight_kg": float(round(weight_kg, 3)),
            "materials": materials,
        }

    def _calc_laminated(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        """Ламинированные магниты: печать + ламинация + магнитный винил + резка."""
        from common.layout import layout_on_sheet

        quantity = int(params.get("quantity", 1))
        material_id = str(params.get("magnet_id", "") or "MagnetVinil04")
        width = float(params.get("width_mm", 0) or params.get("width", 90))
        height = float(params.get("height_mm", 0) or params.get("height", 54))
        lamination_id = str(params.get("lamination_id", "") or "").strip()
        is_packing = bool(params.get("is_packing", True))
        mode = ProductionMode(int(params.get("mode", 1)))

        if width <= 0 or height <= 0:
            raise ValueError("Для ламинированных магнитов укажите ширину и высоту")

        size = [width, height]
        color_str = "4+0"
        size_sheet = [320.0, 450.0]

        try:
            magnet_vinyl = get_material("hardsheet", material_id)
        except KeyError:
            raise ValueError(f"Магнитный винил не найден: {material_id!r}")

        layout = layout_on_sheet(size, size_sheet, [2, 2, 2, 2], 4)
        num_per_sheet = layout.get("num", 1) or 1
        num_sheets = math.ceil(quantity / num_per_sheet) if num_per_sheet > 0 else quantity

        print_calc = PrintSheetCalculator()
        print_params = {
            "quantity": quantity,
            "width": width,
            "height": height,
            "material_id": DEFAULT_PRINT_MATERIAL,
            "color": color_str,
            "lamination_id": lamination_id,
            "lamination_double_side": True,
            "mode": mode.value,
        }
        print_result = print_calc.calculate(print_params)
        cost_print = float(print_result.get("cost", 0))
        price_print = float(print_result.get("price", 0))
        time_print = float(print_result.get("time_hours", 0))
        time_ready_print = float(print_result.get("time_ready", 0))
        weight_print = float(print_result.get("weight_kg", 0))
        materials_print = print_result.get("materials", [])

        vinyl_sizes = magnet_vinyl.sizes or [[620, 0]]
        size_vinyl = list(vinyl_sizes[0]) if vinyl_sizes else [620, 0]
        sheet_w = size_vinyl[0]
        sheet_h = size_vinyl[1] if len(size_vinyl) > 1 and size_vinyl[1] > 0 else 450.0
        area_m2 = (sheet_w / 1000.0) * (sheet_h / 1000.0) * num_sheets
        cost_vinyl = float(magnet_vinyl.cost or 0) * area_m2
        price_vinyl = cost_vinyl * (1 + MARGIN_MATERIAL)

        cut_calc = CutGuillotineCalculator()
        cut_params = {
            "num_sheet": num_sheets,
            "width": width,
            "height": height,
            "sheet_width": size_sheet[0],
            "sheet_height": size_sheet[1],
            "material_id": material_id,
            "material_category": "hardsheet",
            "margins": [2, 2, 2, 2],
            "interval": 4,
            "mode": mode.value,
        }
        cut_result = cut_calc.calculate(cut_params)
        cost_cut = float(cut_result.get("cost", 0))
        price_cut = float(cut_result.get("price", 0))
        time_cut = float(cut_result.get("time_hours", 0))

        cost_pack = 0.0
        price_pack = 0.0
        time_pack = 0.0
        weight_pack = 0.0
        materials_pack: List[Dict[str, Any]] = []
        if is_packing:
            pack_options = {"isPacking": "ZipLock1015"}
            pack_size = [width, height, 1]
            pack_result = calc_packing(quantity, pack_size, pack_options, mode.value)
            cost_pack = pack_result.cost
            price_pack = pack_result.price
            time_pack = pack_result.time_hours
            weight_pack = pack_result.weight_kg
            materials_pack = pack_result.materials

        margin = get_margin("marginMagnet") or get_margin("marginBadge")
        cost = cost_print + cost_vinyl + cost_cut + cost_pack
        price = (price_print + price_vinyl + price_cut + price_pack) * (1 + margin)

        time_hours = time_print + time_cut + time_pack
        time_ready = time_hours + max(
            time_ready_print, float(BASE_TIME_READY[min(mode.value, len(BASE_TIME_READY) - 1)])
        )
        weight_kg = weight_print + weight_pack

        mat_vinyl = {
            "code": material_id,
            "name": magnet_vinyl.description,
            "title": magnet_vinyl.title,
            "quantity": round(area_m2, 4),
            "unit": "m2",
        }
        materials = [mat_vinyl] + materials_print + materials_pack

        return {
            "cost": float(math.ceil(cost)),
            "price": float(math.ceil(price)),
            "unit_price": float(math.ceil(price)) / max(1, quantity),
            "time_hours": math.ceil(time_hours * 100) / 100.0,
            "time_ready": time_ready,
            "weight_kg": round(weight_kg, 2),
            "materials": materials,
        }
