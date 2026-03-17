"""
Калькулятор РОЛЛАПОВ (роллерных стендов).

Мигрировано из js_legacy/calc/calcRollup.js.
Роллап = стенд (presswall Rollup) + печать баннера на рулоне + доставка.
"""

from __future__ import annotations

import json5
import math
from pathlib import Path
from typing import Any, Dict, List, Mapping

from calculators.base import BaseCalculator, ProductionMode
from calculators.print_roll import PrintRollCalculator
from common.markups import COST_OPERATOR, MARGIN_MATERIAL, MARGIN_OPERATION, get_margin
from materials import presswall as presswall_catalog
from materials import roll as roll_catalog
from common.process_tools import calc_shipment

DEFAULT_PRINTER = "TechnojetXR720"
ROLLUP_BASE_TIME_READY = [40, 24, 8]  # как в JS calcRollup
_PRESSWALL_PATH = Path(__file__).parent.parent / "data" / "materials" / "presswall.json"


def _get_rollup_raw(rollup_id: str) -> Dict[str, Any]:
    """Получить сырые данные роллапа (sizeBanner, size, cost, weight) из presswall.json."""
    with open(_PRESSWALL_PATH, "r", encoding="utf-8") as f:
        data = json5.load(f)
    rollup_group = data.get("Rollup", {})
    default = rollup_group.get("Default", {}) or {}
    raw = rollup_group.get(rollup_id)
    if not raw:
        raise KeyError(f"Роллап не найден: {rollup_id!r}")
    merged = dict(default)
    merged.update(raw)
    return merged


