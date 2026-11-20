"""
Калькулятор термопереноса.

Мигрировано из js_legacy/calc/calcHeatPress.js.
Типы трансфера: сублимация, DTF, шелкотрансфер, плёнка (film),
плёнка с сублимационной печатью (filmSublimation), плёнка с экосольвентной
печатью (filmEcosolvent), термобумага лазерная (paperLaser).

Не перенесено (ветки JS):
- в ветке dtf нет calcCutSaber (и calcLayoutOnSheet для резки)
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Mapping

import json5

from calculators.base import BaseCalculator, ProductionMode
from calculators.cut_plotter import CutPlotterCalculator
from calculators.print_roll import PrintRollCalculator
from calculators.print_sheet import PrintSheetCalculator
from calculators.sticker import StickerCalculator
from common.layout import layout_on_sheet
from common.markups import MARGIN_MATERIAL, MARGIN_OPERATION, get_margin
from common.process_tools import calc_silk_print
from equipment import heatpress as heatpress_catalog
from equipment import plotter as plotter_catalog
from materials import sheet as sheet_catalog

HEATPRESS_JSON = Path(__file__).parent.parent / "data" / "equipment" / "heatpress.json"
SUBLIMATION_MATERIAL = "PaperSublimation128"
SUBLIMATION_PRINTER = "EPSONWF7610"
DTF_MATERIAL = "PaperDTFTransfer"
DTF_PRINTER = "DTFTransfer"
FILM_DEFAULT_MATERIAL = "POLIFLEXPREMIUMBW"
PLOTTER_CODE = "GraphtecCE5000-60"
FILM_SUBLIMATION_MATERIAL = "POLIFLEX4675"
FILM_ECOSOLVENT_MATERIAL = "POLIFLEX4030"
FILM_ECOSOLVENT_PRINTER = "Technojet160ECO"
PAPER_LASER_MATERIAL = "PaperFOREVERLASERTRANSPARENT"
PAPER_LASER_PRINTER = "KMBizhubC220"
CUSTOMER_MATERIAL_COEFF = 1.25
_TRANSFER_ALIASES = {
    "filmsublimation": "filmSublimation",
    "film_sublimation": "filmSublimation",
    "filmecosolvent": "filmEcosolvent",
    "film_ecosolvent": "filmEcosolvent",
    "paperlaser": "paperLaser",
    "paper_laser": "paperLaser",
}
ITEM_HEATPRESS_MAP = {
    "hat": "Grafalex",
    "mug": "EconopressMUGH",
    "tshirt": "SahokSH49BD",
    "clothes": "SahokSH49BD",
    "bag": "SahokSH49BD",
    "ambrella": "SahokSH49BD",
    "metal": "SahokSH49BD",
}
ITEM_DIFFICULTY = {"clothes": 1, "bag": 1}


def _load_heatpress_raw(code: str) -> Dict[str, Any]:
    with open(HEATPRESS_JSON, "r", encoding="utf-8") as f:
        data = json5.load(f)
    return data.get(code, {})


class HeatPressCalculator(BaseCalculator):
    """Термоперенос: сублимация, DTF, шелкотрансфер, плёнка."""

    slug = "heat_press"
    name = "Термоперенос"
    description = "Расчёт термопереноса на ткани и изделия: сублимация, DTF, шелкотрансфер, плёнка."

    def get_param_schema(self) -> Dict[str, Any]:
        return {
            "slug": self.slug,
            "title": self.name,
            "params": [
                {"name": "quantity", "type": "integer", "required": True, "title": "Тираж", "validation": {"min": 1}},
                {"name": "width", "type": "number", "required": True, "title": "Ширина нанесения (мм)", "unit": "мм"},
                {"name": "height", "type": "number", "required": True, "title": "Высота нанесения (мм)", "unit": "мм"},
                {"name": "transfer_type", "type": "enum", "required": True, "title": "Тип трансфера",
                 "choices": {"inline": [
                     {"id": "sublimation", "title": "Сублимация"},
                     {"id": "dtf", "title": "DTF"},
                     {"id": "silk", "title": "Шелкотрансфер"},
                     {"id": "film", "title": "Плёнка (плоттерная резка)"},
                     {"id": "filmSublimation", "title": "Плёнка с полноцветной сублимационной печатью"},
                     {"id": "filmEcosolvent", "title": "Плёнка с полноцветной экосольвентной печатью"},
                     {"id": "paperLaser", "title": "Печать полноцветной термобумагой"},
                 ]}},
                {"name": "item_type", "type": "enum", "required": False, "default": "tshirt", "title": "Тип изделия",
                 "choices": {"inline": [
                     {"id": "hat", "title": "Головной убор"},
                     {"id": "mug", "title": "Кружка"},
                     {"id": "tshirt", "title": "Футболка"},
                     {"id": "clothes", "title": "Плотная одежда"},
                     {"id": "bag", "title": "Сумка/рюкзак"},
                     {"id": "ambrella", "title": "Зонт"},
                     {"id": "metal", "title": "Металл"},
                 ]}},
                {"name": "silk_colors", "type": "integer", "required": False, "default": 1, "title": "Кол-во цветов (шелк)"},
                {"name": "material_id", "type": "string", "required": False, "default": FILM_DEFAULT_MATERIAL, "title": "Термоплёнка (film)"},
                {"name": "film_colors", "type": "integer", "required": False, "default": 1, "title": "Кол-во цветов/плёнок (film)"},
                {"name": "size_item", "type": "number", "required": False, "default": 0, "title": "Размер элемента резки (film)", "unit": "мм"},
                {"name": "density", "type": "number", "required": False, "default": 0, "title": "Плотность заполнения 0..1 (film)"},
                {"name": "difficulty", "type": "number", "required": False, "default": 1, "title": "Сложность резки (film)"},
                {"name": "is_customer_material", "type": "boolean", "required": False, "default": False, "title": "Изделие заказчика (+25%)"},
                {"name": "mode", "type": "integer", "required": False, "default": 1, "title": "Режим"},
            ],
            "param_groups": {
                "main": ["quantity", "width", "height"],
                "processing": ["transfer_type", "item_type", "is_customer_material", "silk_colors", "material_id", "film_colors", "size_item", "density", "difficulty"],
                "mode": ["mode"],
            },
        }

    def get_options(self) -> Dict[str, Any]:
        heatpresses = []
        try:
            for code, spec in heatpress_catalog._items.items():
                heatpresses.append({"code": code, "name": spec.name})
        except Exception:
            pass
        return {
            "heatpresses": heatpresses,
            "transfer_types": [
                "sublimation",
                "dtf",
                "silk",
                "film",
                "filmSublimation",
                "filmEcosolvent",
                "paperLaser",
            ],
            "item_types": list(ITEM_HEATPRESS_MAP.keys()),
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
                    "quantity": {"type": "integer", "minimum": 1, "description": "Тираж"},
                    "width": {"type": "number", "minimum": 1, "description": "Ширина нанесения, мм"},
                    "height": {"type": "number", "minimum": 1, "description": "Высота нанесения, мм"},
                    "transfer_type": {
                        "type": "string",
                        "enum": [
                            "sublimation",
                            "dtf",
                            "silk",
                            "film",
                            "filmSublimation",
                            "filmEcosolvent",
                            "paperLaser",
                        ],
                        "description": "Тип трансфера",
                    },
                    "item_type": {"type": "string", "enum": list(ITEM_HEATPRESS_MAP.keys()), "default": "tshirt"},
                    "silk_colors": {"type": "integer", "default": 1, "description": "Кол-во цветов для шелка"},
                    "material_id": {"type": "string", "default": FILM_DEFAULT_MATERIAL, "description": "Код термоплёнки (film)"},
                    "film_colors": {"type": "integer", "default": 1, "description": "Кол-во плёнок/цветов (film)"},
                    "size_item": {"type": "number", "default": 0, "description": "Размер элемента для резки (film), мм"},
                    "density": {"type": "number", "default": 0, "description": "Плотность заполнения 0..1 (film)"},
                    "difficulty": {"type": "number", "default": 1, "description": "Сложность формы резки (film)"},
                    "is_customer_material": {"type": "boolean", "default": False, "description": "Изделие заказчика (+25% к итоговой цене)"},
                    "mode": {"type": "integer", "enum": [0, 1, 2], "default": 1},
                },
                "required": ["quantity", "width", "height", "transfer_type"],
            },
        }

    def calculate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        n = int(params.get("quantity", 1))
        width = float(params.get("width", 0))
        height = float(params.get("height", 0))
        size = [width, height]
        raw_transfer = str(params.get("transfer_type", "sublimation")).strip()
        transfer_type = _TRANSFER_ALIASES.get(raw_transfer.lower(), raw_transfer.lower())
        item_type = str(params.get("item_type", "tshirt") or "tshirt").strip().lower()
        silk_colors = int(params.get("silk_colors", 1) or 1)
        material_id = str(params.get("material_id") or FILM_DEFAULT_MATERIAL).strip() or FILM_DEFAULT_MATERIAL
        film_colors = int(params.get("film_colors", 1) or 1)
        size_item = float(params.get("size_item", 0) or 0)
        density = float(params.get("density", 0) or 0)
        difficulty = float(params.get("difficulty", 1) or 1)
        raw_cust = params.get("is_customer_material", False)
        if isinstance(raw_cust, str):
            is_customer_material = raw_cust.strip().lower() in ("1", "true", "yes", "да", "on")
        else:
            is_customer_material = bool(raw_cust)
        mode = ProductionMode(int(params.get("mode", 1)))

        heatpress_code = ITEM_HEATPRESS_MAP.get(item_type, "SahokSH49BD")
        heatpress = heatpress_catalog.get(heatpress_code)
        heatpress_raw = _load_heatpress_raw(heatpress_code)

        defects = heatpress.get_defect_rate(float(n))
        if mode.value > 1:
            defects += defects * (mode.value - 1)
        # JS Math.round: половина вверх; Python round(10.5)==10
        num_with_defects = int(n * (1 + defects) + 0.5)

        item_difficulty = ITEM_DIFFICULTY.get(item_type, 0)
        time_load_arr = heatpress_raw.get("timeLoad", [0.02, 0.05])
        time_load = float(time_load_arr[item_difficulty]) if item_difficulty < len(time_load_arr) else float(time_load_arr[0])
        base_time_ready = heatpress_raw.get("baseTimeReady", [16, 8, 1])
        # JS: baseTimeReady[Math.ceil(modeProduction)]
        idx = min(max(0, math.ceil(mode.value)), len(base_time_ready) - 1)
        base_ready = float(base_time_ready[idx])

        cost_transfer = 0.0
        price_transfer = 0.0
        time_transfer = 0.0
        time_ready_transfer = 0.0
        weight_transfer = 0.0
        cost_cut = 0.0
        price_cut = 0.0
        time_cut = 0.0
        time_ready_cut = 0.0
        weight_cut = 0.0
        materials_out: List[Dict[str, Any]] = []

        if transfer_type == "sublimation":
            print_calc = PrintSheetCalculator()
            print_params = {
                "quantity": num_with_defects,
                "width": size[0],
                "height": size[1],
                "color": "4+0",
                "margins": [0, 0, 0, 0],
                "interval": 2,
                "material_id": SUBLIMATION_MATERIAL,
                "printer_code": SUBLIMATION_PRINTER,
                "mode": mode.value,
            }
            print_result = print_calc.calculate(print_params)
            cost_transfer = float(print_result.get("cost", 0))
            price_transfer = float(print_result.get("price", 0))
            time_transfer = float(print_result.get("time_hours", 0))
            time_ready_transfer = float(print_result.get("time_ready", 0))
            weight_transfer = float(print_result.get("weight_kg", 0))
            materials_out = list(print_result.get("materials") or [])
            time_press_per_item = 35 / 3600.0

        elif transfer_type == "dtf":
            print_calc = PrintSheetCalculator()
            print_params = {
                "quantity": num_with_defects,
                "width": size[0],
                "height": size[1],
                "color": "4+0",
                "margins": [2, 2, 2, 2],
                "interval": 2,
                "material_id": DTF_MATERIAL,
                "printer_code": DTF_PRINTER,
                "mode": mode.value,
                "no_cut": True,
            }
            try:
                print_result = print_calc.calculate(print_params)
                cost_transfer = float(print_result.get("cost", 0))
                price_transfer = float(print_result.get("price", 0))
                time_transfer = float(print_result.get("time_hours", 0))
                time_ready_transfer = float(print_result.get("time_ready", 0))
                weight_transfer = float(print_result.get("weight_kg", 0))
                materials_out = list(print_result.get("materials") or [])
            except KeyError:
                pass
            # JS: calcCutSaber — не перенесено
            time_press_per_item = 15 / 3600.0

        elif transfer_type == "silk":
            silk_result = calc_silk_print(
                num_with_defects,
                size,
                silk_colors,
                "transfer",
                mode=mode.value,
            )
            cost_transfer = silk_result.cost
            price_transfer = silk_result.price
            time_transfer = silk_result.time_hours
            time_ready_transfer = silk_result.time_ready
            materials_out = list(silk_result.materials)
            time_press_per_item = 10 / 3600.0

        elif transfer_type == "film":
            sticker_calc = StickerCalculator()
            sticker_params = {
                "quantity": num_with_defects * max(1, film_colors),
                "width": size[0],
                "height": size[1],
                "size_item": size_item,
                "density": density,
                # В JS: difficulty * 2 (термоплёнка сложнее для выборки)
                "difficulty": difficulty * 2.0,
                "material_id": material_id,
                "mode": mode.value,
            }
            sticker_result = sticker_calc.calculate(sticker_params)
            cost_transfer = float(sticker_result.get("cost", 0))
            price_transfer = float(sticker_result.get("price", 0))
            time_transfer = float(sticker_result.get("time_hours", 0))
            time_ready_transfer = float(sticker_result.get("time_ready", 0))
            weight_transfer = float(sticker_result.get("weight_kg", 0))
            materials_out = list(sticker_result.get("materials") or [])
            time_press_per_item = 20 / 3600.0

        elif transfer_type == "filmSublimation":
            plotter = plotter_catalog.get(PLOTTER_CODE)
            plotter_margins = [float(x) for x in (plotter.margins or [30, 10, 10, 10])]
            if len(plotter_margins) < 4:
                plotter_margins = [30.0, 10.0, 10.0, 10.0]
            # JS margins [left, top, right, bottom] → layout_on_sheet [top, right, bottom, left].
            layout_margins = [
                plotter_margins[1],
                plotter_margins[2],
                plotter_margins[3],
                plotter_margins[0],
            ]
            sub_sheet_mat = sheet_catalog.get(SUBLIMATION_MATERIAL)
            size_sheet = [float(sub_sheet_mat.sizes[0][0]), float(sub_sheet_mat.sizes[0][1])]
            layout_sheet = layout_on_sheet(size, size_sheet, layout_margins, 2.0)
            if layout_sheet["num"] <= 0:
                raise ValueError("Размер нанесения больше допустимого для сублимационного листа")
            num_sheet = math.ceil(num_with_defects / layout_sheet["num"])
            sub_result = self.calculate(
                {
                    "quantity": num_sheet,
                    "width": size_sheet[0],
                    "height": size_sheet[1],
                    "transfer_type": "sublimation",
                    "item_type": "tshirt",
                    "mode": mode.value,
                }
            )
            cost_transfer = float(sub_result.get("cost", 0))
            price_transfer = float(sub_result.get("price", 0))
            time_transfer = float(sub_result.get("time_hours", 0))
            time_ready_transfer = float(sub_result.get("time_ready", 0))
            weight_transfer = float(sub_result.get("weight_kg", 0))
            materials_out = list(sub_result.get("materials") or [])

            cut_result = CutPlotterCalculator().calculate(
                {
                    "quantity": num_sheet,
                    "width": size_sheet[0],
                    "height": size_sheet[1],
                    "size_item": max(size[0], size[1]),
                    "density": 1.0,
                    "difficulty": 1.7,
                    "material_id": FILM_SUBLIMATION_MATERIAL,
                    "is_find_mark": True,
                    "mode": mode.value,
                }
            )
            cost_cut = float(cut_result.get("cost", 0))
            price_cut = float(cut_result.get("price", 0))
            time_cut = float(cut_result.get("time_hours", 0))
            # В JS calcCutPlotter не считает weight, а calcHeatPress.js:183 не прибавляет costCut.timeReady
            time_press_per_item = 45 / 3600.0

        elif transfer_type == "filmEcosolvent":
            print_result = PrintRollCalculator().calculate(
                {
                    "quantity": num_with_defects,
                    "width": size[0],
                    "height": size[1],
                    "material_id": FILM_ECOSOLVENT_MATERIAL,
                    "printer_code": FILM_ECOSOLVENT_PRINTER,
                    "mode": mode.value,
                }
            )
            cost_transfer = float(print_result.get("cost", 0))
            price_transfer = float(print_result.get("price", 0))
            time_transfer = float(print_result.get("time_hours", 0))
            time_ready_transfer = float(print_result.get("time_ready", 0))
            weight_transfer = float(print_result.get("weight_kg", 0))
            materials_out = list(print_result.get("materials") or [])

            cut_result = CutPlotterCalculator().calculate(
                {
                    "quantity": num_with_defects,
                    "width": size[0],
                    "height": size[1],
                    "size_item": max(size[0], size[1]),
                    "density": 1.0,
                    "difficulty": 1.7,
                    "material_id": FILM_ECOSOLVENT_MATERIAL,
                    "is_find_mark": True,
                    "mode": mode.value,
                }
            )
            cost_cut = float(cut_result.get("cost", 0))
            price_cut = float(cut_result.get("price", 0))
            time_cut = float(cut_result.get("time_hours", 0))
            # В JS calcCutPlotter не считает weight (и вес плёнки уже в print_roll), timeReady резки не прибавляется
            time_press_per_item = 15 / 3600.0

        elif transfer_type == "paperLaser":
            print_result = PrintSheetCalculator().calculate(
                {
                    "quantity": num_with_defects,
                    "width": size[0],
                    "height": size[1],
                    "color": "4+0",
                    "margins": [2, 2, 2, 2],
                    "interval": 2,
                    "material_id": PAPER_LASER_MATERIAL,
                    "printer_code": PAPER_LASER_PRINTER,
                    "mode": mode.value,
                }
            )
            cost_transfer = float(print_result.get("cost", 0))
            price_transfer = float(print_result.get("price", 0))
            time_transfer = float(print_result.get("time_hours", 0))
            time_ready_transfer = float(print_result.get("time_ready", 0))
            weight_transfer = float(print_result.get("weight_kg", 0))
            materials_out = list(print_result.get("materials") or [])
            time_press_per_item = 45 / 3600.0

        else:
            raise ValueError(f"Неизвестный тип трансфера: {transfer_type!r}")

        time_press_total = (time_press_per_item + time_load) * num_with_defects
        # JS: heatpress.timePrepare * modeProduction (при mode=0 → 0)
        time_prepare = float(heatpress_raw.get("timePrepare", 0.05)) * mode.value
        time_operator = time_press_total + time_prepare

        cost_depreciation_hour = heatpress.depreciation_per_hour
        cost_power = float(heatpress_raw.get("costPower", 5.0))
        power_per_hour = float(heatpress_raw.get("powerPerHour", 2.0))
        cost_press_per_hour = cost_power * power_per_hour
        cost_press = cost_depreciation_hour * time_press_total + cost_press_per_hour * time_press_total
        cost_operator = time_operator * heatpress.operator_cost_per_hour

        cost_total = cost_operator + cost_press + cost_transfer + cost_cut
        margin_heatpress = get_margin("marginHeatPress")
        price_total = (
            cost_operator * (1 + MARGIN_OPERATION)
            + cost_press * (1 + MARGIN_MATERIAL)
            + (price_transfer + price_cut)
        ) * (1 + margin_heatpress)
        # В cjsCalc формы 40 (элемент 2283 ckbMaterialCostomer='isMaterialCustomer'):
        # наценка +25% применяется к итоговой цене, себестоимость не умножается.
        if is_customer_material:
            price_total *= CUSTOMER_MATERIAL_COEFF

        time_hours = time_operator + time_transfer + time_cut
        # JS: result.time + costTransfer.timeReady + baseTimeReady (+ costCut)
        time_ready = time_hours + time_ready_transfer + time_ready_cut + base_ready

        return {
            "cost": float(cost_total),
            "price": float(price_total),
            "unit_price": float(price_total) / max(1, n),
            "time_hours": float(time_hours),
            "time_ready": float(time_ready),
            "weight_kg": float(weight_transfer + weight_cut),
            "materials": materials_out,
        }
