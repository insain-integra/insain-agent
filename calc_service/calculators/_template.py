"""
Шаблон калькулятора.

Использование:
    1. Скопируйте этот файл в calculators/имя_калькулятора.py.
    2. Переименуйте класс TemplateCalculator.
    3. Заполните логику в методе calculate().
    4. Зарегистрируйте калькулятор в calculators/__init__.py.

См. также:
    - CLAUDE.md (обязательные поля ответа калькулятора)
    - docs/data-formats.md (форматы JSON-справочников)
    - docs/migration-guide.md (чек-листы по миграции JS-калькуляторов)
"""

from __future__ import annotations

from typing import Any, Dict, Mapping

from calculators.base import BaseCalculator, ProductionMode
from common.helpers import calc_weight, find_in_table
from common.holidays import add_working_hours, next_working_day
from common.layout import layout_on_roll, layout_on_sheet
from common.markups import (
    BASE_TIME_READY,
    MARGIN_MIN,
    MARGIN_MATERIAL,
    MARGIN_OPERATION,
    get_margin,
)
from materials.loader import load_catalog
from equipment.loader import load_generic_catalog, load_laser_catalog


class TemplateCalculator(BaseCalculator):
    """
    Пример калькулятора.

    Этот класс показывает:
      - как импортировать материалы и оборудование;
      - как считать раскрой на лист / рулон;
      - как учитывать брак по таблице;
      - как считать время (time_hours, time_ready);
      - как применять наценки через get_margin() и MARGIN_MIN;
      - как формировать ответ API в требуемом формате.
    """

    slug = "template"
    name = "Шаблон калькулятора"
    description = "Пример структуры калькулятора, использующего справочники и наценки."

    def get_options(self) -> Dict[str, Any]:
        """
        Опции для фронтенда / бота.

        Обычно сюда входят:
          - списки материалов;
          - режимы качества / скорости (ProductionMode);
          - предустановленные размеры и тиражи.

        Возвращаем простой пример структуры.
        """
        # Пример: грузим каталог листовых материалов
        # catalog = load_catalog("hardsheet.json")
        # materials = catalog.list_for_frontend()

        return {
            "modes": [
                {"value": ProductionMode.ECONOMY, "label": "Экономичный"},
                {"value": ProductionMode.STANDARD, "label": "Стандартный"},
                {"value": ProductionMode.EXPRESS, "label": "Экспресс"},
            ],
            # "materials": materials,
        }

    def get_tool_schema(self) -> Dict[str, Any]:
        """
        Описание входных параметров для LLM (tools/function calling).

        Это просто пример структуры, адаптируйте под конкретный калькулятор.
        """
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
                    "width": {
                        "type": "number",
                        "minimum": 1,
                        "description": "Ширина изделия, мм.",
                    },
                    "height": {
                        "type": "number",
                        "minimum": 1,
                        "description": "Высота изделия, мм.",
                    },
                    "mode": {
                        "type": "integer",
                        "enum": [
                            ProductionMode.ECONOMY,
                            ProductionMode.STANDARD,
                            ProductionMode.EXPRESS,
                        ],
                        "description": "Режим производства (0 — эконом, 1 — стандарт, 2 — экспресс).",
                    },
                },
                "required": ["quantity", "width", "height"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        """
        Основной расчёт.

        Порядок действий (общий шаблон):

          1. Прочитать входные параметры.
             quantity = int(params.get("quantity", 1))
             size = [width, height]  # width, height — мм (params "width", "height")
             mode = ProductionMode(params.get("mode", ProductionMode.STANDARD))

          2. Выбрать материалы и оборудование:
             - catalog = load_catalog("hardsheet.json")
             - material = catalog.get("PVC3")
             - equip_catalog = load_laser_catalog() или load_generic_catalog("printer.json")
             - equipment = equip_catalog.get("Qualitech11G1290")

          3. Посчитать раскладку:
             - layout = layout_on_sheet(item_size=size, sheet_size=material.sizes[0])
             - или layout_on_roll(quantity, size, [roll_width, 0])

          4. Посчитать расход материала и вес:
             - num_sheets = math.ceil(quantity / layout["num"])
             - weight_kg = calc_weight(... параметры из MaterialSpec ...)

          5. Посчитать брак по таблице дефектов оборудования:
             - defect_rate = equipment.get_defect_rate(quantity)
             - quantity_with_defects = math.ceil(quantity * (1 + defect_rate))

          6. Посчитать время:
             - time_process = ... (например, длина / скорость)
             - time_operator = ... (с учётом подготовки и загрузки)
             - time_hours = time_process  (или другая метрика)
             - time_ready = add_working_hours(start_date, hours, hours_per_day=8.0)
               (в калькуляторах обычно время_ready считают в рабочих часах, без даты,
                поэтому достаточно time_hours + equipment.get_time_ready(mode)).

          7. Посчитать себестоимость:
             - cost_material = material.get_cost(area_or_quantity) * (1 + defect_rate)
             - cost_equip = (equipment.depreciation_per_hour + equipment.operator_cost_per_hour) * time_process
             - cost_other = equipment.consumables_per_hour * time_process (для лазера)
             - cost = cost_material + cost_equip + cost_other

          8. Применить наценки:
             - margin_extra = get_margin("marginLaser")  # пример, ключ берётся из common.json
             - margin_total = MARGIN_OPERATION + margin_extra
             - если margin_total < MARGIN_MIN → margin_total = MARGIN_MIN
             - price = cost * (1 + margin_total)
             - unit_price = price / quantity

          9. Собрать расход материалов:
             - materials = [
                   {
                       "code": material.code,
                       "name": material.name,
                       "quantity": quantity_with_defects,
                       "unit": "шт",
                   },
               ]

         10. Вернуть результат в формате, описанном в CLAUDE.md.

        Здесь мы возвращаем заглушку, чтобы шаблон компилировался до реализации.
        """

        quantity = int(params.get("quantity", 1))

        result: Dict[str, Any] = {
            "cost": 0.0,
            "price": 0.0,
            "unit_price": 0.0,
            "time_hours": 0.0,
            "time_ready": BASE_TIME_READY[1] if BASE_TIME_READY else 0.0,
            "weight_kg": 0.0,
            "materials": [],
        }

        # Обратите внимание: поле share_url будет добавлено автоматически
        # в методе BaseCalculator.execute().

        return result