class RollupCalculator(BaseCalculator):
    """Роллапы: стенд + печать баннера + доставка."""

    slug = "rollup"
    name = "Роллапы"
    description = (
        "Расчёт роллапов (роллерных стендов): стоимость стенда, "
        "печать баннера на рулонном материале, доставка."
    )

    def get_param_schema(self) -> Dict[str, Any]:
        rollups = self._list_rollups()
        return {
            "slug": self.slug,
            "title": self.name,
            "params": [
                {
                    "name": "quantity",
                    "type": "integer",
                    "required": True,
                    "title": "Количество",
                    "description": "Количество роллапов",
                    "validation": {"min": 1, "max": 100},
                },
                {
                    "name": "rollup_id",
                    "type": "enum",
                    "required": True,
                    "title": "Тип роллапа",
                    "description": "Модель стенда",
                    "choices": {"inline": rollups},
                },
                {
                    "name": "material_id",
                    "type": "enum_cascading",
                    "required": False,
                    "title": "Материал баннера",
                    "description": "Рулонный материал для печати (пусто — без печати)",
                    "choices": {"source": "materials:roll"},
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
                "main": ["quantity", "rollup_id"],
                "material": ["material_id"],
                "mode": ["mode"],
            },
        }

    def _list_rollups(self) -> List[Dict[str, Any]]:
        """Список роллапов из группы Rollup."""
        try:
            group = presswall_catalog.get_group("Rollup")
        except Exception:
            return []
        return [
            {"id": m.code, "title": m.title, "description": m.description}
            for m in group
        ]

    def get_options(self) -> Dict[str, Any]:
        materials = roll_catalog.list_for_frontend()
        rollups = self._list_rollups()
        return {
            "materials": materials[:40],
            "rollups": rollups,
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
                    "quantity": {"type": "integer", "minimum": 1, "description": "Количество роллапов"},
                    "rollup_id": {"type": "string", "description": "Код типа роллапа (Rollup_econom_85 и т.д.)"},
                    "material_id": {"type": "string", "description": "Код материала баннера (roll), пусто — без печати"},
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["quantity", "rollup_id"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        n = int(params.get("quantity", 1))
        rollup_id = str(params.get("rollup_id", "") or "").strip()
        material_id = str(params.get("material_id", "") or "").strip()
        mode = ProductionMode(int(params.get("mode", 1)))

        if n < 1 or not rollup_id:
            return self._empty_result(mode)

        try:
            rollup_raw = _get_rollup_raw(rollup_id)
        except (KeyError, FileNotFoundError):
            return self._empty_result(mode)

        rollup_cost = float(rollup_raw.get("cost", 0))
        rollup_weight = float(rollup_raw.get("weight", 0))
        size_banner = rollup_raw.get("sizeBanner", [850, 2000])
        size_ship = rollup_raw.get("size", [880, 100, 100])

        if isinstance(size_banner[0], (list, tuple)):
            size_banner = size_banner[0]
        size_banner = [float(size_banner[0]), float(size_banner[1])]
        if len(size_ship) < 3:
            size_ship = list(size_ship) + [100] * (3 - len(size_ship))
        size_ship = [float(size_ship[0]), float(size_ship[1]), float(size_ship[2])]

        cost_materials = n * rollup_cost
        weight_kg = n * rollup_weight

        materials_out: List[Dict[str, Any]] = [{
            "code": rollup_id,
            "name": rollup_raw.get("description", rollup_id),
            "title": rollup_raw.get("title", rollup_id),
            "quantity": n,
            "unit": "шт",
        }]

        cost_banner = 0.0
        price_banner = 0.0
        time_banner = 0.0
        time_ready_banner = 0.0
        weight_banner = 0.0

        cost_install = 0.0
        price_install = 0.0
        time_install = 0.5

        if material_id:
            print_calc = PrintRollCalculator()
            try:
                banner_result = print_calc.calculate({
                    "quantity": n,
                    "width": size_banner[0],
                    "height": size_banner[1],
                    "material_id": material_id,
                    "printer_code": DEFAULT_PRINTER,
                    "is_joining": True,
                    "mode": mode.value,
                })
                cost_banner = float(banner_result.get("cost", 0))
                price_banner = float(banner_result.get("price", 0))
                time_banner = float(banner_result.get("time_hours", 0))
                time_ready_banner = float(banner_result.get("time_ready", 0))
                weight_banner = float(banner_result.get("weight_kg", 0))
                for m in banner_result.get("materials", []):
                    materials_out.append({
                        "code": m.get("code", ""),
                        "name": m.get("name", ""),
                        "title": m.get("title", ""),
                        "quantity": m.get("quantity", 0),
                        "unit": m.get("unit", "м"),
                    })
            except (KeyError, ValueError):
                pass

            cost_install = time_install * COST_OPERATOR
            price_install = cost_install * (1 + MARGIN_OPERATION)

        cost_ship = calc_shipment(n, size_ship, rollup_weight, "Own")

        cost = cost_install + cost_banner + cost_ship.cost + cost_materials
        margin_rollup = get_margin("marginRollup")
        price = (
            (price_install + price_banner + cost_ship.price) * (1 + margin_rollup)
            + cost_materials * (1 + MARGIN_MATERIAL + margin_rollup)
        )
        price = math.ceil(price)

        time_hours = math.ceil((time_install + time_banner) * 100) / 100.0
        base_ready = ROLLUP_BASE_TIME_READY[min(mode.value, len(ROLLUP_BASE_TIME_READY) - 1)]
        time_ready = time_hours + max(base_ready, time_ready_banner)

        weight_kg += weight_banner

        return {
            "cost": float(cost),
            "price": int(price),
            "unit_price": float(price) / max(1, n),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": weight_kg,
            "materials": materials_out,
        }

    def _empty_result(self, mode: ProductionMode) -> Dict[str, Any]:
        base_ready = ROLLUP_BASE_TIME_READY[min(mode.value, len(ROLLUP_BASE_TIME_READY) - 1)]
        return {
            "cost": 0.0,
            "price": 0,
            "unit_price": 0.0,
            "time_hours": 0.0,
            "time_ready": float(base_ready),
            "weight_kg": 0.0,
            "materials": [],
        }
