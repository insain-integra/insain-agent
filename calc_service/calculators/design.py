"""
Калькулятор ДИЗАЙН-УСЛУГ.

Мигрировано из js_legacy/calc/calcDesign.js.
Расчёт стоимости дизайна и вёрстки по времени: подготовка + работа в зависимости от сложности.
Данные из data/equipment/design.json.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Mapping

import json5

from calculators.base import BaseCalculator, ProductionMode
from common.markups import BASE_TIME_READY, COST_OPERATOR, MARGIN_OPERATION, get_margin

DESIGN_JSON = Path(__file__).parent.parent / "data" / "equipment" / "design.json"


def _load_design_data() -> Dict[str, Any]:
    """Загрузить данные дизайна из design.json."""
    with open(DESIGN_JSON, "r", encoding="utf-8") as f:
        return json5.load(f)


def _get_design_tool(design_id: str) -> Dict[str, Any]:
    """Получить конфиг дизайна по коду (timeProcess, timePrepare, costOperator)."""
    data = _load_design_data()
    for code, raw in data.items():
        if not isinstance(raw, dict):
            continue
        if code == design_id:
            return raw
    raise KeyError(f"Тип дизайна {design_id!r} не найден в design.json")


class DesignCalculator(BaseCalculator):
    """Дизайн и вёрстка: расчёт по времени работы дизайнера."""

    slug = "design"
    name = "Дизайн-услуги"
    description = "Расчёт стоимости дизайна и вёрстки: время подготовки + работа по сложности."

    def get_options(self) -> Dict[str, Any]:
        data = _load_design_data()
        design_types = [
            {"code": code, "name": raw.get("name", code)}
            for code, raw in data.items()
            if isinstance(raw, dict)
        ]
        return {
            "design_types": design_types,
            "difficulties": [
                {"value": 0, "label": "Только проверка"},
                {"value": 1, "label": "Внесение текстовых изменений"},
                {"value": 2, "label": "Вёрстка на базе готовых"},
                {"value": 3, "label": "Разработка дизайна"},
            ],
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
                    "quantity": {"type": "integer", "minimum": 1, "description": "Количество изделий/макетов"},
                    "design_id": {"type": "string", "description": "Тип дизайна (DesignCard)"},
                    "difficulty": {"type": "integer", "enum": [0, 1, 2, 3], "default": 1,
                                  "description": "0=проверка, 1=текст, 2=вёрстка, 3=разработка"},
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["quantity", "design_id"],
            },
        }

    def get_param_schema(self) -> Dict[str, Any]:
        return {
            "slug": self.slug,
            "title": self.name,
            "params": [
                {"name": "quantity", "type": "integer", "required": True, "title": "Количество", "validation": {"min": 1}},
                {"name": "design_id", "type": "enum", "required": True, "title": "Тип дизайна",
                 "choices": {"inline": [{"id": "DesignCard", "title": "Дизайн визитных карт"}]}},
                {"name": "difficulty", "type": "enum", "required": False, "default": 1, "title": "Сложность",
                 "choices": {"inline": [
                     {"id": 0, "title": "Только проверка"},
                     {"id": 1, "title": "Внесение текстовых изменений"},
                     {"id": 2, "title": "Вёрстка на базе готовых"},
                     {"id": 3, "title": "Разработка дизайна"},
                 ]}},
                {"name": "mode", "type": "enum", "required": False, "default": 1, "title": "Режим",
                 "choices": {"inline": [{"id": 0, "title": "Эконом"}, {"id": 1, "title": "Стандарт"}, {"id": 2, "title": "Экспресс"}]}},
            ],
            "param_groups": {"main": ["quantity", "design_id"], "options": ["difficulty"], "mode": ["mode"]},
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        n = int(params.get("quantity", 1))
        design_id = str(params.get("design_id", "") or "DesignCard").strip() or "DesignCard"
        difficulty = int(params.get("difficulty", 1))
        mode = ProductionMode(int(params.get("mode", 1)))

        tool = _get_design_tool(design_id)

        time_prepare = float(tool.get("timePrepare", 0.05))
        time_process_arr = tool.get("timeProcess", [0.25, 1, 2])
        cost_operator = float(tool.get("costOperator", 0.0)) or COST_OPERATOR
        base_time_ready = tool.get("baseTimeReady") or BASE_TIME_READY
        idx = max(0, min(len(base_time_ready) - 1, math.ceil(mode.value)))
        ready_hours = float(base_time_ready[idx])

        # Время: подготовка * режим + время работы по сложности
        time_prepare_total = n * time_prepare * max(1, mode.value)
        time_process = time_prepare_total
        if difficulty > 0 and difficulty <= len(time_process_arr):
            time_process += n * time_process_arr[difficulty - 1]

        time_operator = time_process
        cost_operator_total = time_operator * cost_operator

        cost = cost_operator_total
        price = cost * (1 + MARGIN_OPERATION + get_margin("marginDesign"))
        time_hours = math.ceil(time_operator * 100) / 100
        time_ready = time_hours + ready_hours

        return {
            "cost": math.ceil(cost),
            "price": math.ceil(price),
            "unit_price": math.ceil(price) / max(1, n),
            "time_hours": time_hours,
            "time_ready": time_ready,
            "weight_kg": 0.0,
            "materials": [],
        }
