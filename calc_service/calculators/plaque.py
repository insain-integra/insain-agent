"""
Калькулятор НАГРАДНЫХ ПЛАКЕТОК.

Мигрировано из js_legacy/calc/calcTablets.js (функция calcPlaque, строки 582–661).
Плакетка = деревянная основа (дощечка) + металлическая пластина с нанесением
(УФ-печать / лазерная гравировка / сублимация).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

import json5

from calculators.base import BaseCalculator, ProductionMode
from calculators.tablets import TabletsCalculator
from common.markups import BASE_TIME_READY, MARGIN_MATERIAL, get_margin
from materials import plaque as plaque_catalog, hardsheet as hardsheet_catalog

# Путь к файлу данных плакеток (для загрузки sizePlate / weight — полей,
# отсутствующих в стандартной MaterialSpec)
_PLAQUE_DATA_PATH = Path(__file__).parent.parent / "data" / "materials" / "plaque.json"
_RAW_PLAQUE_DATA: Optional[Dict[str, Dict[str, Any]]] = None


def _load_raw_plaque_data() -> Dict[str, Dict[str, Any]]:
    """Загрузить сырые данные плакеток из JSON (с полем sizePlate)."""
    global _RAW_PLAQUE_DATA
    if _RAW_PLAQUE_DATA is None:
        with open(_PLAQUE_DATA_PATH, "r", encoding="utf-8") as f:
            raw = json5.load(f)
        flat: Dict[str, Dict[str, Any]] = {}
        for group_data in raw.values():
            if isinstance(group_data, dict):
                for code, spec in group_data.items():
                    if code == "Default" or not isinstance(spec, dict):
                        continue
                    flat[code] = spec
        _RAW_PLAQUE_DATA = flat
    return _RAW_PLAQUE_DATA


def _get_plaque_extra(plaque_id: str) -> Dict[str, Any]:
    """
    Получить дополнительные поля плакетки (sizePlate, weight),
    которых нет в MaterialSpec.
    """
    data = _load_raw_plaque_data()
    if plaque_id not in data:
        raise KeyError(f"Неизвестная плакетка: {plaque_id!r}")
    spec = data[plaque_id]
    size_plate = spec.get("sizePlate")
    if not size_plate or len(size_plate) < 2:
        raise ValueError(f"sizePlate не задан для плакетки {plaque_id!r}")
    return {
        "size_plate": [float(size_plate[0]), float(size_plate[1])],
        "weight": float(spec.get("weight", 0)),
    }


# Маппинг способа нанесения → print_method для TabletsCalculator
_APPLICATION_TO_PRINT_METHOD: Dict[str, str] = {
    "noApplication": "none",
    "isUVPrint": "uv",
    "isGrave": "laser",
    "isSublimation": "none",
}

APPLICATION_CHOICES = [
    {"id": "noApplication", "title": "Без нанесения"},
    {"id": "isUVPrint", "title": "УФ-печать"},
    {"id": "isGrave", "title": "Лазерная гравировка"},
    {"id": "isSublimation", "title": "Сублимация"},
]


class PlaqueCalculator(BaseCalculator):
    """Наградные плакетки: деревянная основа + пластина с нанесением."""

    slug = "plaque"
    name = "Наградные плакетки"
    description = (
        "Расчёт стоимости наградных плакеток: "
        "основа + нанесение (УФ-печать/гравировка/сублимация)."
    )
    def get_options(self) -> Dict[str, Any]:
        plaques = plaque_catalog.list_for_frontend()
        materials = hardsheet_catalog.list_for_frontend()
        return {
            "plaques": plaques,
            "materials": materials[:50],
            "applications": APPLICATION_CHOICES,
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
                    "quantity": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "Тираж, шт.",
                    },
                    "plaque_id": {
                        "type": "string",
                        "description": "Код заготовки плакетки (Plaque2330, Plaque2025, Plaque1520)",
                    },
                    "material_id": {
                        "type": "string",
                        "description": "Код материала пластины (hardsheet)",
                    },
                    "application": {
                        "type": "string",
                        "enum": ["noApplication", "isUVPrint", "isGrave", "isSublimation"],
                        "default": "isUVPrint",
                        "description": "Способ нанесения на пластину",
                    },
                    "mode": {
                        "type": "integer",
                        "enum": [0, 1, 2],
                        "default": 1,
                    },
                },
                "required": ["quantity", "plaque_id", "material_id"],
            },
        }

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
                    "name": "plaque_id",
                    "type": "enum",
                    "required": True,
                    "title": "Заготовка плакетки",
                    "choices": {"source": "materials:plaque"},
                },
                {
                    "name": "material_id",
                    "type": "enum_cascading",
                    "required": True,
                    "title": "Материал пластины",
                    "choices": {"source": "materials:hardsheet"},
                },
                {
                    "name": "application",
                    "type": "enum",
                    "required": False,
                    "default": "isUVPrint",
                    "title": "Нанесение",
                    "choices": {"inline": APPLICATION_CHOICES},
                },
                {
                    "name": "mode",
                    "type": "enum",
                    "required": False,
                    "default": 1,
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
                "main": ["quantity", "plaque_id"],
                "material": ["material_id"],
                "processing": ["application"],
                "mode": ["mode"],
            },
        }

    def get_llm_prompt(self) -> str:
        return ""

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        n = int(params.get("quantity", 1))
        plaque_id = str(params.get("plaque_id", "")).strip()
        material_id = str(params.get("material_id", "")).strip()
        application = str(params.get("application", "isUVPrint") or "isUVPrint").strip()
        mode = ProductionMode(int(params.get("mode", 1)))

        if not plaque_id:
            raise ValueError("plaque_id обязателен")
        if not material_id:
            raise ValueError("material_id обязателен")
        if application not in _APPLICATION_TO_PRINT_METHOD:
            raise ValueError(f"Неизвестный способ нанесения: {application!r}")

        # --- 1. Стоимость основы (деревянная дощечка) ---
        plaque = plaque_catalog.get(plaque_id)
        extra = _get_plaque_extra(plaque_id)
        size_plate: List[float] = extra["size_plate"]

        cost_plaque = float(plaque.cost or 0) * n
        price_plaque = cost_plaque * (1 + MARGIN_MATERIAL)
        weight_plaque = extra["weight"] * n

        materials_out: List[Dict[str, Any]] = [
            {
                "code": plaque_id,
                "name": plaque.description,
                "title": plaque.title,
                "quantity": n,
                "unit": "шт",
            }
        ]

        # --- 2. Расчёт пластины через TabletsCalculator ---
        cost_plate = 0.0
        price_plate = 0.0
        time_plate = 0.0
        time_ready_plate = 0.0
        weight_plate = 0.0

        if application != "noApplication":
            print_method = _APPLICATION_TO_PRINT_METHOD[application]
            tablets_calc = TabletsCalculator()
            tablets_params: Dict[str, Any] = {
                "quantity": n,
                "width": size_plate[0],
                "height": size_plate[1],
                "material_id": material_id,
                "print_method": print_method,
                "mode": mode.value,
            }
            plate_result = tablets_calc.calculate(tablets_params)

            cost_plate = float(plate_result.get("cost", 0))
            price_plate = float(plate_result.get("price", 0))
            time_plate = float(plate_result.get("time_hours", 0))
            time_ready_plate = float(plate_result.get("time_ready", 0))
            weight_plate = float(plate_result.get("weight_kg", 0))
            materials_out.extend(plate_result.get("materials", []))

        # --- 3. Итог ---
        cost_total = cost_plaque + cost_plate
        price_total = price_plaque + price_plate
        margin_plaque = get_margin("marginPlaque")
        price_total = math.ceil(price_total * (1 + margin_plaque))

        time_hours = math.ceil(time_plate * 100) / 100.0

        # JS: result.timeReady = result.time + Math.max(costPlate.timeReady, costPlaque.timeReady, costSet.timeReady)
        time_ready = time_hours + max(time_ready_plate, 0)
        if time_ready <= 0:
            idx = max(0, min(len(BASE_TIME_READY) - 1, mode.value))
            time_ready = float(BASE_TIME_READY[idx])

        weight_kg = math.ceil((weight_plaque + weight_plate) * 100) / 100.0

        return {
            "cost": float(cost_total),
            "price": int(price_total),
            "unit_price": round(float(price_total) / max(1, n), 2),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": weight_kg,
            "materials": materials_out,
        }
