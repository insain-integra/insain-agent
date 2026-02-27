from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Optional, Sequence

from calculators.base import BaseCalculator, ProductionMode
from common.helpers import calc_weight
from common.layout import layout_on_roll, layout_on_sheet
from common.markups import (
    MARGIN_MATERIAL,
    MARGIN_MIN,
    MARGIN_OPERATION,
    get_margin,
)
from equipment import laser as laser_catalog, tools as tools_catalog
from materials import hardsheet, misc


class LaserCalculator(BaseCalculator):
    """
    Калькулятор лазерной резки и гравировки.

    Логика полностью перенесена из `js_legacy/calc/calcLaser.js` с
    сохранением структуры расчёта. Основные этапы:

    1. Чтение входных параметров: тираж, размер изделия, материал, режим, опции.
    2. Загрузка оборудования (`laser_catalog`) и материала (`hardsheet`).
    3. Расчёт процента брака по таблице дефектов лазера, учёт режима производства.
    4. При необходимости — расчёт времени гравировки (сплошная + контур).
    5. Подбор оптимального формата материала (лист / рулон) с минимальной себестоимостью
       через перебор всех размеров `material.sizes` и `layout_on_sheet/layout_on_roll`.
    6. Расчёт времени резки и загрузки (`timeCut` в JS) по скорости `cut_speed_table`.
    7. Опционально — расчёт ручных операций нанесения клеевого слоя через инструмент
       `ManualRoll` из каталога `tools` (аналог `calcManualRoll` из JS).
    8. Суммирование времени (`timePrepare`, `timeCut`, `timeGrave`, время клеевого слоя)
       и вычисление `time_hours` и `time_ready` с учётом `baseTimeReady` лазера.
    9. Расчёт полной себестоимости: материал + амортизация + оператор + расходники
       + ручные операции, с учётом возможного перерасчёта на брак.
    10. Применение наценок: материал — через `MARGIN_MATERIAL`, операции — через
        `MARGIN_OPERATION + get_margin("marginLaser")` с нижней границей `MARGIN_MIN`.
    11. Расчёт массы тиража через `calc_weight` и сбор структуры расхода материалов.

    Результат возвращается в формате, описанном в `CLAUDE.md` (cost, price,
    unit_price, time_hours, time_ready, weight_kg, materials). Поле `share_url`
    добавляется в базовом классе `BaseCalculator.execute()`.
    """

    slug = "laser"
    name = "Лазерная резка и гравировка"
    description = "Расчёт стоимости лазерной резки и гравировки по материалам hardsheet."

    def get_options(self) -> Dict[str, Any]:
        """
        Опции для фронтенда / бота.

        Сейчас возвращает:
          - список листовых материалов `hardsheet` для выбора;
          - список режимов производства `ProductionMode`.

        При интеграции с сайтом или ботом этот метод можно расширить
        дополнительными опциями (тип гравировки, предустановки размеров и т.п.).
        """
        materials = hardsheet.list_for_frontend()
        return {
            "materials": materials,
            "modes": [
                {"value": ProductionMode.ECONOMY, "label": "Экономичный"},
                {"value": ProductionMode.STANDARD, "label": "Стандартный"},
                {"value": ProductionMode.EXPRESS, "label": "Экспресс"},
            ],
        }

    def get_tool_schema(self) -> Dict[str, Any]:
        """
        JSON Schema для LLM / function calling.

        Описывает структуру входных параметров `calculate()` для инструментов ИИ
        и валидации API. Поля подобраны так, чтобы один-в-один покрыть опции
        оригинального JS-калькулятора:

          - базовые размеры и тираж (`quantity`, `width_mm`, `height_mm`);
          - выбор материала (`material_code` из каталога `hardsheet`);
          - режим производства (`mode` → `ProductionMode`);
          - блок `is_cut_laser` для конфигурации резки;
          - флаги и параметры гравировки (`is_grave`, `is_grave_fill`, `is_grave_contur`);
          - поиск меток для резки по изображению (`is_find_mark`);
          - режим работы с материалом (наш/заказчика/без учёта);
          - опциональный клеевой слой (`is_adhesive_layer`).
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
                    "width_mm": {
                        "type": "number",
                        "minimum": 1,
                        "description": "Ширина изделия, мм.",
                    },
                    "height_mm": {
                        "type": "number",
                        "minimum": 1,
                        "description": "Высота изделия, мм.",
                    },
                    "material_code": {
                        "type": "string",
                        "description": "Код материала из hardsheet (например, 'PVC3').",
                    },
                    "mode": {
                        "type": "integer",
                        "enum": [
                            ProductionMode.ECONOMY,
                            ProductionMode.STANDARD,
                            ProductionMode.EXPRESS,
                        ],
                        "description": "Режим производства: 0 — эконом, 1 — стандарт, 2 — экспресс.",
                        "default": ProductionMode.STANDARD,
                    },
                    "is_cut_laser": {
                        "type": "object",
                        "description": "Параметры резки (если не задано — без резки).",
                        "properties": {
                            "len_cut": {
                                "type": "number",
                                "description": "Общая длина реза одного изделия, мм. Если 0 — считается автоматически.",
                                "default": 0,
                            },
                            "size_item": {
                                "type": "number",
                                "description": "Площадь изделия, мм², для расчёта внутреннего периметра.",
                                "default": 0,
                            },
                            "density": {
                                "type": "number",
                                "description": "Коэффициент заполнения/плотности внутреннего контура.",
                                "default": 0,
                            },
                            "difficulty": {
                                "type": "number",
                                "description": "Коэффициент сложности контура.",
                                "default": 1,
                            },
                        },
                    },
                    "is_grave": {
                        "type": "integer",
                        "description": "Индекс детализации гравировки (0, 1, 2...).",
                    },
                    "is_grave_fill": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 2,
                        "maxItems": 2,
                        "description": "Размер области сплошной гравировки [w, h] в мм.",
                    },
                    "is_grave_contur": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 2,
                        "maxItems": 2,
                        "description": "Размер области контурной гравировки [w, l] в мм.",
                    },
                    "is_find_mark": {
                        "type": "boolean",
                        "description": "Поиск меток при резке по изображению (увеличивает время загрузки).",
                        "default": False,
                    },
                    "material_mode": {
                        "type": "string",
                        "enum": ["isMaterial", "isMaterialCustomer", "noMaterial"],
                        "description": (
                            "Режим работы с материалом: "
                            "isMaterial — наш материал, "
                            "isMaterialCustomer — материал заказчика, "
                            "noMaterial — материал не учитывается."
                        ),
                        "default": "isMaterial",
                    },
                    "is_adhesive_layer": {
                        "type": "string",
                        "enum": ["AdhesiveLayer50", "AdhesiveLayer130"],
                        "description": "Нанесение клеевого слоя (тип скотча).",
                    },
                },
                "required": ["quantity", "width_mm", "height_mm"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        """
        Перенос логики `insaincalc.calcLaser` из JS.

        Важно: метод реализует только математику и структуру ответа. Он не:
          - не добавляет `share_url` (это делает `execute()` базового класса);
          - не занимается сериализацией/валидацией входа — за это отвечает
            вызывающий код (API, бот или LLM-интеграция).

        Аргумент `params` — обычный `Mapping` (обычно dict) с ключами,
        описанными в `get_tool_schema()`.
        """
        quantity = int(params.get("quantity", 1))
        width_mm = float(params.get("width_mm", 0))
        height_mm = float(params.get("height_mm", 0))
        if width_mm <= 0 or height_mm <= 0:
            raise ValueError("width_mm and height_mm must be positive")
        size = [width_mm, height_mm]

        material_code = str(params.get("material_code", "") or "")
        mode = ProductionMode(params.get("mode", ProductionMode.STANDARD))

        # Оборудование и материал
        laser = next(iter(laser_catalog._items.values()))  # type: ignore[attr-defined]

        material = None
        if material_code:
            material = hardsheet.get(material_code)
        else:
            raise ValueError("material_code is required for laser calculator")

        # Брак
        defect_rate = laser.get_defect_rate(quantity)
        if mode.value > 1:
            defect_rate += defect_rate * (mode.value - 1)
        num_with_defects = round(quantity * (1 + defect_rate))

        interval = 5.0
        # Отступы берем из лазера; это массив [top, right, bottom, left]
        margins = (laser.margins or [0.0, 0.0, 0.0, 0.0])[:4]

        time_cut = 0.0
        time_grave = 0.0
        cost_material = 0.0
        materials: List[Dict[str, Any]] = []

        # Гравировка
        is_grave = params.get("is_grave")
        if is_grave is not None:
            resolution = int(is_grave)
            grave_per_hour = laser.get_grave_speed(resolution)
            if grave_per_hour > 0:
                if "is_grave_fill" in params:
                    size_grave = params["is_grave_fill"]  # type: ignore[index]
                    area_grave = float(size_grave[0]) * float(size_grave[1]) / 1_000_000.0
                    area_grave_with_defects = area_grave * num_with_defects
                    time_grave += area_grave_with_defects / grave_per_hour

                if "is_grave_contur" in params:
                    size_grave_contur = params["is_grave_contur"]  # type: ignore[index]
                    num_contur = math.ceil(float(size_grave_contur[0]) / 0.1)
                    len_grave_contur = (
                        num_with_defects * num_contur * float(size_grave_contur[1])
                    )  # мм
                    cut_per_hour_for_grave = laser.get_cut_speed(0.0) or 1.0
                    time_grave += len_grave_contur / cut_per_hour_for_grave / 1000.0

        # Резка и материал
        is_cut = params.get("is_cut_laser")
        len_material = 0.0
        num_sheet = 0.0

        if material is not None:
            sizes_material = material.sizes or []
            if sizes_material:
                # Параметры резки
                len_cut = 0.0
                if isinstance(is_cut, Mapping):
                    len_cut = float(is_cut.get("len_cut", 0.0))
                    size_item = float(is_cut.get("size_item", 0.0))
                    density = float(is_cut.get("density", 0.0))
                    difficulty = float(is_cut.get("difficulty", 1.0))
                else:
                    size_item = 0.0
                    density = 0.0
                    difficulty = 1.0

                if len_cut == 0.0:
                    len_cut = (size[0] + size[1]) * 2.0
                    if size_item:
                        len_cut += 4.0 * size[0] * size[1] * density / size_item
                    len_cut *= difficulty

                # Проверяем, помещается ли в лазер (используем только первые две координаты max_size)
                laser_size_xy = (laser.max_size or sizes_material[0])[:2]
                layout_on_laser = layout_on_sheet(
                    item_size=size,
                    sheet_size=laser_size_xy,
                    margins=margins,
                    gap=interval,
                )
                if layout_on_laser["num"] == 0:
                    raise ValueError("Изделие не помещается в лазер")

                num_load = math.ceil(num_with_defects / layout_on_laser["num"])
                is_find_mark = bool(params.get("is_find_mark", False))

                min_cost_material: Optional[float] = None
                best_size_material: Optional[Sequence[float]] = None
                best_num_sheet = 0.0
                best_len_material = 0.0

                for size_material in sizes_material:
                    size_w, size_h = float(size_material[0]), float(size_material[1])
                    len_cut_with_defects = len_cut * num_with_defects

                    if size_h == 0.0:
                        # Рулон
                        layout_roll = layout_on_roll(
                            quantity=num_with_defects,
                            item_size=size,
                            roll_size=[size_w, size_h],
                            gap=interval,
                        )
                        if layout_roll["num"] == 0:
                            continue
                        len_mat = layout_roll["length"]
                        base_cost = material.get_cost(len_mat / 1000.0)
                        if material.length_min and material.length_min > 0:
                            cost_mat = (
                                base_cost
                                * math.ceil(len_mat / material.length_min)
                                * material.length_min
                                / 1_000_000.0
                                * size_w
                            )
                        else:
                            cost_mat = base_cost * len_mat * size_w / 1_000_000.0
                        num_sheets = 0.0
                    else:
                        # Лист
                        layout_sheet = layout_on_sheet(
                            item_size=size,
                            sheet_size=[size_w, size_h],
                            margins=margins,
                            gap=interval,
                        )
                        if layout_sheet["num"] == 0:
                            continue

                        if material.min_size:
                            layout_min = layout_on_sheet(
                                item_size=material.min_size,
                                sheet_size=[size_w, size_h],
                            )
                            layout_min_num = max(1, layout_min["num"])
                        else:
                            layout_min_num = 1

                        num_sheets = math.ceil(
                            num_with_defects / layout_sheet["num"] * layout_min_num
                        ) / layout_min_num

                        base_cost = material.get_cost(num_sheets)
                        cost_mat = (
                            base_cost * num_sheets * size_w * size_h / 1_000_000.0
                        )
                        len_mat = 0.0

                    if min_cost_material is None or cost_mat < min_cost_material:
                        min_cost_material = cost_mat
                        best_size_material = [size_w, size_h]
                        best_num_sheet = num_sheets
                        best_len_material = len_mat

                if min_cost_material is None:
                    raise ValueError("Изделие не помещается на материал")

                cost_material = min_cost_material
                size_material = best_size_material or sizes_material[0]
                num_sheet = best_num_sheet
                len_material = best_len_material

                cut_speed = laser.get_cut_speed(material.thickness or 0.0) or 1.0
                len_cut_with_defects = len_cut * num_with_defects
                time_cut = len_cut_with_defects / cut_speed / 1000.0 + num_load * (
                    laser.time_load or 0.0
                )
                if is_find_mark:
                    time_cut += num_load * (laser.time_load or 0.0)

                # Расход материала
                material_qty: float
                material_unit: str
                if size_material[1] == 0.0:
                    material_qty = len_material
                    material_unit = "mm"
                else:
                    material_qty = num_sheet
                    material_unit = "sheet"

                materials.append(
                    {
                        "code": material.code,
                        "name": material.name,
                        "size_mm": size_material,
                        "quantity": material_qty,
                        "unit": material_unit,
                    }
                )

        # Нанесение клеевого слоя (через ManualRoll)
        cost_adhesive_cost = 0.0
        cost_adhesive_price = 0.0
        cost_adhesive_time = 0.0
        cost_adhesive_weight = 0.0

        adhesive_layer = params.get("is_adhesive_layer")
        if adhesive_layer and material is not None:
            if adhesive_layer == "AdhesiveLayer130":
                adhesive_id = "Sheet3M7955"
            else:
                adhesive_id = "Sheet3M7952"

            mat_adh = misc.get(adhesive_id)
            size_adh = mat_adh.sizes[0]
            num_adh_sheets = (
                quantity
                * (size[0] + 5.0)
                * (size[1] + 5.0)
                / (size_adh[0] * size_adh[1])
            )

            tool = tools_catalog.get("ManualRoll")
            area = size[0] * size[1] / 1_000_000.0
            roll_table = tool._items.get("ManualRoll") if False else None  # type: ignore[attr-defined]
            # Упрощённая версия calcManualRoll: без подгиба края.
            roll_per_hour = tool._items is None  # type: ignore[attr-defined]
            # Берём скорость из данных JSON напрямую:
            raw = next(iter(tool._items.values())).__dict__  # type: ignore[attr-defined]
            roll_per_hour_val = 1.0
            edge_per_hour_val = 1.0
            if "rollPerHour" in raw:
                from equipment.base import LookupTable

                roll_per_hour_val = LookupTable(raw["rollPerHour"]).find(area * num_adh_sheets)  # type: ignore[arg-type]
            if "edgePerHour" in raw:
                edge_per_hour_val = float(raw["edgePerHour"])

            sum_len = 0.0
            sum_area = area * num_adh_sheets
            time_prepare = tool.time_prepare * mode.value
            time_process = (
                sum_area / roll_per_hour_val + sum_len / edge_per_hour_val + time_prepare
            )
            time_operator = time_process
            cost_depr_hour_tool = tool.depreciation_per_hour
            cost_process = cost_depr_hour_tool * time_process
            cost_operator_tool = time_operator * tool.operator_cost_per_hour
            cost_manual = cost_process + cost_operator_tool
            margin_extra_manual = get_margin("marginProcessManual")
            margin_manual = max(MARGIN_OPERATION + margin_extra_manual, MARGIN_MIN)
            price_manual = cost_manual * (1 + margin_manual)

            cost_adhesive_cost = cost_manual
            cost_adhesive_price = price_manual
            cost_adhesive_time = time_process
            cost_adhesive_weight = (
                num_adh_sheets * (mat_adh.weight_per_unit or 0.0) / 1000.0
            )

            # Материал клеевого слоя
            materials.append(
                {
                    "code": adhesive_id,
                    "name": mat_adh.name,
                    "size_mm": size_adh,
                    "quantity": num_adh_sheets,
                    "unit": "sheet",
                }
            )

            # Себестоимость и цена клеевого слоя (материал)
            cost_adhesive_cost += num_adh_sheets * mat_adh.get_cost(1.0)
            cost_adhesive_price += num_adh_sheets * mat_adh.get_cost(1.0) * (
                1 + MARGIN_MATERIAL
            )

        # Время
        time_prepare = laser.time_prepare * mode.value
        time_operator = 0.75 * time_cut + 0.5 * time_grave + time_prepare

        # Стоимость
        cost_dep_hour = laser.depreciation_per_hour
        cost_operator = time_operator * laser.operator_cost_per_hour
        cost_cut = (cost_dep_hour + laser.consumables_per_hour) * time_cut
        cost_grave = (cost_dep_hour + laser.consumables_per_hour) * time_grave

        cost = cost_cut + cost_grave + cost_material + cost_operator + cost_adhesive_cost
        cost = math.ceil(cost)

        # Если брак не учли в количестве — умножаем на (1 + defect_rate)
        if num_with_defects == quantity:
            cost *= 1 + defect_rate

        margin_extra = get_margin("marginLaser")
        effective_margin = max(MARGIN_OPERATION + margin_extra, MARGIN_MIN)
        price = math.ceil(
            cost_material * (1 + MARGIN_MATERIAL)
            + (cost_cut + cost_grave + cost_operator) * (1 + effective_margin)
            + cost_adhesive_price
        )

        time_hours = math.ceil(
            (time_cut + time_grave + time_prepare + cost_adhesive_time) * 100.0
        ) / 100.0
        time_ready = time_hours + laser.get_time_ready(mode.value + 1)

        weight_kg = 0.0
        if material is not None:
            weight_kg = calc_weight(
                quantity=quantity,
                density=material.density or 0.0,
                thickness=material.thickness or 0.0,
                size=size,
                density_unit=material.density_unit,
            )
        weight_kg += cost_adhesive_weight

        result: Dict[str, Any] = {
            "cost": float(cost),
            "price": float(price),
            "unit_price": float(price) / float(quantity),
            "time_hours": float(time_hours),
            "time_ready": float(time_ready),
            "weight_kg": float(weight_kg),
            "materials": materials,
        }

        return result

