"""
Калькулятор акриловых брелоков.

Перенесено из js_legacy/calc/calcAcrylicKeychain.js.
Комбинирует: заготовка брелока + печать вставки (стикер) + установка вставки + упаковка.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping

from calculators.base import BaseCalculator, ProductionMode
from calculators.sticker import StickerCalculator
from common.markups import MARGIN_MATERIAL, MARGIN_OPERATION, get_margin
from common.process_tools import calc_packing, calc_set_insert


class KeychainCalculator(BaseCalculator):
    """Акриловые брелоки с печатью вставки."""

    slug = "keychain"
    name = "Брелоки"
    description = "Расчёт акриловых брелоков с печатью бумажной вставки."

    def get_param_schema(self) -> Dict[str, Any]:
        from materials import keychain as keychain_catalog

        keychains = keychain_catalog.list_for_frontend()
        choices = [
            {"id": m["code"], "title": m.get("title", m.get("name", m["code"]))}
            for m in keychains
        ]
        return {
            "slug": self.slug,
            "title": self.name,
            "params": [
                {
                    "name": "quantity",
                    "type": "integer",
                    "required": True,
                    "title": "Тираж",
                    "description": "Количество брелоков",
                    "validation": {"min": 1, "max": 10000},
                },
                {
                    "name": "keychain_id",
                    "type": "enum",
                    "required": True,
                    "title": "Заготовка",
                    "description": "Тип акриловой заготовки",
                    "choices": {"inline": choices},
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
                    "name": "is_packing",
                    "type": "boolean",
                    "required": False,
                    "default": True,
                    "title": "Упаковка",
                    "description": "Упаковка в зиплок",
                },
                {
                    "name": "mode",
                    "type": "integer",
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
                "main": ["quantity", "keychain_id"],
                "options": ["color", "is_packing"],
                "mode": ["mode"],
            },
        }

    def get_options(self) -> Dict[str, Any]:
        from materials import keychain as keychain_catalog

        return {
            "keychains": keychain_catalog.list_for_frontend(),
            "modes": [
                {"value": 0, "label": "Экономичный"},
                {"value": 1, "label": "Стандартный"},
                {"value": 2, "label": "Экспресс"},
            ],
        }

    def get_tool_schema(self) -> Dict[str, Any]:
        return {
            "name": self.slug,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "quantity": {"type": "integer", "minimum": 1, "description": "Тираж, шт."},
                    "keychain_id": {
                        "type": "string",
                        "description": "Код заготовки: KeychainAcrylic3939, KeychainAcrylic3558 и т.д.",
                    },
                    "color": {
                        "type": "integer",
                        "description": "1 — односторонняя печать, 2 — двухсторонняя",
                        "default": 1,
                    },
                    "is_packing": {"type": "boolean", "default": True},
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["quantity", "keychain_id"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        from materials import keychain as keychain_catalog

        quantity = int(params.get("quantity", 1))
        keychain_id = str(params.get("keychain_id", "") or "KeychainAcrylic3939")
        color = int(params.get("color", 1))
        is_packing = bool(params.get("is_packing", True))
        mode = int(params.get("mode", ProductionMode.STANDARD))

        from common.process_tools import _get_raw_material

        keychain = keychain_catalog.get(keychain_id)
        try:
            raw = _get_raw_material("keychain", keychain_id)
        except KeyError:
            raw = {}
        size = list(raw.get("size", keychain.sizes[0] if keychain.sizes else [39, 39]))
        size_insert = list(raw.get("sizeInsert", size))
        size_item = min(size_insert[0], size_insert[1])

        color_str = "4+4" if color >= 2 else "4+0"

        # 1. Заготовка брелока
        cost_blank = float(keychain.cost or 0) * quantity
        price_blank = cost_blank * (1 + MARGIN_MATERIAL)
        weight_blank = float(raw.get("weight", 10)) * quantity / 1000

        mat_blank = {
            "code": keychain_id,
            "name": keychain.description,
            "title": keychain.title,
            "quantity": quantity,
            "unit": "шт",
        }

        # 2. Печать вставки (стикер)
        sticker_calc = StickerCalculator()
        sticker_params = {
            "quantity": quantity,
            "width": size_insert[0],
            "height": size_insert[1],
            "size_item": size_item,
            "density": 0,
            "difficulty": 1,
            "material_id": "PaperCoated115M",
            "color": color_str,
            "printer_code": "KMBizhubC220",
            "mode": mode,
        }
        sticker_result = sticker_calc.calculate(sticker_params)

        cost_insert = float(sticker_result.get("cost", 0))
        price_insert = float(sticker_result.get("price", 0))
        time_insert = float(sticker_result.get("time_hours", 0))
        weight_insert = float(sticker_result.get("weight_kg", 0))
        time_ready_insert = float(sticker_result.get("time_ready", 0))
        materials_insert = sticker_result.get("materials", [])

        # 3. Установка вставки в брелок
        set_insert = calc_set_insert(quantity, mode)
        cost_set = set_insert.cost
        price_set = set_insert.price
        time_set = set_insert.time_hours
        time_ready_set = set_insert.time_ready

        # 4. Упаковка
        materials_pack: List[Dict[str, Any]] = []
        cost_pack = 0.0
        price_pack = 0.0
        time_pack = 0.0
        time_ready_pack = 0.0
        weight_pack = 0.0
        if is_packing:
            pack_options = {"isPacking": "ZipLockAcrylic"}
            pack_size = [size[0], size[1], 5]
            pack_result = calc_packing(quantity, pack_size, pack_options, mode)
            cost_pack = pack_result.cost
            price_pack = pack_result.price
            time_pack = pack_result.time_hours
            time_ready_pack = pack_result.time_ready
            weight_pack = pack_result.weight_kg
            materials_pack = pack_result.materials

        # Итог
        cost = cost_insert + cost_set + cost_blank + cost_pack
        margin_keychain = get_margin("marginAcrylicKeychain")
        price = (
            price_insert + price_set + price_blank + price_pack
        ) * (1 + margin_keychain)

        time_hours = time_insert + time_set + time_pack
        time_ready = time_hours + max(
            time_ready_insert,
            time_ready_set,
            time_ready_pack,
        )
        weight_kg = weight_insert + weight_blank + weight_pack

        materials: List[Dict[str, Any]] = [mat_blank] + materials_insert + materials_pack

        return {
            "cost": float(round(cost, 2)),
            "price": float(round(price, 2)),
            "unit_price": float(round(price, 2)) / float(quantity),
            "time_hours": float(round(time_hours, 2)),
            "time_ready": float(time_ready),
            "weight_kg": float(round(weight_kg, 3)),
            "materials": materials,
        }
