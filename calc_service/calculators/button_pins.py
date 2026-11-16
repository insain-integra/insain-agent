"""
Калькулятор закатных значков.

Обёртка над common.process_tools.calc_button_pins: формулы закатки, вставки,
наценки marginButtonPins и ветка Амалит живут там, здесь только вход API.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping

from calculators.base import BaseCalculator, ProductionMode
from common.process_tools import calc_button_pins
from materials import pins as pins_catalog

PIN_CODES = ("D25", "D38", "D56", "D78")


class ButtonPinsCalculator(BaseCalculator):
    """Закатные значки: своя закатка до порога Амалит, дальше заказ у подрядчика."""

    slug = "button_pins"
    name = "Закатные значки"
    description = "Расчёт закатных значков: заготовка, вставка, закатка и упаковка."

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
                    "validation": {"min": 1},
                },
                {
                    "name": "pin_id",
                    "type": "string",
                    "required": True,
                    "title": "Размер",
                    "description": "D25, D38, D56 или D78",
                },
                {
                    "name": "is_packing",
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "title": "Упаковка",
                    "description": "true или пустая строка — автоподбор пакета, строка — код пакета",
                },
                {
                    "name": "mode",
                    "type": "integer",
                    "required": False,
                    "default": int(ProductionMode.STANDARD),
                    "title": "Режим",
                },
            ],
            "param_groups": {
                "main": ["quantity", "pin_id"],
                "options": ["is_packing"],
                "mode": ["mode"],
            },
        }

    def get_options(self) -> Dict[str, Any]:
        pins = []
        for spec in pins_catalog.get_group("ButtonPins"):
            if spec.code not in PIN_CODES:
                continue
            pins.append({
                "code": spec.code,
                "name": spec.title,
                "title": spec.title,
            })
        return {
            "pins": pins,
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
                    "pin_id": {
                        "type": "string",
                        "enum": list(PIN_CODES),
                        "description": "Размер значка: D25, D38, D56, D78",
                    },
                    "is_packing": {
                        "type": "boolean",
                        "default": False,
                        "description": "Упаковка. true — автоподбор, строка — код пакета",
                    },
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["quantity", "pin_id"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        try:
            n = int(params.get("quantity", 1))
        except (TypeError, ValueError):
            raise ValueError("Тираж должен быть целым числом") from None
        if n < 1:
            raise ValueError("Тираж должен быть не меньше 1")

        pin_id = str(params.get("pin_id") or params.get("pinID") or "").strip()
        if pin_id not in PIN_CODES:
            raise ValueError("Укажите размер значка: pin_id (D25, D38, D56 или D78)")

        try:
            mode = int(params.get("mode", ProductionMode.STANDARD))
        except (TypeError, ValueError):
            raise ValueError("Неизвестный режим производства") from None
        if mode not in (0, 1, 2):
            raise ValueError("Неизвестный режим производства")

        options: Dict[str, Any] = {}
        if "is_packing" in params or "isPacking" in params:
            raw_pack = params["is_packing"] if "is_packing" in params else params.get("isPacking")
            if raw_pack is False or raw_pack is None:
                pass
            elif raw_pack is True:
                options["isPacking"] = ""
            else:
                options["isPacking"] = raw_pack

        result = calc_button_pins(n, pin_id, options, mode)
        price = float(result.price)
        return {
            "cost": float(result.cost),
            "price": price,
            "unit_price": price / n,
            "time_hours": float(result.time_hours),
            "time_ready": float(result.time_ready),
            "weight_kg": float(result.weight_kg),
            "materials": result.materials,
        }
