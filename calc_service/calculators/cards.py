"""
Калькулятор пластиковых карт.

Перенесено из js_legacy/calc/calcCards.js.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Mapping

import json5

from calculators.base import BaseCalculator, ProductionMode
from common.markups import MARGIN_MATERIAL, get_margin, get_time_ready

CARDS_JSON = Path(__file__).parent.parent / "data" / "equipment" / "cards.json"


def _load_cards_config() -> Dict[str, Any]:
    """Загрузить конфигурацию пластиковых карт из cards.json."""
    with open(CARDS_JSON, "r", encoding="utf-8") as f:
        data = json5.load(f)
    return data.get("PlasticCards", {})


def _find_cost_tier(cost_table: List[List[float]], n: int) -> float:
    """
    Найти цену за штуку по таблице [[порог, цена], ...].
    idx = findIndex(item => item[0] > n); if idx==-1 idx=len-1 else idx-=1
    """
    if not cost_table:
        return 0.0
    idx = -1
    for i, row in enumerate(cost_table):
        if row[0] > n:
            idx = i - 1
            break
    if idx == -1:
        idx = len(cost_table) - 1
    return float(cost_table[idx][1])


class CardsCalculator(BaseCalculator):
    """Пластиковые карты: белые, дизайнерские, с чипом."""

    slug = "cards"
    name = "Пластиковые карты"
    description = "Расчёт изготовления пластиковых карт с опциями ламинации и персонализации."

    def get_param_schema(self) -> Dict[str, Any]:
        config = _load_cards_config()
        cost_plastic = config.get("costPlastic", {})
        choices = [
            {"id": code, "title": raw.get("name", code)}
            for code, raw in cost_plastic.items()
            if code != "Default" and isinstance(raw, dict)
        ]
        cost_lamination = config.get("costLamination", {})
        lamination_choices = [
            {"id": k, "title": k}
            for k in cost_lamination
            if k != "Default" and isinstance(cost_lamination.get(k), (int, float))
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
                    "description": "Количество карт",
                    "validation": {"min": 1, "max": 100000},
                },
                {
                    "name": "material_id",
                    "type": "enum",
                    "required": True,
                    "title": "Тип карты",
                    "description": "Белые, дизайнерские, с чипом EM Marine или Mifare",
                    "choices": {"inline": choices},
                },
                {
                    "name": "lamination",
                    "type": "string",
                    "required": False,
                    "default": "",
                    "title": "Ламинация",
                    "description": "gloss, matte, touch или пусто",
                },
                {
                    "name": "is_number",
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "title": "Нумерация",
                },
                {
                    "name": "is_barcode",
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "title": "Штрихкод",
                },
                {
                    "name": "is_embossing_foil",
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "title": "Тиснение фольгой",
                },
                {
                    "name": "is_magnetic_stripe",
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "title": "Магнитная полоса HiCo",
                },
                {
                    "name": "is_embossing",
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "title": "Эмбоссинг",
                },
                {
                    "name": "is_signature_strip",
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "title": "Полоса для подписи",
                },
                {
                    "name": "is_scratch_panel",
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "title": "Скретч-панель",
                },
                {
                    "name": "mode",
                    "type": "integer",
                    "required": False,
                    "default": int(ProductionMode.STANDARD),
                    "title": "Режим",
                    "description": "0=эконом, 1=стандарт, 2=экспресс",
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
                "main": ["quantity", "material_id"],
                "options": [
                    "lamination",
                    "is_number",
                    "is_barcode",
                    "is_embossing_foil",
                    "is_magnetic_stripe",
                    "is_embossing",
                    "is_signature_strip",
                    "is_scratch_panel",
                ],
                "mode": ["mode"],
            },
        }

    def get_options(self) -> Dict[str, Any]:
        config = _load_cards_config()
        cost_plastic = config.get("costPlastic", {})
        materials = [
            {"code": code, "name": raw.get("name", code)}
            for code, raw in cost_plastic.items()
            if code != "Default" and isinstance(raw, dict)
        ]
        return {
            "materials": materials,
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
                    "quantity": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "Тираж, шт.",
                    },
                    "material_id": {
                        "type": "string",
                        "description": "Код типа карты: White, Design, ChipEMMarine, ChipMifare",
                    },
                    "lamination": {
                        "type": "string",
                        "description": "Ламинация: gloss, matte, touch или пусто",
                        "default": "",
                    },
                    "is_number": {"type": "boolean", "default": False},
                    "is_barcode": {"type": "boolean", "default": False},
                    "is_embossing_foil": {"type": "boolean", "default": False},
                    "is_magnetic_stripe": {"type": "boolean", "default": False},
                    "is_embossing": {"type": "boolean", "default": False},
                    "is_signature_strip": {"type": "boolean", "default": False},
                    "is_scratch_panel": {"type": "boolean", "default": False},
                    "mode": {
                        "type": "integer",
                        "enum": [0, 1, 2],
                        "default": 1,
                    },
                },
                "required": ["quantity", "material_id"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        config = _load_cards_config()
        tool = config
        cost_plastic = tool.get("costPlastic", {})
        default_card = cost_plastic.get("Default", {})

        quantity = int(params.get("quantity", 1))
        material_id = str(params.get("material_id", "") or "White")
        mode = int(params.get("mode", ProductionMode.STANDARD))

        if material_id not in cost_plastic:
            raise ValueError(f"Неизвестный тип карты: {material_id!r}")

        card = {**default_card, **cost_plastic[material_id]}
        cost_table = card.get("cost", [])
        if not cost_table:
            raise ValueError(f"Нет таблицы цен для карт {material_id!r}")

        cost_per_piece = _find_cost_tier(cost_table, quantity)
        cost_material = cost_per_piece * quantity

        weight_per_piece = float(card.get("weight", default_card.get("weight", 5.0)))
        weight_kg = weight_per_piece * quantity / 1000.0

        cost_options = 0.0
        cost_lamination = tool.get("costLamination", {})
        lamination = str(params.get("lamination", "") or "").strip().lower()
        if lamination and lamination in cost_lamination:
            cost_options += float(cost_lamination.get(lamination, 0))
        if params.get("is_number"):
            cost_options += float(tool.get("costNumber", 0))
        if params.get("is_barcode"):
            cost_options += float(tool.get("costBarcode", 0))
        if params.get("is_embossing_foil"):
            cost_options += float(tool.get("costEmbossingFoil", 0))
        if params.get("is_magnetic_stripe"):
            cost_options += float(tool.get("costMagneticStripeHiCo", 0))
        if params.get("is_embossing"):
            cost_options += float(tool.get("costEmbossing", 0))
        if params.get("is_signature_strip"):
            cost_options += float(tool.get("costSignatureStrip", 0))
        if params.get("is_scratch_panel"):
            cost_options += float(tool.get("costScratchPanel", 0))
        cost_options *= quantity

        cost_shipment = float(tool.get("costShipment", 500))

        cost = cost_material + cost_options + cost_shipment
        margin_cards = get_margin("marginCards")
        price = cost * (1 + MARGIN_MATERIAL + margin_cards)

        time_prepare = float(tool.get("timePrepare", 0.5))
        base_time_ready = tool.get("baseTimeReady")
        if base_time_ready:
            idx = min(max(0, math.ceil(mode)), len(base_time_ready) - 1)
            time_ready = float(base_time_ready[idx])
        else:
            time_ready = get_time_ready("baseTimeReady")[min(mode, 2)]

        card_name = card.get("name", material_id)
        card_size = card.get("size", default_card.get("size", [86, 54]))

        materials: List[Dict[str, Any]] = [
            {
                "code": material_id,
                "name": card_name,
                "title": card_name,
                "quantity": quantity,
                "unit": "шт",
            }
        ]

        return {
            "cost": float(math.ceil(cost)),
            "price": float(math.ceil(price)),
            "unit_price": float(math.ceil(price)) / float(quantity),
            "time_hours": float(time_prepare),
            "time_ready": float(time_ready),
            "weight_kg": float(round(weight_kg, 3)),
            "materials": materials,
        }
